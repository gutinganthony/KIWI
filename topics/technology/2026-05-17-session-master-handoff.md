---
title: KIWI 專案總備忘 — 新 Session 快速上手指南
url: local
source: Session 2026-05-10 ~ 2026-05-17 完整紀錄
date_added: 2026-05-17
last_updated: 2026-05-17
topic: technology
tags: [session-handoff, guide, avi-v5, cpi, tsi, dashboard, fund-management, master-doc]
version: 1.0
---

## 給新 Session 的 Claude：讀這份文件就夠了

這是 KIWI 專案的**完整上下文**。使用者是台灣的金融投資顧問 @afternoon.jk (gutinganthony)，正在建立個人量化投資系統 + 代操朋友資金的事業。

---

## 一、使用者背景

- **身份**：台灣金融投資顧問，工作不忙，大量時間可投入
- **電腦**：Mac（MacBook Pro + Mac Mini），Python 3.9
- **帳號**：GitHub gutinganthony、FRED API key 已設定在 .env
- **目標**：
  1. 用量化系統管理自己和朋友的投資
  2. 代操 2-3 位朋友的資金（元大證券帳戶）
  3. 長期目標 AUM 3.2 億台幣 / 年毛收入 1000 萬台幣

---

## 二、已建成的三套風控系統

### AVI V5（市場估值指標，月度）
- **功能**：14 個指標 × 6 維度 → 0-10 分，看市場有多貴
- **指令**：`python3 scripts/run_monthly.py --v5`
- **程式碼**：`src/engine/` + `src/regime/` + `src/garch/` + `src/pipeline/`
- **已知問題**：Buffett Indicator（FRED WILL5000IND）和 P/S（multpl.com 只有年度資料需插值）資料源不完美，導致回測偵測率 2/5。原版 AVI V4 是 5/5。
- **回測結果**：V4.2（+Regime+GARCH）Sharpe 0.73、Max DD -29%（vs Buy&Hold -53%）

### CPI（崩盤概率指數，日頻）
- **功能**：12 個指標 → 0-100 分，看短期崩盤概率
- **指令**：`python3 scripts/run_cpi.py` 或 `python3 scripts/run_dashboard.py`（瀏覽器視覺面板）
- **程式碼**：`src/cpi/__init__.py` + `src/cpi/data.py` + `src/cpi/backtest.py`
- **回測**：4/4 大崩盤偵測（Dot-com 47, GFC 51, COVID 39, 2022 41），Lead time 23-42 天
- **Dashboard**：`dashboard/template.html`（深色主題、EN/中文切換、一年歷史圖、hover tooltip）
- **使用手冊**：`python3 scripts/run_dashboard.py --guide`（HTML 版）

### TSI（科技壓力指數，日頻）
- **功能**：9 個指標（含 10Y+30Y 國債）→ 0-100 分，看科技股壓力
- **指令**：`python3 scripts/run_tsi.py` 或 `--history 252`（一年趨勢）
- **程式碼**：`src/tsi/__init__.py` + `src/tsi/data.py`
- **回測**：過去一年 7/7 壓力事件全數偵測，1-14 天提前預警
- **2026-05-15 驗證**：5/12 起連續 4 天 CAUTIOUS（44-54），提前 3 天預警殖利率衝擊

---

## 三、Dashboard 現況

### 已完成
- CPI 視覺面板（`run_dashboard.py`）：CPI 分數 + AVI 分數 + 12 指標拆解 + 一年歷史圖 + hover tooltip + EN/中文
- CPI 使用手冊（`run_dashboard.py --guide`）：HTML 版完整指南
- Pine Script 模板（`pine/cpi_indicator.pine`）

### 待做（下一步）
- **統合 Dashboard**：把 CPI + TSI + AVI 合成一個頁面
- **部署到 GitHub Pages**：GitHub Actions 每天自動跑 → 生成靜態 HTML → 部署到 `gutinganthony.github.io/KIWI/dashboard`
- **TradingView MCP**：Playwright 自動化（Phase 5）

---

## 四、檔案結構

