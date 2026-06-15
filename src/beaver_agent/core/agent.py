"""Beaver Agent Core - LLM-integrated agent orchestration."""

import re
import uuid
from io import StringIO
from typing import Any

import structlog
from rich.console import Console
from rich.table import Table

from beaver_agent.core.config import BeaverConfig
from beaver_agent.core.conversation_logger import ConversationLogger
from beaver_agent.core.data_store import init_data_store
from beaver_agent.core.intent_parser import IntentParser
from beaver_agent.core.memory.long_term import LongTermMemory
from beaver_agent.core.memory.session import SessionMemory
from beaver_agent.core.task_planner import TaskPlanner
from beaver_agent.core.tool_router import ToolRouter

logger = structlog.get_logger()

__all__ = ["BeaverAgent"]


class BeaverAgent:
    """Beaver Agent - Main orchestration class with LLM"""

    def __init__(self, config: BeaverConfig) -> None:
        """Initialize the BeaverAgent with configuration.

        Args:
            config: BeaverConfig containing model, tools, and app settings.

        Raises:
            Exception: Re-raises data store initialization failures after logging.
        """
        self.config = config

        # Initialize data store and run migrations BEFORE other init
        try:
            self.data_store = init_data_store()
            logger.info(
                "data_store_initialized",
                version=self.data_store.get_version().raw,
                stats=self.data_store.get_stats(),
            )
        except Exception as e:
            logger.error("data_store_init_failed", exc_info=e)
            raise

        self.session_id = str(uuid.uuid4())[:8]
        self.memory = SessionMemory()
        self.long_term_memory = LongTermMemory(self.data_store.data_dir / "memory")
        self.intent_parser = IntentParser()
        self.task_planner = TaskPlanner()
        self.tool_router = ToolRouter(config)
        self.conversation_history: list[dict[str, str]] = []
        self.logger = ConversationLogger()

        # Initialize LLM
        try:
            self.llm = self.tool_router.get_llm_client()
        except Exception as e:
            logger.warning("llm_init_failed", exc_info=e)
            self.llm = None

        # Start conversation logging
        self.logger.start_session(self.session_id)

        logger.info("agent_initialized", session_id=self.session_id, model=config.model.name)

    def run(self, user_input: str) -> str:
        """Main agent loop: parse intent → plan tasks → execute tools → return response.

        Args:
            user_input: The user's input string (truncated to 100 chars for logging).

        Returns:
            The agent's response string, or an error message if processing failed.

        Raises:
            No exceptions are raised — all errors are caught and returned as error strings.
        """
        try:
            logger.info("processing_request", input=user_input[:100])

            # Add user message to history
            self.conversation_history.append({"role": "user", "content": user_input})

            # Log user input
            self.logger.log_user_input(user_input, intent=None)

            # Step 1: Parse intent
            intent = self.intent_parser.parse(user_input)
            logger.debug("intent_parsed", intent=intent)

            # Step 2: Plan tasks
            tasks = self.task_planner.plan(user_input, intent)
            logger.debug("tasks_planned", task_count=len(tasks))

            # Step 3: Execute tools and collect results
            tool_results = []
            for task in tasks:
                result = self.tool_router.route(task)
                tool_results.append(result)

                # Log tool call
                self.logger.log_tool_call(
                    tool_name=task.get("tool", "unknown"),
                    action=task.get("action", ""),
                    params=task.get("params", {}),
                    result=result,
                    success=result.get("success", False),
                )

            # Step 4: Generate response using LLM
            response = self._generate_response(user_input, intent, tool_results)

            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": response})

            # Auto-extract and store important information from this exchange
            self._extract_and_store_memory(user_input, response, tool_results)

            return response

        except Exception as e:
            logger.error("agent_run_failed", exc_info=e, input=user_input[:100])
            return f"❌ An unexpected error occurred: {e}"

    def _extract_and_store_memory(
        self,
        user_input: str,
        response: str,
        tool_results: list[dict[str, Any]],
    ) -> None:
        """Automatically extract and store important information in long-term memory.

        Scans the conversation for:
        - User preferences (language, communication style)
        - Project conventions and facts
        - Problem-solution pairs from successful tool executions
        - Tool usage patterns

        Args:
            user_input: The user's input message.
            response: The agent's response.
            tool_results: Results from tool executions.
        """
        # Pattern-based extraction for common cases

        # 1. User language/preference patterns
        chinese_patterns = [
            r"用中文",
            r"中文沟通",
            r"说话.*中文",
            r"回复.*中文",
        ]
        for pattern in chinese_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                self.long_term_memory.remember_user_preference(
                    "User prefers Chinese communication",
                    session_id=self.session_id,
                )
                break

        # 2. Project facts from tool results
        # Extract successful file operations to learn project structure
        for result in tool_results:
            if not result.get("success"):
                continue

            tool_name = result.get("tool", "")
            data = result.get("data", "")

            # Learn from code analyzer
            if tool_name in ("code_analyzer", "analyze") and isinstance(data, str):
                # Extract module/path information
                if "src/" in data or "tests/" in data:
                    self.long_term_memory.remember_project_fact(
                        f"Project has code at: {data[:200]}",
                        tags=["project", "structure"],
                        session_id=self.session_id,
                    )

            # Learn from git operations
            if tool_name in ("git", "github") and isinstance(data, str):
                if "branch" in data.lower() or "commit" in data.lower():
                    self.long_term_memory.remember_convention(
                        f"Git operation result: {data[:150]}",
                        context="learned from tool execution",
                        session_id=self.session_id,
                    )

        # 3. Problem-solution: successful bug fixes
        if "error" in user_input.lower() or "bug" in user_input.lower():
            for result in tool_results:
                if result.get("success") and result.get("data"):
                    self.long_term_memory.remember_solution(
                        problem=user_input[:200],
                        solution=f"Tool: {result.get('tool')}, Result: {str(result.get('data'))[:200]}",
                        tags=["bugfix", "problem"],
                        session_id=self.session_id,
                    )
                    break

        logger.debug(
            "memory_auto_extracted",
            session_id=self.session_id,
            user_input_preview=user_input[:50],
        )

    def _generate_response(
        self, user_input: str, intent: str, tool_results: list[dict[str, Any]]
    ) -> str:
        """Generate final response using LLM with tool results.

        Args:
            user_input: The original user input string.
            intent: The parsed intent from IntentParser (e.g., 'code_generation').
            tool_results: List of tool execution results to include in context.

        Returns:
            The LLM-generated response string, or a fallback response if LLM is unavailable.

        Raises:
            No exceptions are raised — all errors are caught and returned as error strings.
        """

        context = self._build_context(tool_results)

        if not self.llm:
            logger.debug("llm_unavailable_using_fallback", intent=intent)
            return self._generate_fallback_response(intent, context)

        # Build conversation context for LLM
        messages = []

        # System prompt
        system = """You are Beaver Agent, an expert AI coding assistant.
You help users with:
- Writing and generating code
- Code review and quality analysis
- Debugging and error fixing
- GitHub operations

Be concise, helpful, and technical.
Always provide actionable suggestions."""

        messages.append({"role": "system", "content": system})

        # Add conversation history (last 10 messages)
        for msg in self.conversation_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add long-term memory context
        memory_context = self.long_term_memory.get_context_for_prompt(
            query=user_input,  # Search relevant memories based on current input
            limit=5,
        )
        if memory_context:
            messages.append({"role": "system", "content": memory_context})

        # Add current context
        if context:
            context_msg = f"Here are the results of tools executed:\n{context}\n\nUser's latest request: {user_input}"
            messages.append({"role": "system", "content": context_msg})

        # Log LLM request
        self.logger.log_llm_request(
            messages=messages,
            model=self.llm.model if self.llm else "unknown",
            provider=self.llm.provider if self.llm else "unknown",
        )

        try:
            response = self.llm._call(messages, max_tokens=2048)

            # Log LLM response
            self.logger.log_llm_response(
                content=response.content,
                model=response.model,
                usage=response.usage,
            )

            return response.content
        except Exception as e:
            logger.error("llm_response_failed", exc_info=e)

            # Log error
            self.logger.log_llm_response(
                content="",
                model=self.llm.model if self.llm else "unknown",
                error=str(e),
            )

            return self._generate_fallback_response(intent, context)

    def _build_context(self, tool_results: list[dict[str, Any]]) -> str:
        """Build context string from tool results — tool-specific summarization.

        Args:
            tool_results: List of tool execution result dicts, each containing
                'tool', 'success', 'data', and 'error' keys.

        Returns:
            A formatted string table of tool results, with each tool's output
            summarized based on its type. Returns empty string if no results.
        """
        if not tool_results:
            return ""

        table = Table(
            title="🔧 工具执行结果",
            show_header=True,
            header_style="bold cyan",
            border_style="cyan",
            box=None,
            padding=(0, 1),
        )
        table.add_column("状态", justify="center", style="green", no_wrap=True)
        table.add_column("工具", style="bold")
        table.add_column("结果", style="white")

        for result in tool_results:
            tool_name = result.get("tool", "unknown")
            success = result.get("success", False)
            data = result.get("data", "")
            error = result.get("error", "")

            status = "[green]✓[/green]" if success else "[red]✗[/red]"
            content = data if success else f"[red]{error}[/red]"

            # Tool-specific summarization
            content = self._summarize_content(tool_name, content)

            table.add_row(status, tool_name, content)

        # Render table to string
        buf = StringIO()
        tmp_console = Console(file=buf, force_terminal=True)
        tmp_console.print(table)
        return buf.getvalue()

    def _summarize_content(self, tool: str, content: str) -> str:
        """Summarize long tool output based on tool type — no truncation, highlight key info.

        Args:
            tool: Tool name (e.g., 'read_file', 'terminal', 'search', 'mcp').
            content: Raw string output from the tool execution.

        Returns:
            A summarized string with key information highlighted. For short
            outputs (<24 lines for files, <35 for terminal), returns the
            original content unchanged.
        """
        if not isinstance(content, str):
            content = str(content)

        # For file read: show first 20 lines + file stats
        if tool in ("read_file", "Read"):
            lines = content.strip().split("\n")
            if len(lines) > 24:
                total = len(lines)
                preview = "\n".join(lines[:20])
                # Extract key info from first lines
                first_lines = lines[:5]
                stats = ""
                for fl in first_lines:
                    if "total lines" in fl.lower() or "file" in fl.lower():
                        stats += f" | {fl.strip()}"
                return (
                    f"{preview}\n"
                    f"[dim]... ({total - 20} more lines){stats}[/dim]\n\n"
                    "[cyan]📄 文件预览 (前 20 行)[/cyan]"
                )
            return content

        # For terminal output: show last 30 lines (usually the important part)
        if tool in ("terminal", "exec", "bash", "run_command"):
            lines = content.strip().split("\n")
            if len(lines) > 35:
                # Try to find error/warning patterns
                error_lines = [
                    line
                    for line in lines
                    if any(
                        k in line.lower()
                        for k in ("error", "fail", "exception", "traceback", "warning", "warn")
                    )
                ]
                if error_lines:
                    # Show last 15 normal + all error lines
                    last_normal = lines[-20:] if len(lines) > 20 else lines
                    errors = "\n".join(error_lines[:10])
                    return (
                        f"{chr(10).join(last_normal[:15])}\n\n"
                        f"[red]⚠️ 发现问题 ({len(error_lines)} 处):[/red]\n{errors}"
                    )
                return f"{chr(10).join(lines[-30:])}\n\n[dim]↑ 前 {len(lines) - 30} 行...[/dim]"
            return content

        # For search results: show top matches with context
        if tool in ("search", "grep", "SearchFiles"):
            lines = content.strip().split("\n")
            if len(lines) > 20:
                # Show first 10 + count summary
                return f"{chr(10).join(lines[:10])}\n\n[dim]... 共 {len(lines)} 条匹配结果[/dim]"
            return content

        # For JSON data: pretty-print with syntax highlight
        if tool in ("mcp", "API", "http", "fetch"):
            import json

            try:
                parsed = json.loads(content)
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                if len(formatted) > 2000:
                    # Show structure summary + first 50 lines
                    lines = formatted.split("\n")
                    return (
                        f"{chr(10).join(lines[:50])}\n\n"
                        f"[dim]JSON 结构: {self._json_summary(parsed)}[/dim]"
                    )
                return formatted
            except (json.JSONDecodeError, TypeError):
                pass

        # For git/status: keep last 20 lines
        if tool in ("git", "git_status", "git_log"):
            lines = content.strip().split("\n")
            if len(lines) > 25:
                return f"{chr(10).join(lines[-20:])}\n\n[dim]↑ 前 {len(lines) - 20} 行...[/dim]"
            return content

        # Default: if really long, show structure summary
        if len(content) > 3000:
            lines = content.strip().split("\n")
            return (
                f"{chr(10).join(lines[:30])}\n\n"
                f"[dim]...(共 {len(lines)} 行, 约 {len(content)} 字符)[/dim]"
            )

        return content

    def _json_summary(self, obj: Any, depth: int = 0) -> str:
        """Build a one-line summary of JSON structure.

        Args:
            obj: The object to summarize (dict, list, str, or other).
            depth: Current recursion depth (used internally, max 3).

        Returns:
            A compact one-line string describing the object structure.
            - dicts show up to 5 keys with their value types and a (+N keys) suffix
            - lists show item count
            - strings show first 20 characters
            - other types show repr() truncated to 30 chars
        """
        if depth > 3:
            return "..."
        if isinstance(obj, dict):
            keys = list(obj.keys())[:5]
            summary = ", ".join(f"{k}={self._json_summary(obj[k], depth + 1)}" for k in keys)
            suffix = f" (+{len(obj) - 5} keys)" if len(obj) > 5 else ""
            return f"{{{summary}{suffix}}}"
        elif isinstance(obj, list):
            return f"[{len(obj)} items]"
        elif isinstance(obj, str):
            return f'"{obj[:20]}{"..." if len(obj) > 20 else ""}"'
        return repr(obj)[:30]

    def _generate_fallback_response(self, intent: str, context: str) -> str:
        """Generate response without LLM (fallback mode).

        Args:
            intent: The parsed intent (e.g., 'code_generation', 'code_review').
            context: The tool execution results formatted as a context string.

        Returns:
            A human-readable response string explaining what the agent would do
            if the LLM were configured, including a brief guide for enabling
            AI capabilities.
        """

        if intent == "code_generation":
            return f"""## 💻 代码生成

**状态**: 工具已执行

{context}

---

💡 如需完整 AI 代码生成能力，请配置:
- `MINIMAX_API_KEY`
"""

        elif intent == "code_review":
            return f"""## 🔍 代码审查

**状态**: 审查完成

{context}

---

💡 配置 LLM API key 可获取深度 AI 代码分析。
"""

        elif intent == "debug":
            return f"""## 🐛 调试分析

**状态**: 分析完成

{context}

---

💡 配置 LLM API key 可获取详细错误根因分析。
"""

        elif intent == "github_operation":
            return f"""## 🐙 GitHub 操作

{context}
"""

        else:
            return f"""## 💬 对话

你好！我是 Beaver Agent 🦫

**上次操作结果**:
{context or "暂无"}

---

目前我可以帮你：
- 💻 写代码（描述你想要的功能）
- 🔍 审查代码（分析问题、优化建议）
- 🐛 调试问题（错误分析）
- 🐙 GitHub 操作（仓库、Issue、PR）

输入 [green]/help[/green] 查看更多命令。
"""

    def reset(self) -> None:
        """Reset agent state for a new conversation session.

        Clears the conversation history, memory, and session logger, then
        starts a fresh session with a new session ID. Used to begin a new
        task or conversation context.

        Args:
            None

        Returns:
            None. Internal state is mutated in place.
        """
        self.logger.end_session()
        self.conversation_history.clear()
        self.memory.clear()
        self.session_id = str(uuid.uuid4())[:8]
        self.logger.start_session(self.session_id)
        logger.info("agent_reset", new_session_id=self.session_id)

    def shutdown(self) -> None:
        """Shutdown the agent and release all resources.

        Ends the current logging session and closes any open file handles
        or connections. After shutdown, the agent should not be used without
        re-initialization.

        Args:
            None

        Returns:
            None. Resources are released in place.
        """
        self.logger.end_session()
        logger.info("agent_shutdown", session_id=self.session_id)
