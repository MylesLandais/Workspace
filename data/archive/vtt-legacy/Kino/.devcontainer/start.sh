#!/bin/bash
# Quick start script for devcontainer using Docker Compose directly
# Use this if the Dev Containers extension isn't available in Cursor

set -e

echo "🚀 Starting DevContainer services with Docker Compose..."
echo ""

# Navigate to .devcontainer directory
cd "$(dirname "$0")"

# Start services
echo "📦 Starting containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for Neo4j to be healthy..."
timeout=60
counter=0
while ! docker-compose exec -T neo4j cypher-shell -u neo4j -p password "RETURN 1" > /dev/null 2>&1; do
  if [ $counter -ge $timeout ]; then
    echo "❌ Neo4j failed to start within $timeout seconds"
    exit 1
  fi
  echo -n "."
  sleep 2
  counter=$((counter + 2))
done
echo ""
echo "✅ Neo4j is ready!"

echo ""
echo "📥 Installing dependencies..."
docker-compose exec -T app bash -c "cd dnd_app && mix deps.get"

echo ""
echo "✅ DevContainer is ready!"
echo ""
echo "To enter the container:"
echo "  docker-compose exec app bash"
echo ""
echo "Then inside the container:"
echo "  cd dnd_app"
echo "  mix phx.server"
echo ""
echo "Access the app at: http://localhost:4000"
echo "Access Neo4j Browser at: http://localhost:7474"
echo ""
echo "To stop: docker-compose down"




