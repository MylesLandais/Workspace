# Bunny - Feed Manager System

Control plane for content ingestion from Reddit, with a Scrolller-like feed interface.

## Architecture

- **Frontend**: Astro + React (Docker-based development)
- **Backend**: Phoenix + Ash → GraphQL API
- **Database**: Neo4j (graph database)
- **Runtime**: Bun

## Quick Start

### Frontend Development

```bash
cd frontend
docker-compose up --build
```

Visit `http://localhost:4321`

## Documentation

See `/docs` for complete documentation:

- [Main Documentation](./docs/README.md)
- [Feed Domain](./docs/domains/feed/README.md)
- [Subscriptions Domain](./docs/domains/subscriptions/README.md)
- [Architecture Decisions](./docs/architecture/adr/)
- [Risks & Mitigations](./docs/risks.md)

## Project Structure

```
.
├── frontend/          # Astro frontend application
├── docs/              # Project documentation
└── README.md          # This file
```


