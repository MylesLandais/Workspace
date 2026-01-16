#!/bin/bash

# Docker Gallery Server Management Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_RESET='\033[0m'

log_info() {
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} $1"
}

log_success() {
    echo -e "${COLOR_GREEN}[SUCCESS]${COLOR_RESET} $1"
}

log_warning() {
    echo -e "${COLOR_YELLOW}[WARNING]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        log_info "Install Docker from https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        log_info "Install Docker Compose from https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    log_success "Docker and Docker Compose are installed"
}

check_port() {
    local port=$1
    if docker ps --format "{{.Ports}}" | grep -q ":$port->"; then
        log_warning "Port $port is already in use by another container"
        return 1
    fi
    
    # Check if port is in use on host
    if command -v lsof &> /dev/null; then
        if lsof -ti:$port &> /dev/null; then
            log_warning "Port $port is in use by a local process"
            return 1
        fi
    fi
    
    return 0
}

build_image() {
    log_info "Building gallery Docker image..."
    cd gallery
    docker-compose -f docker-compose.yml build
    cd ..
    log_success "Image built successfully"
}

start_gallery() {
    log_info "Starting gallery server..."
    
    # Check port
    if ! check_port 8001; then
        log_error "Cannot start - port 8001 is in use"
        log_info "Try: docker-compose down"
        exit 1
    fi
    
    cd gallery
    docker-compose -f docker-compose.yml up -d
    cd ..
    
    log_success "Gallery server started"
    log_info "Access it at: http://localhost:8001"
    log_info "Health check: http://localhost:8001/health"
}

stop_gallery() {
    log_info "Stopping gallery server..."
    cd gallery
    docker-compose -f docker-compose.yml down
    cd ..
    log_success "Gallery server stopped"
}

restart_gallery() {
    log_info "Restarting gallery server..."
    stop_gallery
    start_gallery
}

view_logs() {
    log_info "Viewing gallery logs..."
    cd gallery
    docker-compose -f docker-compose.yml logs -f
}

show_status() {
    log_info "Gallery server status:"
    cd gallery
    docker-compose -f docker-compose.yml ps
    cd ..
}

clean_gallery() {
    log_warning "This will remove all gallery data and containers"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd gallery
        docker-compose -f docker-compose.yml down -v
        cd ..
        log_success "Gallery cleaned up"
    else
        log_info "Cleanup cancelled"
    fi
}

test_connection() {
    log_info "Testing gallery connection..."
    
    # Wait for container to be ready
    log_info "Waiting for server to start..."
    for i in {1..30}; do
        if curl -f http://localhost:8001/health &> /dev/null; then
            log_success "Gallery is accessible!"
            break
        fi
        echo -n "."
        sleep 1
    done
    echo
    
    # Get health status
    log_info "Health check response:"
    curl -s http://localhost:8001/health | python -m json.tool
}

show_help() {
    cat << EOF
Gallery Docker Management Script

Usage: ./docker-manage.sh [COMMAND]

Commands:
    build       Build Docker image
    start       Start gallery server
    stop        Stop gallery server
    restart     Restart gallery server
    logs        View server logs
    status      Show server status
    test        Test server connection
    clean       Remove containers and volumes
    help        Show this help message

Examples:
    ./docker-manage.sh build
    ./docker-manage.sh start
    ./docker-manage.sh logs

Direct access:
    http://localhost:8001
    Health check: http://localhost:8001/health

EOF
}

main() {
    check_docker
    
    case "${1:-help}" in
        build)
            build_image
            ;;
        start)
            start_gallery
            ;;
        stop)
            stop_gallery
            ;;
        restart)
            restart_gallery
            ;;
        logs)
            view_logs
            ;;
        status)
            show_status
            ;;
        test)
            test_connection
            ;;
        clean)
            clean_gallery
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
