#!/usr/bin/env python3
"""
Debug script to test should_use method directly
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.tools.database.snowflake_tool import SnowflakeTool

def main():
    """Test should_use method directly."""
    print("🎯 Testing should_use method directly")
    print("=" * 40)
    
    # Create Snowflake tool instance
    tool = SnowflakeTool()
    
    print(f"Tool enabled: {tool.enabled}")
    print(f"Tool capabilities name: {tool.capabilities.name}")
    
    # Test confidence calculation
    intent = "What tables are available in Snowflake?"
    context = {}
    
    confidence = tool.should_use(intent, context)
    print(f"Confidence for '{intent}': {confidence}")
    
    # Print capabilities for reference
    print("\nTool capabilities:")
    print(f"  Use cases: {tool.capabilities.use_cases}")
    print(f"  Keywords: {tool.capabilities.confidence_keywords}")
    print(f"  Prerequisites: {tool.capabilities.prerequisites}")

if __name__ == "__main__":
    main()
