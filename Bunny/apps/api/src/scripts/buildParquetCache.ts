import "dotenv/config";
import { readFileSync, writeFileSync } from "fs";
import { join } from "path";
import { parquetRead } from "hyparquet";

const PACKS_DIR = "/home/warby/Workspace/jupyter/packs";
const LATEST_PACK = "nightly-2026-01-02";
const OUTPUT_DIR =
  "/home/warby/Workspace/Bunny/app/client/public/parquet-cache";

interface Thread {
  board: string;
  thread_id: bigint;
  url: string;
  title: string;
  post_count: bigint;
  image_count: bigint;
  html_path: string;
  html_filename: string;
  file_size: bigint;
  file_modified: string;
  cached_at: string;
}

interface Image {
  sha256: string;
  local_path: string;
  relative_path: string;
  filename: string;
  file_size: bigint;
  file_modified: string;
  cached_at: string;
}

async function readParquet<T>(fileName: string): Promise<T[]> {
  const filePath = join(PACKS_DIR, LATEST_PACK, fileName);
  console.log(`Reading ${filePath}...`);

  const buffer = readFileSync(filePath);

  return new Promise((resolve, reject) => {
    parquetRead({
      file: {
        byteLength: buffer.byteLength,
        async slice(offset, end) {
          return buffer.buffer.slice(
            buffer.byteOffset + offset,
            buffer.byteOffset + end,
          );
        },
      },
      rowFormat: "object",
      onComplete: (data) => {
        console.log(`✓ Read ${data.length} rows from ${fileName}`);
        resolve(data as T[]);
      },
    }).catch(reject);
  });
}

// Convert BigInt values to strings for JSON serialization
function convertBigInts(obj: any): any {
  if (typeof obj === "bigint") {
    return obj.toString();
  } else if (Array.isArray(obj)) {
    return obj.map(convertBigInts);
  } else if (obj && typeof obj === "object") {
    const result: any = {};
    for (const [key, value] of Object.entries(obj)) {
      result[key] = convertBigInts(value);
    }
    return result;
  }
  return obj;
}

async function main() {
  try {
    console.log("=== Parquet to JSON Cache Builder ===");

    const [threads, images] = await Promise.all([
      readParquet<Thread>("threads.parquet"),
      readParquet<Image>("images.parquet"),
    ]);

    // Group images by thread (using a simple hash-based approach)
    const threadImages = new Map<string, Image[]>();

    // For each unique thread, assign a subset of images
    const uniqueThreads = Array.from(
      new Set(threads.map((t) => t.thread_id.toString())),
    );
    console.log(
      `Found ${uniqueThreads.length} unique threads out of ${threads.length} total`,
    );

    uniqueThreads.forEach((threadId, index) => {
      const imagesPerThread = Math.max(
        1,
        Math.floor(images.length / uniqueThreads.length),
      );
      const startIndex = (index * imagesPerThread) % images.length;
      const endIndex = Math.min(startIndex + imagesPerThread, images.length);

      const assignedImages = images.slice(startIndex, endIndex);
      threadImages.set(threadId, assignedImages);
      console.log(
        `Thread ${threadId}: assigned ${assignedImages.length} images`,
      );
    });

    // Create processed data structure
    const threadMappingObj: Record<string, any> = {};
    for (const [threadId, imgs] of threadImages.entries()) {
      threadMappingObj[threadId] = convertBigInts(imgs);
    }

    console.log(
      `Thread mapping has ${Object.keys(threadMappingObj).length} entries`,
    );

    const processedData = {
      metadata: {
        generatedAt: new Date().toISOString(),
        totalThreads: threads.length,
        totalImages: images.length,
        source: LATEST_PACK,
      },
      threads: convertBigInts(threads),
      images: convertBigInts(images),
      threadImageMapping: threadMappingObj,
    };

    // Write the cache file
    const outputPath = join(OUTPUT_DIR, "feed-data.json");
    writeFileSync(outputPath, JSON.stringify(processedData, null, 2));

    console.log(`✓ Cache written to ${outputPath}`);
    console.log(`  - ${threads.length} threads`);
    console.log(`  - ${images.length} images`);
    console.log(
      `  - ${Object.keys(threadMappingObj).length} thread-image mappings`,
    );
  } catch (error) {
    console.error("Failed to build cache:", error);
    process.exit(1);
  }
}

main();
