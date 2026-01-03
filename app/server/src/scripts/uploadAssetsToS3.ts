import 'dotenv/config';
import { readdir, stat } from 'fs/promises';
import { join } from 'path';
import { readFileSync } from 'fs';
import { createHash } from 'crypto';
import { getStorageBackend } from '../services/storage.js';
import { ImageHasher } from '../services/imageHasher.js';

interface AssetFile {
  path: string;
  name: string;
  size: number;
  mimeType: string;
}

async function getMimeType(filename: string): Promise<string> {
  const ext = filename.toLowerCase().split('.').pop();
  const mimeTypes: Record<string, string> = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'webp': 'image/webp',
    'gif': 'image/gif',
    'mp4': 'video/mp4',
    'mov': 'video/quicktime',
    'avi': 'video/x-msvideo',
    'mkv': 'video/x-matroska',
    'webm': 'video/webm',
  };
  return mimeTypes[ext || ''] || 'application/octet-stream';
}

async function scanAssetsDirectory(assetsPath: string): Promise<AssetFile[]> {
  const files: AssetFile[] = [];
  
  async function scanDir(dir: string, relativePath: string = '') {
    const entries = await readdir(dir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = join(dir, entry.name);
      const relPath = relativePath ? join(relativePath, entry.name) : entry.name;
      
      if (entry.isDirectory()) {
        // Skip hidden directories and common cache directories
        if (entry.name.startsWith('.') || entry.name === 'node_modules') {
          continue;
        }
        await scanDir(fullPath, relPath);
      } else if (entry.isFile()) {
        const stats = await stat(fullPath);
        const mimeType = await getMimeType(entry.name);
        
        // Only process image and video files
        if (mimeType.startsWith('image/') || mimeType.startsWith('video/')) {
          files.push({
            path: fullPath,
            name: relPath,
            size: stats.size,
            mimeType,
          });
        }
      }
    }
  }
  
  await scanDir(assetsPath);
  return files;
}

async function uploadAssetToS3(asset: AssetFile, storage: any): Promise<{ sha256: string; uploaded: boolean; error?: string }> {
  try {
    console.log(`Processing: ${asset.name}`);
    
    // Read the file
    const buffer = readFileSync(asset.path);
    console.log(`  Read ${buffer.length} bytes`);
    
    // Compute SHA256 hash
    const hasher = new ImageHasher();
    const hashes = await hasher.computeHashesFromBuffer(buffer);
    console.log(`  SHA256: ${hashes.sha256.substring(0, 12)}...`);
    
    // Upload to S3
    const storageKey = await storage.storeImage(buffer, hashes.sha256, hashes.mimeType);
    console.log(`  Uploaded to: ${storageKey}`);
    
    return {
      sha256: hashes.sha256,
      uploaded: true,
    };
  } catch (error: any) {
    console.error(`  Error: ${error.message}`);
    return {
      sha256: '',
      uploaded: false,
      error: error.message,
    };
  }
}

async function main() {
  const assetsPath = process.env.ASSETS_PATH || '/home/warby/assets';
  
  console.log(`Scanning assets directory: ${assetsPath}`);
  console.log('---');
  
  const assets = await scanAssetsDirectory(assetsPath);
  console.log(`Found ${assets.length} media files`);
  console.log('---');
  
  const storage = getStorageBackend();
  
  const results = {
    total: assets.length,
    uploaded: 0,
    failed: 0,
    skipped: 0,
    errors: [] as Array<{ file: string; error: string }>,
  };
  
  for (let i = 0; i < assets.length; i++) {
    const asset = assets[i];
    console.log(`[${i + 1}/${assets.length}] ${asset.name}`);
    
    const result = await uploadAssetToS3(asset, storage);
    
    if (result.uploaded) {
      results.uploaded++;
    } else {
      results.failed++;
      if (result.error) {
        results.errors.push({ file: asset.name, error: result.error });
      }
    }
    
    console.log('');
  }
  
  console.log('---');
  console.log('Upload Summary:');
  console.log(`  Total files: ${results.total}`);
  console.log(`  Uploaded: ${results.uploaded}`);
  console.log(`  Failed: ${results.failed}`);
  console.log(`  Skipped: ${results.skipped}`);
  
  if (results.errors.length > 0) {
    console.log('\nErrors:');
    results.errors.forEach(({ file, error }) => {
      console.log(`  ${file}: ${error}`);
    });
  }
  
  console.log('---');
  console.log('Upload complete!');
  
  process.exit(results.failed > 0 ? 1 : 0);
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
