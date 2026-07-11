"""us-funnel 集中設定：EDGAR Form 4 三層漏斗（資格→否決→等權評分）與前瞻表現追蹤。

純唯讀研究管線。此專案不包含任何下單、券商 API、簽章、金鑰功能，
所有請求皆為免金鑰的公開唯讀查詢：
- GET https://www.sec.gov/Archives/edgar/daily-index/...（Form 4 每日索引）
- GET https://www.sec.gov/Archives/edgar/data/...（單筆 filing 全文，含 ownershipDocument XML）
- GET https://stooq.com/q/d/l/...（免費日線 CSV，前瞻表現與流動性估算——主價格源）
- GET https://query1.finance.yahoo.com/v8/finance/chart/...（免金鑰日線 JSON——Stooq 備援）

設計依據：topics/business/2026-07-10-us-tw-signal-funnel-design.md §1（三層定稿）與
topics/business/2026-07-10-stock-signal-appendix/stock_signal_form4.md（訊號細節）。
"""

# ---------------------------------------------------------------------------
# HTTP 共通參數
# ---------------------------------------------------------------------------

HTTP_TIMEOUT = 30            # 每請求 timeout（秒）
HTTP_RETRIES = 2             # 失敗後重試次數（不含首次）
HTTP_BACKOFFS = [1, 3]       # 第 1 / 2 次重試前的等待秒數
# 403 專屬重試等待（2026-07-11 CI 實證：EDGAR daily-index 回 S3 AccessDenied，疑共享 IP
# 暫時封鎖）——比一般 backoff 長，給封鎖窗喘息；仍失敗 → 既有優雅降級（吃快取/跳過檢查）
HTTP_403_BACKOFFS = [10, 30]
ERROR_BODY_SNIPPET_LEN = 200  # 端點失敗時記錄 body 前 N 字

# ---------------------------------------------------------------------------
# EDGAR 端點與禮儀（SEC fair access policy——規定，不是建議）
# https://www.sec.gov/os/accessing-edgar-data：
#   1. User-Agent 必須含可聯絡的 email（缺 UA 直接 403）。
#   2. 限速 ≤10 requests/秒，超速封鎖 10 分鐘。
# 本管線每請求間 sleep EDGAR_SLEEP_BETWEEN=0.15s（≈6.7 req/s，含網路延遲實際更低），
# 留足餘裕、絕不並行請求。
# ---------------------------------------------------------------------------

# UA 循 SEC 建議格式「Sample Company Name AdminContact@<domain>.com」。信箱必須真實可聯絡
# ——GitHub noreply 信箱會轉入帳號通知；勿用假信箱（2026-07-11 CI 實證 example.com 假信箱
# 期間 daily-index 回 403 AccessDenied，疑遭過濾/封鎖）。
EDGAR_USER_AGENT = ("KIWI-research (github.com/gutinganthony/KIWI; "
                    "gutinganthony@users.noreply.github.com)")
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
# 非普通股 issuer 排除：Form 4 也涵蓋共同基金/ETF/信託的內部人申報，非股票訊號
# （2026-07-10 CI 首跑實證混入 First Trust/AMG 系基金）。以 issuer 名稱關鍵字過濾。
VETO_FUND_NAME_KEYWORDS = (
    " FUND", " TRUST", " ETF", "PORTFOLIOS", "ASSET-BACKED", "MUNICIPAL",
    "INCOME FUND", "CREDIT FUND", "CLOSED-END", "ALTERNATIVE STRATEGY",
)
# 例行申報潮排除：巨型公司高管定期同窗申報會偽裝成集群（CI 首跑實證 TSM 31 人、
# 人均僅 ~$8k——非 opportunistic 同謀式買入）。人數超上限或人均金額過低 → 否決。
VETO_MAX_CLUSTER_SIZE = 8
VETO_MIN_BUY_PER_INSIDER_USD = 25_000.0
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
# 市值帶評分（自此版啟用；市值來源見下方「風險分級」節的 company facts API）：
# micro/small（<$2B）=2 分、mid（$2B–10B）=1 分、large（>$10B）=0 分；None（無數據）=0 分
MCAP_SMALL_CAP_MAX = 2_000_000_000.0  # 市值 < $2B 視為小型（micro/small 帶上界）
# 下跌後買入：買入 VWAP < 20 日均價 → 1 分；< 均價 × DIP_DEEP_DISCOUNT → 2 分
DIP_MA_DAYS = 20
DIP_DEEP_DISCOUNT = 0.90

