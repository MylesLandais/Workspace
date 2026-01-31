import "dotenv/config";
import {
  S3Client,
  ListObjectsV2Command,
  GetObjectCommand,
} from "@aws-sdk/client-s3";
import { getStorageBackend } from "../services/storage.js";
import { ImageHasher } from "../services/imageHasher.js";
import { DuplicateDetector } from "../services/duplicateDetector.js";
import { getSession } from "../neo4j/driver.js";
import {
  createMediaWithHashes,
  linkMediaToCluster,
  setCanonicalImage,
} from "../neo4j/queries/images.js";
import { v4 as uuidv4 } from "uuid";

async function downloadObject(bucket: string, key: string): Promise<Buffer> {
  const endpoint = process.env.S3_ENDPOINT;
  const region = process.env.S3_REGION || "us-east-1";

  const clientConfig: any = {
    region,
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID || "",
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || "",
    },
  };

  if (endpoint) {
    clientConfig.endpoint = endpoint;
    clientConfig.forcePathStyle = true;
  }

  const client = new S3Client(clientConfig);

  const command = new GetObjectCommand({
    Bucket: bucket,
    Key: key,
  });

  const response = await client.send(command);

  if (!response.Body) {
    throw new Error(`No body returned for ${key}`);
  }

  const chunks: Uint8Array[] = [];
  for await (const chunk of response.Body as any) {
    chunks.push(chunk);
  }

  return Buffer.concat(chunks);
}

async function main() {
  console.log("Testing single image ingestion...");

  const bucket = "random";
  const key = "1760720529496212.jpg"; // First image from the bucket

  console.log(`Downloading: ${key}`);
  const buffer = await downloadObject(bucket, key);
  console.log(`Downloaded ${buffer.length} bytes`);

  const hasher = new ImageHasher();
  const hashes = await hasher.computeHashesFromBuffer(buffer);
  console.log(`Hashes: SHA256=${hashes.sha256.substring(0, 12)}...`);

  const duplicateDetector = new DuplicateDetector();
  const exactDuplicate = await duplicateDetector.checkExactDuplicate(
    hashes.sha256,
  );

  if (exactDuplicate) {
    console.log(`Duplicate found: ${exactDuplicate}`);
    return;
  }

  const clusterId = uuidv4();
  console.log(`Created cluster: ${clusterId}`);

  const storage = getStorageBackend();
  const imageUrl = await storage.getPresignedUrl(
    hashes.sha256,
    hashes.mimeType,
  );
  console.log(`Generated presigned URL: ${imageUrl.substring(0, 60)}...`);

  console.log("Creating Media node in Neo4j...");
  const mediaId = await createMediaWithHashes({
    sha256: hashes.sha256,
    phash: hashes.phash,
    dhash: hashes.dhash,
    width: hashes.width,
    height: hashes.height,
    sizeBytes: buffer.length,
    mimeType: hashes.mimeType,
    url: imageUrl,
    storagePath: key,
    createdAt: new Date(),
  });
  console.log(`Created Media node: ${mediaId}`);

  console.log("Linking to cluster...");
  await linkMediaToCluster(mediaId, clusterId, 1.0);
  await setCanonicalImage(clusterId, mediaId);
  console.log("Cluster linked!");

  console.log("SUCCESS! Image ingested successfully.");
  process.exit(0);
}

main().catch((error) => {
  console.error("FATAL ERROR:", error);
  console.error("Stack:", error.stack);
  process.exit(1);
});
