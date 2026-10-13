---
title: 記憶體八因子季度重跑（2026 Q4 輪）＋ T1 v2 六條逐條判定
url: local
date_added: 2026-10-13
topic: business
tags: [memory, dram, nand, hbm, T1, T6, eight-factor, quarterly-rerun, apacer, 8271, cxmt, hyperscaler-capex]
version: 1.1
related: [./2026-07-26-memory-bear-market-multifactor-verdict.md, ./2026-08-28-t1-condition5-nvda-q2-fy27-trigger.md, ../../skills/serenity/exit-playbook.md, ../../skills/serenity/holdings.md]
---

# 記憶體八因子季度重跑：2026 Q4 輪

> **執行日 2026-10-13**（AGENDA 到期日 10/15，**本輪準時**）。這是 2026-08-25「T1 不降級」裁決要求的每季重跑。
> 上一輪：2026-07-26 v1.0 判定、2026-08-19 §9 重跑（逾期 20 天）。
> **標記**：`[一手]`＝公司新聞稿、SEC 申報或 TrendForce 官方新聞稿原文；`[二手]`＝媒體轉述；`[推論]`＝本檔推導；`未取得`＝查不到，沒有補數字。
> **來源可達性**：trendforce.com、sec.gov／data.sec.gov、api.finmindtrade.com 用 curl 直連成功。news.samsung.com、dramexchange.com、technews.tw、marketbeat、heraldcorp、platformonomics、blocksandfiles 被代理 403（CONNECT rejected），這些站的內容一律改用二手轉述並在文中標明。

## 0. 摘要（結論先行）

1. **實體面仍未見頂，維持 8/19 判定。** 一階導數繼續變強：Samsung 3Q26 營業利益 ₩107.4 兆創歷史新高，略高於共識（₩106.64 兆或 ₩106.1 兆，視來源而定，約高 0.7–1.2%）；Micron FQ4 毛利率 86.8%、FQ1 營收指引 $61.5B。
2. **價格面是混合訊號，不是全面轉弱。** DRAM 合約價繼續收斂：4Q26 一般型 DRAM +10–15% QoQ，3Q26 為 +13–18%。**NAND 合約價反而加速**，從 +10–15% 升到 +15–20%（TrendForce 9/30）。現貨方面，**只有 DDR5 和 NAND wafer 轉弱**：DDR5 詢價放緩、部分顆粒轉軟；NAND wafer 現貨 8/31→10/5 跌 9%。DDR4 現貨 8/12→10/6 反而漲約 9%，最近兩週持平。另外 TrendForce 說模組廠「需求弱、庫存高」。
3. **T1 v2 六條**：①②③④ 未觸發，其中 ② 是推定（沒有伺服器 DRAM 的 QoQ 數字）。⑤ 維持 8/28 的「觸發」，本輪沒有新增擴大證據；但 **(b) 照 8/28 檔 §6.4 的字面已達升級門檻**（OpenAI IPO 延到 2027），要不要升級待 Jake 裁決。⑥ 無法判定，因為門檻沒寫數字。**本輪沒有任何一條新觸發。**
4. **本輪新出現、8/19 沒看到的兩個需求端訊號**：(a) GPU／ASIC 廠和 CSP 開始為了成本**降低每台記憶體配置**（例如 HBM 12-Hi 改 8-Hi）；(b) TrendForce 估記憶體佔 CSP capex 的比重從 2026 年 47% 升到 2027 年 68%，代表**名目 capex 的增長越來越多是價格，不是量**。這會讓 T1④／T6 在位元需求下滑時仍然顯示「未觸發」，是結構性盲點。**反方證據**同樣來自 TrendForce 一手：CSP 和伺服器 OEM 正在**增加**一般伺服器 RDIMM 的位元採購（9/30）；8-Hi 每 Gb 反而比 12-Hi 貴 10–20%，降配置「不太可能扭轉 HBM 大幅漲價的趨勢」（9/29）。所以這兩點是**量的隱憂**，還不是量已經下滑的證據。
5. **T1 目前管的部位是零，本輪結果不會產生任何減碼動作。** 有實際意義的是兩件事。一是 **8271 宇瞻**：營收從 4 月高點下滑，3Q26 季減約 11%，同期上游合約價卻還在漲。二是 **T6 前哨**：Alphabet 2Q26 自由現金流轉負（−$5.9B），靠發行股票和債券支應 capex。
6. **最近的裁判日都落在未來 5 週內**：SK hynix 3Q（約 10/28，日期未確認）、Samsung 3Q 完整財報（10/29）、四大 hyperscaler 3Q 實際 capex（10 月底）、NVDA Q3 FY27（約 11/18）。**建議 10/30 後針對 ④⑤ 做一次小重跑。**

## 1. T1 v2 六條逐條狀態

門檻原文出自 `skills/serenity/exit-playbook.md` §3。

