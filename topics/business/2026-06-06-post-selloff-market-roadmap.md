---
title: 2026-06-05 美股大跌後市場路徑研判 — ACT 系統解讀 + 歷史對標 + 底部加倉劇本（美/台）
url: local
source: Claude Research Session (Jake × Claude) — 延續 KIWI / Redefine Fund
date_added: 2026-06-06
last_updated: 2026-06-06
topic: business
tags: [market-analysis, act-system, avi, cpi, tsi, selloff, semiconductor, fed-warsh, taiex, sp500, nasdaq, midterm, spacex-ipo, triple-witching, position-sizing, backtest, scenario-analysis]
version: 1.0
related: [./2026-05-29-serenity-chokepoint-three-market-scan.md, ./2026-06-03-redefine-fund-project.md, ../technology/2026-05-17-session-master-handoff.md, ./2026-04-20-avi-v4-market-risk-index.md]
---

> **任務**：用 ACT 系統（AVI 估值 / CPI 崩盤概率 / TSI 科技壓力）+ 上網資料，研判 2026-06-05 美股大跌後的可能走向；找歷史對標；分美/台兩市；檢驗底部時點與加倉勝率劇本，供倉位決策參考。
>
> **環境註記**：本次 session 在雲端容器執行，網路 allowlist **封鎖 yfinance / FRED**，ACT 三套程式**無法跑即時數據**。下方 ACT 讀數為**用已驗證的真實市場數據 + 各指標定義「人工重建」的估計值**，請在 Mac 上跑 `run_tsi.py / run_cpi.py / run_monthly.py --v5` 校正。所有市場數字來自 2026-06-05~06-06 網路新聞（出處見文末）。

---

## 0. 一頁速覽（TL;DR）

| 項目 | 研判 |
|---|---|
| **6/5 事件性質** | 從 VIX 16 的極度自滿狀態，被「**強就業 → 殖利率噴 → 升息恐慌**」+「**半導體估值鬆動**」雙擊。SOX 單日最大跌幅自 2020/3 以來，蒸發 >$1T。**像 2018/2 的「好消息變壞消息」利率衝擊，不像 2008/2000 的系統性崩盤起點。** |
| **最佳歷史對標** | **2018/2 Volmageddon**（精準）：熱薪資 → 殖利率噴 → 一週內 −10% → 2/8~2/9 見底 → 後 6 月 S&P +11% / Nasdaq +19%。次要對標：1999–2000（AI 泡沫 + Fed 轉鷹的空頭劇本）、2018Q4（鷹派過頭的急殺）、1994（升息震盪但無熊）。 |
| **ACT 重建讀數（估）** | **AVI ≈ 6.7–7.0 🟡 偏貴**（非狂熱極端）｜**CPI ≈ 46–52 ⚠️ 謹慎**（提防非恐慌）｜**TSI ≈ 60–70 🔴 壓力**（最該看的表，正在閃） |
| **美股基準情境（55%）** | 「2018/2 重演」：中段事件密集區（6/11–12 SpaceX IPO 抽水、6/17 FOMC/Warsh、6/18 三巫）震盪/再探，自高點總回檔 **6–12%**，6–7 月打底，再回升。期中年季節性 → 夏秋偏弱，11 月後轉強。 |
| **美股空頭情境（25%）** | 「1999–2000 / 晚週期」：這是 AI 泡沫頂 + Fed 重啟升息的第一道裂縫。觸發＝**信用利差爆開 + 殖利率失序（30Y 遠破 5%）+ 廣度崩**。回檔 15–25%（期中年均 −17.5%）。 |
| **美股噴出情境（20%）** | 殖利率穩、Warsh 6/17 偏鴿（AI 生產力論）、SpaceX 上市點火、急殺被秒買 → Q3 創新高。 |
| **台股** | TAIEX 對美科技 beta ~1.2–1.5x，TSMC 占權重 44% = 槓桿版 SOX。但外資 6/4 淨買超 NT$670 億（史上第 6 大）→ 結構買盤強。**回檔幅度更大但更該被買**，進場點同步美科技止穩。**TWD 升值是最大內生風險**（每升 1% 砍 TSMC 毛利 0.4–1.5pp）。 |
| **倉位結論** | AVI 6.7🟡 = **「risk-off 彈性」regime，不是 all-in**。現在跌幅僅自高點 −3%，太淺、不是「那個底」。**留乾火藥、預掛分批加碼價位、把 Serenity 清單備好等秋季期中季節性洗盤。** |

