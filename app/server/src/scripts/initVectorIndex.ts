import { VectorSearchService } from '../services/vectorSearch.js';
import { verifyValkeyConnection } from '../valkey/client.js';

async function initializeVectorIndex() {
  console.log('Initializing Redis Vector Search index...');

  try {
    await verifyValkeyConnection();

    const vectorSearch = new VectorSearchService();
    await vectorSearch.initializeIndex();

    console.log('Vector search index initialized successfully!');
    console.log('Index name: idx:clip_embeddings');
    console.log('Prefix: clip:embedding:');
    console.log('Dimensions: 512');
    console.log('Distance metric: COSINE');
    console.log('Algorithm: HNSW');

    process.exit(0);
  } catch (error) {
    console.error('Failed to initialize vector search index:', error);
    process.exit(1);
  }
}

initializeVectorIndex();
