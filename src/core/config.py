"""
Configuration management for the intelligent agent system.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML files.
    
    Args:
        config_path: Optional path to config directory
        
    Returns:
        Combined configuration dictionary
    """
    if config_path is None:
        # Default to config directory relative to this file
        config_path = Path(__file__).parent.parent.parent / "config"
    else:
        config_path = Path(config_path)
    
    config = {}
    
    # Load agent prompts
    agent_prompts_file = config_path / "agent_prompts.yaml"
    if agent_prompts_file.exists():
        with open(agent_prompts_file, 'r') as f:
            config['agent_prompts'] = yaml.safe_load(f)
    
    # Load tool configurations
    tool_configs_file = config_path / "tool_configs.yaml"  
    if tool_configs_file.exists():
        with open(tool_configs_file, 'r') as f:
            config['tool_configs'] = yaml.safe_load(f)
    
    return config

def get_openai_config() -> Dict[str, Any]:
    """Get OpenAI configuration from environment variables."""
    return {
        'api_key': os.getenv('OPENAI_API_KEY'),
        'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
        'temperature': float(os.getenv('OPENAI_TEMPERATURE', '0.7')),
        'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '2000')),
        'timeout': int(os.getenv('OPENAI_TIMEOUT', '60'))
    }

def get_database_config() -> Dict[str, Any]:
    """Get database configuration from environment variables."""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'recommendations'),
        'username': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'ssl_mode': os.getenv('DB_SSL_MODE', 'prefer')
    }

def get_google_drive_config() -> Dict[str, Any]:
    """Get Google Drive configuration from environment variables."""
    return {
        'credentials_path': os.getenv('GOOGLE_CREDENTIALS_PATH'),
        'token_path': os.getenv('GOOGLE_TOKEN_PATH'),
        'scopes': os.getenv('GOOGLE_SCOPES', 'https://www.googleapis.com/auth/drive.readonly').split(',')
    }

def get_notion_config() -> Dict[str, Any]:
    """Get Notion configuration from environment variables."""
    return {
        'api_token': os.getenv('NOTION_API_TOKEN'),
        'workspace_id': os.getenv('NOTION_WORKSPACE_ID')
    }

def get_slack_config() -> Dict[str, Any]:
    """Get Slack configuration from environment variables."""
    return {
        'bot_token': os.getenv('SLACK_BOT_TOKEN'),
        'signing_secret': os.getenv('SLACK_SIGNING_SECRET'),
        'app_token': os.getenv('SLACK_APP_TOKEN')
    }
