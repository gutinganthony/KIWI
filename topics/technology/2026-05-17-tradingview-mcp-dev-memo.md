---
title: TradingView MCP 開發備忘 — Phase 5 完成版
url: local
source: AVI V5 ARCHITECTURE.md + session progress
date_added: 2026-05-17
last_updated: 2026-05-19
topic: technology
tags: [tradingview, mcp, pine-script, automation, avi-v5, phase-5, dev-memo]
version: 2.0
---

## 開新 Session 時的指令

> 「繼續 KIWI AVI V5，做 TradingView MCP（Phase 5）。參考 `topics/technology/2026-05-17-tradingview-mcp-dev-memo.md`」

---

## 一、所有已完成的部分

| 項目 | 狀態 | 檔案位置 |
|------|------|---------|
| HTML Dashboard | ✅ | `projects/avi-v5/dashboard/template.html` + `cpi_dashboard.py` |
| CPI 使用手冊 HTML | ✅ | `projects/avi-v5/dashboard/guide.html` |
| CPI Pine Script 模板 | ✅ | `projects/avi-v5/pine/cpi_indicator.pine` |
| **TSI Pine Script 模板** | ✅ **Phase 5 新** | `projects/avi-v5/pine/tsi_indicator.pine` |
| **AVI 三合一 Composite** | ✅ **Phase 5 新** | `projects/avi-v5/pine/avi_composite.pine` |
| **Pine 生成共用模組** | ✅ **Phase 5 新** | `projects/avi-v5/src/pine_export.py` |
| Dashboard CLI（升級版） | ✅ **Phase 5 升級** | `scripts/run_dashboard.py --pine` 現在生成 3 個 Pine 檔 |
| CPI 引擎 (12 指標) | ✅ | `src/cpi/__init__.py` |
| TSI 引擎 (9 指標) | ✅ | `src/tsi/__init__.py` |
| AVI V5 Pipeline | ✅ | `src/pipeline/avi_v5_pipeline.py` |
| **TradingView MCP Server** | ✅ **Phase 5 新** | `mcp_tradingview/server.py` |
| **Playwright Bridge** | ✅ **Phase 5 新** | `mcp_tradingview/tradingview_bridge.py` |
| **MCP 工具：圖表操作** | ✅ **Phase 5 新** | `mcp_tradingview/tools/chart_tools.py` |
| **MCP 工具：Pine 上傳** | ✅ **Phase 5 新** | `mcp_tradingview/tools/pine_tools.py` |
| **MCP 工具：市場資料** | ✅ **Phase 5 新** | `mcp_tradingview/tools/data_tools.py` |
| **MCP 工具：回測** | ✅ **Phase 5 新** | `mcp_tradingview/tools/backtest_tools.py` |

---

## 二、「推送到 TradingView」教學（小學生版）

### 方法 A：手動貼上（簡單，5 分鐘）

不需要 MCP，不需要 session cookie，**推薦先用這個**。

```
第 1 步：在你的電腦上執行
  cd ~/KIWI/projects/avi-v5
  python3 scripts/run_dashboard.py --pine

  → 執行完成後會顯示 3 個 Pine 檔的路徑，例如：
      [CPI]       /Users/你/KIWI/projects/avi-v5/pine/cpi_indicator_current.pine
      [TSI]       /Users/你/KIWI/projects/avi-v5/pine/tsi_indicator_current.pine
      [Composite] /Users/你/KIWI/projects/avi-v5/pine/avi_composite_current.pine

第 2 步：打開 TradingView（瀏覽器）
  → 進入任何一個圖表，例如 SPY 日線圖

第 3 步：打開 Pine 編輯器
  → 點下方「Pine Editor」分頁（或按 Alt+P）

第 4 步：貼上程式碼
  → 用文字編輯器打開上面的 .pine 檔（記事本也行）
  → 全選（Ctrl+A）→ 複製（Ctrl+C）
  → 回到 TradingView Pine 編輯器，全選後貼上

第 5 步：加到圖表
  → 點右上角「Add to chart」按鈕
  → 指標就出現在圖表下方了！

重複第 2-5 步，把 3 個 Pine 檔都加上去
（CPI 崩盤概率、TSI 科技壓力、Composite 三合一）
```

---

