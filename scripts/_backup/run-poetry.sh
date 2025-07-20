#!/bin/bash
# Poetry run script for the intelligent agent

echo "🚀 Starting Intelligent Agent with Poetry..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed."
    echo "Install Poetry: curl -sSL https://install.python-poetry.org | python3 -"
    echo "Or use the regular run script: ./run.sh"
    exit 1
fi

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo "❌ pyproject.toml not found. Run ./setup.sh first."
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your OpenAI API key!"
    echo "   Set OPENAI_API_KEY=your_key_here"
    echo ""
    read -p "Press Enter after you've added your API key to continue..."
fi

# Create data directory if it doesn't exist
mkdir -p data

# Check if OpenAI key is set
if grep -q "your_openai_api_key_here" .env; then
    echo "❌ Please set your OpenAI API key in .env file"
    echo "   Edit OPENAI_API_KEY=your_actual_key_here"
    exit 1
fi

# Install dependencies if not already installed
if [ ! -f "poetry.lock" ]; then
    echo "📦 Installing dependencies..."
    poetry install
fi

echo "🌐 Starting FastAPI server with Poetry..."
echo "📖 API docs will be available at: http://127.0.0.1:8000/docs"
echo "🔗 Health check at: http://127.0.0.1:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server using Poetry
poetry run uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
