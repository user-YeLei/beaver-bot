.PHONY: help install test lint fmt run clean run-test install-dev

# 自动检测项目根目录
SCRIPT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_ROOT := $(SCRIPT_DIR)
export PYTHONPATH := $(PROJECT_ROOT)/src

# 帮助信息
help:
	@echo "🦫 Beaver Bot - 开发者命令"
	@echo ""
	@echo "📦 安装相关"
	@echo "  make install          安装依赖 (创建 venv + pip install)"
	@echo "  make install-dev     安装开发依赖 (含 pytest, ruff)"
	@echo ""
	@echo "🚀 运行"
	@echo "  make run             运行交互式 CLI"
	@echo "  make query ARGS='-q \"问题\"'  单次查询模式"
	@echo ""
	@echo "🧪 测试"
	@echo "  make test            运行所有测试"
	@echo "  make coverage        生成覆盖率报告"
	@echo ""
	@echo "🔍 代码质量"
	@echo "  make lint            运行 ruff 检查"
	@echo "  make fmt             自动格式化代码"
	@echo "  make type-check      运行 mypy 类型检查"
	@echo ""
	@echo "🧹 清理"
	@echo "  make clean           清理缓存和构建产物"
	@echo ""

# 安装依赖
install:
	@cd $(PROJECT_ROOT) && \
	if [ ! -d ".venv" ]; then python3 -m venv .venv; fi && \
	.venv/bin/pip install --upgrade pip && \
	.venv/bin/pip install -r requirements.txt

# 安装开发依赖
install-dev:
	@cd $(PROJECT_ROOT) && \
	if [ ! -d ".venv" ]; then python3 -m venv .venv; fi && \
	.venv/bin/pip install --upgrade pip && \
	.venv/bin/pip install -r requirements.txt && \
	.venv/bin/pip install pytest pytest-asyncio pytest-cov ruff mypy pre-commit

# 运行 CLI
run:
	@cd $(PROJECT_ROOT) && \
	.venv/bin/python -m beaver_bot.main run $(ARGS)

# 运行单次查询
query:
	@cd $(PROJECT_ROOT) && \
	.venv/bin/python -m beaver_bot.main chat $(ARGS)

# 运行测试
test:
	@cd $(PROJECT_ROOT) && \
	PYTHONPATH=src .venv/bin/python -m pytest tests/ -v --ignore=tests/test_cli.py

# 覆盖率报告
coverage:
	@cd $(PROJECT_ROOT) && \
	PYTHONPATH=src .venv/bin/python -m pytest tests/ --ignore=tests/test_cli.py --cov=beaver_bot --cov-report=term-missing --cov-report=html

# Lint
lint:
	@cd $(PROJECT_ROOT) && \
	.venv/bin/ruff check src/

# 格式化
fmt:
	@cd $(PROJECT_ROOT) && \
	.venv/bin/ruff format src/ tests/

# 类型检查
type-check:
	@cd $(PROJECT_ROOT) && \
	.venv/bin/mypy src/

# 清理
clean:
	@cd $(PROJECT_ROOT) && \
	echo "🧹 清理缓存..." && \
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true && \
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true && \
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true && \
	rm -rf build/ dist/ *.egg-info .coverage htmlcov/ .venv/ && \
	echo "✅ 清理完成"

# 一键开发环境
dev: install-dev test
	@echo "✅ 开发环境就绪"
