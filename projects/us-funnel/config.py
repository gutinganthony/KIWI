"""us-funnel 集中設定：EDGAR Form 4 三層漏斗（資格→否決→等權評分）與前瞻表現追蹤。

純唯讀研究管線。此專案不包含任何下單、券商 API、簽章、金鑰功能，
所有請求皆為免金鑰的公開唯讀查詢：
- GET https://www.sec.gov/Archives/edgar/daily-index/...（Form 4 每日索引）
- GET https://www.sec.gov/Archives/edgar/data/...（單筆 filing 全文，含 ownershipDocument XML）
- GET https://stooq.com/q/d/l/...（免費日線 CSV，前瞻表現與流動性估算）

設計依據：topics/business/2026-07-10-us-tw-signal-funnel-design.md §1（三層定稿）與
topics/business/2026-07-10-stock-signal-appendix/stock_signal_form4.md（訊號細節）。
"""

# ---------------------------------------------------------------------------
# HTTP 共通參數
# ---------------------------------------------------------------------------

HTTP_TIMEOUT = 30            # 每請求 timeout（秒）
HTTP_RETRIES = 2             # 失敗後重試次數（不含首次）
HTTP_BACKOFFS = [1, 3]       # 第 1 / 2 次重試前的等待秒數
ERROR_BODY_SNIPPET_LEN = 200  # 端點失敗時記錄 body 前 N 字

# ---------------------------------------------------------------------------
# EDGAR 端點與禮儀（SEC fair access policy——規定，不是建議）
# https://www.sec.gov/os/accessing-edgar-data：
#   1. User-Agent 必須含可聯絡的 email（缺 UA 直接 403）。
#   2. 限速 ≤10 requests/秒，超速封鎖 10 分鐘。
# 本管線每請求間 sleep EDGAR_SLEEP_BETWEEN=0.15s（≈6.7 req/s，含網路延遲實際更低），
# 留足餘裕、絕不並行請求。
# ---------------------------------------------------------------------------

EDGAR_USER_AGENT = "KIWI-research kiwi-observer@example.com"
EDGAR_SLEEP_BETWEEN = 0.15   # 每請求間隔（秒）；0.15s ≈ 6.7 req/s < 10 req/s 上限

# 每日索引（按 form type 排序版）：form.{YYYYMMDD}.idx，只在該日有申報時存在（週末/假日 404）
EDGAR_DAILY_INDEX_URL = (
    "https://www.sec.gov/Archives/edgar/daily-index/{year}/QTR{quarter}/form.{yyyymmdd}.idx"
)
# 索引內 File Name 欄（edgar/data/{cik}/{accession}.txt）拼上此 base 即為 filing 全文 URL
EDGAR_ARCHIVES_BASE = "https://www.sec.gov/Archives/"

# 索引「日結」邊界：EDGAR 收件到美東 22:00（EDT=02:00 UTC / EST=03:00 UTC）。
# 某日的 daily index 在次日 03:15 UTC 之後視為完整；在此之前抓到的存檔標記
# incomplete，下次執行會重抓。CI cron 定在 03:30 UTC 正是為了落在此邊界之後。
INDEX_COMPLETE_UTC_HOUR = 3
INDEX_COMPLETE_UTC_MINUTE = 15

# ---------------------------------------------------------------------------
# 掃描窗口與事件存檔
# ---------------------------------------------------------------------------

SCAN_WINDOW_DAYS = 7          # 集群滾動窗＝漏斗掃描窗（日曆日）
INDEX_LOOKBACK_DAYS = 10      # 往回掃的日曆日數（涵蓋週末假日，湊滿 ~7 個申報日）
MAX_FILINGS_PER_DAY = 4000    # 單日 filing 抓取安全上限（實務高峰 ~3000）
EVENT_RETENTION_DAYS = 14     # data/events/ 事件檔保留天數，過期自動刪除（控 repo 體積）

# 無效 ticker 值（issuerTradingSymbol 缺漏時 EDGAR 常見填法）——無法定價/追蹤，略過
INVALID_TICKERS = {"", "NONE", "N/A", "NA"}

# ---------------------------------------------------------------------------
# 第一層｜資格關卡（進場券，不是 alpha 排名）
# ---------------------------------------------------------------------------

