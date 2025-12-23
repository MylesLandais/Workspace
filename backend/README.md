# Bunny Backend

Node.js/TypeScript GraphQL API server connected to Neo4j Aura database.

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
├── index.ts              # Express + Apollo Server setup
├── schema/
│   └── schema.ts         # GraphQL type definitions
├── resolvers/
│   ├── queries.ts        # Query resolvers
│   └── mutations.ts     # Mutation resolvers
└── neo4j/
    ├── driver.ts         # Neo4j connection
    └── queries/          # Cypher query functions
        ├── feed.ts
        ├── creators.ts
        └── sources.ts
```

