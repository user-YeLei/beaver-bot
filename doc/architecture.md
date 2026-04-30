# 🦫 Beaver Bot 全能智能体 — 架构设计 v2

> 版本: v2.0
> 更新: 2026-04-28
> 作者: Beaver Bot Team

---

## 一、项目定位

| 阶段 | 目标 | 落地时间 |
|------|------|---------|
| **Phase 1** | 开发助手 — 代码生成/审查/调试/GitHub | 本次 |
| **Phase 2** | 多平台助手 — 微信/飞书/Telegram 对话 | 第二期 |
| **Phase 3** | 自动化执行 — 定时任务/CI触发/监控告警 | 第三期 |

---

## 二、系统架构

```
                     ┌─────────────────────────────────────────┐
                     │           Messaging Platforms            │
                     │   WeChat  Telegram  Discord  飞书  微信  │
                     └──────────────┬──────────────────────────┘
                                    │
                     ┌──────────────▼──────────────────────────┐
                     │          Gateway / Adapter Layer          │
                     │  (消息路由、身份识别、指令解析、多租户)    │
                     └──────────────┬──────────────────────────┘
                                    │
┌───────────────────────────────────┼───────────────────────────────────────────┐
│                         ┌──────────▼──────────┐                                 │
│                         │   CLI Adapter      │  ← 新增                          │
│                         │  (命令解析/交互式)  │                                 │
│                         └──────────┬──────────┘                                 │
│                                    │                                            │
│                         ┌──────────▼──────────┐                                 │
│                         │   Input Normalizer │  (统一输入格式)                   │
│                         └──────────┬──────────┘                                 │
└────────────────────────────────────┼───────────────────────────────────────────┘
                                    │
┌────────────────────────────────────▼───────────────────────────────────────────┐
│                          Agent Orchestration Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Intent    │  │   Task      │  │   Tool      │  │   Memory    │             │
│  │   Parser    │  │   Planner   │  │   Router    │  │   Manager   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘             │
└────────────────────────────────────────────────────────────────────────────────┘
                                    │
┌────────────────────────────────────▼───────────────────────────────────────────┐
│                              Tool Layer                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │  Code    │  │   Git    │  │   Web    │  │  File    │  │ Terminal │          │
│  │  Tools   │  │  Tools   │  │  Tools   │  │  Tools   │  │  Tools   │          │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │
└────────────────────────────────────────────────────────────────────────────────┘
                                    │
┌────────────────────────────────────▼───────────────────────────────────────────┐
│                              External Services                                  │
│      GitHub API        LLM API (OpenRouter/Claude)    Database   Search         │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、三种交互模式

| 模式 | 入口 | 适用场景 |
|------|------|---------|
| **CLI 交互** | 终端 `beaver` 命令 | 开发者日常使用、快速调试 |
| **WebSocket CLI** | `beaver --protocol ws` | 远程连接、嵌入 IDE |
| **消息平台** | 微信/飞书/Telegram | 移动端、团队共享 |

---

## 四、项目目录结构

```
beaver-bot/
├── config/
│   ├── settings.yaml          # 主配置（模型、API、限流）
│   └── .env.example           # 环境变量模板
├── src/
│   ├── __init__.py
│   ├── main.py                # CLI 入口 beaver run
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── adapter.py          # CLI 适配器（命令解析/补全/彩色输出）
│   │   ├── commands.py         # 内置命令（/help /exit /model）
│   │   └── interactive.py      # 交互式 REPL
│   ├── core/
│   │   ├── agent.py            # Agent 主循环
│   │   ├── intent_parser.py   # 意图识别
│   │   ├── task_planner.py    # 任务拆解
│   │   ├── tool_router.py     # 工具路由
│   │   └── memory/
│   │       ├── session.py     # 会话记忆
│   │       └── persistent.py  # 持久记忆
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── code_gen.py         # 代码生成工具
│   │   ├── code_review.py     # 代码审查工具
│   │   ├── debugger.py        # 调试助手工具
│   │   ├── github_tool.py     # GitHub API 封装
│   │   ├── file_tool.py       # 文件读写搜索
│   │   ├── terminal_tool.py   # 终端执行（安全沙箱）
│   │   └── web_tool.py        # 网页搜索/爬取
│   └── gateway/
│       ├── router.py          # 消息路由器
│       └── platforms/
│           ├── wechat.py       # 微信适配器
│           ├── telegram.py    # Telegram 适配器
│           └── github.py      # GitHub Webhook 适配器
├── tests/
├── requirements.txt
└── pyproject.toml
```

---

## 五、技术选型

| 层级 | 技术 | 理由 |
|------|------|------|
| **语言** | Python 3.11+ | 生态丰富、AI 工具成熟 |
| **LLM 调用** | OpenRouter / Claude | 统一抽象，支持多模型 |
| **Agent 框架** | 自研 | 轻量、可控、可定制 |
| **GitHub** | PyGithub / requests | 官方 API 封装 |
| **异步** | asyncio + aiohttp | 高并发消息处理 |
| **配置** | Pydantic + YAML | 类型安全、易管理 |
| **日志** | structlog | 结构化日志、便于调试 |

---

## 六、Phase 1 — 开发助手功能矩阵

| 模块 | 功能 | 说明 |
|------|------|------|
| **代码生成** | 根据描述生成代码 | 支持 Python/JS/Go/Rust 等 |
| **代码审查** | PR Review、代码质量分析 | 调用 GitHub API |
| **代码调试** | 错误分析、修复建议 | 读取日志+代码上下文 |
| **GitHub 集成** | 创建仓库、处理 Issue/PR | 已有 Token |
| **文件操作** | 读写、搜索、重构 | 本地项目目录 |
| **终端执行** | 运行命令、跑测试 | sandboxed 环境 |

---

## 七、CLI 工作流示例

```
$ beaver run

  🦫 Beaver Bot 开发助手

  > 帮助: /help
  > 退出: /exit 或 Ctrl+C

