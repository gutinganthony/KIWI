"""tw-funnel 集中設定：台股投信×營收動能三層漏斗（v0，上市 TWSE only）。

純唯讀觀察管線。此專案不包含任何下單、簽章、金鑰、券商連線功能，
所有請求皆為 TWSE 公開免金鑰端點的 read-only GET 查詢。不構成投資建議。

設計依據：topics/business/2026-07-10-us-tw-signal-funnel-design.md §2（台股漏斗定稿）
＋ topics/business/2026-07-10-stock-signal-appendix/stock_signal_taiwan.md。

三層漏斗：
  第一層 資格關卡：投信買超（當日 >0 且近 3 日累計 ≥ 門檻）且 月營收 YoY>0 且 YoY 加速
  第二層 否決關卡：流動性下限／處置警示股／1 月作帳反轉窗／董監質押 >50%（接得到才生效）
  第三層 等權評分：YoY 加速幅度、投信買超強度、小型股帶、近 60 日首次買超（各 0–2 分）
"""

# ---------------------------------------------------------------------------
# HTTP 共通參數
# ---------------------------------------------------------------------------

HTTP_TIMEOUT = 30            # 每請求 timeout（秒）
HTTP_RETRIES = 2             # 失敗後重試次數（不含首次）
HTTP_BACKOFFS = [2, 5]       # 第 1 / 2 次重試前的等待秒數
HTTP_SLEEP_BETWEEN = 1.0     # 端點之間的間隔（秒），避免打擾公開 API
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
ERROR_BODY_SNIPPET_LEN = 200  # 端點失敗時記錄 body 前 N 字

# ---------------------------------------------------------------------------
# TWSE 公開端點（全部免金鑰、唯讀 GET）
# ---------------------------------------------------------------------------

# 三大法人買賣超日報（含投信買進/賣出/買賣超股數）——主端點：OpenAPI 最新交易日全表
T86_OPENAPI_URL = "https://openapi.twse.com.tw/v1/fund/T86"
# 備援：rwd JSON（可指定日期；date=YYYYMMDD, selectType=ALL）
T86_RWD_URL = "https://www.twse.com.tw/rwd/zh/fund/T86"

# 全市場每日收盤（收盤價＋成交金額；同時餵前瞻表現追蹤與流動性否決）
STOCK_DAY_ALL_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"

# 上市公司每月營業收入彙總表（含 當月營收/去年同月增減(%)；資料年月為民國年月）
REVENUE_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap05_L"

# 上市公司基本資料（取已發行普通股數 → 市值；缺欄位時退回 實收資本額/10 估股數）
COMPANY_BASIC_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"

# 處置有價證券公告（否決用）。⚠ 本環境 egress 被擋、端點存在性未實測，
# CI 首跑以 meta.endpoint_health 記錄真實狀態；失敗＝該否決不生效並誠實標註。
PUNISH_URL = "https://openapi.twse.com.tw/v1/announcement/punish"
# 注意股票公告（否決用）。⚠ 同上，未實測 best-effort。
ATTENTION_URL = "https://openapi.twse.com.tw/v1/announcement/notice"

# 董監事持股餘額/設質（質押比否決用）。⚠ dataset 代號未實測 best-effort：
# 失敗或欄位不含「設質」→ 質押否決不生效，meta 誠實標註 TODO。
PLEDGE_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap11_L"

# 董監事申讓申報：TWSE OpenAPI 查無對應 dataset（申讓申報在 MOPS，無官方 API）。
# v0 不接線 → None；meta.todo_not_wired 與 README 誠實標註。
DIRECTOR_TRANSFER_URL = None

# TODO(v0)：上櫃 TPEx 對應端點（https://www.tpex.org.tw/openapi/ 系列）未接線，
# v0 只做上市（TWSE）。

# ---------------------------------------------------------------------------
# 第一層｜資格關卡
# ---------------------------------------------------------------------------

