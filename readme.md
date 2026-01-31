# Bunny

A high-performance media feed and community platform built with a focus on speed, type safety, and intelligent discovery.

## Project Overview

Bunny is a modern full-stack application designed for managing and exploring large-scale media feeds. It features a sophisticated backend powered by graph databases and vector search, providing a seamless and intelligent user experience.

### Key Features

- **Intelligent Feed**: Responsive masonry layout with infinite scroll and server-side filtering.
- **Customizable Dashboard**: Drag-and-drop workspace with 11 widget types, real-time collaboration, and canvas mode.
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

### Quick Start with devenv (Recommended)

Use Nix and devenv for a fully reproducible environment:

```bash
# Enter the dev shell
devenv shell

# Start Neo4j (required for data)
neo4j start

# Start GraphQL server
server-start

# Start all client services
devenv up

# Visit: http://localhost:3000
```

**Important**: Neo4j and the GraphQL server must be running for the feed/dashboard to work.

See **[docs/setup-guide.md](docs/setup-guide.md)** for complete setup instructions including data compatibility layer.

### Alternative: Docker

- [Docker](https://www.docker.com/)
- [Bun](https://bun.sh/)

```bash
# Start GraphQL server
cd app/server && docker-compose up -d

# Start client
cd app/client && bun run dev
```

## Project Structure

- `app/client`: Next.js frontend application.
- `app/server`: Express GraphQL server and ingestion scripts.
- `shared/`: Shared TypeScript types and utilities.
- `docs/`: Technical documentation and ADRs.

## Documentation

For detailed information, see the `docs/` directory:

### Setup & Configuration

- **[Setup Guide](docs/setup-guide.md)** - Complete system setup with Neo4j, GraphQL, and dashboard
- **[Contributing Guide](contributing.md)** - Development environment setup with devenv
- **[Data Compatibility Layer](docs/data-compatibility-layer.md)** - Post/Media schema bridging

### Features

- **[Dashboard Guide](docs/dashboard.md)** - Dashboard features, widgets, and collaboration

### Architecture

- [Architecture Decision Records](docs/adr-001-express-elysia.md)
- [GraphQL Code Generation](docs/graphql-codegen.md)
- [Neo4j Optimization](docs/neo4j-optimization.md)
- [Performance Guide](docs/performance.md)

## License

Private / Proprietary
