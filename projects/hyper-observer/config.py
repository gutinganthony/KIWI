"""hyper-observer 集中設定：Hyperliquid 公開 info API 端點與永續分類門檻常數。

純唯讀觀察器設定。此專案不包含任何下單、簽章、私鑰、錢包連線功能，
所有請求皆為 Hyperliquid 公開免金鑰的 read-only 查詢：
- POST https://api.hyperliquid.xyz/info（免金鑰 info API，只查不改）
- GET  https://stats-data.hyperliquid.xyz/Mainnet/leaderboard（未文件化前端快取端點，脆弱）

刻意不引用任何 exchange endpoint（/exchange）、eth_account、簽章或私鑰。
"""

# ---------------------------------------------------------------------------
# HTTP 共通參數
# ---------------------------------------------------------------------------

HTTP_TIMEOUT = 20            # 每請求 timeout（秒）
HTTP_RETRIES = 2            # 失敗後重試次數（不含首次）
HTTP_BACKOFFS = [1, 3]      # 第 1 / 2 次重試前的等待秒數
# Hyperliquid info API rate limit：每 IP 1200 權重/min，clearinghouseState 權重 2、
# userFills/userFunding 權重 20＋每 20 筆再加權重。逐錢包掃描要保守 sleep + 分批。
HTTP_SLEEP_BETWEEN = 0.5    # 每請求之間的間隔（秒），避免打爆公開 API
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
ERROR_BODY_SNIPPET_LEN = 200  # 端點失敗時記錄 body 前 N 字

# ---------------------------------------------------------------------------
# Hyperliquid 公開端點
# ---------------------------------------------------------------------------

# 免金鑰 info API：所有每錢包查詢一律 POST 此 URL，body 帶 {"type": ..., "user": ...}
INFO_URL = "https://api.hyperliquid.xyz/info"

# 每錢包 info 查詢的 type（本里程碑用到的四種；皆唯讀）
INFO_TYPES = [
    "clearinghouseState",  # 持倉/方向/槓桿/強平價/未實現PnL/帳戶淨值
    "portfolio",           # 多視窗 accountValueHistory / pnlHistory / vlm（分類器骨幹）
    "userFills",           # 成交（closedPnl/dir/coin/px/sz/side），贏輸平倉皆有 closedPnl
    "userFunding",         # 資金費收付（本里程碑僅抓來記總額）
]

# userFunding 起始時間（epoch 毫秒）：抓自此後的資金費紀錄，None → 省略 startTime
USER_FUNDING_START_MS = None

# 宇宙來源（Path A）：未文件化前端 leaderboard 端點。GET、免金鑰、**脆弱**（可能 403/
# 改 schema/加防爬）。fetch.py 試打；失敗就記 meta.endpoint_health 並退回只用 seeds。
LEADERBOARD_ENDPOINTS = [
    "https://stats-data.hyperliquid.xyz/Mainnet/leaderboard",
]

# ---------------------------------------------------------------------------
# 錢包宇宙
# ---------------------------------------------------------------------------

DEFAULT_MAX_WALLETS = 60      # fetch.py --max-wallets 預設值（seeds 永遠保留）

# ---------------------------------------------------------------------------
# portfolio 視窗選擇
# ---------------------------------------------------------------------------

# 分類器優先用永續全期視窗；缺則退回總帳全期視窗。
PORTFOLIO_PRIMARY_WINDOW = "perpAllTime"
PORTFOLIO_FALLBACK_WINDOW = "allTime"

# ---------------------------------------------------------------------------
# 分類門檻（classify.py 使用；永續語意，全部可調）
# ---------------------------------------------------------------------------

# insufficient_data：無 portfolio PnL 曲線且成交筆數低於此值 → 資料不足
MIN_FILLS_FOR_CLASSIFICATION = 5

# --- blowup_risk（James Wynn 型：曾爆倉／極端槓桿＋大回撤）---
# 目前任一部位槓桿 >= 此值且回撤夠大 → 判 blowup（高槓桿賭徒）
BLOWUP_EXTREME_LEVERAGE = 25.0
BLOWUP_DRAWDOWN_PCT = 0.60            # 搭配高槓桿的回撤門檻（占 peak）
# pnl 曲線單步崩跌 >= 此比例（占 peak）→ 判 blowup；只在 peak 夠大時計算，
# 避免 PnL≈0 的刷量戶因小額波動被誤判崩跌。
BLOWUP_SINGLE_DAY_CRASH_PCT = 0.50
BLOWUP_MIN_PEAK_FOR_CRASH = 10_000.0
# fills 出現 liquidation dir / liquidation 欄位 → 一律 blowup（不需其他條件）

