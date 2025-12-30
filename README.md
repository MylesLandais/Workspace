# Bunny - Unified Content Management Platform

Bunny is a graph-native content management and reading platform that aggregates content from multiple sources (Reddit, RSS, social media, newsletters) into a unified feed experience. Built with Neo4j for relationship-rich data modeling, Valkey for high-performance caching, and Astro + React for a modern frontend.

## Overview

Bunny transforms how users discover, organize, and engage with content by:

- **Unified Ingestion**: Aggregate content from Reddit, RSS feeds, social media, newsletters, and more
- **Graph-Native Architecture**: Leverage Neo4j's relationship model for intelligent content discovery
- **Visual Feed Interface**: Scrolller-inspired infinite scroll with Bunny Feed components
- **Smart Organization**: Multi-dimensional tagging, boards, and collections
- **AI-Powered Features**: Summarization, Q&A, and intelligent content analysis
- **Cross-Platform Sync**: Seamless experience across web, mobile, and browser extensions

## Architecture

### Technology Stack

- **Frontend**: Astro 4 + React 19 with TypeScript
- **Backend**: Node.js + Express with Apollo GraphQL Server
- **Database**: Neo4j Aura (graph database)
- **Cache**: Valkey (Redis-compatible in-memory cache)
- **Storage**: S3-compatible object storage (MinIO/GCP/R2)
- **Development**: Docker Compose for local development

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Astro + React)              │
│  - Bunny Feed components (infinite scroll)               │
│  - Feed Manager (subscription management)                │
│  - Mock data support for development                     │
└──────────────────────┬────────────────────────────────────┘
                       │ GraphQL
┌──────────────────────▼────────────────────────────────────┐
│              Backend (Apollo GraphQL Server)              │
│  - Query resolvers (feed, creators, sources)              │
│  - Mutation resolvers (subscriptions, rules)             │
│  - Bunny-specific resolvers                               │
└──────┬──────────────────────────────┬──────────────────────┘
       │                              │
┌──────▼──────────┐        ┌─────────▼─────────────┐
│   Valkey Cache  │        │   Neo4j Graph DB      │
│  - Query cache  │        │  - Nodes & Relations  │
│  - Session data │        │  - Cypher queries    │
└─────────────────┘        └────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) Neo4j Aura credentials for production

### Frontend Development

```bash
cd app/frontend
docker-compose up --build
```

Visit `http://localhost:4321`

The frontend includes:
- Hot module reloading
- Mock data support (set `PUBLIC_GRAPHQL_MOCK=true`)
- Vitest for unit testing
- Playwright for E2E testing

### Backend Development

```bash
cd app/backend
docker-compose up --build
```

GraphQL endpoint: `http://localhost:4002/api/graphql`
Health check: `http://localhost:4002/health`

The backend includes:
- Auto-reload on file changes
- Automatic Neo4j index creation
- Valkey connection verification

### Full Stack Development

Start both services:

```bash
# Terminal 1: Backend
cd app/backend && docker-compose up

# Terminal 2: Frontend
cd app/frontend && docker-compose up
```

## Project Structure

```
.
├── app/                    # Unified application codebase
│   ├── frontend/           # Astro + React frontend
│   │   ├── src/
│   │   │   ├── components/ # React components (islands)
│   │   │   │   ├── feed/   # Feed display components
│   │   │   │   ├── feed-manager/ # Subscription management
│   │   │   │   └── bunny/ # Bunny Feed components
│   │   │   ├── layouts/    # Astro layouts
│   │   │   └── pages/      # Astro pages (routing)
│   │   ├── scripts/        # Mock data generation
│   │   └── tests/          # Test suites
│   └── backend/           # GraphQL backend
│       ├── src/
│       │   ├── schema/     # GraphQL type definitions
│       │   ├── resolvers/  # Query and mutation resolvers
│       │   ├── neo4j/      # Neo4j driver and queries
│       │   ├── valkey/     # Valkey cache client
│       │   ├── services/   # Business logic services
│       │   └── bunny/     # Bunny-specific resolvers
│       └── storage/        # Local storage (dev)
├── docs/                   # Project documentation
│   ├── domains/            # Domain-specific documentation
│   ├── architecture/       # Architecture Decision Records
│   └── interfaces/         # API schemas (GraphQL, Cypher)
├── archive/                # Archived extracted components
└── temp/                   # Temporary files and mock data
```

