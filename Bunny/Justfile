# Bunny Development Justfile
# Shared services model - backing services managed by data engineering/MLOps

set shell := ["bash", "-uc"]

# Default: show help
default:
    @just --list

# === Shared Services ===

# Check status of shared services
services-status:
    @echo "Shared Services Status:"
    @echo ""
    @echo "MySQL (mysql-scheduler.jupyter.dev.local:3307):"
    @docker ps --filter name=mysql-scheduler.jupyter.dev.local --format "  {{.Status}}" || echo "  Not running"
    @echo ""
    @echo "Valkey (cache.jupyter.dev.local:6379):"
    @docker ps --filter name=cache.jupyter.dev.local --format "  {{.Status}}" || echo "  Not running"
    @echo ""
    @echo "Neo4j (neo4j-devenv:7474/7687):"
    @docker ps --filter name=neo4j-devenv --format "  {{.Status}}" || echo "  Not running"
    @echo ""
    @echo "MinIO (s3.jupyter.dev.local:9000):"
    @docker ps --filter name=s3.jupyter.dev.local --format "  {{.Status}}" || echo "  Not running"

# === Wait Utilities ===

# Wait for MySQL to accept connections (TCP check)
wait-for-db:
    @echo "Waiting for shared MySQL (port 3307)..."
    @while ! nc -z localhost 3307 2>/dev/null; do \
        sleep 2; \
    done
    @echo "MySQL is ready!"

# Wait for all shared services
wait-for-all: wait-for-db
    @echo "Checking Valkey (port 6379)..."
    @while ! nc -z localhost 6379 2>/dev/null; do sleep 2; done
    @echo "Valkey ready!"
    @echo "Checking Neo4j (port 7474)..."
    @while ! nc -z localhost 7474 2>/dev/null; do sleep 2; done
    @echo "Neo4j ready!"
    @echo "All shared services ready!"

# === Development ===

# Start dev environment
dev: wait-for-db
    devenv up

# Install all dependencies
install:
    cd apps/web && bun install
    cd apps/api && bun install

# === Database ===

# Create bunny_auth database if missing
db-create:
    docker exec mysql-scheduler.jupyter.dev.local mysql -u root -psecret -e "CREATE DATABASE IF NOT EXISTS bunny_auth;"
    @echo "Database bunny_auth created/verified"

# Push Drizzle schema to MySQL
db-push: wait-for-db
    cd apps/web && bun run db:push

# Open Drizzle Studio
db-studio:
    cd apps/web && bun run db:studio

# Open MySQL shell
db-shell:
    mysql -h localhost -P 3307 -u root -psecret bunny_auth

# === Testing ===

# Run unit tests
test:
    cd apps/web && bun test

# Run E2E tests
e2e:
    cd apps/web && bun run test:e2e

# Run all tests
test-all: test e2e

# === Build ===

# Build Next.js app
build:
    cd apps/web && bun run build

# Run Lighthouse performance audit
perf:
    lighthouse http://localhost:3000 --view

# === GraphQL Server ===

# Start GraphQL server
server-start:
    cd apps/api && docker compose up -d

# Stop GraphQL server
server-stop:
    cd apps/api && docker compose down

# View GraphQL server logs
server-logs:
    cd apps/api && docker compose logs -f
