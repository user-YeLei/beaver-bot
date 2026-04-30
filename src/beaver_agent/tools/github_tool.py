"""Beaver Bot GitHub Tool"""

from typing import Optional

import structlog

logger = structlog.get_logger()


class GitHubTool:
    """Tool for GitHub operations"""

    def __init__(self, config):
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
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generic GitHub operation"""
        owner = owner or self.owner
        repo = repo or self.repo

        if action == "info":
            return self.get_repo_info(owner, repo)
        elif action == "create_issue":
            return self.create_issue(
                owner, repo,
                kwargs.get("title", ""),
                kwargs.get("body", "")
            )
        elif action == "list_issues":
            return self.list_issues(owner, repo)
        elif action == "get_issue":
            return self.get_issue(owner, repo, kwargs.get("number", 1))
        elif action == "create_pr":
            return self.create_pr(
                owner, repo,
                kwargs.get("title", ""),
                kwargs.get("body", ""),
                kwargs.get("head", ""),
                kwargs.get("base", "main")
            )
        else:
            return f"Unknown action: {action}"

    def get_repo_info(self, owner: str, repo: str) -> str:
        """Get repository information"""
        if not self._check_config():
            return "❌ GitHub token not configured. Set github.token in config."

        try:
            import requests

            url = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return f"""🐙 GitHub 仓库信息

**{owner}/{repo}**

- ⭐ Stars: {data.get('stargazers_count', 0)}
- 🍴 Forks: {data.get('forks_count', 0)}
- 👁️ Watchers: {data.get('watchers_count', 0)}
- 📝 Issues: {data.get('open_issues_count', 0)}
- 🏷️ Language: {data.get('language', 'N/A')}
- 📖 Description: {data.get('description', 'N/A')}
- 🔗 URL: {data.get('html_url', 'N/A')}
"""
            else:
                return f"❌ Failed to get repo info: {response.status_code} - {response.text}"

        except Exception as e:
            logger.error("github_api_failed", error=str(e))
            return f"❌ Error: {e}"

    def create_issue(self, owner: str, repo: str, title: str, body: str = "") -> str:
        """Create a new issue"""
        if not self._check_config():
            return "❌ GitHub token not configured. Set github.token in config."

        try:
            import requests

            url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            data = {"title": title, "body": body}

            response = requests.post(url, headers=headers, json=data, timeout=10)

            if response.status_code == 201:
                issue = response.json()
                return f"""✅ Issue 创建成功!

**#{issue.get('number')}**: {issue.get('title')}
🔗 {issue.get('html_url')}
"""
            else:
                return f"❌ Failed to create issue: {response.status_code} - {response.text}"

        except Exception as e:
            return f"❌ Error: {e}"

    def list_issues(self, owner: str, repo: str, state: str = "open") -> str:
        """List issues"""
        if not self._check_config():
            return "❌ GitHub token not configured. Set github.token in config."

        try:
            import requests

            url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
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
            return f"❌ Error: {e}"

    def get_issue(self, owner: str, repo: str, number: int) -> str:
        """Get a specific issue"""
        if not self._check_config():
            return "❌ GitHub token not configured. Set github.token in config."

        try:
            import requests

            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                issue = response.json()
                labels = ", ".join([l.get("name") for l in issue.get("labels", [])])
                return f"""📋 Issue #{issue.get('number')}

**Title**: {issue.get('title')}
**State**: {issue.get('state')}
**Labels**: {labels or 'None'}
**Author**: {issue.get('user', {}).get('login', 'Unknown')}
**URL**: {issue.get('html_url')}

---

{issue.get('body', 'No description')}
"""
            else:
                return f"❌ Issue not found: {response.status_code}"

        except Exception as e:
            return f"❌ Error: {e}"

    def create_pr(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        head: str = "",
        base: str = "main"
    ) -> str:
        """Create a pull request"""
        if not self._check_config():
            return "❌ GitHub token not configured. Set github.token in config."

        try:
            import requests

            url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            data = {
                "title": title,
                "body": body,
                "head": head,
                "base": base
            }

            response = requests.post(url, headers=headers, json=data, timeout=10)

            if response.status_code == 201:
                pr = response.json()
                return f"""✅ PR 创建成功!

**#{pr.get('number')}**: {pr.get('title')}
🔗 {pr.get('html_url')}
"""
            else:
                return f"❌ Failed to create PR: {response.status_code} - {response.text}"

        except Exception as e:
            return f"❌ Error: {e}"
