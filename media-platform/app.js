const express = require('express');
const config = require('./config');
const { cache } = require('./cache');
const { MediaService, CollectionService } = require('./services/mediaService');

const app = express();
app.use(express.json());

// Services
const mediaService = new MediaService();
const neo4jDriver = mediaService.neo4jDriver;
const collectionService = new CollectionService(neo4jDriver);

// Middleware to track cache stats
app.use((req, res, next) => {
  res.on('finish', () => {
    if (process.env.LOG_CACHE_STATS === 'true') {
      console.log('Cache Stats:', cache.getStats());
    }
  });
  next();
});

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    const cacheInfo = await cache.info();
    const stats = cache.getStats();
    
    res.json({
      status: 'healthy',
      environment: config.environment,
      services: {
        cache: cache.isConnected ? 'connected' : 'disconnected',
        neo4j: 'connected', // TODO: Add proper check
        storage: 'connected' // TODO: Add proper check
      },
      cache: {
        stats,
        connected: cache.isConnected
      }
    });
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: error.message
    });
  }
});

// Cache stats endpoint
app.get('/api/cache/stats', async (req, res) => {
  try {
    const stats = cache.getStats();
    const info = await cache.info();
    
    res.json({
      stats,
      info: info ? info.split('\r\n').slice(0, 20) : null
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Flush cache endpoint (protected in production!)
app.post('/api/cache/flush', async (req, res) => {
  if (config.environment === 'production') {
    return res.status(403).json({ error: 'Not allowed in production' });
  }
  
  try {
    await cache.flushAll();
    res.json({ message: 'Cache flushed successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Media endpoints
app.get('/api/media/:id', async (req, res) => {
  try {
    const media = await mediaService.getMedia(req.params.id);
    
    if (!media) {
      return res.status(404).json({ error: 'Media not found' });
    }
    
    res.json(media);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/media/:id/metadata', async (req, res) => {
  try {
    const media = await mediaService.getMediaWithMetadata(req.params.id);
    
    if (!media) {
      return res.status(404).json({ error: 'Media not found' });
    }
    
    res.json(media);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/users/:userId/media', async (req, res) => {
  try {
    const { userId } = req.params;
    const limit = parseInt(req.query.limit || '50', 10);
    const skip = parseInt(req.query.skip || '0', 10);
    
    const media = await mediaService.getUserMedia(userId, limit, skip);
    
    res.json({
      items: media,
      pagination: {
        limit,
        skip,
        hasMore: media.length === limit
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/collections/:id', async (req, res) => {
  try {
    const collection = await collectionService.getCollection(req.params.id);
    
    if (!collection) {
      return res.status(404).json({ error: 'Collection not found' });
    }
    
    res.json(collection);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Startup
async function start() {
  try {
    // Connect to Valkey
    await cache.connect();
    console.log('✓ Valkey connected');
    
    // Start server
    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
      console.log(`✓ Server running on port ${PORT}`);
      console.log(`✓ Environment: ${config.environment}`);
      console.log(`✓ Neo4j: ${config.neo4j.uri}`);
      console.log(`✓ Valkey: ${config.valkey.url}`);
      console.log(`✓ Storage: ${config.storage.endpoint}`);
    });
  } catch (error) {
    console.error('Failed to start:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down gracefully...');
  await cache.disconnect();
  await mediaService.close();
  process.exit(0);
});

start();

module.exports = app;




