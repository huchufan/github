#!/bin/bash
# Hermes 系统初始化和自动生成脚本
# 设计文档: 12_设计方案落地执行指南.md
set -e

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "🚀 Hermes 系统框架初始化..."

# 1. 创建所有框架目录
echo "📁 创建框架目录结构..."
mkdir -p agent/{governance,orchestration,memory,automation,evolution,multiagent}/{core,tests,utils}
for framework in governance orchestration memory automation evolution multiagent; do
  touch agent/$framework/__init__.py
  touch agent/$framework/core/__init__.py
  touch agent/$framework/tests/__init__.py
done

# 2. 使用模块生成器为清单中的模块生成基础代码
echo "🛠️ 生成模块基础代码..."
if [ -f tools/MODULE_MANIFEST.json ]; then
  python3 - <<'PY'
import json, subprocess, sys
with open("tools/MODULE_MANIFEST.json") as f:
    manifest = json.load(f)
for fw, info in manifest["frameworks"].items():
    for mod in info["modules"]:
        subprocess.run([sys.executable, "tools/generators/module_generator.py", fw, mod], check=False)
PY
fi

# 3. 运行测试验证
echo "🧪 运行测试验证..."
python3 -m pytest agent/ -q

echo ""
echo "✅ 初始化完成！"
echo ""
echo "下一步:"
echo "1. 启动各框架开发"
echo "2. 运行 pytest 验证"
echo "3. 每日运行本脚本以生成新模块"