---

## 1. 6/5 究竟發生什麼（事實層）

**指數**（6/5 收盤）：
- Nasdaq 綜合 **−4.18% → 25,709**（自 2025/4 以來最慘單日），終結 9 週連漲
- S&P 500 **−2.64% → 7,383**（前一日 6/4 收 7,584）
- Dow **−1.35% → 50,867**（6/4 才創 ATH）
- **費城半導體 SOX：單日最大跌幅自 2020/3 以來**，蒸發 >$1 兆市值

**雙重觸發**：
1. **半導體估值鬆動**：Broadcom 財報未上調 AI 晶片展望 → 週四先殺，週五 Broadcom −7~12%、Marvell −16%、Micron −13%、AMD/Intel −11%。
2. **強就業 → 升息恐慌**：5 月非農 **+172k（預期僅 ~85k，翻倍）**、失業率 4.3% 持穩、3 月上修至 214k。→ **10Y 殖利率破 4.5%、30Y 破 5%**；CME FedWatch 年內升息機率跳到 ~57%（12 月近 70%）。

**關鍵背景**：跌之前 **VIX 僅 16（6/1）**、30 日已實現波動率才 10.3 = **極度自滿**。3 月曾因伊朗衝突/油價衝擊 VIX 破 30、S&P 探 6,343，之後一路反彈創高。**所以這是「自滿 + 創高 → 被利率與晶片雙擊」的急殺，技術上 S&P 仍在 200DMA(6,853) 之上甚遠，距高點僅約 −3%——還沒到「崩盤」等級。**

---

## 2. ACT 系統解讀（人工重建，待 Mac 校正）

> 方法：用各指標真實輸入（VIX、10Y/30Y、SOX 動能、Mag7 估值、信用訊號）對照系統定義反推。回測基準來自 handoff：CPI 四大崩盤觸發區 39–51、領先 23–42 天；TSI 過去一年 7/7 命中、1–14 天預警。

### AVI（估值，0–10，越高越貴）≈ **6.7–7.0 🟡 偏貴**
- 6/03 fund 文件已記錄 **AVI 6.73🟡**；之後市場再創高才回落，估值未實質便宜。
- Mag7 ~28x 前瞻（**約 dotcom 一半**，有真實獲利：NVDA TTM 獲利 $99B、淨利率 53%）；但 **AI 相關 P/S「逼近科技泡沫水準」**（Morningstar）、集中度近 dotcom 僅見。
- 結論：**偏貴但非 9–10 的狂熱極端**。給「該有下檔保護彈性」的訊號，不是「立刻清倉」。

### CPI（崩盤概率，0–100，越高越危）≈ **46–52 ⚠️ 謹慎（非恐慌）**
- 跌前（VIX16、9 週連漲）CPI 應在低中區（~30–40）。
- 6/5 注入壓力：SOX 自 2020 最大單日、殖利率噴、Fed 轉鷹、AI 信用個案緊張（Oracle 10Y CDS 飆到 ~180，與羅馬尼亞國家同級）。→ CPI 跳到 **中高 40s ~ 低 50s**。
- 對照回測（崩盤觸發 39–51）：**這個讀數＝「警戒、但還不是崩盤確認」**。要看到 **60+** 才是系統性風險。勞動強、無衰退訊號、信用「整體」尚未爆 → 維持「謹慎」而非「逃命」。