QUAL_WINDOW_DAYS = 3                    # 累計買超視窗（交易日）
MIN_3D_NET_BUY_SHARES = 500_000         # 近 3 日累計投信買超股數門檻（500 張）
MIN_3D_NET_BUY_VALUE_TWD = 50_000_000   # 或 近 3 日累計買超金額門檻（股數×收盤估算）
# 兩門檻擇一通過即可（OR）；金額門檻讓高價股不因張數少被漏掉。

# 月營收：YoY > 0 且 本月 YoY > 上月 YoY（加速）。上月 YoY 取自 revenue_history
# 逐月累積；史料不足（首月上線）→ 該股無法判加速 → 不入池，meta 記 accel_unknown。

# ---------------------------------------------------------------------------
# 第二層｜否決關卡
# ---------------------------------------------------------------------------

MIN_AVG_DAILY_TURNOVER_TWD = 30_000_000  # 日均成交額下限（3 千萬；近 N 日平均）
TURNOVER_AVG_WINDOW = 20                 # 日均成交額回看視窗（交易日）
VETO_UNKNOWN_TURNOVER = True             # 查無成交額 → 保守否決（寧可漏勿錯）

PLEDGE_VETO_RATIO = 0.50                 # 董監質押比 > 50% 一票否決（接得到數據才生效）

JANUARY_NO_NEW_ENTRY = True              # 1 月作帳反轉窗：上半月不進新倉（config 開關）
JANUARY_WINDOW_LAST_DAY = 15             # 1/1–1/15 不出新候選

# ---------------------------------------------------------------------------
# 第三層｜等權評分（每項 0–2 分，等權加總；DeMiguel 1/N——不做權重最適化）
# ---------------------------------------------------------------------------

# (1) 營收 YoY 加速幅度（本月YoY − 上月YoY，百分點）
SCORE_ACCEL_1PT = 5.0     # 加速 ≥ 5pp → 1 分
SCORE_ACCEL_2PT = 15.0    # 加速 ≥ 15pp → 2 分

# (2) 投信買超強度＝連續天數（+1）＋ 金額/市值比（+1），上限 2
SCORE_CONSEC_DAYS = 3           # 連續買超 ≥ 3 日 → +1
SCORE_NETBUY_MCAP_RATIO = 0.0005  # 近 3 日買超金額 / 市值 ≥ 0.05% → +1
SCORE_NETBUY_VALUE_TWD = 100_000_000  # 市值不可得時的退化門檻：3 日買超金額 ≥ 1 億 → +1

# (3) 小型股帶（投信認養效應集中處）
SMALLCAP_2PT_MCAP_TWD = 30_000_000_000    # 市值 < 300 億 → 2 分
SMALLCAP_1PT_MCAP_TWD = 100_000_000_000   # 市值 < 1000 億 → 1 分；市值不可得 → 0 分

# (4) 投信「首次」買超（近 60 交易日、本次連買段之前無任何買超日）→ 2 分
FIRST_BUY_LOOKBACK_DAYS = 60

# ---------------------------------------------------------------------------
# 輸出與狀態保留
# ---------------------------------------------------------------------------

TOP_N = 15                        # 輸出前 N 檔候選
TRUST_HISTORY_KEEP_DAYS = 70      # 投信買賣超歷史保留交易日數（60 日回看＋緩衝）
TURNOVER_HISTORY_KEEP_DAYS = 25   # 成交額歷史保留交易日數（20 日均量＋緩衝）
REVENUE_HISTORY_KEEP_MONTHS = 4   # 月營收歷史保留月數（判加速只需 2，留緩衝）

# 前瞻表現追蹤視窗（日曆日）：買訊後 1週/1月/3月/6月/12月
PERFORMANCE_WINDOWS_DAYS = {"1w": 7, "1m": 30, "3m": 91, "6m": 182, "12m": 365}

# ---------------------------------------------------------------------------
# 漏斗饑餓/失效監控（設計文件 §3 運營規則 2；只警告寫進 meta，不自動調參）
# ---------------------------------------------------------------------------

FUNNEL_STARVED_BELOW = 10   # 否決後候選 < 10 → meta 警告「考慮放寬資格關卡」
FUNNEL_BROKEN_ABOVE = 100   # 否決後候選 > 100 → meta 警告「檢查資格關卡是否失效」
