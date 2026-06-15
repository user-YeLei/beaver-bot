"""Beaver Agent Terminal Tool"""

__all__ = ["TerminalTool"]

import os
import platform
import subprocess

import structlog

logger = structlog.get_logger()


class TerminalTool:
    """Tool for executing terminal commands"""

    # Commands that are blocked for security
    BLOCKED_COMMANDS = [
        "rm -rf /",
        "rm -rf ~",
        ":(){ :|:& };:",  # Dangerous commands
        "mkfs",
        "dd if=",
        "> /dev/sd",  # Disk operations
    ]

    def __init__(self, config) -> None:
        """Initialize the TerminalTool with configuration.

        Args:
            config: Configuration object for the tool. Must provide any
                settings needed for command execution (e.g., allowed directories,
                environment variables, timeout defaults).
        """
        self.config = config

    def execute(
        self, command: str, cwd: str | None = None, timeout: int = 60, shell: bool = True
    ) -> str:
        """Execute a terminal command.

        Runs a shell command and returns its stdout/stderr output. Security-blocked
        commands (e.g., destructive rm, disk operations) are rejected before execution.

        Args:
            command: The shell command string to execute.
            cwd: Optional working directory to run the command in. Defaults to None (current dir).
            timeout: Maximum seconds to wait for command completion. Defaults to 60.
            shell: If True, command is executed via shell (allows pipes, redirects). Defaults to True.

        Returns:
            A string containing command output (stdout/stderr), or an error message.
            Returns "✅ Command executed successfully (no output)" on success with no output.
            Returns "❌ Command blocked for security reasons" for blocked commands.
            Returns "❌ Command timed out after {timeout}s" on timeout.
            Returns "❌ Error: {exception}" on unexpected failures.

        Raises:
            No exceptions are raised — all errors are returned as strings.

        Example:
            >>> result = tool.execute("ls -la /tmp")
            >>> result = tool.execute("grep -r 'error' ./logs", cwd="/home/user")
            >>> result = tool.execute("python script.py", timeout=120)
        """
        try:
            # Security check
            if self._is_blocked(command):
                return "❌ Command blocked for security reasons"

            logger.info("executing_command", command=command, cwd=cwd)

            result = subprocess.run(
                command, shell=shell, cwd=cwd, capture_output=True, text=True, timeout=timeout
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
            logger.error("command_execution_failed", command=command, exc_info=e)
            return f"❌ Error: {e}"

    def _is_blocked(self, command: str) -> bool:
        """Check if command contains blocked security patterns.

        Scans the command string for known dangerous patterns (e.g., recursive
        rm, fork bombs, disk operations) defined in BLOCKED_COMMANDS.

        Args:
            command: The raw command string to check (case-insensitive scan).

        Returns:
            True if the command matches any blocked pattern, False otherwise.
        """
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
                    [
                        "powershell",
                        "-Command",
                        "Get-WinEvent -LogName System -MaxEvents 50 | "
                        "Where-Object {$_.LevelDisplayName -eq 'Error'} | "
                        "Format-List TimeCreated,Message",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.stdout:
                    return result.stdout
                return "No Windows System log errors found"
            except Exception as e:
                logger.warning("error_reading_windows_log", exc_info=e)
                return f"Error reading Windows log: {e}"

        # Linux / macOS / other Unix
        try:
            for log_file in log_files:
                path = os.path.expanduser(log_file)

                # Handle directory targets (macOS ~/Library/Logs/)
                if os.path.isdir(path):
                    try:
                        log_files_in_dir = sorted(
                            [
                                os.path.join(path, f)
                                for f in os.listdir(path)
                                if f.endswith(".log") or "error" in f.lower()
                            ],
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
            logger.warning("error_log_read_failed", exc_info=e)
            return f"Error reading log: {e}"

    def _read_error_lines(self, path: str, lines: int) -> str:
        """Read and filter error lines from a log file.

        Opens the log file at the given path, reads the most recent N lines,
        and filters for lines containing 'error', 'exception', or 'fail'.

        Args:
            path: Absolute path to the log file to read.
            lines: Maximum number of lines to read from the end of the file.

        Returns:
            A formatted string of matching error lines prefixed with the file path,
            or an empty string if no errors are found or on PermissionError.
        """
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
            recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
            errors = [
                line
                for line in recent
                if "error" in line.lower() or "exception" in line.lower() or "fail" in line.lower()
            ]
            if errors:
                return f"=== {path} ===\n" + "".join(errors)
            return ""
        except PermissionError:
            return ""

    def run_tests(self, test_command: str | None = None) -> str:
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