──────────────────────────────────────────────────

You: 帮我review一下 /home/user/project/main.py

Beaver: [正在分析代码...]
  ✅ 读取文件: /home/user/project/main.py (45行)
  ✅ 代码审查完成

  📝 审查结果:
  1. [警告] 第23行: 缺少空值检查
  2. [建议] 第31行: 可用列表推导式优化
  3. [优化] 第38-42行: 循环可并行化

  是否需要我直接修复？ (y/n)
```

---

## 八、Phase 1 快速启动路线

```
Week 1: 核心框架
  ├── 项目脚手架搭建
  ├── Agent 主循环实现
  ├── Tool 基础工具（文件、终端）
  └── GitHub 集成

Week 2: 开发能力
  ├── 代码生成（接入 LLM）
  ├── 代码审查流程
  └── 调试助手

Week 3: 集成测试
  ├── 本地 CLI 测试
  ├── GitHub App 集成
  └── 微信/飞书 接入
```

---

## 九、核心模块说明

### 9.1 CLI Adapter

负责解析用户输入，支持：
- 普通文本输入（直接对话）
- 命令行指令（以 `/` 开头）
- 文件路径识别（自动触发文件工具）
- 多轮对话上下文管理

### 9.2 Intent Parser

将用户输入分类为：
- `code_generation` — 请求生成代码
- `code_review` — 请求审查代码
- `debug` — 请求调试/修复
- `github_operation` — GitHub 操作
- `general_chat` — 闲聊

### 9.3 Tool Router

根据 Intent 结果，路由到对应工具链：

```
Intent          →  Tool
code_generation  →  code_gen.py + file_tool.py
code_review      →  code_review.py + github_tool.py
debug            →  debugger.py + terminal_tool.py
github_operation →  github_tool.py
```

### 9.4 Memory Manager

- **Session Memory**: 当前会话上下文（LLM context window 内）
- **Persistent Memory**: 跨会话知识（项目偏好、常见模式）

---

## 十、CLI 命令参考

| 命令 | 说明 |
|------|------|
| `beaver run` | 启动交互式 CLI |
| `beaver chat -q "<query>"` | 单次查询模式 |
| `beaver --model <model>` | 指定模型 |
| `beaver --help` | 显示帮助 |

---

## 十一、后续扩展

- **Phase 2**: 接入飞书/微信 Webhook，支持群聊对话
- **Phase 3**: 支持定时任务、CI/CD 触发、自定义工作流
- **扩展工具**: 数据库工具、API 测试工具、Docker 工具

---

## 十二、当前状态 (2026-04-28)

| 项目 | 状态 |
|------|------|
| **测试** | 70 tests passing |
| **LLM** | MiniMax-M2.7 (api.minimaxi.com/anthropic/v1/messages) |
| **CI/CD** | GitHub Actions ✓ |
| **代码质量** | Self-evolution cron (每日 09:00) |

### 模块清单

| 模块 | 文件 | 说明 |
|------|------|------|
| Intent Parser | `src/beaver_bot/core/intent_parser.py` | 用户意图识别 |
| Task Planner | `src/beaver_bot/core/task_planner.py` | 任务分解 |
| LLM Client | `src/beaver_bot/core/llm_client.py` | MiniMax/Anthropic/OpenAI |
| File Tool | `src/beaver_bot/tools/file_tool.py` | 文件操作 |
| GitHub Tool | `src/beaver_bot/tools/github_tool.py` | GitHub API |
| Code Review | `src/beaver_bot/tools/code_review.py` | 代码审查 |
| Debugger | `src/beaver_bot/tools/debugger.py` | 错误调试 |
| Terminal | `src/beaver_bot/tools/terminal_tool.py` | 命令执行 |

### 自我进化

- 定时任务: 每日 09:00
- 日志: `.evolution/log.md`
- 原则: 小步快跑，不破坏测试
