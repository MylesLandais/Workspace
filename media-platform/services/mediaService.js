const neo4j = require('neo4j-driver');
const { S3Client, GetObjectCommand, HeadObjectCommand } = require('@aws-sdk/client-s3');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');
const config = require('../config');
const { cache } = require('../cache');

class MediaService {
  constructor() {
    this.neo4jDriver = neo4j.driver(
      config.neo4j.uri,
      neo4j.auth.basic(config.neo4j.user, config.neo4j.password)
    );

    this.s3Client = new S3Client({
      endpoint: config.storage.endpoint,
      region: config.storage.region,
      credentials: {
        accessKeyId: config.storage.accessKeyId,
        secretAccessKey: config.storage.secretAccessKey
      },
      forcePathStyle: config.storage.forcePathStyle
    });
  }

  async getMedia(mediaId) {
    const cacheKey = `media:${mediaId}`;
    
    // Check cache first
    const cached = await cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    // Cache miss - query Neo4j
    const session = this.neo4jDriver.session({ database: config.neo4j.database });
    try {
      const result = await session.run(
        'MATCH (m:Media {id: $id}) RETURN m',
        { id: mediaId }
      );

      if (result.records.length === 0) {
        return null;
      }

      const media = result.records[0].get('m').properties;
      
      // Store in cache with TTL
      await cache.set(cacheKey, media, config.valkey.ttl);
      
      return media;
    } finally {
      await session.close();
    }
  }

  async getMediaWithMetadata(mediaId) {
    const cacheKey = `media:metadata:${mediaId}`;
    
    // Check cache first
    const cached = await cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    // Get media from Neo4j
    const media = await this.getMedia(mediaId);
    if (!media) {
      return null;
    }

    // Get metadata from S3
    try {
      const headCommand = new HeadObjectCommand({
        Bucket: config.storage.bucket,
        Key: media.objectKey
      });
      
      const metadata = await this.s3Client.send(headCommand);
      
      const result = {
        ...media,
        metadata: {
          size: metadata.ContentLength,
          contentType: metadata.ContentType,
          lastModified: metadata.LastModified,
          etag: metadata.ETag
        }
      };

      // Store in cache with longer TTL for metadata
      await cache.set(cacheKey, result, config.valkey.ttl * 2);
      
      return result;
    } catch (error) {
      console.error('Error fetching metadata:', error);
      return media;
    }
  }

  async getUserMedia(userId, limit = 50, skip = 0) {
    const cacheKey = `user:${userId}:media:${limit}:${skip}`;
    
    // Check cache first
    const cached = await cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    // Cache miss - query Neo4j
    const session = this.neo4jDriver.session({ database: config.neo4j.database });
    try {
      const result = await session.run(
        `MATCH (u:User {id: $userId})-[:OWNS]->(m:Media)
         RETURN m
         ORDER BY m.createdAt DESC
         SKIP $skip
         LIMIT $limit`,
        { userId, skip, limit }
      );

      const media = result.records.map(record => record.get('m').properties);
      
      // Store in cache
      await cache.set(cacheKey, media, config.valkey.ttl);
      
      return media;
    } finally {
      await session.close();
    }
  }

  async close() {
    await this.neo4jDriver.close();
  }
}

class CollectionService {
  constructor(neo4jDriver) {
    this.neo4jDriver = neo4jDriver;
  }

  async getCollection(collectionId) {
    const cacheKey = `collection:${collectionId}`;
    
    // Check cache first
    const cached = await cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    // Cache miss - query Neo4j
    const session = this.neo4jDriver.session({ database: config.neo4j.database });
    try {
      const result = await session.run(
        `MATCH (c:Collection {id: $id})
         OPTIONAL MATCH (c)-[:CONTAINS]->(m:Media)
         RETURN c, collect(m) as media`,
        { id: collectionId }
      );

      if (result.records.length === 0) {
        return null;
      }

      const record = result.records[0];
      const collection = record.get('c').properties;
      const media = record.get('media').map(m => m.properties);
      
      const result_data = {
        ...collection,
        media
      };

      // Store in cache
      await cache.set(cacheKey, result_data, config.valkey.ttl);
      
      return result_data;
    } finally {
      await session.close();
    }
  }
}

module.exports = { MediaService, CollectionService };