# --- wash_suspect（刷量／對敲：巨量但 PnL≈0，或無淨方向＋極短持倉高頻）---
WASH_MIN_VLM = 1_000_000.0           # 只有交易量真的巨大才考慮判刷量
WASH_VLM_TO_PNL_RATIO = 500.0        # 量 / max(|總PnL|,eps) >= 此值 → 疑刷量
WASH_NET_DIRECTION_MAX = 0.05        # |買量-賣量|/(買量+賣量) <= 此值 → 無淨方向
WASH_MAX_HOLD_HOURS = 0.1            # 平均持倉 < 此小時數 → 極短持倉
WASH_MIN_FILLS = 50                  # 無淨方向分支另要求成交筆數夠高（高頻自成交特徵）

# --- one_hit（單期爆賺主導，或活躍太短）---
ONE_HIT_BEST_MONTH_SHARE = 0.70      # 單一最佳月 PnL > 總 PnL 的此比例
ONE_HIT_MIN_SPAN_DAYS = 30           # 活躍跨度 < 此天數

# --- dormant（閒置且目前無持倉 → 無單可跟）---
DORMANT_MAX_IDLE_DAYS = 30

# --- consistent_winner（值得進一步觀察、可能可跟的候選）---
CONSISTENT_MIN_SPAN_DAYS = 60
CONSISTENT_MIN_TOTAL_PNL = 10_000.0
CONSISTENT_MAX_DRAWDOWN_PCT = 0.40           # 占 peak PnL 的比例
CONSISTENT_MIN_PROFIT_FACTOR = 1.3           # Σ正closedPnl / |Σ負closedPnl|
CONSISTENT_MAX_LEVERAGE = 20.0               # 目前任一部位槓桿須 <= 此值
CONSISTENT_MIN_POSITIVE_MONTH_RATIO = 0.5

# 報告用：目前任一部位槓桿 >= 此值 → 標為「極端槓桿」旗標（僅提示，非單獨判決）
EXTREME_LEVERAGE_FLAG = 25.0

# ---------------------------------------------------------------------------
# 裁決門檻（verification 報告末段）
# ---------------------------------------------------------------------------

VERDICT_STRONG_MIN_WINNERS = 5   # consistent_winner >= 5 → 存在性檢驗通過
VERDICT_WEAK_MIN_WINNERS = 1     # 1–4 → 弱存在；0 → 未發現

# ---------------------------------------------------------------------------
# Ground-truth 校驗（seeds.json 內已知結局的錢包 → 預期分類集合）
# 分類器若把這些錢包分進預期以外的類別，verification 報告會醒目標出。
# 註：地址來自研究快照、本環境未鏈上驗證，首次 CI 跑會用真 info API 覆核。
# ---------------------------------------------------------------------------

GROUND_TRUTH_EXPECTED = {
    # James Wynn：40x BTC 高槓桿、累計 194 次強平、$100M → $900 的活教材反例。
    # 分類器必須把這種「曾爆倉」錢包判為 blowup_risk（高勝率≠存活）。
    "0x5078c2fbea2b2ad61bc840bc023e35fce56bedb6": ["blowup_risk"],
}

# ---------------------------------------------------------------------------
# 深度追蹤名單（track_wallet.py 逐日 dossier；跟單模擬器為下一個里程碑，本次不做）
# 這些錢包的原始 snapshot 會被 track_wallet.py 複製到 data/tracked/{addr}/，
# 在每日 prune data/snapshots/*/wallets 之後仍持久化，供未來模擬器使用。
# 純唯讀：追蹤為紙上分析，不含任何下單、簽章、金鑰、錢包連線程式碼。
# ---------------------------------------------------------------------------

TRACKED_WALLETS = [
    {"address": "0x5078c2fbea2b2ad61bc840bc023e35fce56bedb6",
     "label": "james-wynn-blowup-groundtruth"},
    {"address": "0x5b5d51203a0f9079f8aeb098a6523a13f298c060",
     "label": "hft-highvolume-candidate"},
]
