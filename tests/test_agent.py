"""
Tests for the intelligent agent.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from src.agent.intelligent_agent import IntelligentAgent
from src.tools.base_tool import ToolResult, ToolResultStatus


class TestIntelligentAgent:
    """Test cases for the intelligent agent."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, intelligent_agent):
        """Test agent initialization."""
        assert intelligent_agent is not None
        assert intelligent_agent.tool_registry is not None
    
    @pytest.mark.asyncio
    async def test_process_request_basic(self, intelligent_agent, sample_user_request):
        """Test basic request processing."""
        # Mock tool execution
        mock_tool = AsyncMock()
        mock_tool.capabilities.name = "test_tool"
        mock_tool.should_use.return_value = 0.8
        mock_tool.execute.return_value = ToolResult(
            tool_name="test_tool",
            status=ToolResultStatus.SUCCESS,
            data={"result": "test data"}
        )
        
        intelligent_agent.tool_registry.get_available_tools = Mock(return_value=[mock_tool])
        
        # Process request
        result = await intelligent_agent.process_request(
            user_request=sample_user_request["user_request"],
            context=sample_user_request
        )
        
        assert result is not None
        assert "response" in result
    
    def test_extract_keywords(self, intelligent_agent):
        """Test keyword extraction from user requests."""
        request = "Create a weekly summary for user123 with database analysis"
        keywords = intelligent_agent._extract_keywords(request)
        
        expected_keywords = ["create", "weekly", "summary", "user123", "database", "analysis"]
        
        for keyword in expected_keywords:
            assert keyword in keywords
    
    def test_calculate_tool_confidence(self, intelligent_agent):
        """Test tool confidence calculation."""
        request_keywords = ["database", "user", "analysis"]
        tool_keywords = ["database", "query", "user", "data"]
        
        confidence = intelligent_agent._calculate_confidence(request_keywords, tool_keywords)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be high confidence due to keyword overlap
