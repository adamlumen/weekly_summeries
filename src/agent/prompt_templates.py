"""
Prompt templates for the intelligent agent.
"""

from typing import Dict, Any, List, Optional
from ..core.config import load_config

class PromptTemplates:
    """Manages prompt templates for the intelligent agent."""
    
    def __init__(self):
        """Initialize with configuration."""
        self.config = load_config()
        self.agent_prompts = self.config.get('agent_prompts', {})
    
    def get_system_prompt(self) -> str:
        """Get the main system prompt for the agent."""
        return self.agent_prompts.get('agent_prompts', {}).get('system_prompt', self._default_system_prompt())
    
    def get_tool_selection_prompt(self) -> str:
        """Get the tool selection guidance prompt."""
        return self.agent_prompts.get('agent_prompts', {}).get('tool_selection_prompt', self._default_tool_selection_prompt())
    
    def get_confidence_scoring_prompt(self) -> str:
        """Get the confidence scoring guidance."""
        return self.agent_prompts.get('agent_prompts', {}).get('confidence_scoring', self._default_confidence_scoring())
    
    def format_reasoning_template(self, template_type: str, **kwargs) -> str:
        """
        Format a reasoning template with provided variables.
        
        Args:
            template_type: Type of reasoning template
            **kwargs: Variables to substitute in template
            
        Returns:
            Formatted reasoning text
        """
        templates = self.agent_prompts.get('reasoning_templates', {})
        template = templates.get(template_type, "")
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            return f"Template variable missing: {e}"
    
    def build_tool_selection_context(self, available_tools: List[Dict[str, Any]]) -> str:
        """
        Build context about available tools for selection decisions.
        
        Args:
            available_tools: List of available tool information
            
        Returns:
            Formatted tool context
        """
        if not available_tools:
            return "No tools are currently available."
        
        context = "Available tools:\n\n"
        
        for tool in available_tools:
            name = tool.get('name', 'Unknown')
            description = tool.get('description', 'No description')
            use_cases = tool.get('use_cases', [])
            
            context += f"**{name}**\n"
            context += f"Description: {description}\n"
            
            if use_cases:
                context += f"Use cases: {', '.join(use_cases)}\n"
            
            context += "\n"
        
        return context
    
    def format_user_request_analysis(self, user_request: str, extracted_keywords: List[str], 
                                   context: Dict[str, Any]) -> str:
        """
        Format user request analysis for the agent.
        
        Args:
            user_request: Original user request
            extracted_keywords: Keywords extracted from request
            context: Additional context information
            
        Returns:
            Formatted analysis
        """
        analysis = f"User Request Analysis:\n\n"
        analysis += f"Original request: {user_request}\n\n"
        
        if extracted_keywords:
            analysis += f"Extracted keywords: {', '.join(extracted_keywords)}\n\n"
        
        if context.get('user_id'):
            analysis += f"User ID: {context['user_id']}\n"
        
        if context.get('session_id'):
            analysis += f"Session ID: {context['session_id']}\n"
        
        if context.get('conversation_history'):
            analysis += f"Previous interactions: {len(context['conversation_history'])} messages\n"
        
        analysis += "\n"
        return analysis
    
    def _default_system_prompt(self) -> str:
        """Default system prompt if not configured."""
        return """
You are an intelligent agent that helps users get personalized weekly recommendations and summaries.

Your capabilities include:
- Analyzing user data from databases
- Searching documentation in Google Drive
- Processing and analyzing data
- Generating personalized summaries
- Deciding which tools to use based on user requests

When a user makes a request, analyze it to determine:
1. What information is needed?
2. Where is that information likely stored?
3. What processing or analysis is required?
4. What format should the final response take?

Make intelligent decisions about which tools to use and in what order.
        """.strip()
    
    def _default_tool_selection_prompt(self) -> str:
        """Default tool selection prompt if not configured."""
        return """
You are deciding which tools to use for a user request. Consider these guidelines:

Available tools and their primary use cases:
- database_tool: User activity data, historical patterns, preferences, metrics
- google_drive_tool: Documentation, guidelines, templates, policies, formats
- notion_tool: Team knowledge, project docs, meeting notes, collaboration data
- slack_tool: Team communication, notifications, status updates, messaging
- data_analysis_tool: Process and analyze retrieved data, generate insights
- summary_tool: Generate personalized summaries and recommendations

Decision criteria:
1. Data sources needed (database, documents, external APIs)
2. Processing requirements (analysis, formatting, summarization)
3. Output format (summary, notification, data export)
4. User context and preferences
        """.strip()
    
    def _default_confidence_scoring(self) -> str:
        """Default confidence scoring guidance if not configured."""
        return """
Score tool confidence (0-1) based on:
- Keyword matches in user request
- Required data sources mentioned
- Context from previous interactions
- Tool availability and prerequisites

High confidence (0.8-1.0): Direct keyword matches, clear data source needs
Medium confidence (0.5-0.7): Related keywords, inferred needs
Low confidence (0.1-0.4): Tangential relation, fallback options
No confidence (0.0): Not applicable to request
        """.strip()

# Global instance
prompt_templates = PromptTemplates()
