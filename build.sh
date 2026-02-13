#!/usr/bin/env bash
# ============================================================
# Render Build Script — AI News Aggregator
# 在 Render 部署时自动执行, 也可本地手动运行
# ============================================================
set -o errexit   # 任何命令失败立即退出
set -o pipefail  # 管道中的命令失败也退出

echo "==> Installing Python dependencies..."
cd backend
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

echo "==> Copying frontend assets into backend..."
# FastAPI 期望 frontend/ 目录在 backend/ 下面 (BASE_DIR/frontend)
rm -rf ./frontend
cp -r ../frontend ./frontend

echo "==> Build complete!"
