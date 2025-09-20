#!/bin/bash

echo "🚀 啟動 MC Hackathon 後端服務..."

# 啟動 PostgreSQL 和 pgAdmin
echo "📦 啟動 Docker 服務..."
docker-compose up -d

# 等待 PostgreSQL 啟動
echo "⏳ 等待 PostgreSQL 啟動..."
sleep 10

# 進入後端目錄
cd backend

# 安裝依賴
echo "📥 安裝 Python 依賴..."
uv sync

# 執行資料庫遷移
echo "🗄️ 執行資料庫遷移..."
uv run alembic revision --autogenerate -m "Create users table"
uv run alembic upgrade head

# 創建管理員帳號
echo "👤 創建管理員帳號..."
uv run python -c "from app.core.init_admin import create_admin_user; create_admin_user()"

# 啟動後端服務
echo "🎯 啟動 FastAPI 服務..."
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