```
KIWI/
├── projects/
│   ├── avi-v5/                          ← 主要程式碼
│   │   ├── .env                         ← FRED_API_KEY（不上傳 git）
│   │   ├── ARCHITECTURE.md              ← AVI V5 完整架構
│   │   ├── CPI_ARCHITECTURE.md          ← CPI 技術文件
│   │   ├── config/
│   │   │   ├── indicators.yaml          ← 14 個 AVI 指標
│   │   │   ├── avi_weights.yaml         ← 6 維度權重
│   │   │   └── regime_params.yaml       ← Regime + GARCH 參數
│   │   ├── src/
│   │   │   ├── data/sources/            ← FRED, multpl, yfinance
│   │   │   ├── engine/                  ← AVI V4 核心 + percentile
│   │   │   ├── regime/                  ← 4-state HMM
│   │   │   ├── garch/                   ← GARCH(1,1)
│   │   │   ├── pipeline/               ← V5 整合
│   │   │   ├── cpi/                     ← CPI 12 指標
│   │   │   └── tsi/                     ← TSI 9 指標
│   │   ├── backtest/                    ← AVI 回測框架
│   │   ├── dashboard/
│   │   │   ├── template.html            ← Dashboard 模板
│   │   │   ├── guide.html               ← 使用手冊 HTML
│   │   │   └── cpi_dashboard.py         ← 生成器
│   │   ├── pine/
│   │   │   └── cpi_indicator.pine       ← TradingView Pine Script
│   │   ├── scripts/
│   │   │   ├── run_monthly.py           ← AVI V5（--v5 flag）
│   │   │   ├── run_cpi.py              ← CPI（--backtest flag）
│   │   │   ├── run_tsi.py              ← TSI（--history N flag）
│   │   │   ├── run_dashboard.py         ← 視覺面板（--guide flag）
│   │   │   └── run_backtest.py          ← AVI 回測比較
│   │   └── tests/
│   │       └── test_cpi_validation.py   ← CPI 嵌入式驗證
│   ├── second-brain/                    ← Obsidian vault starter kit
│   ├── skills/                          ← /evaluate-idea Skill
│   └── quant/                           ← 4 個量化專案
│
├── topics/
│   ├── business/
│   │   ├── 2026-05-16-ai-memory-chip-boom-bust-analysis.md   ← AI 記憶體風險
│   │   ├── 2026-05-17-h2-investment-strategy.md               ← H2 投資策略
│   │   ├── 2026-05-17-tsi-backtest-tech-run-amok.md          ← TSI 回測 + 圖表驗證
│   │   ├── 2026-05-17-fund-management-plan.md                 ← 代操方案
│   │   ├── 2026-05-17-fund-scaling-analysis.md                ← 營收路徑（全台幣）
│   │   ├── 2026-05-17-fund-premortem.md                       ← 6 種死法
│   │   ├── 2026-05-17-fund-death2-death3-solutions.md         ← 友誼+募資解法
│   │   ├── 2026-05-17-fund-contract-clauses.md                ← 風控+溝通+免責條款
│   │   └── 2026-05-17-fund-practical-setup.md                 ← 實務執行+LINE確認
│   └── technology/
│       ├── 2026-05-14-avi-v5-cpi-session-progress.md          ← 系統開發進度
│       ├── 2026-05-14-cpi-crash-probability-index.md          ← CPI 使用指南（繁中）
│       └── 2026-05-17-tradingview-mcp-dev-memo.md             ← TradingView 開發備忘
```

---

## 五、下一步待辦事項（優先序）

### P0：統合 Dashboard + 部署到 GitHub Pages
- 把 CPI + TSI + AVI 合成一個網頁
- GitHub Actions 每天 08:00 TST 自動跑
- 部署到 `gutinganthony.github.io/KIWI/dashboard`
- 任何裝置手機/電腦都能看

### P1：TradingView MCP（Phase 5）
- 方案 A（輕量）：自動生成 Pine Script 含 CPI+TSI+AVI
- 方案 B（完整）：Playwright 控制 TradingView 瀏覽器
- 詳細規格在 `topics/technology/2026-05-17-tradingview-mcp-dev-memo.md`

### P2：修復 AVI V5 資料源
- Buffett Indicator：WILL5000IND 可能也有問題
- P/S Ratio：multpl.com 只有年度資料，需更好的來源
- 目標：回測偵測率從 2/5 提升到 5/5

### P3：代操月報自動化
- 每月自動生成各帳戶績效報告
- 整合 TSI/CPI/AVI 分數到月報
- 自動發 LINE 通知

---

## 六、環境設定（換電腦時）

```bash
# 1. Clone
git clone https://github.com/gutinganthony/KIWI.git
cd KIWI
git checkout claude/add-kiwi-integration-VwVzs

# 2. 安裝套件
cd projects/avi-v5
pip3 install -r requirements.txt

# 3. 設定 API Key
echo "FRED_API_KEY=8181079f96c8210790797e299aca965a" > .env

# 4. 測試
python3 scripts/run_tsi.py              # TSI
python3 scripts/run_dashboard.py        # CPI Dashboard
python3 scripts/run_monthly.py --v5     # AVI V5
```

---

## 七、新 Session 開場白範本

視你要做什麼，複製以下其中一個：

**做 Dashboard 部署：**
> 繼續 KIWI 專案。讀 `topics/technology/2026-05-17-session-master-handoff.md` 了解完整上下文。任務：把 CPI+TSI+AVI 統合到一個 Dashboard 然後部署到 GitHub Pages，讓我手機也能看。

**做 TradingView MCP：**
> 繼續 KIWI 專案。讀 `topics/technology/2026-05-17-session-master-handoff.md` 和 `topics/technology/2026-05-17-tradingview-mcp-dev-memo.md`。任務：做 TradingView MCP Phase 5。

**修 AVI 資料源：**
> 繼續 KIWI 專案。讀 `topics/technology/2026-05-17-session-master-handoff.md`。任務：修復 AVI V5 的 Buffett Indicator 和 P/S Ratio 資料源，讓回測偵測率從 2/5 提升到 5/5。

**做代操月報：**
> 繼續 KIWI 專案。讀 `topics/technology/2026-05-17-session-master-handoff.md` 和 `topics/business/2026-05-17-fund-practical-setup.md`。任務：建立自動化月報系統。

---

## Update Log

- 2026-05-17 v1.0: 完整 session handoff 文件，涵蓋所有系統、檔案結構、待辦、環境設定、開場白範本。
