"""Beaver Agent Terminal Tool"""

import subprocess
from typing import Optional, Dict, Any

import structlog

logger = structlog.get_logger()


class TerminalTool:
    """Tool for executing terminal commands"""

    # Commands that are blocked for security
    BLOCKED_COMMANDS = [
        "rm -rf /", "rm -rf ~", ":(){ :|:& };:",  # Dangerous commands
        "mkfs", "dd if=", "> /dev/sd",  # Disk operations
    ]

    def __init__(self, config):
        self.config = config

    def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: int = 60,
        shell: bool = True
    ) -> str:
        """Execute a terminal command"""
        try:
            # Security check
            if self._is_blocked(command):
                return "❌ Command blocked for security reasons"

            logger.info("executing_command", command=command, cwd=cwd)

            result = subprocess.run(
                command,
                shell=shell,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            output = []
            if result.stdout:
                output.append(f"stdout:\n{result.stdout}")
            if result.stderr:
                output.append(f"stderr:\n{result.stderr}")
            if result.returncode != 0:
                output.append(f"exit code: {result.returncode}")

            if output:
                return "\n".join(output)
            else:
                return "✅ Command executed successfully (no output)"

        except subprocess.TimeoutExpired:
            return f"❌ Command timed out after {timeout}s"
        except Exception as e:
            logger.error("command_execution_failed", command=command, error=str(e))
            return f"❌ Error: {e}"

    def _is_blocked(self, command: str) -> bool:
        """Check if command contains blocked patterns"""
        command_lower = command.lower()
        for blocked in self.BLOCKED_COMMANDS:
            if blocked.lower() in command_lower:
                return True
        return False

    def get_error_log(self, lines: int = 50) -> str:
        """Get recent error log entries from common log files.

        Searches standard system log locations and filters for error/exception
        entries. Useful for debugging and diagnosing issues.

        Platform-aware: detects Linux, macOS, or Windows and searches
        the appropriate log locations for each.

        Args:
            lines: Maximum number of recent lines to retrieve (default: 50)

        Returns:
            A string containing recent error log entries, or a message
            indicating no errors were found or no log files exist.
        """
        import platform
        import os

        system = platform.system().lower()

        # Platform-specific log locations
        if system == "darwin":
            # macOS
            log_files = [
                "/var/log/system.log",
                "~/Library/Logs/",
                "~/Library/Logs/CoreCapture/",
            ]
        elif system == "linux":
            # Linux
            log_files = [
                "/var/log/syslog",
                "/var/log/messages",
                "~/.local/share/Logs",
            ]
        elif system == "windows":
            # Windows PowerShell event log
            log_files = []
        else:
            log_files = []

        # For Windows, fall back to PowerShell Get-WinEvent
        if system == "windows":
            try:
                result = subprocess.run(
                    ["powershell", "-Command",
                     "Get-WinEvent -LogName System -MaxEvents 50 | "
                     "Where-Object {$_.LevelDisplayName -eq 'Error'} | "
                     "Format-List TimeCreated,Message"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.stdout:
                    return result.stdout
                return "No Windows System log errors found"
            except Exception as e:
                return f"Error reading Windows log: {e}"

        # Linux / macOS / other Unix
        try:
            for log_file in log_files:
                path = os.path.expanduser(log_file)

                # Handle directory targets (macOS ~/Library/Logs/)
                if os.path.isdir(path):
                    try:
                        log_files_in_dir = sorted(
                            [os.path.join(path, f) for f in os.listdir(path)
                             if f.endswith(".log") or "error" in f.lower()],
                            key=os.path.getmtime,
                            reverse=True,
                        )[:3]
                        for lf in log_files_in_dir:
                            errors = self._read_error_lines(lf, lines)
                            if errors:
                                return errors
                    except PermissionError:
                        continue
                    continue

                if os.path.exists(path) and os.path.isfile(path):
                    errors = self._read_error_lines(path, lines)
                    if errors:
                        return errors

            return "No log files found"

        except Exception as e:
            logger.warning("error_log_read_failed", error=str(e))
            return f"Error reading log: {e}"

    def _read_error_lines(self, path: str, lines: int) -> str:
        """Read and filter error lines from a log file."""
        import os
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
            recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
            errors = [
                l for l in recent
                if "error" in l.lower() or "exception" in l.lower() or "fail" in l.lower()
            ]
            if errors:
                return f"=== {path} ===\n" + "".join(errors)
            return ""
        except PermissionError:
            return ""

    def run_tests(self, test_command: Optional[str] = None) -> str:
        """Run tests using auto-detected test framework.

        Automatically detects available test frameworks (pytest, npm, cargo, go)
        by checking for their presence in the current working directory.

        Args:
            test_command: Optional explicit test command to run.
                          If provided, uses this command directly instead of
                          auto-detection.

        Returns:
            A string containing the test execution output, or an error
            message if no test framework is detected.
        """
        import os

        # Auto-detect test framework
        if test_command:
            return self.execute(test_command)

        test_commands = [
            ("pytest", "pytest -v"),
            ("python -m pytest", "python -m pytest -v"),
            ("npm test", "npm test"),
            ("cargo test", "cargo test"),
            ("go test", "go test ./..."),
        ]

        cwd = os.getcwd()
        for name, cmd in test_commands:
            if os.path.exists(os.path.join(cwd, name)):
                return self.execute(cmd)

        return "❌ No test framework detected"
