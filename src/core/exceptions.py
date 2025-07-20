"""
Custom exceptions for the intelligent agent system.
"""

class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass

class ToolError(AgentError):
    """Exception raised when a tool execution fails."""
    
    def __init__(self, tool_name: str, message: str, original_error: Exception = None):
        self.tool_name = tool_name
        self.original_error = original_error
        super().__init__(f"Tool '{tool_name}' failed: {message}")

class ToolNotFoundError(AgentError):
    """Exception raised when a requested tool is not found."""
    
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' not found in registry")

class ToolConfigurationError(AgentError):
    """Exception raised when a tool is not properly configured."""
    
    def __init__(self, tool_name: str, missing_config: str):
        self.tool_name = tool_name
        self.missing_config = missing_config
        super().__init__(f"Tool '{tool_name}' missing configuration: {missing_config}")

class InvalidParametersError(AgentError):
    """Exception raised when invalid parameters are provided to a tool."""
    
    def __init__(self, tool_name: str, invalid_params: list):
        self.tool_name = tool_name
        self.invalid_params = invalid_params
        super().__init__(f"Tool '{tool_name}' received invalid parameters: {invalid_params}")

class DatabaseConnectionError(AgentError):
    """Exception raised when database connection fails."""
    pass

class GoogleDriveError(AgentError):
    """Exception raised when Google Drive operations fail."""
    pass

class NotionError(AgentError):
    """Exception raised when Notion operations fail."""
    pass

class SlackError(AgentError):
    """Exception raised when Slack operations fail."""
    pass

class OpenAIError(AgentError):
    """Exception raised when OpenAI API operations fail."""
    pass

class ContextError(AgentError):
    """Exception raised when context management fails."""
    pass

class ConversationError(AgentError):
    """Exception raised when conversation state management fails."""
    pass
