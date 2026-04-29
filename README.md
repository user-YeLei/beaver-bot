# 🦫 Beaver Bot

> A self-evolving AI coding agent — built for developers who want an assistant that grows with their projects.

[![Tests](https://img.shields.io/badge/tests-66%20passing-brightgreen)](https://github.com/4th-engineer/beaver-bot)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

Beaver Bot is an intelligent coding assistant that combines LLM-powered code generation, review, and debugging with a unique **self-evolution** capability — it continuously improves itself on a schedule, learning from your projects and workflows.

---

## ✨ Features

### 🤖 Core Capabilities

| Feature | Description |
|---------|-------------|
| **Code Generation** | Describe what you need, get production-ready code in Python, JavaScript, Go, Rust, and more |
| **Code Review** | AI-powered PR review with inline suggestions and quality analysis |
| **Debug Assistant** | Paste error messages, get root cause analysis and fix recommendations |
| **GitHub Integration** | Manage repos, issues, and pull requests directly from conversation |
| **Web Research** | Search the web, fetch documentation, extract technical information |

### 🔧 Extensible Architecture

| Extension Point | How It Works |
|----------------|-------------|
| **Skills** (`skills/`) | Drop-in skill modules with trigger keywords, templates, and step-by-step instructions |
| **MCP Servers** (`mcp_configs/`) | Configure Model Context Protocol servers via YAML — Beaver auto-connects them |
| **Tools** (`src/tools/`) | Modular tool system — each tool is self-contained with its own prompts |

### 🦫 Self-Evolution

Beaver Bot runs a daily improvement cycle at 09:00. It:
1. Analyzes recent conversations and identifies patterns
2. Cleans up TODOs and improves generated code quality
3. Updates its own skills and documentation
4. Logs all changes to `doc/evolution.md`

---

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/4th-engineer/beaver-bot.git
cd beaver-bot

# Set up environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure (copy and edit)
cp config/settings.yaml.example config/settings.yaml
# Add your MINIMAX_API_KEY and GITHUB_TOKEN

# Run
export PYTHONPATH=src
beaver run
```

### Single Query Mode

```bash
PYTHONPATH=src beaver chat -q "帮我写一个快排算法"
```

---

## 📁 Project Structure

```
beaver-bot/
├── src/beaver_bot/
│   ├── core/
│   │   ├── agent.py              # Agent orchestration loop
│   │   ├── intent_parser.py      # Intent recognition & routing
│   │   ├── task_planner.py       # Task decomposition
│   │   ├── tool_router.py        # Tool dispatch
│   │   ├── skill_manager.py      # Skill loading & invocation
│   │   ├── mcp_manager.py        # MCP server management
│   │   ├── llm_client.py         # MiniMax / Anthropic / OpenAI
│   │   ├── conversation_logger.py # Debug logs for user-LLM interactions
│   │   └── memory/
│   │       ├── session.py        # Per-session context
│   │       └── persistent.py     # Cross-session knowledge
│   ├── tools/
│   │   ├── code_gen.py           # Code generation from descriptions
│   │   ├── code_review.py        # PR/代码审查
│   │   ├── debugger.py           # 错误分析与修复
│   │   ├── github_tool.py        # GitHub API 封装
│   │   ├── browser_tool.py       # 网页浏览与搜索
│   │   ├── file_tool.py          # 文件操作 (安全沙箱)
│   │   └── terminal_tool.py      # 命令执行 (sandboxed)
│   └── cli/
│       ├── interactive.py        # REPL 交互界面
│       └── commands.py           # /help /exit /model 等内置命令
├── skills/                        # 👤 User-extensible skills
│   ├── hello-world/              # Skill example
│   ├── project-analyzer/        # Codebase analysis skill
│   └── mcp-config/              # Auto-configure MCP servers
├── mcp_configs/                   # 👤 MCP server configurations
│   ├── example-filesystem.yaml
│   └── example-time.yaml
├── logs/                         # Conversation & debug logs
├── tests/                        # 66 tests
└── doc/
    ├── architecture.md          # Full architecture docs
    └── evolution.md             # Self-evolution changelog
```

---

## 🛠️ Usage Examples

### Code Generation

```
You: 写一个 Python 装饰器来缓存函数结果，带过期时间
Beaver: [生成代码...]
✅ 已创建 cache_decorator.py

def memoize(ttl_seconds=300):
    """带过期时间的 LRU 缓存装饰器"""
    cache = {}
    ...
```

### Code Review

```
You: review /home/user/project/main.py
Beaver: [分析中...]
✅ 读取文件 (45行)

📝 审查结果:
1. [警告] 第23行: 缺少空值检查
2. [建议] 第31行: 可用列表推导式优化
3. [优化] 第38-42行: 循环可并行化
```

### Skill Extension

Skills are triggered by keywords and can provide templates, multi-step workflows, and specialized prompts.

```
You: 我想配置一个 MCP 服务器
Beaver: [触发 mcp-config skill]
✅ 检测到 MCP 配置请求
📋 可用模板: GitHub, Filesystem, Time, Brave Search, Slack
```

---

## ⚙️ Configuration

```yaml
# config/settings.yaml
llm:
  provider: minimax
  model: MiniMax-M2.7
  base_url: https://api.minimaxi.com/anthropic/v1/messages
  api_key: ${MINIMAX_API_KEY}

github:
  token: ${GITHUB_TOKEN}

tools:
  allowed_commands:
    - pip install
    - pytest
    - git
  sandbox_root: /home/agentuser

logging:
  level: INFO
  conversation_logs: logs/
```

---

## 🧪 Test Suite

```bash
PYTHONPATH=src pytest tests/ -v
```

| Category | Tests | Status |
|----------|-------|--------|
| Core (agent, intent, planner, router) | 20 | ✅ |
| Tools (code_gen, file, terminal, github) | 18 | ✅ |
| Skills & MCP | 12 | ✅ |
| Memory & Logging | 16 | ✅ |
| **Total** | **66** | **✅** |

---

## 🦫 Self-Evolution

Beaver Bot is designed to improve itself continuously:

- **Cron Schedule**: Daily at 09:00
- **Evolution Log**: `doc/evolution.md`
- **Principle**: Small, incremental changes — never break tests

| Date | Improvement |
|------|-------------|
| 2026-04-28 | Fixed path security in FileTool |
| 2026-04-29 | Added extensible skill system |
| 2026-04-29 | Added MCP server auto-configuration |
| 2026-04-29 | Added conversation logger for debugging |

---

## 📚 Documentation

- **[Architecture](doc/architecture.md)** — Full system design, component diagrams, data flow
- **[Evolution Log](doc/evolution.md)** — Track all self-improvements
- **[Skills Guide](skills/)** — How to create custom skills
- **[MCP Config Guide](mcp_configs/)** — How to configure MCP servers

---

## �tech Stack

| Layer | Technology |
|-------|------------|
| **Language** | Python 3.11+ |
| **LLM** | MiniMax-M2.7 (Anthropic-compatible API) |
| **Agent** | Custom async orchestration |
| **Config** | Pydantic + YAML |
| **Testing** | pytest + pytest-asyncio |
| **CI** | GitHub Actions (optional) |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