| # | 門檻原文 | 本輪實測值 | 狀態 |
|---|---|---|---|
| ① | 4Q26／1Q27 合約價 QoQ **轉負**（刪掉「走平」） | **4Q26 一般型 DRAM +10–15%、NAND Flash +15–20%**（TrendForce 2026-09-30 新聞稿 `[一手]`）。**1Q27：未取得**，TrendForce 尚未發布 [推論：通常在 12 月底到 1 月初發布] | **未觸發** |
| ② | **HBM／伺服器 DRAM** 合約價 QoQ 轉負（不看現貨、不看 DDR4） | 伺服器 DRAM 4Q26「仍供不應求」，部分供應商因 LTA 定價機制漲幅低於市場平均，**新聞稿沒有給伺服器 DRAM 單獨的 QoQ 數字**（TrendForce 9/30 `[一手]`）。HBM 2027 混合 ASP **上修為 +121% YoY**（TrendForce 2026-09-29 `[一手]`；8/25 時為 +70–140%） | **推定未觸發**。方向證據明確，但伺服器 DRAM 的 QoQ 數字未取得，HBM 只有 2027 年的年度數字 |
| ③ | 三大廠**售罄覆蓋期**由「2027 全年」縮短至 **<2 季** 🔧 | Micron：FY27 產出 **>75% 已鎖定**、SCA 由 16 份增加到 **26 份**、預估占 2030 年前營收 >35%、部分合約延伸到 2031（9/30 法說，Benzinga／Herald 等 `[二手]`）。Samsung：短缺「2027 年比今年更嚴重，並延續到 2028」，LTA 為 5 年滾動、附**地板價**（Khaleej Times 等，2026-08 `[二手]`）。TrendForce 轉述 Reuters：Samsung 與 Micron 都預期供給偏緊延續到 2028（2026-10-08 `[二手]`）。⇒ 覆蓋期 **≥5 季**。⚠️ **SK hynix 本輪沒有覆蓋期的直接證據**，只有「已與約 10 家客戶談完」和 8 月 DigiTimes「三大廠 2027 全數配完」的匿名報導 `[二手]`。三大廠中只有兩家有直接說法 | **未觸發**（Micron 與 Samsung 的覆蓋期沒有縮短，反而延伸到 2028；SK hynix 缺直接證據） |
| ④ | hyperscaler **實際資本支出**連兩季低於前次指引，**且排除會計重述** | 2Q26 四家實際 capex（PP&E 現金支出，SEC XBRL `[一手]`）：MSFT $35.8B、GOOGL $44.9B、AMZN $54.2B、META $30.1B，合計 **$165.0B，季增 +27%**（1Q26 為 $129.8B）。指引：GOOGL 上修到 $195–205B；META 為 **$130–145B（由 $125–145B 收窄，下緣上調）**（Meta 8-K 2026-07-29 `[一手]`）；AMZN 約 $220B `[二手]`；MSFT CY26 由約 $190B 改為約 $175B，**原因是資料中心使用年限從 15 年延長為 25 年，部分融資租賃改列營業租賃，屬會計變更、已排除**（CFO Dive 等 `[二手]`）。**沒有任何一家下修指引。** 3Q26 實際值要到 10 月底才公布 | **未觸發**（3Q 實際值未取得） |
| ⑤ | 供應商融資擴散（2026-07-28 定義：擔保/融資再擴大、或錨定客戶募資困難、或 NVDA 應收增速顯著高於營收） | 8/28 已判觸發，(a)(c) 兩項命中，10/8 經 10-Q 一手複核仍成立。**本輪沒有查到新的擔保或融資擴大事件**（9 月至今的搜尋沒有結果，不代表沒有發生）。(b) 灰區：OpenAI 洽談**至少 $30B 過橋輪、估值約 $1.4T，IPO 延到 2027**，Altman 稱「現在上市是不明智的時機」，The Information 報導**尚未簽任何 term sheet**（Bloomberg 轉述，2026-09-30 `[二手]`）。同期年化營收接近 $70B（Axios/Reuters `[二手]`）。**8/28 檔 §6.4 升級欄的原文是「出現募資困難、估值下修或延遲」**。IPO 從 2026 延到 2027、過橋輪尚無 term sheet，**照字面已符合「延遲」** | **觸發（維持 8/28 判定）；(b) 照字面達升級門檻，本檔不自行升級，交 Jake 裁決（§5 Q1）**。不採字面的理由：(1) 估值從 $852B（3 月）上升到約 $1.4T，與「估值下修」方向相反；(2) 2026 年 IPO 從來不是公司的正式承諾，延期不等於募資失敗；(3) §6.4 的「延遲」原意較可能是指募資輪本身延遲，而 $30B 過橋輪 9/30 才開始談，還談不上延遲 [推論]。支持字面的理由：用過橋輪取代 IPO，正是資金需求大於可得資金時的典型動作。**因為 T1 管的部位是零，升不升級都不會產生動作**。下一個裁判日是 NVDA Q3 FY27（約 11/18，公司未確認） |
| ⑥ | **CXMT DDR5 良率達標／HBM 通過客戶驗證** | HBM3：8 層試產良率**約 25%**（ChosunBiz 2026-09-09，引述匿名設備業者 `[二手]`）；量產可能要等阿里平頭哥、寒武紀測試後才在 **2027** 開始（2026-09-20 報導 `[二手]`）；**沒有查到任何客戶完成驗證**。DDR5：良率說法「約 80%」到「約 90%」，但 80% 來自 Citi 2024 年底的分析，且當時已被韓媒質疑；90% 的說法沒有日期 `[二手]` | **無法判定**。HBM 那一半未觸發。DDR5 那一半因為「達標」沒有數字門檻而無法判定。若以 80% 當門檻，二手說法早已達到，⑥ 會被一筆兩年前的舊數字誤觸發，**需要 Jake 定義（見 §5 Q1）** |