### TSI（科技壓力，0–100，越高越壓力）≈ **60–70 🔴 壓力（正在閃）**
- TSI 9 指標含 **10Y + 30Y 國債**——兩者同時噴，加上 SOX 自 2020 最大單日、Broadcom/Marvell/Micron 重挫 → **TSI 是三表中最直接相關、也最該看的，目前明確在 STRESSED 區。**
- handoff 記錄 TSI 5/12 起連 4 天 CAUTIOUS 提前 3 天預警殖利率衝擊——**這次很可能又是 TSI 先亮**。請務必在 Mac 跑 `run_tsi.py --history 252` 確認趨勢。

> **三表合讀**：TSI🔴 領先警示「科技/利率壓力」已到；CPI⚠️ 說「謹慎、非崩盤」；AVI🟡 說「貴、要留彈性」。= **典型的「高估值 + 利率衝擊的急殺洗盤」signature，不是「信用崩 + 衰退」的熊市起點 signature**。後者要等 CPI 破 60 + 信用利差爆。

---

## 3. 歷史對標：這種「大跌 + 經濟數據 + 背景」過去發生過嗎？

**有，而且非常像 2018 年 2 月。** 把四個對標按「相似度」排：

### 🥇 最像：2018/2 Volmageddon（「好消息變壞消息」的利率衝擊）
- **觸發完全同構**：1 月就業熱、**薪資成長超預期 → 通膨/升息恐慌 → 殖利率噴 → 股債正相關斷裂 → 股災**。
- **路徑**：2/2 開殺 → **2/5 VIX 盤中 16→38（史上最大單日 +115%）** → 2/8~2/9 見底，主要指數一度 −10% 進修正。
- **結局**：自 2/8 底起 **6 個月 S&P +11%、Nasdaq +19%**。**不是熊市，是急洗盤後續創高。**
- **差異**：2018/2 還疊加 short-VIX ETF（XIV）爆倉的技術踩踏；這次的「技術放大器」換成 **SpaceX $75B 抽水 + 6/18 三巫到期**（見 §5）。

### 🥈 空頭對標：1999–2000（AI/科技泡沫頂 + Fed 轉鷹）
- Fed 1999/6 起升息 → **首次升息後 9 個月內**進入熊市 + 衰退；Fed 事後從 6.5% 一路砍到 1%。
- **這次的對映風險**：若 6/5 是「AI 泡沫頂 + Fed 從『以為要降』反手升息」的第一道裂縫，劇本就往這走。**關鍵差別**：當前 Mag7 28x（dotcom 一半）、有真現金流、capex 多為自有現金 → 泡沫「品質」比 2000 好，但**集中度與 AI 變現落差（$400B+ capex vs 企業端變現有限）是真風險**。

### 🥉 急殺對標：2018Q4（Fed 鷹派過頭）
- Fed 升到 2.5%、鮑爾「離中性還遠」鷹派發言 → 2018Q4 −20% 急殺 → 2019 轉降息三碼、強彈。
- **對映**：若 Warsh 6/17 確認鷹派轉向（移除寬鬆偏好、暗示升息），市場可能複製 Q4-style 的「政策恐慌急殺」，但只要經濟不衰退，隔年通常修復。

### 4️⃣ 良性對標：1994（升息震盪、軟著陸、無熊）
- Fed 3%→6% 七次升息、債市大屠殺，**股市震盪整年但無熊**，1995 軟著陸後反手降 75bp。
- **對映**：若這次升息恐慌「雷聲大雨點小」（通膨回落、Fed 不真升），就是 1994 式的「年中震盪、無熊」。

> **統計錨**：過去五個升息循環，**首次升息到熊市起點平均 3.5 年**，一年內只 1 次熊、0 次衰退。**單看「升息恐慌」本身，歷史上鮮少立刻變成熊市。** 這支持基準情境（震盪洗盤後修復），把熊市當需被「信用 + 衰退」確認的尾部風險。

---

## 4. 美股：趨勢、情境、要看的指標

### 4.1 三情境（機率為主觀後驗）