QUALIFY_TRANSACTION_CODE = "P"   # 只認公開市場自主買入（transactionCode=P）
# 10b5-1 checkbox（aff10b5One，2023-04 起強制）勾選＝計畫單，一律排除（資格關卡）
CLUSTER_MIN_INSIDERS = 2         # 7 日窗內同 issuer ≥2 名不同 reportingOwner 買入才成群

# ---------------------------------------------------------------------------
# 第二層｜否決關卡（一票否決）
# ---------------------------------------------------------------------------

VETO_MIN_PRICE_USD = 1.0             # 仙股排除：集群買入 VWAP < $1 → 否決（操縱紅旗 v0 從簡）
VETO_SELL_TO_BUY_RATIO = 0.5         # 同窗同 issuer 內部人賣出額 > 買入額 × 此比例 → 否決
VETO_MIN_AVG_DOLLAR_VOLUME = 200_000.0  # 近 20 交易日日均成交額（close×volume）下限（USD）；
                                        # 刻意設低——保留小市值 alpha 帶（設計檔 §1 第二層）
DOLLAR_VOLUME_LOOKBACK_DAYS = 20     # 日均成交額回看交易日數
# 價格源抓不到時：流動性檢查跳過（不否決）、記進 meta.skipped_checks——寧可放行待人工複核，
# 不因數據源故障讓漏斗空轉

# ---------------------------------------------------------------------------
# 第三層｜等權評分（每項 0–2 分，等權加總——DeMiguel 2009：本樣本量下等權唯一有據）
# ---------------------------------------------------------------------------

SCORE_CLUSTER_STRONG = 3             # 集群人數 ≥3 → 2 分；=2 → 1 分
SCORE_BUY_USD_BAND_1 = 100_000.0     # 集群買入總額 ≥ $100k → 1 分
SCORE_BUY_USD_BAND_2 = 500_000.0     # ≥ $500k → 2 分
# 職稱加分：CFO > CEO（Wang-Shin-Francis 2012 JFQA：CFO 買入 12 個月超額比 CEO 高 ~5pp）
CFO_TITLE_KEYWORDS = ("CFO", "CHIEF FINANCIAL")   # 命中 → 2 分
CEO_TITLE_KEYWORDS = ("CEO", "CHIEF EXECUTIVE")   # 命中（無 CFO）→ 1 分
# 市值帶：v0 無流通股數來源，一律 N/A → 0 分（Phase 2 接 company facts API 後補）
MCAP_SMALL_CAP_MAX = 2_000_000_000.0  # 預留：市值 < $2B 視為小型（目前未啟用）
# 下跌後買入：買入 VWAP < 20 日均價 → 1 分；< 均價 × DIP_DEEP_DISCOUNT → 2 分
DIP_MA_DAYS = 20
DIP_DEEP_DISCOUNT = 0.90

TOP_N_CANDIDATES = 15         # 評分排序後輸出前 N 名

# ---------------------------------------------------------------------------
# 價格源（Stooq 為主；免金鑰、CI 可直連。刻意不用 yfinance——避免限流坑，擇穩）
# ---------------------------------------------------------------------------

STOOQ_DAILY_URL = "https://stooq.com/q/d/l/?s={symbol}&i=d"   # symbol 例：aapl.us
STOOQ_SLEEP_BETWEEN = 0.5     # 每請求間隔（秒）——免費源，保守禮貌
PRICE_HISTORY_MIN_ROWS = 5    # 低於此行數的回應視為無效（防 'No data' / 半殘 CSV）

# ---------------------------------------------------------------------------
# 前瞻表現追蹤（track_performance.py）
# ---------------------------------------------------------------------------

# 報酬窗口（日曆日）：買訊後 1週/1月/3月/6月/12月
RETURN_WINDOWS = {"1w": 7, "1m": 30, "3m": 91, "6m": 182, "12m": 365}
TRACK_DEDUP_DAYS = 30         # 同 ticker 30 日內不重複開倉追蹤

# ---------------------------------------------------------------------------
# meta_latest.json（monitor 網頁讀取的管線健康端點）
# ---------------------------------------------------------------------------

META_ENDPOINT_HEALTH_MAX = 50  # endpoint_health 每節保留最近 N 筆（防 meta 膨脹）
META_ERRORS_MAX = 30           # errors 每節保留最近 N 筆