**合計：0 條新觸發，1 條維持觸發（⑤，其中 (b) 字面上達升級門檻、待裁決），1 條無法判定（⑥），② 為推定未觸發。** 因為 T1 管的部位是零，以上全部只有觀察意義。

## 2. 八因子本季讀數（對照 7/26 與 8/19）

| # | 因子 | 7/26 → 8/19 | **10/13 讀數** | 方向 | 關鍵新證據 |
|---|---|---|---|---|---|
| 1 | 長約／客戶承諾 | 未現（強反證）→ 未現，反證更強 | **未現，反證再加強。「長約是頂部特徵」那種讀法也有新的旁證** | ↑ **偏多**（承諾量與期限都增加；頂部特徵只是旁證） | Micron SCA 從 16 份增加到 26 份，客戶財務承諾從 $22B 增加到 **$32B**，大部分是現金預付 `[二手]`。Micron FY26 現金流量表「客戶合約負債存款收入」**$12.75B** `[一手 8-K]`。**LTA 的價格條款是雙向的**：TrendForce 一手寫明「2Q26 起簽的部分 LTA 附**價格上限**，可能限制後續漲幅」`[一手 8/25]`，9/30 也說部分供應商因 LTA 定價機制漲幅低於市場平均 `[一手]`；Samsung 的 LTA 則被報導附**地板價**，用來對沖資本投資的下檔風險 `[二手]`。上限與地板並存，代表雙方都在鎖定區間；供應商買下跌保險這一點，跟 7/26 §3② 的讀法一致 [推論] |
| 2 | 合約價／現貨價 | 部分已現 → 「已現」那一半消失 | **混合：DRAM 合約價收斂、NAND 合約價加速；現貨只有 DDR5 與 NAND wafer 轉弱** | ↔ **混合**（合約價半邊偏強，現貨半邊轉弱） | 合約價：一般型 DRAM 3Q26 +13–18%（TrendForce 9/7 `[一手]`）→ **4Q26 +10–15%**（9/30 `[一手]`），仍為正。更早的 1Q26／2Q26 只有二手數字且互相矛盾：1Q26 有 +55–60%、+81%、+90–95% 三種說法，2Q26 為 +58–63%，**不作為判定依據**。⚠️ 8/19 記錄的 4Q26「+8–13%」比 9/30 正式稿低，**正式稿反而略高，所以收斂速度比 8/19 認為的慢**。NAND **由 +10–15% 回升到 +15–20%**，只有企業級 SSD 加速。現貨（TrendForce 每週報告 `[一手]`）：DDR4 1Gx8 主流顆粒 $42.50（8/12）→ $46.32（10/6），**最近兩週持平**。9/16「DDR5 詢價放緩、部分顆粒開始轉軟」。NAND 512Gb TLC wafer **$20.708（8/31）→ $18.833（10/5），−9.1%** |
| 3 | 庫存 | 未現（低信心）→ 未現，但有層次歧義 | **歧義擴大：原廠端低，通路／模組端高，而且 Micron 的絕對庫存開始上升** | ↓（通路端轉差） | 原廠：TrendForce 9/7 稱供應商庫存「處於歷史低點」`[一手]`；KB 證券估 Samsung/SKH 記憶體庫存不到 10 天（DigiTimes 9/7 `[二手]`）。**但 Micron 庫存 $8.57B → $10.37B，季增 +21%**，以 FQ4 14 週計算 DIO 約 122 → 約 141 天 `[一手數字，DIO 為本檔自算]`。⚠️ 毛利率 87% 讓 COGS 很小，DIO 的絕對值意義有限，增量也可能是 HBM／新產線的在製品 [推論]。Samsung 6 月底存貨 ₩17.99 兆，半年增加 25.9%，這是全公司口徑（Herald 8/18 `[二手]`）。通路：**模組廠「需求弱、庫存高」**（TrendForce 10/7）；手機品牌第四季靠既有庫存生產 eMMC/UFS；PC OEM 用上半年囤的成品與通路庫存出貨（TrendForce 9/30）`[一手]` |
| 4 | 供給 capex／設備 | 已現 → 已現且加深 | **已現，capex 金額再加深；投產時點不是本季的新變化** | ↔ **混合**（capex 金額 ↓ 對多方不利；新增位元的時點沒有實質提前） | Micron FY26 capex $27.37B `[一手]`。FY27 FQ1 約 $11.5B、上半年約 $25B、下半年再增加，**這是本季真正的新變化**；全年 **>$50B** 是媒體外推，不是公司正式數字（Herald 9/30 `[二手]`）。Singapore HBM 廠 2027 年初、Idaho 一廠與台灣銅鑼 2027 年中投產 `[二手]`。⚠️ 審查指出這些時程 **2025 年就已公布，屬於補 8/19 的遺漏，不是本季的新變化**；而且 **Singapore 是 HBM 後段封裝廠，不增加 DRAM 晶圓位元**（本檔未獨立核對這兩點）。Micron 自己說 FY27 capex 的增量主要是「讓 2028 年底以後的潔淨室提早可用」的營建支出 `[二手]`，也就是說有意義的新增位元仍落在 2028 年以後。TrendForce：2027 伺服器 DRAM＋HBM 位元供給 +27%，新廠產能落在 2H27 `[一手 8/25]`。Samsung HBM 晶圓投片從每月約 18 萬片增加到約 25 萬片（2027）`[二手]`。SK hynix 傳洽租 Intel 俄亥俄廠（TrendForce News 9/16 標題 `[二手]`）。**Micron 公布 capex 上調後盤後股價下跌**（Herald 9/30 `[二手]`），市場開始懲罰擴產 |
| 5 | 中國供給 | 證據不足 → 已現且有量化時點 | **已現，時點略往後滑（HBM），但資金面變強** | →（持平，偏中性） | CXMT 7 月科創板 IPO，募資額說法不一（約 ¥295 億或約 ¥579 億，互相矛盾）`[二手]`。HBM3 良率約 25%、量產滑到 2027 `[二手]`。DDR5 良率沒有可信的新數字。**本格仍是八因子中證據品質最差的一格** |
| 6 | 需求 | 分層 → AI 端全數上修 | **AI 端名目值仍在上修；量的隱憂首次出現（有反證）；消費端更差** | ↓（品質轉差） | AI：2Q26 四家實際 capex 季增 27% `[一手 XBRL]`；TrendForce 估 CSP capex 2026 +98%、2027 再 +50% `[一手 8/25]`。**裂縫 1**：記憶體佔 CSP capex 從 47%（2026）升到 **68%（2027）**，同一份報告點名 CSP 可能「降低每套系統的記憶體容量」`[一手 8/25]`。**裂縫 2**：GPU／ASIC 廠評估 HBM 從 12-Hi 改 8-Hi，原因是「HBM 供給有限、系統成本快速上升」，TrendForce 明說「不是終端需求減弱」`[一手 9/29]`；8/4 另有「NVIDIA 為 Rubin Ultra 降低 HBM 配置」的標題 `[一手標題]`。**反證**：同一份 9/29 報告寫明 8-Hi 每 Gb 比 12-Hi 貴 10–20%，降配置「不太可能扭轉 HBM 大幅漲價的趨勢」；9/30 報告說 CPU 供給改善後，CSP 與伺服器 OEM 正在**增加**一般伺服器 RDIMM 的位元採購，以支援 agentic AI `[一手]`。消費端：筆電 2026 年 −9.4%，2027 年可能再衰退個位數低段到高段（TrendForce 9/4、10/8 `[一手]`）；手機 2026 年上修到 10.7 億支，**原因是提前採購**（9/8 `[一手]`），等於預支 2027 年的需求；Samsung DX 部門 3Q 虧損擴大到超過 ₩1 兆（Seoul Economic Daily 轉述 `[二手]`） |
| 7 | 賣方觀點 | 未現 → 「看多＝擁擠」 | **仍然擁擠；邊際上第一次出現下修** | ↓（邊際） | Bernstein：短缺延續到 2028（Webull 轉述 `[二手]`）。**但 Samsung 共識自 8 月底下修約 8%**，理由是漲幅放緩加上韓元走強；**SK hynix 3Q 營業利益共識約 ₩78 兆，Citi 從 76.7 下修到 74、DS 給 70** `[二手 9/15–9/29]` |
| 8 | 歷史對照 | 第 2.5 步 → 2.5–3 步，沿「週期延長」方向移動 | **約第 3 步 [推論]** | ↓（往後段移動） | 本輪同時出現：供應商附地板價的長約、capex 金額上調、客戶評估降規格、通路庫存偏高、DDR5／NAND wafer 現貨轉軟、hyperscaler 用股債融資擴 capex、賣方開始下修。**一階導數仍然是史上最強**：Micron 毛利率 86.8%；Samsung 營業利益 ₩107.4 兆，超出共識約 0.7–1.2%（Herald 引券商共識 ₩106.64 兆、Reuters 引 LSEG ₩106.1 兆 `[二手]`）。Micron FQ1 毛利率指引為 **GAAP 約 85.95%、non-GAAP 約 86.25%**，分別比 FQ4 的 86.8%／87.0% 低 0.85／0.75 個百分點 `[一手 8-K]`。二手報導稱管理層說「FQ1 是毛利率低點」，**這句話未經一手核對** |

