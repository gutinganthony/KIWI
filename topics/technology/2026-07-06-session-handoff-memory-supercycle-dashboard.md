---
title: KIWI Session 交接 — 記憶體超級循環研究 + Dashboard 修復 + 抄底引擎（2026-07 更新）
url: local
source: Session handoff（延續 2026-05-17 master handoff）
date_added: 2026-07-06
last_updated: 2026-07-06
topic: technology
tags: [session-handoff, memory-supercycle, HBM, dashboard, act-system, dip-buying-backtest, serenity, portfolio, resume-guide]
supersedes_context: 補充 ./2026-05-17-session-master-handoff.md（該檔仍是系統總覽的基礎）
---

## 給新 Session 的 Claude：讀這份 + 2026-05-17 master handoff 就能接續

使用者＝Jake（@afternoon.jk / gutinganthony），台灣金融投資顧問，正在建個人量化投資系統 + 代操朋友資金（Redefine Fund）。持台美日股。
**工作分支：`claude/focused-shannon-2UHlo`**（所有工作 commit+push 到這；HEAD 已同步遠端、工作區乾淨）。
語言：一律**繁體中文**回覆。研究筆記慣例：存 `topics/business/`，更新該資料夾 `INDEX.md`，commit+push。

---

## 一、Git 狀態（交接時）
- 分支 `claude/focused-shannon-2UHlo`，**工作區乾淨、全部已 push**。
- 注意：**自動 dashboard 的 bot commit（"auto: update dashboard data …"）現在也進這條分支**，所以 log 會有很多這種 commit，實質研究 commit 夾在其間。
- 每份研究都在 `topics/business/INDEX.md` 有索引。

## 二、三大支柱現況

### A) ACT 系統（AVI V5 估值 / CPI 崩盤概率 / TSI 科技壓力）+ 線上 Dashboard
- 程式：`projects/avi-v5/`（`scripts/run_monthly.py --v5`、`run_cpi.py`、`run_tsi.py`、`update_dashboard.py`）。
- 線上：`gutinganthony.github.io/KIWI/`（`docs/index.html`），GitHub Actions 每天自動更新。
- **本輪修好的 bug（重要）**：
  1. `src/data/sources/multpl.py` P/S dagger `†` 截斷 → AVI 鎖在 2024（已修：regex 抓值 + Current→今天）。
  2. Buffett 指標 `WILL5000IND` 被 FRED 2024-06 下架 → 改用 **`NCBEILQ027S`/GDP**（`src/data/sources/fred.py`），現值 ~233%。
  3. `src/engine/avi_core.py` as-of 用 `min()`→鎖舊月，改 **`max()`**（當月）。
  4. **Dashboard 已接真 AVI V5 管線**（`update_dashboard.py` 的 `compute_avi_from_v5()`，跑失敗自動退回舊代理）；payload 有 `avi.source`。
- **⚠️ 待處理**：`deploy-pages.yml`（發佈到 Pages）**2026-07-03 起失敗**，錯誤是 GitHub Pages 後端「Deployment failed, try again later」——**非我方程式問題**（docs 僅 0.19MB）。修法：Actions 分頁點 **Re-run failed jobs**，或等下次自動 deploy；查 githubstatus.com。**整合 token 無 actions:write 權限，Claude 無法代觸發（403）。**

### B) 抄底回測引擎（本輪新建，已驗證）
- `projects/avi-v5/scripts/dip_combo_backtest.py`：窮舉 VIX/F&G/RSI/回檔/200DMA 組合，去叢集 + 期間配對基準 + BH-FDR 多重比較 + 樣本外 + Wilson。
- `scripts/wavetrend.py`：LazyBear WaveTrend（`--ticker`(Mac yfinance)/`--csv`）。
- `scripts/fetch_data.py`：本機抓即時資料（雲端 yfinance/FRED 被擋，Mac 上跑）。
- **已驗證結論**：**美股「回檔≥10% 且站上200DMA」→ 抱 6 個月 95% 勝率（n=37, Wilson 82%, 樣本外 10/10）＝唯一過 FDR 的抄底訊號**；台股「深跌≥15-20% + 抱一年」~85%。→ 這是我們的**擇時紀律**。

