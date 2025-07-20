#!/usr/bin/env python3
"""
Debug script to test confidence calculation manually
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_confidence_manually():
    """Test confidence calculation manually."""
    print("🧮 Testing Confidence Calculation")
    print("=" * 40)
    
    intent = "What tables are available in Snowflake?"
    intent_lower = intent.lower()
    
    print(f"Intent: {intent}")
    print(f"Intent lower: {intent_lower}")
    
    # Snowflake tool keywords
    use_cases = [
        "Query user activity data",
        "Retrieve historical analytics", 
        "Get aggregated metrics",
        "Extract data for recommendations",
        "Analyze user behavior patterns",
        "Generate reports from warehouse data",
        "List available tables and schemas",
        "Show database structure",
        "Describe table information"
    ]
    
    confidence_keywords = [
        "data", "query", "sql", "database", "analytics", "metrics",
        "snowflake", "warehouse", "reports", "activity", "users", 
        "tables", "table", "schema", "schemas", "columns", "available",
        "list", "show", "describe", "information", "structure"
    ]
    
    print(f"\nUse cases ({len(use_cases)}):")
    use_case_matches = 0
    for use_case in use_cases:
        match = use_case.lower() in intent_lower
        if match:
            use_case_matches += 1
        print(f"  '{use_case}' -> {match}")
    
    print(f"\nConfidence keywords ({len(confidence_keywords)}):")
    keyword_matches = 0
    for keyword in confidence_keywords:
        match = keyword.lower() in intent_lower
        if match:
            keyword_matches += 1
        print(f"  '{keyword}' -> {match}")
    
    total_keywords = len(use_cases) + len(confidence_keywords)
    base_score = (use_case_matches + keyword_matches) / total_keywords
    
    print(f"\nCalculation:")
    print(f"  Use case matches: {use_case_matches}")
    print(f"  Keyword matches: {keyword_matches}")  
    print(f"  Total possible: {total_keywords}")
    print(f"  Base score: {base_score:.3f}")

if __name__ == "__main__":
    test_confidence_manually()