### 八因子整體結論

**實體面仍未見頂**：因子 1、因子 2 的合約價半邊、因子 3 的原廠端仍然支撐。**跟 8/19 相比，8 格的方向如下：**

| 方向 | 格數 | 因子 |
|---|---|---|
| 轉空 | 3 | 3 庫存、6 需求、7 賣方 |
| 混合 | 2 | 2 價格、4 供給 |
| 偏多 | 1 | 1 長約 |
| 持平 | 1 | 5 中國 |
| 跟著其他格走 | 1 | 8 歷史對照，約第 3 步 [推論] |

**淨方向偏空，但幅度溫和，沒有任何一格的變化足以改變「未見頂」的判定。** 8/19 的「週期延長」論點靠的是供給的實體限制。本輪 Micron capex 金額上調，對這個支柱**略有壓力**；但有意義的新增晶圓位元仍落在 2028 年以後，**支柱大致成立**。

## 3. 這次重跑對現有持倉的實際意義

**前提**：依 `skills/serenity/holdings.md`（最後同步 2026-08-28；⚠️ 本次沒有讀 Google Sheet，持倉可能已變動），現有部位是 8271 宇瞻、2303 聯電、COHX、BE，**沒有任何記憶體原廠**。T1 處於休眠，**本輪結果不會產生任何減碼指令**。

