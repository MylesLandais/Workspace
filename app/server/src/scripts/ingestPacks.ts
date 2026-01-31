import "dotenv/config";
import { readFileSync, existsSync, writeFileSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { parquetRead } from "hyparquet";
import {
  ImageIngestionService,
  IngestionMetadata,
} from "../services/imageIngestion.js";
import { getSession } from "../neo4j/driver.js";

async function readParquet(path: string): Promise<any[]> {
  const buffer = readFileSync(path);
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
      onComplete: (data) => resolve(data),
    }).catch(reject);
  });
}

async function downloadImage(url: string): Promise<Buffer | null> {
  try {
    const response = await fetch(url);
    if (!response.ok) return null;
    return Buffer.from(await response.arrayBuffer());
  } catch (error) {
    console.error(`    Failed to download image from ${url}:`, error);
    return null;
  }
}

async function ingestImageboardPack(
  packPath: string,
  ingestionService: ImageIngestionService,
  limit?: number,
) {
  console.log(`\n=== Ingesting Imageboard Pack: ${packPath} ===`);

  const imagesPath = join(packPath, "images.parquet");
  const threadsPath = join(packPath, "threads.parquet");

  const images = await readParquet(imagesPath);
  const threads = await readParquet(threadsPath);

  const subset = limit ? images.slice(0, limit) : images;
  console.log(
    `Found ${images.length} images (processing ${subset.length}) and ${threads.length} threads`,
  );

  const threadMap = new Map();
  for (const thread of threads) {
    threadMap.set(`${thread.board}_${thread.thread_id}`, thread);
  }

  const fullPackPath = packPath.includes("-full")
    ? packPath
    : packPath.replace(/nightly-(\d{4}-\d{2}-\d{2})/, "nightly-$1-full");

  let success = 0;
  let failed = 0;

  for (let i = 0; i < subset.length; i++) {
    const img = subset[i];
    try {
      const parts = img.relative_path.split("/");
      const board = parts[0];
      const threadId = parts[1];
      const thread = threadMap.get(`${board}_${threadId}`);

      const localPath = join(fullPackPath, "images", img.relative_path);

      if (!existsSync(localPath)) {
        console.warn(`  Image not found: ${localPath}`);
        failed++;
        continue;
      }

      const imageBuffer = readFileSync(localPath);
      const metadata: IngestionMetadata = {
        postId: `ib_${board}_${threadId}`,
        title: thread?.title || img.filename,
        createdAt: new Date(img.cached_at || Date.now()),
        subreddit: board,
        author: "anonymous",
      };

      process.stdout.write(
        `  [${i + 1}/${subset.length}] Ingesting ${img.filename}... `,
      );
      await ingestionService.ingestImage(imageBuffer, metadata);
      process.stdout.write("DONE\n");
      success++;
    } catch (error) {
      console.error(`ERROR:`, error);
      failed++;
    }
  }
  console.log(`Summary: ${success} succeeded, ${failed} failed`);
}

async function ingestRedditPack(
  packPath: string,
  ingestionService: ImageIngestionService,
  limit?: number,
) {
  console.log(`\n=== Ingesting Reddit Pack: ${packPath} ===`);

  const imagesPath = join(packPath, "images.parquet");
  const postsPath = join(packPath, "posts.parquet");

  const images = await readParquet(imagesPath);
  const posts = await readParquet(postsPath);

  const subset = limit ? images.slice(0, limit) : images;
  console.log(
    `Found ${images.length} images (processing ${subset.length}) and ${posts.length} posts`,
  );

  const postMap = new Map();
  for (const post of posts) {
    postMap.set(post.id, post);
  }

  const localImagesDir = join(packPath, "images");
  if (!existsSync(localImagesDir)) {
    mkdirSync(localImagesDir, { recursive: true });
  }

  let success = 0;
  let failed = 0;
  let downloaded = 0;

  for (let i = 0; i < subset.length; i++) {
    const img = subset[i];
    try {
      const post = postMap.get(img.post_id);

      let imageBuffer: Buffer | null = null;
      const fileName =
        img.image_url.split("/").pop()?.split("?")[0] || `${img.post_id}.jpg`;
      const localPath = join(localImagesDir, fileName);

      if (existsSync(localPath)) {
        imageBuffer = readFileSync(localPath);
      } else {
        process.stdout.write(
          `  [${i + 1}/${subset.length}] Downloading ${img.post_id}... `,
        );
        imageBuffer = await downloadImage(img.image_url);
        if (imageBuffer) {
          writeFileSync(localPath, imageBuffer);
          process.stdout.write("DONE\n");
          downloaded++;
        } else {
          process.stdout.write("FAILED\n");
        }
      }

      if (!imageBuffer) {
        failed++;
        continue;
      }

      const metadata: IngestionMetadata = {
        postId: img.post_id,
        title: post?.title || img.title,
        createdAt: new Date(img.created_utc || Date.now()),
        subreddit: img.subreddit,
        author: post?.author || "Unknown",
      };

      process.stdout.write(`  Ingesting ${img.post_id} into graph & S3... `);
      await ingestionService.ingestImage(imageBuffer, metadata);
      process.stdout.write("DONE\n");
      success++;
    } catch (error) {
      console.error(`ERROR:`, error);
      failed++;
    }
  }
  console.log(
    `Summary: ${success} succeeded (${downloaded} newly downloaded), ${failed} failed`,
  );
}

async function main() {
  const ingestionService = new ImageIngestionService();

  const ibPackPath = "/home/warby/Workspace/jupyter/packs/nightly-2026-01-02";
  const redditPackPath =
    "/home/warby/Workspace/jupyter/packs/reddit-nightly-2026-01-03";

  const limit = 5; // Test limit

  try {
    await ingestImageboardPack(ibPackPath, ingestionService, limit);
  } catch (e) {
    console.error("Failed to ingest Imageboard pack:", e);
  }

  try {
    await ingestRedditPack(redditPackPath, ingestionService, limit);
  } catch (e) {
    console.error("Failed to ingest Reddit pack:", e);
  }

  console.log("\nIngestion complete!");
  process.exit(0);
}

main().catch(console.error);