### 方法 B：MCP 自動化（進階，一次設定後每次一句話搞定）

設定一次後，以後只要跟 Claude 說「更新 TradingView 指標」，Claude 就會自動幫你做完所有事。

#### B-1：安裝 Playwright

```bash
cd ~/KIWI/projects/avi-v5
pip3 install mcp playwright
playwright install chromium
```

#### B-2：取得 TradingView Session Cookie

```
1. 用 Chrome 打開 tradingview.com 並登入
2. 按 F12 打開開發者工具
3. 點上方「Application」分頁
4. 左側找到「Cookies」→「https://www.tradingview.com」
5. 找到名為「sessionid」的那行
6. 複製它的「Value」欄位（一長串英文數字）
```

#### B-3：設定 Claude Code

打開（或新建）`~/.claude/settings.json`，加入：

```json
{
  "mcpServers": {
    "tradingview": {
      "command": "python",
      "args": ["mcp_tradingview/server.py"],
      "cwd": "/Users/你的名字/KIWI/projects/avi-v5",
      "env": {
        "TV_SESSION_COOKIE": "貼上剛才複製的 sessionid",
        "TV_HEADLESS": "1",
        "FRED_API_KEY": "8181079f96c8210790797e299aca965a"
      }
    }
  }
}
```

> ⚠️ 把 `cwd` 路徑改成你電腦上實際的路徑

#### B-4：使用方式

重新啟動 Claude Code，然後直接說：

```
「幫我更新 TradingView 的 AVI 指標」
```

Claude 就會自動：
1. 抓最新市場數據
2. 計算 CPI / TSI / AVI 分數
3. 把 3 個指標更新並推送到你的 TradingView 圖表

---

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

# === Pine Script（三合一）===
python3 scripts/run_dashboard.py --pine    # 生成 CPI + TSI + Composite 三個 Pine 檔

# === TSI ===
python3 scripts/run_tsi.py                 # 當日 TSI 分數
python3 scripts/run_tsi.py --history 30    # 30 天趨勢
python3 scripts/run_tsi.py --history 252   # 一年趨勢

# === AVI 回測 ===
python3 scripts/run_backtest.py            # V4 vs V4.1 vs V4.2 比較
```

---

## 四、環境設定（換電腦時）

```bash
# 1. Clone repo
git clone https://github.com/gutinganthony/KIWI.git
cd KIWI
git checkout claude/tradingview-mcp-phase-5-wOPl8

# 2. 安裝套件
cd projects/avi-v5
pip3 install -r requirements.txt
playwright install chromium   # Phase 5 MCP 需要

# 3. 設定 API Key
echo "FRED_API_KEY=8181079f96c8210790797e299aca965a" > .env

# 4. 測試（不需要 MCP）
python3 scripts/run_tsi.py
python3 scripts/run_dashboard.py --pine
```

---

## 五、3 個 Pine Script 各自的用途

| 檔案 | 指標 | 顯示什麼 | 何時使用 |
|------|------|---------|---------|
| `cpi_indicator_current.pine` | CPI 12 指標 | 大盤崩盤概率（0-100） | 看整體市場風險 |
| `tsi_indicator_current.pine` | TSI 9 指標 | 科技股壓力（0-100） | 看 QQQ/科技股 |
| `avi_composite_current.pine` | CPI+TSI+AVI | 三線同一圖，右上角摘要表 | **日常主要用這個** |

> 💡 **建議**：平常只加 `avi_composite_current.pine` 就夠了，三個指標都看得到。

---

## 六、當前系統能力總結

| 系統 | 指標數 | 頻率 | 偵測率 | 用途 |
|------|--------|------|--------|------|
| **AVI V5** | 14 | 月度 | 2/5 (資料源待修) | 市場估值環境 |
| **CPI** | 12 | 日頻 | 4/4 大崩盤 | 大盤崩盤概率 |
| **TSI** | 9 | 日頻 | 7/7 事件 | 科技股壓力 |

---

## Update Log

- 2026-05-17 v1.0: Phase 5 開發備忘，含方案 A/B、指令備忘、環境設定、檔案結構
- 2026-05-19 v2.0: Phase 5 **完成**。新增 TSI Pine、Composite Pine、MCP Server（8 個工具）、小學生版 TradingView 推送教學
