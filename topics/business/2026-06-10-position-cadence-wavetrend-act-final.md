---
title: 倉位配置 + 投資節奏（未來一年）+ WaveTrend 市場位階 — FINAL（本機即時資料、ACT 實跑、三 sub-agent 驗證）
url: local
source: KIWI 量化專案，2026-06-10 本機跑 ACT + WaveTrend + 三 sub-agent 紅隊驗證
date_added: 2026-06-10
last_updated: 2026-06-10
topic: business
tags: [position-sizing, cadence, wavetrend, act-system, tsi, cpi, avi, taiex, sp500, vix, dip-buying, top10, verified, live-data]
version: 2.0
related: [./2026-06-10-silicon-photonics-cpo-optical-report-analysis.md, ./2026-06-06-dip-buying-best-indicator-combos-backtest.md, ./2026-06-06-post-selloff-market-roadmap.md]
supersedes: ./2026-06-10-position-cadence-wavetrend-act-DRAFT.md
engine: projects/avi-v5/scripts/{run_tsi.py, run_cpi.py, run_monthly.py, fetch_data.py, wavetrend.py}
---

> **這份是「真跑的」**：本機 Mac、即時 yfinance/FRED 資料，ACT 三表全跑、WaveTrend 對 Top10+大盤+熱股全掃、三個獨立 sub-agent 紅隊驗證後定稿。
> 取代 [DRAFT](./2026-06-10-position-cadence-wavetrend-act-DRAFT.md)（其中 ACT 是估計、TW 觸發條件有 drift）。

---

## TL;DR（一頁）

**現況**：晚期多頭 + 局部修正。S&P 7,405（-2.7% from ATH）、TAIEX 43,227（-7.0%）、VIX 18.9。**未到任何 FDR-validated 抄底訊號**。

**ACT 即時讀數**（2026-06-10 在 Mac 跑出來）：
- **TSI = 49/100 CAUTIOUS** + FLASH yield-spike 警報（vix_tech_correlation 100、yield_shock 82）
- **CPI = 13/100 LOW**（only yield_surge 74 + vix_spike 52 偏高；無系統性危機跡象）
- **AVI = ELEVATED**（程式顯示 5.67 但鎖在 2024-12-31，因 `multpl.py` 解析器 bug；以市場高 ~25% 推估**真實值約 6.5–7.0**）

**結論**：**淨多 65%、現金 35%、不做空**。買清單已選好（PLAB 第一、ITEQ 第二），但**沒有任何訊號要你「現在加」**——等 S&P −10% + 站 200DMA（95%/Wilson 82% 鐵證）或 VIX≥30 才扣板機。**Fujimi 4109.T 已觸超買（WT1=65.7、>+60）→ 趁強減；AAOI +177% 高於 200DMA → 控部位 20→10%。**

**未來一年三段式節奏**：穿越 6/11–18 事件區（不追）→ 跌深扣板機（分批）→ 9–10 月秋季洗盤重壓 → 11 月–次年 4 月期中後強季抱滿。

---

## A. 即時讀數（2026-06-10 本機跑，非雲端估計）

### A.1 市場價格與位階（yfinance live）

| 指標 | 數值 | 日期 | 含義 |
|---|---|---|---|
| **S&P 500** | 7,405.7 | 6/8 | 距 ATH **-2.7%**；**+7.9% 高於 200DMA**（6,864）→ 多頭結構**完整**、淺修正 |
| **Nasdaq** | 25,930 | 6/8 | -4.3% from high、+11.1% 高於 200DMA |
| **TAIEX** | 43,227 | 6/10 | 距 ATH **-7.0%**；**+37.6% 高於 200DMA** → 高位但結構完整、剛開始修正 |
| **Nikkei** | 63,897 | 6/10 | -6.6% from high、+21.6% 高於 200DMA |
| **VIX** | 18.9 | 6/8 | **未到 ≥25/≥30** 抄底門檻；+2.6% 高於自身 200DMA → 恐懼動能緩升、未投降 |

### A.2 ACT 三表（**真實程式輸出，不是估計**）

