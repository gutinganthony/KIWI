# vibe-lab — Vibe-Trading 因子實驗室（KIWI 側）

用 [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading)（港大 Data Science Lab
開源交易研究 agent，MIT，`pip install vibe-trading-ai`）的 **Alpha Zoo** 跑因子
benchmark 的作業區。Zoo 內建 460 支註冊因子，其中 `alpha101` zoo =
Kakushadze (2015)《101 Formulaic Alphas》（arXiv:1601.00991）逐條實作。

## 這裡有什麼

```
run_bench_sp500.py        # S&P 500 bench 的 wrapper（見下方「為什麼不直接用 CLI」）
data/constituents.csv     # S&P 500 成分股快照（github.com/datasets/s-and-p-500-companies）
runs/<日期>_<zoo>_<universe>/   # 每輪 bench 的結果（JSON + REPORT.md + HTML）
```

## 為什麼不直接用官方 CLI

官方入口是 `vibe-trading alpha bench --zoo alpha101 --universe sp500 --period 2020-2025`，
但它的 S&P 500 成分股清單抓 en.wikipedia.org——**雲端容器的 proxy 擋 Wikipedia**，
工具會靜默降級成內建 50 檔清單（log 標 `degraded run`），bench 就只剩 50 檔大型股。
`run_bench_sp500.py` 把本地 `data/constituents.csv`（503 檔）餵進去，並額外注入
GICS sector 標籤（讓 20 支 `requires_sector` 的行業中性化因子可測，官方路徑下會被
SkipAlpha 跳過），其餘流程照走官方 `cmd_alpha_bench`。

## 重跑一輪

```bash
pip install --user vibe-trading-ai            # 本環境 pip 一律 --user（見 agents/LEARNINGS.md）
python3 projects/vibe-lab/run_bench_sp500.py \
    --period 2020-01-01/2026-07-10 --top 101 --fresh
# 結果 JSON 印到 stdout；HTML 報告寫到 ~/.vibe-trading/reports/
# 成分清單更新：curl -sSo projects/vibe-lab/data/constituents.csv \
#   https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv
# 改過清單後第一次跑必帶 --fresh（panel 有 universe+period 的 pickle 快取）
```

## Bench 方法論（讀數怎麼算的，vibe-trading v0.1.11 實測）

- **IC**：每日橫截面 Spearman rank correlation（因子值 vs **次日** close-to-close
  簡單報酬），有效樣本 <5 檔的交易日剔除。
- **IR**：`ic_mean / ic_std`，**日頻、未年化**（年化 ≈ ×√252）。
- **vwap**：美股面板無真 vwap，用 `(O+H+L+C)/4` 合成。
- **行業中性化**（indneutralize 類因子）：per-row sector group demean 近似，
  sector 用「今日 GICS sector」套整段歷史。
- **category**：工具對每支因子的存活判定標籤（alive/decayed/dead）。

## 已知限制（判讀前必讀）

1. **Survivorship bias**：universe 是「今日」成分股，期間內被剔除/下市的成分不在樣本
   → IC 系統性偏高，真實可交易表現只會更差。官方 wiki 同樣警告；point-in-time
   membership 是上游 planned 功能。
2. 1 日 horizon、無交易成本、無做空成本——這是「訊號含量」bench，不是策略回測。
3. sector 標籤是今日快照，期間內換版塊的公司會被標錯。
4. 免費數據路由（yahoo loader），未經第二來源複核；QVeris premium 路由未啟用。

## 環境備忘

- 安裝若撞 `jsonpath` wheel build 失敗（Debian setuptools 的 `install_layout` bug）：
  先 `pip install --user --upgrade setuptools wheel` 再裝。
- 首輪 503 檔 cold fetch 約幾分鐘；之後同 universe+period 命中
  `~/.vibe-trading/cache/sp500_<start>_<end>.pkl` 秒回。
