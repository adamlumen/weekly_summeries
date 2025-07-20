#!/bin/bash
# Docker run script for intelligent agent

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
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -i, --image IMAGE   Docker image name (default: intelligent-agent-basic)"
    echo "  -p, --port PORT     Host port to bind to (default: 8000)"
    echo "  -n, --name NAME     Container name (default: intelligent-agent-container)"
    echo "  -e, --env ENV_FILE  Environment file (default: .env)"
    echo "  -d, --detach        Run in detached mode"
    echo "  -r, --remove        Remove container after it exits"
    echo "  -b, --build         Build image before running"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run with defaults"
    echo "  $0 --port 8080 --detach             # Run on port 8080 in background"
    echo "  $0 --image intelligent-agent-poetry  # Run poetry image"
    echo "  $0 --build --remove                  # Build and run with cleanup"
}

# Default values
IMAGE_NAME="intelligent-agent-basic"
HOST_PORT="8000"
CONTAINER_NAME="intelligent-agent-container"
ENV_FILE=".env"
DETACHED=false
REMOVE_AFTER=false
BUILD_FIRST=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -p|--port)
            HOST_PORT="$2"
            shift 2
            ;;
        -n|--name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -e|--env)
            ENV_FILE="$2"
            shift 2
            ;;
        -d|--detach)
            DETACHED=true
            shift
            ;;
        -r|--remove)
            REMOVE_AFTER=true
            shift
            ;;
        -b|--build)
            BUILD_FIRST=true
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

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

print_info "Preparing to run Docker container..."
print_info "Image: $IMAGE_NAME"
print_info "Port: $HOST_PORT:8000"
print_info "Container name: $CONTAINER_NAME"

# Change to project root
cd "$PROJECT_ROOT"

# Build first if requested
if [[ "$BUILD_FIRST" == true ]]; then
    print_info "Building image first..."
    if [[ "$IMAGE_NAME" == "intelligent-agent-basic" ]]; then
        BUILD_TYPE="basic"
    elif [[ "$IMAGE_NAME" == "intelligent-agent-poetry" ]]; then
        BUILD_TYPE="poetry"
    elif [[ "$IMAGE_NAME" == "intelligent-agent-main" ]]; then
        BUILD_TYPE="main"
    else
        print_warning "Cannot determine build type from image name, using basic"
        BUILD_TYPE="basic"
    fi
    
    "$SCRIPT_DIR/build.sh" --type "$BUILD_TYPE" --name "$IMAGE_NAME"
fi

# Check if image exists
if ! docker images "$IMAGE_NAME" --format '{{.Repository}}:{{.Tag}}' | grep -q "$IMAGE_NAME"; then
    print_error "Docker image '$IMAGE_NAME' not found. Build it first with --build option."
    exit 1
fi

# Stop and remove existing container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_warning "Container '$CONTAINER_NAME' already exists. Stopping and removing..."
    docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi

# Build Docker run command
DOCKER_CMD="docker run"

if [[ "$DETACHED" == true ]]; then
    DOCKER_CMD="$DOCKER_CMD -d"
fi

if [[ "$REMOVE_AFTER" == true ]]; then
    DOCKER_CMD="$DOCKER_CMD --rm"
fi

DOCKER_CMD="$DOCKER_CMD -p ${HOST_PORT}:8000"
DOCKER_CMD="$DOCKER_CMD --name $CONTAINER_NAME"

# Add environment file if it exists
if [[ -f "$ENV_FILE" ]]; then
    DOCKER_CMD="$DOCKER_CMD --env-file $ENV_FILE"
    print_info "Using environment file: $ENV_FILE"
else
    print_warning "Environment file not found: $ENV_FILE"
fi

DOCKER_CMD="$DOCKER_CMD $IMAGE_NAME"

print_info "Running: $DOCKER_CMD"

# Execute run command
if eval "$DOCKER_CMD"; then
    if [[ "$DETACHED" == true ]]; then
        print_success "Container started successfully in detached mode"
        print_info "Container ID: $(docker ps --filter name=$CONTAINER_NAME --format '{{.ID}}')"
        print_info "View logs: docker logs $CONTAINER_NAME"
        print_info "Stop container: docker stop $CONTAINER_NAME"
    else
        print_success "Container started successfully"
    fi
    
    print_info "API will be available at: http://localhost:$HOST_PORT"
    print_info "API documentation: http://localhost:$HOST_PORT/docs"
else
    print_error "Failed to start Docker container"
    exit 1
fi
