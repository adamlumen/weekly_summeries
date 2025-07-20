from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class ContextManager:
    """
    Manages conversation context and state across tool executions.
    Helps maintain coherent conversations and avoid redundant operations.
    """
    
    def __init__(self, max_history_size: int = 50):
        """
        Initialize the context manager.
        
        Args:
            max_history_size: Maximum number of historical entries to keep
        """
        self.max_history_size = max_history_size
        self.session_contexts: Dict[str, Dict[str, Any]] = {}
    
    def build_context(self,
                     user_request: str,
                     user_id: Optional[str] = None,
                     session_id: Optional[str] = None,
                     additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build context for a user request.
        
        Args:
            user_request: The user's request
            user_id: Optional user ID
            session_id: Optional session ID for conversation tracking
            additional_context: Additional context data
            
        Returns:
            Complete context dictionary
        """
        # Create base context
        context = {
            "user_request": user_request,
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id or "default",
        }
        
        # Add user ID if provided
        if user_id:
            context["user_id"] = user_id
        
        # Extract entities from the request
        extracted_entities = self._extract_entities(user_request)
        context.update(extracted_entities)
        
        # Add session history if available
        if session_id and session_id in self.session_contexts:
            session_context = self.session_contexts[session_id]
            context["conversation_history"] = session_context.get("history", [])
            context["recent_tool_usage"] = session_context.get("recent_tools", [])
            context["user_preferences"] = session_context.get("preferences", {})
        
        # Merge additional context
        if additional_context:
            context.update(additional_context)
        
        logger.debug(f"Built context with {len(context)} keys")
        return context
    
    def _extract_entities(self, user_request: str) -> Dict[str, Any]:
        """
        Extract entities like dates, user IDs, etc. from the user request.
        """
        entities = {}
        
        # Extract dates
        date_patterns = [
            r'\b(\d{4}-\d{2}-\d{2})\b',  # YYYY-MM-DD
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',  # MM/DD/YYYY or M/D/YYYY
            r'\b(today|yesterday|tomorrow)\b',
            r'\b(last week|this week|next week)\b',
            r'\b(last month|this month|next month)\b'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, user_request, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    entities["date"] = parsed_date
                    entities["original_date_text"] = date_str
                break
        
        # Extract user identifiers
        user_patterns = [
            r'\buser[_\s]*(?:id)?[:\s]+([a-zA-Z0-9_-]+)\b',
            r'\bfor\s+user\s+([a-zA-Z0-9_-]+)\b',
            r'\b([a-zA-Z0-9_-]+)@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'  # Email
        ]
        
        for pattern in user_patterns:
            match = re.search(pattern, user_request, re.IGNORECASE)
            if match:
                entities["extracted_user_id"] = match.group(1)
                break
        
        # Extract data types or categories
        data_type_keywords = {
            "activity": ["activity", "activities", "actions", "behavior"],
            "preferences": ["preferences", "settings", "configuration"],
            "history": ["history", "historical", "past", "previous"],
            "summary": ["summary", "report", "overview", "digest"],
            "analysis": ["analysis", "insights", "trends", "patterns"]
        }
        
        request_lower = user_request.lower()
        for data_type, keywords in data_type_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                entities.setdefault("data_types", []).append(data_type)
        
        return entities
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse various date formats and return ISO format.
        """
        try:
            now = datetime.now()
            
            # Handle relative dates
            if date_str.lower() == "today":
                return now.date().isoformat()
            elif date_str.lower() == "yesterday":
                return (now - timedelta(days=1)).date().isoformat()
            elif date_str.lower() == "tomorrow":
                return (now + timedelta(days=1)).date().isoformat()
            elif "last week" in date_str.lower():
                return (now - timedelta(weeks=1)).date().isoformat()
            elif "this week" in date_str.lower():
                return now.date().isoformat()
            elif "next week" in date_str.lower():
                return (now + timedelta(weeks=1)).date().isoformat()
            
            # Handle absolute dates
            from dateutil import parser
            parsed_date = parser.parse(date_str)
            return parsed_date.date().isoformat()
            
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return None
    
    def update_context(self,
                      context: Dict[str, Any],
                      tool_results: List[Any]) -> None:
        """
        Update context with tool execution results and maintain session state.
        """
        session_id = context.get("session_id", "default")
        
        # Initialize session context if not exists
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = {
                "history": [],
                "recent_tools": [],
                "preferences": {},
                "created_at": datetime.now().isoformat()
            }
        
        session_context = self.session_contexts[session_id]
        
        # Add to conversation history
        history_entry = {
            "timestamp": context["timestamp"],
            "user_request": context["user_request"],
            "tool_results": [
                {
                    "tool_name": result.tool_name,
                    "status": result.status.value,
                    "has_data": result.data is not None
                }
                for result in tool_results
            ]
        }
        
        session_context["history"].append(history_entry)
        
        # Update recent tools
        for result in tool_results:
            if result.tool_name not in session_context["recent_tools"]:
                session_context["recent_tools"].append(result.tool_name)
        
        # Keep only recent tools (last 10)
        session_context["recent_tools"] = session_context["recent_tools"][-10:]
        
        # Keep history within limits
        if len(session_context["history"]) > self.max_history_size:
            session_context["history"] = session_context["history"][-self.max_history_size:]
        
        # Extract and update user preferences from successful results
        self._extract_preferences(context, tool_results, session_context)
    
    def _extract_preferences(self,
                           context: Dict[str, Any],
                           tool_results: List[Any],
                           session_context: Dict[str, Any]) -> None:
        """
        Extract user preferences from successful tool results.
        """
        preferences = session_context.setdefault("preferences", {})
        
        # Track frequently requested data types
        data_types = context.get("data_types", [])
        for data_type in data_types:
            key = f"requested_{data_type}"
            preferences[key] = preferences.get(key, 0) + 1
        
        # Track successful tool combinations
        successful_tools = [
            result.tool_name for result in tool_results
            if hasattr(result, 'status') and result.status.value == "success"
        ]
        
        if len(successful_tools) > 1:
            combination_key = "tool_combinations"
            if combination_key not in preferences:
                preferences[combination_key] = {}
            
            combo_str = " + ".join(sorted(successful_tools))
            preferences[combination_key][combo_str] = preferences[combination_key].get(combo_str, 0) + 1
    
    def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session context by ID."""
        return self.session_contexts.get(session_id)
    
    def clear_session_context(self, session_id: str) -> None:
        """Clear session context."""
        if session_id in self.session_contexts:
            del self.session_contexts[session_id]
    
    def get_user_preferences(self, session_id: str) -> Dict[str, Any]:
        """Get user preferences for a session."""
        session_context = self.session_contexts.get(session_id, {})
        return session_context.get("preferences", {})
    
    def get_conversation_summary(self, session_id: str) -> str:
        """Get a summary of the conversation history."""
        session_context = self.session_contexts.get(session_id)
        if not session_context:
            return "No conversation history found."
        
        history = session_context.get("history", [])
        if not history:
            return "No conversation history available."
        
        summary_parts = [
            f"Conversation started: {session_context.get('created_at', 'Unknown')}",
            f"Total interactions: {len(history)}",
            f"Recent tools used: {', '.join(session_context.get('recent_tools', [])[-5:])}",
        ]
        
        # Add recent requests
        recent_requests = [entry["user_request"] for entry in history[-3:]]
        if recent_requests:
            summary_parts.append("Recent requests:")
            for i, request in enumerate(recent_requests, 1):
                summary_parts.append(f"  {i}. {request}")
        
        return "\n".join(summary_parts)
