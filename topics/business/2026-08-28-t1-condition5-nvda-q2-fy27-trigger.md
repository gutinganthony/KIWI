---
title: T1 條件⑤ 檢核 — NVDA Q2 FY27：供應商融資擴散**觸發**
url: local
date_added: 2026-08-28
topic: business
tags: [T1, exit-signal, nvda, vendor-financing, receivables, dso, memory, sk-hynix, revenue-quality]
version: 1.0
related: [./2026-07-28-nvda-vendor-financing-two-sided-review.md, ./2026-07-26-memory-bear-market-multifactor-verdict.md, ../../skills/serenity/exit-playbook.md]
---

# T1 條件⑤ 檢核 — NVDA Q2 FY27

> **為什麼跑這個**：Jake 2026-08-25 裁決 T1 不降級、維持出場觸發 → v2 六條即刻生效。
> 條件⑤（供應商融資擴散）在 2026-08-19 重跑時標為「本輪未查」，而 NVDA Q2 FY27 於
> **2026-08-26 盤後**開獎，是六條裡最近的裁判日。
> **⚠️ 全部數字為二手來源交叉（雲端對 SEC/報價 API 皆受限），標 `[推論]`；建倉/減碼前建議以 10-Q 原文複核。**

## 〇、結論：**條件⑤ 觸發**（三個子條款中兩個命中）

條件⑤ 原始定義（`2026-07-28-nvda-vendor-financing-two-sided-review.md:83`，**任一成立即觸發**）：

> ⑤ 供應商融資擴散度：NVDA（或 AMD）對客戶的擔保/融資/認股權證安排**再擴大**、
> 或任一錨定客戶（OpenAI／Anthropic）出現**募資困難**、
> 或 NVDA **應收帳款/合約資產增速顯著高於營收**

| 子條款 | 判定 | 證據 |
|---|---|---|
| (a) 擔保/融資安排**再擴大** | ✅ **命中，且是大幅擴大** | 2026-08 對 SB Energy PORTS-Pike（俄亥俄）提供土地/電力/外殼建置信用擔保，鎖定 **4.25 GW**、20 年租約**專供 OpenAI**；**擔保義務上限 $1,050 億**（分階段生效，首批預計 FY2029）。供應與產能承諾增至 **$2,790 億**，跨供應/雲/資料中心/股權/capex 總未來承諾 **$3,660 億** `[推論]` |
| (b) 錨定客戶募資困難 | ❌ 未見證據 | 本輪未查到 OpenAI／Anthropic 募資困難 |
| (c) 應收增速**顯著高於**營收 | ✅ **明確命中** | 見下表 |

## 一、(c) 的數字（最乾淨的一條）

| 指標 | 數值 |
|---|---|
| 應收帳款 | **$38.5B（2026-01-25）→ $63.1B（2026-07-26）＝ +63.9%** |
| **DSO** | **45 → 60 天，單季 +33.3%**。⚠️ **前八季都在 43–46 天的窄帶** |
| 單季對比 | **應收 +64% vs 營收環比 +18% ＝ 應收增速是營收的 3.6 倍** |
| 自由現金流 | **$48.6B → $21.3B ＝ 單季蒸發 $27.3B（−56.2%）** |
| 應收集中度 | 五家直接客戶佔 **22%/14%/13%/11%/10% ＝ 70%**（約 **$44.1B** 集中在五個名字） |

Q2 FY27 營收 $96.22B（YoY 約 +96%）、EPS $2.22，均超預期；Q3 指引 $108.0B。
→ **損益表非常好看，現金流與應收品質是另一回事。這正是 2026-07-28 那份檢討預言的形狀**：
> 「擔保在觸發前是**表外或有負債**；營收今天認列，信用損失未來才實現。**這種結構在財報上短期一定好看。**」

## 二、誠實的三個限制（必須跟結論一起讀）

1. **NVDA 自己的說法是「investment grade 客戶」**——延長付款條件 90 天至一年，用於大型資料中心建置。
   這與原始文件擔心的「信用敏感的 neocloud」**不是同一批人**。
   ⚠️ **但這個說法只涵蓋應收那一塊，不涵蓋擔保那一塊**：$1,050 億擔保的最終承租人是 **OpenAI**，
   而 OpenAI 並非 investment grade。**信用風險實質上是 OpenAI 的，只是包裝在對 SB Energy 的擔保裡。**
