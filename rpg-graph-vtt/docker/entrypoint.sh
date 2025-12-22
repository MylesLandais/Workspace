#!/bin/bash
# Entrypoint script for RPG Graph VTT container

set -e

echo "=== RPG Graph VTT Service Starting ==="

# Check for required environment variables
if [ -z "$NEO4J_URI" ]; then
    echo "ERROR: NEO4J_URI environment variable is not set"
    exit 1
fi

if [ -z "$NEO4J_PASSWORD" ]; then
    echo "ERROR: NEO4J_PASSWORD environment variable is not set"
    exit 1
fi

echo "Neo4j URI: $NEO4J_URI"
echo "Neo4j Username: ${NEO4J_USERNAME:-neo4j}"

# Wait for Neo4j to be ready (if using local Neo4j)
if [[ "$NEO4J_URI" == *"localhost"* ]] || [[ "$NEO4J_URI" == *"neo4j"* ]]; then
    echo "Waiting for Neo4j to be ready..."
    timeout=60
    elapsed=0
    while ! curl -s http://localhost:7474 > /dev/null 2>&1; do
        if [ $elapsed -ge $timeout ]; then
            echo "WARNING: Neo4j did not become ready within $timeout seconds"
            break
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
fi

# Run database migrations if they exist
if [ -d "/app/database/migrations" ]; then
    echo "Database migrations directory found (migrations should be run manually via notebooks)"
fi

# Start the server
echo "Starting FastAPI server..."
exec "$@"



