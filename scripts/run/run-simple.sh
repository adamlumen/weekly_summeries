#!/bin/bash
# Simple run script that works without complex dependencies

echo "🚀 Starting Simple Intelligent Agent..."

# Check if we're in the right directory
if [ ! -f "src/api/main_simple.py" ]; then
    echo "❌ Please run this from the project root directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
elif [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ Virtual environment already active: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment found. Using system Python..."
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating basic one..."
    echo "OPENAI_API_KEY=your_key_here" > .env
    echo "DEBUG=true" >> .env
    echo "📝 Edit .env file to add your OpenAI API key when ready"
fi

echo "🌐 Starting FastAPI server (simple mode)..."
echo "📖 API docs: http://127.0.0.1:8000/docs"
echo "🔗 Health check: http://127.0.0.1:8000/health"
echo "🤖 Agent status: http://127.0.0.1:8000/agent/status"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Check for Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Python not found. Please install Python 3.11 or higher."
    exit 1
fi

echo "Using Python: $PYTHON_CMD"

# Run the simple version
$PYTHON_CMD -m uvicorn src.api.main_simple:app --reload --host 127.0.0.1 --port 8000
