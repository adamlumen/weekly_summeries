#!/usr/bin/env python3
"""
Debug script to test should_use method with debugging
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.tools.database.snowflake_tool import SnowflakeTool

def debug_should_use(tool, intent, context):
    """Debug version of should_use method."""
    print(f"🔍 Debugging should_use for: {intent}")
    
    if not tool.enabled:
        print("❌ Tool not enabled")
        return 0.0
    
    # Basic implementation using keywords
    intent_lower = intent.lower()
    capabilities = tool.capabilities
    
    print(f"Intent lower: '{intent_lower}'")
    
    # Check use cases
    use_case_matches = 0
    print("\n🎯 Checking use cases:")
    for use_case in capabilities.use_cases:
        match = use_case.lower() in intent_lower
        if match:
            use_case_matches += 1
        print(f"  '{use_case}' -> {match}")
    
    # Check confidence keywords
    keyword_matches = 0
    print("\n🔑 Checking keywords:")
    for keyword in capabilities.confidence_keywords:
        match = keyword.lower() in intent_lower
        if match:
            keyword_matches += 1
        print(f"  '{keyword}' -> {match}")
    
    # Check if prerequisites are met
    prereq_penalty = 0
    print("\n📋 Checking prerequisites:")
    for prereq in capabilities.prerequisites:
        if prereq not in context:
            prereq_penalty += 0.2
            print(f"  '{prereq}' -> MISSING (penalty +0.2)")
        else:
            print(f"  '{prereq}' -> OK")
    
    # Calculate confidence score
    total_keywords = len(capabilities.use_cases) + len(capabilities.confidence_keywords)
    if total_keywords == 0:
        base_score = 0.1
    else:
        base_score = (use_case_matches + keyword_matches) / total_keywords
    
    # Apply penalty for missing prerequisites
    final_score = max(0, base_score - prereq_penalty)
    
    print(f"\n📊 Calculation:")
    print(f"  Use case matches: {use_case_matches}")
    print(f"  Keyword matches: {keyword_matches}")
    print(f"  Total possible: {total_keywords}")
    print(f"  Base score: {base_score:.3f}")
    print(f"  Prereq penalty: {prereq_penalty:.3f}")
    print(f"  Final score: {final_score:.3f}")
    
    return min(1.0, final_score)

def main():
    """Test should_use method with debugging."""
    print("🐛 Debugging should_use method")
    print("=" * 50)
    
    # Create Snowflake tool instance
    tool = SnowflakeTool()
    
    # Test confidence calculation
    intent = "What tables are available in Snowflake?"
    context = {}
    
    confidence = debug_should_use(tool, intent, context)
    print(f"\n✅ Final confidence: {confidence}")

if __name__ == "__main__":
    main()
