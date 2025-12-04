"""
Application Settings Module
---------------------------
Centralized configuration management using environment variables.
Configured for AWS-native services (Bedrock, OpenSearch Serverless).
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


@dataclass
class ServerConfig:
    """Web server configuration settings."""
    
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    
    @classmethod
    def from_environment(cls) -> "ServerConfig":
        """Load server config from environment variables."""
        return cls(
            host=os.getenv("SERVER_HOST", "0.0.0.0"),
            port=int(os.getenv("SERVER_PORT", "5000")),
            debug=os.getenv("DEBUG_MODE", "false").lower() == "true"
        )


@dataclass
class AWSConfig:
    """AWS services configuration."""
    
    region: str = "us-east-1"
    opensearch_endpoint: str = ""
    bedrock_model: str = "claude-3-sonnet"
    
    @classmethod
    def from_environment(cls) -> "AWSConfig":
        """Load AWS config from environment variables."""
        return cls(
            region=os.getenv("AWS_REGION", "us-east-1"),
            opensearch_endpoint=os.getenv("OPENSEARCH_ENDPOINT", ""),
            bedrock_model=os.getenv("BEDROCK_MODEL", "claude-3-sonnet")
        )
    
    def validate(self) -> bool:
        """Check if required AWS config is present."""
        return bool(self.opensearch_endpoint)


@dataclass
class VectorDBConfig:
    """Vector database (OpenSearch) configuration settings."""
    
    index_name: str = "healthai-knowledge-v1"
    vector_dimension: int = 384
    
    @classmethod
    def from_environment(cls) -> "VectorDBConfig":
        """Load vector DB config from environment variables."""
        return cls(
            index_name=os.getenv("KNOWLEDGE_INDEX_NAME", "healthai-knowledge-v1"),
            vector_dimension=int(os.getenv("VECTOR_DIMENSION", "384"))
        )


@dataclass
class LLMConfig:
    """Language model (Bedrock) configuration settings."""
    
    model_name: str = "claude-3-sonnet"
    temperature: float = 0.7
    max_tokens: int = 1024
    
    @classmethod
    def from_environment(cls) -> "LLMConfig":
        """Load LLM config from environment variables."""
        return cls(
            model_name=os.getenv("BEDROCK_MODEL", "claude-3-sonnet"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1024"))
        )


@dataclass
class AppSettings:
    """
    Master configuration container for all application settings.
    AWS-native: No external API keys required.
    """
    
    app_name: str = "HealthAI Assistant"
    version: str = "1.0.0"
    knowledge_base_path: str = "knowledge_base"
    
    server: ServerConfig = field(default_factory=ServerConfig)
    aws: AWSConfig = field(default_factory=AWSConfig)
    database: VectorDBConfig = field(default_factory=VectorDBConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    @classmethod
    def load(cls) -> "AppSettings":
        """
        Load complete application settings from environment.
        
        Returns:
            Fully populated AppSettings instance.
        """
        return cls(
            app_name=os.getenv("APP_NAME", "HealthAI Assistant"),
            version=os.getenv("APP_VERSION", "1.0.0"),
            knowledge_base_path=os.getenv("KNOWLEDGE_PATH", "knowledge_base"),
            server=ServerConfig.from_environment(),
            aws=AWSConfig.from_environment(),
            database=VectorDBConfig.from_environment(),
            llm=LLMConfig.from_environment()
        )
    
    def validate_all(self) -> dict:
        """
        Validate all configuration sections.
        
        Returns:
            Dictionary with validation status for each section.
        """
        return {
            "aws": self.aws.validate(),
        }
    
    def get_knowledge_base_directory(self) -> Path:
        """Return the path to the knowledge base directory."""
        return Path(self.knowledge_base_path)


# Global settings instance for easy access
_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """
    Get the global application settings instance.
    
    Returns:
        Cached AppSettings instance.
    """
    global _settings
    if _settings is None:
        _settings = AppSettings.load()
    return _settings


def reload_settings() -> AppSettings:
    """
    Force reload of settings from environment.
    
    Returns:
        Fresh AppSettings instance.
    """
    global _settings
    load_dotenv(override=True)
    _settings = AppSettings.load()
    return _settings
