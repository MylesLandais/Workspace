# Bunny Backend

Express.js + Apollo Server GraphQL API connected to Neo4j graph database and Valkey cache.

## Setup

1. Copy `.env.example` to `.env` and configure Neo4j credentials:
```
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
PORT=4002
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

Or using Docker:
```bash
docker-compose up --build
```

## Architecture

### Tech Stack
- **Server Framework**: Express.js
- **GraphQL**: Apollo Server
- **Database**: Neo4j (graph database for relationships)
- **Cache**: Valkey (Redis-compatible)
- **Image Processing**: Sharp
- **AI/ML**: Transformers.js (CLIP embeddings, image hashing)
- **Storage**: AWS S3-compatible (MinIO for local dev)

### Design Decisions
**Why Express + Apollo Server?**
- Mature ecosystem with extensive community support
- Well-documented patterns for GraphQL with Apollo
- Flexible middleware pipeline for auth, logging, etc.
- Easy integration with existing Node.js tooling

**Why Neo4j?**
- Graph-native data modeling for creator identities and media relationships
- Efficient traversal of complex social graphs
- Built-in support for relationship queries
- Powerful Cypher query language

**Why Valkey?**
- Sub-millisecond caching for hot data paths
- Redis-compatible for easy migration
- Persistent cache for expensive operations (AI embeddings, duplicate detection)

## GraphQL Endpoint

- Development: `http://localhost:4002/api/graphql`
- Health check: `http://localhost:4002/health`

## Features

- GraphQL API with Apollo Server
- Neo4j database integration
- Automatic index/constraint creation
- Cursor-based pagination for feed
- Real-time data queries

## Project Structure

```
src/
├── index.ts                    # Express + Apollo Server setup
├── schema/
│   └── schema.ts              # GraphQL type definitions
├── resolvers/
│   ├── queries.ts             # Core query resolvers
│   └── mutations.ts          # Core mutation resolvers
├── bunny/                     # Bunny-specific features
│   ├── types.ts               # Bunny type definitions
│   ├── adapters.ts            # Data transformation utilities
│   ├── queries.ts             # Bunny-specific queries
│   └── resolvers.ts           # Bunny resolvers (merged into main)
├── neo4j/
│   ├── driver.ts              # Neo4j connection management
│   └── queries/               # Cypher query functions
│       ├── feed.ts
│       ├── creators.ts
│       ├── images.ts
│       └── sources.ts
├── services/                  # Business logic services
│   ├── storage.ts             # S3/MinIO storage
│   ├── presignedUrl.ts        # URL generation
│   ├── urlCache.ts            # Valkey caching
│   ├── imageHasher.ts         # Phash/dhash generation
│   ├── clipEmbedder.ts        # CLIP embeddings
│   ├── duplicateDetector.ts   # Duplicate detection
│   ├── phashBucketing.ts      # Perceptual hash indexing
│   └── imageIngestion.ts      # Image ingestion pipeline
├── valkey/
│   └── client.ts              # Valkey (Redis) client
└── scripts/                   # Utility scripts
    ├── checkDatabase.ts       # Database health check
    ├── cleanDatabase.ts       # Database cleanup
    ├── ingestFromS3.ts        # Bulk S3 ingestion
    └── testFeedQuery.ts       # Query testing
```

