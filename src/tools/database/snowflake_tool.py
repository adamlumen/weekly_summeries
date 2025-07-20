"""
Snowflake Database Tool for intelligent agent.
Provides data querying capabilities from Snowflake data warehouse.
"""

import logging
from typing import Dict, Any, Optional, List
import pandas as pd
from pathlib import Path

from ..base_tool import BaseTool, ToolResult, ToolResultStatus, ToolCapability
from .utilities import get_snowflake_settings, read_from_snowflake, test_snowflake_connection
from .connection_manager import snowflake_manager

logger = logging.getLogger(__name__)

class SnowflakeTool(BaseTool):
    """Tool for querying Snowflake data warehouse."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
    
    @property
    def capabilities(self) -> ToolCapability:
        """Describe what this tool can do."""
        return ToolCapability(
            name="snowflake_query",
            description="Execute SQL queries against Snowflake data warehouse to retrieve and analyze data",
            parameters={
                "query": {
                    "type": "string",
                    "description": "SQL query to execute or path to SQL file",
                    "required": True
                },
                "parameters": {
                    "type": "object",
                    "description": "Optional parameters for parameterized queries",
                    "required": False
                },
                "limit": {
                    "type": "integer", 
                    "description": "Maximum number of rows to return (default: 1000)",
                    "required": False,
                    "default": 1000
                }
            },
            use_cases=[
                "Query user activity data",
                "Retrieve historical analytics", 
                "Get aggregated metrics",
                "Extract data for recommendations",
                "Analyze user behavior patterns",
                "Generate reports from warehouse data",
                "List available tables and schemas",
                "Show database structure",
                "Describe table information"
            ],
            data_sources=["Snowflake Data Warehouse", "LUMEN_PROD database"],
            prerequisites=[],
            confidence_keywords=[
                "data", "query", "sql", "database", "analytics", "metrics",
                "snowflake", "warehouse", "reports", "activity", "users", 
                "tables", "table", "schema", "schemas", "columns", "available",
                "list", "show", "describe", "information", "structure"
            ]
        )
    
    async def execute(self, query: str, parameters: Optional[Dict[str, Any]] = None, 
                     limit: int = 1000, **kwargs) -> ToolResult:
        """
        Execute a SQL query against Snowflake.
        
        Args:
            query: SQL query string or path to SQL file
            parameters: Optional parameters for parameterized queries
            limit: Maximum number of rows to return
            
        Returns:
            ToolResult with query results
        """
        try:
            # Test connection first using connection manager
            if not snowflake_manager.test_connection():
                return ToolResult(
                    tool_name=self.capabilities.name,
                    status=ToolResultStatus.ERROR,
                    data={"error": "Failed to connect to Snowflake"},
                    metadata={"tool": self.capabilities.name}
                )
            
            # Check if query is a file path
            if query.endswith('.sql') and Path(query).exists():
                # Read from file using connection manager
                file_query = Path(query).read_text()
                df = snowflake_manager.execute_query(file_query, parameters)
            else:
                # Execute direct query using connection manager
                df = snowflake_manager.execute_query(query, parameters)
            
            # Apply limit and handle large result sets
            total_rows = len(df)
            if total_rows > limit:
                df_limited = df.head(limit)
                truncated = True
            else:
                df_limited = df
                truncated = False

            # For very large result sets (>100 rows), provide summary instead of full data
            if total_rows > 100:
                # Get table names if this is a SHOW TABLES query
                if 'show tables' in query.lower() or 'table' in df.columns[0].lower():
                    table_names = df_limited.iloc[:, 1].tolist()  # Usually table name is second column
                    result_data = {
                        "summary": f"Found {total_rows} tables in Snowflake",
                        "tables": table_names[:50],  # Show first 50 tables
                        "total_tables": total_rows,
                        "sample_shown": min(50, len(table_names)),
                        "query_type": "SHOW TABLES"
                    }
                else:
                    # Convert to dictionary for JSON serialization
                    df_str = df_limited.astype(str)
                    result_data = {
                        "summary": f"Query returned {total_rows} rows",
                        "sample_rows": df_str.head(10).to_dict('records'),
                        "columns": df.columns.tolist(),
                        "total_rows": total_rows,
                        "sample_shown": min(10, len(df_limited))
                    }
            else:
                # Convert to dictionary for JSON serialization
                df_str = df_limited.astype(str)
                result_data = {
                    "rows": df_str.to_dict('records'),
                    "columns": df.columns.tolist(),
                    "row_count": len(df_limited),
                    "truncated": truncated,
                    "total_available": total_rows
                }
            
            logger.info(f"Snowflake query executed successfully. Returned {total_rows} rows.")
            
            return ToolResult(
                tool_name=self.capabilities.name,
                status=ToolResultStatus.SUCCESS,
                data=result_data,
                metadata={
                    "tool": self.capabilities.name,
                    "query_type": "file" if query.endswith('.sql') else "direct",
                    "parameters_used": parameters is not None
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing Snowflake query: {e}")
            return ToolResult(
                tool_name=self.capabilities.name,
                status=ToolResultStatus.ERROR,
                data={"error": str(e)},
                metadata={"tool": self.capabilities.name}
            )
    
    def _execute_direct_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Execute a direct SQL query string using connection manager."""
        return snowflake_manager.execute_query(query, parameters)
    
    def get_schema_info(self) -> ToolResult:
        """Get information about available tables and schemas."""
        try:
            schema_query = """
            SELECT 
                table_schema,
                table_name,
                table_type,
                row_count,
                created,
                last_altered
            FROM information_schema.tables 
            WHERE table_schema != 'INFORMATION_SCHEMA'
            ORDER BY table_schema, table_name
            """
            
            result = self._execute_direct_query(schema_query)
            
            return ToolResult(
                tool_name=self.capabilities.name,
                status=ToolResultStatus.SUCCESS,
                data={
                    "tables": result.to_dict('records'),
                    "schema_count": result['TABLE_SCHEMA'].nunique(),
                    "table_count": len(result)
                },
                metadata={"tool": self.capabilities.name, "query_type": "schema_info"}
            )
            
        except Exception as e:
            logger.error(f"Error getting schema info: {e}")
            return ToolResult(
                tool_name=self.capabilities.name,
                status=ToolResultStatus.ERROR,
                data={"error": str(e)},
                metadata={"tool": self.capabilities.name}
            )
