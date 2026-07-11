# Serenity 每週篩選器（weekly-screen）

**執行時機**：每週日 & 週三（週日＝週末覆盤，全球週五收盤後；週三＝接週二美股收盤 + 月初合約價）
**節奏**：每月第一個週日＝**全掃**（重定價 + 觸發/否證 + 催化劑 + 新標的獵殺）；其餘週日 + 每個週三＝**輕量**（跳過新標的獵殺，省 credits）
**輸出**：dated digest + 更新 watchlist + 更新 `docs/serenity/data.json`（含 🟣 holding 層）+ commit/push；**有燈號翻轉 / 🟢🔴觸發 / 🟣持倉賣訊 / >15% 跳動才推 Telegram+LINE，無變化靜默**（`serenity_alert.py`）
**框架**：`skills/serenity/SKILL.md`；名單：`skills/serenity/watchlist.md`

> **核心紀律（本輪反覆踩到的教訓）**：資料幾週就過時（Seikoh 9 天 +30%、MEC 15×→33×、santec 衝破 $2B）。**第一步永遠先重拉現價市值，不靠記憶。**

---

## 執行步驟

### Phase 0 — 載入狀態
- 讀 `skills/serenity/SKILL.md`（框架）+ `skills/serenity/watchlist.md`（現役名單 + 觸發價/否證條件 + 上週價格快照）
- 記下上次篩選日期與各檔上次價格

### Phase 1 — 重定價（鐵律）
對 watchlist 每一檔（Serenity 候選 + 週期擇時大型股 + **🟣 我的持倉追蹤**如 DRAM ETF 都要）：
- WebSearch 重拉 **LIVE 現價 + 市值 + forward P/E**（財經網站常 403，用搜尋 snippet 交叉驗證；注意日圓億/兆、台幣億的單位陷阱與 10× 誤植）
- 計算 vs 上週變化 %
- 🚩 標記任何**一週移動 >15%** 的（無論漲跌）
- 更新 watchlist.md 的市值快照欄 + 「上次現價更新」日期

### Phase 2 — 觸發價 & 否證檢查
對每一檔，比對現價與：
- **買進觸發線** → 🟢 命中 = 主動提示（含建倉區間）
- **賣出/否證線** → 🔴 命中 = 主動提示
- 逐條檢查該檔 watchlist 列的**否證條件**（新增資/ATM、中國 >40%、單一客戶 >50%、指引 miss、內部人賣股、CB 稀釋…）
- 對過 <$2B 硬門檻的標的：確認**市值是否仍 <$2B**（漲出框要標記降評）

### Phase 3 — 催化劑日曆（未來 1–2 週）
- 掃各檔的**財報日、有価証券報告書日、指數調整、政策日期、IPO/上市日**
- 列出未來 14 天內事件 + 該盯的具體資訊（如客戶集中度、sandbag 是否延續）

### Phase 4 — 新標的獵殺（僅全掃模式＝每月第一個週日；輕量日跳過）
- 輕掃 **US / 日本 / 台灣 / 韓國** 四市場，找任何新浮現的小型（<$2B）卡口
- 聚焦追蹤層：HBM/探針卡/先進封裝、光通訊/CPO/FAU、記憶體全鏈（DRAM/NAND/RCD/控制器）、玻璃基板/TGV、CoPoS/COUPE
- 只浮出「plausibly 過 4 條硬門檻」的名字 → 標記為待深掘（不在週報做完整 Step 1–9，只 flag）
- 同步監控 IPO 管線（Ayar Labs / Lightmatter / Korea Instrument / CXMT 等）

### Phase 5 — 輸出
1. 寫 dated digest → `topics/business/serenity-weekly/YYYY-MM-DD.md`
2. 更新 `skills/serenity/watchlist.md`（價格快照 + 任何觸發/降評/新增）
3. **更新網站儀表板資料 `docs/serenity/data.json`**（結構化，餵 `docs/serenity/index.html`）——
   欄位見下方 schema；`updated` 填當日、`headline` 一句話狀態、`macro` 五項燈號、
   `positions` 全名單（tier/flag/現價/週變化/觸發/note）、`catalysts` 未來事件、`candidates` 新標的。
   **重拉到的現價要填進每檔 `price` 與 `wk`（週變化）。** GitHub Pages 會自動部署到
   `gutinganthony.github.io/KIWI/serenity/`。
