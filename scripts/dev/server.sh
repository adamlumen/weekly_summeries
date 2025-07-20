#!/bin/bash
# Development server script for intelligent agent

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
    echo "  -m, --mode MODE     Development mode: poetry, venv, simple (default: auto-detect)"
    echo "  -p, --port PORT     Port to run on (default: 8000)"
    echo "  -h, --host HOST     Host to bind to (default: 127.0.0.1)"
    echo "  -r, --reload        Enable auto-reload (default: true)"
    echo "  -w, --workers NUM   Number of workers (default: 1)"
    echo "  --simple            Use simple main.py (basic functionality)"
    echo "  --full              Use full main.py (all features)"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                              # Auto-detect and run"
    echo "  $0 --mode poetry --port 8080    # Run with poetry on port 8080"
    echo "  $0 --simple --reload            # Run simple version with reload"
}

# Default values
DEV_MODE=""
PORT="8000"
HOST="127.0.0.1"
RELOAD=true
WORKERS=1
USE_SIMPLE=false
USE_FULL=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mode)
            DEV_MODE="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -r|--reload)
            RELOAD=true
            shift
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        --simple)
            USE_SIMPLE=true
            shift
            ;;
        --full)
            USE_FULL=true
            shift
            ;;
        --help)
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

# Change to project root
cd "$PROJECT_ROOT"

# Auto-detect development mode if not specified
if [[ -z "$DEV_MODE" ]]; then
    if [[ -f "pyproject.toml" ]] && command -v poetry >/dev/null 2>&1; then
        if poetry env info >/dev/null 2>&1; then
            DEV_MODE="poetry"
        else
            print_warning "Poetry installed but no environment found. Using venv/pip mode."
            DEV_MODE="venv"
        fi
    elif [[ -f "venv/bin/activate" ]] || [[ -n "$VIRTUAL_ENV" ]]; then
        DEV_MODE="venv"
    else
        DEV_MODE="simple"
    fi
fi

# Validate mode
if [[ ! "$DEV_MODE" =~ ^(poetry|venv|simple)$ ]]; then
    print_error "Invalid mode: $DEV_MODE. Must be one of: poetry, venv, simple"
    exit 1
fi

print_info "Starting development server..."
print_info "Mode: $DEV_MODE"
print_info "Host: $HOST"
print_info "Port: $PORT"
print_info "Auto-reload: $RELOAD"

# Determine app module
if [[ "$USE_SIMPLE" == true ]]; then
    APP_MODULE="src.api.main_simple:app"
    print_info "Using simple app (basic functionality)"
elif [[ "$USE_FULL" == true ]]; then
    APP_MODULE="src.api.main:app"
    print_info "Using full app (all features)"
else
    # Auto-detect based on available files
    if [[ -f "src/api/main_simple.py" ]]; then
        APP_MODULE="src.api.main_simple:app"
        print_info "Using simple app (auto-detected)"
    elif [[ -f "src/api/main.py" ]]; then
        APP_MODULE="src.api.main:app"
        print_info "Using full app (auto-detected)"
    else
        print_error "No main app file found. Expected src/api/main.py or src/api/main_simple.py"
        exit 1
    fi
fi

# Build uvicorn command
UVICORN_CMD="uvicorn $APP_MODULE --host $HOST --port $PORT"

if [[ "$RELOAD" == true ]]; then
    UVICORN_CMD="$UVICORN_CMD --reload"
fi

if [[ "$WORKERS" -gt 1 ]]; then
    UVICORN_CMD="$UVICORN_CMD --workers $WORKERS"
fi

# Execute based on mode
case $DEV_MODE in
    poetry)
        print_info "Checking Poetry environment..."
        if ! poetry env info >/dev/null 2>&1; then
            print_error "Poetry environment not found. Run 'poetry install' first."
            exit 1
        fi
        
        FULL_CMD="poetry run $UVICORN_CMD"
        print_info "Running: $FULL_CMD"
        
        if eval "$FULL_CMD"; then
            print_success "Server started successfully"
        else
            print_error "Failed to start server"
            exit 1
        fi
        ;;
        
    venv)
        # Check if virtual environment is activated
        if [[ -z "$VIRTUAL_ENV" ]]; then
            if [[ -f "venv/bin/activate" ]]; then
                print_info "Activating virtual environment..."
                source venv/bin/activate
            else
                print_error "Virtual environment not found and none is activated"
                print_info "Create one with: python -m venv venv && source venv/bin/activate"
                exit 1
            fi
        fi
        
        print_info "Using virtual environment: $VIRTUAL_ENV"
        print_info "Running: $UVICORN_CMD"
        
        if eval "$UVICORN_CMD"; then
            print_success "Server started successfully"
        else
            print_error "Failed to start server"
            exit 1
        fi
        ;;
        
    simple)
        print_warning "Running in simple mode (no virtual environment)"
        print_info "Running: $UVICORN_CMD"
        
        if eval "$UVICORN_CMD"; then
            print_success "Server started successfully"
        else
            print_error "Failed to start server"
            exit 1
        fi
        ;;
esac

print_info "Server will be available at: http://$HOST:$PORT"
print_info "API documentation: http://$HOST:$PORT/docs"
print_info "Press Ctrl+C to stop the server"
