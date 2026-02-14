#!/bin/bash
# Wrapper script to run Phoenix server and keep it alive

set -e

cd /workspace/dnd_app

# Set Neo4j URL if not provided
export NEO4J_URL="${NEO4J_URL:-bolt://172.17.0.4:7687}"
export NEO4J_USER="${NEO4J_USER:-neo4j}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-password}"

echo "Starting Phoenix server with Neo4j at: $NEO4J_URL"

# Run the server and catch any exits
# Use exec to replace shell with mix process
exec mix phx.server

