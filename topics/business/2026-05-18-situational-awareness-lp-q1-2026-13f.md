---
title: Situational Awareness LP — Q1 2026 13F 持股拆解（Leopold Aschenbrenner）
url: https://www.sec.gov/Archives/edgar/data/2045724/000204572426000008/0002045724-26-000008-index.htm
source: SEC EDGAR + Blockspace + Quiver Quantitative + Crypto.news + 24/7 Wall St.
date_added: 2026-05-18
last_updated: 2026-05-18
topic: business
tags: [investment, hedge-fund, 13F, AI-infrastructure, semiconductor, bitcoin-miner, Aschenbrenner, options, puts]
version: 1.0
---

## Summary

Leopold Aschenbrenner（前 OpenAI 研究員、《Situational Awareness》白皮書作者、24 歲）的 Situational Awareness LP 在 2026-05-15 提交 Q1 2026 13F、SEC 於 2026-05-18 受理。相較上一季（Q4 2025）的純多頭 AI 基建組合，本季出現**根本性策略轉變**：

- 持股檔數從 29 → **42**
- 總名目曝險（notional）從 $5.52B → **$13.67B**（+148%）
- 新加入約 **$8.7B 半導體 / AI 晶片股的 PUT 空單**（NVDA、AVGO、AMD、TSM、MU、ORCL、SMH ETF 等)
- 多頭部位仍集中在 **電力 + 儲存 + GPU 雲 + 加密礦工**
- 重大出清：Intel calls、Lumentum (LITE)、Coherent (COHR)

整體變成標準的 **Barbell（槓鈴）策略**：多頭擁有電力與資料中心場址的「實體」、空頭被市場過度定價的「晶片股」。

---

## 申報基本資料

| 項目 | Q4 2025 | **Q1 2026** |
|---|---|---|
| 報告期 (Period) | 2025-12-31 | **2026-03-31** |
| 申報日 (Filed) | 2026-02-11 | **2026-05-15（SEC 5/18 受理）** |
| Accession # | 0002045724-26-000002 | **0002045724-26-000008** |
| 持股檔數 | 29 | **42** |
| 總名目曝險 | $5.52 B | **$13.67 B（+148%）** |
| Equity 多頭 | $5.52 B | ≈$5.5 B |
| Put 空單 notional | — | **≈$8.7 B（新）** |

---

## Put 空單明細（本季新策略，重點）

| 標的 | Ticker | Notional |
|---|---|---|
| VanEck Semiconductor ETF | SMH | **$2.04 B** |
| Nvidia | NVDA | **$1.57 B** |
| Oracle | ORCL | **$1.07 B** |
| Broadcom | AVGO | **$1.01 B** |
| AMD | AMD | $969 M |
| Micron | MU | $584 M |
| Taiwan Semiconductor | TSM | $535 M |
| Intel | INTC | $159 M |
| **合計** | — | **≈ $8.7 B** |

> ⚠️ Put options 的 notional 不等於實際虧損上限或所投權利金；真實風險取決於 delta、到期日、履約價,13F 沒揭露這些。

---

## 多頭股票部位（Top Longs，含 calls）

| # | 標的 | Ticker | 部位 | 季變動 |
|---|---|---|---|---|
| 1 | Bloom Energy | BE | $878.7 M（6.49M 股 + calls） | 持平 |
| 2 | SanDisk | SNDK | $724.4 M + $389M calls | **大幅加碼** |
| 3 | CoreWeave | CRWV | $556.1 M + $141M calls | **大幅減碼**（Q4 $1.21B） |
| 4 | IREN | IREN | $401 M | 加碼 |
| 5 | Core Scientific | CORZ | $389 M | 持平 |
| 6 | Applied Digital | APLD | $320 M | 加碼 |
| 7 | Riot Platforms | RIOT | $142 M（11.5M 股，Q4 6.17M） | **+86%** |
| 8 | CleanSpark | CLSK | $104 M（12.28M 股，Q4 1.64M） | **+650% 🚀** |
| 9 | BitDeer | BTDR | 3.44M 股（Q4 1.79M） | **+92%** |
| 10 | Keel Infrastructure（前 Bitfarms） | KEEL | 19.88M 股（Q4 6.9M） | **+188%** |
| 11 | T1 Energy | T1E | 3.6% 部位 | **新進場** |

---

## 主要出清 / 平倉

| 標的 | Ticker | Q4 部位 | Q1 動作 |
|---|---|---|---|
| Intel call options | INTC | $747 M | **全數平倉** |
| Lumentum | LITE | $479 M | **全部出清** |
| Coherent | COHR | $60 M | **全部出清** |

> 諷刺的是,Q4 才把 LITE / COHR 加倉到 top holdings,Q1 直接全砍。同時把 INTC 從 call 翻成 put,代表他對半導體股的看法在這個季度做了 180° 轉彎。

