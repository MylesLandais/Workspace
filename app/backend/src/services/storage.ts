import { S3Client, PutObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { createHash } from 'crypto';

export interface StorageBackend {
  storeImage(buffer: Buffer, sha256: string, mimeType: string): Promise<string>;
  getImage(sha256: string): Promise<Buffer | null>;
  getImageUrl(sha256: string): string;
  getPresignedUrl(sha256: string, mimeType: string, expiresIn?: number): Promise<string>;
}

export class LocalStorage implements StorageBackend {
  private basePath: string;

  constructor(basePath: string = '/app/storage/images') {
    this.basePath = basePath;
  }

  private getImagePath(sha256: string, mimeType: string): string {
    const ext = mimeType.split('/')[1] || 'jpg';
    const prefix = sha256.substring(0, 8);
    const dir = join(this.basePath, prefix);
    
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
    
    return join(dir, `${sha256}.${ext}`);
  }

  async storeImage(buffer: Buffer, sha256: string, mimeType: string): Promise<string> {
    const path = this.getImagePath(sha256, mimeType);
    writeFileSync(path, buffer);
    return path;
  }

  async getImage(sha256: string): Promise<Buffer | null> {
    const possibleExts = ['jpg', 'jpeg', 'png', 'webp', 'gif'];
    
    for (const ext of possibleExts) {
      const prefix = sha256.substring(0, 8);
      const path = join(this.basePath, prefix, `${sha256}.${ext}`);
      
      if (existsSync(path)) {
        return readFileSync(path);
      }
    }
    
    return null;
  }

  getImageUrl(sha256: string): string {
    return `/storage/images/${sha256.substring(0, 8)}/${sha256}`;
  }

  async getPresignedUrl(sha256: string, mimeType: string, expiresIn: number = 14400): Promise<string> {
    return this.getImageUrl(sha256);
  }
}

export class S3Storage implements StorageBackend {
  private client: S3Client;
  private bucket: string;
  private region: string;
  private endpoint?: string;

  constructor(bucket: string, region: string, endpoint?: string) {
    this.bucket = bucket;
    this.region = region;
    this.endpoint = endpoint;

    const clientConfig: any = {
      region,
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || '',
      },
    };

    if (endpoint) {
      clientConfig.endpoint = endpoint;
      clientConfig.forcePathStyle = true;
    }

    this.client = new S3Client(clientConfig);
  }

  private getImageKey(sha256: string, mimeType: string): string {
    const ext = mimeType.split('/')[1] || 'jpg';
    const prefix = sha256.substring(0, 8);
    return `images/${prefix}/${sha256}.${ext}`;
  }

  async storeImage(buffer: Buffer, sha256: string, mimeType: string): Promise<string> {
    const key = this.getImageKey(sha256, mimeType);
    
    await this.client.send(
      new PutObjectCommand({
        Bucket: this.bucket,
        Key: key,
        Body: buffer,
        ContentType: mimeType,
      })
    );
    
    return key;
  }

  async getImage(sha256: string): Promise<Buffer | null> {
    const possibleExts = ['jpg', 'jpeg', 'png', 'webp', 'gif'];
    
    for (const ext of possibleExts) {
      const prefix = sha256.substring(0, 8);
      const key = `images/${prefix}/${sha256}.${ext}`;
      
      try {
        const response = await this.client.send(
          new GetObjectCommand({
            Bucket: this.bucket,
            Key: key,
          })
        );
        
        if (response.Body) {
          const chunks: Uint8Array[] = [];
          for await (const chunk of response.Body as any) {
            chunks.push(chunk);
          }
          return Buffer.concat(chunks);
        }
      } catch (error: any) {
        if (error.name !== 'NoSuchKey') {
          throw error;
        }
      }
    }
    
    return null;
  }

  getImageUrl(sha256: string): string {
    return `https://${this.bucket}.s3.${this.region}.amazonaws.com/images/${sha256.substring(0, 8)}/${sha256}`;
  }

  async getPresignedUrl(sha256: string, mimeType: string, expiresIn: number = 14400): Promise<string> {
    const key = this.getImageKey(sha256, mimeType);
    const command = new GetObjectCommand({
      Bucket: this.bucket,
      Key: key,
    });
    return await getSignedUrl(this.client, command, { expiresIn });
  }
}

export function getStorageBackend(): StorageBackend {
  const bucket = process.env.S3_BUCKET;
  const region = process.env.S3_REGION;
  const endpoint = process.env.S3_ENDPOINT;

  if (bucket && region) {
    return new S3Storage(bucket, region, endpoint);
  }

  return new LocalStorage();
}

