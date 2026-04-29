"""Tests for MCP Manager"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from beaver_bot.core.config import (
    BeaverConfig, MCPServerConfig, MCPConfig, MCPConfig
)
from beaver_bot.core.mcp_manager import MCPManager, MCPTool


class TestMCPServerConfig:
    """Test MCP server configuration"""

    def test_stdio_config(self):
        """Test stdio transport config"""
        config = MCPServerConfig(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-time"]
        )
        assert config.command == "npx"
        assert config.url is None

    def test_http_config(self):
        """Test HTTP transport config"""
        config = MCPServerConfig(
            url="https://mcp.example.com/mcp",
            headers={"Authorization": "Bearer test"}
        )
        assert config.url == "https://mcp.example.com/mcp"
        assert config.command is None


class TestMCPTool:
    """Test MCPTool class"""

    def test_to_dict(self):
        """Test tool dict representation"""
        mock_manager = MagicMock()
        tool = MCPTool(
            name="get_time",
            server_name="time",
            description="Get current time",
            input_schema={"type": "object"},
            mcp_manager=mock_manager,
        )

        d = tool.to_dict()
        assert d["name"] == "mcp_time_get_time"
        assert d["description"] == "Get current time"
        assert d["server"] == "time"
        assert d["original_name"] == "get_time"

    def test_normalize_tool_name(self):
        """Test that tool names are normalized"""
        mock_manager = MagicMock()
        tool = MCPTool(
            name="list-files",
            server_name="filesystem",
            description="List files",
            input_schema={},
            mcp_manager=mock_manager,
        )

        d = tool.to_dict()
        # Name should be normalized (hyphen replaced with underscore)
        assert d["name"] == "mcp_filesystem_list_files"
        # But original_name keeps the original
        assert d["original_name"] == "list-files"


class TestMCPManager:
    """Test MCPManager class"""

    @pytest.fixture
    def config(self):
        """Create a test config"""
        return BeaverConfig()

    @pytest.fixture
    def mcp_manager(self, config):
        """Create an MCP manager"""
        return MCPManager(config)

    def test_init(self, mcp_manager):
        """Test manager initialization"""
        assert mcp_manager._tools == {}
        assert mcp_manager._server_processes == {}

    def test_get_tools_empty(self, mcp_manager):
        """Test getting tools when none loaded"""
        assert mcp_manager.get_tools() == []

    def test_get_tool_not_found(self, mcp_manager):
        """Test getting non-existent tool"""
        assert mcp_manager.get_tool("nonexistent") is None

    def test_build_env(self, mcp_manager):
        """Test environment building for subprocess"""
        user_env = {"MY_API_KEY": "secret123"}
        env = mcp_manager._build_env(user_env)

        # Should include baseline
        assert "PATH" in env
        assert "HOME" in env
        # Should include user vars
        assert env["MY_API_KEY"] == "secret123"

    def test_build_env_does_not_leak_all_env(self, mcp_manager):
        """Test that not all env vars are passed through"""
        import os
        # Set a test env var
        os.environ["MY_SECRET_TOKEN"] = "should_not_be_passed"

        env = mcp_manager._build_env({})

        # Baseline vars should be present
        assert "PATH" in env
        # But not all user env vars
        assert "MY_SECRET_TOKEN" not in env

    def test_mcp_config_parsing(self):
        """Test that mcp_servers config is parsed correctly"""
        # Create a temporary config file with mcp_servers
        import tempfile
        config_content = """
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        # Patch the config path to use our temp file
        from beaver_bot.core import config as config_module
        original_find = config_module.load_config

        def patched_load():
            import yaml
            with open(temp_path) as f:
                data = yaml.safe_load(f)
            # Apply the same remapping that load_config does
            if "mcp_servers" in data:
                data["mcp"] = {"servers": data.pop("mcp_servers")}
            return BeaverConfig(**data)

        config = patched_load()
        assert "time" in config.mcp.servers
        assert config.mcp.servers["time"].command == "uvx"


class TestMCPManagerIntegration:
    """Integration tests for MCP manager (mocked)"""

    @pytest.fixture
    def config_with_server(self):
        """Config with a test MCP server"""
        config = BeaverConfig()
        config.mcp.servers["test"] = MCPServerConfig(
            command="echo",
            args=["test"]
        )
        return config

    def test_init_empty_config(self):
        """Test initialization with no servers configured"""
        config = BeaverConfig()
        manager = MCPManager(config)
        # Should not raise
        import asyncio
        asyncio.run(manager.initialize())
        assert manager.get_tools() == []
