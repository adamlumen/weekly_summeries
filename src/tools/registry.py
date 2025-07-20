from typing import Dict, List, Any, Optional, Type
import importlib
import inspect
import logging
from pathlib import Path

from .base_tool import BaseTool, ToolCapability

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    Central registry for all tools in the system.
    Handles tool discovery, registration, and lifecycle management.
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._initialized = False
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the registry and auto-discover tools."""
        if self._initialized:
            return
            
        config = config or {}
        
        # Auto-discover tools from the tools directory
        self._discover_tools()
        
        # Initialize enabled tools
        for tool_name, tool_instance in self._tools.items():
            tool_config = config.get(f"tools.{tool_name}", {})
            if tool_config.get("enabled", True):
                try:
                    success = tool_instance.initialize()
                    if success:
                        logger.info(f"Initialized tool: {tool_name}")
                    else:
                        logger.warning(f"Failed to initialize tool: {tool_name}")
                except Exception as e:
                    logger.error(f"Error initializing tool {tool_name}: {e}")
        
        self._initialized = True
        logger.info(f"Tool registry initialized with {len(self._tools)} tools")
    
    def _discover_tools(self) -> None:
        """Auto-discover tools from the tools directory."""
        tools_dir = Path(__file__).parent
        
        # Look for tool modules in subdirectories
        for category_dir in tools_dir.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('__'):
                self._discover_tools_in_directory(category_dir)
    
    def _discover_tools_in_directory(self, directory: Path) -> None:
        """Discover tools in a specific directory."""
        for py_file in directory.glob("*_tool.py"):
            module_name = f"src.tools.{directory.name}.{py_file.stem}"
            try:
                module = importlib.import_module(module_name)
                
                # Find BaseTool subclasses in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseTool) and 
                        obj != BaseTool and 
                        not inspect.isabstract(obj)):
                        
                        # Create instance and register
                        tool_instance = obj()
                        self.register_tool(tool_instance)
                        logger.debug(f"Discovered tool: {name} in {module_name}")
                        
            except Exception as e:
                logger.warning(f"Failed to import tool module {module_name}: {e}")
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        tool_name = tool.capabilities.name
        
        if tool_name in self._tools:
            logger.warning(f"Tool {tool_name} already registered, replacing...")
        
        self._tools[tool_name] = tool
        self._tool_classes[tool_name] = type(tool)
        logger.debug(f"Registered tool: {tool_name}")
    
    def register_tool_class(self, tool_class: Type[BaseTool], config: Optional[Dict[str, Any]] = None) -> None:
        """Register a tool class and create an instance."""
        tool_instance = tool_class(config)
        self.register_tool(tool_instance)
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def get_enabled_tools(self) -> Dict[str, BaseTool]:
        """Get only enabled tools."""
        return {name: tool for name, tool in self._tools.items() if tool.enabled}
    
    def get_tools_for_intent(self, intent: str, context: Dict[str, Any], min_confidence: float = 0.1) -> List[tuple[BaseTool, float]]:
        """
        Get tools that are suitable for the given intent, sorted by confidence.
        
        Args:
            intent: The user's intent/request
            context: Additional context
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of (tool, confidence) tuples sorted by confidence (descending)
        """
        tool_scores = []
        
        for tool in self.get_enabled_tools().values():
            confidence = tool.should_use(intent, context)
            if confidence >= min_confidence:
                tool_scores.append((tool, confidence))
        
        # Sort by confidence (descending)
        tool_scores.sort(key=lambda x: x[1], reverse=True)
        return tool_scores
    
    def get_tool_capabilities(self) -> Dict[str, ToolCapability]:
        """Get capabilities for all tools."""
        return {name: tool.capabilities for name, tool in self._tools.items()}
    
    def get_openai_functions(self) -> List[Dict[str, Any]]:
        """Get OpenAI function definitions for all enabled tools."""
        functions = []
        for tool in self.get_enabled_tools().values():
            try:
                function_def = tool.get_openai_function_definition()
                functions.append(function_def)
            except Exception as e:
                logger.warning(f"Failed to get OpenAI function for {tool.capabilities.name}: {e}")
        
        return functions
    
    async def cleanup(self) -> None:
        """Cleanup all tools."""
        for tool in self._tools.values():
            try:
                await tool.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up tool {tool.capabilities.name}: {e}")
        
        self._tools.clear()
        self._tool_classes.clear()
        self._initialized = False
        logger.info("Tool registry cleaned up")
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all tools with their information."""
        tools_info = []
        for tool in self._tools.values():
            capabilities = tool.capabilities
            tools_info.append({
                "name": capabilities.name,
                "description": capabilities.description,
                "enabled": tool.enabled,
                "initialized": tool.is_initialized,
                "use_cases": capabilities.use_cases,
                "data_sources": capabilities.data_sources,
                "prerequisites": capabilities.prerequisites
            })
        return tools_info
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, tool_name: str) -> bool:
        return tool_name in self._tools
    
    def __getitem__(self, tool_name: str) -> BaseTool:
        return self._tools[tool_name]

# Global registry instance
tool_registry = ToolRegistry()
