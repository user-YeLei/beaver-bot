"""Beaver Agent CLI Commands"""

from rich.console import Console

from beaver_agent.core.config import BeaverConfig, load_config
from beaver_agent.core.agent import BeaverAgent


console = Console()


def handle_command(cmd: str, config: BeaverConfig, agent: BeaverAgent) -> bool:
    """Handle built-in slash commands. Returns False if should exit."""
    from pathlib import Path
    from beaver_agent.tools.browser_tool import BrowserTool
    from beaver_agent.tools.code_analyzer import analyze_repository
    import tempfile

    cmd = cmd.strip().lower()

    # Exit commands
    if cmd in ("/exit", "/quit", "/q"):
        console.print("[blue]下次见! 👋[/blue]")
        return False

    # Help
    if cmd in ("/help", "/h", "?"):
        print_help()
        return True

    # Clear screen
    if cmd in ("/clear", "/reset"):
        console.clear()
        return True

    # Model info
    if cmd == "/model":
        show_model_info(config)
        return True

    # Status
    if cmd == "/status":
        show_status(agent)
        return True

    # Switch model
    if cmd.startswith("/model "):
        config.model.name = cmd.split(" ", 1)[1].strip()
        console.print(f"[green]模型已切换为:[/green] {config.model.name}")
        return True

    # Debug toggle
    if cmd == "/debug":
        config.app.debug = not config.app.debug
        console.print(f"[yellow]调试模式:[/yellow] {'开启' if config.app.debug else '关闭'}")
        return True

    # Analyze repository
    if cmd == "/analyze":
        result = analyze_repository(str(Path(__file__).parent.parent.parent.parent))
        console.print(result)
        return True

    # Browse URL
    if cmd.startswith("/browse "):
        url = cmd.split(" ", 1)[1].strip()
        if not url.startswith("http"):
            url = "https://" + url
        bt = BrowserTool()
        result = bt.open(url)
        console.print(f"[green]已打开:[/green] {url}\n{result}")
        return True

    # Screenshot
    if cmd == "/screenshot":
        bt = BrowserTool()
        bt.open("https://example.com")
        ss_path = tempfile.mktemp(suffix=".png")
        result = bt.screenshot(ss_path, full=True)
        console.print(f"[green]{result}[/green]\n路径: {ss_path}")
        return True

    # Unknown command
    console.print(f"[red]未知命令:[/red] {cmd}\n输入 [green]/help[/green] 查看可用命令")
    return True


def print_help() -> None:
    """Print help message"""
    help_text = """
# 🦫 Beaver Agent 帮助

## 命令
| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/exit` | 退出程序 |
| `/clear` | 清屏 |
| `/model` | 显示当前模型 |
| `/model <name>` | 切换模型 |
| `/status` | 显示状态 |
| `/debug` | 切换调试模式 |
| `/analyze` | 分析代码仓库结构 |
| `/browse <url>` | 打开网页并获取内容 |
| `/screenshot` | 截取当前页面截图 |

## 功能
- **代码生成**: 描述你想要的功能，我帮你写代码
- **代码审查**: 分析代码问题，提供优化建议
- **调试助手**: 帮你分析错误原因
- **GitHub 集成**: 管理仓库、Issue、PR

## 示例
```
帮我写一个快排算法
帮我 review /path/to/file.py
解释一下这段代码的作用
```
"""
    from rich.markdown import Markdown
    console.print(Markdown(help_text))


def show_model_info(config: BeaverConfig) -> None:
    """Show current model info"""
    console.print(f"[green]当前模型:[/green] {config.model.name}")
    console.print(f"[green]Provider:[/green] {config.model.provider}")


def show_status(agent: BeaverAgent) -> None:
    """Show agent status"""
    console.print(f"[green]Agent状态:[/green] 运行中")
    console.print(f"[green]会话ID:[/green] {agent.session_id}")


def chat_command(config: BeaverConfig, query: str) -> None:
    """Execute a single chat query and exit.
    
    Args:
        config: The Beaver configuration object
        query: The user's query string to process
    """
    agent = BeaverAgent(config)
    response = agent.run(query)
    console.print(response)


def model_command(show: bool) -> None:
    """Display or manage the current LLM model.
    
    Args:
        show: If True, display current model information
    """
    config = load_config()
    if show:
        show_model_info(config)
    else:
        show_model_info(config)
