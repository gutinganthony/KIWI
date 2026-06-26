---
title: HBM 理論下的持股影響評估 + 最值得佈局 + 尚未反映的板塊（Jake 持股）
url: local
source: 延續〈AI 半導體終局 — HBM token 經濟學〉的持股應用
date_added: 2026-06-10
last_updated: 2026-06-10
topic: business
tags: [HBM, portfolio, apacer, AAOI, murata, tokyo-electron, micron, hybrid-bonding, besi, asmpt, advantest, TSMC, GUC, power-semi, serenity, chokepoint]
related: [./2026-06-10-hbm-token-economics-ai-semiconductor-endgame.md, ./2026-05-29-serenity-chokepoint-three-market-scan.md]
---

> 持股（2026-06）：宇瞻 8271、AAOI、村田 6981.T、東京威力科創(Tokyo Electron)8035.T、Micron MU(期貨, 少量)。
> 核心理論：token 吞吐 ≈ HBM 容量 × 頻寬 → HBM 需求結構性指數成長；價值往「HBM + 其封裝/測試/設備/base die」遷移。

## 1. 逐檔影響評估

| 持股 | 在 HBM 理論裡的位置 | 受惠度 | 評語 |
|---|---|---|---|
| **Micron MU**（期貨） | **HBM 三雄之一（直接 pure play）** | ⭐⭐⭐ 最直接 | 理論最大受惠者；HBM4E base die 已交台積電(2027)。**但最循環、最波動，期貨＝槓桿→擇時風險最大**。盯 ASP 與良率 |
| **東京威力科創 8035**（WFE 設備） | **HBM/記憶體 capex + 先進封裝設備** | ⭐⭐⭐ 強結構 | HBM 吃晶圓兇（每 bit 用 ~2-3× 晶圓：TSV、堆疊、低密度）→ 蝕刻/沉積/塗佈/清洗需求升。WFE 寡頭、品質高、比 MU 不循環。**最佳「鏟子」之一** |
| **村田 6981**（MLCC/被動） | **AI 伺服器電源的高容值 MLCC** | ⭐⭐ 受惠不直接 | 120kW 機櫃電源去耦需要海量高階 MLCC，村田是龍頭；content-per-server 成長、較少被炒。**但公司大又含手機，AI 訊號被稀釋** |
| **宇瞻 8271**（記憶體模組） | **HBM 排擠一般 DRAM → DRAM/NAND 偏緊** | ⭐ 二階/低品質 | 受惠記憶體漲價(庫存+ASP)，工控/利基記憶體毛利較穩；但下游、低附加值、**純記憶體價格 beta**，不抓 HBM 價值。最像「週期股」 |
| **AAOI** | **光互連/CPO（不同層，與 HBM 無直接關係）** | ➖ 中性 | HBM 理論幫不到也傷不到它；屬另一條 AI infra 卡脖子（見矽光子/CPO 檔）。維持「控部位、結構威脅中長期」結論 |

**一句話**：你的組合在 HBM 理論上**其實佈局不差**——MU(直接) + TEL(設備) + 村田(被動) 覆蓋三層；**弱連結是宇瞻(低品質記憶體 beta)與 AAOI(另一條線)**。

## 2. 基於理論「最值得佈局」（品質排序）
價值往**瓶頸**遷移：HBM 廠 + 其「設備/測試/封裝/base die」。最高信心的品質標的：
1. **HBM 廠**：**SK Hynix（主導，你沒持有）** ＞ Micron（你有）＞ Samsung（翻身）。
2. **HBM 設備（你已有 TEL）**：另可看 Lam/AMAT/ASML。
3. **HBM 測試**：**Advantest 6857**（AI/HBM 測試龍頭，測試時間/強度隨堆疊上升）。
4. **HBM base die 移到代工**：**台積電 2330 + 創意 GUC 3443**（新增的價值捕捉）。
5. **混合鍵合**：**BESI ＞ ASMPT 0522.HK**（HBM4+ 堆疊的卡脖子設備）。

## 3. 🎯 尚未被完全反映的板塊/公司（找 alpha）
> HBM 本身已熱、price in 較多；真正「還沒完全反映」的是**HBM 的二階受惠（鏟子的鏟子）**——這些通常在 HBM 之後才 re-rate。

| 環節 | 標的 | 為何還沒完全反映 |
|---|---|---|
| **混合鍵合 hybrid bonding** | **BESI（AMS/US）、ASMPT 0522.HK** | HBM 從 TCB 轉混合鍵合是 HBM4(三星)/第7代(SK)的關鍵轉折；BESI 正從「利基」變「主要營收引擎」，**封裝競爭從產能戰轉技術戰**，市場仍當它是循環封測設備 |
| **HBM 測試** | **Advantest 6857**、測試介面 FormFactor FORM / MPI 6223 / 千如 6510 | 每顆 HBM 堆疊測試時間/成本上升；test 常被「相對記憶體廠」低估 |
| **HBM4 base die 代工** | **台積電 2330、創意 GUC 3443** | 三家 HBM base die 全外包台積電(N12→N3P)＝**HBM 價值漏到邏輯代工**；GUC 吃 custom HBM 控制器 IP/設計，市場多半只盯記憶體廠 |
| **高功率電源/VRM** | **MPWR、Infineon、Vicor、台達電 2308** | 120kW+ 機櫃→電源半導體/VRM/電源模組 content-per-rack 暴增；台達是電源+散熱複合 |
| **被動元件 content** | 村田(已持)、TDK、太陽誘電、**國巨 2327** | AI 伺服器 MLCC 用量是一般伺服器數倍，content 成長故事被 HBM 蓋過 |
| **散熱（液冷）** | **雙鴻 3324、BOYD** | 高功率機櫃液冷剛需（部分已反映，回檔可留意） |

**最高信心三個「鏟子的鏟子」**：① **BESI/ASMPT（混合鍵合）** ② **Advantest（HBM 測試）** ③ **台積電+GUC（HBM base die）**——都符合你 Serenity 卡脖子框架、且 re-rate 落後 HBM 本身。

## 4. 風險與接點（要誠實）
- 全部是 **AI capex beta**；理論的**命門**＝「token 需求成長 vs 軟體效率(FP4/MoE/KV 壓縮)」誰快 + AI capex 消化（接 Jain/bubble boi/SemiAnalysis 那條）。一旦 capex 消化，HBM 仍是**成長型「週期」**股，會回檔。
- **擇時**：用前面已驗證的抄底紀律（美股 −10%+站200DMA、台股深跌抱一年）分批；別追飆。
- **組合建議**：弱連結（宇瞻純 beta）可考慮換成品質更高的卡脖子（Advantest/BESI/GUC）；MU 期貨槓桿控好部位（最循環）。SK Hynix 是你目前缺的「HBM 主導者」純 play。

## Update Log
- 2026-06-10 v1.0：逐檔評估 + 品質排序 + 6 個尚未反映環節（最高信心：混合鍵合/HBM測試/base die 代工）。
</content>
