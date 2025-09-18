# HTTPS 設定說明

本專案已配置支援 HTTPS，解決手機相機功能需要 HTTPS 的問題。

## 快速開始

### 1. 生成憑證
```bash
./generate-certs.sh
```

### 2. 啟動 HTTPS 服務
```bash
./start-https.sh
```

## 手動啟動

### 前端 HTTPS
```bash
cd frontend
npm run dev:https
```
前端將在 `https://localhost:5173` 運行

### 後端 HTTPS
```bash
cd backend
make dev-https
```
後端將在 `https://localhost:8000` 運行

## 手機測試

1. 確保手機和電腦在同一 WiFi 網路
2. 查看電腦的 IP 位址（腳本會自動顯示）
3. 在手機瀏覽器訪問：
   - 前端：`https://[電腦IP]:5173`
   - 後端：`https://[電腦IP]:8000`

## 瀏覽器安全警告

由於使用自簽憑證，瀏覽器會顯示安全警告：

### Chrome/Edge
1. 點擊「進階」
2. 點擊「繼續前往 localhost（不安全）」

### Safari
1. 點擊「顯示詳細資料」
2. 點擊「訪問此網站」

### Firefox
1. 點擊「進階」
2. 點擊「接受風險並繼續」

## 故障排除

### 憑證問題
如果遇到憑證錯誤，重新生成憑證：
```bash
rm -rf frontend/certs backend/certs
./generate-certs.sh
```

### 端口被佔用
如果端口被佔用，可以修改配置：
- 前端：修改 `vite.config.ts` 中的 `port`
- 後端：修改 `Makefile` 中的 `--port`

### 手機無法連接
1. 檢查防火牆設定
2. 確認 IP 位址正確
3. 嘗試使用電腦的實際 IP 而非 localhost

## 生產環境

生產環境建議使用：
1. Let's Encrypt 憑證
2. 反向代理（如 Nginx）
3. 域名配置

## 注意事項

- 自簽憑證僅適用於開發環境
- 每次重新生成憑證後需要重新啟動服務
- 手機測試時需要手動接受安全警告
