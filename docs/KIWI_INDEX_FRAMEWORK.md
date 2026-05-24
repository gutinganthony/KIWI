# KIWI 三指標框架說明

**AVI · CRI · TSI — 設計邏輯、計算框架與使用方式**

> 適合對象：新 session、協作者、或想了解這套系統如何運作的人。

---

## 目錄

1. [整體架構](#整體架構)
2. [AVI V5 — 長週期估值壓力](#avi-v5--長週期估值壓力)
3. [CRI — 短週期崩盤風險](#cri--短週期崩盤風險)
4. [TSI — 科技板塊壓力](#tsi--科技板塊壓力)
5. [三指標聯合判讀](#三指標聯合判讀)
6. [觸發條件與行動準則](#觸發條件與行動準則)
7. [技術架構](#技術架構)

---

## 整體架構

KIWI 用三個指標從不同時間維度和板塊角度衡量市場風險，互補而不重疊：

| 指標 | 全名 | 時間週期 | 分數範圍 | 更新頻率 | 核心問題 |
|------|------|----------|----------|----------|----------|
| **AVI** | Adjusted Valuation Index | 月度 / 長週期 | 0–10 | 每日（月度精度） | 市場現在貴不貴？ |
| **CRI** | Crash Risk Index | 日度 / 短週期 | 0–100 | 每日 | 未來 23–42 天崩盤機率高嗎？ |
| **TSI** | Tech Stress Index | 日度 / 短週期 | 0–100 | 每日 | 科技板塊現在有壓力嗎？ |

三個指標同時偏高才是最高風險訊號；單一指標偏高提供板塊或週期性警示。

---

## AVI V5 — 長週期估值壓力

### 設計理念

AVI 回答的問題是：**市場現在的估值水位，在歷史上處於哪個百分位？**
分數越高，代表市場越貴、長期下行風險越大，但不預測短期時間點。

### 六個維度與權重

```
Valuation     38%  ── CAPE (Shiller P/E) 絕對水位
Rate          14%  ── 通膨 YoY、10Y 實質殖利率
Macro         14%  ── VIX 滾動百分位
Momentum      14%  ── SPY vs 200MA 距離
Credit        12%  ── BAA-10Y 利差百分位
Profitability  8%  ── 企業盈利穩定性（相對靜態）
```

### 計算方式

每個維度產出 0–100 的百分位數，再用權重加總換算為 0–10 分：

```
AVI = Σ (dimension_percentile / 100 × weight × 10)
```

| 分數 | 等級 | 含義 |
|------|------|------|
| 0–4.0 | LOW | 估值合理，長期風險低 |
| 4.0–5.5 | NEUTRAL | 中性，正常持倉 |
| 5.5–7.0 | ELEVATED | 估值偏高，謹慎 |
| 7.0–8.0 | HIGH | 明顯高估，降低曝險 |
| 8.0+ | CRITICAL | 極端高估，最高警戒 |

### 各維度資料來源

- **Valuation**：Shiller CAPE（每月更新，來自 multpl.com 爬蟲）
- **Rate**：FRED `CPIAUCSL`（通膨 YoY）+ FRED `DGS10`（10Y 殖利率）
- **Macro**：yfinance `^VIX`（252 日滾動百分位）
- **Credit**：FRED `BAA` - FRED `DGS10`（信用利差）
- **Momentum**：yfinance `SPY`（現價 vs 200MA 比率）
- **Profitability**：目前固定為 34（穩定指標，暫不動態計算）

---

## CRI — 短週期崩盤風險

### 設計理念

CRI（Crash Risk Index）回答的問題是：**未來 23–42 天內，市場出現 20%+ 崩盤的機率有多高？**

歷史回測：4 次主要崩盤（2000、2008、2020、2022）全部提前偵測，
領先時間 23–42 個交易日，沒有漏報。

### 12 個指標與權重

```
vix_term_structure   12%  ── VIX 期限結構（spot vs 3M）反轉 = 壓力
vix_spike             9%  ── VIX 絕對水位 + 5 日上升速度
garch_vix_gap         8%  ── GARCH 預測波動率 vs VIX 隱含波動率差距
credit_acceleration  10%  ── BAA-AAA 利差 10 日加速擴大
breadth_divergence    8%  ── 指數新高但市場廣度下降
distribution_days     8%  ── 25 日內放量下跌天數（主力出貨訊號）
rsi_divergence        7%  ── 價格創高但 RSI 下降（背離）
ma_distance_reversal  7%  ── 嚴重超漲後開始反轉
yield_curve_steepen   6%  ── 殖利率曲線在倒掛後快速陡化（衰退訊號）
momentum_collapse     9%  ── 5 日急跌（最直接的短期崩盤前兆）
yield_surge           8%  ── 10Y 殖利率 5 日快速跳升（折現率衝擊）
intraday_selloff      8%  ── 同日股票跌 + VIX 漲（即時確認壓力）
```

### 計算方式

```
CRI_base = Σ (indicator_signal × weight)

# 增幅機制（依序疊加）：
若 AVI > 6 且 CRI > 40  → × 1.2
若 ≥5 個指標 signal ≥40  → × 1.3
若 ≥3 個指標 signal ≥40  → × 1.15
若 momentum_collapse > 50 → × 1.3
若 vix_spike > 60 且 momentum_collapse > 30 → × 1.25
```

增幅機制的設計邏輯：崩盤前夕通常有「多指標同時亮燈」的現象，
單純加權容易低估，所以當多指標共振時主動放大信號。

| 分數 | 等級 | 含義 |
|------|------|------|
| 0–20 | LOW | 正常，崩盤機率低 |
| 20–35 | MODERATE | 留意，部分壓力指標升溫 |
| 35–50 | ELEVATED | 偏高，準備避險計畫 |
| 50–70 | HIGH | 高風險，積極減倉 |
| 70+ | CRITICAL | 極端，立即行動 |

### Flash Alert 觸發條件

當 **2 個以上**指標同時超過門檻，發出 Flash Alert：
- VIX backwardation（spot > 3M 1.05 倍以上）
- GARCH vol >> VIX（隱藏壓力）
- 信用利差 10 日擴大 >20bps
- 市場廣度惡化（指數高點但廣度下降）
- 25 日內 ≥5 個 distribution days
- 殖利率 5 日飆升 >12bps
- 股票跌 >0.8% 同日 VIX 漲 >8%

---

## TSI — 科技板塊壓力

### 設計理念

TSI（Tech Stress Index）聚焦半導體 + 科技板塊，捕捉主力指數（SPY）
還未反映、但科技板塊已在惡化的早期訊號。

歷史回測：7/7 科技重大回調事件偵測成功（含 2000 年網路泡沫、
2022 年科技熊市、2024 年 AI 泡沫修正）。

### 9 個指標與權重

```
vix_tech_correlation    18%  ── VIX 上漲同時科技跌 = 真正的壓力
sox_qqq_divergence      14%  ── 半導體（SOX）落後大盤科技（QQQ）
memory_momentum         12%  ── 記憶體股（MU）動能崩潰（需求先行指標）
yield_shock             12%  ── 10Y 殖利率 5 日快速上升（科技估值殺手）
ai_infra_rs             10%  ── SMH（AI 基礎設施）vs SPY 相對強度
tech_breadth            10%  ── QQQ 內部動能（vs 20/50MA）
cloud_rs                 8%  ── QQQ vs SPY 相對強度（科技 vs 大盤）
yield_30y_stress         8%  ── 30Y 殖利率絕對水位（DCF 折現率直接衝擊）
yield_curve_bear_steep   8%  ── 30Y-10Y 利差擴大 + 兩端同步上升（最毒場景）
```

### 計算方式

```
TSI_base = Σ (indicator_signal × weight)

# 共振增幅：
若 ≥5 個指標 signal ≥50  → × 1.25
若 ≥3 個指標 signal ≥50  → × 1.10

# 單一強信號保底：
若 ≥2 個指標 signal ≥50  → TSI ≥ avg(high_signals) × 0.65
若最高單一信號 ≥70       → TSI ≥ max_signal × 0.5

# 廣泛壓力保底：
若 ≥4 個指標 signal ≥25  → TSI ≥ 45（強制進入 CAUTIOUS）
```

| 分數 | 等級 | 含義 |
|------|------|------|
| 0–22 | BULLISH | 科技板塊健康，可持有 |
| 22–40 | NEUTRAL | 中性，標準風控 |
| 40–60 | CAUTIOUS | 謹慎，不追高，留意觸發 |
| 60+ | BEARISH | 高壓，減少科技曝險 |

### 特別指標說明：30Y 殖利率壓力

2026 年 5 月設計加入，原因是 30Y 殖利率突破 5%（2007 年以來最高），
對科技股 DCF 估值的衝擊比 10Y 更大。

計算邏輯：
```
level_signal = clip((30Y_yield - 4.0) / 1.5 × 50, 0, 50)
speed_signal = clip(5日變化(bps) / 15 × 50, 0, 50)
signal = level_signal + speed_signal
# 30Y > 5%：額外加 30 分懲罰
```

### Flash Alert 觸發條件（需 2 個以上同時）

- SOX 落後 QQQ >4%（10 日）
- 記憶體股急跌
- 10Y 殖利率 5 日上升 >15bps
- 30Y 殖利率超過極端水位（>5%）
- VIX 飆升 + 科技跌

---

## 三指標聯合判讀

### 信號矩陣

| AVI | CRI | TSI | 解讀 | 建議行動 |
|-----|-----|-----|------|----------|
| 低 | 低 | 低 | 🟢 全線正常 | 照常操作 |
| 高 | 低 | 低 | 🟡 長期偏貴但短期無壓力 | 不加碼，等待機會 |
| 低 | 高 | 低 | 🟠 短期崩盤風險升高 | 建立避險，檢查持倉 |
| 低 | 低 | 高 | 🟠 科技板塊承壓 | 減科技部位，轉防禦 |
| 高 | 高 | 低 | 🔴 高估值 + 崩盤風險 | 積極減倉 |
| 低 | 高 | 高 | 🔴 短期雙重壓力 | 立即建立避險 |
| 高 | 高 | 高 | 🔴🔴 全線警戒 | 最高優先：大幅降低曝險 |

### 各指標的領先時間

```
AVI ── 月度估值壓力，不預測時間點，提供背景脈絡
CRI ── 領先崩盤 23–42 個交易日（約 1–2 個月）
TSI ── 領先科技修正 3–14 個交易日（約 1–3 週）
```

CRI 領先時間較長，適合提前部署（空倉、買 Put、轉移資產配置）；
TSI 反應較快，適合做短期倉位調整。

---

## 觸發條件與行動準則

### 硬性觸發條件（需立即行動）

```
TSI > 55         → 減少科技部位曝險
CRI > 35         → 建立避險或減倉
CRI > 35 且 TSI > 55 → 雙高，立即行動
```

### 軟性觸發條件（留意觀察）

```
TSI 40–55        → 不追高科技，留意是否繼續惡化
CRI 20–35        → 掃描是哪個指標在升溫
AVI > 7          → 不宜大幅加碼，保持安全邊際
AVI > 6 且 CRI > 40 → CRI 自動 × 1.2，注意共振效應
```

### Flash Alert 含義

Flash Alert 是各指標的「多重引爆」訊號，代表短時間內多個前兆同時出現。
CRI Flash Alert 通常比 CRI 分數本身更早、更準地指向即將到來的壓力。
收到 Flash Alert 應立即檢視觸發原因，不能只看總分。

---

## 技術架構

### 資料流

```
每日 08:00 TST（GitHub Actions）
  ├── 抓取 yfinance 資料（^GSPC, ^VIX, QQQ, SOXX, SMH, SPY, MU, BZ=F）
  ├── 抓取 FRED 資料（DGS10, DGS30, BAA, CPIAUCSL）
  ├── 爬取 CAPE（multpl.com）
  ├── 計算 CRI、TSI、AVI 三個指標
  ├── 寫入 docs/index.html（KIWI_DATA JSON）
  └── git commit + push → GitHub Pages 自動部署

每日 08:30 TST（GitHub Actions）
  ├── 讀取 docs/index.html 的 KIWI_DATA JSON
  ├── 建構 Telegram HTML 訊息
  ├── 建構 LINE 純文字訊息
  └── 同時發送兩個平台
```

### 核心程式碼位置

```
projects/avi-v5/
├── src/
│   ├── cpi/__init__.py          ← CRI 計算引擎（CrashProbabilityIndex class）
│   ├── cpi/data.py              ← CRI 資料收集（CPIDataCollector）
│   ├── tsi/__init__.py          ← TSI 計算引擎（TechStressIndex class）
│   ├── tsi/data.py              ← TSI 資料收集（TSIDataCollector）
│   └── pipeline/avi_v5_pipeline.py  ← AVI V5 完整管線
├── scripts/
│   ├── update_dashboard.py      ← 每日資料更新主程式
│   └── notify.py                ← Telegram + LINE 推播
docs/
└── index.html                   ← Dashboard 前端（含 KIWI_DATA JSON）

.github/workflows/
├── update-dashboard.yml         ← 08:00 TST 每日更新
├── daily-alert.yml              ← 08:30 TST 每日推播
└── deploy-pages.yml             ← push to main 自動部署 GitHub Pages
```

### KIWI_DATA JSON 格式

```json
{
  "updated": "YYYY-MM-DD",
  "avi": {
    "score": 5.9,
    "level": "ELEVATED",
    "dimensions": {
      "valuation":     { "pct": 89, "emoji": "🔴" },
      "profitability": { "pct": 34, "emoji": "🟢" },
      "macro":         { "pct": 52, "emoji": "🟡" },
      "rate":          { "pct": 65, "emoji": "🟠" },
      "credit":        { "pct": 5,  "emoji": "🟢" },
      "momentum":      { "pct": 40, "emoji": "🟡" }
    }
  },
  "cri": {
    "score": 21.0,
    "level": "MODERATE",
    "flash": false,
    "indicators": { ... }
  },
  "tsi": {
    "score": 45.0,
    "bias": "CAUTIOUS",
    "flash": false,
    "indicators": { ... }
  },
  "market": {
    "sp500": 7432.97,
    "vix": 17.44,
    "t10y": 4.67,
    "t30y": 5.18,
    "cape": 41.78,
    "oil": 105.02
  },
  "alert": { ... }
}
```

### GitHub Secrets 需求

| Secret | 用途 |
|--------|------|
| `FRED_API_KEY` | 抓取 FRED 數據（殖利率、通膨、信用利差）|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot 發訊 |
| `TELEGRAM_CHAT_ID` | 你的 Telegram user ID |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Official Account 廣播 |

---

*最後更新：2026-05-24*
*此文件由 KIWI session 自動生成，反映當前程式碼的實際設計。*