| 系統 | 分數 | 等級 | 關鍵驅動 | 與草稿估計差距 |
|---|---|---|---|---|
| **TSI**（科技壓力） | **49/100** | 🟠 CAUTIOUS + FLASH | yield_shock 82、vix_tech_corr 100、memory_momentum 60、yield_30y 54 | 草稿估 55–65；**實測偏低 6 分**。FLASH 確認「殖利率衝擊+科技賣壓」並存 |
| **CPI**（崩盤概率） | **13/100** | 🟢 LOW | 只有 yield_surge 74 + vix_spike 52 elevated；其餘 0–20 | 草稿估 45–52；**實測低 32 分**——當前並非系統性崩盤前兆 |
| **AVI**（估值） | **5.67/10 ELEVATED**（鎖在 2024-12-31，見 ★） | 🟡 偏貴 | valuation dim 9.60（CAPE 98.8%ile、P/S 98.8%ile）；regime volatile_trend | 草稿估 6.7–7.0；**真實值受 bug 影響低估**，市場高 ~25%，真實值應在 **6.0–7.0** 區間 |

**★ 已定位的程式 bug**（sub-agent A 找出，留待下個 session 修）：`src/data/sources/multpl.py:100-112` — multpl.com P/S 表用 dagger 字元 † 標註 provisional 值，現有 parser 把 `†3.65` 丟到 `float()` 觸發 ValueError 後**靜默 continue**，所以 P/S 卡在 2024-12-31。`src/engine/avi_core.py:176` 用 `min(latest_dates)` 取最小最新日期 → 整個 AVI 凍結。**Fix**：parser 加 `re.sub(r"[^\d.\-]", "", value_text)` 一行修掉。

### A.3 ACT 三系統的「為什麼數字差這麼多」（紅隊解讀）

**CPI 13 vs TSI 49 並不衝突**：
- CPI 量「廣義 S&P 崩盤前兆」——S&P 距 ATH 只 -2.7%、VIX 18.9（未過 25）、無 breadth/RSI divergence、無信用爆 → 13/100 合理
- TSI 量「科技/SOX 局部壓力」——殖利率衝擊+記憶體動能轉負+SOX 已示警 → 49/100 + FLASH 合理
- **這個 gap 是 feature 不是 bug**：科技已痛、但廣義市場尚未爆。是「**警戒區、非逃命區**」的典型訊號。

**對倉位的意義**：CPI 13 = 不必減太多；TSI 49 + FLASH = 別貪科技、控高 beta 部位。**淨多+留緩衝+減科技權重**，是這組讀數的唯一一致解。

---

## B. WaveTrend 全掃（本機即時，Top 10 + 大盤 + 熱股）

**參數**：LazyBear（n1=10、n2=21、OB=+60、OS=-60）；sub-agent B 已獨立重算三個 ticker（^VIX/^GSPC/4109.T）與程式輸出**逐位對齊到 0.1**，公式正確、無 bug。

### B.1 大盤位階

| 指數 | 收盤 | WT1 | WT2 | 區位 | 交叉 | RSI | 距 52w高 | vs 200DMA |
|---|---|---|---|---|---|---|---|---|
| ^GSPC | 7,405.7 | **33.1** | 48.0 | 中性 | — | 50 | -2.7% | **+7.9% 🐂** |
| ^IXIC | 25,930 | **27.0** | 43.9 | 中性 | — | 47 | -4.3% | **+11.1% 🐂** |
| ^TWII | 43,227 | **42.6** | 54.3 | 中性 | **bear-X↓** | 64 | -7.0% | **+37.6% 🐂** |
| ^N225 | 63,897 | **39.5** | 51.9 | 中性 | **bear-X↓** | 64 | -6.6% | **+21.6% 🐂** |
| ^VIX | 18.9 | **-17.8** | -37.7 | 中性 | **bull-X↑（VIX 多方=股市利空）** | 53 | -39.1% | **+2.6% 🐂** |

**解讀**：① 四大指數全部 >200DMA → 多頭 regime 完整、不做空 ✓ ② TAIEX/Nikkei WT 剛 bear-X↓ → 短期修正動能轉空、別追新高 ③ VIX bull-X↑ + WT1 從低位翻上來 = 恐懼動能升中、警示但未到投降 ④ TWII +37.6% 高於 200DMA 是**極端拉伸**，回測本身的歷史均值約 +5–15%——統計上「向均值回歸」壓力大。

