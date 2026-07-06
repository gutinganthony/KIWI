---
title: AI 半導體終局 Part II — HBM/DRAM/NAND 到 2030 會不會重回週期（分析師驗證版）
url: local (推文 @fi56622380 Part II，使用者提供全文)
source: @fi56622380 (X)〈AI半導體終局推演2026 (II)〉— 大白話改寫版
date_added: 2026-06-10
last_updated: 2026-06-10
topic: business
tags: [HBM, DRAM, NAND, memory-supercycle, cyclicality, CXMT, YMTC, agentic-AI, CPU, sk-hynix, micron, apacer, sandisk, 2030, chokepoint]
related: [./2026-06-10-hbm-token-economics-ai-semiconductor-endgame.md, ./2026-06-10-nvidia-rubin-cut-hbm4-slowdown-tracker.md, ./2026-06-10-serenity-scorecards-hbm-memory-optical.md]
---

> Part II 用「打破週期的三條件」框架，推演 HBM/DRAM/NAND 到 2030 是否脫離傳統週期。
> 本檔＝分析師驗證：哪裡紮實、哪裡誇大，並與我剛追的「Rubin 砍單/HBM4 放緩」事件 + Part I 綜合。

## ★ 一句話判決
**框架很好、HBM「成長週期」紮實、「一般 DRAM 也變緊」這個較新的洞見也對（而且剛被現實證實）；但有兩處明顯誇大（CPU 1:1 / $4000億、長鑫輕敵），NAND 最弱。最重要的提醒：「週期論點對」≠「股票在 $1T / 68–159x PE 是買點」——這是兩件事。**

## 1. 易懂摘要：打破週期的三條件 + 三種記憶體評分

**傳統記憶體週期的病根**：建廠要 3 年、上百億美元、回不了頭 → 需求高峰時擴產 → 廠好了需求過峰 → 崩盤。
**打破週期的三條件**：①產品高度定制化（要簽長約、產能不能亂轉）②需求指數成長（供給永遠追不上）③技術迭代極快（舊品速貶、沒人囤）。滿足越多越脫離週期。

| | ①定制化 | ②指數需求 | ③迭代快 | 脫離週期？ | 我的補充 |
|---|---|---|---|---|---|
| **HBM** | 半條(三星沒過 NVIDIA 認證→轉供 Google/AMD) | ✓(KV cache 每代翻倍) | ✓(2 年一代 vs DDR 15 年) | **大部分脫離** | **靠「結構」脫離→最耐久** |
| **一般 DRAM** | ✗(commodity) | ~✓(agent 常駐記憶體+CPU server 爆發) | ✗(DDR 迭代慢) | 文章稱「實質脫離」 | **其實不符三條件；它脫離週期是靠「需求缺口」這個單一論點→較脆，需求假設錯就破** |
| **NAND** | ✗ | 部分(冷資料/AI 影片/agent 浪費式佔用) | ✗ | 部分脫離 | **最弱、最靠廠商自律 + YMTC 變數** |

**關鍵洞見（值得收）**：HBM/DRAM/NAND 不是三個獨立故事，而是同一個 AI 記憶體層級「快→便宜」三層（熱資料 HBM、溫資料 DRAM、冷資料 NAND），**會一起漲、互相補位**。

## 2. 分析師逐項驗證

| 主張 | 裁決 | 註 |
|---|---|---|
| HBM 供給只能 ~年增 23%、vs 指數需求 | ✅ 合理 | 供給受 TSV/堆疊/良率限制；缺口擴大與我查到的「HBM 已吃 23% DRAM 晶圓、新 fab 2027+ 才放量」一致 |
| 三星 HBM 沒過 NVIDIA 認證→轉供 Google/AMD | ✅ 屬實 | 也誠實點出「定制化只算半條」——好的自我打折 |
| DDR3→DDR5 花 15 年 vs HBM 2 年一代 | ✅ 正確 | — |
| **一般 DRAM 也在脫離週期（agent 常駐記憶體）** | ✅ **較新且已被證實** | **正是我剛追的事件：一般 DRAM 缺到 margin 比 HBM 高 >15pp、SK Hynix 把產能從 HBM 倒回一般 DRAM**。Part II 的理論＝現實上演 |
| **CPU:GPU 趨近 1:1、CPU TAM $2000~4000 億(2030)** | ⚠️ **方向對、數字誇大** | 旗艦機架 **Vera Rubin NVL72=1 CPU:2 GPU**，非 1:1；但 agentic 確實把 1:4~8 推向 1:1（Arm：每 GW CPU 核心 3000萬→1.2億）。**惟 CPU TAM 共識 ~$120B(2030)、>35%/年，$4000億是高標** |
| **長鑫 CXMT 密度只有一半、DDR6 撞更大牆** | ❌ **過時/太輕敵** | CXMT 已推 **DDR5-8000/LPDDR5X-10667（規格追上）**，成本/bit 高約 **30%（非密度差一半）**，且**可能全球第一個 2026H2 推 LPDDR6**。**CXMT 是比文章承認更大的中期風險** |
| 「蓄水池」效應(降價→壓抑需求湧出接盤) | 🟡 真但偏軟 | 需求有彈性是真的，但在真正超供時蓄水池回填慢，能緩衝、不能保證不崩 |
| 2030 光 agent 新增 DRAM 需求 > 今天全產業總產量 | 🟡 最佳情境外推 | 取決於 agent 常駐記憶體假設複利成立；當「牛市情境」非「基準」 |
| NAND 最弱、靠自律 + YMTC 變數 | ✅ 正確 | NAND 技術門檻低、最 commodity；YMTC 不講武德就破 |

