"""Beaver Agent MCP Manager - Connect to MCP servers and expose their tools"""

import asyncio
import json
import re
from pathlib import Path
from typing import Any, Optional

import structlog

from beaver_agent.core.config import BeaverConfig, MCPServerConfig

logger = structlog.get_logger()


class MCPTool:
    """Represents a tool from an MCP server"""

    def __init__(self, name: str, server_name: str, description: str,
                 input_schema: dict, mcp_manager: "MCPManager"):
        self.name = name
        self.server_name = server_name
        self.description = description
        self.input_schema = input_schema
        self.mcp_manager = mcp_manager

    def to_dict(self) -> dict:
        """Convert MCP tool to dict format for LLM API compatibility.

        Normalizes the tool name by replacing non-alphanumeric characters
        with underscores, then prefixes with 'mcp_{server_name}_'.

        Returns:
            dict: Tool representation with name, description, input_schema,
                  server info, and original_name fields.
        """
        normalized_name = re.sub(r"[^a-zA-Z0-9_]", "_", self.name)
        return {
            "name": f"mcp_{self.server_name}_{normalized_name}",
            "description": self.description,
            "input_schema": self.input_schema,
            "server": self.server_name,
            "original_name": self.name,
        }

    async def call(self, **kwargs) -> dict:
        """Call this MCP tool with the given arguments"""
        return await self.mcp_manager.call_tool(
            self.server_name, self.name, kwargs
        )


