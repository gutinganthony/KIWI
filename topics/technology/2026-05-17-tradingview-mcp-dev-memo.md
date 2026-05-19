---
title: TradingView MCP 開發備忘 — Phase 5 接續指南
url: local
source: AVI V5 ARCHITECTURE.md + session progress
date_added: 2026-05-17
last_updated: 2026-05-17
topic: technology
tags: [tradingview, mcp, pine-script, automation, avi-v5, phase-5, dev-memo]
version: 1.0
---

## 開新 Session 時的指令

> 「繼續 KIWI AVI V5，做 TradingView MCP（Phase 5）。參考 `topics/technology/2026-05-17-tradingview-mcp-dev-memo.md`」

---

## 一、已完成的部分

| 項目 | 狀態 | 檔案位置 |
|------|------|---------|
| HTML Dashboard | ✅ | `projects/avi-v5/dashboard/template.html` + `cpi_dashboard.py` |
| CPI 使用手冊 HTML | ✅ | `projects/avi-v5/dashboard/guide.html` |
| Pine Script 模板 | ✅ | `projects/avi-v5/pine/cpi_indicator.pine` |
| Dashboard CLI | ✅ | `scripts/run_dashboard.py` (支援 `--guide`, `--pine`) |
| CPI 引擎 (12 指標) | ✅ | `src/cpi/__init__.py` |
| TSI 引擎 (9 指標) | ✅ | `src/tsi/__init__.py` |
| AVI V5 Pipeline | ✅ | `src/pipeline/avi_v5_pipeline.py` |

## 二、Phase 5 尚未做的

### 方案 A：輕量版（建議先做）

**自動生成 Pine Script + 每日更新**

不需要 Playwright，只需要：
1. `run_dashboard.py --pine` 已經能生成 `pine/cpi_indicator_current.pine`
2. 需要擴展：同時生成 TSI Pine Script
3. 需要新增：一鍵複製到剪貼簿的功能
4. 需要新增：Pine Script 中同時顯示 CPI + TSI + AVI 三個分數

**Pine Script 模板已存在：** `projects/avi-v5/pine/cpi_indicator.pine`

模板使用 `{{placeholder}}` 語法，Python 腳本替換後輸出到 `pine/cpi_indicator_current.pine`。

### 方案 B：完整 MCP（進階）

**Playwright 瀏覽器自動化**

架構設計在 `projects/avi-v5/ARCHITECTURE.md` 的 Part A，包含：

```
mcp-tradingview/
├── server.py                   # MCP protocol handler (stdio)
├── tradingview_bridge.py       # Playwright automation
└── tools/
    ├── chart_tools.py          # switch_symbol, draw_level
    ├── pine_tools.py           # create/modify Pine Script
    ├── data_tools.py           # get_ohlcv, market_state
    └── backtest_tools.py       # run_backtest
```

**MCP 設定（settings.json）：**
```json
{
  "mcpServers": {
    "tradingview": {
      "command": "python",
      "args": ["-m", "projects.avi-v5.mcp-tradingview.server"],
      "env": {
        "TV_SESSION_COOKIE": "${TV_SESSION_COOKIE}"
      }
    }
  }
}
```

**MCP Tools 規格：**

| Tool | 參數 | 功能 |
|------|------|------|
| `tv_switch_symbol` | symbol, timeframe | 切換標的 |
| `tv_draw_level` | price, label, color | 畫水平線 |
| `tv_get_ohlcv` | symbol, timeframe, bars | 讀 K 線 |
| `tv_get_market_state` | symbol | 即時價格 |
| `tv_create_pine_indicator` | name, source_code | 上傳 Pine |
| `tv_run_backtest` | strategy_code, symbol | 執行回測 |
| `tv_screenshot` | filepath | 截圖 |

**技術需求：**
- Playwright（`pip install playwright && playwright install chromium`）
- TradingView Pro 帳號（用戶已有）
- Session Cookie 認證（比帳密登入穩定）

## 三、所有系統的指令備忘

```bash
# 切換到專案
cd ~/KIWI/projects/avi-v5

# === AVI V5 ===
python3 scripts/run_monthly.py --v5        # 當月 AVI V5 分數

# === CPI ===
python3 scripts/run_cpi.py                 # 當日 CPI 分數（終端機）
python3 scripts/run_cpi.py --backtest      # CPI 回測（11 事件）
python3 scripts/run_dashboard.py           # CPI 視覺面板（瀏覽器）
python3 scripts/run_dashboard.py --guide   # CPI 使用手冊（瀏覽器）
python3 scripts/run_dashboard.py --pine    # 同時生成 Pine Script

# === TSI ===
python3 scripts/run_tsi.py                 # 當日 TSI 分數
python3 scripts/run_tsi.py --history 30    # 30 天趨勢
python3 scripts/run_tsi.py --history 252   # 一年趨勢

# === AVI 回測 ===
python3 scripts/run_backtest.py            # V4 vs V4.1 vs V4.2 比較
```

## 四、環境設定（換電腦時）

```bash
# 1. Clone repo
git clone https://github.com/gutinganthony/KIWI.git
cd KIWI
git checkout claude/add-kiwi-integration-VwVzs

# 2. 安裝套件
cd projects/avi-v5
pip3 install -r requirements.txt

# 3. 設定 API Key
echo "FRED_API_KEY=8181079f96c8210790797e299aca965a" > .env

# 4. 測試
python3 scripts/run_tsi.py
python3 scripts/run_dashboard.py
```

## 五、檔案結構速查

```
projects/avi-v5/
├── ARCHITECTURE.md              # 完整架構設計
├── CPI_ARCHITECTURE.md          # CPI 技術文件
├── .env                         # FRED API Key（不上傳 git）
├── config/
│   ├── indicators.yaml          # 14 個 AVI 指標定義
│   ├── avi_weights.yaml         # 6 維度權重
│   └── regime_params.yaml       # Regime + GARCH 參數
├── src/
│   ├── data/sources/            # FRED, multpl, yfinance 資料源
│   ├── engine/                  # AVI V4 核心 + percentile
│   ├── regime/                  # 4-state HMM
│   ├── garch/                   # GARCH(1,1) + VIX comparison
│   ├── pipeline/                # V5 整合 pipeline
│   ├── cpi/                     # CPI 崩盤概率（12 指標）
│   └── tsi/                     # TSI 科技壓力（9 指標）
├── backtest/                    # AVI 回測框架
├── dashboard/                   # HTML Dashboard + Guide
│   ├── template.html            # Dashboard 模板
│   ├── guide.html               # 使用手冊
│   └── cpi_dashboard.py         # 生成器
├── pine/                        # TradingView Pine Script
│   └── cpi_indicator.pine       # Pine 模板
├── scripts/
│   ├── run_monthly.py           # AVI V5
│   ├── run_cpi.py               # CPI
│   ├── run_tsi.py               # TSI
│   ├── run_dashboard.py         # 視覺面板
│   └── run_backtest.py          # AVI 回測
└── tests/
    └── test_cpi_validation.py   # CPI 嵌入式驗證
```

## 六、當前系統能力總結

| 系統 | 指標數 | 頻率 | 偵測率 | 用途 |
|------|--------|------|--------|------|
| **AVI V5** | 14 | 月度 | 2/5 (資料源待修) | 市場估值環境 |
| **CPI** | 12 | 日頻 | 4/4 大崩盤 | 大盤崩盤概率 |
| **TSI** | 9 | 日頻 | 7/7 事件 | 科技股壓力 |

---

## Update Log

- 2026-05-17 v1.0: Phase 5 開發備忘，含方案 A/B、指令備忘、環境設定、檔案結構。
