import { getValkeyClient } from '../valkey/client.js';
import { ImageHashes } from './imageHasher.js';
import { getBucketKeys, hammingDistance } from './phashBucketing.js';
import { ClipEmbedder } from './clipEmbedder.js';

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
    
    for (const bucketKey of bucketKeys) {
      const clusterIds = await client.sMembers(bucketKey);
      for (const clusterId of clusterIds) {
        candidateClusterIds.add(clusterId);
      }
    }
    
    if (candidateClusterIds.size === 0) {
      return [];
    }
    
    const matches: DuplicateMatch[] = [];
    
    for (const clusterId of candidateClusterIds) {
      const clusterMeta = await this.getClusterMetadata(clusterId);
      if (!clusterMeta) continue;
      
      const canonicalHash = await client.hGetAll(`image:hashes:${clusterMeta.canonicalSha256}`);
      if (!canonicalHash.phash) continue;
      
      const canonicalPhash = BigInt(canonicalHash.phash);
      const canonicalDhash = canonicalHash.dhash ? BigInt(canonicalHash.dhash) : null;
      
      const phashDist = hammingDistance(hashes.phash, canonicalPhash);
      
      if (phashDist <= PHASH_THRESHOLD) {
        const confidence = this.calculateConfidence(phashDist, 64);
        matches.push({
          mediaId: clusterMeta.canonicalMediaId,
          clusterId,
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
            clusterId,
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
      const similarity = this.clipEmbedder.cosineSimilarity(queryEmbedding, canonicalEmbedding);
      
      return similarity >= CLIP_THRESHOLD ? similarity : null;
    } catch (error) {
      console.error('CLIP similarity check failed:', error);
      return null;
    }
  }

  async storeClipEmbedding(sha256: string, embedding: number[]): Promise<void> {
    const client = getValkeyClient();
    const key = `clip:embedding:${sha256}`;
    await client.set(key, JSON.stringify(embedding));
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
  }

  calculateConfidence(hammingDistance: number, maxDistance: number = 64): number {
    return Math.max(0.0, 1.0 - hammingDistance / maxDistance);
  }
}

