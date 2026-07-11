# us-funnel — 美股 Form 4 三層漏斗管線 v0

每日掃 SEC EDGAR Form 4（內部人申報），跑「資格關卡 → 否決關卡 → 等權評分」漏斗，
輸出候選股並自動追蹤買訊後 1週/1月/3月/6月/12月 前瞻表現。數據供 monitor 網頁呈現。

**純唯讀研究管線**：只 GET 公開免金鑰數據，無任何下單、券商 API、簽章、金鑰。
設計依據：`topics/business/2026-07-10-us-tw-signal-funnel-design.md` §1（三層定稿）＋
`topics/business/2026-07-10-stock-signal-appendix/stock_signal_form4.md`（訊號實證細節）。

## 管線

```
fetch_edgar.py   EDGAR 每日索引 → 逐筆 Form 4 XML → data/events/form4_{date}.json（精簡事件）
funnel.py        7 日窗事件 → 三層漏斗 → data/candidates_latest.json（前 N 候選）
track_performance.py  候選 → data/performance_tracking.json（開倉去重＋窗口報酬回填）
```

三層漏斗（常數全在 `config.py`）：

1. **資格關卡**：transactionCode=P 自主買入、無 10b5-1 checkbox（aff10b5One，2023-04 起）、
   7 日滾動窗內同 issuer ≥2 名不同 reportingOwner（集群）。
2. **否決關卡**（一票否決）：仙股（買入 VWAP < $1）、同窗內部人賣出額 > 買入額 50%、
   近 20 交易日日均成交額 < $200k（價格源故障→跳過此檢查並記 meta，不否決）。
3. **等權評分**（每項 0–2 分，加總取前 15）：集群人數（2人=1、≥3人=2）、買入總額帶
   （≥$100k=1、≥$500k=2）、職稱（CFO=2、CEO=1）、市值帶（**評分自此版含市值帶**：
   micro/small <$2B=2、mid $2B–10B=1、large >$10B=0；無數據=0）、
   下跌後買入（VWAP<20日均價=1、<均價×0.9=2）。

另對通過否決關的 survivors 計算**風險分級**（beta × 市值雙維度，非評分項）：

- 市值＝EDGAR company facts 流通股數（`dei/EntityCommonStockSharesOutstanding`，
  缺則 `us-gaap/CommonStockSharesOutstanding`）× Stooq 最新收盤。
  檔分：<$300M=3、$300M–2B=2、$2B–10B=1、>$10B=0；無數據=3（保守）。
- beta＝候選 vs SPY 近 1 年日報酬 OLS 斜率（有效重疊 <60 交易日 → None）。
  檔分：>1.3=2、0.8–1.3=1、<0.8=0；無數據=2（保守）。
- 加總：≥4 → high、2–3 → medium、≤1 → low；任一維無數據 → `data_gap=true`。
  風險分級是價格波動與規模的代理指標，非基本面/違約風險評估。常數與函式見
  `config.py`「風險分級」節與 `funnel.py` 的 `assess_risk()`。

## 數據源與禮儀

- **EDGAR**（免費）：daily-index `form.{YYYYMMDD}.idx` 篩 form type "4" → 逐筆 .txt 全文擷取
  `<ownershipDocument>` XML；company facts（`data.sec.gov/api/xbrl/companyconcept/...`）
  供流通股數（只對 survivors 查，~9–15 檔/日）。**SEC fair access 規定**：User-Agent 必須含
  真實可聯絡信箱（`config.EDGAR_USER_AGENT`，GitHub noreply——假信箱疑遭過濾致 403）、
  ≤10 req/s（本管線 sleep 0.15s ≈ 6.7 req/s，序列執行）；403 重試前等 [10s, 30s]。
- **Stooq（主）→ Yahoo chart API（備援）**（皆免費、無金鑰）：日線
  `https://stooq.com/q/d/l/?s={ticker}.us&i=d`；Stooq 無效（微型股常回 'No data'）時改抓
  `https://query1.finance.yahoo.com/v8/finance/chart/{TICKER}?range=1y&interval=1d`
  （瀏覽器 UA、sleep 0.6s、429 退避一次再棄；僅日線唯讀、每日 ~20 支，遠低於限流）。
  供流動性否決、dip 評分、beta（含 SPY 基準）與前瞻報酬；per-ticker 使用源記
  meta（`price_sources`/`price_source_stats`）。刻意不用 yfinance 套件（CI 限流前科，擇穩）。

## 輸出契約（monitor 網頁依此讀取，鍵名不可改）

- `data/candidates_latest.json`：`{generated_at, scan_window_days, funnel_stats:{raw_filings,
  qualified_events, post_veto, final_candidates}, candidates:[{ticker, company, cluster_size,
  insiders:[{name,title}], total_buy_usd, score, score_breakdown, first_filing_date,
  entry_price_ref, risk:{level, data_gap, beta, mcap_usd, mcap_band, beta_band}}]}`
  （entry_price_ref＝集群買入 VWAP；risk.level ∈ high/medium/low、
  mcap_band ∈ micro/small/mid/large/unknown、beta_band ∈ high/mid/low/unknown）
- `data/performance_tracking.json`：`{updated_at, positions:[{ticker, signal_date,
  entry_price_ref, current_price, returns:{1w,1m,3m,6m,12m}, status}]}`。
  每日：新候選 append（同 ticker 30 日內不重複開倉）；已到期窗口回填報酬
  （終點日或之後第一個交易日收盤 / entry - 1），未到期留 null；全回填 → status=completed。
- `data/meta_latest.json`：fetch/funnel/tracking 三節各自的端點健康、漏斗各層計數、錯誤。

## 執行

```bash
pip install -r requirements.txt
python3 fetch_edgar.py            # 首跑回補 ~7 個申報日（可能 1–2 小時）；之後每日增量 1 天
python3 funnel.py                 # 加 --no-network 可離線驗證（流動性檢查跳過、dip=0）
python3 track_performance.py
python3 tests/test_offline.py     # 離線測試，結尾 ALL TESTS PASSED (N checks)
```

CI：`.github/workflows/us-funnel.yml`，cron `30 3 * * 2-6`（UTC 03:30＝美東前一交易日
22:00 收件截止之後、台北 11:30；週二至週六對應美股週一至五申報日）。三步各 `|| true` 保底，
commit-back 只加 `data/`（rebase-then-push）。事件檔保留 14 天自動清理，單次 commit 產物 <1MB。

## 已知限制（Phase 2）

- 歷史回測不在 v0 範圍。
- opportunistic/routine 分型（CMP 2012）需 ≥3 年逐人交易史，v0 未實作。
- 13F 慢錢共振加分未實作（設計檔 §1 第三層 ★★ 項）。
- M-Score 級操縱紅旗 v0 從簡為仙股排除。
