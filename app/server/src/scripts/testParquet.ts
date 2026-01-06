
import { readFileSync } from 'fs';
import { parquetRead } from 'hyparquet';

async function testRead() {
  const threadsPath = '/home/warby/Workspace/jupyter/packs/nightly-2026-01-02/threads.parquet';
  const imagesPath = '/home/warby/Workspace/jupyter/packs/nightly-2026-01-02/images.parquet';
  
  console.log('=== Threads ===');
  const threadsBuffer = readFileSync(threadsPath);
  
  await parquetRead({
    file: {
      byteLength: threadsBuffer.byteLength,
      async slice(offset, end) {
        return threadsBuffer.buffer.slice(threadsBuffer.byteOffset + offset, threadsBuffer.byteOffset + end);
      }
    },
    rowFormat: 'object',
    onComplete: (data) => {
      console.log('Thread rows:', data.length);
      if (data.length > 0) {
        console.log('Sample thread:', data[0]);
      }
    }
  });

  console.log('\n=== Images ===');
  const imagesBuffer = readFileSync(imagesPath);
  
  await parquetRead({
    file: {
      byteLength: imagesBuffer.byteLength,
      async slice(offset, end) {
        return imagesBuffer.buffer.slice(imagesBuffer.byteOffset + offset, imagesBuffer.byteOffset + end);
      }
    },
    rowFormat: 'object',
    onComplete: (data) => {
      console.log('Image rows:', data.length);
      if (data.length > 0) {
        console.log('Sample image:', data[0]);
      }
    }
  });
}

testRead().catch(console.error);
