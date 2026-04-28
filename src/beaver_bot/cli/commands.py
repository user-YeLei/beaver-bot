"""Beaver Bot CLI Commands"""

from rich.console import Console

from beaver_bot.core.config import BeaverConfig, load_config
from beaver_bot.core.agent import BeaverAgent


console = Console()


def handle_command(cmd: str, config: BeaverConfig, agent: BeaverAgent) -> bool:
    """Handle built-in slash commands. Returns False if should exit."""

    cmd = cmd.strip().lower()

    if cmd in ("/exit", "/quit", "/q"):
        console.print("[blue]下次见! 👋[/blue]")
        return False

    elif cmd in ("/help", "/h", "?"):
        print_help()
        return True

    elif cmd in ("/clear", "/reset"):
        console.clear()
        return True

    elif cmd == "/model":
        show_model_info(config)
        return True

    elif cmd == "/status":
        show_status(agent)
        return True

    elif cmd.startswith("/model "):
        new_model = cmd.split(" ", 1)[1].strip()
        config.model.name = new_model
        console.print(f"[green]模型已切换为:[/green] {new_model}")
        return True

    elif cmd == "/debug":
        config.app.debug = not config.app.debug
        console.print(f"[yellow]调试模式:[/yellow] {'开启' if config.app.debug else '关闭'}")
        return True

    elif cmd == "/analyze":
        from beaver_bot.tools.code_analyzer import analyze_repository
        from pathlib import Path
        root = Path(__file__).parent.parent.parent.parent
        result = analyze_repository(str(root))
        console.print(result)
        return True

    elif cmd.startswith("/browse "):
        from beaver_bot.tools.browser_tool import BrowserTool
        url = cmd.split(" ", 1)[1].strip()
        if not url.startswith("http"):
            url = "https://" + url
        bt = BrowserTool()
        result = bt.open(url)
        console.print(f"[green]已打开:[/green] {url}")
        console.print(result)
        return True

    elif cmd == "/screenshot":
        from beaver_bot.tools.browser_tool import BrowserTool
        import tempfile
        bt = BrowserTool()
        bt.open("https://example.com")
        ss_path = tempfile.mktemp(suffix=".png")
        result = bt.screenshot(ss_path, full=True)
        console.print(f"[green]{result}[/green]")
        console.print(f"路径: {ss_path}")
        return True

    else:
        console.print(f"[red]未知命令:[/red] {cmd}")
        console.print("输入 [green]/help[/green] 查看可用命令")
        return True


def print_help() -> None:
    """Print help message"""
    help_text = """
# 🦫 Beaver Bot 帮助

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
    """Single query mode"""
    agent = BeaverAgent(config)
    response = agent.run(query)
    console.print(response)


def model_command(show: bool) -> None:
    """Model info command"""
    config = load_config()
    if show:
        show_model_info(config)
    else:
        show_model_info(config)
