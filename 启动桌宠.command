#!/bin/zsh
# 双击启动：自动准备环境并启动牛来行情桌宠（macOS 版，无黑窗残留）
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "首次运行：正在准备环境（约 1-2 分钟）..."
  command -v uv >/dev/null 2>&1 || { osascript -e 'display notification "请先安装 uv: brew install uv" with title "牛来行情桌宠"'; exit 1; }
  uv venv --python 3.12 .venv >/dev/null 2>&1
  uv pip install -p .venv/bin/python -r requirements.txt >/dev/null 2>&1
fi

exec .venv/bin/python app.py
