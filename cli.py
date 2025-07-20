#!/usr/bin/env python3
"""
Command-line interface for the intelligent agent.
Useful for testing and development.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agent.intelligent_agent import IntelligentAgent
from src.tools.registry import tool_registry
from src.core.config import get_openai_config


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Intelligent Agent CLI")
    parser.add_argument("request", help="User request to process")
    parser.add_argument("--user-id", help="User ID", default="cli_user")
    parser.add_argument("--session-id", help="Session ID", default="cli_session")
    parser.add_argument("--context", help="Additional context as JSON", default="{}")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        # Parse additional context
        additional_context = json.loads(args.context)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in context argument")
        sys.exit(1)
    
    # Initialize agent
    openai_config = get_openai_config()
    if not openai_config.get('api_key'):
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    agent = IntelligentAgent(api_key=openai_config['api_key'])
    
    # Prepare context
    if args.verbose:
        print(f"Processing request: {args.request}")
        print(f"User ID: {args.user_id}")
        print(f"Session ID: {args.session_id}")
        print(f"Additional context: {additional_context}")
        print("-" * 50)
    
    try:
        # Process request
        result = await agent.process_request(
            user_request=args.request,
            user_id=args.user_id,
            additional_context=additional_context
        )
        
        # Output result
        if args.verbose:
            print("Full result:")
            print(json.dumps(result, indent=2))
        else:
            print(result.get("response", "No response generated"))
            
    except Exception as e:
        print(f"Error processing request: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
