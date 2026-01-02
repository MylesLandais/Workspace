# Bunny Project Rules

Project-specific instructions for AI assistants working on the Bunny platform.

## Tech Stack

- **Client**: Next.js (App Router) + React 19 + TailwindCSS + Bun runtime
- **Server**: Elysia.js (Bun-native) + Eden (end-to-end type safety)
- **Database**: Neo4j (graph) + Drizzle ORM (relational) + Valkey (cache)
- **Runtime**: Bun for development, builds, and server
- **Testing**: Bun (unit) + Playwright (E2E)
- **Type Safety**: Eden treaty for client-server type inference

## Repository Structure Convention

### Directory Naming Standard

Use clear, purpose-driven names. Avoid vague architectural terms.

**Preferred:**
- `/app`, `/client`, `/web`, `/mobile`, `/desktop`, `/server`, `/api`, `/services`

**Avoid:**
- `/frontend`, `/backend`

### Standard Next.js + Bun Structure

```
/
├── app/                  # Next.js App Router pages and layouts
├── src/                  # Application source code (components, features, business logic)
├── lib/                  # Shared utilities, helpers, and third-party integrations
├── public/               # Static assets (images, fonts, etc.)
├── docker/               # Docker configuration and dev container setup
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .devcontainer/
├── api/                  # API routes (if separated from /app/api)
├── services/             # Backend services, data access, external integrations
└── shared/               # Code shared across multiple apps (monorepo scenarios)
```

### Directory Purposes

**`/app`** - Next.js App Router convention
- Page components, layouts, loading states
- Route handlers (`/app/api/*`)
- Server components and actions

**`/src`** - Core application code
- React components (not page-level)
- Business logic and feature modules
- Application-specific code that doesn't fit in `/lib`

**`/lib`** - Reusable utilities and integrations
- Helper functions and utilities
- Third-party library configurations (Drizzle, Auth, etc.)
- Type definitions and constants
- Database clients, API clients, Eden client

**`/docker`** - Development environment consistency
- Dockerfile for production builds
- docker-compose.yml for local development
- .devcontainer/ for VS Code/Cursor dev containers
- Ensures identical environments across OpenCode, Cursor, and Claude Code

### Guidelines

1. **When adding new code:**
   - UI components → `/src/components`
   - Utilities/helpers → `/lib/utils`
   - Pages/routes → `/app`
   - Database schemas → `/lib/db/schema`
   - API services → `/services` or `/lib`

2. **Docker usage:**
   - All development should happen inside the dev container
   - Ensures Bun runtime consistency across environments
   - Run `docker-compose up` or use dev container in your IDE

3. **Maintain consistency:**
   - Follow existing patterns in the project
   - Avoid creating `/frontend` or `/backend` directories
   - Keep similar code together (colocation principle)

## Type Safety Patterns

### Elysia + Eden
- Define API routes with Elysia's type-safe route handlers
- Use Eden treaty for type-safe client calls
- Types are automatically inferred from server to client

### Drizzle ORM
- Schema definitions in `/lib/db/schema/`
- Use Drizzle's type-safe query builder
- Prefer Drizzle for relational data, Neo4j for graph relationships

## Development Patterns

### Graph-Native First
- Model data as nodes and relationships, not tables
- Use Cypher for traversing relationships
- Leverage graph algorithms over application logic

### Caching Strategy
- Valkey for hot data paths (sub-millisecond)
- Neo4j for complex graph queries
- Cache AI responses and expensive operations

## Code Style

- Use TypeScript strict mode
- Prefer Bun APIs where available
- Follow existing patterns in the codebase
- Keep similar code together (colocation principle)

## Runtime and Package Management

### Docker Compliance Requirement

All `bun` commands must be executed through Docker. Running `bun` directly on the host machine is not permitted per risk and compliance requirements. This includes:

- `bun add <package>`
- `bun install`
- `bun run <script>`
- `bun build`
- Any other `bun` operations

Execute all `bun` commands inside the Docker container using `docker compose exec` or by running commands within an active container shell.

### Package Manager

Replace all `npm` commands with `bun` equivalents:

- `npm install` → `bun install`
- `npm add <package>` → `bun add <package>`
- `npm run <script>` → `bun run <script>`
- `npm ci` → `bun install` (with lockfile)
