# Bunny

A high-performance media feed and community platform built with a focus on speed, type safety, and intelligent discovery.

## Project Overview

Bunny is a modern full-stack application designed for managing and exploring large-scale media feeds. It features a sophisticated backend powered by graph databases and vector search, providing a seamless and intelligent user experience.

### Key Features

- **Intelligent Feed**: Responsive masonry layout with infinite scroll and server-side filtering.
- **Vector Discovery**: Similarity-based media discovery using CLIP embeddings and Redis Vector Similarity Search (VSS).
- **Media Management**: Automated image ingestion, hashing (pHash) for deduplication, and clustering.
- **Graph-Powered**: Relationships and metadata managed via Neo4j for complex querying and discovery.
- **Secure Access**: Invite-only community system with integrated waitlist and authentication.
- **Type Safety**: End-to-end TypeScript integration with GraphQL Code Generator.

## Tech Stack

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Library**: React 19
- **Styling**: Tailwind CSS + Framer Motion
- **State**: Zustand
- **Auth**: Better Auth

### Backend
- **Server**: Node.js + Express (GraphQL)
- **Database**: Neo4j (Graph)
- **Cache & Vector Store**: Redis/Valkey (HNSW Index)
- **ML/AI**: Transformers.js (CLIP embeddings)
- **Schema**: GraphQL + Drizzle ORM

### Infrastructure
- **Runtime**: Bun
- **Containerization**: Docker + Docker Compose
- **Testing**: Playwright (E2E) + Bun (Unit)

## Getting Started

### Prerequisites
- [Docker](https://www.docker.com/)
- [Bun](https://bun.sh/) (optional, for local task execution)

### Installation

1. **Clone the repository**
2. **Start the infrastructure:**
   ```bash
   docker compose up -d
   ```
3. **Run the development servers:**
   ```bash
   # Client
   cd app/client && bun run dev
   
   # Server
   cd app/server && bun run dev
   ```

## Project Structure

- `app/client`: Next.js frontend application.
- `app/server`: Express GraphQL server and ingestion scripts.
- `shared/`: Shared TypeScript types and utilities.
- `docs/`: Technical documentation and ADRs.

## Documentation

For more detailed information, please refer to the files in the `docs/` directory:
- [Architecture Decision Records](docs/adr-001-express-elysia.md)
- [GraphQL Code Generation](docs/graphql-codegen.md)
- [Neo4j Optimization](docs/neo4j-optimization.md)
- [Performance Guide](docs/performance.md)

## License

Private / Proprietary