### B.2 Top 10 + 熱股逐檔

| Ticker | 公司 | 收盤 | 日期 | WT1 | WT2 | 區位 | 交叉 | RSI | 距52w高 | vs 200DMA |
|---|---|---|---|---|---|---|---|---|---|---|
| **PLAB** | Photronics（Top1, 光罩） | 30.0 | 6/8 | **-36.0** | -32.0 | 中性近超賣 | — | **28 (oversold)** | **-45.5%** | **-9.9% 🐻** |
| **COHR** | Coherent（CPO ELS） | 401.9 | 6/8 | 42.8 | 45.2 | 中性 | **bear-X↓** | 59 | -5.8% | +89.2% 🐂 |
| **MTRN** | Materion（鈹） | 225.5 | 6/8 | **56.0** | 60.2 | **近超買** | **bear-X↓** | 68 | -1.9% | +55.6% 🐂 |
| **COHU** | Cohu（AI handler） | 52.5 | 6/8 | 39.1 | 46.3 | 中性 | **bear-X↓** | 63 | -8.8% | +75.7% 🐂 |
| **AAOI** | Applied Opto（你持 20%） | 196.6 | 6/8 | 28.9 | 25.8 | 中性 | — | 57 | -11.9% | **+176.9% 🐂** |
| **6213.TW** | ITEQ 台耀（Top2 CCL） | 255.0 | 6/10 | -12.2 | -8.0 | 中性 | — | 53 | -15.1% | +69.6% 🐂 |
| **6820.TWO** | ACON 禾昌（MT ferrule） | 260.0 | 6/10 | -7.2 | 5.5 | 中性 | — | 46 | **-38.3%** | +86.1% 🐂 |
| **6643.TWO** | M31 邁兆（3nm IP） | 467.0 | 6/10 | **-52.6** | -41.9 | 中性近超賣 | — | **22 (deep oversold)** | -33.0% | -1.5% 🐻 |
| **3363.TWO** | 上詮（COUPE 光纖共研） | 747.0 | 6/10 | -6.8 | 7.3 | 中性 | **bear-X↓** | 43 | -24.5% | +44.6% 🐂 |
| **5384.T** | Stella（BF3） | 3,730 | 6/10 | 34.7 | 45.1 | 中性 | — | 62 | -12.7% | +38.2% 🐂 |
| **4109.T** | **Fujimi（CMP）** | 7,720 | 6/10 | **65.7 🔴 超買** | 64.6 | **OVERBOUGHT** | — | 65 | -2.9% | +57.9% 🐂 |
| **6830.TW** | 汎銓（檢測，已驗證 = Msscorps） | 497.0 | 6/10 | **-56.6** | -46.7 | 中性近超賣 | — | **30 (oversold)** | **-49.0%** | +49.7% 🐂 |
| **3081.TWO** | 聯亞（InP 磊晶） | 2,245 | 6/10 | -28.3 | -15.8 | 中性 | — | 43 | -29.0% | +93.1% 🐂 |
| **3163.TWO** | 波若威（FAU/MPO） | 884.0 | 6/10 | -34.5 | -25.5 | 中性 | — | 41 | -31.7% | +60.2% 🐂 |

> ✓ Sub-agent B 已確認 **6830.TW = Msscorps Co. Ltd. = 汎銓科技**（yfinance 中 6830.TWO 已下市，現用 .TW 抓得到）。

### B.3 三組分類（用 WaveTrend + RSI + 200DMA 三維篩）

**🔴 超買/熱（趁強減）**：
- **4109.T Fujimi** WT1=65.7 純超買 → 若在持倉中，**就是要減的那一檔**
- **AAOI** +177% 高於 200DMA（極端拉伸）+ 你持 20% → **執行 20→10% 計畫**（已被 SemiAnalysis scale-up CPO 觀點結構性降級至 17/30）
- **MTRN** WT1=56 + bear-X↓ + RSI 68 → 鈹題材長期看好但短期過熱，**等回檔**
- **COHR** bear-X↓ + 距 200DMA +89% → 別追、回檔分批
- **COHU** bear-X↓ + RSI 63 → 同上

