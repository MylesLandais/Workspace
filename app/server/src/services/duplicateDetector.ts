import { getValkeyClient } from '../valkey/client.js';
import { ImageHashes } from './imageHasher.js';
import { getBucketKeys, hammingDistance } from './phashBucketing.js';
import { ClipEmbedder } from './clipEmbedder.js';
import logger from '../lib/logger.js';

export interface DuplicateMatch {
  mediaId: string;
  clusterId: string;
  confidence: number;
  method: 'sha256' | 'phash' | 'dhash' | 'clip';
  hammingDistance?: number;
  clipSimilarity?: number;
}

export interface ClusterMetadata {
  clusterId: string;
  canonicalSha256: string;
  canonicalMediaId: string;
  repostCount: number;
  firstSeen: string;
}

const PHASH_THRESHOLD = 10;
const DHASH_THRESHOLD = 5;
const CLIP_THRESHOLD = 0.95;

export class DuplicateDetector {
  private clipEmbedder: ClipEmbedder;

  constructor() {
    this.clipEmbedder = new ClipEmbedder();
  }

  async checkExactDuplicate(sha256: string): Promise<string | null> {
    const client = getValkeyClient();
    const key = `image:hashes:${sha256}`;
    
    const existing = await client.hGetAll(key);
    if (existing && existing.mediaId) {
      await client.setEx(`recent:sha256:${sha256}`, 86400, existing.mediaId);
      return existing.mediaId;
    }
    
    return null;
  }

  async storeHashMapping(sha256: string, phash: bigint, dhash: bigint, clusterId: string, mediaId: string): Promise<void> {
    const client = getValkeyClient();
    const key = `image:hashes:${sha256}`;
    
    await client.hSet(key, {
      phash: phash.toString(),
      dhash: dhash.toString(),
      clusterId,
      mediaId,
    });
    
    await client.setEx(`recent:sha256:${sha256}`, 86400, mediaId);
  }

  async findNearDuplicates(hashes: ImageHashes): Promise<DuplicateMatch[]> {
    const client = getValkeyClient();
    const bucketKeys = getBucketKeys(hashes.phash, 16);

    const candidateClusterIds = new Set<string>();

    const bucketPromises = bucketKeys.map((bucketKey) =>
      client.sMembers(bucketKey)
    );
    const bucketResults = await Promise.all(bucketPromises);

    for (const clusterIds of bucketResults) {
      for (const clusterId of clusterIds) {
        candidateClusterIds.add(clusterId);
      }
    }

    if (candidateClusterIds.size === 0) {
      return [];
    }

    const clusterIdArray = Array.from(candidateClusterIds);
    const pipeline = client.multi();

    for (const clusterId of clusterIdArray) {
      pipeline.hGetAll(`cluster:meta:${clusterId}`);
    }

    const metaResults = (await pipeline.exec()) as any[];

    const clusterMetadatas = new Map<string, ClusterMetadata>();
    const hashPromises: Promise<any>[] = [];

    for (let i = 0; i < metaResults.length; i++) {
      const meta = metaResults[i];
      if (meta && meta.clusterId) {
        clusterMetadatas.set(meta.clusterId, {
          clusterId: meta.clusterId,
          canonicalSha256: meta.canonicalSha256,
          canonicalMediaId: meta.canonicalMediaId,
          repostCount: parseInt(meta.repostCount || '0', 10),
          firstSeen: meta.firstSeen,
        });

        hashPromises.push(
          client.hGetAll(`image:hashes:${meta.canonicalSha256}`)
        );
      }
    }

    const hashResults = await Promise.all(hashPromises);

    const matches: DuplicateMatch[] = [];

    for (let i = 0; i < hashResults.length; i++) {
      const hashResult = hashResults[i];
      if (!hashResult.phash) continue;

      const clusterMeta = Array.from(clusterMetadatas.values())[i];
      if (!clusterMeta) continue;

      const canonicalPhash = BigInt(hashResult.phash);
      const canonicalDhash = hashResult.dhash ? BigInt(hashResult.dhash) : null;

      const phashDist = hammingDistance(hashes.phash, canonicalPhash);

      if (phashDist <= PHASH_THRESHOLD) {
        const confidence = this.calculateConfidence(phashDist, 64);
        matches.push({
          mediaId: clusterMeta.canonicalMediaId,
          clusterId: clusterMeta.clusterId,
          confidence,
          method: 'phash',
          hammingDistance: phashDist,
        });
      } else if (canonicalDhash) {
        const dhashDist = hammingDistance(hashes.dhash, canonicalDhash);
        if (dhashDist <= DHASH_THRESHOLD) {
          const confidence = this.calculateConfidence(dhashDist, 64);
          matches.push({
            mediaId: clusterMeta.canonicalMediaId,
            clusterId: clusterMeta.clusterId,
            confidence,
            method: 'dhash',
            hammingDistance: dhashDist,
          });
        }
      }
    }

    matches.sort((a, b) => b.confidence - a.confidence);
    return matches;
  }

