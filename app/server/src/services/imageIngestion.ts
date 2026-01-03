import { ImageHasher } from './imageHasher.js';
import { DuplicateDetector } from './duplicateDetector.js';
import { ClipEmbedder } from './clipEmbedder.js';
import { getStorage } from '../lib/serviceRegistry.js';
import {
  createImageCluster,
  createMediaWithHashes,
  linkMediaToCluster,
  setCanonicalImage,
  updateClusterLastSeen,
  incrementClusterRepostCount,
  createRepostRelationship,
  linkMediaToPost,
  getMediaById,
  getClusterById,
} from '../neo4j/queries/images.js';
import { withSession } from '../lib/session.js';

export interface IngestionMetadata {
  postId?: string;
  subreddit?: string;
  author?: string;
  title?: string;
  createdAt?: Date;
}

export interface IngestionResult {
  mediaId: string;
  clusterId: string;
  isDuplicate: boolean;
  isRepost: boolean;
  confidence?: number;
  matchedMethod?: string;
  original?: {
    mediaId: string;
    firstSeen: Date;
    postId?: string;
  };
}

export class ImageIngestionService {
  private hasher: ImageHasher;
  private detector: DuplicateDetector;
  private clipEmbedder: ClipEmbedder;

  constructor() {
    this.hasher = new ImageHasher();
    this.detector = new DuplicateDetector();
    this.clipEmbedder = new ClipEmbedder();
  }

  async ingestImage(
    imageBuffer: Buffer,
    metadata: IngestionMetadata = {}
  ): Promise<IngestionResult> {
    const storage = getStorage();
    const hashes = await this.hasher.computeHashesFromBuffer(imageBuffer);

    const exactMatch = await this.detector.checkExactDuplicate(hashes.sha256);
    if (exactMatch) {
      const existingMedia = await getMediaById(exactMatch);
      if (existingMedia && existingMedia.clusterId) {
        const cluster = await getClusterById(existingMedia.clusterId);
        return {
          mediaId: exactMatch,
          clusterId: existingMedia.clusterId,
          isDuplicate: true,
          isRepost: false,
          confidence: 1.0,
          matchedMethod: 'sha256',
          original: cluster ? {
            mediaId: exactMatch,
            firstSeen: new Date(cluster.firstSeen),
            postId: metadata.postId,
          } : undefined,
        };
      }
    }

    const nearDuplicates = await this.detector.findNearDuplicates(hashes);
    
    let clusterId: string;
    let isRepost = false;
    let confidence: number | undefined;
    let matchedMethod: string | undefined;
    let originalMediaId: string | undefined;

    if (nearDuplicates.length > 0) {
      const bestMatch = nearDuplicates[0];
      clusterId = bestMatch.clusterId;
      isRepost = true;
      confidence = bestMatch.confidence;
      matchedMethod = bestMatch.method;
      originalMediaId = bestMatch.mediaId;

      await incrementClusterRepostCount(clusterId);
      await updateClusterLastSeen(clusterId, new Date());
    } else {
      const clipMatches = await this.checkClipSimilarity(imageBuffer, hashes);
      if (clipMatches && clipMatches.length > 0) {
        const bestMatch = clipMatches[0];
        clusterId = bestMatch.clusterId;
        isRepost = true;
        confidence = bestMatch.similarity;
        matchedMethod = 'clip';
        originalMediaId = bestMatch.mediaId;

        await incrementClusterRepostCount(clusterId);
        await updateClusterLastSeen(clusterId, new Date());
      } else {
        clusterId = await createImageCluster(hashes.sha256, new Date());
        await this.detector.addToPhashBuckets(hashes.phash, clusterId);
      }
    }

    const storagePath = await storage.storeImage(imageBuffer, hashes.sha256, hashes.mimeType);
    const imageUrl = storage.getImageUrl(hashes.sha256);

    const mediaId = await createMediaWithHashes({
      sha256: hashes.sha256,
      phash: hashes.phash,
      dhash: hashes.dhash,
      width: hashes.width,
      height: hashes.height,
      sizeBytes: hashes.sizeBytes,
      mimeType: hashes.mimeType,
      url: imageUrl,
      storagePath,
      createdAt: metadata.createdAt || new Date(),
    });

    await linkMediaToCluster(mediaId, clusterId, confidence || 1.0);

    if (!isRepost) {
      await setCanonicalImage(clusterId, mediaId);
      await this.detector.storeClusterMetadata({
        clusterId,
        canonicalSha256: hashes.sha256,
        canonicalMediaId: mediaId,
        repostCount: 1,
        firstSeen: new Date().toISOString(),
      });
      await this.detector.addToPhashBuckets(hashes.phash, clusterId);
    } else if (originalMediaId) {
      await createRepostRelationship(mediaId, originalMediaId, confidence || 0.95, matchedMethod || 'unknown');
    }

    await this.detector.storeHashMapping(
      hashes.sha256,
      hashes.phash,
      hashes.dhash,
      clusterId,
      mediaId
    );

    if (!isRepost) {
      const embedding = await this.clipEmbedder.computeEmbeddingFromBuffer(imageBuffer);
      await this.detector.storeClipEmbedding(hashes.sha256, embedding);
    }

    if (metadata.postId) {
      await this.ensurePostExists(metadata);
      await linkMediaToPost(mediaId, metadata.postId);
    }

    const cluster = await getClusterById(clusterId);
    const original = originalMediaId ? await getMediaById(originalMediaId) : null;

    return {
      mediaId,
      clusterId,
      isDuplicate: isRepost,
      isRepost,
      confidence,
      matchedMethod,
      original: original && cluster ? {
        mediaId: original.id,
        firstSeen: new Date(cluster.firstSeen),
        postId: metadata.postId,
      } : undefined,
    };
  }

