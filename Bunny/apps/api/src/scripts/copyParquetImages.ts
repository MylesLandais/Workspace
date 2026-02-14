import "dotenv/config";
import { readFileSync, writeFileSync, mkdirSync, copyFileSync } from "fs";
import { join, dirname } from "path";
import { parquetRead } from "hyparquet";

const PACKS_DIR = "/home/warby/Workspace/jupyter/packs";
const LATEST_PACK = "nightly-2026-01-02";
const OUTPUT_DIR =
  "/home/warby/Workspace/Bunny/app/client/public/parquet-images";

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

async function copyImagesToPublic() {
  try {
    console.log("=== Parquet Images Copy Utility ===");

    // Create output directory if it doesn't exist
    mkdirSync(OUTPUT_DIR, { recursive: true });

    const images = await readParquet<Image>("images.parquet");

    let copied = 0;
    let skipped = 0;

    for (const image of images.slice(0, 100)) {
      // Limit to first 100 images for testing
      const sourcePath = join(
        PACKS_DIR,
        `${LATEST_PACK}-full/images`,
        image.filename,
      );
      const destPath = join(OUTPUT_DIR, image.filename);

      try {
        // Try to find the image in the full pack directory
        copyFileSync(sourcePath, destPath);
        copied++;
        process.stdout.write(`✓ Copied ${image.filename}\n`);
      } catch (error) {
        skipped++;
        process.stdout.write(`✗ Skipped ${image.filename} (not found)\n`);
      }
    }

    console.log(`\nSummary: ${copied} copied, ${skipped} skipped`);
  } catch (error) {
    console.error("Failed to copy images:", error);
    process.exit(1);
  }
}

copyImagesToPublic();
