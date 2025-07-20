import json
from datetime import datetime
from typing import Any

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def json_serializer(obj: Any) -> Any:
    """Custom JSON serializer to handle pandas objects and datetime objects."""
    if HAS_PANDAS and isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif HAS_PANDAS and isinstance(obj, pd.DataFrame):
        # Convert DataFrame to dict with serializable types
        return obj.to_dict('records')
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, 'isoformat'):  # For other datetime-like objects
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def serialize_tool_results(tool_results: list) -> list:
    """Serialize tool results for JSON output."""
    serialized = []
    for result in tool_results:
        # Convert to dict and handle non-serializable objects
        result_dict = result.__dict__.copy()
        
        # Handle the data field specially if it contains DataFrames or Timestamp objects
        if result_dict.get('data'):
            try:
                # Try to serialize the data
                json.dumps(result_dict['data'], default=json_serializer)
            except (TypeError, ValueError):
                # If serialization fails, convert problematic objects
                result_dict['data'] = json.loads(json.dumps(result_dict['data'], default=json_serializer))
        
        serialized.append(result_dict)
    
    return serialized
