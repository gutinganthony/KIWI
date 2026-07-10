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

# userFills 由 Hyperliquid info API 截斷在此筆數（近端窗）。n_fills >= 此值 → 視為截斷：
# 此時 profit_factor / realized_win_rate 只反映近端樣本、偏誤大，consistent_winner 不以
# profit_factor 硬否決（改由 portfolio 曲線指標主導）。見 classify BUG 3。
MAX_USER_FILLS = 2000

# --- blowup_risk（James Wynn 型：反覆爆倉／極端槓桿＋大回撤／近全損）---
# 目前任一部位槓桿 >= 此值且回撤夠大 → 判 blowup（高槓桿賭徒）
BLOWUP_EXTREME_LEVERAGE = 25.0
BLOWUP_DRAWDOWN_PCT = 0.60            # 搭配高槓桿或「近全損」的回撤門檻（占 peak）
# pnl 曲線單步崩跌 >= 此比例（占 peak）→ 佐證用；只在 peak 夠大時計算，
# 避免 PnL≈0 的刷量戶因小額波動被誤判崩跌。（本輪起崩塌判據以峰值回撤為主，此值僅供報告揭露）
BLOWUP_SINGLE_DAY_CRASH_PCT = 0.50
BLOWUP_MIN_PEAK_FOR_CRASH = 10_000.0
# 修正 B：反覆爆倉次數門檻。n_liquidations（統計 dir/欄位含 'liquidat' 的成交筆數）>= 此值
# → 一律 blowup 硬事實，即使 portfolio 缺失也照判（如 James Wynn 194 次強平）。
# 單次歷史強平（n_liquidations 在 1..2）不再強制 blowup：走正常分類（consistent/wash/choppy），
# 但於 metrics 保留 had_liquidation／n_liquidations 供 dossier 與報告揭露風險，不隱藏。
BLOWUP_MIN_LIQUIDATIONS = 3

# --- 峰值回撤/崩跌的最小 peak 閘（修正 A：殺早期小峰值假象）---
# 回撤與崩跌只在 running peak >= max(DD_MIN_PEAK_ABS, DD_MIN_PEAK_FRACTION × 全期峰值) 時才累計。
# 根因：running peak 從第一筆的小正值（如 $100）起算，之後任何一次跌破 0 都相對那個小峰值算出
# 天文數字回撤%（觀測到 dd=78028、6.46 等荒謬值）。加此閘後「$100→-$500→$181M」的早期 dip
# 不計入回撤（其 peak 遠低於全期峰值的 10%），而「$181M→$90M」的真實回撤仍計入。
DD_MIN_PEAK_ABS = 10_000.0           # 絕對地板：running peak 至少 $1 萬才開始計回撤
DD_MIN_PEAK_FRACTION = 0.10          # 且須達全期峰值（global_peak）的 10%

# --- wash_suspect（刷量／對敲：巨量但 PnL≈0，或無淨方向＋極短持倉高頻）---
WASH_MIN_VLM = 1_000_000.0           # 只有交易量真的巨大才考慮判刷量
WASH_VLM_TO_PNL_RATIO = 500.0        # 量 / max(|總PnL|,eps) >= 此值 → 疑刷量
WASH_NET_DIRECTION_MAX = 0.05        # |買量-賣量|/(買量+賣量) <= 此值 → 無淨方向
WASH_MAX_HOLD_HOURS = 0.1            # 平均持倉 < 此小時數 → 極短持倉
WASH_MIN_FILLS = 50                  # 無淨方向分支另要求成交筆數夠高（高頻自成交特徵）

# --- mm_like / 高量低效（BUG 2：做市商/高頻，巨量但量/PnL 比極高，即使 PnL 為正也不可跟）---
# 與 wash 併類為 wash_suspect（語意：非方向性 alpha，跟不到）。校準自真實 CI：某 +$28.1M PnL
# 錢包 vlm=$45.9 億、vlm_to_pnl=163、avg_win≈avg_loss≈$45、realized_win_rate 1.3% → 做市商，
# 應排除而非丟進 choppy。此條要在 consistent 檢查之前判。正常方向性贏家 vlm/PnL 應遠低於門檻。
MM_MIN_VLM = 100_000_000.0           # 交易量 >= $1 億才考慮（避免誤殺小額戶）
MM_MIN_VLM_TO_PNL = 50.0             # 量 / max(|總PnL|,eps) >= 此值 → 高量低效（做市商特徵）

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
# 廣域掃描（scan_universe.py：全量排行榜 → 「可跟畫像」候選過濾）
# 門檻用 2026-07-10 全量排行榜原始檔（40,381 列）離線校準：
#   40,381 → pnl 1,342 → 仍在賺 700 → 量/PnL 206 → roi 160 → 帳戶 148 → 排 topN 148
#   → 取分數前 120 名。起始建議值（pnl>=$100k, vpr<=30, roi>=0.3）產出 2,732 個，
#   遠超 80–150 目標，故收緊「已證明贏家」端（pnl/roi），反做市端 vpr<=30 維持建議值。
# ---------------------------------------------------------------------------

