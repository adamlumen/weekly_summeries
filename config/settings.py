from typing import Dict, Any, Optional
import os
import logging
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import validator
import yaml

class Settings(BaseSettings):
    """Application settings loaded from environment variables and config files."""
    
    # Application settings
    app_name: str = "Intelligent Weekly Recommendation Agent"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    
    # OpenAI settings
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.1
    
    # Database settings
    database_url: Optional[str] = None
    
    # Google Drive settings
    google_drive_credentials_file: Optional[str] = None
    google_drive_token_file: Optional[str] = None
    google_drive_scopes: str = "https://www.googleapis.com/auth/drive.readonly"
    
    # Tool enablement
    enable_database_tool: bool = True
    enable_google_drive_tool: bool = True
    enable_notion_tool: bool = False
    enable_slack_tool: bool = False
    
    # Security
    secret_key: str = "your-secret-key-change-this"
    access_token_expire_minutes: int = 30
    
    # Cache settings
    redis_url: Optional[str] = None
    cache_ttl: int = 3600
    
    # Paths
    config_dir: Path = Path(__file__).parent
    project_root: Path = Path(__file__).parent.parent
    
    @validator('openai_api_key')
    def validate_openai_key(cls, v):
        if not v or v == "your_openai_api_key_here":
            raise ValueError("OpenAI API key must be set")
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @property
    def google_drive_scopes_list(self) -> list:
        """Convert scopes string to list."""
        return [scope.strip() for scope in self.google_drive_scopes.split(",")]
    
    def load_agent_prompts(self) -> Dict[str, str]:
        """Load agent prompt templates from YAML file."""
        prompts_file = self.config_dir / "agent_prompts.yaml"
        if prompts_file.exists():
            with open(prompts_file, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def load_tool_configs(self) -> Dict[str, Any]:
        """Load tool configuration from YAML file."""
        config_file = self.config_dir / "tool_configs.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for tools."""
        return {
            "database_url": self.database_url,
            "enabled": self.enable_database_tool
        }
    
    def get_google_drive_config(self) -> Dict[str, Any]:
        """Get Google Drive configuration for tools."""
        return {
            "credentials_file": self.google_drive_credentials_file,
            "token_file": self.google_drive_token_file,
            "scopes": self.google_drive_scopes_list,
            "enabled": self.enable_google_drive_tool
        }
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration."""
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "max_tokens": self.openai_max_tokens,
            "temperature": self.openai_temperature
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

def setup_logging(settings: Settings) -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                settings.project_root / "logs" / "agent.log",
                mode="a"
            ) if (settings.project_root / "logs").exists() else logging.StreamHandler()
        ]
    )
    
    # Set specific loggers
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# Global settings instance
settings = Settings()

# Setup logging
try:
    # Create logs directory if it doesn't exist
    (settings.project_root / "logs").mkdir(exist_ok=True)
    setup_logging(settings)
except Exception as e:
    # Fallback to basic logging if log directory creation fails
    logging.basicConfig(level=getattr(logging, settings.log_level))
    logging.warning(f"Could not setup file logging: {e}")

logger = logging.getLogger(__name__)
logger.info(f"Settings loaded: {settings.app_name} v{settings.app_version}")
