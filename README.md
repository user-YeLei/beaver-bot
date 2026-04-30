# 🦫 Beaver Agent

> A self-evolving AI coding assistant — built for developers who want an agent that grows with their projects.

[![Tests](https://img.shields.io/badge/tests-87%20passing-brightgreen)](https://github.com/4th-engineer/beaver-agent)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

---

## 🚀 Quick Start

```bash
git clone https://github.com/4th-engineer/beaver-agent.git
cd beaver-agent

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e ".[dev]"

# 首次配置
beaver setup

# 运行
beaver run
```

---

## 📋 Commands

| Command | Description |
|---------|-------------|
| `beaver setup` | 首次配置（创建 .env） |
| `beaver run` | 启动交互式 CLI |
| `beaver chat -q "问题"` | 单次查询 |
| `beaver model` | 查看/切换模型 |
| `pytest` | 运行测试 |
| `ruff check .` | 代码检查 |
| `ruff format .` | 格式化代码 |
| `mypy src/` | 类型检查 |

---

## ⚙️ Configuration

创建 `.env` 文件（复制 `.env.example`），填入：

```bash
MINIMAX_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
```

.env 文件会被自动加载。

---

## ✨ Features

### 🤖 Core Capabilities

| Feature | Description |
|---------|-------------|
| **Code Generation** | 描述需求 → 生成代码（Python, JS, Go, Rust 等） |
| **Code Review** | AI 代码审查，inline 建议 |
| **Debug Assistant** | 错误分析 + 修复建议 |
| **GitHub Integration** | 管理仓库、Issue、PR |
| **Web Research** | 网页搜索、文档抓取 |

### 🔧 Extensible Architecture

| Extension | 说明 |
|-----------|------|
| **Skills** (`skills/`) | 可插拔技能模块，关键词触发 |
| **MCP Servers** (`mcp_configs/`) | YAML 配置 MCP 服务器 |
| **Tools** (`src/beaver_agent/tools/`) | 模块化工具系统 |

### 🦫 Self-Evolution

每日 09:00 自动运行改进周期：
1. 分析对话模式，识别改进点
2. 清理 TODO，优化生成代码质量
3. 更新 skills 和文档
4. 所有变更记录到 `doc/evolution.md`

---

## 📁 Project Structure

```
beaver-agent/
├── src/beaver_agent/
│   ├── core/
│   │   ├── agent.py              # Agent 主循环
│   │   ├── intent_parser.py      # 意图识别
│   │   ├── task_planner.py       # 任务规划
│   │   ├── tool_router.py        # 工具路由
│   │   ├── skill_manager.py      # Skill 管理
│   │   ├── mcp_manager.py        # MCP 服务器管理
│   │   ├── llm_client.py         # LLM 客户端
│   │   └── conversation_logger.py # 调试日志
│   ├── tools/
│   │   ├── code_gen.py, code_review.py, debugger.py
│   │   ├── github_tool.py, browser_tool.py
│   │   ├── file_tool.py, terminal_tool.py
│   └── cli/
│       ├── interactive.py, commands.py
├── skills/                      # 用户可扩展 skills
├── mcp_configs/                  # 用户可配置 MCP
├── logs/                         # 对话日志
├── tests/                        # 70 tests
└── doc/
    ├── architecture.md           # 架构文档
    └── evolution.md             # 自我进化日志
```

---

## 🧪 Test Suite

```bash
pytest
```

---

## 📚 Documentation

- **[Architecture](doc/architecture.md)** — 系统架构详解
- **[Evolution Log](doc/evolution.md)** — 自我进化记录

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Language** | Python 3.11+ |
| **LLM** | MiniMax-M2.7 (Anthropic-compatible API) |
| **Agent** | Custom async orchestration |
| **Config** | Pydantic + YAML + python-dotenv |
| **Testing** | pytest + pytest-asyncio |
| **Linting** | ruff |
| **Type Check** | mypy |

---

## 📄 License

MIT License
