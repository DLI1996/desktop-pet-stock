#!/bin/zsh
# 打包：生成可独立运行的 牛来行情桌宠.app（无需 Python 环境）
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  command -v uv >/dev/null 2>&1 || { echo "请先安装 uv: brew install uv"; exit 1; }
  uv venv --python 3.12 .venv
  uv pip install --require-hashes -p .venv/bin/python -r requirements.txt
fi

./build_app.sh
