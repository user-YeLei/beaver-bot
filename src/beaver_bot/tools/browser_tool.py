"""Browser Tool - Web scraping, screenshots, and browser automation using agent-browser CLI"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


AGENT_BROWSER_BIN = "/home/agentuser/.hermes/hermes-agent/node_modules/.bin/agent-browser"


@dataclass
class BrowserResult:
    success: bool
    content: Any = None
    message: str = ""
    error: Optional[str] = None


def _run_browser_cmd(cmd: str, timeout: int = 30) -> BrowserResult:
    """Run agent-browser command and return result"""
    try:
        result = subprocess.run(
            f"{AGENT_BROWSER_BIN} {cmd}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return BrowserResult(success=True, content=result.stdout, message=result.stdout.strip())
        else:
            return BrowserResult(success=False, error=result.stderr.strip() or result.stdout.strip())
    except subprocess.TimeoutExpired:
        return BrowserResult(success=False, error=f"Command timed out after {timeout}s")
    except Exception as e:
        return BrowserResult(success=False, error=str(e))


def navigate(url: str, timeout: int = 30) -> BrowserResult:
    """Navigate to a URL"""
    return _run_browser_cmd(f"open {url}", timeout=timeout)


def snapshot(interactive_only: bool = True, compact: bool = True, depth: int = 10) -> BrowserResult:
    """Get page accessibility tree snapshot"""
    cmd = "snapshot"
    if interactive_only:
        cmd += " -i"
    if compact:
        cmd += " -c"
    cmd += f" -d {depth}"
    return _run_browser_cmd(cmd)


def screenshot(path: Optional[str] = None, full_page: bool = False, annotate: bool = False) -> BrowserResult:
    """Take screenshot of current page"""
    if path is None:
        path = tempfile.mktemp(suffix=".png")

    cmd = f"screenshot {path}"
    if full_page:
        cmd += " --full"
    if annotate:
        cmd += " --annotate"

    result = _run_browser_cmd(cmd)
    if result.success:
        result.content = path
        result.message = f"Screenshot saved to {path}"
    return result


def get_text(selector: str = None) -> BrowserResult:
    """Get text content from page or element"""
    cmd = f"get text" if selector is None else f"get text {selector}"
    return _run_browser_cmd(cmd)


def get_html(selector: str = None) -> BrowserResult:
    """Get HTML content from page or element"""
    cmd = f"get html" if selector is None else f"get html {selector}"
    return _run_browser_cmd(cmd)


def get_title() -> BrowserResult:
    """Get page title"""
    return _run_browser_cmd("get title")


def get_url() -> BrowserResult:
    """Get current URL"""
    return _run_browser_cmd("get url")


def click(selector: str) -> BrowserResult:
    """Click an element by selector or @ref"""
    return _run_browser_cmd(f"click {selector}")


def fill(selector: str, text: str) -> BrowserResult:
    """Fill input field with text"""
    escaped_text = text.replace('"', '\\"')
    return _run_browser_cmd(f'fill {selector} "{escaped_text}"')


def type_text(selector: str, text: str) -> BrowserResult:
    """Type text into element (character by character)"""
    escaped_text = text.replace('"', '\\"')
    return _run_browser_cmd(f'type {selector} "{escaped_text}"')


def press(key: str) -> BrowserResult:
    """Press keyboard key"""
    return _run_browser_cmd(f"press {key}")


def scroll(direction: str, pixels: int = 300) -> BrowserResult:
    """Scroll page: up, down, left, right"""
    return _run_browser_cmd(f"scroll {direction} {pixels}")


def scroll_into_view(selector: str) -> BrowserResult:
    """Scroll element into view"""
    return _run_browser_cmd(f"scrollintoview {selector}")


def wait(selector_or_ms: str) -> BrowserResult:
    """Wait for element or time in ms"""
    return _run_browser_cmd(f"wait {selector_or_ms}")


def find_elements(role: str, value: str, action: str = "click", name: str = None) -> BrowserResult:
    """Find elements by role, text, label, etc."""
    cmd = f"find {role} {value} {action}"
    if name:
        cmd += f" --name {name}"
    return _run_browser_cmd(cmd)


def back() -> BrowserResult:
    """Go back in browser history"""
    return _run_browser_cmd("back")


def forward() -> BrowserResult:
    """Go forward in browser history"""
    return _run_browser_cmd("forward")


def reload() -> BrowserResult:
    """Reload current page"""
    return _run_browser_cmd("reload")


def close() -> BrowserResult:
    """Close browser"""
    return _run_browser_cmd("close")


def fetch_content(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Fetch URL and return structured content"""
    # Navigate to URL
    nav_result = navigate(url, timeout=timeout)
    if not nav_result.success:
        return {"success": False, "error": nav_result.error, "url": url}

    # Wait for page to load
    wait("networkidle")

    # Get page info
    title_result = get_title()
    url_result = get_url()
    snapshot_result = snapshot()

    return {
        "success": True,
        "url": url_result.content or url,
        "title": title_result.content,
        "snapshot": snapshot_result.content,
        "message": "Page fetched successfully"
    }


