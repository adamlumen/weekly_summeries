"""
Test configuration and fixtures.
"""

import pytest
import asyncio
from typing import Generator
from unittest.mock import Mock

from src.agent.intelligent_agent import IntelligentAgent
from src.tools.registry import ToolRegistry


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.choices[0].message.function_call = None
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def tool_registry():
    """Create a test tool registry."""
    return ToolRegistry()


@pytest.fixture
def intelligent_agent(mock_openai_client, tool_registry):
    """Create a test intelligent agent."""
    return IntelligentAgent(
        openai_client=mock_openai_client,
        tool_registry=tool_registry
    )


@pytest.fixture
def sample_user_request():
    """Sample user request for testing."""
    return {
        "user_request": "Create a weekly summary for user123",
        "user_id": "user123",
        "session_id": "session456",
        "additional_context": {
            "date": "2025-07-20",
            "preferences": {"format": "detailed"}
        }
    }
