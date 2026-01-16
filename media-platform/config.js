require('dotenv').config({ path: `.env.${process.env.ENVIRONMENT || 'local'}` });

module.exports = {
  environment: process.env.ENVIRONMENT || 'local',
  
  valkey: {
    url: process.env.VALKEY_URL || 'valkey://localhost:6379',
    password: process.env.VALKEY_PASSWORD || undefined,
    db: parseInt(process.env.VALKEY_DB || '0', 10),
    ttl: parseInt(process.env.VALKEY_TTL || '300', 10)
  },
  
  storage: {
    endpoint: process.env.S3_ENDPOINT,
    accessKeyId: process.env.S3_ACCESS_KEY_ID,
    secretAccessKey: process.env.S3_SECRET_ACCESS_KEY,
    bucket: process.env.S3_BUCKET_NAME,
    region: process.env.S3_REGION,
    forcePathStyle: process.env.S3_FORCE_PATH_STYLE === 'true',
    publicUrl: process.env.S3_PUBLIC_URL
  },
  
  neo4j: {
    uri: process.env.NEO4J_URI,
    user: process.env.NEO4J_USER,
    password: process.env.NEO4J_PASSWORD,
    database: process.env.NEO4J_DATABASE || 'neo4j'
  }
};