  private async checkClipSimilarity(
    imageBuffer: Buffer,
    hashes: { sha256: string }
  ): Promise<Array<{ clusterId: string; mediaId: string; similarity: number }> | null> {
    const { getVectorSearchService } = await import('../lib/serviceRegistry.js');
    const vectorSearch = getVectorSearchService();

    const queryEmbedding = await this.clipEmbedder.computeEmbeddingFromBuffer(imageBuffer);
    const similarEmbeddings = await vectorSearch.searchSimilar(queryEmbedding, 10, 0.95);

    if (!similarEmbeddings || similarEmbeddings.length === 0) {
      return null;
    }

    const matches: Array<{ clusterId: string; mediaId: string; similarity: number }> = [];

    for (const { sha256, similarity } of similarEmbeddings) {
      const clusterMeta = await this.detector.getClusterMetadataBySha256(sha256);
      if (!clusterMeta) continue;

      matches.push({
        clusterId: clusterMeta.clusterId,
        mediaId: clusterMeta.canonicalMediaId,
        similarity,
      });
    }

    return matches.length > 0 ? matches.sort((a, b) => b.similarity - a.similarity) : null;
  }

  private async ensurePostExists(metadata: IngestionMetadata): Promise<void> {
    if (!metadata.postId) return;

    return withSession(async (session) => {
      const query = `
        MERGE (p:Post {id: $postId})
        ON CREATE SET
          p.title = $title,
          p.created_utc = datetime($createdAt),
          p.is_image = true
        WITH p
        OPTIONAL MATCH (s:Subreddit {name: $subreddit})
        FOREACH (ignore IN CASE WHEN s IS NOT NULL THEN [1] ELSE [] END |
          MERGE (p)-[:POSTED_IN]->(s)
        )
        WITH p
        OPTIONAL MATCH (u:User {username: $author})
        FOREACH (ignore IN CASE WHEN u IS NOT NULL THEN [1] ELSE [] END |
          MERGE (u)-[:POSTED]->(p)
        )
      `;

      await session.run(query, {
        postId: metadata.postId,
        title: metadata.title || '',
        createdAt: (metadata.createdAt || new Date()).toISOString(),
        subreddit: metadata.subreddit || '',
        author: metadata.author || 'deleted',
      });
    });
  }
}