**🟢 基準｜2018/2 重演（55%）**
- 經濟強（172k、4.3%）= 無衰退；Mag7 有真獲利、估值非極端；信用整體未爆；外資/散戶 buy-the-dip 慣性仍在。
- **路徑**：穿越 6 月事件密集區時震盪/再探（見 §5），自高點總回檔 **6–12%**（S&P 約 6,950–7,150 一帶找支撐，對應 50DMA 7,140 / 前低結構），**6–7 月完成打底**，之後回升。期中年季節性 → 夏秋（9–10 月）仍有第二隻腳風險，**11 月後是四年週期最強的 6 個月**。

**🔴 空頭｜1999–2000 晚週期（25%）**
- 若殖利率持續失序（10Y 奔 5%、30Y 遠破 5%、期限溢價跳升）→ 壓垮最高倍數 AI/長存續股；AI capex 變現失望 + Oracle 式信用緊張擴散；集中度反轉。
- **回檔 15–25%**（剛好對上期中年均 −17.5% 回撤）。**這條路要被「信用利差爆 + 廣度崩 + CPI 破 60」確認才成立。**

**🟦 噴出｜Melt-up（20%）**
- 殖利率穩、Warsh 6/17 偏鴿（重申「AI 生產力 → 利率可更低」）、SpaceX 上市成功點火風險偏好、急殺被秒買（複製 9 週連漲慣性）→ Q3 創新高。

### 4.2 要盯的儀表板（依重要性）
1. **10Y / 30Y 殖利率**＝唯一最大驅動。**10Y >4.5%、尤其 30Y >5% 是痛點門檻。** 失序上行（30Y 遠破 5%、期限溢價跳）＝偏空；回穩/回落＝解除警報。
2. **Fed 路徑 / Warsh 6/17 首場 presser**：確認鷹派轉向（移除寬鬆偏好、暗示升息）vs 偏鴿（AI 生產力論）。FedWatch：12 月升息機率 ~57–70%。
3. **通膨數據（CPI/PCE）**：再加速 → 升息成真 → 偏空；回落 → 1994/解除。
4. **信用利差（IG/HY + AI 個案）**：Oracle CDS、hyperscaler 發債利差。**爆開＝空頭觸發鍵。**
5. **SOX / 半導體（＝TSI）**：賣壓止住 or 級聯？Broadcom/NVDA/Marvell 能否止穩。
6. **市場廣度**：%>200DMA、騰落線。先前很窄（靠 Mag7）。**廣度崩＝確認熊。** 反之出現 **90% 上漲日 / breadth thrust** ＝強力做多訊號。
7. **VIX 期限結構**：VIX 自 16 跳升；**backwardation（近月>遠月）= 恐慌/投降**，歷史上近 30–40 反而是逆勢買點。
8. **SpaceX IPO 吸收度（6/11–12）**：$75B 抽水是否壓 Nasdaq，或被順利吸收。
9. **AI capex / 變現**：財報對 ROI 的說法（$500–725B 2026 capex vs 企業端變現）。

---

## 5. 6 月事件甘特圖（為何「中段」最關鍵）

```
6/05(五) 已發生：強就業+晶片殺，Nasdaq −4.18%，VIX 16→跳升
6/11(四) SpaceX IPO 定價（SPCX）
6/12(五) SpaceX Nasdaq 掛牌 ── 募 ≤$75B、估值 ≥$1.8T（94x 營收）＝史上最大 IPO 的 2 倍
          ⚠️ 巨額抽水 + 指數納入風險，可能再抽 Nasdaq 流動性
6/17(三) FOMC 決議 + Warsh 上任首場記者會 ── 鷹/鴿定調全年（FedWatch:6 月按兵 >80%）
6/18(四) 三巫到期（因 6/19 Juneteenth 提前一天）── 期權/期貨/期指同到期，放大波動
─────────────────────────────────────────────
11/03    美國期中選舉 ── 期中年均 −17.5% 回撤；選後 6 月(11→4 月)四年週期最強(+14%)，選後一年 +15.4%
```

