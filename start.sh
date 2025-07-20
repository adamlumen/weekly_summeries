#!/bin/bash
# Main launcher script for Intelligent Agent
# This script provides a simple interface to all available options

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🤖 Intelligent Agent Launcher"
echo "=============================="
echo ""

show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup         Set up the project (install dependencies)"
    echo "  run           Run the application"
    echo "  docker        Run with Docker"
    echo "  cli           Use command-line interface"
    echo "  help          Show this help"
    echo ""
    echo "Run Options:"
    echo "  run simple    Quick start with minimal dependencies"
    echo "  run poetry    Run with Poetry (full features)"
    echo "  run dev       Development mode with auto-reload"
    echo ""
    echo "Docker Options:"
    echo "  docker simple     Basic Docker setup"
    echo "  docker compose    Full Docker Compose setup"
    echo "  docker build      Build Docker images"
    echo ""
    echo "Examples:"
    echo "  ./start.sh setup            # Initial setup"
    echo "  ./start.sh run simple       # Quick start"
    echo "  ./start.sh docker simple    # Run in Docker"
    echo "  ./start.sh cli \"Create summary for user123\""
    echo ""
}

case "${1:-help}" in
    setup)
        echo "🛠️  Running setup..."
        ./scripts/setup/setup.sh "${@:2}"
        ;;
    
    run)
        case "${2:-simple}" in
            simple)
                echo "🚀 Starting simple mode..."
                ./scripts/run/run-simple.sh "${@:3}"
                ;;
            poetry)
                echo "🎵 Starting with Poetry..."
                ./scripts/run/run-poetry.sh "${@:3}"
                ;;
            dev|smart)
                echo "🔧 Starting development mode..."
                ./scripts/run/run-smart.sh "${@:3}"
                ;;
            *)
                echo "❌ Unknown run option: $2"
                echo "Available: simple, poetry, dev"
                exit 1
                ;;
        esac
        ;;
    
    docker)
        case "${2:-simple}" in
            simple)
                echo "🐳 Starting with Docker (simple)..."
                cd docker && docker-compose -f compose/docker-compose.simple.yml up "${@:3}"
                ;;
            compose)
                echo "🐳 Starting with Docker Compose (full)..."
                cd docker && docker-compose -f compose/docker-compose.poetry.yml up "${@:3}"
                ;;
            build)
                echo "🔨 Building Docker images..."
                case "${3:-basic}" in
                    basic)
                        docker build -f docker/Dockerfile.basic -t intelligent-agent-basic .
                        ;;
                    poetry)
                        docker build -f docker/Dockerfile.poetry -t intelligent-agent-poetry .
                        ;;
                    all)
                        docker build -f docker/Dockerfile.basic -t intelligent-agent-basic .
                        docker build -f docker/Dockerfile.poetry -t intelligent-agent-poetry .
                        ;;
                    *)
                        echo "❌ Unknown build option: $3"
                        echo "Available: basic, poetry, all"
                        exit 1
                        ;;
                esac
                ;;
            *)
                echo "❌ Unknown docker option: $2"
                echo "Available: simple, compose, build"
                exit 1
                ;;
        esac
        ;;
    
    cli)
        if [ -z "$2" ]; then
            echo "❌ Please provide a request for the CLI"
            echo "Example: ./start.sh cli \"Create summary for user123\""
            exit 1
        fi
        echo "💬 Running CLI..."
        ./scripts/cli-poetry.sh "${@:2}"
        ;;
    
    help|--help|-h)
        show_help
        ;;
    
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