### 3.1 對 8271 宇瞻（模組廠）

`holdings.md` 把 8271 定位為「漲價期是成本上升方，損益方向與原廠相反」。**本輪資料顯示這個定位不完整：**

- **TrendForce 自己的說法**（2026-09-22 `[一手]`）：Apacer 2025 年 DRAM 營收 +96%，原因是「**第二季就開始確保額外供給**」，所以能「**把 DRAM 漲價轉成更好的營運成果**」。換句話說，模組廠在上行期靠**低價庫存的庫存利益**賺錢，曝險不是單純的反向。
- **模組廠真正怕的是「轉折」**：在高成本庫存上，碰到現貨和通路價格走弱 [推論]。本輪剛好看到這個組合的前兆：合約價還在漲（進貨成本上升）、現貨持平或轉軟、NAND wafer 現貨 −9%、TrendForce 點名模組廠「需求弱、庫存高」。
- **8271 月營收**（FinMind `[一手資料源]`，單位 NT$ 百萬）：

| 月份 | 4 月 | 5 月 | 6 月 | 7 月 | 8 月 | 9 月 |
|---|---|---|---|---|---|---|
| 營收 | **3,739.8**（高點） | 3,022.8 | 2,913.6 | 2,791.2 | 2,789.3 | 3,001.4 |

  - **3Q26 合計 8,581.9 vs 2Q26 9,676.2，季減 −11.3%**。同一季上游一般型 DRAM 合約價 +13–18%，所以位元出貨量大概跌得更多 [推論]。
  - 9 月月增 +7.6%、年增 +158%，**還不能說趨勢已經轉壞**。
  - **3Q 毛利率未取得**（季報約 11 月公布），而存貨跌價損失會出現在毛利率，不會出現在營收。
- **供給面風險**：TrendForce 9/30 寫明原廠 2026 年每季都有履行對 PC OEM 與模組廠的約定量，但「**2027 年 PC DRAM 供給可能下降**」，因為產能持續移往伺服器 `[一手]`。模組廠拿貨可能變難。

**觀察結論**：T1 各條件對 8271 的意義不是「T1 觸發＝對 8271 有利」。如果 ① 觸發（合約價轉負），對 8271 的短期效果可能是**存貨跌價**，之後才會出現成本紓解 [推論]。8271 現行唯一適用的出場規則仍是 §0 規則 1（月收盤跌破年線），**本檔不改變這一點**。

### 3.2 作為 T6（AI capex 總否證）的前哨

T6 的定義是「任一 hyperscaler capex 指引下修」（exit-playbook §2）。**本輪 T6 未觸發**：MSFT 那一筆是會計變更，其他三家都上修或收窄區間。但有三個前哨值得記錄：

1. **capex 開始靠外部融資支應**：
   - Alphabet 2Q26 自由現金流 **−$5.86B**（營業現金流 $39.07B − capex $44.92B，Alphabet 8-K `[一手]`）。
   - Alphabet 6 月發行普通股＋強制可轉換特別股淨得 **$49.6B**、Q2 發債 $20.3B、8/10 再發 **$25B** 公司債，另設 $40B ATM `[一手]`。
   - Amazon 2Q26 營業現金流 $45.4B 對 PP&E 支出 $54.2B，相減約 **−$8.8B** `[一手 XBRL，差額為本檔自算]`。
   - 這和 ⑤（NVDA 自己當銀行）是同一件事的另一面：**AI capex 的資金來源從內部現金流轉向資本市場** [推論]。
