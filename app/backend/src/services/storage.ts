import { S3Client, PutObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { createHash } from 'crypto';

export interface StorageBackend {
  storeImage(buffer: Buffer, sha256: string, mimeType: string): Promise<string>;
  getImage(sha256: string): Promise<Buffer | null>;
  getImageUrl(sha256: string): string;
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
}

export class S3Storage implements StorageBackend {
  private client: S3Client;
  private bucket: string;
  private region: string;

  constructor(bucket: string, region: string) {
    this.bucket = bucket;
    this.region = region;
    this.client = new S3Client({
      region,
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || '',
      },
    });
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
}

export function getStorageBackend(): StorageBackend {
  const bucket = process.env.S3_BUCKET;
  const region = process.env.S3_REGION;
  const nodeEnv = process.env.NODE_ENV || 'development';

  if (bucket && region && nodeEnv === 'production') {
    return new S3Storage(bucket, region);
  }

  return new LocalStorage();
}

