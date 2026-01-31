import { pipeline, env } from "@xenova/transformers";
import { readFileSync } from "fs";

env.allowLocalModels = false;

let clipModel: any = null;
let clipProcessor: any = null;

export class ClipEmbedder {
  private async getModel() {
    if (!clipModel) {
      clipModel = await pipeline(
        "feature-extraction",
        "Xenova/clip-vit-base-patch32",
      );
    }
    return clipModel;
  }

  async computeEmbedding(imagePath: string): Promise<number[]> {
    const model = await this.getModel();
    const imageBuffer = readFileSync(imagePath);

    const output = await model(imageBuffer, { image: true });
    return Array.from(output.data);
  }

  async computeEmbeddingFromBuffer(imageBuffer: Buffer): Promise<number[]> {
    const model = await this.getModel();
    const output = await model(imageBuffer, { image: true });
    return Array.from(output.data);
  }

  cosineSimilarity(embedding1: number[], embedding2: number[]): number {
    if (embedding1.length !== embedding2.length) {
      throw new Error("Embeddings must have the same length");
    }

    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;

    for (let i = 0; i < embedding1.length; i++) {
      dotProduct += embedding1[i] * embedding2[i];
      norm1 += embedding1[i] * embedding1[i];
      norm2 += embedding2[i] * embedding2[i];
    }

    const denominator = Math.sqrt(norm1) * Math.sqrt(norm2);
    if (denominator === 0) {
      return 0;
    }

    return dotProduct / denominator;
  }
}
