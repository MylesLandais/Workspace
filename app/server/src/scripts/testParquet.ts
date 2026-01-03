
import { readFileSync } from 'fs';
import { parquetRead } from 'hyparquet';

async function testRead() {
  const path = '/home/warby/Workspace/jupyter/packs/nightly-2026-01-02/threads.parquet';
  const buffer = readFileSync(path);
  
  await parquetRead({
    file: {
      byteLength: buffer.byteLength,
      async slice(offset, end) {
        return buffer.buffer.slice(buffer.byteOffset + offset, buffer.byteOffset + end);
      }
    },
    rowFormat: 'object',
    onComplete: (data) => {
      console.log('Rows:', data.length);
      if (data.length > 0) {
        console.log('Sample row:', data[0]);
      }
    }
  });
}

testRead().catch(console.error);
