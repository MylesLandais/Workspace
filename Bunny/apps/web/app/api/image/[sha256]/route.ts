import { NextRequest, NextResponse } from "next/server";
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";
import { Readable } from "stream";

const S3_ENDPOINT =
  process.env.MINIO_ENDPOINT || "http://host.docker.internal:9000";
const S3_REGION = process.env.MINIO_REGION || "us-east-1";
const S3_BUCKET = process.env.MINIO_BUCKET || "random";

interface RouteContext {
  params: Promise<{
    sha256: string;
  }>;
}

export async function GET(request: NextRequest, context: RouteContext) {
  try {
    const { sha256 } = await context.params;

    if (!sha256) {
      console.error("[Image Proxy] Missing SHA256 parameter");
      return NextResponse.json(
        { error: "SHA256 parameter required" },
        { status: 400 },
      );
    }

    console.log(
      `[Image Proxy] Fetching image for SHA256: ${sha256.substring(0, 16)}...`,
    );

    // Get storage path from query param
    const searchParams = request.nextUrl.searchParams;
    const s3Key = searchParams.get("path");

    if (!s3Key) {
      console.error("[Image Proxy] Missing path parameter");
      return NextResponse.json(
        { error: "Storage path parameter required" },
        { status: 400 },
      );
    }

    console.log(`[Image Proxy] S3 Key: ${s3Key}`);

    const accessKeyId = process.env.MINIO_ACCESS_KEY;
    const secretAccessKey = process.env.MINIO_SECRET_KEY;

    if (!accessKeyId || !secretAccessKey) {
      console.error("[Image Proxy] Missing MinIO credentials");
      return NextResponse.json(
        { error: "MinIO credentials not configured" },
        { status: 500 },
      );
    }

    // Create S3 client
    const s3Client = new S3Client({
      endpoint: S3_ENDPOINT,
      region: S3_REGION,
      credentials: {
        accessKeyId,
        secretAccessKey,
      },
      forcePathStyle: true,
    });

    console.log(`[Image Proxy] Fetching image from MinIO...`);

    // Fetch actual image from MinIO using direct S3 client
    let imageBuffer: Buffer = Buffer.alloc(0);
    let contentType: string = "image/jpeg";
    let fetched = false;

    // Try original storage path first
    try {
      const command = new GetObjectCommand({
        Bucket: S3_BUCKET,
        Key: s3Key,
      });

      const response = await s3Client.send(command);
      const chunks: Uint8Array[] = [];

      if (response.Body) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        for await (const chunk of response.Body as any) {
          chunks.push(chunk);
        }
      }

      imageBuffer = Buffer.concat(chunks);
      contentType = response.ContentType || "image/jpeg";
      fetched = true;

      console.log(
        `[Image Proxy] Successfully fetched image (${contentType}, ${imageBuffer.byteLength} bytes)`,
      );
    } catch (error) {
      if (
        error &&
        typeof error === "object" &&
        "name" in error &&
        error.name === "NoSuchKey"
      ) {
        console.log(
          `[Image Proxy] Original path not found, trying SHA256-based path...`,
        );

        // Try SHA256-based path as fallback
        const possibleExts = ["jpg", "jpeg", "png", "webp", "gif"];
        for (const ext of possibleExts) {
          // Unused prefix variable removed
          const fallbackKey = `${sha256.substring(0, 8)}/${sha256}.${ext}`;

          try {
            const fallbackCommand = new GetObjectCommand({
              Bucket: S3_BUCKET,
              Key: fallbackKey,
            });
            const response = await s3Client.send(fallbackCommand);
            const chunks: Uint8Array[] = [];

            if (response.Body) {
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              for await (const chunk of response.Body as any) {
                chunks.push(chunk);
              }
            }

            imageBuffer = Buffer.concat(chunks);
            contentType = response.ContentType || "image/jpeg";
            fetched = true;

            console.log(
              `[Image Proxy] Successfully fetched image from fallback path (${contentType}, ${imageBuffer.byteLength} bytes)`,
            );
            break;
          } catch (fallbackError) {
            if (
              fallbackError &&
              typeof fallbackError === "object" &&
              "name" in fallbackError &&
              fallbackError.name !== "NoSuchKey"
            ) {
              console.error(
                `[Image Proxy] Error fetching from fallback path:`,
                fallbackError,
              );
            }
          }
        }

        if (!fetched) {
          throw new Error(
            `Image not found in S3 (tried original path and all SHA256-based paths)`,
          );
        }
      } else {
        console.error(`[Image Proxy] Failed to fetch image:`, error);
        throw error;
      }
    }

    // Return image with proper headers
    return new NextResponse(new Uint8Array(imageBuffer), {
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "public, max-age=3600, immutable",
      },
    });
  } catch (error) {
    console.error("[Image Proxy] CRITICAL ERROR:", error);
    if (error instanceof Error) {
      console.error("[Image Proxy] Error message:", error.message);
      console.error("[Image Proxy] Error stack:", error.stack);
    }
    return NextResponse.json(
      {
        error: "Internal server error",
        message: error instanceof Error ? error.message : String(error),
      },
      { status: 500 },
    );
  }
}