## 3. 與 Rubin 事件 + Part I 的綜合（最重要）
- **Part I**（token 吞吐 = HBM size×頻寬）→ 解釋 HBM 為何指數成長。
- **Part II**（三條件 + 一般 DRAM 也緊）→ 解釋為何 HBM **與** 一般 DRAM 都脫離週期。
- **現實事件（Rubin 砍單/HBM4 放緩）** → **正是 Part II「一般 DRAM 變得比 HBM 更賺」的活證據**：SK Hynix 理性把產能往一般 DRAM 倒，GS/MS 認為是「供給紀律」利多。**所以那次 −12% 是供給側重分配，不是需求消化**（見 tracker 檔）。
- **三者互相印證**：理論(I/II) + 現實(事件) 高度一致 → 記憶體「成長超級循環」論點**可信度高**。

## 4. 但兩件事必須分開（風控核心）
1. **「週期論點對」≠「股票是買點」**：SK Hynix/MU $1T、SNDK +4000%/68x、LITE 159x——**論點 80% 對，股票仍可在「ASP 走平 + Rubin 小延」時大幅 de-rate**。Part II 講的是「循環/基本面」，不是「估值」。
2. **真正能打破這套論的三個風險**（依先後）：①**CXMT/YMTC 中國不講武德擴產**（DRAM/NAND，2027-28 起，比文章想的大）②**ASP 2026 下半年走平**（供給逐步追上）③**AI 架構長期演進**（5 年+：若 KV cache/注意力機制改變，HBM 強度下降——Part I 的軟體命門）。

## 5. 關鍵節點（更新）
1. **Hyperscaler capex 指引**（總開關，目前 +40% 未砍）。
2. **一般 DRAM ASP + HBM↔一般 DRAM margin 差**（Part II 的核心新變數；現在一般 DRAM 更賺）。
3. **CXMT/YMTC 擴產與良率**（DRAM/NAND 脫離週期論的最大反證；盯 LPDDR6、HBM3 國產化進度）。
4. **CPU:GPU 比例 + server CPU TAM 上修**（agent 帶動一般 DRAM 的驅動力驗證）。
5. **實際 Rubin 出貨時程**（HBM4 指數拐點）。

## 6. 對 Jake 持股的意涵
- **一般 DRAM 變緊＝對宇瞻 8271 正向 re-read**（Part II + 事件雙重支持；先前低分主因是「低品質 beta」，但這波一般 DRAM 缺貨是它的真順風）——但記住它仍是 commodity、CXMT 是它的長期天敵。
- **SK Hynix/MU**：論點最強、但已 $1T——**等回檔用「好生意」身分進**，別追。
- **SNDK**：Part II 自己也說 NAND 最弱、靠自律 + YMTC 變數→**+4000%/68x 的狂熱與最脆弱的基本面落差最大，續避**。
- **CXMT 是整個 DRAM 論點的長期 X 因子**：若你要長抱記憶體，必須持續追蹤 CXMT/YMTC（我已列為節點 3）。

## 來源（驗證用）
- [Vera Rubin NVL72 = 72 GPU:36 CPU (1:2) (NVIDIA)](https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72/)
- [Agentic AI 把 CPU:GPU 從 1:4~8 推向 1:1；CPU 核心/GW 4 倍 (AMD/Arm)](https://www.amd.com/en/blogs/2026/agentic-ai-changes-the-cpu-gpu-equation.html)
- [Server CPU TAM >$120B by 2030、>35%/yr (uncoveralpha)](https://www.uncoveralpha.com/p/the-forgotten-chip-cpus-the-new-bottleneck)
- [CXMT 推 DDR5-8000、成本高~30%、或全球首發 LPDDR6 (TechPowerUp/Caixin)](https://www.techpowerup.com/343185/chinese-cxmt-shows-homegrown-ddr5-8000-and-lpddr5x-10667-memory)
- [CXMT 進主流 DDR5 / 國產 HBM3 2026 (Tom's Hardware)](https://www.tomshardware.com/pc-components/dram/chinese-semiconductor-industry-gears-up-for-domestic-hbm3-production-by-the-end-of-2026-cxmt-to-produce-chips)

## Update Log
- 2026-06-10 v1.0：Part II 分析師驗證。框架紮實、HBM+一般DRAM 脫離週期成立(且被 Rubin 事件證實)；兩處誇大(CPU 1:1/$4000億、CXMT 輕敵)；NAND 最弱。最大 X 因子＝CXMT/YMTC。核心提醒：週期對≠股票是買點。
</content>
