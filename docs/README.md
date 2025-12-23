# Documentation

This directory contains all project documentation organized by domain and architecture concerns.

## Quick Navigation

- [Requirements](./requirements.md) - Application requirements and specifications
- [Design Principles](./design-principles.md) - Core design principles and architectural guidelines
- [Feed Domain](./domains/feed/README.md) - Post ingestion, display, and infinite scroll
- [Subscriptions Domain](./domains/subscriptions/README.md) - Subreddit management and ingestion rules
- [Architecture Decisions](./architecture/adr/) - Why we made key technical choices
- [Risks & Mitigations](./risks.md) - Known risks and mitigation strategies

### Lumina Feed Integration

Analysis and integration documentation for the Lumina Feed application:

- **[Integration Summary](./lumina-integration-summary.md)** - START HERE: High-level overview and key findings
- [Lumina Analysis](./lumina-analysis.md) - Complete codebase analysis and feature catalog
- [Tech Stack Conflicts](./lumina-tech-stack-conflicts.md) - Integration challenges and resolution strategies
- [Component Interface Map](./lumina-component-interface-map.md) - UI component specifications and GraphQL operations
- [Data Schema Expectations](./lumina-data-schema-expectations.md) - Neo4j schema requirements and mappings
- [Features & Requirements](./lumina-features-requirements.md) - Feature requirements and user stories
- [Board/FeedGroup Design Exploration](./lumina-board-feedgroup-design.md) - Organizational model design exploration
- [Integration ADR](./architecture/adr/lumina-feed-integration.md) - Architecture decision record for integration
- [Decisions Log](./decisions-log.md) - Log of key integration decisions

### OmniPane Reader Integration

Analysis and integration documentation for the OmniPane Reader application:

- **[Integration Summary](./omnipane-integration-summary.md)** - START HERE: High-level overview and key findings
- [OmniPane Analysis](./omnipane-analysis.md) - Complete codebase analysis and feature catalog
- [Tech Stack Conflicts](./omnipane-tech-stack-conflicts.md) - Integration challenges and resolution strategies
- [Component Interface Map](./omnipane-component-interface-map.md) - UI component specifications and GraphQL operations
- [Data Schema Expectations](./omnipane-data-schema-expectations.md) - Neo4j schema requirements and mappings
- [Features & Requirements](./omnipane-features-requirements.md) - Feature requirements and user stories

## Documentation Principles

1. **Domain-Driven**: Docs organized by business domain, not technology
2. **Docs Close to Code**: Module-level READMEs live with code, high-level docs here
3. **Examples Everywhere**: Every API endpoint has runnable examples
4. **Single Source of Truth**: Schema lives in code, docs reference it

## Structure

```
docs/
├── requirements.md                    # Application requirements and specifications
├── design-principles.md               # Core design principles
├── domains/                           # Business domain documentation
├── architecture/                      # Technical architecture and decisions
│   └── adr/                          # Architecture Decision Records
│       └── lumina-feed-integration.md # Lumina integration decision
├── interfaces/                        # API contracts and schemas
├── risks.md                           # Risk tracking and mitigation
├── lumina-*.md                        # Lumina Feed integration documentation
│   ├── lumina-analysis.md             # Codebase analysis
│   ├── lumina-tech-stack-conflicts.md # Integration challenges
│   ├── lumina-component-interface-map.md # Component specifications
│   ├── lumina-data-schema-expectations.md # Schema requirements
│   └── lumina-features-requirements.md # Features and user stories
└── omnipane-*.md                      # OmniPane Reader integration documentation
    ├── omnipane-analysis.md           # Codebase analysis
    ├── omnipane-tech-stack-conflicts.md # Integration challenges
    ├── omnipane-component-interface-map.md # Component specifications
    ├── omnipane-data-schema-expectations.md # Schema requirements
    └── omnipane-features-requirements.md # Features and user stories
```