**解讀**：6/11–18 是「**IPO 抽水 → 央行定調 → 三巫放大波動**」三連擊，**最可能是這次回檔的「測試/再探底」窗口**。基準情境下，這週的二次探底若伴隨 VIX 衝高 + 200DMA 守住，往往是較好的分批進場點。期中年季節性提醒：**真正的高勝率大底，歷史上更常落在 9–10 月**，不是現在。

---

## 6. 底部時點 + 加倉勝率劇本（回測邏輯）

> ACT 系統的定位：**CPI/TSI 是「領先警示」**（CPI 領先崩盤 23–42 天），**不是抓底工具**。抓底要用「投降 + 廣度 + 價格收復」三類確認訊號。

### 6.1 高勝率「加倉觸發」訊號（依歷史）
| 訊號 | 內容 | 歷史依據 |
|---|---|---|
| **A. VIX 投降後回落** | VIX 衝 >30–35 且 backwardation，**首次收回 10 日線下** | 2018/2 VIX 峰 37 後崩＝底。**買在恐懼見頂「並反轉」，不是還在升時** |
| **B. 廣度推力** | 出現 **90% 成交量上漲日**，或 Zweig breadth thrust（10 日騰落急升） | 洗盤後 breadth thrust 的前瞻勝率歷史極高 |
| **C. 價格收復** | S&P **重新站回 50DMA(7,140)**，或在 **200DMA(6,853) 回測守住** | 200DMA＝多空線；回測不破＝加碼 |
| **D. 時間窗** | 期中年大底常群聚 **9–10 月**；選後 11→4 月最強 | 四年週期季節性 |

### 6.2 分批加碼地圖（綁回撤深度 × 指標確認，不要一次全壓）
- **第 1 批（現在/小）**：僅在「目前持股偏低」才動。**現在自高點僅 −3%，太淺、不是「那個底」。優先留乾火藥。**
- **第 2 批（自高點 −8~−10% + VIX>28 + 200DMA 回測守住 + TSI 由壓力區回落）**：**有意義地加。** 對應 S&P ~6,850–7,000。
- **第 3 批（−15%+ + 投降式廣度(90% 上漲日) + 信用利差未爆）**：**重壓。** 對應期中年均回撤滿足區。
- **🚫 反向鎖**：若**信用利差爆開 / 出現衰退訊號 / CPI 破 60** → **不要往下攤平**，那是 1999–2000 / 2008 路；等 Fed 政策轉向（降息訊號）再進。
- **節奏綁 ACT**：**TSI 由 STRESSED 回落、CPI 觸頂回落、AVI 變便宜** 三者轉向時逐批投放。

### 6.3 「怎麼加」具體建議
- **工具**：指數層用 SPY/QQQ 或台股 0050 控總曝險；alpha 層用 **Serenity 卡脖子清單**（高 beta 小型股跌最兇＝最佳進場，前提是 macro 守住）。
- **比例**：把「為這次回檔準備的乾火藥」切 **3 份（如 30% / 40% / 30%）**，分別對應第 1/2/3 批條件，**條件不到不投**。
- **吃自己的狗糧**：fund 文件已自承 AVI 偏高需「risk-off 彈性」——**現在的紀律是『穿越 6 月事件區先保留現金/避險緩衝，預掛價位等秋季季節性洗盤』**，而不是追。

---

## 7. 台股：趨勢、情境、指標

### 7.1 現況
- **TAIEX 創高 46,459（首破 46,000）後回 45,677（週四 −1.7%）**，跟跌美股 + 中東升溫。
- **TSMC 占權重 44%** → **TAIEX ≈ 槓桿版 SOX/AI**。SOX 自 2020 最大單日 → 台股高度連動暴露。
- 但 **外資 6/4 淨買超 NT$670 億（史上第 6 大）** → **結構買盤強、跌被買**。
- TSMC 基本面：2026 美元營收 +30%+、AI 晶片供給缺口「持續數年」、capex $52–56B。

