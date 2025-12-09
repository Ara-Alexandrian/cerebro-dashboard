#!/bin/bash
#
# Cerebro Dashboard Deployment Script
# Usage: ./deploy.sh [build|up|down|restart|logs|status]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Container names
BACKEND_CONTAINER="cerebro-backend"
FRONTEND_CONTAINER="cerebro-frontend"
NETWORK="azerothcore"

# Image names
BACKEND_IMAGE="cerebro-backend:latest"
FRONTEND_IMAGE="cerebro-frontend:latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Build images
build() {
    log_info "Building backend image..."
    docker build -t "$BACKEND_IMAGE" ./backend
    log_success "Backend built"

    log_info "Building frontend image..."
    docker build -t "$FRONTEND_IMAGE" ./frontend
    log_success "Frontend built"
}

# Stop and remove containers
down() {
    log_info "Stopping containers..."
    docker stop "$FRONTEND_CONTAINER" "$BACKEND_CONTAINER" 2>/dev/null || true
    docker rm "$FRONTEND_CONTAINER" "$BACKEND_CONTAINER" 2>/dev/null || true
    log_success "Containers stopped and removed"
}

# Start containers
up() {
    log_info "Starting backend container..."
    docker run -d \
        --name "$BACKEND_CONTAINER" \
        --network "$NETWORK" \
        -p 8086:8080 \
        -e POSTGRES_HOST=azerothcore-pgvector \
        -e POSTGRES_PORT=5432 \
        -e POSTGRES_USER=azeroth \
        -e POSTGRES_PASSWORD=azeroth \
        -e POSTGRES_DB=azeroth_vectors \
        -e REDIS_HOST=172.21.0.11 \
        -e REDIS_PORT=6379 \
        -e VLLM_URL=http://172.21.0.3:8000 \
        -e AC_BIN_PATH=/mnt/nextorage/appdata/wotlk/server/bin \
        -e AC_ETC_PATH=/mnt/nextorage/appdata/wotlk/server/etc \
        -e AC_SERVER_HOST=azerothcore-server \
        -e AC_WORLD_PORT=8085 \
        -e AC_AUTH_PORT=3724 \
        -e AC_SOAP_HOST=azerothcore-server \
        -e AC_SOAP_PORT=7878 \
        -e AC_SOAP_USER=scaldor \
        -e "AC_SOAP_PASS=321\$" \
        -e AC_DOCKER_CONTAINER=azerothcore-server \
        -v /mnt/nextorage/appdata/wotlk/server/etc:/mnt/nextorage/appdata/wotlk/server/etc:rw \
        -v /var/run/docker.sock:/var/run/docker.sock \
        --restart unless-stopped \
        "$BACKEND_IMAGE"
    log_success "Backend started"

    log_info "Starting frontend container..."
    docker run -d \
        --name "$FRONTEND_CONTAINER" \
        --network "$NETWORK" \
        -p 3000:3000 \
        -e ORIGIN=http://localhost:3000 \
        --restart unless-stopped \
        "$FRONTEND_IMAGE"
    log_success "Frontend started"

    log_info "Waiting for services to be ready..."
    sleep 3
    status
}

# Show container status
status() {
    echo ""
    log_info "Container Status:"
    docker ps --filter "name=cerebro" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""

    log_info "Testing backend API..."
    if curl -sf http://localhost:8086/api/server/status > /dev/null 2>&1; then
        log_success "Backend API is responding"
        echo "  Server status: $(curl -s http://localhost:8086/api/server/status)"
    else
        log_warn "Backend API not responding yet"
    fi

    echo ""
    log_info "Testing frontend..."
    if curl -sf http://localhost:3000 > /dev/null 2>&1; then
        log_success "Frontend is responding"
    else
        log_warn "Frontend not responding yet"
    fi

    echo ""
    log_info "Access URLs:"
    echo "  Dashboard: http://localhost:3000"
    echo "  Backend API: http://localhost:8086/api"
}

# Show logs
logs() {
    local service="${1:-all}"
    case "$service" in
        backend)
            docker logs -f "$BACKEND_CONTAINER"
            ;;
        frontend)
            docker logs -f "$FRONTEND_CONTAINER"
            ;;
        all)
            docker logs --tail 50 "$BACKEND_CONTAINER"
            echo "---"
            docker logs --tail 50 "$FRONTEND_CONTAINER"
            ;;
        *)
            log_error "Unknown service: $service"
            echo "Usage: $0 logs [backend|frontend|all]"
            ;;
    esac
}

# Restart (full rebuild and redeploy)
restart() {
    down
    build
    up
}

# Quick restart (no rebuild)
quick_restart() {
    down
    up
}

# Main
case "${1:-help}" in
    build)
        build
        ;;
    up)
        up
        ;;
    down)
        down
        ;;
    restart)
        restart
        ;;
    quick)
        quick_restart
        ;;
    logs)
        logs "${2:-all}"
        ;;
    status)
        status
        ;;
    help|*)
        echo "Cerebro Dashboard Deployment"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  build     Build Docker images"
        echo "  up        Start containers"
        echo "  down      Stop and remove containers"
        echo "  restart   Full rebuild and restart"
        echo "  quick     Quick restart (no rebuild)"
        echo "  logs      Show logs (logs [backend|frontend|all])"
        echo "  status    Show container status and test endpoints"
        echo ""
        ;;
esac
