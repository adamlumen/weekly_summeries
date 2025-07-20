from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime

class ToolResultStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    SKIPPED = "skipped"

@dataclass
class ToolCapability:
    """Describes what a tool can do and when to use it."""
    name: str
    description: str
    parameters: Dict[str, Any]
    use_cases: List[str]
    data_sources: List[str]
    prerequisites: List[str]
    confidence_keywords: List[str]  # Keywords that increase confidence for this tool

@dataclass
class ToolResult:
    """Standard result format for all tools."""
    tool_name: str
    status: ToolResultStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    result_id: Optional[str] = None
    
    def __post_init__(self):
        if self.result_id is None:
            self.result_id = str(uuid.uuid4())

@dataclass
class ToolAction:
    """Represents an action the agent wants to take with a tool."""
    tool_name: str
    parameters: Dict[str, Any]
    priority: int = 1  # 1 is highest priority
    depends_on: Optional[List[str]] = None  # Tool result IDs this action depends on
    action_id: Optional[str] = None
    
    def __post_init__(self):
        if self.action_id is None:
            self.action_id = str(uuid.uuid4())

class BaseTool(ABC):
    """
    Abstract base class for all tools in the system.
    Each tool must implement this interface to be discoverable and usable by the agent.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self._initialized = False
    
    @property
    @abstractmethod
    def capabilities(self) -> ToolCapability:
        """
        Describes what this tool can do.
        This is used by the agent to decide when to use the tool.
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.
        Should return a ToolResult with status and data.
        """
        pass
    
    def initialize(self) -> bool:
        """
        Initialize the tool (setup connections, auth, etc.).
        Override this if your tool needs setup.
        """
        self._initialized = True
        return True
    
    async def cleanup(self) -> None:
        """
        Cleanup resources when tool is no longer needed.
        Override this if your tool needs cleanup.
        """
        pass
    
    def should_use(self, intent: str, context: Dict[str, Any]) -> float:
        """
        Return confidence score (0-1) for using this tool given the intent and context.
        Higher score means higher confidence.
        
        Args:
            intent: The user's intent/request as a string
            context: Additional context like previous results, user preferences, etc.
            
        Returns:
            float: Confidence score between 0 and 1
        """
        if not self.enabled:
            return 0.0
            
        # Basic implementation using keywords
        intent_lower = intent.lower()
        capabilities = self.capabilities
        
        # Check use cases
        use_case_matches = sum(1 for use_case in capabilities.use_cases 
                              if use_case.lower() in intent_lower)
        
        # Check confidence keywords
        keyword_matches = sum(1 for keyword in capabilities.confidence_keywords 
                             if keyword.lower() in intent_lower)
        
        # Check if prerequisites are met
        prereq_penalty = 0
        for prereq in capabilities.prerequisites:
            if prereq not in context:
                prereq_penalty += 0.2
        
        # Calculate confidence score
        total_keywords = len(capabilities.use_cases) + len(capabilities.confidence_keywords)
        if total_keywords == 0:
            base_score = 0.1
        else:
            base_score = (use_case_matches + keyword_matches) / total_keywords
        
        # Apply penalty for missing prerequisites
        final_score = max(0, base_score - prereq_penalty)
        
        return min(1.0, final_score)
    
    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """
        Validate and clean parameters before execution.
        Override this to add custom validation logic.
        
        Returns:
            Dict with validated parameters
        """
        return kwargs
    
    @property
    def is_initialized(self) -> bool:
        """Check if tool is initialized and ready to use."""
        return self._initialized
    
    def get_openai_function_definition(self) -> Dict[str, Any]:
        """
        Generate OpenAI function definition for this tool.
        This allows the tool to be used as an OpenAI function.
        """
        capabilities = self.capabilities
        
        return {
            "name": capabilities.name,
            "description": capabilities.description,
            "parameters": {
                "type": "object",
                "properties": capabilities.parameters,
                "required": [
                    param for param, config in capabilities.parameters.items()
                    if config.get("required", False)
                ]
            }
        }
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.capabilities.name})"
    
    def __repr__(self) -> str:
        return self.__str__()
