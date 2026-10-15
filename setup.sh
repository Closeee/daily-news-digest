#!/bin/bash
# 每日新闻简报 · macOS 一键安装脚本
# 用法：在终端里进入本目录后执行  bash setup.sh
set -e
cd "$(dirname "$0")"

echo "======================================"
echo "  每日新闻简报 · 安装"
echo "======================================"

# 1. 检测 Python
if ! command -v python3 >/dev/null 2>&1; then
    echo ""
    echo "❌ 没检测到 python3，请先安装 Python："
    echo "   方法一（推荐）：brew install python"
    echo "   方法二：访问 https://www.python.org/downloads/ 下载 macOS 安装包"
    exit 1
fi

SYSTEM_PY="$(command -v python3)"
RUN_PY="$SYSTEM_PY"
echo ""
echo "✅ 已找到 Python：$($SYSTEM_PY --version 2>&1)"

# 2. 安装依赖
echo ""
echo "正在安装依赖（requests / beautifulsoup4 / lxml）……"
if $SYSTEM_PY -m pip install -r requirements.txt; then
    echo "✅ 依赖安装完成"
else
    echo "⚠️  系统 Python 受保护，改用虚拟环境安装……"
    $SYSTEM_PY -m venv .venv
    . .venv/bin/activate
    pip install -r requirements.txt
    RUN_PY="$(pwd)/.venv/bin/python"
    echo "✅ 依赖安装完成（已创建虚拟环境 .venv）"
fi

# 3. 运行说明
echo ""
echo "======================================"
echo "  安装完成！"
echo "======================================"
echo ""
echo "现在生成一份日报："
echo "  $RUN_PY fetch.py"
echo ""
echo "每天 08:30 自动运行（可选）："
echo "  1. 执行  crontab -e"
echo "  2. 粘贴下面这行（路径已填好）："
echo "     30 8 * * * $RUN_PY $(pwd)/fetch.py"
echo ""
echo "生成的日报在 output/ 文件夹，双击 news-*.html 用浏览器打开。"
