#!/bin/bash
# Poetry CLI wrapper for the intelligent agent

echo "🤖 Intelligent Agent CLI (Poetry)"
echo ""

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed."
    echo "Install Poetry: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check if request is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 \"Your request here\" [--user-id USER] [--verbose]"
    echo ""
    echo "Examples:"
    echo "  $0 \"Create a weekly summary for user123\""
    echo "  $0 \"Find documentation about API formats\" --user-id user456 --verbose"
    echo ""
    exit 1
fi

# Run the CLI with Poetry
poetry run python cli.py "$@"
