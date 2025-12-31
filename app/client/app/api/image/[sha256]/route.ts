import { NextRequest, NextResponse } from 'next/server';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';

const S3_ENDPOINT = 'http://host.docker.internal:9000';
const S3_REGION = 'us-east-1';
const S3_BUCKET = 'random';
const ACCESS_KEY_ID = 'minioadmin';
const SECRET_ACCESS_KEY = 'minioadmin';

interface RouteContext {
  params: Promise<{
    sha256: string;
  }>;
}

export async function GET(
  request: NextRequest,
  context: RouteContext
) {
  try {
    const { sha256 } = await context.params;

    if (!sha256) {
      console.error('[Image Proxy] Missing SHA256 parameter');
      return NextResponse.json(
        { error: 'SHA256 parameter required' },
        { status: 400 }
      );
    }

    console.log(`[Image Proxy] Fetching image for SHA256: ${sha256.substring(0, 16)}...`);

    // Get storage path from query param
    const searchParams = request.nextUrl.searchParams;
    const s3Key = searchParams.get('path');

    if (!s3Key) {
      console.error('[Image Proxy] Missing path parameter');
      return NextResponse.json(
        { error: 'Storage path parameter required' },
        { status: 400 }
      );
    }

    console.log(`[Image Proxy] S3 Key: ${s3Key}`);

    // Create S3 client
    const s3Client = new S3Client({
      endpoint: S3_ENDPOINT,
      region: S3_REGION,
      credentials: {
        accessKeyId: ACCESS_KEY_ID,
        secretAccessKey: SECRET_ACCESS_KEY,
      },
      forcePathStyle: true,
    });

    // Generate presigned URL
    const command = new GetObjectCommand({
      Bucket: S3_BUCKET,
      Key: s3Key,
    });

    const presignedUrl = await getSignedUrl(s3Client, command, {
      expiresIn: 14400, // 4 hours
    });

    console.log(`[Image Proxy] Generated presigned URL, fetching image...`);

    // Fetch the actual image from MinIO
    const imageResponse = await fetch(presignedUrl);

    if (!imageResponse.ok) {
      console.error(`[Image Proxy] Failed to fetch image: ${imageResponse.status} ${imageResponse.statusText}`);
      return NextResponse.json(
        { error: 'Failed to fetch image from storage', status: imageResponse.status },
        { status: imageResponse.status }
      );
    }

    const imageBuffer = await imageResponse.arrayBuffer();
    const contentType = imageResponse.headers.get('Content-Type') || 'image/jpeg';

    console.log(`[Image Proxy] Successfully proxied image (${contentType}, ${imageBuffer.byteLength} bytes)`);

    // Return the image with proper headers
    return new NextResponse(imageBuffer, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=3600, immutable',
      },
    });
  } catch (error) {
    console.error('[Image Proxy] CRITICAL ERROR:', error);
    if (error instanceof Error) {
      console.error('[Image Proxy] Error message:', error.message);
      console.error('[Image Proxy] Error stack:', error.stack);
    }
    return NextResponse.json(
      { error: 'Internal server error', message: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
