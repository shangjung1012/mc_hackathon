# MC Hackathon 後端使用者系統

## 功能特色

- ✅ PostgreSQL 資料庫 (Docker)
- ✅ pgAdmin 管理介面
- ✅ 使用者註冊/登入
- ✅ JWT 認證
- ✅ 密碼雜湊
- ✅ 使用者 CRUD 操作
- ✅ Alembic 資料庫遷移

## 快速啟動

### 方法一：使用啟動腳本
```bash
./start-backend.sh
```

### 方法二：手動啟動

1. 啟動資料庫服務
```bash
docker-compose up -d
```

2. 進入後端目錄並安裝依賴
```bash
cd backend
uv sync
```

3. 執行資料庫遷移
```bash
uv run alembic revision --autogenerate -m "Create users table"
uv run alembic upgrade head
```

4. 啟動後端服務
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 服務端點

- **後端 API**: http://localhost:8000
- **API 文件**: http://localhost:8000/docs
- **pgAdmin**: http://localhost:8080
  - 帳號: admin@admin.com
  - 密碼: admin

## API 端點

### 使用者相關
- `POST /users/register` - 註冊新使用者
- `POST /users/login` - 使用者登入
- `GET /users/me` - 獲取當前使用者資訊
- `GET /users/` - 獲取使用者列表
- `GET /users/{user_id}` - 根據 ID 獲取使用者
- `PUT /users/{user_id}` - 更新使用者資訊
- `DELETE /users/{user_id}` - 刪除使用者

### 其他
- `GET /health` - 健康檢查
- `POST /gemini/chat` - Gemini AI 聊天
- `POST /tts/synthesize` - 文字轉語音

## 資料庫連線資訊

- **主機**: localhost
- **埠號**: 5432
- **資料庫**: mc_hackathon
- **使用者**: postgres
- **密碼**: postgres

## 環境變數

可以在 `.env` 檔案中設定以下變數：

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mc_hackathon
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 測試 API

### 註冊使用者
```bash
curl -X POST "http://localhost:8000/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpassword",
    "full_name": "Test User"
  }'
```

### 登入
```bash
curl -X POST "http://localhost:8000/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpassword"
  }'
```

### 獲取使用者資訊 (需要認證)
```bash
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```
