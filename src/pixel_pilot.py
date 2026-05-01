"""
PixelPilot - 一行代码接入 beaver-agent 可视化观测

使用方式：

    import pixel_pilot

    # 初始化（推荐在 agent 初始化时调用一次）
    pixel_pilot.connect("http://localhost:7777")

    # 现在所有 tool_router.route() 调用都会自动发送到 PixelPilot
    # 无需修改任何现有代码

    # 也可以手动发送事件
    pixel_pilot.send("thinking", message="分析需求...")
    pixel_pilot.send("done", message="任务完成")

环境变量（自动连接）：

    export PIXEL_VIEWER_URL=http://localhost:7777
    python your_agent.py  # 自动连接
"""

import os
import sys
import json
import time
import uuid
import functools
from datetime import datetime
from threading import Lock
from urllib import request, error
from typing import Optional, Dict, Any

try:
    import structlog
    _has_structlog = True
except ImportError:
    _has_structlog = False

# 全局状态
_enabled = False
_viewer_url = "http://localhost:7777"
_initialized = False
_lock = Lock()

# PixelPilot logger — only active if structlog is available
if _has_structlog:
    _logger = structlog.get_logger("pixel_pilot")

# 工具名映射（tool_name + action -> 人类可读名称）
TOOL_ACTION_MAP = {
    ("file_tool", "read_file"): "Read",
    ("file_tool", "write_file"): "Write",
    ("file_tool", "search_files"): "Find",
    ("file_tool", "search_content"): "Search",
    ("file_tool", "list_directory"): "List",
    ("file_tool", "check_project_structure"): "Check",
    ("terminal_tool", "run_command"): "Bash",
    ("terminal_tool", "run_terminal_command"): "Bash",
    ("terminal_tool", "run"): "Bash",
    ("github_tool", "*"): "GitHub",
    ("code_gen", "*"): "CodeGen",
    ("code_review", "*"): "Review",
    ("debugger", "*"): "Debug",
    ("browser_tool", "*"): "Browser",
}


def connect(url: str = "http://localhost:7777", verbose: bool = True) -> None:
    """
    连接 PixelPilot 服务器，启用自动事件追踪。

    只需调用一次，之后所有 ToolRouter.route() 会自动发送事件。

    Args:
        url: PixelPilot 服务器地址
        verbose: 是否打印连接状态
    """
    global _enabled, _viewer_url, _initialized

    _viewer_url = url.rstrip("/")

    if verbose:
        if _has_structlog:
            _logger.info("connecting", url=_viewer_url)
        else:
            print(f"[PixelPilot] Connecting to {_viewer_url}...")

    # 测试连接
    if _test_connection():
        _enabled = True
        _initialized = True
        _patch_tool_router()
        if verbose:
            if _has_structlog:
                _logger.info("connected", url=_viewer_url)
            else:
                print(f"[PixelPilot] ✅ Connected! Events will be streamed automatically.")
    else:
        if verbose:
            if _has_structlog:
                _logger.warning("server_not_reachable", url=_viewer_url)
            else:
                print(f"[PixelPilot] ⚠️  Server not reachable, events will be queued locally.")


def disconnect() -> None:
    """断开连接，停止事件追踪"""
    global _enabled
    _enabled = False
    if _has_structlog:
        _logger.info("disconnected")
    else:
        print("[PixelPilot] Disconnected.")


def send(
    event_type: str,
    message: str = "",
    agent: str = "beaver",
    tool: Optional[str] = None,
    file: Optional[str] = None,
    status: str = "active",
) -> bool:
    """
    手动发送一个事件到 PixelPilot。

    Args:
        event_type: 事件类型 (request/thinking/tool/tool_done/done/agent/system)
        message: 显示消息
        agent: Agent 名称
        tool: 工具名称
        file: 相关文件
        status: 状态 (active/idle/error)

    Returns:
        发送是否成功
    """
    event = {
        "type": event_type,
        "agent": agent,
        "message": message,
        "tool": tool,
        "file": file,
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }

    return _post_event(event)


def is_enabled() -> bool:
    """检查是否已连接"""
    return _enabled


