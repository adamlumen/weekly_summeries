# Makefile for Poetry-based development

.PHONY: help install install-dev install-full run test lint format clean

help: ## Show this help message
	@echo "🚀 Intelligent Agent - Poetry Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install basic dependencies
	poetry install

install-basic: ## Install minimal dependencies (no MCP conflicts)
	pip install -r requirements-basic.txt

install-dev: ## Install with development dependencies
	poetry install --with dev

install-full: ## Install all features (Google Drive, data analysis, etc.)
	poetry install --extras full --with dev

install-mcp: ## Install with MCP support (may have conflicts)
	poetry install --extras mcp

install-google: ## Install with Google Drive support
	poetry install --extras google-drive

install-data: ## Install with data analysis support
	poetry install --extras data-analysis

install-snowflake: ## Install with Snowflake support
	poetry install --extras snowflake

install-database: ## Install with database support
	poetry install --extras database

run: ## Start the API server
	@./scripts/dev/server.sh

run-simple: ## Start simple API server
	@./scripts/dev/server.sh --simple

run-poetry: ## Start with Poetry
	@./scripts/dev/server.sh --mode poetry

run-venv: ## Start with virtual environment
	@./scripts/dev/server.sh --mode venv

cli: ## Run the CLI tool (usage: make cli ARGS="your request here")
	poetry run python cli.py $(ARGS)

test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage
	poetry run pytest --cov=src --cov-report=html

lint: ## Run linting
	poetry run flake8 src tests
	poetry run mypy src

format: ## Format code
	poetry run black src tests
	poetry run isort src tests

format-check: ## Check code formatting
	poetry run black --check src tests
	poetry run isort --check-only src tests

clean: ## Clean up build artifacts
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	poetry build

shell: ## Activate Poetry shell
	poetry shell

update: ## Update dependencies
	poetry update

add: ## Add a new dependency (usage: make add PACKAGE=package_name)
	poetry add $(PACKAGE)

add-dev: ## Add a new development dependency
	poetry add --group dev $(PACKAGE)

show: ## Show project information
	poetry show --tree

env: ## Show environment information
	poetry env info

# Docker commands (organized scripts)
docker-build: ## Build Docker image (type: basic, poetry, main)
	@./scripts/docker/build.sh --type basic

docker-build-poetry: ## Build Poetry Docker image
	@./scripts/docker/build.sh --type poetry

docker-build-main: ## Build main Docker image
	@./scripts/docker/build.sh --type main

docker-run: ## Run Docker container
	@./scripts/docker/run.sh

docker-run-detached: ## Run Docker container in background
	@./scripts/docker/run.sh --detach

docker-compose-up: ## Start services with docker-compose
	@./scripts/docker/compose.sh up --file simple

docker-compose-poetry: ## Start Poetry docker-compose setup
	@./scripts/docker/compose.sh up --file poetry

docker-compose-full: ## Start full docker-compose setup
	@./scripts/docker/compose.sh up --file full

docker-compose-down: ## Stop docker-compose services
	@./scripts/docker/compose.sh down --file simple

docker-clean: ## Clean Docker images and containers
	@./scripts/docker/compose.sh down --file simple --volumes
	@./scripts/docker/compose.sh down --file poetry --volumes
	@./scripts/docker/compose.sh down --file full --volumes
	docker system prune -f

# Deployment commands
deploy-staging: ## Deploy to staging environment
	@./scripts/deployment/deploy.sh build --env staging
	@./scripts/deployment/deploy.sh deploy --env staging

deploy-production: ## Deploy to production environment
	@./scripts/deployment/deploy.sh deploy --env production --force

deploy-status: ## Check deployment status
	@./scripts/deployment/deploy.sh status --env staging

deploy-logs: ## Show deployment logs
	@./scripts/deployment/deploy.sh logs --env staging

# Quick start commands
quick-start: ## Quick start with Docker Compose
	@echo "🚀 Quick starting intelligent agent..."
	@./scripts/docker/compose.sh up --file simple --detach
	@echo "✅ Agent started! Visit http://localhost:8000/docs"

quick-stop: ## Quick stop all services
	@echo "🛑 Stopping all services..."
	@./scripts/docker/compose.sh down --file simple
	@./scripts/docker/compose.sh down --file poetry
	@./scripts/docker/compose.sh down --file full

# Example usage targets
example-basic: ## Run basic example
	poetry run python cli.py "Create a weekly summary for user123"

example-verbose: ## Run verbose example
	poetry run python cli.py "Analyze user activity for the past week" --user-id user123 --verbose

example-api: ## Test API with curl
	@echo "Testing API..."
	curl -X POST "http://127.0.0.1:8000/agent/process" \
		-H "Content-Type: application/json" \
		-d '{"user_request": "Create a summary for user123", "user_id": "user123"}'

# Unified script launcher
scripts: ## Show available script commands
	@./scripts/agent.sh --help
