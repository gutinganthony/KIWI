---
title: KIWI 超級 Session 總結 — 2026-05-10 ~ 2026-05-17 完整交付清單
url: local
source: Session 01B4wAdptHN16JP2FY2SZ7on
date_added: 2026-05-17
last_updated: 2026-05-17
topic: technology
tags: [session-summary, master-doc, avi-v5, cpi, tsi, fund-management, investment]
version: 1.0
---

## 這個 Session 做了什麼

這是 KIWI 專案有史以來最長的 session，從 2026-05-10 到 2026-05-17，橫跨 8 天。以下是完整交付清單。

---

## 一、量化投資系統（3 套）

### AVI V5（市場估值，月度）
- 14 指標 × 6 維度 → 0-10 分
- Phase 1-4 完成：Data → Engine → Regime HMM → GARCH → Backtest
- `python3 scripts/run_monthly.py --v5`

### CPI（崩盤概率，日頻）
- 12 指標 → 0-100 分
- 回測：4/4 大崩盤偵測，Lead time 23-42 天
- HTML Dashboard + 使用手冊 + EN/中文切換
- `python3 scripts/run_dashboard.py`

### TSI（科技壓力，日頻）
- 9 指標（含 10Y+30Y 國債）→ 0-100 分
- 回測：過去一年 7/7 事件偵測
- 2026-05-15 殖利率衝擊：提前 3 天預警（CAUTIOUS）
- `python3 scripts/run_tsi.py`

---

## 二、Dashboard & 自動化

- CPI 視覺面板（深色主題、gauge、指標條、一年歷史圖、hover tooltip）
- CPI 使用手冊 HTML（`--guide`）
- Pine Script 模板（TradingView）
- Telegram 自動推播（`scripts/notify.py` + GitHub Actions）
- AVI 分數整合進 Dashboard

---

## 三、Second Brain（Obsidian）

- 完整 vault 結構（7 資料夾 + KIWI symlink）
- CLAUDE.md（使用者背景 + 專案 + 目標）
- 6 個 McKinsey 級診斷 Prompt（繁中）
- 7 個 Obsidian 模板
- 報告情報管線（17 免費來源）
- setup-mac.sh（iCloud 同步）
- 已安裝在使用者的 Mac 上

---

## 四、/evaluate-idea Skill

- 8 維度創業想法評估
- Paul Graham + a16z + YC 框架
- 4 案例庫（Yoga App、Amazon Review、AVI V4、Yuni）
- Launch Confidence Score 0-100
- 已安裝在 `~/.claude/skills/evaluate-idea/`

---

## 五、KIWI 知識庫文章（本 session 新增 20+ 篇）

### Technology
| 文章 | 主題 |
|------|------|
| CPI 使用指南（繁中）| 10 指標白話說明 + 回測表 + 每日用法 |
| AVI V5 + CPI 開發進度 | 系統備份 |
| TradingView MCP 開發備忘 | Phase 5 接續指南 |
| Session Master Handoff | 新 session 完整上下文 |
| 新加坡外長 AI 第二大腦 | NanoClaw + Obsidian + 6 個應用點 |

### Business — 投資分析
| 文章 | 主題 |
|------|------|
| AI 記憶體崩盤風險驗證 | Situational Awareness 框架 + 5 先行指標 |
| TSI 回測 + Tech Run Amok | 7/7 偵測 + Capital Context 100 年 3 次驗證 |
| HBM 光互連 CPO | Jukan 觀點驗證 8/10 |
| SoCAMM 供需缺口 | Vera CPU 需求推算 + CXMT 鬼故事拆解 |
| 光子投資邏輯 v2.0 | 補齊 $AVGO, $MRVL, $CRDO + 時間軸 |
| 2026 H2 投資策略 | 三階段 + 事件日曆 + 配置建議 |

### Business — 代操事業
| 文章 | 主題 |
|------|------|
| 代操方案 | IBKR/券商 + 收費模式 + 流程 |
| 營收路徑分析 | AUM vs 毛收入（全台幣）|
| Premortem 6 種死法 | 風險分析 |
| 死因 2+3 解法 | 友誼保護 + 內容行銷漏斗 |
| 合約條款設計 | 風控 + 溝通 + 免責 |
| 實務執行方案 | 券商帳密 + LINE 確認模板 |

### Other
| 文章 | 主題 |
|------|------|
| IG 珍藏 209 篇分類 | 10 類 + Top 5 推薦 |

---

## 六、IG 珍藏整理
- 209 篇自動分類（Tech 65, Animals 55, Finance 42...）
- Tech/Finance/Startup 各 Top 5-10 推薦
- 跨類別洞察

---

## 七、4 個量化專案（Python）
- Market Regime Clustering（HMM/K-Means）
- IV Surface Builder
- CVaR Portfolio Optimization
- Event-Driven Backtester

---

## 八、待辦事項（下次 Session）

### P0
- [ ] 統合 Dashboard（CPI+TSI+AVI 一頁）部署到 GitHub Pages
- [ ] Telegram 推播設定（Bot Token + Chat ID + GitHub Secrets）

### P1
- [ ] TradingView MCP Phase 5
- [ ] 修復 AVI V5 資料源（Buffett + P/S）→ 回測 5/5

### P2
- [ ] 代操月報自動化
- [ ] Mnemon 式知識圖譜整合到 Obsidian
- [ ] CPI/TSI 加入「慢性出血」偵測

### P3
- [ ] AVI V4 SaaS 化評估（/evaluate-idea）
- [ ] 內容行銷啟動（IG/Threads/Newsletter）

---

## 九、關鍵決策紀錄

1. **代操用券商帳密共享**，不用 IBKR Advisor
2. **合約用 LINE 白話確認**，不用正式合約（降低「經營業務」外觀）
3. **費用白話化**：「每年收帳戶金額的 1.2%」而非「管理費率 1.2% p.a.」
4. **管理費 300 萬/年前不辭職**（AUM ≥ 2.5 億）
5. **毛收入 1000 萬才開公司**（AUM ~3.2 億）
6. **投資策略三階段**：觀察(5-7月) → 防守(8-9月) → 部署(10-12月)

---

## Update Log

- 2026-05-17 v1.0: 超級 session 完整總結。