TOP_N_CANDIDATES = 15         # 評分排序後輸出前 N 名

# ---------------------------------------------------------------------------
# 風險分級（beta × 市值雙維度）——monitor 頁「風險分級劃分方法」備註須與此節一致
# 只對通過否決關的 survivors 計算（~9–15 檔/日，EDGAR 請求數微增）。
# ---------------------------------------------------------------------------

# 流通股數來源：EDGAR company facts（company concept API，免金鑰；沿用 EDGAR UA 禮儀）
# 依序嘗試下列 (taxonomy, tag)：404/缺 units.shares → 換下一個；全缺 → None（保守分級）
EDGAR_COMPANY_CONCEPT_URL = (
    "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik10}/{taxonomy}/{tag}.json"
)
SHARES_OUTSTANDING_CONCEPTS = (
    ("dei", "EntityCommonStockSharesOutstanding"),
    ("us-gaap", "CommonStockSharesOutstanding"),
)

# Beta：候選 vs SPY 近 1 年日報酬的 OLS 斜率 cov(r_i, r_spy)/var(r_spy)
BETA_BENCHMARK_TICKER = "SPY"   # Stooq symbol 由 stooq_symbol() 轉（spy.us）
BETA_LOOKBACK_ROWS = 252        # 近 1 年交易日
BETA_MIN_OVERLAP_DAYS = 60      # 有效重疊（成對日報酬數）低於此 → beta=None

# 市值檔分：<$300M=3、$300M–2B=2、$2B–10B=1、>$10B=0；None=3（保守）
# 帶名供輸出契約 mcap_band 使用（低於門檻即命中；超過最後一檔 → large=0）
MCAP_RISK_BANDS = (
    (300_000_000.0, 3, "micro"),
    (2_000_000_000.0, 2, "small"),
    (10_000_000_000.0, 1, "mid"),
)
MCAP_LARGE_BAND = "large"       # >$10B
MCAP_NONE_POINTS = 3            # 無市值數據 → 保守視同 micro

# Beta 檔分：>1.3=2、0.8–1.3=1、<0.8=0；None=2（保守）
BETA_HIGH_MIN = 1.3             # beta > 1.3 → 2 分（band=high）
BETA_MID_MIN = 0.8              # 0.8 ≤ beta ≤ 1.3 → 1 分（band=mid）；<0.8 → 0（band=low）
BETA_NONE_POINTS = 2            # 無 beta 數據 → 保守視同 high

# 總分 → level：≥4 → high、2–3 → medium、≤1 → low；任一維 None → data_gap=True
RISK_HIGH_MIN_POINTS = 4
RISK_MEDIUM_MIN_POINTS = 2

# ---------------------------------------------------------------------------
# 價格源（主 Stooq → 備 Yahoo chart API；皆免金鑰、CI 可直連。
# 刻意不用 yfinance 套件——避免限流坑，擇穩）
# ---------------------------------------------------------------------------

STOOQ_DAILY_URL = "https://stooq.com/q/d/l/?s={symbol}&i=d"   # symbol 例：aapl.us
STOOQ_SLEEP_BETWEEN = 0.5     # 每請求間隔（秒）——免費源，保守禮貌
PRICE_HISTORY_MIN_ROWS = 5    # 低於此行數的回應視為無效（防 'No data' / 半殘 CSV）

# Yahoo chart API 備援（2026-07-11 CI 實證：Stooq 對微型股全回 'No data'，EWSB/PFBX/JCTC
# 等 9 檔候選無價格 → beta/流動性/entry/前瞻全癱）。僅日線唯讀查詢、每日 ~20 支 ticker、
# 遠低於限流。免金鑰 JSON；User-Agent 必須用一般瀏覽器字串（預設 python UA 會被 429）。
YAHOO_CHART_URL = ("https://query1.finance.yahoo.com/v8/finance/chart/"
                   "{symbol}?range=1y&interval=1d")   # symbol 例：AAPL、BRK-B
YAHOO_SLEEP_BETWEEN = 0.6     # 每請求間隔（秒）——備援源，保守禮貌
YAHOO_429_BACKOFF = 10        # 429 限流：退避一次（秒）再試，仍失敗即棄（該 ticker 走 None）
YAHOO_USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

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
