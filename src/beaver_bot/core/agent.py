"""Beaver Bot Agent Core v2 - With LLM Integration"""

import uuid
from typing import Optional, Dict, Any, List

import structlog

from beaver_bot.core.config import BeaverConfig
from beaver_bot.core.llm_client import LLMClient
from beaver_bot.core.intent_parser import IntentParser
from beaver_bot.core.task_planner import TaskPlanner
from beaver_bot.core.tool_router import ToolRouter
from beaver_bot.core.memory.session import SessionMemory
from beaver_bot.core.conversation_logger import ConversationLogger
from beaver_bot.core.data_store import init_data_store

logger = structlog.get_logger()


class BeaverAgent:
    """Beaver Bot Agent - Main orchestration class with LLM"""

    def __init__(self, config: BeaverConfig):
        self.config = config
        
        # Initialize data store and run migrations BEFORE other init
        try:
            self.data_store = init_data_store()
            logger.info("data_store_initialized", 
                       version=self.data_store.get_version().raw,
                       stats=self.data_store.get_stats())
        except Exception as e:
            logger.error("data_store_init_failed", error=str(e))
            raise
        
        self.session_id = str(uuid.uuid4())[:8]
        self.memory = SessionMemory()
        self.intent_parser = IntentParser()
        self.task_planner = TaskPlanner()
        self.tool_router = ToolRouter(config)
        self.conversation_history: List[Dict[str, str]] = []
        self.logger = ConversationLogger()

        # Initialize LLM
        try:
            self.llm = self.tool_router.get_llm_client()
        except Exception as e:
            logger.warning("llm_init_failed", error=str(e))
            self.llm = None

        # Start conversation logging
        self.logger.start_session(self.session_id)

        logger.info("agent_initialized", session_id=self.session_id, model=config.model.name)

    def run(self, user_input: str) -> str:
        """Main agent loop: parse intent → plan tasks → execute tools → return response"""

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

        return response

    def _generate_response(
        self,
        user_input: str,
        intent: str,
        tool_results: List[Dict[str, Any]]
    ) -> str:
        """Generate final response using LLM with tool results"""

        context = self._build_context(tool_results)

        if not self.llm:
            return self._generate_fallback_response(intent, context)

        # Build conversation context for LLM
        messages = []

        # System prompt
        system = """You are Beaver Bot, an expert AI coding assistant.
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
            logger.error("llm_response_failed", error=str(e))

            # Log error
            self.logger.log_llm_response(
                content="",
                model=self.llm.model if self.llm else "unknown",
                error=str(e),
            )

            return self._generate_fallback_response(intent, context)

    def _build_context(self, tool_results: List[Dict[str, Any]]) -> str:
        """Build context string from tool results"""
        if not tool_results:
            return ""

        lines = []
        for result in tool_results:
            tool_name = result.get("tool", "unknown")
            success = result.get("success", False)
            data = result.get("data", "")
            error = result.get("error", "")

            status = "✅" if success else "❌"
            if success:
                lines.append(f"{status} [{tool_name}]\n{data}")
            else:
                lines.append(f"{status} [{tool_name}] Error: {error}")

        return "\n\n".join(lines)

    def _generate_fallback_response(self, intent: str, context: str) -> str:
        """Generate response without LLM (fallback mode)"""

        if intent == "code_generation":
            return f"""## 💻 代码生成

**状态**: 工具已执行

{context}

---

💡 如需完整 AI 代码生成能力，请配置:
- `OPENROUTER_API_KEY` 或 `ANTHROPIC_API_KEY`
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

你好！我是 Beaver Bot 🦫

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
        """Reset agent state"""
        self.logger.end_session()
        self.conversation_history.clear()
        self.memory.clear()
        self.session_id = str(uuid.uuid4())[:8]
        self.logger.start_session(self.session_id)
        logger.info("agent_reset", new_session_id=self.session_id)

    def shutdown(self) -> None:
        """Shutdown agent and close log files"""
        self.logger.end_session()
        logger.info("agent_shutdown", session_id=self.session_id)