2. **全年指引隱含下半年大幅加速**：
   - Alphabet 全年 $195–205B 減上半年 $80.6B，下半年每季要 $57–62B，比 Q2 的 $44.9B 高 28–39% [推論]。
   - Amazon 全年約 $220B 減上半年 $98.4B，下半年每季約 $61B（口徑可能不一致）[推論]。
   - **10 月底 3Q 實際值若明顯低於這個隱含節奏，會是 ④ 與 T6 的第一個實質訊號**。但依現行文字，年度指引在年底前無法被判定為「低於」（見 §5 Q2）。
3. **名目 capex 不再代表量**：記憶體佔 CSP capex 從 47% 升到 68%（TrendForce 8/25），GPU／ASIC 廠開始降低 HBM 配置。⇒ **T6 與 ④ 都看名目 capex，可能在位元需求已經轉弱時仍顯示綠燈** [推論]。這對現有四檔（全部是 AI capex 衍生品）影響最大。⚠️ 目前這是**機制上的盲點，還不是已發生的事**：TrendForce 9/30 寫的是 CSP 與 OEM 正在增加一般伺服器 RDIMM 的位元採購。

## 4. 我可能錯在哪

1. **數字大多是二手。** 一手的部分只有：TrendForce 新聞稿、Micron 8-K、SEC XBRL、Meta／Alphabet／MSFT 8-K、FinMind。Samsung 初步業績來自 TrendForce 轉述官方 guidance，因為 news.samsung.com 被 403。Micron 的 SCA 26 份、$32B、>75% 已鎖，全部是法說會的二手轉述，**沒有讀到逐字稿**。
2. **「售罄」可能是重複下單。** TrendForce 9/30 原文說 PC OEM 在終端需求偏弱下仍「積極採購，因為預期 2027 年供給偏緊」。這正是短缺期客戶超額下單、囤貨的典型說法。若是如此，③（售罄覆蓋期）會在週期反轉前一直顯示綠燈，然後一次崩掉 [推論]。③ 的設計本身沒有防重複下單的機制。
3. **T1 六條全部落後於股價。** 7/26 已指出記憶體股歷史上領先實體見頂 5–7 個月。本輪「0 條新觸發」不代表股價層安全。
4. **8271「反向」的定位可能從頭就錯**（見 §3.1）。若模組廠的實際曝險是「價格方向＋庫存週期」而不是「價格水準的反向」，那過去用「T1 不適用 8271」得到的安心感就沒有根據。
5. **因子 3 的 Micron 庫存上升可能被我過度解讀。** 增量可能是 HBM／新產線的在製品備料，不是賣不掉。沒有拆分資料，無法區分。
6. **CXMT（因子 5、條件 ⑥）的資料品質很差**，多數是匿名來源或過期數字。本格的「持平」判定信心很低。
7. **4Q26 合約價的比較基準有疑問。** 8/19 記錄的 +8–13% 沒有在該檔標明出處。本檔說「收斂速度比 8/19 認為的慢」是拿正式稿去比一個來源不明的數字。
8. **日期**：今天是 2026-10-13（環境日期），本檔不依賴任何檔名時戳。所有「下一個裁判日」都是預計日期，公司大多尚未確認。

## 5. 需要 Jake 裁決的問題（3 題）

1. **兩條門檻的詮釋要你定。**
   - **(a) ⑥ 的「DDR5 良率達標」要定一個數字和來源標準嗎？** 例如「≥80%，且有 2 個獨立來源、日期在 6 個月內」，或者乾脆刪掉 DDR5、只看「HBM 通過非中國客戶驗證」。不定的話，⑥ 會一直是「無法判定」，或被一筆 2024 年的舊數字誤觸發。
   - **(b) ⑤(b) 升級欄的「延遲」包不包括 OpenAI IPO 從 2026 延到 2027？** 照字面算，⑤ 現在就該升級。本檔沒有自行升級，理由是估值在上升、2026 IPO 從來不是正式承諾（見 §1 ⑤）。建議把「延遲」限定為「已宣布的募資輪延遲或縮水」，或者明說包含 IPO 延期。
2. **④ 的「連兩季低於前次指引」要怎麼量？** 各家給的是年度指引（MSFT 另給單季），年度數字在年底前無法判定「低於」。選項有三個：(a) 用「全年指引減已實現」推出的剩餘季度隱含節奏；(b) 只用 MSFT 的單季指引（FY27Q1 含融資租賃 >$50B）；(c) 另外加一個量的指標，修正「記憶體漲價墊高名目 capex」的盲點。
3. **8271 要不要加一組記憶體週期觀察項？** 例如 DRAM／NAND 現貨週報、TrendForce 模組廠庫存描述、8271 月營收連續季減。只寫進週報當背景，**不扣扳機、不取代規則 1**。理由是 §3.1 顯示 8271 對週期轉折的曝險不是 T1 所說的單純反向，而目前沒有任何東西在盯它。

## 6. 未取得資料清單

