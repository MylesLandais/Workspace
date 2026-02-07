import "dotenv/config";
import {
  S3Client,
  ListObjectsV2Command,
  GetObjectCommand,
  GetObjectTaggingCommand,
} from "@aws-sdk/client-s3";
import { getStorageBackend } from "../services/storage.js";
import { ImageHasher } from "../services/imageHasher.js";
import { DuplicateDetector } from "../services/duplicateDetector.js";
import { ClipEmbedder } from "../services/clipEmbedder.js";
import { getSession } from "../neo4j/driver.js";
import {
  createMediaWithHashes,
  linkMediaToCluster,
  setCanonicalImage,
  createImageCluster,
} from "../neo4j/queries/images.js";
import { v4 as uuidv4 } from "uuid";

interface S3Object {
  key: string;
  size: number;
  lastModified: Date;
  tags: Record<string, string>;
}

async function listBucketObjects(bucket: string): Promise<S3Object[]> {
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
  const objects: S3Object[] = [];

  let continuationToken: string | undefined;

  do {
    const command = new ListObjectsV2Command({
      Bucket: bucket,
      ContinuationToken: continuationToken,
    });

    const response = await client.send(command);

    if (response.Contents) {
      for (const obj of response.Contents) {
        if (!obj.Key) continue;

        const tagsCommand = new GetObjectTaggingCommand({
          Bucket: bucket,
          Key: obj.Key,
        });

        let tags: Record<string, string> = {};
        try {
          const tagsResponse = await client.send(tagsCommand);
          if (tagsResponse.TagSet) {
            tags = tagsResponse.TagSet.reduce(
              (acc, tag) => {
                if (tag.Key && tag.Value) {
                  acc[tag.Key] = tag.Value;
                }
                return acc;
              },
              {} as Record<string, string>,
            );
          }
        } catch (error) {
          console.log(`No tags for ${obj.Key}`);
        }

        objects.push({
          key: obj.Key,
          size: obj.Size || 0,
          lastModified: obj.LastModified || new Date(),
          tags,
        });
      }
    }

    continuationToken = response.NextContinuationToken;
  } while (continuationToken);

  return objects;
}

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

