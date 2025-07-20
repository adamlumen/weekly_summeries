"""
Simple FastAPI application for the intelligent agent.
This is a minimal version to get the application running.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
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
    timestamp: str = Field(..., description="Check timestamp")
    environment: str = Field(..., description="Runtime environment")

# Initialize FastAPI app
app = FastAPI(
    title="Intelligent Weekly Recommendation Agent",
    version="1.0.0",
    description="An extensible AI agent that intelligently selects and uses tools",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Intelligent Weekly Recommendation Agent",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        environment=os.getenv("ENVIRONMENT", "development")
    )

@app.post("/agent/process", response_model=ProcessResponse, tags=["Agent"])
async def process_request(request: ProcessRequest):
    """
    Process a user request using the intelligent agent.
    
    This is a simplified version that returns a mock response.
    The full implementation will include tool selection and execution.
    """
    try:
        logger.info(f"Processing request: {request.user_request}")
        
        # For now, return a mock response
        # TODO: Implement actual agent processing
        mock_response = f"""
Hello! I received your request: "{request.user_request}"

This is a basic response from the intelligent agent. The system is running successfully!

Available features:
- ✅ FastAPI server running
- ✅ Request validation working
- ✅ Basic logging enabled
- ⏳ Agent tools (coming soon)
- ⏳ OpenAI integration (coming soon)
- ⏳ Database connectivity (coming soon)

To enable full functionality, you'll need to:
1. Add your OpenAI API key to .env file
2. Configure database connection
3. Enable the full agent implementation

Status: Basic functionality working!
        """.strip()
        
        return ProcessResponse(
            response=mock_response,
            status="success",
            tool_results=[],
            tool_actions=[],
            context={
                "user_id": request.user_id,
                "session_id": request.session_id,
                "additional_context": request.additional_context,
                "mock_mode": True
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

@app.get("/agent/status", tags=["Agent"])
async def agent_status():
    """Get agent status and available tools."""
    return {
        "status": "running",
        "mode": "basic",
        "message": "Agent is running in basic mode. Full functionality requires additional configuration.",
        "available_endpoints": [
            "GET /",
            "GET /health", 
            "POST /agent/process",
            "GET /agent/status",
            "GET /docs"
        ],
        "next_steps": [
            "Add OPENAI_API_KEY to .env file",
            "Configure database connection",
            "Enable full agent implementation"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
