#!/usr/bin/env bash
# Startup script for imageboard crawler with OTEL monitoring

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Imageboard Crawler - OTEL Monitoring Setup ===${NC}"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: docker not found${NC}"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}ERROR: docker compose not available${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and docker compose available${NC}"

# Check if base services are running
echo ""
echo "Checking base services..."
BASE_SERVICES=("jupyterlab" "neo4j" "valkey" "minio")
ALL_BASE_RUNNING=true

for service in "${BASE_SERVICES[@]}"; do
    if docker ps --format "{{.Names}}" | grep -q "$service"; then
        echo -e "${GREEN}✓ $service is running${NC}"
    else
        echo -e "${YELLOW}⚠ $service is not running${NC}"
        ALL_BASE_RUNNING=false
    fi
done

if [ "$ALL_BASE_RUNNING" = false ]; then
    echo ""
    echo -e "${YELLOW}Starting base services...${NC}"
    docker compose up -d neo4j valkey minio jupyterlab
    echo ""
    echo "Waiting for services to be healthy..."
    sleep 15
fi

# Check and stop existing crawler containers
echo ""
echo "Checking for existing crawler containers..."
CRAWLER_CONTAINERS=("imageboard_orchestrator" "imageboard_worker" "imageboard_dashboard" "imageboard_prometheus" "imageboard_pushgateway" "imageboard_metrics_collector")

for container in "${CRAWLER_CONTAINERS[@]}"; do
    if docker ps -a --format "{{.Names}}" | grep -q "$container"; then
        echo "Stopping $container..."
        docker stop "$container" 2>/dev/null || true
        docker rm "$container" 2>/dev/null || true
    fi
done

# Create logs directory
echo ""
echo "Creating logs directory..."
mkdir -p logs/metrics
echo -e "${GREEN}✓ Logs directory created${NC}"

# Start crawler services with monitoring
echo ""
echo -e "${GREEN}=== Starting Crawler Services ===${NC}"
docker compose -f docker-compose.crawler.yml up -d \
    imageboard_orchestrator \
    imageboard_worker \
    imageboard_dashboard \
    prometheus \
    pushgateway \
    metrics_collector

echo ""
echo "Waiting for services to start..."
sleep 10

# Verify services started
echo ""
echo "Verifying services..."
RUNNING_COUNT=0

for service in "${CRAWLER_CONTAINERS[@]}"; do
    if docker ps --format "{{.Names}}" | grep -q "$service"; then
        echo -e "${GREEN}✓ $service is running${NC}"
        ((RUNNING_COUNT++))
    else
        echo -e "${RED}✗ $container failed to start${NC}"
    fi
done

echo ""
if [ $RUNNING_COUNT -eq ${#CRAWLER_CONTAINERS[@]} ]; then
    echo -e "${GREEN}=== All services started successfully! ===${NC}"
else
    echo -e "${YELLOW}=== $RUNNING_COUNT out of ${#CRAWLER_CONTAINERS[@]} services running ===${NC}"
fi

# Display access URLs
echo ""
echo "=== Service Access URLs ==="
echo "Prometheus:   http://localhost:9090"
echo "Pushgateway:   http://localhost:9091"
echo "Dashboard:     http://localhost:5001"
echo "Neo4j:        http://localhost:7474"
echo "MinIO:        http://localhost:9000"
echo ""

# Ask if user wants to start monitoring
echo -e "${YELLOW}=== Start Monitoring? ===${NC}"
echo "Run the following command to start the monitoring session:"
echo ""
echo "  python monitor_imageboard_otel.py --duration 240 --alerts conservative"
echo ""
echo "Or with verbose alerts:"
echo ""
echo "  python monitor_imageboard_otel.py --duration 240 --alerts moderate"
echo ""
echo "Press Ctrl+C at any time to stop the monitoring session"
echo ""
