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
   （≥$100k=1、≥$500k=2）、職稱（CFO=2、CEO=1）、市值帶（v0 無流通股數來源，一律 N/A=0）、
   下跌後買入（VWAP<20日均價=1、<均價×0.9=2）。

## 數據源與禮儀

- **EDGAR**（免費）：daily-index `form.{YYYYMMDD}.idx` 篩 form type "4" → 逐筆 .txt 全文擷取
  `<ownershipDocument>` XML。**SEC fair access 規定**：User-Agent 必須含聯絡 email
  （`config.EDGAR_USER_AGENT`）、≤10 req/s（本管線 sleep 0.15s ≈ 6.7 req/s，序列執行）。
- **Stooq**（免費、無金鑰）：日線 CSV `https://stooq.com/q/d/l/?s={ticker}.us&i=d`，
  供流動性否決、dip 評分與前瞻報酬。刻意不用 yfinance（CI 限流前科，擇穩）。

## 輸出契約（monitor 網頁依此讀取，鍵名不可改）

- `data/candidates_latest.json`：`{generated_at, scan_window_days, funnel_stats:{raw_filings,
  qualified_events, post_veto, final_candidates}, candidates:[{ticker, company, cluster_size,
  insiders:[{name,title}], total_buy_usd, score, score_breakdown, first_filing_date,
  entry_price_ref}]}`（entry_price_ref＝集群買入 VWAP）
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
- 市值帶評分待接 EDGAR company facts（sharesOutstanding）；v0 一律 0 分。
- 13F 慢錢共振加分未實作（設計檔 §1 第三層 ★★ 項）。
- M-Score 級操縱紅旗 v0 從簡為仙股排除。