def _test_connection() -> bool:
    """测试服务器连接"""
    try:
        req = request.Request(
            f"{_viewer_url}/status",
            method="GET",
        )
        with request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def _post_event(event: Dict[str, Any]) -> bool:
    """发送事件到服务器"""
    if not _viewer_url:
        return False

    try:
        req = request.Request(
            f"{_viewer_url}/event",
            data=json.dumps(event).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except error.URLError:
        return False
    except Exception:
        return False


def _get_agent_name(self) -> str:
    """从 ToolRouter 的 config 中获取 agent 名称"""
    try:
        app = getattr(getattr(self, "config", None), "app", None)
        return getattr(app, "name", "beaver") if app else "beaver"
    except Exception:
        return "beaver"


def _get_tool_display_name(tool_name: str, action: str = "") -> str:
    """获取工具的显示名称"""
    # 先尝试精确匹配 (tool_name, action)
    key = (tool_name, action)
    if key in TOOL_ACTION_MAP:
        return TOOL_ACTION_MAP[key]
    # 再尝试通配符 (tool_name, "*")
    wildcard = (tool_name, "*")
    if wildcard in TOOL_ACTION_MAP:
        return TOOL_ACTION_MAP[wildcard]
    # 最后用默认转换
    if action:
        return action.replace("_", " ").title()
    return tool_name.replace("_", " ").title()


def _patch_tool_router() -> None:
    """
    动态注入 ToolRouter.route() 方法，自动追踪所有工具调用。
    这是一个猴子补丁，但非常轻量且完全向后兼容。
    """
    try:
        from beaver_agent.core.tool_router import ToolRouter

        # 避免重复注入
        if hasattr(ToolRouter, "_pixel_patched"):
            return

        original_route = ToolRouter.route
        original_route_batch = getattr(ToolRouter, "route_batch", None)

        @functools.wraps(original_route)
        def patched_route(self, task: Dict[str, Any]) -> Dict[str, Any]:
            tool_name = task.get("tool", "unknown")
            action = task.get("action", "")
            params = task.get("params", {})
            file = params.get("file_path") or params.get("path") or ""

            # 获取 agent 名称（从 config 中读取，支持多 agent）
            agent_name = _get_agent_name(self)

            # 发送 tool 事件（工具开始）
            if _enabled:
                _post_event({
                    "type": "tool",
                    "agent": agent_name,
                    "tool": _get_tool_display_name(tool_name, action),
                    "action": action,
                    "file": str(file) if file else "",
                    "message": f"{_get_tool_display_name(tool_name, action)}: {action}",
                    "status": "active",
                    "timestamp": datetime.now().isoformat(),
                })

            # 调用原始方法
            result = original_route(self, task)

            # 发送 tool_done 事件（工具完成）
            if _enabled:
                success = result.get("success", False)
                _post_event({
                    "type": "tool_done" if success else "error",
                    "agent": agent_name,
                    "tool": _get_tool_display_name(tool_name, action),
                    "action": action,
                    "file": str(file) if file else "",
                    "message": f"{_get_tool_display_name(tool_name, action)}: {action} "
                               + ("✅" if success else "❌"),
                    "status": "idle" if success else "error",
                    "timestamp": datetime.now().isoformat(),
                })

            return result

        # 如果有 route_batch 也一并注入
        if original_route_batch:
            @functools.wraps(original_route_batch)
            def patched_route_batch(self, tasks):
                for task in tasks:
                    patched_route(self, task)
                return [patched_route(self, t) for t in tasks]

            ToolRouter.route_batch = patched_route_batch

        ToolRouter.route = patched_route
        ToolRouter._pixel_patched = True

        if _enabled:
            if _has_structlog:
                _logger.info("toolrouter_patched")
            else:
                print("[PixelPilot] 🔌 ToolRouter patched - all tool calls will be tracked")

    except ImportError as e:
        if _has_structlog:
            _logger.warning("could_not_patch_toolrouter", error=str(e))
        else:
            print(f"[PixelPilot] Warning: Could not patch ToolRouter: {e}")
    except Exception as e:
        if _has_structlog:
            _logger.warning("patching_failed", error=str(e))
        else:
            print(f"[PixelPilot] Warning: Patching failed: {e}")