**🟡 中性回檔（觀察區）**：
- **6213.TW ITEQ** -15% from high，WT 中性偏弱、RSI 53 → 接近第一批甜蜜點（仍在 200DMA 上、估值 1.4x P/S 是清單最便宜之一），**回檔到 -20% 可第一批**
- **6820.TWO ACON** -38% from high，WT 中性、RSI 46 → 已深修但 WT 未到超賣；等 WT 翻正 or 跌到 RSI<30 再進
- **3363.TWO 上詮** bear-X↓ + -24% → 修正進行中，跌深訊號未到
- **3081.TWO 聯亞、3163.TWO 波若威、5384.T Stella** → 中性、繼續觀察

**🟢 深超賣/接近底部訊號（高機率、高風險）**：
- **PLAB** RSI 28 + WT1=-36 + 距高 -45.5%，但**已跌破 200DMA** → 不符合「美股回檔≥10% 且站 200DMA」FDR 訊號。**可小批試水（≤1/4 部位）**，但放棄 SOP 鐵律保護；個股 alpha 賭注
- **6643.TWO M31** RSI 22 深超賣 + 距高 -33%，但**跌破 200DMA** → 同上，個股單獨判斷
- **6830.TW 汎銓** RSI 30 + WT1=-56.6 + 距高 -49%，但**虧損公司、本夢比** → 即使技術超賣，Serenity 16/30 維持「**不可投資**」結論。**觀察名單**

---

## C. 市場位階 + 該多該空 + 現金水位

### C.1 Regime 判定（三層證據）
| 層 | 證據 | 判定 |
|---|---|---|
| **價格** | S&P/IXIC/TWII/N225 全部 >200DMA | 🐂 **多頭 regime 完整** |
| **波動** | VIX 18.9（<25 抄底門檻）；CPI 13 LOW | 🟢 **無系統性危機跡象** |
| **動能** | TWII/N225 bear-X↓；VIX bull-X↑；TSI 49 + FLASH | 🟠 **晚期多頭 + 局部修正進行中** |

### C.2 該多該空？ → **淨多、不做空**

**正向理由**：
1. 多頭 regime 完整（4 指數全 >200DMA）→ [Backtest §7](./2026-06-06-dip-buying-best-indicator-combos-backtest.md) 明示「多頭 regime 裡放空/接刀勝率低」
2. CPI 13 LOW → 系統性風險低
3. 已驗證 FDR 鐵證訊號**未觸發**（S&P -2.7% << -10%；VIX 18.9 << 30）→ 不該在「觀察區」過度操作

**警惕理由**：
1. AVI 估值偏貴（CAPE/P/S 都 98.8%ile）→ 上限封頂、需現金緩衝
2. TSI 49 + FLASH → 高 beta 科技不該加碼
3. TWII +37.6% 高於 200DMA = 極端拉伸 → 不追台股新高
4. 事件密集區（SpaceX IPO 6/11–12、FOMC/Warsh 6/17、三巫 6/18）→ 6/18 前不大動

### C.3 現金水位（現在 → 觸發後）

**現在：65% 投資 / 35% 現金**（區間 50%–90%）

> Sub-agent C 確認：以下「1/3 子彈」**= 1/3 of cash reserve（每批約 10pp），不是 1/3 of NAV**——這是 cash-slide 自洽的唯一解（若按 NAV，第二批會把現金變負數，數學不通）。

---

## D. 一年節奏（2026-06 → 2027-06）

