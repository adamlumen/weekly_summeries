#!/bin/bash
# Deployment script for intelligent agent

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
    echo "  build         Build production Docker image"
    echo "  deploy        Deploy to production"
    echo "  restart       Restart production services"
    echo "  stop          Stop production services"
    echo "  status        Check deployment status"
    echo "  logs          Show production logs"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV       Environment: staging, production (default: staging)"
    echo "  -i, --image IMAGE   Docker image name (default: auto-generated)"
    echo "  -t, --tag TAG       Image tag (default: latest)"
    echo "  -f, --force         Force deployment without confirmation"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build                           # Build staging image"
    echo "  $0 deploy --env production         # Deploy to production"
    echo "  $0 restart --env staging           # Restart staging services"
}

# Default values
ENVIRONMENT="staging"
IMAGE_NAME=""
IMAGE_TAG="latest"
FORCE_DEPLOY=false
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
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -i|--image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_DEPLOY=true
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
if [[ ! "$COMMAND" =~ ^(build|deploy|restart|stop|status|logs)$ ]]; then
    print_error "Invalid command: $COMMAND"
    usage
    exit 1
fi

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be staging or production"
    exit 1
fi

# Set default image name if not provided
if [[ -z "$IMAGE_NAME" ]]; then
    IMAGE_NAME="intelligent-agent-$ENVIRONMENT"
fi

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

print_info "Deployment management for intelligent agent"
print_info "Command: $COMMAND"
print_info "Environment: $ENVIRONMENT"
print_info "Image: $IMAGE_NAME:$IMAGE_TAG"

# Change to project root
cd "$PROJECT_ROOT"

# Function to check if deployment confirmation is needed
confirm_deployment() {
    if [[ "$FORCE_DEPLOY" == true ]]; then
        return 0
    fi
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        print_warning "This will deploy to PRODUCTION environment!"
        read -p "Are you sure you want to continue? (yes/no): " confirm
        case $confirm in
            [Yy][Ee][Ss])
                return 0
                ;;
            *)
                print_info "Deployment cancelled"
                exit 0
                ;;
        esac
    fi
}

# Function to build production image
build_production_image() {
    print_info "Building production Docker image..."
    
    # Use poetry dockerfile for production
    DOCKERFILE="docker/Dockerfile.poetry"
    
    if [[ ! -f "$DOCKERFILE" ]]; then
        print_error "Production Dockerfile not found: $DOCKERFILE"
        exit 1
    fi
    
    BUILD_CMD="docker build -f $DOCKERFILE -t $IMAGE_NAME:$IMAGE_TAG"
    
    # Add build args for production
    BUILD_CMD="$BUILD_CMD --build-arg ENVIRONMENT=$ENVIRONMENT"
    BUILD_CMD="$BUILD_CMD ."
    
    print_info "Running: $BUILD_CMD"
    
    if eval "$BUILD_CMD"; then
        print_success "Production image built successfully: $IMAGE_NAME:$IMAGE_TAG"
        
        # Tag as latest for the environment
        docker tag "$IMAGE_NAME:$IMAGE_TAG" "$IMAGE_NAME:latest"
        print_info "Tagged as $IMAGE_NAME:latest"
        
        # Show image size
        SIZE=$(docker images "$IMAGE_NAME:$IMAGE_TAG" --format "{{.Size}}")
        print_info "Image size: $SIZE"
    else
        print_error "Failed to build production image"
        exit 1
    fi
}

# Function to deploy services
deploy_services() {
    confirm_deployment
    
    print_info "Deploying services to $ENVIRONMENT..."
    
    # Determine compose file
    if [[ "$ENVIRONMENT" == "production" ]]; then
        COMPOSE_FILE="docker/compose/docker-compose.yml"
    else
        COMPOSE_FILE="docker/compose/docker-compose.poetry.yml"
    fi
    
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        print_error "Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Set environment variables for compose
    export IMAGE_NAME="$IMAGE_NAME"
    export IMAGE_TAG="$IMAGE_TAG"
    export ENVIRONMENT="$ENVIRONMENT"
    
    # Deploy with docker-compose
    DEPLOY_CMD="docker-compose -f $COMPOSE_FILE up -d --build"
    
    print_info "Running: $DEPLOY_CMD"
    
    if eval "$DEPLOY_CMD"; then
        print_success "Services deployed successfully"
        
        # Wait a moment for services to start
        sleep 5
        
        # Check service health
        print_info "Checking service health..."
        if curl -s -f "http://localhost:8000/health" >/dev/null; then
            print_success "Service is healthy and responding"
            print_info "API available at: http://localhost:8000"
            print_info "Documentation: http://localhost:8000/docs"
        else
            print_warning "Service may not be fully ready yet"
            print_info "Check logs with: $0 logs --env $ENVIRONMENT"
        fi
    else
        print_error "Deployment failed"
        exit 1
    fi
}

# Execute command
case $COMMAND in
    build)
        build_production_image
        ;;
        
    deploy)
        build_production_image
        deploy_services
        ;;
        
    restart)
        print_info "Restarting $ENVIRONMENT services..."
        
        # Determine compose file
        if [[ "$ENVIRONMENT" == "production" ]]; then
            COMPOSE_FILE="docker/compose/docker-compose.yml"
        else
            COMPOSE_FILE="docker/compose/docker-compose.poetry.yml"
        fi
        
        if docker-compose -f "$COMPOSE_FILE" restart; then
            print_success "Services restarted successfully"
        else
            print_error "Failed to restart services"
            exit 1
        fi
        ;;
        
    stop)
        print_info "Stopping $ENVIRONMENT services..."
        
        # Determine compose file
        if [[ "$ENVIRONMENT" == "production" ]]; then
            COMPOSE_FILE="docker/compose/docker-compose.yml"
        else
            COMPOSE_FILE="docker/compose/docker-compose.poetry.yml"
        fi
        
        if docker-compose -f "$COMPOSE_FILE" down; then
            print_success "Services stopped successfully"
        else
            print_error "Failed to stop services"
            exit 1
        fi
        ;;
        
    status)
        print_info "Checking $ENVIRONMENT deployment status..."
        
        # Check if containers are running
        if docker ps --format '{{.Names}}' | grep -q intelligent-agent; then
            print_success "Services are running"
            
            print_info "Container status:"
            docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep intelligent-agent
            
            # Check API health
            if curl -s -f "http://localhost:8000/health" >/dev/null; then
                print_success "API is healthy"
            else
                print_warning "API is not responding"
            fi
        else
            print_warning "No services are running"
        fi
        ;;
        
    logs)
        print_info "Showing $ENVIRONMENT logs..."
        
        # Determine compose file
        if [[ "$ENVIRONMENT" == "production" ]]; then
            COMPOSE_FILE="docker/compose/docker-compose.yml"
        else
            COMPOSE_FILE="docker/compose/docker-compose.poetry.yml"
        fi
        
        docker-compose -f "$COMPOSE_FILE" logs -f
        ;;
esac
