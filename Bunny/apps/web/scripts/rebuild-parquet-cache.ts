import "dotenv/config";
import { writeFileSync, existsSync, readdirSync, readFileSync } from "fs";
import { join } from "path";

const JUPYTER_CACHE = "/home/warby/Workspace/jupyter/cache";
const PARQUET_DIR =
  "/home/warby/Workspace/Bunny/app/client/public/parquet-images";
const OUTPUT_PATH =
  "/home/warby/Workspace/Bunny/app/client/public/parquet-cache/feed-data.json";

interface Thread {
  board: string;
  thread_id: string;
  url: string;
  title: string;
  post_count: string;
  image_count: string;
  html_path: string;
  html_filename: string;
  file_size: string;
  file_modified: string;
  cached_at: string;
}

interface Image {
  sha256: string;
  local_path: string;
  relative_path: string;
  filename: string;
  file_size: string;
  file_modified: string;
  cached_at: string;
}

interface ParquetCache {
  metadata: {
    generatedAt: string;
    totalThreads: number;
    totalImages: number;
    source: string;
  };
  threads: Thread[];
  images: Image[];
  threadImageMapping: Record<string, Image[]>;
}

function getFileModified(path: string): string {
  try {
    const stats = require("fs").statSync(path);
    return stats.mtime.toISOString();
  } catch {
    return new Date().toISOString();
  }
}

function extractTitleFromHtml(html: string): string {
  const titleMatch = html.match(/<title>\/b\/ - ([^-]+) -/);
  if (titleMatch && titleMatch[1]) {
    return titleMatch[1].trim();
  }
  return "";
}

function extractSubjectFromHtml(html: string): string {
  const subjectMatch = html.match(/<span class="subject">([^<]+)<\/span>/);
  if (subjectMatch && subjectMatch[1]) {
    return subjectMatch[1].trim();
  }
  return "";
}

async function main() {
  console.log("=== Building Parquet Cache from Local Files ===\n");

  const existingThreads: Thread[] = [];
  const allImages: Image[] = [];
  const threadImageMapping: Record<string, Image[]> = {};

  const jupyterImageboardDir = join(JUPYTER_CACHE, "imageboard/images/b");
  const jupyterHtmlDir = join(JUPYTER_CACHE, "imageboard/html");

  if (!existsSync(jupyterImageboardDir)) {
    console.error(
      `Jupyter imageboard directory not found: ${jupyterImageboardDir}`,
    );
    process.exit(1);
  }

  const threadDirs = readdirSync(jupyterImageboardDir).filter((f) => {
    const path = join(jupyterImageboardDir, f);
    return require("fs").statSync(path).isDirectory();
  });

  console.log(
    `Found ${threadDirs.length} thread directories in Jupyter cache\n`,
  );

  for (const threadId of threadDirs) {
    const threadPath = join(jupyterImageboardDir, threadId);
    const files = readdirSync(threadPath).filter(
      (f) => f.endsWith(".jpg") || f.endsWith(".png") || f.endsWith(".webp"),
    );

    if (files.length === 0) continue;

    const images: Image[] = files.map((filename) => {
      const sha256 = filename.replace(/\.(jpg|png|webp)$/, "");
      return {
        sha256,
        local_path: `imageboard/b/${threadId}/${filename}`,
        relative_path: filename,
        filename,
        file_size: require("fs")
          .statSync(join(threadPath, filename))
          .size.toString(),
        file_modified: getFileModified(join(threadPath, filename)),
        cached_at: getFileModified(join(threadPath, filename)),
      };
    });

    allImages.push(...images);
    threadImageMapping[threadId] = images;

    const htmlPath = join(jupyterHtmlDir, `b_${threadId}.html`);
    let title = "";
    let subject = "";

    if (existsSync(htmlPath)) {
      try {
        const html = readFileSync(htmlPath, "utf-8");
        title = extractTitleFromHtml(html);
        subject = extractSubjectFromHtml(html);
      } catch (e) {
        console.warn(`Failed to parse HTML for thread ${threadId}`);
      }
    }

    const displayTitle = subject || title || `Thread ${threadId}`;

    existingThreads.push({
      board: "b",
      thread_id: threadId,
      url: `https://boards.4chan.org/b/thread/${threadId}`,
      title: displayTitle,
      post_count: files.length.toString(),
      image_count: files.length.toString(),
      html_path: `imageboard/html/b_${threadId}.html`,
      html_filename: `b_${threadId}.html`,
      file_size: "0",
      file_modified: new Date().toISOString(),
      cached_at: new Date().toISOString(),
    });
  }

  if (existsSync(PARQUET_DIR)) {
    const parquetFiles = readdirSync(PARQUET_DIR).filter(
      (f) => f.endsWith(".jpg") || f.endsWith(".png") || f.endsWith(".webp"),
    );
    console.log(`Found ${parquetFiles.length} files in parquet-images\n`);

    for (const filename of parquetFiles) {
      const sha256 = filename.replace(/\.(jpg|png|webp)$/, "");
      const existingIndex = allImages.findIndex((img) => img.sha256 === sha256);

      if (existingIndex === -1) {
        allImages.push({
          sha256,
          local_path: `parquet-images/${filename}`,
          relative_path: filename,
          filename,
          file_size: require("fs")
            .statSync(join(PARQUET_DIR, filename))
            .size.toString(),
          file_modified: getFileModified(join(PARQUET_DIR, filename)),
          cached_at: getFileModified(join(PARQUET_DIR, filename)),
        });
      }
    }
  }

  const cache: ParquetCache = {
    metadata: {
      generatedAt: new Date().toISOString(),
      totalThreads: existingThreads.length,
      totalImages: allImages.length,
      source: "local-filesystem",
    },
    threads: existingThreads,
    images: allImages,
    threadImageMapping,
  };

  writeFileSync(OUTPUT_PATH, JSON.stringify(cache, null, 2));

  console.log("=== Cache Built Successfully ===");
  console.log(`  - ${cache.metadata.totalThreads} threads`);
  console.log(`  - ${cache.metadata.totalImages} images`);
  console.log(
    `  - ${Object.keys(cache.threadImageMapping).length} thread-image mappings`,
  );
  console.log(`\nOutput: ${OUTPUT_PATH}`);
}

main().catch(console.error);
