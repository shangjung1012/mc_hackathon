# MC Hackathon – Smart Shelf MVP

快速上手指南：前端使用 Vue + Vite + TypeScript + TailwindCSS；後端使用 FastAPI（以 uv 啟動）。支援手機瀏覽器（Android Chrome）測試。

## 專案結構

```
backend/   # FastAPI with uv
frontend/  # Vue + Vite + TS + TailwindCSS
```

## 需求環境

- Node.js 18+（含 npm）
- Python 3.9+
- uv（Python 包管理/執行器）：`curl -LsSf https://astral.sh/uv/install.sh | sh`

---

## 前端（npm）

目錄：`frontend/`

1) 安裝依賴

```
cd frontend
npm ci
```

2) 開發啟動（本機）

```
npm run dev
```

Vite 會在 `http://localhost:5173/` 啟動。

3) 同網段手機測試（Android Chrome）

```
# 於 macOS 取得本機 IP（Wi‑Fi）
ipconfig getifaddr en0

# 使用 0.0.0.0 對外綁定
npm run dev -- --host 0.0.0.0
```

在手機瀏覽器開啟：`http://<你的電腦IP>:5173/`。

---

## 後端（uv）

目錄：`backend/`

1) 安裝依賴（會讀取 `pyproject.toml`）

```
cd backend
uv sync
```

2) 開發啟動（FastAPI + Uvicorn）

```
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

健康檢查：`http://127.0.0.1:8000/health` 應回傳：`{"status":"ok"}`。

（或使用 Makefile 快速啟動）

```
make dev
```

3) 手機測試後端

手機與電腦在同一個 Wi‑Fi 下，於手機瀏覽器開啟：

```
http://<你的電腦IP>:8000/health
```

---

## CORS 與本機端點

目前後端已開放以下前端開發來源：
- `http://localhost:5173`
- `http://127.0.0.1:5173`

若你以手機 IP 存取前端（例如 `http://192.168.x.x:5173`），如需從前端直接呼叫後端，也請在 `backend/main.py` 的 `allow_origins` 補上你的前端實際網址（含協定與埠號）。

---

## 常見問題（FAQ）

- 端口占用：5173（前端）、8000（後端）若被占用，請更換埠或關閉其他服務。
- 權限/證書：行動裝置連線需與電腦同網段；若公司網路有隔離策略，請改用 USB 調試或熱點。
- Node/Python 版本：若安裝失敗，先確認 Node 18+、Python 3.9+，並清理快取後重試（npm: `npm ci`；uv: `uv clean` + `uv sync`）。

---

## 後續開發（Roadmap）

- PWA（manifest + service worker）
- 相機拍照（MediaDevices）、長按語音（Web Speech API）
- TTS 播報、震動回饋
- 後端串接 Google Gemini（多模態 + OCR）與追問能力

如需協作，請開分支並提交 PR；程式碼風格請遵循專案預設格式與 TypeScript 嚴格型別。
