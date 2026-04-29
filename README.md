# 🦫 Beaver Bot

> A self-evolving AI coding agent — built for developers who want an assistant that grows with their projects.

[![Tests](https://img.shields.io/badge/tests-66%20passing-brightgreen)](https://github.com/4th-engineer/beaver-bot)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

Beaver Bot is an intelligent coding assistant that combines LLM-powered code generation, review, and debugging with a unique **self-evolution** capability — it continuously improves itself on a schedule, learning from your projects and workflows.

---

## 🚀 One-Command Installation

```bash
git clone https://github.com/4th-engineer/beaver-bot.git
cd beaver-bot
make install
```

Then edit `.env` with your API keys and run:

```bash
make run
```

That's it.

---

## 💡 Quick Start

```bash
# 编辑配置文件
nano .env

# 运行交互式 CLI
make run

# 或者单次查询
make query ARGS='-q "写一个快排算法"'
```

---

## 🛠️ Developer Commands

All commands use `make`:

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies (creates venv) |
| `make install-dev` | Install with dev tools (pytest, ruff, mypy) |
| `make run` | Start interactive CLI |
| `make test` | Run all tests |
| `make lint` | Run ruff linter |
| `make fmt` | Format code with ruff |
| `make type-check` | Run mypy type checking |
| `make coverage` | Generate coverage report |
| `make clean` | Clean cache and build artifacts |

---

## 🐍 Alternative: Python Module Mode

If you prefer not to install `beaver` as a command, you can run directly with Python:

```bash
# Activate venv
source .venv/bin/activate

# Configure
export MINIMAX_API_KEY=your_key_here
export GITHUB_TOKEN=your_token_here

# Run interactive CLI
PYTHONPATH=src python -m beaver_bot.main run

# Or single query
PYTHONPATH=src python -m beaver_bot.main chat -q "写一个快排"
```

Or use the project's configured environment:

```bash
source .venv/bin/activate
source .env    # Load API keys
export PYTHONPATH=src
python -m beaver_bot.main run
```

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
│   │   ├── llm_client.py          # MiniMax / Anthropic / OpenAI
│   │   ├── conversation_logger.py # Debug logs for user-LLM interactions
│   │   └── memory/
│   │       ├── session.py         # Per-session context
│   │       └── persistent.py    # Cross-session knowledge
│   ├── tools/
│   │   ├── code_gen.py           # Code generation from descriptions
│   │   ├── code_review.py        # PR/代码审查
│   │   ├── debugger.py           # 错误分析与修复
│   │   ├── github_tool.py         # GitHub API 封装
│   │   ├── browser_tool.py       # 网页浏览与搜索
│   │   ├── file_tool.py          # 文件操作 (安全沙箱)
│   │   └── terminal_tool.py       # 命令执行 (sandboxed)
│   └── cli/
│       ├── interactive.py         # REPL 交互界面
│       └── commands.py            # /help /exit /model 等内置命令
├── skills/                        # 👤 User-extensible skills
│   ├── hello-world/
│   ├── project-analyzer/
│   └── mcp-config/
├── mcp_configs/                   # 👤 MCP server configurations
├── logs/                          # Conversation & debug logs
├── scripts/
│   └── install.sh                 # 一键安装脚本
├── tests/                         # 66 tests
└── doc/
    ├── architecture.md            # Full architecture docs
    └── evolution.md               # Self-evolution changelog
```

---

## ⚙️ Configuration

Edit `.env`:

```bash
# Required
MINIMAX_API_KEY=your_minimax_api_key_here
GITHUB_TOKEN=your_github_token_here

# Optional: Alternative LLM providers
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Or edit `config/settings.yaml` directly.

---

## 🧪 Test Suite

```bash
make test
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

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Language** | Python 3.11+ |
| **LLM** | MiniMax-M2.7 (Anthropic-compatible API) |
| **Agent** | Custom async orchestration |
| **Config** | Pydantic + YAML |
| **Testing** | pytest + pytest-asyncio |
| **Linting** | ruff |
| **Type Check** | mypy |

---

## 🔧 Manual Installation

```bash
# Clone and enter
git clone https://github.com/4th-engineer/beaver-bot.git
cd beaver-bot

# Create venv and install
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .   # Install beaver command

# Configure
cp .env.example .env
# Edit .env with your MINIMAX_API_KEY and GITHUB_TOKEN

# Run
beaver run
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
