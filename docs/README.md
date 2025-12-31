# Documentation

This directory contains comprehensive documentation for the Bunny content management platform, organized by domain and architectural concerns.

## Documentation Overview

Bunny's documentation follows a domain-driven structure that separates business concerns from technical implementation details. All documentation is kept up-to-date with the codebase and serves as the single source of truth for system understanding.

## Quick Navigation

### Essential Reading

- **[Requirements](./requirements.md)** - Complete feature requirements and specifications
- **[Design Principles](./design-principles.md)** - Core architectural principles and patterns
- **[Decisions Log](./decisions-log.md)** - Key integration and design decisions

### Domain Documentation

- **[Feed Domain](./domains/feed/README.md)** - Post ingestion, display, and infinite scroll
  - [Data Model](./domains/feed/data-model.md) - Neo4j graph structure
  - [GraphQL Schema](./domains/feed/schema.md) - API types and queries
  - [Mock Data Guide](./domains/feed/mock-data-guide.md) - Development with mock data
- **[Subscriptions Domain](./domains/subscriptions/README.md)** - Source management and ingestion rules
  - [Data Model](./domains/subscriptions/data-model.md) - Subscription graph structure
  - [GraphQL Schema](./domains/subscriptions/schema.md) - API operations
  - [User Stories](./domains/subscriptions/user-stories.md) - Feature requirements

### Architecture

- **[Architecture Decision Records](./architecture/adr/)** - Technical decision documentation
  - [GraphQL over REST](./architecture/adr/graphql-over-rest.md)
  - [Neo4j Graph Database](./architecture/adr/neo4j-graph-database.md)
  - [Valkey Caching Layer](./architecture/adr/valkey-caching-layer.md)
- [Unified Ingestion Layer](./architecture/adr/unified-ingestion-layer.md)
- [Bunny Feed Integration](./architecture/adr/bunny-feed-integration.md)
- [And 18 more ADRs...](./architecture/adr/)


### Risk Management

- **[Risks & Mitigations](./risks.md)** - Known risks, impact assessment, and mitigation strategies

### Integration Documentation

#### Bunny Feed Integration

- **[Integration Summary](./bunny-integration.md)** - START HERE: High-level overview
- [Bunny Analysis](./bunny-analysis.md) - Complete codebase analysis
- [Tech Stack Conflicts](./bunny-tech-stack.md) - Integration challenges
- [Component Interface Map](./bunny-component-map.md) - UI component specifications
- [Data Schema Expectations](./bunny-data-schema.md) - Neo4j schema requirements
- [Features & Requirements](./bunny-features.md) - Feature requirements
- [Board Design](./bunny-board-design.md) - Organizational model exploration

#### Reader Integration

- **[Integration Summary](./reader-integration.md)** - START HERE: High-level overview
- [Reader Analysis](./reader-analysis.md) - Complete codebase analysis
- [Tech Stack Conflicts](./reader-tech-stack.md) - Integration challenges
- [Component Interface Map](./reader-component-map.md) - UI component specifications
- [Data Schema Expectations](./reader-data-schema.md) - Neo4j schema requirements
- [Features & Requirements](./reader-features.md) - Feature requirements

### API Reference

- **[GraphQL Schema](./interfaces/graphql/schema.graphql)** - Complete GraphQL type definitions
- **[Cypher Patterns](./interfaces/cypher/patterns.cypher)** - Common Neo4j query patterns

## Documentation Structure

```
docs/
├── README.md                    # This file - documentation index
├── requirements.md              # Application requirements and specifications
├── design-principles.md         # Core design principles and patterns
├── decisions-log.md            # Integration decisions and rationale
├── risks.md                     # Risk tracking and mitigation
│
├── domains/                     # Business domain documentation
│   ├── feed/                    # Feed domain (ingestion, display)
│   │   ├── README.md
│   │   ├── data-model.md
│   │   ├── schema.md
│   │   ├── mock-data-guide.md
│   │   └── graphql-mock-data-generation.md
│   └── subscriptions/           # Subscriptions domain (sources, rules)
│       ├── README.md
│       ├── data-model.md
│       ├── schema.md
│       └── user-stories.md
│
├── architecture/                # Technical architecture
│   └── adr/                     # Architecture Decision Records
│       ├── graphql-over-rest.md
│       ├── neo4j-graph-database.md
│       ├── valkey-caching-layer.md
│       ├── unified-ingestion-layer.md
│       ├── bunny-feed-integration.md
│       └── [18 more ADRs...]
│
├── interfaces/                  # API contracts and schemas
│   ├── graphql/
│   │   └── schema.graphql      # Complete GraphQL schema
│   └── cypher/
│       └── patterns.cypher     # Common Neo4j query patterns
│
└── [integration docs]           # Bunny and Reader integration analysis
    ├── bunny-*.md
    └── reader-*.md
```

## Documentation Principles

### 1. Domain-Driven Organization

Documentation is organized by business domain (Feed, Subscriptions) rather than technology stack. This makes it easier for domain experts to find relevant information and for new team members to understand the system's purpose.

### 2. Documentation as Code

- Documentation lives in version control alongside code
- ADRs explain **why** decisions were made
- Code comments explain **how** things work
- READMEs provide domain context and quick starts

### 3. Single Source of Truth

- GraphQL schema is defined in code (`app/backend/src/schema/`)
- Documentation references the actual schema, doesn't duplicate it
- When schemas change, documentation is updated in the same commit

### 4. Examples Everywhere

Every API endpoint, query pattern, and workflow includes runnable examples. Documentation should enable developers to be productive immediately.

### 5. Progressive Detail

- **README files**: Quick start and overview (this level)
- **Domain docs**: Detailed domain concepts and patterns
- **ADRs**: Deep technical rationale and alternatives considered
- **Code**: Implementation details

## How to Use This Documentation

### For New Team Members

1. Start with [Requirements](./requirements.md) to understand what the system does
2. Read [Design Principles](./design-principles.md) to understand architectural philosophy
3. Explore domain documentation ([Feed](./domains/feed/README.md), [Subscriptions](./domains/subscriptions/README.md))
4. Review relevant ADRs when implementing features

### For Developers

1. **Starting a new feature**: Check domain docs for existing patterns
2. **Making architectural decisions**: Review ADRs and create new ones for significant decisions
3. **Debugging**: Check domain data models and GraphQL schemas
4. **Integration work**: Review integration documentation (Bunny, Reader)

### For Product/Design

1. Review [Requirements](./requirements.md) for feature specifications
2. Check [User Stories](./domains/subscriptions/user-stories.md) for feature context
3. Review [Integration Summaries](./bunny-integration-summary.md) for UI/UX patterns

## Keeping Documentation Current

- **When adding features**: Update domain docs and create ADRs for architectural decisions
- **When changing APIs**: Update GraphQL schema docs and domain schemas
- **When fixing bugs**: Update risks.md if the bug revealed a new risk
- **When making decisions**: Add to decisions-log.md

## Project Context

Bunny has been refactored into a unified application structure:

- **Frontend**: `app/frontend/` - Astro 4 + React 19 with Bunny components
- **Backend**: `app/backend/` - Node.js + Express with Apollo GraphQL Server
- **Components**: Bunny components in `app/frontend/src/components/bunny/`
- **Reader**: Reader components in `app/frontend/src/components/reader/`
- **Archive**: Original extracted components in `archive/` for reference

The system uses:
- **Neo4j** for graph-native data modeling
- **Valkey** for high-performance caching
- **GraphQL** for flexible API queries
- **Docker** for consistent development environments


