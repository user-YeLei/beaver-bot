.PHONY: help install init run test lint fmt type-check clean doctor

# 自动检测项目根目录
SCRIPT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_ROOT := $(SCRIPT_DIR)
export PYTHONPATH := $(PROJECT_ROOT)/src

PYTHON := $(PROJECT_ROOT)/.venv/bin/python
PIP := $(PROJECT_ROOT)/.venv/bin/pip

# 默认目标
help:
	@echo "🦫 Beaver Bot"
	@echo ""
	@echo "  make init        首次安装 (创建 .env, 安装依赖)"
	@echo "  make install     安装依赖"
	@echo "  make run         运行 CLI"
	@echo "  make test        运行测试"
	@echo "  make lint        代码检查"
	@echo "  make fmt         格式化代码"
	@echo "  make type-check  类型检查"
	@echo "  make doctor      环境检查"
	@echo "  make clean       清理缓存"
	@echo ""
	@echo "  make dev         快速开发 (安装 + 测试)"

# ── 安装 ─────────────────────────────────────────────

install:
	@echo "📦 安装依赖..."
	@if [ ! -f "$(PROJECT_ROOT)/pyproject.toml" ]; then \
		echo "❌ pyproject.toml not found"; exit 1; \
	fi
	@if [ ! -d "$(PROJECT_ROOT)/.venv" ]; then \
		echo "  创建虚拟环境..."; \
		python3 -m venv .venv; \
	fi
	@$(PIP) install --upgrade pip
	@$(PIP) install -e .

# 首次设置
init: install
	@if [ ! -f "$(PROJECT_ROOT)/.env" ]; then \
		echo "⚙️  创建 .env 配置文件..."; \
		cp .env.example .env; \
		echo ""; \
		echo "⚠️  请编辑 .env 填入你的 API Key:"; \
		echo "   nano .env"; \
	else \
		echo "✅ .env 已存在"; \
	fi
	@$(PYTHON) -c "import beaver_bot" 2>/dev/null || { \
		echo ""; \
		echo "❌ 安装失败，请检查错误信息"; \
		exit 1; \
	}
	@echo "✅ 安装完成"

# ── 运行 ─────────────────────────────────────────────

run:
	@$(PYTHON) -m beaver_bot.main run $(ARGS)

# ── 测试 ─────────────────────────────────────────────

test:
	@$(PYTHON) -m pytest tests/ -v --ignore=tests/test_cli.py

# ── 代码质量 ─────────────────────────────────────────

lint:
	@$(PYTHON) -m ruff check src/

fmt:
	@$(PYTHON) -m ruff format src/ tests/

type-check:
	@$(PYTHON) -m mypy src/

# ── 环境检查 ─────────────────────────────────────────

doctor:
	@echo "🔍 环境检查..."
	@echo ""
	@echo "Python:"
	@$(PYTHON) --version
	@echo ""
	@echo "已安装的包:"
	@$(PIP) list --format=freeze | grep -E "^(typer|rich|pydantic|pytest)" || true
	@echo ""
	@echo "配置文件:"
	@[ -f .env ] && echo "  ✅ .env 存在" || echo "  ⚠️  .env 不存在 (make init)"
	@[ -f config/settings.yaml ] && echo "  ✅ config/settings.yaml 存在" || echo "  ❌ config/settings.yaml 不存在"
	@echo ""
	@echo "API Key 检查:"
	@grep -q "MINIMAX_API_KEY=your" .env 2>/dev/null && echo "  ⚠️  请编辑 .env 填入真实 API Key" || \
		grep -q "MINIMAX_API_KEY=" .env && echo "  ✅ MINIMAX_API_KEY 已配置" || echo "  ⚠️  MINIMAX_API_KEY 未设置"

# ── 清理 ─────────────────────────────────────────────

clean:
	@echo "🧹 清理缓存..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ .coverage htmlcov/
	@echo "✅ 清理完成"

# ── 快速开发 ─────────────────────────────────────────

dev: install test
	@echo "✅ 开发环境就绪"
