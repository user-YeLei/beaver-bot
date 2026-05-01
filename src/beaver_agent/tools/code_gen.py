"""Beaver Agent Code Generation Tool"""

from typing import Optional, Dict, Any

import structlog

logger = structlog.get_logger()


class CodeGenTool:
    """Tool for generating code using LLM"""

    def __init__(self, config, llm_client):
        self.config = config
        self.llm = llm_client

    def generate(
        self,
        description: str,
        language: str = "python",
        file_path: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """Generate code based on description"""

        logger.info("generating_code", language=language, description=description[:50])

        try:
            response = self.llm.generate_code(
                description=description,
                language=language,
                context=context
            )

            if not response.content or "not configured" in response.content:
                return self._generate_skeleton(description, language)

            # If file_path provided, offer to save
            if file_path:
                from beaver_agent.tools.file_tool import FileTool
                file_tool = FileTool(self.config)
                save_result = file_tool.write_file(file_path, response.content)
                return f"{response.content}\n\n---\n{save_result}"

            return response.content

        except Exception as e:
            logger.error("code_generation_failed", error=str(e))
            return f"❌ Code generation failed: {e}"

    def _generate_skeleton(self, description: str, language: str) -> str:
        """Generate code skeleton without LLM"""

        templates = {
            "python": f'''# Python Code for: {description}

# This is a placeholder - configure LLM API key for full generation
# Set OPENROUTER_API_KEY or ANTHROPIC_API_KEY in config

def main():
    """Main entry point"""
    pass

if __name__ == "__main__":
    main()
''',
            "javascript": f'''// JavaScript/Node.js for: {description}

// This is a placeholder - configure LLM API key for full generation

function main() {{
    // Your implementation here
}}

module.exports = {{ main }};
''',
            "go": f'''// Go code for: {description}

// This is a placeholder - configure LLM API key for full generation

package main

func main() {{
    // Your implementation here
}}
''',
        }

        return templates.get(language, f"// Code for: {description}\n// Configure LLM API key for full generation")

    def complete_code(
        self,
        partial_code: str,
        description: str,
        language: str = "python"
    ) -> str:
        """Complete partial code using LLM to fill in TODO sections."""
        logger.info("completing_code", language=language, description=description[:50])

        prompt_text = f"""Complete the following {language} code.
Fill in the TODO sections and complete any unfinished functions.

Description: {description}

```{language}
{partial_code}
```"""

        try:
            response = self.llm.chat(prompt_text)
            return response.content
        except Exception as e:
            logger.error("code_completion_failed", error=str(e))
            return f"❌ Code completion failed: {e}"

    def refactor(
        self,
        code: str,
        style: str = "clean",
        language: str = "python"
    ) -> str:
        """Refactor code to follow best practices using LLM."""
        logger.info("refactoring_code", language=language, style=style)

        prompt = f"""Refactor the following {language} code to be more {style}.

```{language}
{code}
```"""

        try:
            response = self.llm.chat(prompt)
            return response.content
        except Exception as e:
            logger.error("code_refactor_failed", error=str(e))
            return f"❌ Refactoring failed: {e}"
