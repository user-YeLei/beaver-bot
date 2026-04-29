#!/bin/bash
# Beaver Bot 一键安装脚本

set -e

echo "🦫 Beaver Bot 安装中..."

# 检测操作系统
OS=$(uname -s)
if [ "$OS" = "Linux" ]; then
    PYTHON_CMD=${PYTHON_CMD:-python3}
elif [ "$OS" = "Darwin" ]; then
    PYTHON_CMD=${PYTHON_CMD:-python3}
else
    PYTHON_CMD=${PYTHON_CMD:-python}
fi

# 检查 Python 版本
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$PYTHON_VERSION" != "3.11" ] && [ "$PYTHON_VERSION" != "3.12" ] && [ "$PYTHON_VERSION" != "3.13" ]; then
    echo "⚠️  警告: 推荐 Python 3.11+，当前版本: $PYTHON_VERSION"
fi

# 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    $PYTHON_CMD -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 升级 pip
echo "⬆️  升级 pip..."
pip install --upgrade pip

# 安装依赖
echo "📥 安装依赖..."
pip install -r requirements.txt

# 复制环境变量文件
if [ ! -f ".env" ]; then
    echo "⚙️  创建 .env 配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件填入你的 API Key"
fi

# 安装 pre-commit hooks (可选)
if command -v pre-commit &> /dev/null; then
    echo "🔧 安装 pre-commit hooks..."
    pip install pre-commit
    pre-commit install || true
fi

echo ""
echo "✅ 安装完成！"
echo ""
echo "请先编辑 .env 文件填入 API Key，然后运行："
echo ""
echo "  source .venv/bin/activate"
echo "  beaver run"
echo ""
echo "或者一键启动："
echo ""
echo "  source .venv/bin/activate && beaver run"
echo ""
