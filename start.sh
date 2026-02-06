#!/bin/bash

# AI News Aggregator 启动脚本

echo "🚀 正在启动 AI News Aggregator..."
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ 错误: Docker 未运行"
    echo ""
    echo "请按以下步骤操作："
    echo "1. 打开 Finder"
    echo "2. 进入 应用程序 文件夹"
    echo "3. 找到并双击 'Docker' 应用"
    echo "4. 等待 Docker Desktop 完全启动（菜单栏图标显示为运行状态）"
    echo "5. 然后再次运行此脚本: ./start.sh"
    echo ""
    echo "或者手动运行: docker-compose up -d"
    exit 1
fi

echo "✅ Docker 正在运行"
echo ""

# 启动所有服务
cd "$(dirname "$0")"
echo "📦 正在启动服务容器..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ 启动失败，请检查错误信息"
    exit 1
fi

echo ""
echo "⏳ 等待服务启动..."
sleep 8

# 检查服务状态
echo ""
echo "📊 服务状态:"
docker-compose ps

echo ""
echo "✅ 项目已启动！"
echo ""
echo "🌐 访问地址:"
echo "   📱 Web 界面: http://localhost:8000"
echo "   📚 API 文档: http://localhost:8000/api/docs"
echo "   🔧 交互式 API: http://localhost:8000/api/redoc"
echo ""
echo "💡 常用命令:"
echo "   查看日志: docker-compose logs -f"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart"
echo ""
