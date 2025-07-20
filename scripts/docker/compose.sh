#!/bin/bash
# Docker Compose management script for intelligent agent

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  up        Start services"
    echo "  down      Stop services"
    echo "  restart   Restart services"
    echo "  logs      Show logs"
    echo "  status    Show service status"
    echo "  build     Build services"
    echo ""
    echo "Options:"
    echo "  -f, --file FILE     Compose file (default: simple)"
    echo "  -d, --detach        Run in detached mode (for up command)"
    echo "  -b, --build         Build before starting (for up command)"
    echo "  -v, --volumes       Remove volumes (for down command)"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Available compose files:"
    echo "  simple    - Basic setup (docker-compose.simple.yml)"
    echo "  poetry    - Poetry-based setup (docker-compose.poetry.yml)"
    echo "  full      - Full setup with all services (docker-compose.yml)"
    echo ""
    echo "Examples:"
    echo "  $0 up                           # Start simple setup"
    echo "  $0 up --file poetry --detach    # Start poetry setup in background"
    echo "  $0 down --volumes               # Stop and remove volumes"
    echo "  $0 logs                         # Show logs"
}

# Default values
COMPOSE_FILE="simple"
DETACHED=false
BUILD_FIRST=false
REMOVE_VOLUMES=false
COMMAND=""

# Parse command line arguments
if [[ $# -eq 0 ]]; then
    usage
    exit 1
fi

COMMAND="$1"
shift

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        -d|--detach)
            DETACHED=true
            shift
            ;;
        -b|--build)
            BUILD_FIRST=true
            shift
            ;;
        -v|--volumes)
            REMOVE_VOLUMES=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate command
if [[ ! "$COMMAND" =~ ^(up|down|restart|logs|status|build)$ ]]; then
    print_error "Invalid command: $COMMAND"
    usage
    exit 1
fi

# Validate compose file
if [[ ! "$COMPOSE_FILE" =~ ^(simple|poetry|full)$ ]]; then
    print_error "Invalid compose file: $COMPOSE_FILE. Must be one of: simple, poetry, full"
    exit 1
fi

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Determine compose file path
case $COMPOSE_FILE in
    simple)
        COMPOSE_FILE_PATH="docker/compose/docker-compose.simple.yml"
        ;;
    poetry)
        COMPOSE_FILE_PATH="docker/compose/docker-compose.poetry.yml"
        ;;
    full)
        COMPOSE_FILE_PATH="docker/compose/docker-compose.yml"
        ;;
esac

print_info "Managing Docker Compose services..."
print_info "Command: $COMMAND"
print_info "Compose file: $COMPOSE_FILE_PATH"

# Change to project root
cd "$PROJECT_ROOT"

# Check if compose file exists
if [[ ! -f "$COMPOSE_FILE_PATH" ]]; then
    print_error "Compose file not found: $COMPOSE_FILE_PATH"
    exit 1
fi

# Execute command
case $COMMAND in
    up)
        DOCKER_CMD="docker-compose -f $COMPOSE_FILE_PATH up"
        
        if [[ "$BUILD_FIRST" == true ]]; then
            DOCKER_CMD="$DOCKER_CMD --build"
        fi
        
        if [[ "$DETACHED" == true ]]; then
            DOCKER_CMD="$DOCKER_CMD -d"
        fi
        
        print_info "Starting services..."
        print_info "Running: $DOCKER_CMD"
        
        if eval "$DOCKER_CMD"; then
            print_success "Services started successfully"
            
            if [[ "$DETACHED" == true ]]; then
                print_info "Services running in background"
                print_info "View logs: $0 logs --file $COMPOSE_FILE"
                print_info "Stop services: $0 down --file $COMPOSE_FILE"
            fi
            
            print_info "API will be available at: http://localhost:8000"
            print_info "API documentation: http://localhost:8000/docs"
        else
            print_error "Failed to start services"
            exit 1
        fi
        ;;
        
    down)
        DOCKER_CMD="docker-compose -f $COMPOSE_FILE_PATH down"
        
        if [[ "$REMOVE_VOLUMES" == true ]]; then
            DOCKER_CMD="$DOCKER_CMD --volumes"
        fi
        
        print_info "Stopping services..."
        print_info "Running: $DOCKER_CMD"
        
        if eval "$DOCKER_CMD"; then
            print_success "Services stopped successfully"
        else
            print_error "Failed to stop services"
            exit 1
        fi
        ;;
        
    restart)
        print_info "Restarting services..."
        
        # Stop first
        docker-compose -f "$COMPOSE_FILE_PATH" down
        
        # Start again
        DOCKER_CMD="docker-compose -f $COMPOSE_FILE_PATH up"
        if [[ "$DETACHED" == true ]]; then
            DOCKER_CMD="$DOCKER_CMD -d"
        fi
        
        if eval "$DOCKER_CMD"; then
            print_success "Services restarted successfully"
        else
            print_error "Failed to restart services"
            exit 1
        fi
        ;;
        
    logs)
        print_info "Showing logs..."
        docker-compose -f "$COMPOSE_FILE_PATH" logs -f
        ;;
        
    status)
        print_info "Service status:"
        docker-compose -f "$COMPOSE_FILE_PATH" ps
        ;;
        
    build)
        print_info "Building services..."
        if docker-compose -f "$COMPOSE_FILE_PATH" build; then
            print_success "Services built successfully"
        else
            print_error "Failed to build services"
            exit 1
        fi
        ;;
esac
