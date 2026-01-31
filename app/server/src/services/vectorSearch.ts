import { getValkeyClient } from "../valkey/client.js";
import logger from "../lib/logger.js";

export class VectorSearchService {
  private static INDEX_NAME = "idx:clip_embeddings";
  private static PREFIX = "clip:embedding:";
  private static VECTOR_DIM = 512;
  private static DISTANCE_METRIC = "COSINE";

  async initializeIndex(): Promise<void> {
    const client = getValkeyClient();

    try {
      await client.ft.dropIndex(VectorSearchService.INDEX_NAME);
    } catch (err) {}

    await (client.ft as any).create(
      VectorSearchService.INDEX_NAME,
      {
        vector: {
          type: "VECTOR",
          ALGORITHM: "HNSW",
          TYPE: "FLOAT32",
          DIM: VectorSearchService.VECTOR_DIM,
          DISTANCE_METRIC: VectorSearchService.DISTANCE_METRIC,
          INITIAL_CAP: 10000,
          M: 16,
          EF_CONSTRUCTION: 64,
        },
        sha256: {
          type: "TAG",
          AS: "sha256",
        },
      },
      {
        ON: "HASH",
        PREFIX: VectorSearchService.PREFIX,
      },
    );
  }

  async storeEmbedding(sha256: string, embedding: number[]): Promise<void> {
    const client = getValkeyClient();
    const key = `${VectorSearchService.PREFIX}${sha256}`;

    const vectorBuffer = this.float32ArrayToBuffer(new Float32Array(embedding));

    await client.hSet(key, {
      vector: vectorBuffer,
      sha256: sha256,
    });
  }

  async searchSimilar(
    embedding: number[],
    limit: number = 10,
    threshold: number = 0.95,
  ): Promise<Array<{ sha256: string; similarity: number }>> {
    const client = getValkeyClient();
    const vectorBuffer = this.float32ArrayToBuffer(new Float32Array(embedding));

    const searchParams = {
      query_vector: vectorBuffer,
    };

    const query = `*=>[KNN ${limit} @vector $query_vector AS score]`;

    try {
      const result = await client.ft.search(
        VectorSearchService.INDEX_NAME,
        query,
        {
          PARAMS: searchParams,
          LIMIT: { from: 0, size: limit },
          RETURN: ["sha256"],
          DIALECT: 2,
        },
      );

      const matches: Array<{ sha256: string; similarity: number }> = [];

      for (const doc of result.documents) {
        const sha256 = doc.value.sha256 as string;
        const score = (doc as any).score as number;
        const similarity = 1 - score;

        if (similarity >= threshold) {
          matches.push({ sha256, similarity });
        }
      }

      return matches;
    } catch (error) {
      logger.error("Vector search failed", error);
      return [];
    }
  }

  async getEmbedding(sha256: string): Promise<number[] | null> {
    const client = getValkeyClient();
    const key = `${VectorSearchService.PREFIX}${sha256}`;

    const data = await client.hGet(key, "vector");
    if (!data) return null;

    return this.bufferToFloat32Array(Buffer.from(data));
  }

  private float32ArrayToBuffer(array: Float32Array): Buffer {
    return Buffer.from(array.buffer);
  }

  private bufferToFloat32Array(buffer: Buffer): number[] {
    const float32Array = new Float32Array(
      buffer.buffer,
      buffer.byteOffset,
      buffer.byteLength / Float32Array.BYTES_PER_ELEMENT,
    );
    return Array.from(float32Array);
  }
}
