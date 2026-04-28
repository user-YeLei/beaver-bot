# 🦫 Beaver Bot

AI Coding Assistant - 开发助手智能体

## 功能

- 💻 **代码生成** - 描述你想要的功能，AI 帮你写代码
- 🔍 **代码审查** - 分析代码问题，提供优化建议
- 🐛 **调试助手** - 帮你分析错误原因
- 🐙 **GitHub 集成** - 管理仓库、Issue、PR

## 安装

```bash
cd beaver-bot
source /path/to/venv/bin/activate  # 使用已有 Python 环境
export PYTHONPATH=src
export GITHUB_TOKEN=your_github_token
```

## 使用

```bash
# 交互式 CLI
PYTHONPATH=src beaver run

# 单次查询
PYTHONPATH=src beaver chat -q "帮我写一个快排算法"

# 查看帮助
PYTHONPATH=src beaver --help
```

## 项目结构

```
beaver-bot/
├── src/beaver_bot/
│   ├── main.py          # CLI 入口
│   ├── cli/             # 命令行交互
│   ├── core/            # Agent 核心
│   │   ├── agent.py     # 主循环
│   │   ├── intent_parser.py   # 意图识别
│   │   ├── task_planner.py     # 任务规划
│   │   └── tool_router.py      # 工具路由
│   └── tools/            # 工具集
│       ├── file_tool.py
│       ├── terminal_tool.py
│       └── github_tool.py
├── config/
│   └── settings.yaml
└── doc/
    └── architecture.md   # 架构设计
```

## 命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/exit` | 退出 |
| `/model` | 查看当前模型 |
| `/clear` | 清屏 |

## 测试状态

- **37 tests** - 全部通过
- 运行测试: `PYTHONPATH=src pytest tests/ -v`

## 技术栈

- **LLM**: MiniMax-M2.7 (api.minimaxi.com)
- **Python**: 3.11+
- **测试**: pytest + pytest-asyncio
- **CI/CD**: GitHub Actions

## 更新日志

- **2026-04-28**: Week 3 - 集成测试 + MiniMax LLM 支持
