"""Beaver Bot File Tool"""

import os
from pathlib import Path
from typing import Optional, List

import structlog

logger = structlog.get_logger()


class FileTool:
    """Tool for file operations"""

    def __init__(self, config):
        self.config = config

    def read_file(self, file_path: str, limit: Optional[int] = None) -> str:
        """Read file contents"""
        try:
            path = Path(file_path).expanduser()
            if not path.exists():
                return f"File not found: {file_path}"

            if not path.is_file():
                return f"Not a file: {file_path}"

            # Security: prevent path traversal
            try:
                root = self.config.file_tool.root_path
                path.resolve().relative_to(root)
            except ValueError:
                return "Access denied: path is outside current directory"

            with open(path, "r", encoding="utf-8") as f:
                if limit:
                    lines = [f.readline() for _ in range(limit)]
                    return f"📄 {path} (前{limit}行):\n" + "".join(lines)
                content = f.read()
                return f"📄 {path} ({len(content.splitlines())} 行):\n{content}"

        except Exception as e:
            logger.error("read_file_failed", path=file_path, error=str(e))
            return f"Error reading file: {e}"

    def write_file(self, file_path: str, content: str) -> str:
        """Write content to file"""
        try:
            path = Path(file_path).expanduser()

            # Create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return f"✅ File written: {path}"

        except Exception as e:
            logger.error("write_file_failed", path=file_path, error=str(e))
            return f"Error writing file: {e}"

    def list_directory(self, dir_path: str = ".") -> str:
        """List directory contents"""
        try:
            path = Path(dir_path).expanduser()
            if not path.exists():
                return f"Directory not found: {dir_path}"

            items = []
            for item in sorted(path.iterdir()):
                size = item.stat().st_size if item.is_file() else "-"
                item_type = "📁" if item.is_dir() else "📄"
                items.append(f"{item_type} {item.name} ({size})")

            return f"📂 {path}:\n" + "\n".join(items)

        except Exception as e:
            return f"Error listing directory: {e}"

    def search_files(self, pattern: str, path: str = ".") -> str:
        """Search for files matching pattern"""
        try:
            import fnmatch
            matches = []
            search_path = Path(path).expanduser()

            for item in search_path.rglob("*"):
                if item.is_file() and fnmatch.fnmatch(item.name, pattern):
                    matches.append(str(item))

            if matches:
                return f"🔍 Found {len(matches)} files:\n" + "\n".join(matches[:20])
            else:
                return f"No files matching '{pattern}' found"

        except Exception as e:
            return f"Error searching files: {e}"

    def search_content(self, query: str, path: str = ".", file_pattern: str = "*") -> str:
        """Search for content within files"""
        try:
            import fnmatch
            matches = []
            search_path = Path(path).expanduser()
            query_lower = query.lower()

            for item in search_path.rglob(file_pattern):
                if item.is_file():
                    try:
                        with open(item, "r", encoding="utf-8") as f:
                            for i, line in enumerate(f, 1):
                                if query_lower in line.lower():
                                    matches.append(f"{item}:{i}: {line.rstrip()}")
                    except (UnicodeDecodeError, PermissionError):
                        continue

            if matches:
                return f"🔍 Found {len(matches)} matches:\n" + "\n".join(matches[:30])
            else:
                return f"No matches for '{query}' found"

        except Exception as e:
            return f"Error searching content: {e}"

    def check_project_structure(self, path: str = ".") -> str:
        """Check project structure"""
        try:
            path = Path(path).expanduser()
            important_files = [
                "pyproject.toml", "setup.py", "requirements.txt",
                "package.json", "Cargo.toml", "go.mod",
                ".git", "README.md", "src/", "tests/"
            ]

            found = []
            missing = []
            for item in important_files:
                item_path = path / item
                if item_path.exists() or (path / item.rstrip("/")).exists():
                    found.append(item)
                else:
                    missing.append(item)

            result = [f"📂 Project: {path}"]
            if found:
                result.append(f"\n✅ Found: {', '.join(found)}")
            if missing:
                result.append(f"\n❌ Missing: {', '.join(missing)}")

            return "\n".join(result)

        except Exception as e:
            return f"Error checking project: {e}"
