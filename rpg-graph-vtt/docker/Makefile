.PHONY: help build up down restart logs shell test clean

# Default target
help:
	@echo "RPG Graph VTT Docker Commands"
	@echo ""
	@echo "  make build          - Build the Docker image"
	@echo "  make up             - Start the service"
	@echo "  make up-db          - Start service with local Neo4j"
	@echo "  make down           - Stop the service"
	@echo "  make restart        - Restart the service"
	@echo "  make logs           - View service logs"
	@echo "  make shell          - Open shell in container"
	@echo "  make test           - Run tests in container"
	@echo "  make clean          - Remove containers and volumes"
	@echo "  make validate       - Validate service is running"
	@echo ""

# Build the Docker image
build:
	docker compose build

# Start the service
up:
	docker compose up -d
	@echo "Service starting at http://localhost:8000"

# Start with local Neo4j
up-db:
	docker compose --profile local-db up -d
	@echo "Service with local Neo4j starting..."
	@echo "  - Web UI: http://localhost:8000"
	@echo "  - Neo4j Browser: http://localhost:7474"

# Stop the service
down:
	docker compose down

# Restart the service
restart: down up

# View logs
logs:
	docker compose logs -f rpg-graph-vtt

# Open shell in container
shell:
	docker compose exec rpg-graph-vtt /bin/bash

# Run tests
test:
	docker compose exec rpg-graph-vtt pytest tests/ -v

# Clean up
clean:
	docker compose down -v
	docker system prune -f

# Validate service
validate:
	@echo "Validating service..."
	@curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8000/ || echo "Service not responding"
	@curl -s -o /dev/null -w "API Status: %{http_code}\n" http://localhost:8000/api/characters || echo "API not responding"



