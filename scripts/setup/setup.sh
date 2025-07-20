#!/bin/bash
# Quick setup script for the intelligent agent

echo "🚀 Setting up Intelligent Agent..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check for Poetry or use pip
if command -v poetry &> /dev/null; then
    echo "🎵 Poetry found! Using Poetry for dependency management..."
    USE_POETRY=true
else
    echo "📦 Poetry not found, using pip with virtual environment..."
    USE_POETRY=false
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies
echo "📥 Installing dependencies..."

if [ "$USE_POETRY" = true ]; then
    echo "Choose Poetry installation option:"
    echo "1. Basic (core features only)"
    echo "2. Google Drive (+ document search)"
    echo "3. Data Analysis (+ pandas, numpy, scikit-learn)"
    echo "4. Database (+ MySQL support)"
    echo "5. Collaboration (+ Notion, Slack)"
    echo "6. Full (all features)"
    read -p "Enter choice (1-6) [default: 1]: " choice
    choice=${choice:-1}
    
    case $choice in
        1)
            echo "Installing basic dependencies..."
            poetry install
            ;;
        2)
            echo "Installing with Google Drive support..."
            poetry install --extras google-drive
            ;;
        3)
            echo "Installing with data analysis support..."
            poetry install --extras data-analysis
            ;;
        4)
            echo "Installing with database support..."
            poetry install --extras database
            ;;
        5)
            echo "Installing with collaboration tools..."
            poetry install --extras collaboration
            ;;
        6)
            echo "Installing all features..."
            poetry install --extras full
            ;;
        *)
            echo "Invalid choice, installing basic dependencies..."
            poetry install
            ;;
    esac
else
    echo "Choose pip installation option:"
    echo "1. Minimal (faster, basic features)"
    echo "2. Full (all features including Google Drive, data analysis)"
    read -p "Enter choice (1 or 2) [default: 1]: " choice
    choice=${choice:-1}

    if [ "$choice" = "1" ]; then
        echo "Installing minimal dependencies..."
        pip install -r requirements-minimal.txt
    else
        echo "Installing full dependencies..."
        pip install -r requirements.txt
    fi
fi

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating environment file..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys!"
    echo "   Required: OPENAI_API_KEY"
    echo "   Optional: DATABASE_URL, GOOGLE_DRIVE_CREDENTIALS_FILE"
fi

# Create data directory
mkdir -p data

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
if [ "$USE_POETRY" = true ]; then
    echo "2. Run: poetry run uvicorn src.api.main:app --reload"
    echo "   Or: poetry shell && uvicorn src.api.main:app --reload"
    echo "3. Visit: http://127.0.0.1:8000/docs"
    echo ""
    echo "Poetry commands:"
    echo "- poetry run python cli.py 'Create a summary for user123'"
    echo "- poetry shell  # Activate poetry environment"
    echo "- poetry add <package>  # Add new dependency"
else
    echo "2. Run: uvicorn src.api.main:app --reload"
    echo "3. Visit: http://127.0.0.1:8000/docs"
    echo ""
    echo "Or test with CLI: python cli.py 'Create a summary for user123'"
fi