2. **條件⑤ 是間接推論，不是直接證據。** 它的機制是「供應商融資擴散 ⇒ 需求品質下降 ⇒ 記憶體需求可能虛胖」。
   **NVDA 延長付款條件不等於終端需求消失。**
3. **全部為二手數字**，未經 10-Q 原文逐項複核。

## 三、⚠️ 這次檢核暴露的框架缺口（比觸發本身更該處理）

**T1 觸發了，但沒有可執行的減碼指令。** 兩個原因：

1. **`exit-playbook.md` §2.1／§2.2 的減碼表是為 DRAM ETF 與 MU 寫的——那兩檔 2026-08 已全數出場。**
   現有記憶體部位是 **SK hynix ADR（20.47%）**，而**它沒有任何減碼比例定義**。
2. **條件⑤ 本身從未被寫進任何減碼表**。它是 2026-07-28 新增的，而 v1 減碼表寫於 2026-07-27。
   AGENDA 只說它「與合約價轉跌同權重（可能更領先）」——**同權重是多少？沒寫。**

> **Jake 2026-08-25 決定「T1 維持扣扳機」，第一次檢核就撞到「扳機在、但槍口沒指向任何東西」。**
> 這不是反對那個決定，而是那個決定的**必要配套還沒補完**。

## 四、needs Jake（本檔不代為決定）

1. **條件⑤ 觸發要不要動 SKHY？動多少？**
   - 參考：v1 給「合約價 QoQ 轉負」的是 **減 1/2**，給前置訊號的是 **減 1/3**。
   - 條件⑤ 被定義為「與合約價轉跌**同權重**」→ 字面推論是 **減 1/2**（SKHY 20.47% → 約 10.2%）。
   - **但這是我的字面推論，不是你寫過的規則。**
2. **要不要為 SK hynix ADR 補一張減碼表**（比照 §2.1 的結構）。
3. **條件⑤ 未來的減碼比例要寫死多少**，避免下次再遇到同樣的空白。

## 五、否證條件（什麼情況代表這次觸發是假訊號）

- 下一季 **DSO 回到 43–46 天窄帶** → 本次為一次性的多季合約時序效應，非趨勢。
- 應收集中的五家客戶**具名後確為 investment grade 且無展期** → (c) 的信用疑慮降級。
- **FCF 回升至營收的正常比例** → 現金流缺口是時序而非品質問題。

## 來源

- [Nvidia (NVDA) Q2 2027 earnings report（CNBC）](https://www.cnbc.com/2026/08/26/nvidia-nvda-earnings-report-q2-2027-live-updates.html)
- [Nvidia's blowout earnings contained some red flags（CNBC）](https://www.cnbc.com/2026/08/27/nvidias-blowout-earnings-contained-some-red-flags.html)
- [60 days to pay: Nvidia is financing its own demand（FXStreet）](https://www.fxstreet.com/analysis/60-days-to-pay-nvidia-is-financing-its-own-demand-202608262148)
- [Why Is Everyone Worried About Nvidia's Days Sales Outstanding?（Yahoo Finance）](https://finance.yahoo.com/news/why-everyone-worried-nvidia-days-171446893.html)
- [NVIDIA Q2 revenue jumps to $96.2B｜10-Q（StockTitan）](https://www.stocktitan.net/sec-filings/NVDA/10-q-nvidia-corp-quarterly-earnings-report-ba2938ed4873.html)
- [NVIDIA CORP Form 10-Q（SEC，nvda-20260726）](https://www.sec.gov/Archives/edgar/data/0001045810/000104581026000075/nvda-20260726.htm)
- [Nvidia 10-Q Risks & Red Flags Redline（Hudson Labs）](https://www.hudson-labs.com/research/nvidia-q2-2027-earnings)
- 內部：`topics/business/2026-07-28-nvda-vendor-financing-two-sided-review.md`

## Update Log
- 2026-08-28 v1.0：建檔。條件⑤ 三子條款中 (a)(c) 命中 → 觸發；列出三個誠實限制；
  指出框架缺口（SKHY 無減碼表、條件⑤ 無減碼比例）；三題 needs Jake；四條否證條件。
