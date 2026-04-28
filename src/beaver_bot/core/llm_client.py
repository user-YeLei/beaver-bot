"""Beaver Bot LLM Client - Unified interface for OpenRouter/Claude/OpenAI"""

import os
from typing import Optional, List, Dict, Any, Union

import structlog

from beaver_bot.core.config import ModelConfig

logger = structlog.get_logger()


class LLMResponse:
    """LLM response wrapper"""

    def __init__(self, content: str, model: str, usage: Optional[Dict] = None):
        self.content = content
        self.model = model
        self.usage = usage or {}


class LLMClient:
    """Unified LLM client supporting OpenRouter, Anthropic, OpenAI"""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.provider = config.provider
        self.model = config.name
        self.api_key = config.api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.api_base = config.api_base

        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the appropriate client based on provider"""
        try:
            if self.provider == "anthropic" or "claude" in self.model.lower():
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
                self._call = self._call_anthropic
            elif self.provider == "openai" or "gpt" in self.model.lower():
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
                self._call = self._call_openai
            elif self.provider == "openrouter":
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.openrouter.ai/api/v1"
                )
                self._call = self._call_openai
            elif self.provider == "minimax":
                self._call = self._call_minimax
            else:
                # Default to OpenRouter
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.openrouter.ai/api/v1"
                )
                self._call = self._call_openai

            logger.info("llm_client_initialized", provider=self.provider, model=self.model)

        except ImportError as e:
            logger.error("llm_client_import_failed", error=str(e))
            self._call = self._call_fallback

    def _call_anthropic(self, messages: List[Dict], **kwargs) -> LLMResponse:
        """Call Anthropic Claude"""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
            messages=messages
        )
        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            usage={"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
        )

    def _call_openai(self, messages: List[Dict], **kwargs) -> LLMResponse:
        """Call OpenAI / OpenRouter"""
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
            messages=messages
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            usage={"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens}
        )

    def _call_minimax(self, messages: List[Dict], **kwargs) -> LLMResponse:
        """Call MiniMax API (Anthropic-compatible /messages endpoint)"""
        base_url = self.api_base or "https://api.minimaxi.com/anthropic/v1/messages"

        import httpx

        with httpx.Client(base_url=base_url.rstrip("/"), timeout=60.0, follow_redirects=True) as client:
            response = client.post(
                "",
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": kwargs.get("max_tokens", 4096),
                    "temperature": kwargs.get("temperature", 0.7),
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

            content = data.get("content", [])
            if isinstance(content, list) and len(content) > 0:
                text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                text = "\n".join(text_parts) if text_parts else str(content)
            else:
                text = str(content)

            return LLMResponse(
                content=text,
                model=self.model,
                usage={
                    "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                    "output_tokens": data.get("usage", {}).get("output_tokens", 0),
                },
            )

    def _call_fallback(self, messages: List[Dict], **kwargs) -> LLMResponse:
        """Fallback when no API key is available"""
        return LLMResponse(
            content="LLM API key not configured. Please set OPENROUTER_API_KEY or ANTHROPIC_API_KEY",
            model="none"
        )

    def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        context: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """Simple chat interface"""

        messages = []

        # Add system prompt
        if system:
            messages.append({"role": "system", "content": system})

        # Add conversation context
        if context:
            for msg in context:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

        # Add user prompt
        messages.append({"role": "user", "content": prompt})

        return self._call(messages, **kwargs)

    def generate_code(
        self,
        description: str,
        language: str = "python",
        context: Optional[str] = None
    ) -> LLMResponse:
        """Generate code from description"""

        system = f"""You are Beaver Bot, an expert coding assistant.
Generate clean, well-documented code based on the user's request.
Always wrap code blocks with triple backticks and specify the language.
If you need more context, ask clarifying questions."""

        prompt = f"Write {language} code for the following:\n\n{description}"

        if context:
            prompt = f"Context:\n{context}\n\n---\n\n{prompt}"

        return self.chat(prompt, system=system)

    def review_code(
        self,
        code: str,
        language: str = "python",
        file_path: Optional[str] = None
    ) -> LLMResponse:
        """Review code and provide suggestions"""

        system = """You are Beaver Bot, an expert code reviewer.
Analyze the code and provide:
1. Potential bugs or issues
2. Code quality improvements
3. Security concerns
4. Performance optimizations

Format your review with clear sections and line numbers if provided."""

        file_info = f"\n\nFile: {file_path}" if file_path else ""
        prompt = f"Review the following {language} code:{file_info}\n\n```{language}\n{code}\n```"

        return self.chat(prompt, system=system)

    def debug_code(
        self,
        code: str,
        error: str,
        language: str = "python"
    ) -> LLMResponse:
        """Debug code with error message"""

        system = """You are Beaver Bot, an expert debugging assistant.
Analyze the error and provide:
1. Root cause analysis
2. The exact fix
3. Prevention tips

Always provide the corrected code if applicable."""

        prompt = f"""Debug the following {language} code that produced this error:

Error:
```
{error}
```

Code:
```{language}
{code}
```"""

        return self.chat(prompt, system=system)

    def explain_code(self, code: str, language: str = "python") -> LLMResponse:
        """Explain what code does"""

        system = """You are Beaver Bot, an expert programming tutor.
Explain code clearly, breaking down complex parts.
Use simple language and provide examples where helpful."""

        prompt = f"Explain the following {language} code:\n\n```{language}\n{code}\n```"

        return self.chat(prompt, system=system)
