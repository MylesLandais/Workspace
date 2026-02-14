#!/bin/bash
# Quick start script for D&D App
# Supports both local and container environments

set -e

# Colors for output (optional, but helpful)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect if we're in a container
IN_CONTAINER=false
if [ -f /.dockerenv ] || [ -n "${CONTAINER}" ]; then
  IN_CONTAINER=true
fi

# Detect if we should use docker exec for commands
USE_DOCKER_EXEC=false
if [ "$IN_CONTAINER" = false ] && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^jupyter$"; then
  USE_DOCKER_EXEC=true
fi

# Function to run commands (either directly or via docker exec)
run_cmd() {
  if [ "$USE_DOCKER_EXEC" = true ]; then
    docker exec -it jupyter "$@"
  else
    "$@"
  fi
}

echo "Starting D&D 5e Character Creator..."
echo ""

# Check if we're in the right directory
if [ ! -f "mix.exs" ]; then
  echo -e "${RED}Error: mix.exs not found. Are you in the dnd_app directory?${NC}"
  exit 1
fi

# Check if Elixir is installed
if ! command -v mix &> /dev/null && [ "$USE_DOCKER_EXEC" = false ]; then
  echo -e "${RED}Error: Elixir/Mix not found.${NC}"
  if [ "$USE_DOCKER_EXEC" = false ]; then
    echo "Please install Elixir first:"
    echo "  Visit: https://elixir-lang.org/install.html"
    echo ""
    echo "Or if you're using the jupyter container, make sure it's running:"
    echo "  docker ps | grep jupyter"
  fi
  exit 1
fi

if [ "$USE_DOCKER_EXEC" = true ]; then
  echo -e "${GREEN}Using jupyter container for commands${NC}"
  ELIXIR_VERSION=$(run_cmd elixir --version 2>/dev/null | head -1 || echo "unknown")
else
  ELIXIR_VERSION=$(elixir --version | head -1)
fi

echo -e "${GREEN}Elixir found: ${ELIXIR_VERSION}${NC}"
echo ""

# Check if dependencies are installed
if [ ! -d "deps" ] || [ -z "$(ls -A deps 2>/dev/null)" ]; then
  echo "Installing Elixir dependencies..."
  run_cmd mix deps.get
  echo ""
fi

# Check if node_modules exist
if [ ! -d "assets/node_modules" ]; then
  echo "Installing Node.js dependencies..."
  if [ "$USE_DOCKER_EXEC" = true ]; then
    run_cmd bash -c "cd /workspace/dnd_app/assets && npm install"
  else
    cd assets
    npm install
    cd ..
  fi
  echo ""
fi

# Check compilation status
echo "Checking compilation status..."
if ! run_cmd mix compile --warnings-as-errors=false &>/dev/null; then
  echo -e "${YELLOW}Warning: Code has compilation warnings or errors${NC}"
  echo "Attempting to compile to see issues..."
  run_cmd mix compile
  echo ""
fi

# Check if Neo4j is running
echo "Checking Neo4j connection..."

NEO4J_RUNNING=false
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q neo4j; then
  echo -e "${GREEN}Neo4j container is running${NC}"
  NEO4J_RUNNING=true
elif command -v lsof &> /dev/null && lsof -i :7687 &> /dev/null; then
  echo -e "${GREEN}Neo4j appears to be running on port 7687${NC}"
  NEO4J_RUNNING=true
elif netstat -tuln 2>/dev/null | grep -q :7687; then
  echo -e "${GREEN}Neo4j appears to be running on port 7687${NC}"
  NEO4J_RUNNING=true
fi

if [ "$NEO4J_RUNNING" = false ]; then
  echo -e "${YELLOW}Warning: Neo4j doesn't appear to be running${NC}"
  echo "The server will attempt to connect, but may fail."
  echo ""
  echo "To start Neo4j with Docker:"
  echo "  docker run -d --name neo4j-dnd -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5-community"
  echo ""
  echo "For more thorough diagnostics, run: bin/check"
  echo ""
  read -p "Continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Check if port 4000 is available
if command -v lsof &> /dev/null && lsof -i :4000 &> /dev/null; then
  echo -e "${YELLOW}Warning: Port 4000 is already in use${NC}"
  echo "Another process may be using the port."
  echo "You can change the port in config/dev.exs if needed."
  echo ""
  read -p "Continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

echo ""
echo -e "${GREEN}Starting Phoenix server...${NC}"
echo "Open http://localhost:4000 in your browser"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
run_cmd mix phx.server
