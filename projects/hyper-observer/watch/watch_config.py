"""哨兵專屬門檻（與 hyper-observer/config.py 分開，避免動到每日班的行為）。

刻意放在 watch/ 底下而不是 projects/hyper-observer/：
hyper-observer.yml 的 paths 過濾是 `projects/hyper-observer/*.py`（單層），
放這裡就不會每次調哨兵參數都觸發那支重量級的每日班。
"""

# 輪詢頻率（只用於訊息文案與 cron 註解；真正的排程在 .github/workflows/hyper-watch.yml）
WATCH_INTERVAL_MINUTES = 10

# 倉位大小變化達此比例才算「加倉／減倉」。
# 為什麼是 20%：實測追蹤錢包在 xyz 用分批進出（單批常 <10% 倉位），若門檻太低會
# 把「同一個決策的分批執行」拆成好幾則通知——那是雜訊，不是新資訊。
WATCH_SIZE_CHANGE_PCT = 0.20

# 同一部位（dex|coin|side）的加減倉通知冷卻時間（分鐘）。
# 新開倉／平倉**不受**冷卻限制：那是真事件，寧可多吵一次也不能漏。
WATCH_COOLDOWN_MINUTES = 60

# 冷卻紀錄保留天數（狀態檔體積控制；超過就沒有壓制意義了）
WATCH_ALERT_TTL_DAYS = 3

# 單則訊息最多列幾個變動，超過的折成一行「另有 N 個變動」。
# 避免他一次大調倉時 Telegram 收到超長訊息（>4096 字會被截斷）。
WATCH_MAX_EVENTS_PER_MESSAGE = 12

# 是否查 builder dex（False → 只看原生，會重現 xyz 盲點，僅供除錯）
WATCH_FETCH_DEXS = True
# 每次輪詢最多查幾個 builder dex。
# 成本：每錢包 (1 + N) 個 clearinghouseState 請求 × 權重 2。
# 3 個 tracked × (1+10) × 2 = 66 權重／次，10 分鐘一次 ≈ 400 權重／小時
# （限額 1200 權重／分鐘），可忽略。
WATCH_MAX_DEXS = 10
