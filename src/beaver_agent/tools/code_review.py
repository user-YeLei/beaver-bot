"""Beaver Agent Code Review Tool"""

from typing import Optional, List, Dict, Any

import structlog

logger = structlog.get_logger()


class CodeReviewIssue:
    """Represents a code review issue"""

    def __init__(
        self,
        severity: str,  # critical, major, minor, suggestion
        line: Optional[int],
        message: str,
        suggestion: Optional[str] = None
    ):
        self.severity = severity
        self.line = line
        self.message = message
        self.suggestion = suggestion

    def format(self) -> str:
        """Format issue as string"""
        emoji = {
            "critical": "🔴",
            "major": "🟠",
            "minor": "🟡",
            "suggestion": "💡"
        }.get(self.severity, "⚪")

        line_info = f" Line {self.line}:" if self.line else ""
        result = f"{emoji} [{self.severity.upper()}] {line_info} {self.message}"

        if self.suggestion:
            result += f"\n   💡 Suggestion: {self.suggestion}"

        return result


class CodeReviewTool:
    """Tool for code review using LLM"""

    def __init__(self, config, llm_client):
        """Initialize CodeReviewTool.

        Args:
            config: Application configuration object containing LLM settings.
            llm_client: LLM client instance for performing deep code reviews.
        """
        self.config = config
        self.llm = llm_client

    def review(
        self,
        code: str,
        language: str = "python",
        file_path: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """Review code and return findings"""

        logger.info("reviewing_code", file_path=file_path, language=language)

        try:
            response = self.llm.review_code(
                code=code,
                language=language,
                file_path=file_path
            )

            if not response.content or "not configured" in response.content:
                return self._basic_review(code, language, file_path)

            return self._format_review_response(response.content, file_path)

        except Exception as e:
            logger.error("code_review_failed", error=str(e))
            return f"❌ Code review failed: {e}"

    def _basic_review(self, code: str, language: str, file_path: Optional[str]) -> str:
        """Perform basic static analysis when LLM is unavailable.

        Runs language-specific and generic static checks to identify common code issues
        like TODO comments, bare except clauses, mutable defaults, long lines, etc.

        Args:
            code: Source code to analyze.
            language: Programming language hint (python, javascript, etc.).
            file_path: Optional file path for context in the report.

        Returns:
            A formatted string containing the review findings or a clean bill of health.
        """

        issues = []
        lines = code.split("\n")

        # Check for common Python issues
        if language.lower() in ("python", "py"):
            issues.extend(self._check_python_issues(lines))

        # Check for common JS issues
        elif language.lower() in ("javascript", "js", "typescript", "ts"):
            issues.extend(self._check_js_issues(lines))

        # Generic checks
        issues.extend(self._check_generic_issues(lines))

        if not issues:
            return f"""## 🔍 代码审查

**文件**: {file_path or "未指定"}
**语言**: {language}

✅ 静态检查未发现问题

如需深度分析，请配置 `OPENROUTER_API_KEY` 或 `ANTHROPIC_API_KEY`"""

        result = [f"""## 🔍 代码审查

**文件**: {file_path or "未指定"}
**语言**: {language}

**发现问题**: {len(issues)} 个

"""]

        for issue in issues:
            result.append(issue.format())

        return "\n".join(result)

    def _check_python_issues(self, lines: List[str]) -> List[CodeReviewIssue]:
        """Check Python source code for common issues.

        Detects: TODO/FIXME comments, bare except clauses, print statements,
        and mutable default arguments.

        Args:
            lines: Source code split into individual lines.

        Returns:
            A list of CodeReviewIssue objects representing detected problems.
        """
        issues = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check for TODO
            if "TODO" in stripped or "FIXME" in stripped:
                issues.append(CodeReviewIssue(
                    severity="minor",
                    line=i,
                    message=f"发现未完成代码: {stripped[:50]}",
                    suggestion="完成后移除 TODO 注释"
                ))

            # Check for bare except
            if stripped.startswith("except:") or stripped == "except:":
                issues.append(CodeReviewIssue(
                    severity="major",
                    line=i,
                    message="使用裸 except 子句",
                    suggestion="使用 `except Exception:` 并指定具体异常类型"
                ))

            # Check for print statements
            if stripped.startswith("print(") and not stripped.startswith('"""'):
                issues.append(CodeReviewIssue(
                    severity="minor",
                    line=i,
                    message="发现 print 语句",
                    suggestion="考虑使用日志模块 (logging)"
                ))

            # Check for mutable default arguments
            if "def " in stripped and "=[]" in stripped:
                issues.append(CodeReviewIssue(
                    severity="major",
                    line=i,
                    message="使用可变默认参数",
                    suggestion="使用 None 作为默认值，在函数内检查"
                ))

        return issues

    def _check_js_issues(self, lines: List[str]) -> List[CodeReviewIssue]:
        """Check JavaScript/TypeScript source code for common issues.

        Detects: console.log statements and var declarations (prefer let/const).

        Args:
            lines: Source code split into individual lines.

        Returns:
            A list of CodeReviewIssue objects representing detected problems.
        """
        issues = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check for console.log
            if "console.log" in stripped:
                issues.append(CodeReviewIssue(
                    severity="minor",
                    line=i,
                    message="发现 console.log",
                    suggestion="移除生产代码中的调试语句"
                ))

            # Check for var (prefer let/const)
            if stripped.startswith("var "):
                issues.append(CodeReviewIssue(
                    severity="minor",
                    line=i,
                    message="使用 var 声明变量",
                    suggestion="使用 let 或 const 替代"
                ))

        return issues

    def _check_generic_issues(self, lines: List[str]) -> List[CodeReviewIssue]:
        """Check source code for generic (language-agnostic) issues.

        Detects: lines exceeding 120 characters and trailing whitespace.

        Args:
            lines: Source code split into individual lines.

        Returns:
            A list of CodeReviewIssue objects representing detected problems.
        """
        issues = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check for very long lines
            if len(line) > 120:
                issues.append(CodeReviewIssue(
                    severity="minor",
                    line=i,
                    message=f"行长度 {len(line)} 超过 120 字符",
                    suggestion="考虑拆分为多行"
                ))

            # Check for trailing whitespace
            if line != line.rstrip():
                issues.append(CodeReviewIssue(
                    severity="suggestion",
                    line=i,
                    message="行尾存在多余空格",
                    suggestion="移除尾随空格"
                ))

        return issues

    def _format_review_response(self, llm_response: str, file_path: Optional[str]) -> str:
        """Format a full LLM-based code review response with header.

        Args:
            llm_response: The raw response content from the LLM.
            file_path: Optional file path to include in the report header.

        Returns:
            A fully formatted review report with header and LLM content.
        """

        header = f"""## 🔍 代码审查

**文件**: {file_path or "未指定"}
**分析**: LLM 深度分析

---

"""

        return header + llm_response