async function createMediaNodeFromS3Object(
  obj: S3Object,
  bucket: string,
): Promise<void> {
  const session = getSession();

  try {
    console.log(`Processing: ${obj.key}`);

    const isImage = /\.(jpg|jpeg|png|webp|gif)$/i.test(obj.key);
    const isVideo = /\.(mp4|mov|avi|mkv|webm)$/i.test(obj.key);

    if (!isImage && !isVideo) {
      console.log(`  Skipping non-media file: ${obj.key}`);
      return;
    }

    if (isVideo) {
      console.log(`  Skipping video (not yet supported): ${obj.key}`);
      return;
    }

    const buffer = await downloadObject(bucket, obj.key);
    console.log(`  Downloaded ${buffer.length} bytes`);

    const hasher = new ImageHasher();
    const hashes = await hasher.computeHashesFromBuffer(buffer);
    console.log(
      `  Computed hashes: SHA256=${hashes.sha256.substring(0, 12)}...`,
    );

    const duplicateDetector = new DuplicateDetector();
    const exactDuplicate = await duplicateDetector.checkExactDuplicate(
      hashes.sha256,
    );

    if (exactDuplicate) {
      console.log(`  Duplicate found, skipping: ${exactDuplicate}`);
      return;
    }

    const nearDuplicates = await duplicateDetector.findNearDuplicates(hashes);
    let clusterId: string;

    if (nearDuplicates.length > 0) {
      clusterId = nearDuplicates[0].clusterId;
      console.log(`  Near duplicate found, using cluster: ${clusterId}`);
    } else {
      clusterId = await createImageCluster(hashes.sha256, obj.lastModified);
      console.log(`  Creating new cluster: ${clusterId}`);
    }

    const storage = getStorageBackend();
    const imageUrl = await storage.getPresignedUrl(
      hashes.sha256,
      hashes.mimeType,
    );

    const title =
      obj.tags.title || obj.tags.name || obj.key.split("/").pop() || "Untitled";
    const platform = obj.tags.platform || obj.tags.source || "imageboard";
    const author = obj.tags.author || obj.tags.creator || "♣";
    const publishDate = obj.tags.publishDate || obj.lastModified.toISOString();

    const mediaId = await createMediaWithHashes({
      sha256: hashes.sha256,
      phash: hashes.phash,
      dhash: hashes.dhash,
      width: hashes.width,
      height: hashes.height,
      sizeBytes: buffer.length,
      mimeType: hashes.mimeType,
      url: imageUrl,
      storagePath: obj.key,
      createdAt: obj.lastModified,
    });

    console.log(`  Created Media node: ${mediaId}`);

    await linkMediaToCluster(mediaId, clusterId, 1.0);
    await setCanonicalImage(clusterId, mediaId);

    await duplicateDetector.storeHashMapping(
      hashes.sha256,
      hashes.phash,
      hashes.dhash,
      clusterId,
      mediaId,
    );

    const tags = obj.tags.tags
      ? obj.tags.tags.split(",").map((t) => t.trim())
      : [];

    const postId = uuidv4();
    const createPostQuery = `
      MATCH (m:Media {id: $mediaId})
      CREATE (p:Post {
        id: $postId,
        title: $title,
        created_at: datetime($publishDate),
        created_utc: $createdUtc,
        source_url: $sourceUrl
      })
      CREATE (m)-[:APPEARED_IN]->(p)
      WITH p
      FOREACH (tag IN $tags |
        MERGE (t:Tag {name: tag})
        CREATE (p)-[:HAS_TAG]->(t)
      )
      RETURN p.id as postId
    `;

    await session.run(createPostQuery, {
      mediaId,
      postId,
      title,
      publishDate,
      createdUtc: Math.floor(obj.lastModified.getTime() / 1000),
      sourceUrl: obj.tags.sourceUrl || `s3://${bucket}/${obj.key}`,
      tags,
    });

    if (obj.tags.platform || obj.tags.source) {
      const platformValue = obj.tags.platform || obj.tags.source;
      const handleQuery = `
        MATCH (p:Post {id: $postId})
        MERGE (h:Handle {
          platform: $platform,
          handle: $handle,
          username: $username
        })
        CREATE (p)-[:HAS_SOURCE]->(h)
      `;

      await session.run(handleQuery, {
        postId,
        platform: platformValue.toUpperCase(),
        handle: obj.tags.handle || author,
        username: author,
      });
    }

    if (obj.tags.subreddit) {
      const subredditQuery = `
        MATCH (p:Post {id: $postId})
        MERGE (s:Subreddit {name: $subreddit})
        ON CREATE SET s.display_name = $displayName
        CREATE (p)-[:POSTED_IN]->(s)
      `;

      await session.run(subredditQuery, {
        postId,
        subreddit: obj.tags.subreddit,
        displayName: obj.tags.subredditDisplay || obj.tags.subreddit,
      });
    }

    if (author !== "Unknown") {
      const authorQuery = `
        MATCH (p:Post {id: $postId})
        MERGE (u:User {username: $username})
        CREATE (p)-[:AUTHORED_BY]->(u)
      `;

      await session.run(authorQuery, {
        postId,
        username: author,
      });
    }

    if (obj.tags.entities) {
      const entities = obj.tags.entities.split(",").map((e) => e.trim());
      const entityQuery = `
        MATCH (m:Media {id: $mediaId})
        FOREACH (entityName IN $entities |
          MERGE (e:Entity {name: entityName, type: 'person'})
          CREATE (m)-[:RELATED_TO]->(e)
        )
      `;

      await session.run(entityQuery, {
        mediaId,
        entities,
      });
    }

    console.log(`  Successfully ingested: ${obj.key}`);
  } catch (error) {
    console.error(`  Error processing ${obj.key}:`, error);
  } finally {
    await session.close();
  }
}

async function main() {
  const bucket = process.env.S3_BUCKET;

  if (!bucket) {
    console.error("S3_BUCKET environment variable not set");
    process.exit(1);
  }

  console.log(`Starting ingestion from bucket: ${bucket}`);
  console.log("---");

  const objects = await listBucketObjects(bucket);
  console.log(`Found ${objects.length} objects in bucket`);
  console.log("---");

  for (const obj of objects) {
    await createMediaNodeFromS3Object(obj, bucket);
  }

  console.log("---");
  console.log("Ingestion complete!");
  process.exit(0);
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
