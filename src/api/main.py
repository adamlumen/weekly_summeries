from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ..agent.intelligent_agent import IntelligentAgent
from ..tools.registry import tool_registry
from ..tools.database.connection_manager import snowflake_manager
from ..config.settings import settings

logger = logging.getLogger(__name__)

# Request/Response models
class ProcessRequest(BaseModel):
    """Request model for processing user requests."""
    user_request: str = Field(..., description="The user's request or question")
    user_id: Optional[str] = Field(None, description="Optional user ID for context")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation tracking")
    additional_context: Optional[Dict[str, Any]] = Field(None, description="Additional context data")

class ProcessResponse(BaseModel):
    """Response model for processed requests."""
    response: str = Field(..., description="The agent's response")
    status: str = Field(..., description="Processing status")
    tool_results: list = Field(default_factory=list, description="Results from tool executions")
    tool_actions: list = Field(default_factory=list, description="Actions taken by tools")
    context: Dict[str, Any] = Field(default_factory=dict, description="Processing context")
    timestamp: str = Field(..., description="Response timestamp")
    error: Optional[str] = Field(None, description="Error message if any")

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    tools_available: int = Field(..., description="Number of available tools")
    timestamp: str = Field(..., description="Check timestamp")

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Intelligent agent for personalized weekly recommendations",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent: Optional[IntelligentAgent] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    global agent
    
    try:
        # Initialize tool registry
        tool_config = settings.load_tool_configs()
        await tool_registry.initialize(tool_config)
        
        # Initialize intelligent agent
        openai_config = settings.get_openai_config()
        agent = IntelligentAgent(
            api_key=openai_config["api_key"],
            model=openai_config["model"],
            max_tokens=openai_config["max_tokens"],
            temperature=openai_config["temperature"]
        )
        
        logger.info(f"Application started successfully with {len(tool_registry)} tools")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    try:
        if tool_registry:
            await tool_registry.cleanup()
        
        # Cleanup Snowflake connection manager
        snowflake_manager.cleanup()
        
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

def get_agent() -> IntelligentAgent:
    """Dependency to get the global agent instance."""
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return agent

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic information."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation disabled in production"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if agent is not None else "unhealthy",
        version=settings.app_version,
        tools_available=len(tool_registry),
        timestamp=datetime.now().isoformat()
    )

@app.post("/agent/process", response_model=ProcessResponse)
async def process_request(
    request: ProcessRequest,
    current_agent: IntelligentAgent = Depends(get_agent)
) -> ProcessResponse:
    """
    Process a user request using the intelligent agent.
    
    The agent will:
    1. Analyze the user's intent
    2. Select appropriate tools
    3. Execute tools in the correct order
    4. Generate a comprehensive response
    """
    try:
        logger.info(f"Processing request: {request.user_request[:100]}...")
        
        # Process the request using the intelligent agent
        result = await current_agent.process_request(
            user_request=request.user_request,
            user_id=request.user_id,
            additional_context=request.additional_context or {}
        )
        
        # Convert to response model
        response = ProcessResponse(
            response=result["response"],
            status=result["status"],
            tool_results=result.get("tool_results", []),
            tool_actions=result.get("tool_actions", []),
            context=result.get("context", {}),
            timestamp=result["timestamp"],
            error=result.get("error")
        )
        
        logger.info(f"Request processed successfully: {result['status']}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e) if settings.debug else "An error occurred processing your request"
            }
        )

@app.get("/tools", response_model=Dict[str, Any])
async def list_tools():
    """List all available tools and their capabilities."""
    try:
        tools_info = tool_registry.list_tools()
        return {
            "total_tools": len(tools_info),
            "tools": tools_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving tools information")

@app.get("/tools/{tool_name}", response_model=Dict[str, Any])
async def get_tool_info(tool_name: str):
    """Get detailed information about a specific tool."""
    try:
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        capabilities = tool.capabilities
        return {
            "name": capabilities.name,
            "description": capabilities.description,
            "parameters": capabilities.parameters,
            "use_cases": capabilities.use_cases,
            "data_sources": capabilities.data_sources,
            "prerequisites": capabilities.prerequisites,
            "enabled": tool.enabled,
            "initialized": tool.is_initialized,
            "openai_function": tool.get_openai_function_definition()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool info for {tool_name}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving tool information")

@app.post("/agent/test-tools", response_model=Dict[str, Any])
async def test_tools(
    request: ProcessRequest,
    current_agent: IntelligentAgent = Depends(get_agent)
):
    """
    Test tool selection without executing them.
    Useful for debugging and understanding which tools would be selected.
    """
    try:
        # Build context
        context = current_agent.context_manager.build_context(
            user_request=request.user_request,
            user_id=request.user_id,
            additional_context=request.additional_context or {}
        )
        
        # Get tool recommendations
        recommended_tools = current_agent.tool_selector.select_tools(
            request.user_request, context
        )
        
        # Format response
        tools_info = []
        for tool, confidence in recommended_tools:
            tools_info.append({
                "name": tool.capabilities.name,
                "description": tool.capabilities.description,
                "confidence": confidence,
                "use_cases": tool.capabilities.use_cases
            })
        
        return {
            "user_request": request.user_request,
            "context": context,
            "recommended_tools": tools_info,
            "explanation": current_agent.tool_selector.get_tool_selection_explanation(
                request.user_request, recommended_tools
            ),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error testing tools: {e}")
        raise HTTPException(status_code=500, detail="Error testing tool selection")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )
