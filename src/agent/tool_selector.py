from typing import Dict, List, Any, Optional, Tuple
import logging
from ..tools.registry import tool_registry
from ..tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ToolSelector:
    """
    Intelligent tool selection based on user intent and context.
    Decides which tools are most appropriate for a given request.
    """
    
    def __init__(self, min_confidence: float = 0.1):
        """
        Initialize the tool selector.
        
        Args:
            min_confidence: Minimum confidence threshold for tool selection
        """
        self.min_confidence = min_confidence
    
    def select_tools(self, 
                    user_request: str, 
                    context: Dict[str, Any]) -> List[Tuple[BaseTool, float]]:
        """
        Select tools based on user request and context.
        
        Args:
            user_request: The user's request/question
            context: Additional context information
            
        Returns:
            List of (tool, confidence) tuples sorted by confidence
        """
        logger.debug(f"Selecting tools for request: {user_request}")
        
        # Get tools from registry
        suitable_tools = tool_registry.get_tools_for_intent(
            intent=user_request,
            context=context,
            min_confidence=self.min_confidence
        )
        
        # Apply additional filtering and ranking
        filtered_tools = self._apply_contextual_filtering(suitable_tools, context)
        
        # Log selected tools
        tool_names = [tool.capabilities.name for tool, _ in filtered_tools]
        logger.info(f"Selected {len(filtered_tools)} tools: {tool_names}")
        
        return filtered_tools
    
    def _apply_contextual_filtering(self, 
                                   tools: List[Tuple[BaseTool, float]], 
                                   context: Dict[str, Any]) -> List[Tuple[BaseTool, float]]:
        """
        Apply additional filtering based on context.
        
        This method can be extended to implement more sophisticated
        filtering logic based on user preferences, data availability, etc.
        """
        filtered_tools = []
        
        for tool, confidence in tools:
            # Check prerequisites
            if self._check_prerequisites(tool, context):
                # Adjust confidence based on context
                adjusted_confidence = self._adjust_confidence(tool, confidence, context)
                if adjusted_confidence >= self.min_confidence:
                    filtered_tools.append((tool, adjusted_confidence))
            else:
                logger.debug(f"Tool {tool.capabilities.name} missing prerequisites")
        
        return filtered_tools
    
    def _check_prerequisites(self, tool: BaseTool, context: Dict[str, Any]) -> bool:
        """
        Check if all prerequisites for a tool are met.
        """
        prerequisites = tool.capabilities.prerequisites
        
        for prereq in prerequisites:
            if prereq not in context:
                return False
        
        return True
    
    def _adjust_confidence(self, 
                          tool: BaseTool, 
                          base_confidence: float, 
                          context: Dict[str, Any]) -> float:
        """
        Adjust confidence based on additional context factors.
        """
        adjusted_confidence = base_confidence
        
        # Boost confidence if user_id and date are available for data tools
        if tool.capabilities.name in ["database_query", "user_data_tool"]:
            if "user_id" in context and "date" in context:
                adjusted_confidence += 0.2
        
        # Boost confidence for documentation tools if request mentions guidelines/docs
        if tool.capabilities.name in ["drive_search", "google_drive_tool"]:
            doc_keywords = ["guide", "documentation", "template", "policy", "format"]
            request_lower = context.get("user_request", "").lower()
            if any(keyword in request_lower for keyword in doc_keywords):
                adjusted_confidence += 0.15
        
        # Reduce confidence if tool was recently used (avoid redundancy)
        recent_tools = context.get("recent_tool_usage", [])
        if tool.capabilities.name in recent_tools:
            adjusted_confidence -= 0.1
        
        # Ensure confidence stays within bounds
        return max(0.0, min(1.0, adjusted_confidence))
    
    def get_tool_selection_explanation(self, 
                                     user_request: str,
                                     selected_tools: List[Tuple[BaseTool, float]]) -> str:
        """
        Generate an explanation of why certain tools were selected.
        """
        if not selected_tools:
            return "No suitable tools found for this request."
        
        explanations = []
        explanations.append(f"Selected {len(selected_tools)} tools for: '{user_request}'")
        explanations.append("")
        
        for i, (tool, confidence) in enumerate(selected_tools, 1):
            capabilities = tool.capabilities
            explanations.append(
                f"{i}. {capabilities.name} (confidence: {confidence:.2f})"
            )
            explanations.append(f"   Purpose: {capabilities.description}")
            explanations.append(f"   Use cases: {', '.join(capabilities.use_cases)}")
            explanations.append("")
        
        return "\n".join(explanations)
    
    def suggest_additional_tools(self, 
                               user_request: str,
                               context: Dict[str, Any]) -> List[str]:
        """
        Suggest additional tools that might be useful but didn't meet
        the confidence threshold.
        """
        all_tools = tool_registry.get_enabled_tools()
        suggestions = []
        
        for tool_name, tool in all_tools.items():
            confidence = tool.should_use(user_request, context)
            if 0.05 <= confidence < self.min_confidence:  # Low but non-zero confidence
                suggestions.append(f"{tool_name} ({confidence:.2f})")
        
        return suggestions