### 7.2 台股三情境
- **🟢 基準**：對美科技下行 beta ~1.2–1.5x。美科技修正 10% → TAIEX 12–18% 區間波動，但**外資淨買 + TSMC 壟斷故事（30%+ 成長）墊高 → 結構性可買**。進場點**同步美科技止穩**，不要早。
- **🔴 空頭**：若美走 1999–2000，TAIEX 因高權重/高 beta **回檔可能更深（−20%+）**，但通常也是 AI 供應鏈最深的折價窗（PLAB 式錯殺 + macro 洗盤＝理想長線進場）。
- **🟦 噴出**：美科技回穩 + TWD 不續升 → TAIEX 隨 SOX 再創高。

### 7.3 台股專屬風險/指標
1. **TWD 升值（最大內生風險）**：政策壓在弱方（年底 ~31）拚出口，但結構性順差（每季 ~$150B、經常帳衝 GDP 20%）= 長線升值壓力。**每升 1% 砍 TSMC/UMC/ASE 毛利 0.4–1.5pp。** 盯 USD/TWD。
2. **外資流向**：淨買→淨賣的轉折＝台股最靈敏的領先訊號（現為強力淨買）。
3. **政治**：2026 底地方選舉，KMT 動能領先（2025/7 大罷免失敗）；兩岸「管控/北京有耐心」、近期溫度可控但持續灰帶施壓。**near-term 政治風險低於市場風險。**
4. **TSMC ADR (TSM) vs 台積電本尊溢價/折價**＝美台情緒橋樑，可當台股開盤領先參考。

---

## 8. 倉位行動清單（給 Jake / Redefine 預備）

1. **現在（6/6）**：**不追、不恐慌。** 跌幅僅自高點 −3%，TSI🔴 已警示但 CPI⚠️ 未確認系統性風險。**保留現金/避險緩衝穿越 6/11–18 事件區。**
2. **預掛分批價位**（§6.2）：S&P ~6,850–7,000（第 2 批）、−15%+（第 3 批）；台股對應 0050 與 Serenity 清單。
3. **每日盯 4 個數**：①10Y/30Y 殖利率 ②信用利差(含 Oracle CDS) ③VIX 與期限結構 ④外資台股買賣超。
4. **6/17 Warsh 定調**為最大轉折事件：鷹（移除寬鬆偏好/暗示升息）→ 偏 §4.1 空頭機率上修；鴿（AI 生產力論）→ 偏噴出。
5. **Mac 上跑 ACT 三表校正本文估計**：`run_tsi.py --history 252`、`run_cpi.py`、`run_monthly.py --v5`，把真實讀數回填本檔 Update Log。
6. **季節性備忘**：高勝率大底歷史更常在 **9–10 月**；選後 11→4 月最強。**把最大子彈留給秋季洗盤，而非 6 月第一腳。**

---

## 9. 重要不確定性 / 本研判可能錯在哪
- ACT 讀數是**人工重建**（環境封鎖即時數據），真實 CPI/TSI 可能更高或更低 → **以 Mac 實跑為準**。
- 「2018/2 重演」假設**信用不爆 + 經濟不衰退**；若 Oracle 式 AI 信用緊張擴散成系統性，基準情境失效、轉 §4.1 空頭。
- Warsh 政策路徑高度不確定（市場對其鴿/鷹分歧為「Fed 史上最分裂任命」54-45）。
- SpaceX $75B 抽水對流動性的實際衝擊難量化，可能比預期大（指數納入 + 巨額認購）。
- 期中年 −17.5% 是「平均」，分布很寬；2026 華爾街共識反而偏多（S&P 2027/1 目標 8,085）。

---

