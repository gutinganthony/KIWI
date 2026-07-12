# alpha101 × S&P 500 Bench 報告（2026-07-12）

> 工具：HKUDS/Vibe-Trading（`vibe-trading-ai` 0.1.11）Alpha Zoo `alpha101`
> ＝ Kakushadze (2015)《101 Formulaic Alphas》逐條實作。
> 執行：`projects/vibe-lab/run_bench_sp500.py`（503 檔真成分股＋GICS sector 注入版）。

## TL;DR

**101 支公開因子在 2020–2026 的 S&P 500 上無一存活**（工具判定 100/100 dead，
門檻 IC>2%＋IC+≥55%＋|t|>2）——但這不等於零訊號：64 支日 |IR|>0.03，
頭部因子統計上顯著（top1 t≈4.7），只是效應量太小（IC ≈1%），
扣掉成本後在日頻上大概率不可交易。主題排序 momentum > reversal > volatility > volume。
放量日短期反轉因子 `alpha101_007` 在三個 universe/窗口組合中全部居前，是本輪最穩健的一支。
**意外發現：近兩年（2024–25）整體 IC 反而高於全期**，公開因子在美股大型股上
並未繼續單調衰減。

## 設定

| 項 | 值 |
|---|---|
| Universe | S&P 500「今日」成分股 503 檔（github datasets 快照 2026-07-12）→ **survivorship-biased** |
| 窗口 | 全期 2020-01-01→2026-07-10（~1,630 交易日）；近期 2024-01-01→2025-12-31（~500 日） |
| IC | 每日橫截面 Spearman rank corr（因子值 vs 次日 close-to-close 報酬），<5 檔有效日剔除 |
| IR | ic_mean/ic_std，日頻未年化（年化≈×√252） |
| 數據 | Yahoo（vibe-trading yahoo_loader 免費路由）；vwap=(O+H+L+C)/4 合成 |
| 行業中性化 | 19 支 IndClass 因子用今日 GICS sector 的 per-row group demean 近似 |
| 覆蓋 | 100/101 測得；唯一 skip：`alpha101_097`（輸出 97% NaN，工具 sanity guard 拒收） |

## 全期窗（2020–2026.07）

- IC mean 中位 **+0.37%**，範圍 [−1.12%, +1.56%]；日 IR 中位 +0.039；全部 dead。
- Top 5 by 日 IR：

| # | Alpha | 主題 | IC | 日 IR | IC+ | 公式要旨 |
|---|---|---|---|---|---|---|
| 1 | 007 | mom/vol | +1.11% | +0.120 | 0.545 | 放量日（volume>adv20）做 7 日價變的反轉 ts_rank |
| 2 | 021 | mom/vlty | +1.18% | +0.102 | 0.530 | 均線帶狀切換的 piecewise 訊號 |
| 3 | 043 | vol/mom | +1.30% | +0.100 | 0.530 | ts_rank(volume/adv20)×ts_rank(−Δclose) |
| 4 | 054 | reversal | +1.32% | +0.091 | 0.549 | (low−close)×open⁵ 比值反轉 |
| 5 | 024 | momentum | +1.45% | +0.091 | 0.540 | 100 日均線變動率切換的長回看反轉 |

- Bottom：085/101/077/001/098（做多的方向整段期間持續做反，最差 −0.076 日 IR）。
- 主題 IC 中位：momentum +0.68% > reversal +0.58% > volatility +0.55% > volume +0.23%
  （67 支 volume 類是重災區，貢獻了 bottom 5 的 4 席）。

## 近兩年窗（2024–2025）——比全期更好，不是更差

- IC mean 中位 **+0.59%**（全期 +0.37%）；|IR|>0.03 有 83 支（全期 64）；top1 日 IR 0.170（全期 0.120）。
- Top3：`007`（又是它，IC+1.46%、IC+ 0.586）、`016`（volume）、`035`（vol/mom）。
- 可能解讀（未驗證，僅列假說）：(a) 2020.03 COVID 崩盤的極端橫截面拉高全期 IC 噪音；
  (b) 近窗的成分清單失真較輕（survivorship bias 對近窗傷害較小）；
  (c) 2024–25 高散戶參與／高集中度行情下，價量短週期效應回潮。
- 注意：兩窗 top 名單重疊有限（007/035/038 兩窗皆入 top10；032 兩窗皆前 11），多數因子的窗間排名漂移大
  ——單窗排名本身噪音很重，選因子看跨窗交集比看單窗名次可靠。

## 橫截面廣度的教訓（degraded 50 檔 vs 正式 503 檔，同全期窗）

| | 50 檔（degraded） | 503 檔（正式） |
|---|---|---|
| 可測支數 | 81 | 100 |
| IC 中位 | +0.12% | +0.37% |
| \|IR\|>0.03 | 19 支 | 64 支 |
| Top 日 IR | 0.045 | 0.120 |

Rank IC 對橫截面廣度極敏感：50 檔 mega-cap 幾乎沒有因子分散度可排。
**工具在 Wikipedia 被擋時會靜默降級成 50 檔**——之後任何人重跑，
先檢查輸出裡沒有 `degraded run` 字樣再讀數字。

## 判讀與限制

1. 「全部 dead」是**對工具門檻**而言（IC>2% 在 2020s 美股大型股的日頻單因子上
   本來就幾乎不存在）；正確讀法是「有統計顯著的微弱訊號、無可直接交易的訊號」。
2. Survivorship bias 讓以上數字**系統性偏樂觀**——真實可得表現更差。
3. 1 日 horizon、無成本、無做空約束：這是訊號含量測量，不是策略回測。
   IC ~1% 的因子在日頻換手下扣成本即歸零；若要用，方向是多因子合成＋降頻。
4. 單一免費數據源（Yahoo），未做第二來源複核；splits/除息品質未審計。
5. 對 KIWI 的實際意義：alpha101 沒有可以直接抄的東西；有價值的是
   (a) `007/043` 型「放量反轉」結構與 wavetrend 的量能邏輯可互相印證；
   (b) 這條 bench 管線本身——之後可對 zoo 內其他 460 支或自建因子重跑。

## 檔案

- `bench_2020-2026_503names.json` / `bench_2024-2025_503names.json`：兩窗完整 100 支結果
- `report_2020-2026.html` / `report_2024-2025.html`：工具原生報告（含 skip 原因）
- `baseline_degraded_50/`：50 檔 degraded 基線（對照組）
- 重現：見 `projects/vibe-lab/README.md`
