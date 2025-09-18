#!/bin/bash

# 生成 HTTPS 憑證腳本

echo "🔐 生成 HTTPS 憑證..."

# 獲取本機 IP 位址
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo "📍 偵測到本機 IP: $LOCAL_IP"

# 生成前端憑證
echo "📁 生成前端憑證..."
mkdir -p frontend/certs
openssl req -x509 -newkey rsa:4096 -keyout frontend/certs/localhost-key.pem -out frontend/certs/localhost.pem -days 365 -nodes \
  -subj "/C=TW/ST=Taiwan/L=Taipei/O=Development/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,DNS:127.0.0.1,IP:127.0.0.1,IP:$LOCAL_IP"

# 生成後端憑證
echo "📁 生成後端憑證..."
mkdir -p backend/certs
openssl req -x509 -newkey rsa:4096 -keyout backend/certs/localhost-key.pem -out backend/certs/localhost.pem -days 365 -nodes \
  -subj "/C=TW/ST=Taiwan/L=Taipei/O=Development/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,DNS:127.0.0.1,IP:127.0.0.1,IP:$LOCAL_IP"

echo "✅ 憑證生成完成！"
echo ""
echo "📱 手機測試網址："
echo "   前端: https://$LOCAL_IP:5173"
echo "   後端: https://$LOCAL_IP:8000"
echo ""
echo "💡 提示："
echo "   - 手機和電腦需要在同一個 WiFi 網路"
echo "   - 手機瀏覽器會顯示安全警告，請點擊「進階」→「繼續前往」"