class MCPManager:
    """Manages MCP server connections and tool discovery.

    Supports both stdio (command-based) and HTTP (URL-based) transports.
    Each server can have multiple tools exposed via the MCP protocol.

    Attributes:
        config: BeaverConfig instance with MCP server definitions.
        mcp_configs_dir: Optional directory path to load additional MCP configs.
    """

    def __init__(self, config: BeaverConfig, mcp_configs_dir: str = None):
        """Initialize MCP manager and load server configurations.

        Args:
            config: BeaverConfig with mcp.servers definitions.
            mcp_configs_dir: Optional directory containing MCP config YAML files.
        """
        self.config = config
        self.config_root = config.model_fields['mcp'].default if hasattr(config, 'mcp') else None
        self._mcp_configs_dir = mcp_configs_dir
        self._servers: dict[str, Any] = {}  # server_name -> process or connection
        self._tools: dict[str, MCPTool] = {}  # full_tool_name -> MCPTool
        self._server_processes: dict[str, asyncio.subprocess.Process] = {}

    async def initialize(self) -> None:
        """Initialize all configured MCP servers.

        Loads MCP server configurations from the project's mcp_configs/
        directory (YAML files), then establishes connections to each
        configured server via the appropriate transport (HTTP or stdio).
        Discovered tools from each server are registered for later use.

        Args:
            No explicit args (uses self.config and project mcp_configs/).

        Returns:
            None. Server connections are stored in self._server_processes
            and tools in self._tools.

        Raises:
            RuntimeError: If a server has neither url nor command configured.
        """
        # Load MCP configs from mcp_configs/ directory
        project_root = Path(__file__).parent.parent.parent
        mcp_configs_path = project_root / "mcp_configs"

        if not hasattr(self.config, 'mcp') or not self.config.mcp:
            from beaver_agent.core.config import MCPConfig
            self.config.mcp = MCPConfig()

        if mcp_configs_path.exists() and mcp_configs_path.is_dir():
            self._load_configs_from_directory(mcp_configs_path)

        mcp_config = self.config.mcp
        if not mcp_config or not mcp_config.servers:
            logger.info("no_mcp_servers_configured")
            return

        for server_name, server_config in mcp_config.servers.items():
            try:
                await self._connect_server(server_name, server_config)
            except Exception as e:
                logger.error("mcp_server_connect_failed",
                           server=server_name, error=str(e))

    def _load_configs_from_directory(self, configs_path: Path) -> None:
        """Load all MCP server configs from a directory of YAML files"""
        import yaml

        for config_file in configs_path.glob("*.yaml"):
            try:
                server_name = config_file.stem  # filename without extension
                with open(config_file) as f:
                    server_data = yaml.safe_load(f) or {}

                server_config = MCPServerConfig(**server_data)
                self.config.mcp.servers[server_name] = server_config
                logger.debug("mcp_config_loaded", server=server_name, file=str(config_file))
            except Exception as e:
                logger.warning("mcp_config_load_failed",
                             file=str(config_file), error=str(e))

    async def _connect_server(self, server_name: str,
                             server_config: MCPServerConfig) -> None:
        """Connect to a single MCP server"""
        if server_config.url:
            await self._connect_http(server_name, server_config)
        elif server_config.command:
            await self._connect_stdio(server_name, server_config)
        else:
            raise ValueError(f"MCP server {server_name} must have either url or command")

    async def _connect_http(self, server_name: str,
                           server_config: MCPServerConfig) -> None:
        """Connect to an HTTP-based MCP server"""
        # HTTP transport implementation
        # For now, log that it's configured
        logger.info("mcp_http_server_configured",
                   server=server_name, url=server_config.url)

    async def _connect_stdio(self, server_name: str,
                            server_config: MCPServerConfig) -> None:
        """Connect to a stdio-based MCP server"""
        try:
            # Build environment (filtered baseline + user-specified)
            env = self._build_env(server_config.env)

            # Start the MCP server process
            process = await asyncio.create_subprocess_exec(
                server_config.command,
                *server_config.args,
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            self._server_processes[server_name] = process

            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "beaver-agent",
                        "version": "0.1.0"
                    }
                }
            }

            await self._send_request(server_name, init_request)
            response = await self._read_response(server_name)

            # Send initialized notification
            await self._send_notification(server_name, "notifications/initialized", {})

            # Discover tools
            await self._discover_tools(server_name)

            logger.info("mcp_stdio_server_connected", server=server_name)

        except Exception as e:
            logger.error("mcp_stdio_connect_failed",
                        server=server_name, error=str(e))
            raise

    def _build_env(self, user_env: dict) -> dict:
        """Build environment for subprocess - safe baseline + user vars"""
        import os
        baseline = {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", ""),
            "USER": os.environ.get("USER", ""),
            "LANG": os.environ.get("LANG", "en_US.UTF-8"),
            "LC_ALL": os.environ.get("LC_ALL", ""),
            "TERM": os.environ.get("TERM", "xterm-256color"),
            "SHELL": os.environ.get("SHELL", "/bin/bash"),
            "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
        }
        baseline.update(user_env)
        return baseline

    async def _send_request(self, server_name: str, request: dict) -> None:
        """Send a JSON-RPC request to the server"""
        process = self._server_processes.get(server_name)
        if not process:
            raise RuntimeError(f"Server {server_name} not connected")

        message = json.dumps(request) + "\n"
        process.stdin.write(message.encode())
        await process.stdin.drain()

    async def _send_notification(self, server_name: str,
                                method: str, params: dict) -> None:
        """Send a JSON-RPC notification (no id) to the server"""
        process = self._server_processes.get(server_name)
        if not process:
            raise RuntimeError(f"Server {server_name} not connected")

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        message = json.dumps(notification) + "\n"
        process.stdin.write(message.encode())
        await process.stdin.drain()

    async def _read_response(self, server_name: str) -> dict:
        """Read a JSON-RPC response from the server"""
        process = self._server_processes.get(server_name)
        if not process:
            raise RuntimeError(f"Server {server_name} not connected")

        line = await process.stdout.readline()
        if not line:
            raise RuntimeError(f"Server {server_name} disconnected")
        return json.loads(line.decode())

    async def _discover_tools(self, server_name: str) -> None:
        """Discover tools from a connected MCP server"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        await self._send_request(server_name, request)
        response = await self._read_response(server_name)

        tools = response.get("result", {}).get("tools", [])
        for tool in tools:
            tool_name = tool.get("name", "")
            # Normalize tool name for LLM compatibility
            normalized_name = re.sub(r"[^a-zA-Z0-9_]", "_", tool_name)
            full_name = f"mcp_{server_name}_{normalized_name}"

            mcp_tool = MCPTool(
                name=tool_name,
                server_name=server_name,
                description=tool.get("description", ""),
                input_schema=tool.get("inputSchema", {}),
                mcp_manager=self,
            )
            self._tools[full_name] = mcp_tool

            logger.debug("mcp_tool_discovered",
                        server=server_name,
                        tool=tool_name,
                        full_name=full_name)

        logger.info("mcp_tools_discovered",
                   server=server_name,
                   count=len(tools))

    async def call_tool(self, server_name: str,
                        tool_name: str, arguments: dict) -> dict:
        """Call a tool on an MCP server"""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        await self._send_request(server_name, request)
        response = await self._read_response(server_name)

        if "error" in response:
            return {"success": False, "error": response["error"]}

        return {"success": True, "result": response.get("result", {})}

    def get_tools(self) -> list[dict]:
        """Return all available MCP tools as dicts"""
        return [tool.to_dict() for tool in self._tools.values()]

    def get_tool(self, full_name: str) -> Optional[MCPTool]:
        """Get a specific MCP tool by full name"""
        return self._tools.get(full_name)

    async def shutdown(self) -> None:
        """Shutdown all MCP server connections"""
        for server_name, process in self._server_processes.items():
            try:
                process.terminate()
                await process.wait()
                logger.debug("mcp_server_stopped", server=server_name)
            except Exception as e:
                logger.error("mcp_server_stop_failed",
                           server=server_name, error=str(e))

        self._server_processes.clear()
        self._tools.clear()
