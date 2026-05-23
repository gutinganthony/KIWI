---
title: HBM 物理極限 + 光互連 + CPO 投資邏輯 — Jukan 觀點驗證
url: local
source: Jukan 分析 + SemiAnalysis + NVIDIA GTC + TrendForce + 學術論文
date_added: 2026-05-17
last_updated: 2026-05-17
topic: business
tags: [HBM, CPO, silicon-photonics, optical-interconnect, NVIDIA, memory, investment-thesis, deep-dive]
version: 1.0
---

## Summary

Jukan 提出的論點：HBM 堆疊正在同時撞上垂直（層數良率）和水平（GPU die 周長）的物理極限，光互連成為唯一出路。如果 HBM 從 GPU 封裝中拆出來用光橋接，CPO 需求量級會從「網路設備級」跳到「晶片級」，整個 CPO 供應鏈受益。

**驗證結果：核心邏輯合理（8/10），但時間軸偏早。2028 年 NVIDIA Feynman 才是真正落地的節點。**

---

## 一、論點逐一驗證

### 論點 1：HBM 堆疊撞上物理極限 ✅ 合理

| 數據 | 來源 |
|------|------|
| 8 層 HBM（99% 良率/層）→ 總良率 92% | [SemiEngineering](https://semiengineering.com/challenges-in-stacking-hbm/) |
| 12 層 → 87%，16 層更低 | 同上 |
| 目前最高 16 層（SK Hynix HBM4，48GB）| [SK Hynix CES 2026](https://news.skhynix.com/sk-hynix-showcases-next-generation-ai-memory-innovations-at-ces-2026/) |
| 24 層預計 2030 才到 | [SemiAnalysis](https://newsletter.semianalysis.com/p/scaling-the-memory-wall-the-rise-and-roadmap-of-hbm) |
| 16 層以上 bump pitch < 10μm，die 厚度問題嚴重 | 同上 |

**結論**：垂直堆疊確實在 16-20 層遇到嚴重的良率和工藝瓶頸。Jukan 說的「指數級上升」有數據支持。

### 論點 2：水平方向被 GPU die 周長卡死 ✅ 合理

- 目前高端 GPU（如 NVIDIA B200）的 die 周長已經佈滿 HBM stack
- 在現有 2.5D 封裝技術下，能擺的 HBM stack 數量受限於 interposer 面積和 die 邊緣長度
- CoWoS（TSMC 的封裝技術）面積已經逼近光罩極限

### 論點 3：光互連是剩下的選項 🟡 部分合理

**支持：**
- NVIDIA Feynman（2028）**首次引入矽光子**，用光信號取代電信號 → [Wikipedia](https://en.wikipedia.org/wiki/Feynman_(microarchitecture))
- NVIDIA 在 2026 GTC 展示光互連的 GPU 系統架構 → [NextPlatform](https://www.nextplatform.com/connect/2026/03/02/nvidia-sees-the-light-on-silicon-photonics-and-maybe-optical-switching/4093099)
- Coherent + NVIDIA 的 CPO 合作已公開 → [Futurum](https://futurumgroup.com/insights/nvidias-4b-optics-bet-signals-photonics-as-ais-next-bottleneck/)
- 學術界有「光互連記憶體」（Optically Connected Memory）的研究，能量效率 1.07 pJ/bit → [arXiv](https://arxiv.org/pdf/2008.10802)

**保留：**
- 光互連解決的是**長距離高頻寬傳輸**，但 HBM-GPU 之間的距離極短（mm 級），電氣互連目前仍夠用
- 從「光互連取代 HBM 封裝內的電氣連接」到量產，至少還需要 2-3 年
- 2028 Feynman 是第一個真正可能落地的節點

### 論點 4：CPO 需求從網路級跳到晶片級 🟡 方向對但時間軸早

**如果每顆 GPU 都需要光耦合點：**
- 現在：1 個機櫃 1-2 個 CPO 模組（交換機上）
- 未來：每顆 GPU 多個光耦合點 → 需求量跟 GPU 出貨量走

**但時間軸：**
- 2026-2027：CPO 仍以交換機為主（Quantum-X、Spectrum-X）
- 2028+：Feynman 引入矽光子後，GPU 級 CPO 才真正開始
- 大規模量產可能要到 2029-2030

### 論點 5：HBM 變成可插拔商品 🟡 有趣但太早

**邏輯鏈：**
```
HBM 拆出封裝 → 用光橋接 → 可獨立替換
→ 記憶體變成可插拔元件
→ 壞了換記憶體，不用整張卡報廢
→ 單次採購量降，但替換頻率升
→ 總需求可能還是往上走
```

**驗證：**
- 概念上合理，但目前沒有任何廠商公開展示「可插拔 HBM」的原型
- NVIDIA 的 Feynman 提到「custom HBM」，但沒有提到可插拔
- 更可能的中間形態：記憶體和 GPU 仍在同一個模組上，但用光互連取代部分電氣連接，而非完全拆分

---

## 二、投資邏輯驗證

### Jukan 的結論：「盯誰在解決記憶體怎麼連到 GPU」 ✅ 正確

| 受益方 | 為什麼 | 相關標的 |
|--------|--------|---------|
| **CPO 供應鏈** | 需求量級跳升（交換機級 → 未來 GPU 級）| $COHR (Coherent), $LITE (Lumentum), $II-VI |
| **矽光子** | NVIDIA Feynman 核心技術 | $COHR, $TSEM (Tower Semi), Intel Foundry |
| **先進封裝** | 不管光互連還是堆疊都需要 | $TSMC (CoWoS), $ASX (ASMPT), $BESI |
| **CPU 廠商** | 新架構需要控制層 | NVIDIA Rosa, AMD, Intel |
| **雲端廠商** | 成本結構可能被重寫 | MSFT, GOOGL, AMZN |

### 與我們 KIWI 已有分析的交叉

這個觀點跟我們之前存的兩篇文章直接相關：

1. **[光子學供應鏈投資邏輯](./2026-04-07-photonics-ai-infrastructure-investment.md)**：$AXTI, $SOI, $AAOI, $LITE, $COHR, $TSEM — Jukan 的論點為這個投資論文提供了新的需求驅動力（從「數據中心光模組」升級到「GPU 晶片級光互連」）

2. **[AI 記憶體崩盤風險](./2026-05-16-ai-memory-chip-boom-bust-analysis.md)**：如果 HBM 真的走向可插拔/解耦，記憶體的週期性會回歸，但 CPO 供應鏈會成為新的結構性受益者

---

## 三、時間軸判斷

| 時間 | 事件 | 投資含義 |
|------|------|---------|
| **2026** | CPO 在交換機上開始部署（NVIDIA Quantum-X） | CPO 股票已在漲 |
| **2027** | NVIDIA Rubin Ultra（1TB HBM4e）| HBM 堆疊極限更明顯 |
| **2028** | **NVIDIA Feynman 首次引入矽光子** | ← 關鍵轉折點 |
| **2029-2030** | GPU 級光互連量產？HBM 解耦？ | CPO 需求量級跳升 |

### 投資建議

- **現在（2026）**：CPO 故事已經在 price in，但 GPU 級光互連還沒有。可以開始建倉但不要追高
- **關鍵催化劑**：NVIDIA 2027-2028 的架構細節揭露，如果確認 Feynman 的光互連用於 GPU-HBM 連接 → CPO 股票會有第二波
- **最大贏家**：Coherent（$COHR）— 同時做 CPO + 矽光子 + 跟 NVIDIA 有合作關係 + TSEM 代工

---

## 四、回答 Jukan 的問題

> 「如果 HBM 可以從 GPU 封裝裡面拆出來，記憶體是不是變成可插拔的商品？」

**短期答案**：不會。2028 Feynman 的光互連更可能是模組內部的橋接，不是真正的「可插拔」。

**長期答案**：概念上是對的。如果光互連的延遲和頻寬能做到跟現在封裝內電氣互連一樣，那確實可以把記憶體解耦出來。但這需要：
1. 光互連延遲 < 1ns（目前能做到但成本高）
2. 頻寬密度跟 HBM TSV 一樣（目前差距大）
3. 成本下降到經濟可行

所以 Jukan 的直覺是對的，但完全實現可能要到 **2030+**。

> 「單次採購量降，但替換頻率升，總需求還是往上走」

**這個判斷非常精準。** 就像 PC 時代的 DRAM 一樣——可插拔反而讓升級門檻降低，更多人更頻繁地升級，總需求反而上升。AI 模型持續膨脹會確保需求端不會萎縮。

---

## Update Log

- 2026-05-17 v1.0: Jukan 觀點驗證 + 數據查核 + 時間軸 + 投資邏輯。
