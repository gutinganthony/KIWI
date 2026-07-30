# EMA20/50 交叉策略回測

實測使用者指定的趨勢跟隨策略，標的為 BTC、ETH 與 Nasdaq 成分股。

## 策略定義（原樣實作，不加任何濾網）

- EMA20 由下往上穿越 EMA50（黃金交叉）→ 全額做多，weight = 1
- EMA20 由上往下穿越 EMA50（死亡交叉）→ 出場
- 只做多、不放空、無停損、無部位控制

## 檔案

| 檔案 | 作用 |
|---|---|
| `ema_backtest.py` | 回測引擎（純函式，不碰網路）：EMA、交叉訊號、逐棒模擬、績效指標 |
| `run_report.py` | 讀價格 CSV → 產出 1/3/6/12/24 個月績效表與跨標的彙總 |
| `fetch_prices.py` | 取數（**必須在 GitHub Actions runner 上跑**，見下） |
| `tests/test_offline.py` | 離線測試，41 項斷言，含正向案例 |
| `results/` | workflow 產出的回測結果（三個變體：零成本／10bps／收盤成交） |
| `sensitivity.py` | 敏感度檢查：成本、成交時點、資料起點處理對結論的影響 |
| **`FINDINGS.md`** | **實測結論——先看這份** |

## 為什麼取數要跑在 GitHub Actions 上

Claude 雲端 session 的 agent proxy 對**所有**行情源一律 CONNECT 403——
實測 Yahoo（query1/query2）、stooq（連 SHA-256 PoW 都解了仍回 Access denied）、
coingecko、binance、tiingo、nasdaqtrader、FRED 全部不通，yfinance 套件同樣被擋。
runner 不受此限，與 `projects/avi-v5/scripts/fetch_backtest_ext.py` 是同一套資料橋模式。

`.github/workflows/ema-backtest.yml` 只在 research 分支觸發、只寫
`projects/ema-backtest/results/`，不與 main 的 6 支生產管線共用任何路徑。

## 本機跑法（若要跳過 workflow）

```bash
pip install yfinance pandas numpy lxml requests
cd projects/ema-backtest
python3 tests/test_offline.py
python3 fetch_prices.py --universe ndx100 --out /tmp/prices --start 2018-01-01
python3 run_report.py --prices /tmp/prices --out results --tag results_cost0 --top 25
```

## 方法學上的取捨（會影響數字怎麼讀）

1. **成交假設**：訊號在第 t 根收盤確認 → 第 t+1 根**開盤價**成交。
   這是避免 look-ahead bias 的保守設定。`--fill close`（當根收盤成交）
   是常見但偏樂觀的做法，兩者差距由 `results_closefill` 量化。
2. **成本**：規格未指定成本。`results_cost0` 是規格原樣（零成本，紙上績效），
   `results_cost10` 加單邊 10 bps（手續費＋滑價）。真實可執行性看後者。
3. **除權息**：一律用 auto_adjust 後的 OHLC，開盤與收盤同一基準。
4. **資料起點邊界**：warm-up（前 50 根）結束時若已是多頭排列，視為一次進場，
   否則結果會取決於資料從哪天開始。回測窗距樣本起點 5 年以上，此設定不影響
   1–24 個月的報酬數字。
5. **視窗覆蓋率**：資料起點晚於窗起點的標的，該窗直接留空，
   不把「上市至今」偽裝成「過去 24 個月」。
6. **存活者偏差（未消除，讀數字時必須扣分）**：用**今天**的 Nasdaq-100
   成分股回測過去 24 個月，被剔除的輸家不在清單裡，會系統性高估買入持有
   與策略兩邊的報酬。跨標的比較（策略 vs 買入持有）受影響較小，
   但「絕對報酬」不可當作可實現預期。