  async checkClipSimilarity(imageBuffer: Buffer, canonicalSha256: string): Promise<number | null> {
    try {
      const client = getValkeyClient();
      const embeddingKey = `clip:embedding:${canonicalSha256}`;
      
      let canonicalEmbedding: number[] | null = null;
      const cached = await client.get(embeddingKey);
      
      if (cached) {
        canonicalEmbedding = JSON.parse(cached);
      } else {
        return null;
      }
      
      const queryEmbedding = await this.clipEmbedder.computeEmbeddingFromBuffer(imageBuffer);
      const similarity = this.clipEmbedder.cosineSimilarity(queryEmbedding, canonicalEmbedding!);
      
      return similarity >= CLIP_THRESHOLD ? similarity : null;
    } catch (error) {
      logger.error('CLIP similarity check failed', error);
      return null;
    }
  }

  async storeClipEmbedding(sha256: string, embedding: number[]): Promise<void> {
    const { VectorSearchService } = await import('./vectorSearch.js');
    const vectorSearch = new VectorSearchService();
    await vectorSearch.storeEmbedding(sha256, embedding);

    const client = getValkeyClient();
    await client.del(`clip:embedding:${sha256}`);
  }

  async addToPhashBuckets(phash: bigint, clusterId: string): Promise<void> {
    const client = getValkeyClient();
    const bucketKeys = getBucketKeys(phash, 16);
    
    for (const bucketKey of bucketKeys) {
      await client.sAdd(bucketKey, clusterId);
    }
  }

  async getClusterMetadata(clusterId: string): Promise<ClusterMetadata | null> {
    const client = getValkeyClient();
    const key = `cluster:meta:${clusterId}`;
    
    const meta = await client.hGetAll(key);
    if (!meta || !meta.clusterId) {
      return null;
    }
    
    return {
      clusterId: meta.clusterId,
      canonicalSha256: meta.canonicalSha256,
      canonicalMediaId: meta.canonicalMediaId,
      repostCount: parseInt(meta.repostCount || '0', 10),
      firstSeen: meta.firstSeen,
    };
  }

  async storeClusterMetadata(metadata: ClusterMetadata): Promise<void> {
    const client = getValkeyClient();
    const key = `cluster:meta:${metadata.clusterId}`;

    await client.hSet(key, {
      clusterId: metadata.clusterId,
      canonicalSha256: metadata.canonicalSha256,
      canonicalMediaId: metadata.canonicalMediaId,
      repostCount: metadata.repostCount.toString(),
      firstSeen: metadata.firstSeen,
    });

    const sha256IndexKey = `sha256:to:cluster:${metadata.canonicalSha256}`;
    await client.set(sha256IndexKey, metadata.clusterId);
  }

  async getClusterMetadataBySha256(sha256: string): Promise<ClusterMetadata | null> {
    const client = getValkeyClient();
    const sha256IndexKey = `sha256:to:cluster:${sha256}`;
    const clusterId = await client.get(sha256IndexKey);

    if (!clusterId) return null;

    return this.getClusterMetadata(clusterId);
  }

  calculateConfidence(hammingDistance: number, maxDistance: number = 64): number {
    return Math.max(0.0, 1.0 - hammingDistance / maxDistance);
  }
}