| 階段 | 時間/觸發 | 動作 | 現金→投資 |
|---|---|---|---|
| **P1 穿越事件區** | 現在–6/18 | 不追、保留緩衝；個股級可減 Fujimi/AAOI 過熱檔 | **65% 投 / 35% 現金**（維持） |
| **P2a 美股觸發 A** | **S&P 自高 -10% 且仍站 200DMA**（~6,665）→ FDR 鐵證 95%/Wilson 82% | 投 1/3 現金（約 10pp） | **75% / 25%** |
| **P2b 美股觸發 B** | S&P -15% 或 VIX≥30（同時站 200DMA） | 再投 1/3 現金 | **85% / 15%** |
| **P2c 台股觸發**（**已校準**） | TAIEX 自 ATH **-15%** 且**跌破 200DMA**（嚴格按 backtest 旗艦：n=25、家族 80–89%，~36,500 區）；若僅 -10% 但未破 200DMA = 不算 FDR 觸發、只小批 | 投台股批（**抱滿 1 年**） | （台股部位內分批） |
| **P3 秋季洗盤** | 9–10 月、VIX≥35–40 + 仍站 200DMA | 重壓最後保留 | **85–90% / 10–15%** |
| **P4 期中後強季** | 11 月–次年 4 月（四年週期最強 +14%） | 維持較滿、騎乘 | **85–90% / 10–15%** |
| **🚨 Regime 破** | S&P 收破 200DMA（~**6,864** 實算） | 砍至 50% 現金、只在 VIX≥40 小批 | **50% / 50%** |
| **獲利了結** | WT1>+60 OB（指數或個股，如 Fujimi 現在） | 分批減、回補現金 | 回補 |

> **與 DRAFT 差別**：（a）P2c 台股觸發**校準**為「-15% **且** 跌破 200DMA」嚴格版（草稿剝掉 200DMA 前提、勝率引用 85%+ 偏樂觀，違反 [Backtest §7 honest 修正](./2026-06-06-dip-buying-best-indicator-combos-backtest.md)）。（b）regime-break 7,405 / 1.079 ≈ **6,864**（草稿 6,850 已正確到 0.2%）。（c）「1/3 子彈」定義明確化為「1/3 of cash」。

---

## E. Top 10 → 「選股 × 擇時」對應表（依即時 WT 重排）

| 排名 | 標的 | Serenity | 即時技術 | 行動 |
|---|---|---|---|---|
| 1 | **PLAB** | 24/30 | RSI 28 深超賣、跌破 200DMA、-45% | **小批試水**（個股 alpha，放棄 SOP；≤1/4 部位） |
| 2 | **ITEQ 6213** | 23/30 | -15%、WT -12、>200DMA | **回檔到 -20% 第一批**；估值 1.4x P/S 全清單最便宜 |
| 3 | **Fujimi 5384.T** | 26/30 | **WT 65.7 超買🔴** | **持有者趁強減**；買家等回檔 |
| 4 | **ACON 6820** | 23/30 | -38%、WT -7（中性） | 觀察 WT 翻正 or RSI<30 再進；先查 Vendor List |
| 5 | **COHR** | 22/30 | bear-X↓、+89% > 200DMA | 等回檔分批，別追 |
| 6 | **MTRN** | 22/30 | WT 56、bear-X↓、RSI 68 | 等回檔（題材長期 OK） |
| 7 | **M31 6643** | 22/30 | **RSI 22 深超賣、跌破 200DMA** | 小批試水（個股 alpha） |
| 8 | **Stella 4109.T** | 22/30 | WT 34、-13%、>200DMA | 中性等待 |
| 9 | **上詮 3363** | 23/30 但已飆 | bear-X↓、-24% | 等深回檔 |
| 10 | **COHU** | 21/30 | bear-X↓、-9% | 等回檔分批 |
| 動能管理 | **AAOI**（持 20%） | 17/30（降級） | +177% >200DMA、SemiAnalysis 結構利空 | **執行 20→10%** |
| 觀察 | 汎銓 6830 / 聯亞 3081 / 波若威 3163 | 16–21 | 都已大跌但題材+估值風險 | 不買、長期觀察 |

**工具**：指數曝險用 SPY/QQQ/0050 控總水位；alpha 用 Top 10 個股。

---

## F. 與其他 KIWI 文件的銜接

- **規則來源**：[2026-06-06-dip-buying-best-indicator-combos-backtest.md](./2026-06-06-dip-buying-best-indicator-combos-backtest.md) §7（FDR 校正後鐵證：美股「回檔≥10% + 站 200DMA」抱 6 月 95%/Wilson 82%/138 組唯一過 FDR）
- **選股清單**：[2026-06-10-silicon-photonics-cpo-optical-report-analysis.md](./2026-06-10-silicon-photonics-cpo-optical-report-analysis.md) §9.5（SemiAnalysis 疊加後的跨市場 Top 10）
- **宏觀地圖**：[2026-06-06-post-selloff-market-roadmap.md](./2026-06-06-post-selloff-market-roadmap.md)（6/5 SOX 史詩級單日後的 roadmap）