- TrendForce **1Q27** 合約價預估（DRAM／HBM／伺服器 DRAM／NAND）。尚未發布 [推論]
- **伺服器 DRAM 4Q26 單獨的 QoQ %**（9/30 新聞稿只寫「供不應求、部分供應商因 LTA 漲幅落後」）
- **DDR5 現貨的具體價格序列**（TrendForce 週報只給 DDR4 1Gx8 基準，dramexchange.com 被 403）
- **SK hynix 3Q26 實際業績**（約 10/28）、**Samsung 3Q26 分部門業績**（10/29）
- **hyperscaler 3Q26 實際 capex**（10 月底）。Amazon 全年指引 $220B 與 MSFT FY27 全年數字未經一手核對。8/19 檔記載的「Meta 上修到 $135–145B」與一手 8-K 的 **$130–145B** 不符，**8/19 的數字有誤**
- **Samsung／SK hynix 原廠存貨直接讀數**（只有 KB 證券估計和 Samsung 全公司口徑存貨）
- **Micron FY27 capex 正式全年數字**（只有 FQ1 約 $11.5B、上半年約 $25B 的二手轉述）與法說會逐字稿
- **CXMT DDR5 良率的 2026 年可信數字**、任何 HBM 客戶驗證通過的確認
- **NVDA／OpenAI 9 月以後新的擔保或融資安排**（搜尋沒有結果，不等於沒有）
- **8271 3Q26 毛利率與存貨**（季報約 11 月）

## 7. 下一輪

- **小重跑（建議 2026-10-30 之後）**：只更新 ④（四家 3Q 實際 capex 對照隱含節奏）、⑤(b)（OpenAI 過橋輪進度）、因子 3（Samsung／SKH 3Q 存貨）、因子 6。
- **NVDA Q3 FY27（約 11/18）**：⑤ 的否證與升級表見 8/28 檔 §6.4。
- **下一次完整季度重跑：2027-01-15 前**，屆時應該已有 TrendForce 1Q27 合約價。

## 來源

