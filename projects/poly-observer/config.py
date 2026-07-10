"""poly-observer 集中設定：API 端點清單與分類門檻常數。

純唯讀觀察器設定。此專案不包含任何下單、金鑰、簽章、錢包連線功能，
所有端點皆為 Polymarket 公開免金鑰的 read-only HTTP GET API。
"""

# ---------------------------------------------------------------------------
# HTTP 共通參數
# ---------------------------------------------------------------------------

HTTP_TIMEOUT = 20            # 每請求 timeout（秒）
HTTP_RETRIES = 2             # 失敗後重試次數（不含首次）
HTTP_BACKOFFS = [1, 3]       # 第 1 / 2 次重試前的等待秒數
HTTP_SLEEP_BETWEEN = 0.35    # 每請求之間的間隔（秒），避免打爆公開 API
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
ERROR_BODY_SNIPPET_LEN = 200  # 端點失敗時記錄 body 前 N 字

# ---------------------------------------------------------------------------
# 端點清單（每類依序 fallback，試到 200＋合法 JSON 為止）
# 佔位符：{window} / {addr} / {off}
# ---------------------------------------------------------------------------

# 2026-07-10 查證：leaderboard 搬家到 data-api /v1，參數 window→timePeriod、
# rankType→orderBy（官方文件 docs.polymarket.com/api-reference/core/get-trader-leaderboard-rankings）。
# 舊 lb-api.polymarket.com 已退役（404），保留為末位 fallback 僅供偵測回歸。
LEADERBOARD_ENDPOINTS = [
    "https://data-api.polymarket.com/v1/leaderboard?timePeriod={window}&orderBy=PNL&limit=50&category=OVERALL&offset=0",
    "https://lb-api.polymarket.com/leaderboard?window={window}&rankType=pnl&limit=50",
]
LEADERBOARD_WINDOWS = ["MONTH", "ALL"]   # 兩窗：近一月、全期
LEADERBOARD_WINDOW_FALLBACKS = {"MONTH": "WEEK"}  # timePeriod 不被接受時的替代值

ACTIVITY_ENDPOINTS = [
    "https://data-api.polymarket.com/activity?user={addr}&limit=500&offset={off}",
]
ACTIVITY_PAGE_LIMIT = 500     # 每頁筆數
ACTIVITY_MAX_RECORDS = 1500   # 每錢包最多抓的 activity 筆數（分頁上限）

POSITIONS_ENDPOINTS = [
    "https://data-api.polymarket.com/positions?user={addr}&limit=500",
]

VALUE_ENDPOINTS = [
    "https://data-api.polymarket.com/value?user={addr}",
]

PNL_ENDPOINTS = [
    "https://user-pnl-api.polymarket.com/user-pnl?user_address={addr}&interval=all&fidelity=1d",
    "https://user-pnl-api.polymarket.com/user-pnl?user_address={addr}&interval=max&fidelity=1d",
]

# ---------------------------------------------------------------------------
# 錢包宇宙
# ---------------------------------------------------------------------------

DEFAULT_MAX_WALLETS = 60      # fetch.py --max-wallets 預設值（seeds 永遠保留）

# ---------------------------------------------------------------------------
# 分類門檻（verify_smart_money.py 使用）
# ---------------------------------------------------------------------------

# 資料不足：無 PnL 曲線且交易筆數低於此值 → insufficient_data
MIN_TRADES_FOR_CLASSIFICATION = 5

# mm_bot_like：頻率 > 1500 筆/月，或平均單筆持有 < 1 小時（可判斷時）
MM_BOT_TRADES_PER_MONTH = 1500
MM_BOT_MAX_AVG_HOLD_HOURS = 1.0

# one_hit：單一最佳月 PnL > 總 PnL 的 70%，或活躍月數 < 2
ONE_HIT_BEST_MONTH_SHARE = 0.70
ONE_HIT_MIN_ACTIVE_MONTHS = 2

# consistent_winner：活躍 >=3 個月、正月比率 >=0.6、總 PnL > $10,000、
# 峰值回撤 < 50% peak、頻率 5–1500 筆/月
# 2026-07-10 實測教訓：只數日曆月會讓 55-69 天的熱 streak 混過「3 個月」門檻
# （5/17 開始的錢包在 7 月拿到 5、6、7 三個月鍵），故加最短實際跨度天數。
CONSISTENT_MIN_SPAN_DAYS = 75
CONSISTENT_MIN_ACTIVE_MONTHS = 3
CONSISTENT_MIN_POSITIVE_MONTH_RATIO = 0.6
CONSISTENT_MIN_TOTAL_PNL = 10_000.0
CONSISTENT_MAX_DRAWDOWN_PCT = 0.50          # 占 peak PnL 的比例
CONSISTENT_FREQ_RANGE = (5.0, 1500.0)       # 筆/月（含端點）

