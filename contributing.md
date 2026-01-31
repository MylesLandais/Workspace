# Contributing to Bunny

This guide covers setting up a reproducible development environment using Nix and devenv.

## Prerequisites

- [Nix](https://nixos.org/download.html) with flakes enabled
- [devenv](https://devenv.sh/getting-started/)

## Quick Start

1. Clone the repository and enter the project directory

2. Start the devenv shell:

   ```bash
   devenv shell
   ```

3. Start all services (MySQL, Redis, MinIO, OTEL Collector, Next.js):

   ```bash
   devenv up
   ```

   Or run detached:

   ```bash
   devenv up -d
   ```

4. Initialize the database schema (first time only):

   ```bash
   db-push
   ```

5. Access the application at http://localhost:3000

## Services

The devenv configuration starts the following services:

| Service        | Port      | Description                          |
| -------------- | --------- | ------------------------------------ |
| Next.js        | 3000      | Frontend application                 |
| MySQL          | 3306      | Authentication database (bunny_auth) |
| Redis          | 6379      | Session cache and rate limiting      |
| MinIO          | 9000      | Object storage (S3-compatible)       |
| OTEL Collector | 4317/4318 | Telemetry (gRPC/HTTP)                |

**Additional services (managed separately):**

| Service        | Port      | Description       | Start Command           |
| -------------- | --------- | ----------------- | ----------------------- |
| Neo4j          | 7687/7474 | Graph database    | `neo4j start` or Docker |
| GraphQL Server | 4002      | Apollo Server API | `server-start`          |
| Valkey         | 6380      | Cache for GraphQL | Started with server     |

### Starting the Complete Stack

1. **Start Neo4j** (must be first):

   ```bash
   neo4j start
   # Or with Docker:
   # docker run -d -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j
   ```

2. **Start GraphQL Server** (in devenv shell):

   ```bash
   server-start
   ```

3. **Start Client Services** (in devenv shell):
   ```bash
   devenv up
   ```

See [COMPLETE-SYSTEM-SETUP.md](COMPLETE-SYSTEM-SETUP.md) for detailed architecture.

## Available Commands

Run these commands inside `devenv shell`:

| Command                 | Description                      |
| ----------------------- | -------------------------------- |
| `devenv up`             | Start all services               |
| `devenv up -d`          | Start services in background     |
| `devenv processes stop` | Stop all services                |
| `build-stack`           | Build the client application     |
| `test-stack`            | Run unit tests                   |
| `e2e`                   | Run Playwright E2E tests         |
| `db-push`               | Push schema changes to MySQL     |
| `db-studio`             | Open Drizzle Studio              |
| `analyze-perf`          | Run Lighthouse performance audit |
| `server-start`          | Start GraphQL server (Docker)    |
| `server-stop`           | Stop GraphQL server              |
| `server-logs`           | View GraphQL server logs         |
| `server-status`         | Check GraphQL server status      |

## Database Management

The project uses Drizzle ORM with MySQL for authentication. Schema is defined in:

```
app/client/src/lib/db/schema/mysql-auth.ts
```

To apply schema changes:

```bash
db-push
```

To inspect the database:

```bash
db-studio
```

## Environment Variables

devenv automatically sets these environment variables:

```bash
MYSQL_HOST=localhost
MYSQL_USER=user
MYSQL_PASSWORD=dev_<deterministic_hash>_default
MYSQL_DATABASE=bunny_auth
REDIS_URL=redis://localhost:6380
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

For local overrides, edit `app/client/.env.local` or export `DEVENV_MYSQL_PASSWORD`,
`DEVENV_MINIO_ACCESS_KEY`, and `DEVENV_MINIO_SECRET_KEY` before running `devenv shell`.

## Troubleshooting

### Port conflicts

If services fail to start due to port conflicts:

```bash
devenv processes stop
# Kill any orphaned processes
pkill -f redis-server
pkill -f mysqld
pkill -f minio
```

### Database connection errors

If you see `ENOTFOUND mysql`, ensure `.env.local` uses `localhost`:

```bash
MYSQL_HOST=localhost
```

### Permission errors on .next

If Next.js fails with permission errors on `.next/`:

```bash
sudo rm -rf app/client/.next
```

### Reset database state

To completely reset the database:

```bash
devenv processes stop
rm -rf .devenv/state/mysql
devenv up -d
db-push
```

## Observability

The OTEL Collector receives traces on ports 4317 (gRPC) and 4318 (HTTP). Configure your telemetry backend by modifying the exporter in `devenv.nix`.

To view traces locally, add Jaeger to your setup or use the debug exporter (logs to console).

## Code Style

- Run `prettier` and `eslint` before committing (enforced via git hooks)
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, etc.
