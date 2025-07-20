from typing import Dict, Any, Optional, List
import asyncio
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from ..base_tool import BaseTool, ToolCapability, ToolResult, ToolResultStatus

logger = logging.getLogger(__name__)

class MCPDatabaseTool(BaseTool):
    """
    Database tool that uses MCP (Model Context Protocol) pattern for database operations.
    Executes predefined queries with user parameters.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.database_url = config.get("database_url") if config else None
        self.engine = None
        self.session_factory = None
        
        # Predefined queries that can be executed safely
        self.predefined_queries = {
            "user_activity": """
                SELECT 
                    activity_date,
                    activity_type,
                    activity_count,
                    duration_minutes,
                    metadata
                FROM user_activities 
                WHERE user_id = :user_id 
                AND activity_date = :date
                ORDER BY activity_date DESC
            """,
            
            "user_weekly_summary": """
                SELECT 
                    user_id,
                    week_start_date,
                    total_activities,
                    avg_daily_duration,
                    most_common_activity,
                    goal_completion_rate
                FROM weekly_summaries 
                WHERE user_id = :user_id 
                AND week_start_date <= :date 
                AND week_end_date >= :date
            """,
            
            "user_preferences": """
                SELECT 
                    preference_key,
                    preference_value,
                    updated_at
                FROM user_preferences 
                WHERE user_id = :user_id
            """,
            
            "user_historical_trends": """
                SELECT 
                    metric_name,
                    metric_value,
                    metric_date,
                    trend_direction
                FROM user_metrics 
                WHERE user_id = :user_id 
                AND metric_date >= DATE(:date) - INTERVAL '30 days'
                ORDER BY metric_date DESC
            """
        }
    
    @property
    def capabilities(self) -> ToolCapability:
        return ToolCapability(
            name="database_query",
            description="Retrieve user data from database using predefined queries",
            parameters={
                "user_id": {
                    "type": "string",
                    "description": "The user ID to query data for",
                    "required": True
                },
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format",
                    "required": True
                },
                "query_type": {
                    "type": "string",
                    "description": "Type of query to execute",
                    "enum": ["user_activity", "user_weekly_summary", "user_preferences", "user_historical_trends"],
                    "default": "user_activity"
                }
            },
            use_cases=[
                "user_activity", "historical_data", "preferences", "weekly_summary",
                "user_metrics", "activity_logs", "user_behavior"
            ],
            data_sources=["postgresql", "mysql", "database"],
            prerequisites=["database_connection"],
            confidence_keywords=[
                "user", "activity", "data", "history", "database", "query",
                "metrics", "preferences", "summary", "trends"
            ]
        )
    
    async def initialize(self) -> bool:
        """Initialize database connection."""
        try:
            if not self.database_url:
                logger.error("Database URL not provided")
                return False
            
            # Create async engine
            self.engine = create_async_engine(
                self.database_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Create session factory
            self.session_factory = sessionmaker(
                self.engine, 
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self._initialized = True
            logger.info("Database tool initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database tool: {e}")
            return False
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute a database query with the given parameters."""
        if not self._initialized:
            return ToolResult(
                tool_name=self.capabilities.name,
                status=ToolResultStatus.ERROR,
                error="Tool not initialized"
            )
        
        try:
            # Validate required parameters
            user_id = kwargs.get("user_id")
            date = kwargs.get("date")
            query_type = kwargs.get("query_type", "user_activity")
            
            if not user_id:
                return ToolResult(
                    tool_name=self.capabilities.name,
                    status=ToolResultStatus.ERROR,
                    error="user_id parameter is required"
                )
            
            if not date:
                return ToolResult(
                    tool_name=self.capabilities.name,
                    status=ToolResultStatus.ERROR,
                    error="date parameter is required"
                )
            
            # Get the predefined query
            if query_type not in self.predefined_queries:
                return ToolResult(
                    tool_name=self.capabilities.name,
                    status=ToolResultStatus.ERROR,
                    error=f"Unknown query type: {query_type}"
                )
            
            query = self.predefined_queries[query_type]
            
            # Execute the query
            result_data = await self._execute_query(query, {
                "user_id": user_id,
                "date": date
            })
            
            return ToolResult(
                tool_name=self.capabilities.name,
                status=ToolResultStatus.SUCCESS,
                data={
                    "query_type": query_type,
                    "user_id": user_id,
                    "date": date,
                    "results": result_data,
                    "record_count": len(result_data)
                },
                metadata={
                    "query_executed": query_type,
                    "parameters_used": {"user_id": user_id, "date": date}
                }
            )
            
        except Exception as e:
            logger.error(f"Error executing database query: {e}")
            return ToolResult(
                tool_name=self.capabilities.name,
                status=ToolResultStatus.ERROR,
                error=str(e)
            )
    
    async def _execute_query(self, query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as list of dictionaries."""
        async with self.session_factory() as session:
            try:
                result = await session.execute(text(query), parameters)
                
                # Convert result to list of dictionaries
                columns = result.keys()
                rows = result.fetchall()
                
                return [
                    dict(zip(columns, row))
                    for row in rows
                ]
                
            except Exception as e:
                logger.error(f"Database query execution failed: {e}")
                raise
    
    async def cleanup(self) -> None:
        """Cleanup database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections cleaned up")
    
    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Validate and clean parameters before execution."""
        validated = {}
        
        # Validate user_id
        user_id = kwargs.get("user_id")
        if user_id:
            # Basic sanitization - only allow alphanumeric and common safe characters
            import re
            if re.match(r'^[a-zA-Z0-9_@.-]+$', str(user_id)):
                validated["user_id"] = str(user_id)
            else:
                raise ValueError(f"Invalid user_id format: {user_id}")
        
        # Validate date
        date = kwargs.get("date")
        if date:
            # Validate date format
            from datetime import datetime
            try:
                datetime.strptime(date, "%Y-%m-%d")
                validated["date"] = date
            except ValueError:
                raise ValueError(f"Invalid date format: {date}. Expected YYYY-MM-DD")
        
        # Validate query_type
        query_type = kwargs.get("query_type", "user_activity")
        if query_type in self.predefined_queries:
            validated["query_type"] = query_type
        else:
            raise ValueError(f"Invalid query_type: {query_type}")
        
        return validated
    
    def should_use(self, intent: str, context: Dict[str, Any]) -> float:
        """Determine if this tool should be used based on intent and context."""
        base_confidence = super().should_use(intent, context)
        
        # Boost confidence if we have required parameters
        if context.get("user_id") and context.get("date"):
            base_confidence += 0.3
        
        # Boost for data-related requests
        data_keywords = ["data", "activity", "history", "user", "database", "query"]
        intent_lower = intent.lower()
        keyword_matches = sum(1 for keyword in data_keywords if keyword in intent_lower)
        
        if keyword_matches > 0:
            base_confidence += (keyword_matches / len(data_keywords)) * 0.2
        
        return min(1.0, base_confidence)
    
    def get_sample_queries(self) -> Dict[str, str]:
        """Get sample queries for documentation/testing purposes."""
        return {
            query_type: query.strip()
            for query_type, query in self.predefined_queries.items()
        }
