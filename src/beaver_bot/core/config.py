"""Beaver Bot Configuration Management"""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    name: str = "Beaver Bot"
    version: str = "0.1.0"
    debug: bool = False


class ModelConfig(BaseModel):
    provider: str = "openrouter"
    name: str = Field(default="anthropic/claude-3-haiku", validation_alias="model")
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7


class GitHubConfig(BaseModel):
    token: Optional[str] = None
    owner: str = "user-YeLei"
    repo: str = "beaver-bot"


class CLIConfig(BaseModel):
    prompt: str = "🦫 Beaver"
    welcome_banner: str = ""


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "json"


class FileToolConfig(BaseModel):
    """Configuration for file tool security settings"""
    root_path: Path = Field(default_factory=Path.cwd)


class BeaverConfig(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    file_tool: FileToolConfig = Field(default_factory=FileToolConfig)


def load_config(debug: bool = False) -> BeaverConfig:
    """Load configuration from settings.yaml and environment variables"""

    # Find config file
    config_paths = [
        Path("config/settings.yaml"),
        Path(__file__).parent.parent / "config" / "settings.yaml",
        Path.home() / ".beaver" / "config.yaml",
    ]

    config_data = {}
    for path in config_paths:
        if path.exists():
            with open(path) as f:
                config_data = yaml.safe_load(f) or {}
            break

    # Override with environment variables
    config_data["model"]["api_key"] = os.environ.get(
        "OPENROUTER_API_KEY",
        os.environ.get("ANTHROPIC_API_KEY", config_data.get("model", {}).get("api_key"))
    )
    config_data["github"]["token"] = os.environ.get(
        "GITHUB_TOKEN",
        config_data.get("github", {}).get("token")
    )

    # Apply debug mode
    if debug:
        config_data["app"] = config_data.get("app", {})
        config_data["app"]["debug"] = True
        config_data["logging"] = {"level": "DEBUG"}

    return BeaverConfig(**config_data)