---

## 投資邏輯讀後感

從 Q4 的「**純多頭 AI 基建**」→ Q1 的 **Barbell**：

- **多頭(實體基建)**：電力 (BE)、儲存/NAND (SNDK)、GPU 雲 (CRWV)、加密礦工轉 AI 託管 (CORZ, IREN, APLD, RIOT, CLSK, BTDR, KEEL)、太陽能/儲能 (T1E)
- **空頭(估值過高的供應商)**：幾乎所有大型半導體股（NVDA, AVGO, AMD, TSM, MU, ORCL）+ 整個 SMH ETF

翻譯成一句話:
> AI 軍備競賽會繼續,但**晶片股估值已透支整輪 AI capex,真正稀缺的是「擱淺電力 + 場址 + GPU 雲容量 + 儲存」這些實體資源**。

對照他 2024 年寫的《Situational Awareness》白皮書(主張 AGI 在 2027、超智能在 2028–2030),這次的部位調整與他的 thesis 完全一致 ── 不是放棄 AI,而是賭**第二階段(power & physical infra)的瓶頸**。

---

## 市場反應(2026-05-18 當日)

- **HIVE Digital** +34%
- **T1 Energy** +20%
- CleanSpark / Riot / CoreWeave 相對冷靜（市場可能注意到 CRWV 被減碼）

---

## 注意事項與盲點

1. **13F 只揭露美股多頭部位**;不含空頭股票(只有透過 put 才會出現)、海外股、加密貨幣現貨、私募部位
2. **45 天延遲**:Q1 部位是 3/31 快照,5/18 才公開 → 過去 1.5 個月他可能已經調倉
3. **Put notional ≠ 實際虧損上限**:他可能只花了幾千萬權利金就拿到 $8.7B notional 曝險
4. **跟單風險**:他的 thesis 短期可能被軋空(NVDA 如果繼續創高,他要繳保證金),長期 thesis 也可能錯
5. **Confidential treatment**:沒有跡象顯示他申請了延遲揭露,所以這份應該是完整版

---

## 我的後續追蹤項目

- 等下季 Q2 2026 13F(2026-08-15 截止)看他是否:
  - **加碼** put 空單 → 證明他在這個 thesis 上加碼
  - **減碼** put 空單 → 可能已實現獲利或方向錯了
  - 多頭部位裡是否新增更多**獨立發電 (IPP)** 或**資料中心 REIT**
- 觀察今天市場反應對 KEEL、T1E、IREN 等流動性較低的小型股是否有持續性

---

## 來源

- [SEC EDGAR — Q1 2026 申報原文 (0002045724-26-000008)](https://www.sec.gov/Archives/edgar/data/2045724/000204572426000008/0002045724-26-000008-index.htm)
- [Blockspace — $5.5B 多頭 + 半導體 puts 分析](https://blockspace.media/insight/situational-awareness-lp-bitcoin-miner-longs/)
- [Crypto.news — Aschenbrenner bets $13.6b on miners](https://crypto.news/leopold-aschenbrenner-bets-13-6b-on-miners/)
- [Quiver Quantitative — Nvidia & AI 晶片巨額 put 部位](https://www.quiverquant.com/news/Former+OpenAI+Employee%E2%80%99s+Hedge+Fund+Unveils+Massive+Nvidia+and+AI+Chip+Options+Positions)
- [Quiver — CleanSpark 加碼 10.6M 股](https://www.quiverquant.com/news/Fund+Update%3A+10%2C635%2C739+CLEANSPARK+%28CLSK%29+shares+added+to+Situational+Awareness+LP+portfolio)
- [24/7 Wall St. — 市場反應 HIVE +34%、T1E +20%](https://247wallst.com/investing/2026/05/18/hive-digital-rockets-34-t1-energy-jumps-20-on-aschenbrenner-buzz-but-cleanspark-riot-coreweave-stay-quiet/)
- [Sherwood News — 出清 LITE 與 COHR](https://sherwood.news/markets/lumentum-coherent-fall-after-hedge-fund-manager-aschenbrenner-dumps-his-holdings/)
- [Yahoo Finance — 13F 申報新聞](https://finance.yahoo.com/markets/options/articles/leopold-aschenbrenners-situational-awareness-files-174339413.html)
- [13F.info — Situational Awareness LP 完整持股明細](https://13f.info/manager/0002045724-situational-awareness-lp)
- [WhaleWisdom — Top 13F Holdings](https://whalewisdom.com/filer/situational-awareness-lp)
- 對照閱讀(同 KIWI):[2026-04-07 光子學供應鏈投資邏輯](./2026-04-07-photonics-ai-infrastructure-investment.md) — Q4 還在加 LITE/COHR,Q1 全砍,可看出光通訊敘事的反轉
