#!/usr/bin/env python3
"""
Debug script to test tool selection
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.tools.registry import tool_registry

async def main():
    """Test tool selection."""
    print("🔧 Testing Tool Selection")
    print("=" * 40)
    
    # Initialize tool registry
    await tool_registry.initialize()
    
    print(f"Total tools available: {len(tool_registry.get_all_tools())}")
    
    # List all tools
    for name, tool in tool_registry.get_all_tools().items():
        print(f"  - {name}: {tool.capabilities.description}")
    
    print("\n🎯 Testing tool selection for Snowflake query...")
    
    # Test tool selection
    intent = "What tables are available in Snowflake?"
    context = {}
    
    suitable_tools = tool_registry.get_tools_for_intent(intent, context, min_confidence=0.0)
    
    print(f"\nSuitable tools found: {len(suitable_tools)}")
    for tool, confidence in suitable_tools:
        print(f"  - {tool.capabilities.name}: confidence={confidence:.3f}")
        print(f"    Keywords: {tool.capabilities.confidence_keywords}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