### C) Serenity 卡脖子研究庫 + 網站
- `skills/serenity/`（框架）、`skills/wavetrend/`。
- 大量深掘在 `topics/business/2026-06-*-serenity-*.md`（美/日/台小型卡脖子）。
- **Serenity 網站儀表板** `docs/serenity/`（`data.json` + `index.html`），ACT dashboard header 有連結。
- 週報 workflow（週六排程，已修 OIDC/工具權限）。

## 三、本輪核心研究：記憶體超級循環系列（topics/business/）
讀這 6 檔即可掌握整條線（新→舊）：
1. `2026-06-23-institutional-vs-kiwi-view-comparison.md` — JB vs 我們觀點對照。
2. `2026-06-23-julius-baer-midyear-2026-outlook-summary.md` — JB 年中展望摘要。
3. `2026-06-10-memory-supercycle-battle-map.md` — **一頁戰情圖（先讀這張）**。
4. `2026-06-10-memory-supercycle-2030-part2-analyst-review.md` — Part II（三條件、DRAM/NAND、CXMT）。
5. `2026-06-10-hbm-token-economics-ai-semiconductor-endgame.md` — Part I（token=HBM size×頻寬）。
6. `2026-06-10-nvidia-rubin-cut-hbm4-slowdown-tracker.md` — Rubin 砍單事件追蹤。
+ `2026-06-10-serenity-scorecards-hbm-memory-optical.md`（10 檔評分，含 melt-up 後重評）、`2026-06-10-hbm-thesis-portfolio-impact-positioning.md`（持股影響）。
> 另有 6/30 兩檔延伸：`hbm-three-giants-…`、`memory-second-derivative-legacy-dram-arms-dealers-cxmt`。

**論點一句話**：記憶體（HBM+一般 DRAM）進入「成長型超級循環」（論點 80% 對、被 Rubin 事件證實）；**但股票已 melt-up 到 $1T/68–159x → 好生意、爛進場點；等回檔用紀律分批**。**總開關＝hyperscaler capex（+40% 未砍＝多頭續命）**。

## 四、Jake 持股 + 結論
- **宇瞻 8271**（記憶體模組）：一般 DRAM 缺貨是真順風（正向 re-read），但仍 commodity、CXMT 長期天敵。
- **MU**（期貨）：直接 HBM，但 $1T、最循環 → 控槓桿、等回檔。
- **村田 6981**：AI 伺服器 MLCC，add-on、手機稀釋。
- **JEM 6855**：日本電子材料＝記憶體/HBM **探針卡（測試卡脖子）**，已卡到位。
- **AAOI**：光互連/CPO，動能部位、CPO 中長期威脅 → 趁強控部位。
- **整體提醒**：整個書押同一個 AI/半導體賭注 → **缺分散**；可借 JB 的債券存續/黃金/歐洲/通訊分散。

## 五、要盯的關鍵節點（跨全系列）
1. **🔑 Hyperscaler capex 指引**（總開關）。
2. Rubin 實際出貨時程（HBM4 拐點）。
3. **CXMT / YMTC 擴產與良率**（DRAM/NAND 脫離週期論最大反證；CXMT 已追上 DDR5、或首發 LPDDR6）。
4. DRAM/HBM ASP 月線（2026 下半年走平與否）。
5. AVI/CPI/TSI 每日讀數（Mac 跑 `run_*` 或看 dashboard）。
6. 抄底訊號：美股自高 −10%+站200DMA / VIX≥30；台股深跌≥15-20%。

## 六、新 Session 開場白範本
> 繼續 KIWI。讀 `topics/technology/2026-07-06-session-handoff-…md` + `topics/technology/2026-05-17-session-master-handoff.md`。工作分支 claude/focused-shannon-2UHlo，繁中回覆。今天想做：____（例：更新記憶體戰情圖 / 跑 ACT 讀數 / 修 Pages deploy / 深掘某檔 Serenity）。

## Update Log
- 2026-07-06 v1.0：session 交接。ACT/dashboard 修復完成、抄底引擎建好、記憶體超級循環系列 6+2 檔、持股結論、Pages deploy 待重跑、關鍵節點清單。
</content>
