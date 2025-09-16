本說明：如何在本機測試語音辨識功能

前提：
- 建議使用 Chrome（或 Chromium-based）以獲得最穩定的 Web Speech API 支援。Safari 在部分版本有支援，但行為可能不同。
- 開發伺服器以 HTTP 或 HTTPS 啟動皆可；Chrome 允許在未使用 HTTPS 的情況下使用麥克風，但部分瀏覽器可能需要 HTTPS。

啟動開發伺服器：

使用 npm:

```bash
npm install
npm run dev
```

或使用 yarn:

```bash
yarn
yarn dev
```

測試語音辨識：
1. 在支援的瀏覽器中打開開發伺服器（預設 http://localhost:5173 或終端輸出顯示的網址）。
2. 頁面底部會有一顆非常大的紅色按鈕：「開始偵測」或「停止」。
3. 第一次使用時，瀏覽器會彈出要求麥克風權限的提示，請允許。若未出現可在瀏覽器設定中手動允許本網站使用麥克風。
4. 開啟後，以普通說話音量說話，辨識結果會出現在上方的 "語音辨識" 區塊中。該區塊也有 `aria-live` 屬性，能讓螢幕朗讀器讀出最新結果。

注意事項：
- 若看到按鈕顯示「不支援」，表示瀏覽器沒有可用的 SpeechRecognition（webkitSpeechRecognition 或 SpeechRecognition）。請改用 Chrome/Edge。
- 若辨識不穩定，請檢查麥克風權限與系統輸入設備設定。Chrome 的實驗性/隱藏旗標可能影響行為。
- 本功能使用 Web Speech API，依賴使用者瀏覽器實作，並非後端服務。

回報問題：
請將瀏覽器名稱、版本、以及出現問題時的 console 訊息貼上，以便除錯。