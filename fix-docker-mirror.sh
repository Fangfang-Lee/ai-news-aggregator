#!/bin/bash

# 修复 Docker 镜像源问题的脚本

echo "🔧 正在修复 Docker 镜像源配置..."

# 备份原配置
if [ -f ~/.docker/daemon.json ]; then
    cp ~/.docker/daemon.json ~/.docker/daemon.json.backup
    echo "✅ 已备份原配置到 ~/.docker/daemon.json.backup"
fi

# 创建临时配置，移除镜像源（使用官方 Docker Hub）
cat > ~/.docker/daemon.json << 'EOF'
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false
}
EOF

echo "✅ 已更新 Docker 配置（移除镜像源，使用官方 Docker Hub）"
echo ""
echo "⚠️  请重启 Docker Desktop 以使配置生效："
echo "   1. 点击菜单栏的 Docker 图标"
echo "   2. 选择 'Quit Docker Desktop'"
echo "   3. 重新启动 Docker Desktop"
echo "   4. 等待 Docker 完全启动后，再次运行 ./start.sh"
echo ""
