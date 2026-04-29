.PHONY: help install test lint fmt run clean run-test run-cli install-dev

# 默认目标
help:
	@echo "🦫 Beaver Bot - 开发者命令"
	@echo ""
	@echo "📦 安装相关"
	@echo "  make install          安装依赖 (创建 venv + pip install)"
	@echo "  make install-dev     安装开发依赖 (含 pytest, ruff)"
	@echo ""
	@echo "🚀 运行"
	@echo "  make run             运行交互式 CLI"
	@echo "  make run ARGS='-q \"你的问题\"'  单次查询模式"
	@echo ""
	@echo "🧪 测试"
	@echo "  make test            运行所有测试"
	@echo "  make run-test        运行测试 (watch 模式)"
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
	@echo "📚 文档"
	@echo "  make doc             查看架构文档"
	@echo ""

# 安装依赖
install:
	@echo "📦 安装依赖..."
	@if [ ! -d ".venv" ]; then python3 -m venv .venv; fi
	@.venv/bin/pip install --upgrade pip
	@.venv/bin/pip install -r requirements.txt

# 安装开发依赖
install-dev:
	@echo "📦 安装开发依赖..."
	@if [ ! -d ".venv" ]; then python3 -m venv .venv; fi
	@.venv/bin/pip install --upgrade pip
	@.venv/bin/pip install -r requirements.txt
	@.venv/bin/pip install pytest pytest-asyncio pytest-cov ruff mypy pre-commit

# 运行 CLI
run:
	@.venv/bin/python -c "import sys; sys.path.insert(0, 'src')" && .venv/bin/python -m beaver_bot.main run $(ARGS)

# 运行单次查询
query:
	@.venv/bin/python -c "import sys; sys.path.insert(0, 'src')" && .venv/bin/python -m beaver_bot.main chat $(ARGS)

# 运行测试
test:
	@PYTHONPATH=src .venv/bin/python -m pytest tests/ -v --ignore=tests/test_cli.py

# Watch 测试
run-test:
	@PYTHONPATH=src .venv/bin/python -m pytest tests/ -v --ignore=tests/test_cli.py -x

# 覆盖率报告
coverage:
	@PYTHONPATH=src .venv/bin/python -m pytest tests/ --ignore=tests/test_cli.py --cov=beaver_bot --cov-report=term-missing --cov-report=html

# Lint
lint:
	@.venv/bin/ruff check src/

# 格式化
fmt:
	@.venv/bin/ruff format src/ tests/

# 类型检查
type-check:
	@.venv/bin/mypy src/

# 清理
clean:
	@echo "🧹 清理缓存..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ *.egg-info .coverage htmlcov/ .venv/
	@echo "✅ 清理完成"

# 查看架构文档
doc:
	@cat doc/architecture.md

# 一键开发环境
dev: install-dev test
	@echo "✅ 开发环境就绪，运行测试: make test"