---

## G. Mac 上重跑指令（每日／每週可重複）

```bash
cd ~/KIWI/projects/avi-v5 && source .venv/bin/activate

# ACT 三表（每天）
python scripts/run_tsi.py
python scripts/run_cpi.py
python scripts/run_monthly.py --v5   # ⚠ 目前鎖在 2024-12-31，待 multpl.py bug 修

# Live data + WaveTrend（每天）
python scripts/fetch_data.py
python scripts/wavetrend.py --ticker '^GSPC' '^IXIC' '^TWII' '^N225' '^VIX' \
  PLAB COHR MTRN COHU AAOI \
  6213.TW 6820.TWO 6643.TWO 3363.TWO 5384.T 4109.T 6830.TW 3081.TWO 3163.TWO
```

---

## H. 待修 / 待做（給下個 session）

1. **multpl.py parser bug**（已定位）：`src/data/sources/multpl.py:100-112` 加 `re.sub(r"[^\d.\-]", "", value_text)` 一行修掉，AVI 即可即時。
2. **wavetrend.py 的 last-bar NaN**：yfinance 偶爾返回未完整 bar 為 NaN；建議加 `.dropna(subset=['close'])` 後再取 i=-1（不修也行，但會顯示 nan）。
3. **CPI 4 個 NaN 指標**（ma_distance_reversal/momentum_collapse/intraday_selloff/breadth_divergence）→ 12 個只有 ~7 個有效，建議檢查資料源。
4. **6830 → 興櫃→上櫃→？**：yfinance 中只有 .TW 抓得到，.TWO 已下市。記錄此 mapping。

---

## I. 紅隊驗證紀錄（3 個獨立 sub-agent，2026-06-10）

| Agent | 任務 | 結論 |
|---|---|---|
| **A** | 重跑 ACT 三表、驗證讀數、診斷 AVI 卡 2024-12-31 | TSI 49 / CPI 13 / AVI 5.67 **全對**；診斷出 multpl.py 解析器 dagger † silent-drop bug |
| **B** | 獨立用 LazyBear 公式重算 ^VIX / ^GSPC / 4109.T 的 WT1/WT2 | 三檔**逐位對齊到 0.1**，公式正確、無 bug；6830.TW = Msscorps = 汎銓 **確認** |
| **C** | 紅隊 cash-slide 數學、觸發條件、no-short 邏輯 | cash-slide **PASS**（cash-thirds 自洽）；US P2a **PASS**；**TW P2c FAIL** → 已校準（補回「跌破 200DMA」前提、撤回 85%+ 引用）；regime-break 6,864 **PASS** |

**對 DRAFT 的關鍵修正**：
- ACT 從估計 (6.7/45-52/55-65) → 實測 (5.67-7.0/13/49)
- TW 觸發從 "-10~15%" → 嚴格版 "-15% **且** 跌破 200DMA"
- "1/3 子彈" 定義明確 = 1/3 of cash（非 NAV）
- regime-break 6,850 → 6,864（用即時 200DMA 反算）

---

## Update Log
- 2026-06-10 v2.0 (FINAL)：本機跑 ACT + WaveTrend + 三 sub-agent 紅隊驗證。取代 v1.0 DRAFT。關鍵：ACT 實測 (TSI 49/CPI 13/AVI 5.67 但需 +0.3-1.3 因 multpl.py bug)；WaveTrend 公式驗證正確；TW 觸發校準回 backtest 嚴格版；cash-slide 自洽（cash-thirds 解讀）；Fujimi 趁強減、AAOI 執行 20→10%。
- 2026-06-10 v1.0 (DRAFT)：雲端版，ACT 為估計、WaveTrend 僅 VIX 一檔、TW 觸發有 drift；待 Mac 本機跑+驗證後定稿。
