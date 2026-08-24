#!/bin/zsh
# 打包：生成 dist/牛来行情桌宠.app
# 策略：将项目（含 .venv）复制进 .app，Launcher 直接调用内置 venv。
cd "$(dirname "$0")"
set -e

if [ ! -d .venv ]; then
  echo "首次运行：正在准备环境..."
  command -v uv >/dev/null 2>&1 || { echo "请先安装 uv: brew install uv"; exit 1; }
  uv venv --python 3.12 .venv
  uv pip install --require-hashes -p .venv/bin/python -r requirements.txt
fi

APP="dist/牛来行情桌宠.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

# 复制项目（排除 dist/logs）
rsync -a --exclude dist --exclude logs --exclude .DS_Store ./ "$APP/Contents/Resources/"

# macOS 需要 app 目录结构可执行
chmod +x "$APP/Contents/Resources/.venv/bin/"*

cat > "$APP/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>牛来行情桌宠</string>
  <key>CFBundleDisplayName</key><string>牛来行情桌宠</string>
  <key>CFBundleIdentifier</key><string>cn.niulai.pet</string>
  <key>CFBundleVersion</key><string>1.0.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>LSUIElement</key><true/>
</dict>
</plist>
EOF

cat > "$APP/Contents/MacOS/牛来行情桌宠" <<'EOF'
#!/bin/zsh
DIR="$(cd "$(dirname "$0")" && pwd)/../Resources"
cd "$DIR"
exec "$DIR/.venv/bin/python" app.py
EOF
chmod +x "$APP/Contents/MacOS/牛来行情桌宠"

echo "打包完成：dist/牛来行情桌宠.app"
osascript -e "display notification \"打包完成，可在 dist 目录找到 牛来行情桌宠.app\" with title \"牛来行情桌宠\""