## 來源（2026-06-05 ~ 06-06 擷取）
- [TheStreet — Nasdaq falls 4%, $1T wiped (6/5)](https://www.thestreet.com/stock-market-today/stock-market-today-dow-jones-sp-500-nasdaq-updates-june-05-2026)
- [CNBC — Nasdaq worst day since Apr 2025, chip flight](https://www.cnbc.com/2026/06/04/stock-market-today-live-updates.html)
- [CNN Business — worst day of year, Fed rate-hike odds rise](https://www.cnn.com/2026/06/05/markets/stock-market-sell-off-fed)
- [SundayGuardian — strong jobs fuels Fed rate-hike fears](https://sundayguardianlive.com/business/why-is-the-us-stock-market-down-today-dow-nasdaq-sp-500-tumble-as-strong-jobs-data-fuels-fed-rate-hike-fears-chip-stocks-sink-what-investors-should-watch-201824/)
- [Reuters/US News — hot jobs, rising rates hit tech](https://money.usnews.com/investing/news/articles/2026-06-05/hot-jobs-report-rising-rates-send-wall-streets-tech-favorites-sprawling)
- [Chase — Kevin Warsh new Fed Chair, what it means](https://www.chase.com/personal/investments/learning-and-insights/article/kevin-warsh-is-the-new-chair-of-the-federal-reserve)
- [TradingKey — June FOMC hawkish hike preview](https://www.tradingkey.com/analysis/economic/central-banks/261924394-fed-fomc-kevin-warsh-hawkish-shift-inflation-cpi-treasury-yields-rate-hike-pricing-labor-resilience-policy-pivot-tradingkey)
- [Yahoo — Warsh sworn in, inflation worries / rate-hike odds](https://finance.yahoo.com/economy/policy/article/kevin-warsh-confirmed-new-fed-chair-as-inflation-kicks-higher-complicating-the-central-banks-path-164303609.html)
- [CNBC 2018 — correction two weeks later (Feb-2018 analog)](https://www.cnbc.com/2018/02/16/the-stock-market-correction-two-weeks-later.html)
- [Swan — Volmageddon Feb 2018](https://www.swanglobalinvestments.com/advisor/tale-of-two-volatilities-part2-volmageddon/)
- [Northwestern Mutual — markets after Fed hikes (1994/1999/2018)](https://www.northwesternmutual.com/life-and-money/the-fed-is-raising-rates-heres-how-markets-have-performed-in-the-past-0/)
- [Ameriprise — midterm election year market impacts 2026](https://www.ameriprise.com/financial-news-research/insights/2026-midterm-election-market-impacts)
- [Capital Group — how midterms affect markets (5 charts)](https://www.capitalgroup.com/pcs/insights/articles/midterm-elections-markets-5-charts-2026.html)
- [Capital.com — SpaceX IPO targets June 2026](https://capital.com/en-int/learn/ipo/spacex-ipo)
- [CNBC — SpaceX IPO live (record size)](https://www.cnbc.com/2026/05/20/spacex-ipo-live-updates.html)
- [OptionAlpha — Triple Witching dates 2026](https://optionalpha.com/learn/triple-witching)
- [Yahoo — Mag7 capex to $725B 2026](https://finance.yahoo.com/markets/article/magnificent-7-earnings-rush-reveals-ai-spending-surge-with-hyperscaler-capex-set-to-reach-725-billion-in-2026-224901707.html)
- [Fidelity — Is AI a bubble? 5 signs](https://www.fidelity.com/learning-center/trading-investing/ai-bubble)
- [Focus Taiwan — TAIEX forecast ~35,000 / AI boom](https://focustaiwan.tw/business/202512060007)
- [Taiwan News — TAIEX ends lower on profit-taking (6/5)](https://www.taiwannews.com.tw/news/6377567)
- [Taipei Times — AI boom drives TAIEX record highs](https://www.taipeitimes.com/News/front/archives/2026/05/05/2003856767)
- [CFR — Taiwan failed recall, cross-strait implications](https://www.cfr.org/articles/what-failed-recall-taiwan-means-us-taiwan-and-cross-strait-relations)
- [Insight Taiwan — TWD surge, exporter risk](https://insighttaiwan.com/taiwan-dollar-surge-exporter-risk-analysis-2025/)

---

## Update Log
- 2026-06-06 v1.0：6/5 美股大跌後完整路徑研判。ACT 人工重建（環境封鎖即時數據，待 Mac 校正）；2018/2 為最佳對標；美/台分情境 + 6 月事件甘特圖 + 分批加碼劇本 + 倉位清單。
</content>
</invoke>
