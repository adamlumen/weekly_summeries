#!/bin/bash
# Main script launcher for intelligent agent project

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
    echo "🚀 Intelligent Agent - Script Launcher"
    echo ""
    echo "Usage: $0 [CATEGORY] [COMMAND] [OPTIONS]"
    echo ""
    echo "Categories:"
    echo "  dev          Development commands"
    echo "  docker       Docker management commands"
    echo "  deploy       Deployment commands"
    echo ""
    echo "Development Commands (dev):"
    echo "  server       Start development server"
    echo "  test         Run tests"
    echo "  lint         Run linting"
    echo "  format       Format code"
    echo ""
    echo "Docker Commands (docker):"
    echo "  build        Build Docker images"
    echo "  run          Run Docker containers"
    echo "  compose      Manage docker-compose services"
    echo ""
    echo "Deployment Commands (deploy):"
    echo "  build        Build production images"
    echo "  deploy       Deploy to environment"
    echo "  restart      Restart services"
    echo "  stop         Stop services"
    echo "  status       Check deployment status"
    echo "  logs         Show deployment logs"
    echo ""
    echo "Examples:"
    echo "  $0 dev server                    # Start development server"
    echo "  $0 dev server --simple           # Start simple development server"
    echo "  $0 docker build --type basic     # Build basic Docker image"
    echo "  $0 docker run --detach           # Run Docker container in background"
    echo "  $0 docker compose up --detach    # Start services with docker-compose"
    echo "  $0 deploy build --env staging    # Build staging deployment"
    echo "  $0 deploy deploy --env production # Deploy to production"
    echo ""
    echo "For detailed help on specific commands:"
    echo "  $0 dev server --help"
    echo "  $0 docker build --help"
    echo "  $0 deploy deploy --help"
}

# Check if any arguments provided
if [[ $# -eq 0 ]]; then
    usage
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse first argument (category)
CATEGORY="$1"
shift

case $CATEGORY in
    dev)
        if [[ $# -eq 0 ]]; then
            print_error "Development command required"
            echo ""
            echo "Available commands: server, test, lint, format"
            exit 1
        fi
        
        DEV_COMMAND="$1"
        shift
        
        case $DEV_COMMAND in
            server)
                exec "$SCRIPT_DIR/dev/server.sh" "$@"
                ;;
            test)
                # Add test command later
                print_info "Running tests..."
                cd "$SCRIPT_DIR/.."
                if command -v poetry >/dev/null 2>&1; then
                    poetry run pytest "$@"
                else
                    python -m pytest "$@"
                fi
                ;;
            lint)
                # Add lint command later
                print_info "Running linting..."
                cd "$SCRIPT_DIR/.."
                if command -v poetry >/dev/null 2>&1; then
                    poetry run flake8 src tests
                else
                    flake8 src tests
                fi
                ;;
            format)
                # Add format command later
                print_info "Formatting code..."
                cd "$SCRIPT_DIR/.."
                if command -v poetry >/dev/null 2>&1; then
                    poetry run black src tests
                    poetry run isort src tests
                else
                    black src tests
                    isort src tests
                fi
                ;;
            *)
                print_error "Unknown development command: $DEV_COMMAND"
                echo "Available commands: server, test, lint, format"
                exit 1
                ;;
        esac
        ;;
        
    docker)
        if [[ $# -eq 0 ]]; then
            print_error "Docker command required"
            echo ""
            echo "Available commands: build, run, compose"
            exit 1
        fi
        
        DOCKER_COMMAND="$1"
        shift
        
        case $DOCKER_COMMAND in
            build)
                exec "$SCRIPT_DIR/docker/build.sh" "$@"
                ;;
            run)
                exec "$SCRIPT_DIR/docker/run.sh" "$@"
                ;;
            compose)
                exec "$SCRIPT_DIR/docker/compose.sh" "$@"
                ;;
            *)
                print_error "Unknown docker command: $DOCKER_COMMAND"
                echo "Available commands: build, run, compose"
                exit 1
                ;;
        esac
        ;;
        
    deploy)
        if [[ $# -eq 0 ]]; then
            print_error "Deployment command required"
            echo ""
            echo "Available commands: build, deploy, restart, stop, status, logs"
            exit 1
        fi
        
        exec "$SCRIPT_DIR/deployment/deploy.sh" "$@"
        ;;
        
    --help|-h|help)
        usage
        exit 0
        ;;
        
    *)
        print_error "Unknown category: $CATEGORY"
        echo ""
        usage
        exit 1
        ;;
esac