## Documentation

Comprehensive documentation is available in `/docs`:

### Getting Started

- **[Main Documentation](./docs/README.md)** - Complete documentation index
- **[Requirements](./docs/requirements.md)** - Feature requirements and specifications
- **[Design Principles](./docs/design-principles.md)** - Core architectural principles

### Domain Documentation

- **[Feed Domain](./docs/domains/feed/README.md)** - Post ingestion, display, and infinite scroll
- **[Subscriptions Domain](./docs/domains/subscriptions/README.md)** - Source management and ingestion rules
- **[Mock Data Guide](./docs/domains/feed/mock-data-guide.md)** - Using mock data for development

### Architecture

- **[Architecture Decisions](./docs/architecture/adr/)** - ADRs explaining technical choices
- **[Risks & Mitigations](./docs/risks.md)** - Known risks and mitigation strategies
- **[Decisions Log](./docs/decisions-log.md)** - Integration decisions and rationale

### Integration Documentation

- **[Bunny Feed Integration](./docs/bunny-integration.md)** - Bunny component integration
- **[Reader Integration](./docs/reader-integration.md)** - Reader component integration

## Key Features

### Content Ingestion

- **Multi-Source Support**: Reddit, RSS, social media, newsletters
- **Unified Data Model**: All sources normalize to consistent Item format
- **Deduplication**: Content hash and URL-based duplicate detection
- **Ingestion Rules**: Configurable filters (min score, media only, resolution)

### Feed Experience

- **Infinite Scroll**: Cursor-based pagination for performance
- **Visual Feed**: Scrolller-inspired grid layout with hover previews
- **Real-Time Updates**: WebSocket subscriptions for live feed updates
- **Filtering**: By source, date, tags, reading status

### Organization

- **Multi-Dimensional Tagging**: Hierarchical tags with relationships
- **Boards & Collections**: Pinterest-style organization
- **Saved Searches**: Query-based smart collections
- **Cross-Content Discovery**: Graph-based recommendations

### AI Features

- **Document Summarization**: 3-5 bullet points or full summary
- **Q&A**: Ask questions about content
- **Automatic Tagging**: AI-powered content categorization
- **Ghost Reader**: AI continues reading where user left off

## Development Workflow

### Using Mock Data

The frontend supports mock data for development without backend dependencies:

```bash
# Generate mock data from scraped Reddit data
cd app/frontend
npm run generate-mock-data

# Enable mock mode
PUBLIC_GRAPHQL_MOCK=true npm run dev
```

### Testing

```bash
# Frontend unit tests
cd app/frontend
docker-compose exec frontend npm run test

# Frontend E2E tests
docker-compose exec frontend npm run test:e2e

# Backend (when tests are added)
cd app/backend
npm run test
```

### Code Organization

- **Domain-Driven**: Code organized by business domain, not technology
- **Type Safety**: Full TypeScript coverage
- **Documentation**: ADRs for architectural decisions, READMEs for domains

## Environment Configuration

### Frontend Environment Variables

```bash
PUBLIC_GRAPHQL_ENDPOINT=http://localhost:4002/api/graphql
PUBLIC_GRAPHQL_MOCK=false
PUBLIC_WS_ENDPOINT=ws://localhost:4002/api/graphql
```

### Backend Environment Variables

```bash
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
VALKEY_URL=redis://localhost:6379
PORT=4002
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines, code standards, and contribution workflow.

## License

[Your License Here]


