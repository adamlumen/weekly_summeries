#!/bin/bash
# Docker build script for intelligent agent

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
    echo "  -t, --type TYPE     Build type: basic, poetry, main (default: basic)"
    echo "  -n, --name NAME     Image name (default: intelligent-agent-TYPE)"
    echo "  -f, --force         Force rebuild without cache"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --type basic                   # Build basic image"
    echo "  $0 --type poetry --name my-agent  # Build poetry image with custom name"
    echo "  $0 --force                        # Force rebuild basic image"
}

# Default values
BUILD_TYPE="basic"
IMAGE_NAME=""
FORCE_BUILD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_BUILD=true
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

# Validate build type
if [[ ! "$BUILD_TYPE" =~ ^(basic|poetry|main)$ ]]; then
    print_error "Invalid build type: $BUILD_TYPE. Must be one of: basic, poetry, main"
    exit 1
fi

# Set default image name if not provided
if [[ -z "$IMAGE_NAME" ]]; then
    IMAGE_NAME="intelligent-agent-$BUILD_TYPE"
fi

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

print_info "Building Docker image..."
print_info "Build type: $BUILD_TYPE"
print_info "Image name: $IMAGE_NAME"
print_info "Project root: $PROJECT_ROOT"

# Change to project root
cd "$PROJECT_ROOT"

# Determine Dockerfile path
DOCKERFILE_PATH="docker/Dockerfile.$BUILD_TYPE"

if [[ ! -f "$DOCKERFILE_PATH" ]]; then
    print_error "Dockerfile not found: $DOCKERFILE_PATH"
    exit 1
fi

# Build Docker command
DOCKER_CMD="docker build -f $DOCKERFILE_PATH -t $IMAGE_NAME"

if [[ "$FORCE_BUILD" == true ]]; then
    DOCKER_CMD="$DOCKER_CMD --no-cache"
    print_warning "Force rebuild enabled (--no-cache)"
fi

DOCKER_CMD="$DOCKER_CMD ."

print_info "Running: $DOCKER_CMD"

# Execute build
if eval "$DOCKER_CMD"; then
    print_success "Docker image built successfully: $IMAGE_NAME"
    
    # Show image info
    print_info "Image details:"
    docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedAt}}"
else
    print_error "Docker build failed"
    exit 1
fi
