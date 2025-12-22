#!/bin/bash
# Startup script for Phoenix server in container
# Sets Neo4j connection and starts the server

set -e

cd /workspace/dnd_app

# Try to get Neo4j container IP from host
# This works if docker socket is accessible, otherwise use fallback
NEO4J_IP=""
if command -v docker >/dev/null 2>&1; then
  NEO4J_IP=$(docker inspect neo4j --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "")
fi

# Set default Neo4j URL if not provided
if [ -z "$NEO4J_URL" ]; then
  if [ -n "$NEO4J_IP" ]; then
    export NEO4J_URL="bolt://${NEO4J_IP}:7687"
  else
    # Fallback to host.docker.internal or localhost
    export NEO4J_URL="bolt://host.docker.internal:7687"
  fi
fi

# Set default Neo4j credentials if not provided
export NEO4J_USER="${NEO4J_USER:-neo4j}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-password}"

echo "Starting Phoenix server..."
echo "Neo4j URL: $NEO4J_URL"
echo "Neo4j User: $NEO4J_USER"
echo "Working directory: $(pwd)"

# Ensure Hex and Rebar are available (non-interactive)
mix local.hex --force || true
mix local.rebar --force || true

# Install dependencies if not already installed
if [ ! -d "deps" ] || [ -z "$(ls -A deps 2>/dev/null)" ]; then
  echo "Installing Elixir dependencies..."
  mix deps.get
fi

# Compile dependencies if needed
echo "Compiling dependencies..."
mix deps.compile || true

# Start Phoenix server (this will run in foreground and keep container alive)
exec mix phx.server