# allTime pnl 下限：全量宇宙裡 $100k+ 有 9,200 戶，太寬；$2M 才進「已證明的大贏家」級距
SCAN_MIN_ALLTIME_PNL = 2_000_000.0
# 「仍在賺」下限：>0 會放進 month pnl=$0.07 的粉塵戶（校準時實際觀測到），加實質地板
SCAN_MIN_MONTH_PNL = 10_000.0
SCAN_MIN_WEEK_PNL = 1_000.0
# 量/PnL 比帶（反做市/刷量核心條件，雙邊）：
# 上限 30：做市/高頻的 vpr 遠高於此（參考 MM_MIN_VLM_TO_PNL=50），方向性贏家遠低。
# 下限 1：pnl 必須能被實際永續成交量解釋——校準時觀測到 allTime vlm=$167 但 pnl=$12.9M
# 的戶（vault/HLP 型收益，非方向性交易，fills 跟單跟不到），vpr<1 在數學上不可能來自
# 真永續交易（平倉本身就產生 ≈ 部位名目的量），一律排除。vlm<=0 亦排除。
SCAN_MIN_VLM_TO_PNL = 1.0
SCAN_MAX_VLM_TO_PNL = 30.0
# allTime roi 下限：方向性交易者 roi 不會像做市那樣趨近 0；0.3 太寬（校準後仍 2,500+），
# 收緊到 1.0（全期 +100%）
SCAN_MIN_ALLTIME_ROI = 1.0
# 帳戶淨值帶：排除粉塵與巨鯨（巨鯨滑價/部位結構與散戶跟單不相容）
SCAN_MIN_ACCOUNT = 20_000.0
SCAN_MAX_ACCOUNT = 20_000_000.0
# 排除排行榜前 N 列（每日 top-60 管線已掃過的頂端；與 fetch.extract_addresses 同語意）
SCAN_EXCLUDE_TOP_N = 200
# 綜合分數排序後取前 N 名（scan_universe --max-candidates 預設值）
SCAN_DEFAULT_MAX_CANDIDATES = 120

# --- followable（可跟性；classify --label scan 報告對 consistent_winner 加判）---
# 真錢跟單的機械可行性門檻：頻率太高跟不上、持倉太短來不及進場、槓桿太高一次爆倉歸零。
SCAN_FOLLOWABLE_MAX_FREQ = 150      # 近 30 天成交筆數（≈每月筆數）<= 150（≈5 筆/天）
SCAN_FOLLOWABLE_MIN_HOLD_H = 12.0   # 平均持倉 >= 12 小時
SCAN_FOLLOWABLE_MAX_LEVERAGE = 10.0  # 目前任一部位槓桿 <= 10x

# --- fills → 部位事件聚合（classify.aggregate_fills_to_events）---
# fills ≠ 決策：一張大單在薄訂單簿會拆成多筆成交、分批建倉也是同一個交易決策。
# 同幣種同方向、相鄰 fills 間隔 <= 此分鐘數 → 合併為同一「部位事件」（一次交易決策）。
AGG_EVENT_GAP_MINUTES = 60
# 可跟性頻率判定升級：改用「近 30 天部位事件數」<= 此值（fills 數降為參考欄位，不再硬否決）。
# 門檻沿用 150（≈5 個決策/天）：真正的決策頻率才是跟單延遲下跟不跟得上的關鍵。
FOLLOWABLE_MAX_EVENTS_30D = 150

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
    # 廣域掃描最佳候選：+$9.28M、回撤 5.6%、pf 14、槓桿 3x、零強平、平均持倉 250h。
    # 唯一不過的判定是「30 日 1,080 筆 fills > 150」——疑為分批執行（fills≠決策），
    # 由 fills→部位事件聚合重算真實決策頻率複核；dossier 的「決策頻率複核」節出結論。
    {"address": "0x8bae3527e5a33fa0cf184f37bc112d071463ab6d",
     "label": "scan-best-candidate-9M-lowdd"},
]
