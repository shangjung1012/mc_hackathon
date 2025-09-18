#!/bin/bash

# 啟動 HTTPS 開發環境腳本

echo "🚀 啟動 HTTPS 開發環境..."

# 檢查憑證是否存在
if [ ! -f "frontend/certs/localhost.pem" ] || [ ! -f "backend/certs/localhost.pem" ]; then
    echo "❌ 憑證檔案不存在，請先執行 generate-certs.sh"
    exit 1
fi

# 啟動後端 HTTPS
echo "🔧 啟動後端 HTTPS (port 8000)..."
cd backend
make dev-https &
BACKEND_PID=$!

# 等待後端啟動
sleep 3

# 啟動前端 HTTPS
echo "🎨 啟動前端 HTTPS (port 5173)..."
cd ../frontend
npm run dev:https &
FRONTEND_PID=$!

echo "✅ 服務已啟動！"
echo "📱 前端: https://localhost:5173"
echo "🔧 後端: https://localhost:8000"
echo ""
echo "⚠️  注意："
echo "   - 瀏覽器會顯示「不安全」警告，請點擊「進階」→「繼續前往」"
echo "   - 手機測試時，請使用電腦的 IP 位址（如 https://192.168.1.100:5173）"
echo ""
echo "按 Ctrl+C 停止所有服務"

# 等待用戶中斷
trap "echo '🛑 停止服務...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