def take_screenshot(url: str, output_path: str = None, full_page: bool = False, timeout: int = 30) -> Dict[str, Any]:
    """Navigate to URL and take screenshot"""
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".png")

    # Navigate
    nav_result = navigate(url, timeout=timeout)
    if not nav_result.success:
        return {"success": False, "error": nav_result.error}

    # Wait for load
    wait("networkidle")

    # Screenshot
    ss_result = screenshot(output_path, full_page=full_page)

    return {
        "success": ss_result.success,
        "path": ss_result.content if ss_result.success else None,
        "error": ss_result.error if not ss_result.success else None,
        "url": url
    }


# Convenience class for unified interface
class BrowserTool:
    """Browser automation tool for beaver-bot"""

    def __init__(self):
        self.current_url: Optional[str] = None
        self.last_snapshot: Optional[str] = None

    def open(self, url: str) -> str:
        """Open URL and return snapshot"""
        result = navigate(url)
        if result.success:
            self.current_url = url
            snapshot_result = snapshot()
            self.last_snapshot = snapshot_result.content
            return snapshot_result.content or f"Opened {url}"
        return f"Error: {result.error}"

    def browse(self, url: str, action: str = "snapshot") -> str:
        """Open URL and perform action (snapshot, screenshot, etc.)"""
        self.open(url)
        if action == "snapshot":
            return self.last_snapshot or "No content"
        elif action == "screenshot":
            ss_result = screenshot()
            return ss_result.message
        elif action == "title":
            title_result = get_title()
            return title_result.content or "No title"
        return "Unknown action"

    def interactive(self) -> str:
        """Get interactive elements only"""
        result = snapshot(interactive_only=True, compact=False)
        self.last_snapshot = result.content
        return result.content or "No interactive elements"

    def screenshot(self, path: str = None, full: bool = False) -> str:
        """Take screenshot"""
        result = screenshot(path, full_page=full, annotate=True)
        return result.message

    def click(self, selector: str) -> str:
        """Click element"""
        result = click(selector)
        if result.success:
            snap = snapshot()
            self.last_snapshot = snap.content
            return snap.content or "Clicked"
        return f"Error: {result.error}"

    def fill(self, selector: str, text: str) -> str:
        """Fill input"""
        result = fill(selector, text)
        return result.message if result.success else f"Error: {result.error}"

    def scroll(self, direction: str = "down", pixels: int = 300) -> str:
        """Scroll page"""
        result = scroll(direction, pixels)
        if result.success:
            snap = snapshot()
            self.last_snapshot = snap.content
            return snap.content or "Scrolled"
        return f"Error: {result.error}"

    def get_page_info(self) -> Dict[str, str]:
        """Get current page info"""
        title = get_title()
        url = get_url()
        return {
            "title": title.content or "",
            "url": url.content or ""
        }
