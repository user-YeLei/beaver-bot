"""Beaver Agent GitHub Tool"""

from __future__ import annotations

__all__ = ["GitHubTool"]

from typing import TYPE_CHECKING

import requests
import structlog

if TYPE_CHECKING:
    from beaver_agent.core.config import BeaverConfig

logger = structlog.get_logger()


class GitHubTool:
    """Tool for GitHub operations"""

    def __init__(self, config: BeaverConfig) -> None:
        """Initialize GitHubTool with BeaverConfig.

        Args:
            config: BeaverConfig instance containing github.token, github.owner,
                and github.repo settings. If any attribute is missing on the
                github sub-config, it defaults to None.
        """
        self.config = config
        self.token = getattr(config.github, "token", None) if hasattr(config, "github") else None
        self.owner = getattr(config.github, "owner", None) if hasattr(config, "github") else None
        self.repo = getattr(config.github, "repo", None) if hasattr(config, "github") else None

    def _check_config(self) -> bool:
        """Check if GitHub config is properly set"""
        return bool(self.token and self.owner and self.repo)

    def operate(
        self,
        action: str = "info",
        owner: str | None = None,
        repo: str | None = None,
        **kwargs,
    ) -> str:
        """Generic GitHub operation dispatcher.

        Routes to the appropriate GitHub API method based on the action parameter.
        Falls back to instance owner/repo if not provided.

        Args:
            action: The operation to perform. Supported values:
                - "info": Get repository information (via get_repo_info)
                - "create_issue": Create an issue (via create_issue)
                - "list_issues": List repository issues (via list_issues)
                - "get_issue": Get a specific issue by number (via get_issue)
                - "create_pr": Create a pull request (via create_pr)
            owner: GitHub repository owner. Defaults to instance owner if not provided.
            repo: GitHub repository name. Defaults to instance repo if not provided.
            **kwargs: Action-specific arguments:
                - create_issue: title (str), body (str)
                - get_issue: number (int)
                - create_pr: title (str), body (str), head (str), base (str)

        Returns:
            A string containing the operation result or an error message.
            Returns "Unknown action: {action}" for unrecognized actions.

        Example:
            >>> tool.operate("info", "owner", "repo")
            >>> tool.operate("create_issue", "owner", "repo", title="Bug", body="...")
            >>> tool.operate("get_issue", number=42)
        """
        owner = owner or self.owner
        repo = repo or self.repo

        if action == "info":
            return self.get_repo_info(owner, repo)
        elif action == "create_issue":
            return self.create_issue(owner, repo, kwargs.get("title", ""), kwargs.get("body", ""))
        elif action == "list_issues":
            return self.list_issues(owner, repo)
        elif action == "get_issue":
            return self.get_issue(owner, repo, kwargs.get("number", 1))
        elif action == "create_pr":
            return self.create_pr(
                owner,
                repo,
                kwargs.get("title", ""),
                kwargs.get("body", ""),
                kwargs.get("head", ""),
                kwargs.get("base", "main"),
            )
        else:
            return f"Unknown action: {action}"

    def get_repo_info(self, owner: str, repo: str) -> str:
        """Get detailed repository information from GitHub API.

        Fetches repository metadata including stars, forks, watchers, open issues,
        language, description, and HTML URL.

        Args:
            owner: GitHub repository owner (user or organization name).
            repo: GitHub repository name.

        Returns:
            A formatted markdown string containing repository statistics:
            - ⭐ Stars, 🍴 Forks, 👁️ Watchers, 📝 Open Issues,
            - 🏷️ Primary language, 📖 Description, 🔗 HTML URL.
            Returns an error message if the GitHub token is not configured
            or the API request fails.
        """
        if not self._check_config():
            return "❌ GitHub token not configured. Set github.token in config."

        try:
            url = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return f"""🐙 GitHub Repository Info

**{owner}/{repo}**

- ⭐ Stars: {data.get("stargazers_count", 0)}
- 🍴 Forks: {data.get("forks_count", 0)}
- 👁️ Watchers: {data.get("watchers_count", 0)}
- 📝 Issues: {data.get("open_issues_count", 0)}
- 🏷️ Language: {data.get("language", "N/A")}
- 📖 Description: {data.get("description", "N/A")}
- 🔗 URL: {data.get("html_url", "N/A")}
"""
            else:
                logger.warning("github_get_repo_info_failed", status=response.status_code, owner=owner, repo=repo)
                return f"❌ Failed to get repo info: {response.status_code} - {response.text}"

        except Exception as e:
            logger.error("github_api_failed", exc_info=e)
            return "❌ Error: Check logs for details."

    def create_issue(self, owner: str, repo: str, title: str, body: str = "") -> str:
        """Create a new issue in a repository.

        Args:
            owner: GitHub repository owner (user or organization)
            repo: Repository name
            title: Issue title
            body: Optional issue body/description (default: empty)

        Returns:
            A formatted success message with issue number and URL,
            or an error message if creation fails.

        Raises:
            No explicit raises - errors are logged and returned as string messages.
        """
        if not self._check_config():
            return "❌ GitHub token not configured. Set github.token in config."

        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
            }
            data = {"title": title, "body": body}

            response = requests.post(url, headers=headers, json=data, timeout=10)

            if response.status_code == 201:
                issue = response.json()
                return f"""✅ Issue created!

**#{issue.get("number")}**: {issue.get("title")}
🔗 {issue.get("html_url")}
"""
            else:
                return f"❌ Failed to create issue: {response.status_code} - {response.text}"

        except Exception as e:
            logger.error("github_create_issue_failed", exc_info=e)
            return "❌ Error: Check logs for details."

    def list_issues(self, owner: str, repo: str, state: str = "open") -> str:
        """List issues from a repository.

        Args:
            owner: GitHub repository owner (user or organization)
            repo: Repository name
            state: Issue state filter - "open", "closed", or "all" (default: "open")

        Returns:
            A formatted string listing issues with their numbers and titles,
            or an error message if the request fails.

        Raises:
            No explicit raises - errors are logged and returned as string messages.
        """
        if not self._check_config():
            return "❌ GitHub token not configured. Set github.token in config."

        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
            }
            params = {"state": state, "per_page": 10}

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                issues = response.json()
                if not issues:
                    return f"No {state} issues found"

                lines = [f"📋 {state.capitalize()} Issues ({len(issues)}):\n"]
                for issue in issues:
                    lines.append(f"  #{issue.get('number')}: {issue.get('title')}")
                return "\n".join(lines)
            else:
                return f"❌ Failed to list issues: {response.status_code}"

        except Exception as e:
            logger.error("github_list_issues_failed", exc_info=e)
            return "❌ Error: Check logs for details."

    def get_issue(self, owner: str, repo: str, number: int) -> str:
        """Get details of a specific issue.

        Args:
            owner: GitHub repository owner (user or organization)
            repo: Repository name
            number: Issue number to retrieve

        Returns:
            A formatted string containing issue details (title, state, labels,
            author, URL, and body), or an error message if the issue is not found.

        Raises:
            No explicit raises - errors are logged and returned as string messages.
        """
        if not self._check_config():
            return "❌ GitHub token not configured. Set github.token in config."

        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                issue = response.json()
                labels = ", ".join([label.get("name") for label in issue.get("labels", [])])
                return f"""📋 Issue #{issue.get("number")}

**Title**: {issue.get("title")}
**State**: {issue.get("state")}
**Labels**: {labels or "None"}
**Author**: {issue.get("user", {}).get("login", "Unknown")}
**URL**: {issue.get("html_url")}

---

{issue.get("body", "No description")}
"""
            else:
                return f"❌ Issue not found: {response.status_code}"

        except Exception as e:
            logger.error("github_get_issue_failed", exc_info=e)
            return "❌ Error: Check logs for details."

    def create_pr(
        self, owner: str, repo: str, title: str, body: str = "", head: str = "", base: str = "main"
    ) -> str:
        """Create a pull request in a repository.

        Args:
            owner: GitHub repository owner (user or organization).
            repo: Repository name.
            title: Pull request title.
            body: Optional PR description (default: empty).
            head: Branch name containing the changes (source branch).
            base: Target branch for the PR (default: "main").

        Returns:
            A formatted success message with PR number and URL,
            or an error message if PR creation fails.

        Raises:
            No explicit raises — errors are logged and returned as string messages.
        """
        if not self._check_config():
            return "❌ GitHub token not configured. Set github.token in config."

        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
            }
            data = {"title": title, "body": body, "head": head, "base": base}

            response = requests.post(url, headers=headers, json=data, timeout=10)

            if response.status_code == 201:
                pr = response.json()
                return f"""✅ PR created!

**#{pr.get("number")}**: {pr.get("title")}
🔗 {pr.get("html_url")}
"""
            else:
                logger.warning("github_create_pr_failed", status=response.status_code, owner=owner, repo=repo)
                return f"❌ Failed to create PR: {response.status_code} - {response.text}"

        except Exception as e:
            logger.error("github_create_pr_failed", exc_info=e)
            return "❌ Error: Check logs for details."