# degraded：符合 consistent 核心條件，但最近 30 天 PnL < -15% × 總 PnL
DEGRADED_RECENT_PNL_FRACTION = -0.15

# dormant：閒置（無交易且 PnL 無變動）超過 N 天、且目前持倉價值 <= 門檻
# → 不論歷史多輝煌都不可跟（無單可跟）。value 端點缺資料時不判 dormant（證據不足）。
DORMANT_MAX_IDLE_DAYS = 30
DORMANT_MAX_CURRENT_VALUE = 100.0

# ---------------------------------------------------------------------------
# 裁決門檻（verification 報告末段）
# ---------------------------------------------------------------------------

VERDICT_STRONG_MIN_WINNERS = 5   # consistent_winner >= 5 → 存在性檢驗通過
VERDICT_WEAK_MIN_WINNERS = 1     # 1–4 → 弱存在；0 → 未發現

# ---------------------------------------------------------------------------
# 觀察器警示門檻（analyze.py 使用）
# ---------------------------------------------------------------------------

ALERT_FREQ_SPIKE_MULTIPLIER = 3.0   # 頻率暴增 >= 3x 前一日 → 警示

# ---------------------------------------------------------------------------
# 類別分桶（由 activity 的 title/slug 關鍵字判斷；由上往下先中先贏，
# esports 必須排在 sports 前，避免 "league of legends" 被吃進 sports）
# ---------------------------------------------------------------------------

CATEGORY_KEYWORDS = [
    ("esports", [
        "esports", "e-sports", "cs2", "csgo", "cs-go", "counter-strike",
        "league of legends", "league-of-legends", " lol ", "-lol-", "lcs", "lck",
        "valorant", "dota", "overwatch", "starcraft", "call of duty",
        "call-of-duty", "rainbow six", "rocket league", "iem-", "blast premier",
    ]),
    ("sports", [
        "nba", "nfl", "mlb", "nhl", "soccer", "football", "basketball",
        "baseball", "tennis", "ufc", "mma", "boxing", "golf", "f1-", "formula 1",
        "premier league", "premier-league", "la liga", "la-liga", "serie a",
        "serie-a", "champions league", "champions-league", "world cup",
        "world-cup", "olympic", "epl-", "cricket", "hockey", "grand slam",
        "wimbledon", "super bowl", "super-bowl", "playoffs",
    ]),
    ("politics", [
        "election", "president", "senate", "congress", "trump", "biden",
        "harris", "governor", "parliament", "prime minister", "prime-minister",
        "mayor", "poll", "nominee", "impeach", "cabinet", "supreme court",
        "supreme-court", "geopolit", "ceasefire", "nato", "referendum",
        "legislation", "veto", "white house", "white-house",
    ]),
    ("crypto", [
        "bitcoin", "btc", "ethereum", "eth-", "solana", "sol-", "crypto",
        "dogecoin", "doge", "xrp", "airdrop", "defi", "nft", "stablecoin",
        "altcoin", "memecoin", "satoshi",
    ]),
    ("economics", [
        "fed ", "fed-", "fomc", "interest rate", "interest-rate", "rate cut",
        "rate-cut", "rate hike", "rate-hike", "inflation", "cpi", "gdp",
        "recession", "unemployment", "treasury", "tariff", "jobs report",
        "jobs-report", "nonfarm", "payroll", "powell",
    ]),
    ("weather", [
        "weather", "temperature", "hurricane", "rainfall", "snowfall", "snow",
        "heatwave", "heat wave", "storm", "tornado", "climate", "degrees",
        "typhoon",
    ]),
]
FALLBACK_CATEGORY = "other"

# ---------------------------------------------------------------------------
# Ground-truth 校驗（data/seeds.json 內已知結局的錢包 → 預期分類集合）
# 分類器若把這些錢包分進預期以外的類別，verification 報告會醒目標出。
# ---------------------------------------------------------------------------

GROUND_TRUTH_EXPECTED = {
    # xdd07070：esports 錢包，2026-02 爆紅（API 證實終身 PnL +$176k、峰值 $262k@4/6、
    # 4/14 起曲線躺平、最後 TRADE 4/12、持倉 $0）→ 現況應判 dormant。
    # 註：媒體傳的「爆倉 −$311k」已被官方 user-pnl API 直查證偽（2026-07-10）。
    "0x25e28169faea17421fcd4cc361f6436d1e449a09": ["dormant"],
}