**一手（直接讀取原文）**
- [TrendForce 2026-09-30｜AI Server Demand Sustains Memory Contract Price Increases in 4Q26](https://www.trendforce.com/presscenter/news/20260930-13258.html)
- [TrendForce 2026-09-29｜HBM 2027 Blended ASP +121% YoY](https://www.trendforce.com/presscenter/news/20260929-13255.html)
- [TrendForce 2026-09-22｜DRAM Module Revenue 2025（含 Apacer）](https://www.trendforce.com/presscenter/news/20260922-13249.html)
- [TrendForce 2026-09-07｜DRAM Industry Revenue 2Q26](https://www.trendforce.com/presscenter/news/20260907-13219.html)
- [TrendForce 2026-08-25｜DRAM and NAND to Account for 68% of CSP CapEx in 2027](https://www.trendforce.com/presscenter/news/20260825-13198.html)
- [TrendForce 2026-10-08｜Rising Costs Threaten Notebook Demand in 2027](https://www.trendforce.com/presscenter/news/20261008-13264.html)
- [TrendForce 現貨週報 2026-10-07](https://www.trendforce.com/news/2026/10/07/insights-memory-spot-price-update-dram-spot-largely-sideways-as-holidays-month-end-effects-weigh/)・[2026-09-16](https://www.trendforce.com/news/2026/09/16/insights-memory-spot-price-update-dram-spot-cools-as-ddr5-inquiries-slow-2gx8-ddr4-prices-retreat/)・[2026-09-02](https://www.trendforce.com/news/2026/09/02/insights-memory-spot-price-update-ddr5-ddr4-demand-weakens-but-firm-supplier-quotes-support-elevated-prices/)
- [TrendForce News 2026-10-08｜Samsung 3Q26 OP ₩107.4T（轉述 Samsung guidance／Reuters／Hankyung）](https://www.trendforce.com/news/2026/10/08/news-samsung-sees-3q26-operating-profit-soaring-783-to-record-krw-107-4-trillion-on-hbm4-memory-price-gains/)
- [Micron FQ4 FY26 新聞稿（SEC 8-K Ex.99.1，2026-09-30）](https://www.sec.gov/Archives/edgar/data/723125/000072312526000018/a2026q4ex991-pressrelease.htm)
- [Meta 2Q26 新聞稿（SEC 8-K Ex.99.1，2026-07-29）](https://www.sec.gov/Archives/edgar/data/1326801/000162828026050596/meta-06302026xexhibit991.htm)
- [Alphabet 2Q26 新聞稿（SEC 8-K Ex.99.1，2026-07-22）](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000066/googexhibit991q22026.htm)・[Alphabet $25B 公司債 8-K（2026-08-10）](https://www.sec.gov/Archives/edgar/data/1652044/000119312526342390/d171253d8k.htm)
- [Microsoft FY27 Q1 調整後展望（SEC 8-K Ex.99.1，2026-09-02）](https://www.sec.gov/Archives/edgar/data/789019/000119312526380280/d291965dex991.htm)
- SEC XBRL companyconcept API（PaymentsToAcquirePropertyPlantAndEquipment／PaymentsToAcquireProductiveAssets／NetCashProvidedByUsedInOperatingActivities；MSFT、GOOGL、AMZN、META）
- FinMind TaiwanStockMonthRevenue（8271，2025-05 至 2026-09）

**二手（媒體轉述，未經原文核對）**
- [Korea Times 2026-10-08｜Samsung Q3 OP](https://www.koreatimes.co.kr/business/companies/20261008/samsung-electronics-estimates-803-bil-in-q3-operating-profit)
- [Benzinga 2026-10｜Micron call](https://www.benzinga.com/markets/earnings/26/10/62098162)・[Herald 2026-09-30｜Micron capex](https://biz.heraldcorp.com/article/10890090)・[247wallst｜Micron raises capital spending](https://247wallst.com/cards/mehrotra-is-guiding-for-fiscal-2027-to-top-a-record-fiscal-2-mu-quote-01m3sywprz9h5tjfcqmppzx7vw)
- [Khaleej Times｜Samsung sees chip shortage extending to 2028](https://www.khaleejtimes.com/business/tech/samsung-sees-chip-shortage-extending-to-2028-signs-long-term-supply-deals)
- [TweakTown／DigiTimes｜2027 DRAM/HBM capacity booked](https://www.tweaktown.com/news/113004/memory-capacity-for-all-of-2027-has-reportedly-been-booked-and-sold-with-no-more-dram-or-hbm-available/index.html)
- [KuCoin 轉述 DigiTimes｜Samsung/SKH inventories <10 days](https://www.kucoin.com/news/flash/samsung-and-sk-hynix-memory-chip-inventories-drop-below-10-days-supply)・[Herald｜inventories +20–30%](https://mbiz.heraldcorp.com/article/10844218)
- [Xenospectrum｜CXMT HBM3 yield](https://xenospectrum.com/en/cxmt-hbm3-yield-stacking/)・[TechPowerUp｜CXMT DDR5 80% (Citi)](https://techpowerup.com/news-tags/17%20nm)・[aiweekly｜CXMT IPO](https://aiweekly.co/alerts/cxmt-prices-855b-shanghai-star-ipo-biggest-since-smic-2020)
- [CFO Dive｜Microsoft holds line on AI spending](https://www.cfodive.com/news/microsoft-holds-line-ai-spending-plans/826648/)・[TIKR｜MSFT capex accounting](https://www.tikr.com/blog/did-microsoft-really-cut-its-capex-heres-the-accounting-move-behind-the-headline)
- [Platformonomics｜Q2 2026 capex scoreboard](https://platformonomics.com/2026/07/follow-the-capex-q2-2026-scoreboard/)（403，內容取自搜尋摘要）
- [The Next Web 2026-09-30｜OpenAI $30B at $1.4T](https://thenextweb.com/news/openai-valuation-1-4tn-30bn-round-revenue-70bn)・[Nairametrics 2026-09-30](https://nairametrics.com/2026/09/30/openai-seeks-30-billion-funding-at-1-4-trillion-valuation/)
- [SK hynix 3Q 共識（stockhub／JoongAng 等）](https://www.koreajoongangdaily.com/business/brokerages-split-on-targets-for-sk-hynix-shares-after-chipmaker-misses-q2-market-consensus/12799468)
- [Guru3D｜Samsung: HBM ~30% of DRAM wafer capacity 2027](https://www.guru3d.com/story/samsung-expects-hbm-to-consume-nearly-of-dram-wafer-capacity-in-2027/)

## Update Log
- 2026-10-13 v1.0：2026 Q4 輪季度重跑（準時，到期日 10/15）。T1 v2 六條：①②③④ 未觸發、⑤ 維持觸發、⑥ 無法判定（門檻無數字）。八因子：實體面仍未見頂，但 5 格往空方移動、0 格往多方移動。新發現：客戶降低記憶體配置、記憶體佔 CSP capex 68% 造成的名目盲點、Alphabet 自由現金流轉負、8271 營收 3Q 季減 11%，以及「模組廠＝反向」的定位不完整。三題待 Jake 裁決。
- 2026-10-13 v1.1：依對抗審查修正，**T1 結論不變**（①②③④ 未觸發、⑥ 無法判定、無新觸發）。修正內容：
  - ⑤(b)：照 §6.4 字面「延遲」已達升級門檻，列出不採字面的理由，併入 §5 Q1(b) 交裁決。
  - 摘要第 2 點：改為「DRAM 合約價收斂、NAND 加速；現貨只有 DDR5 與 NAND wafer 轉弱」。
  - 八因子方向：由「5 轉空、0 轉多」改為「3 轉空（3、6、7）、2 混合（2、4）、1 偏多（1）、1 持平（5）」。因子 4 的投產時程屬補 8/19 遺漏，「削弱支柱」降調。
  - 補反方證據：RDIMM 位元採購增加、8-Hi 每 Gb 較貴、LTA 價格上限（一手）。
  - 補 Samsung 對共識的超出幅度、Micron 毛利率指引的 GAAP／non-GAAP 區分。
  - ② 改為推定未觸發；③ 註明缺 SK hynix 的直接證據。