4. 在 INDEX.md 加該週 digest 連結
5. `git commit` + `git push`（**merge/推到 main 才會觸發 Pages 部署**；日常 digest 可留分支，
   但 `docs/serenity/data.json` 需進 main 網站才更新）
6. **通知使用者：完整 digest**

**`docs/serenity/data.json` schema**（維持既有欄位，逐週覆蓋值）：
`updated` `as_of_note` `headline` · `macro[]{signal,state(ok/watch/alert),note}` ·
`tiers[]{key,label,color}`（**必含 `holding` 層＝使用者實際持倉，如 DRAM ETF，置頂、勿與候選混淆、每週重拉現價**）· `positions[]{tier,ticker,name,market,mcap,fwd_pe,price,wk,direction,trigger,note}` ·
`catalysts[]{date,event}` · `candidates[]{name,note}`

### Phase 6 — 宏觀共同前提監控（每週檢查，任一出現 → 整體降權提示）
- AI capex 大廠（NVIDIA/Google/AWS/MSFT）公開下修指引【＝路線圖 T6 總否證】
- JPY 急升 10%+（日系標的同步打折）
- 記憶體週期轉過剩訊號：CXMT DDR5 擴產進度、TrendForce 合約價漲幅收斂、需求破壞（Gartner PC/手機出貨）【＝T1：合約價 QoQ 轉負＝記憶體出場鐘】
- CXMT 實體清單是否公布（中國記憶體鏈頭號尾險）
- 1.6T 光模組量產時程延後

**路線圖轉折訊號 T1–T6（詳見 `topics/business/2026-07-10-serenity-2026-2030-sector-roadmap.md`；每週逐項評估並更新 data.json 對應宏觀燈的 state/note，燈翻轉會自動觸發 Telegram+LINE 警報）：**
- **T2 CPO 滲透（光互連收場鐘）**：查 CPO 在新世代交換器滲透率（>20–30%＝翻 watch/alert）、1.6T 模組 ASP 年殺幅度、EML 交期是否正常化
- **T3 記憶體反週期買點距離**：查 SKH/MU P/B（SKH <2.3× 或 MU 2–3×＝逼近）、有無大廠減產/砍 capex 公告、合約價是否連兩季下跌——「至少兩項同時」才翻 alert（＝2028 冬天買點開啟）
- **T4 混合鍵合認證（封裝革命開關）**：查三星/SKH 16-hi hybrid bonding 是否過 NVIDIA 認證、TSMC 玻璃基板 roadmap、CoPoS 量產 PO——過關＝翻 alert（BESI 開跑＋Towa 喪鐘）
- **T5 AI 電力確認**：Mersen DC 季銷售 ≥€15M（7/30 首驗）、NVIDIA 800VDC 機櫃出貨、變壓器交期

---

## Digest 格式（每週輸出）

```
# Serenity 週報 YYYY-MM-DD

## 一句話狀態
本週有無 actionable：🟢觸發命中 / 🔴否證命中 / ⏰本週催化劑 / 😴平靜週

## 1. 重定價表
| 標的 | 現價 | 週變化 | vs 觸發價 | 備註 |

## 2. 🟢 觸發命中 / 🔴 否證命中（若有，逐檔說明動作）

## 3. ⏰ 未來 2 週催化劑

## 4. 🆕 新標的候選（若有，flag 待深掘）

## 5. 🌍 宏觀前提狀態（Phase 6 結果）

## 6. ✅ 本週待辦（該做的具體動作）
```

---

## 手動執行

任何 session 都可手動觸發：說「跑 Serenity 週報」或 `/serenity weekly`，即依本協定執行。

## 自動執行

- **GitHub Actions**（真·自動）：`.github/workflows/serenity-weekly.yml`，**週日 + 週三**排程（每月第一個週日全掃、其餘輕量）；需 repo secret `ANTHROPIC_API_KEY`。變化警報經 `projects/avi-v5/scripts/serenity_alert.py` → Telegram + LINE（跟 ACT 每日訊號同頻道），無變化靜默
- **Claude Code web 排程 session**：在 web UI 設週日+週三排程、prompt =「依 skills/serenity/weekly-screen.md 跑 Serenity 週報」
- **session 內 cron**：僅本 session 活著時有效、7 天後過期（僅作即時橋接）

*非投資建議。每週快照，價格易變，行動前重新確認。*
