# 摸魚記 Session 交接檔（2026-07-27 更新）

> 給下一個 session 的 Claude / Codex：**先讀這份，再讀 `personal/content-calendar.md` 和 `personal/writing-style-guide.md`，就能無縫接軌。**
> 本檔是 6/26–7/27 這輪長 session 的完整交接。所有工作都在 git 分支 `claude/evaluate-business-opportunities-mJXMo`（**不是 main，讀取時務必先切換/checkout 到這條分支**）。
> 這輪 session 由多個 AI 工具（Claude Code、Codex）在同一分支上接力工作過，commit 風格因此不完全一致（中文/英文都有），這是正常狀態，不代表衝突。

---

## 一、這是什麼專案

Jake（私人銀行 IFA）經營中文財經 Substack「**摸魚記**」，目標受眾是高收入專業人士，定位「私銀視角×量化框架」。AI 的角色：研究查證、草稿撰寫、圖表製作、選題規劃、風格學習。Jake 是總編輯：他改稿、發佈，AI 每次對照發佈版學語氣（成果在 style guide，已累積 37 條規則）。

## 二、品牌核心資產（跨文章複用的框架語彙）

- **抄底儀表板**：大盤四盞燈（VIXTWN／外資賣超／跌幅-20%／融資維持率）；記憶體五盞燈（①合約價方向②HBM長約③供給時鐘④需求真偽⑤籌碼溫度）
- **旋鈕不是開關**：亮燈數→倉位大小，不是進場/空手二選一
- **快層 vs 慢層**：股價情緒（快）vs 實體證據（慢：報價/需求/維持率）；「崩的是股價不是記憶體」
- **V型 vs U/L型刀**、**混血刀**（AI 疑慮刃＋通膨刃）
- **稀缺租**（可及性租 vs 地緣租）、**餅變大 vs 被抽血**（SKHY vs SpaceX 對照）
- **人道走廊 vs 死貓跳**（7/25 新增，現在是進行中的連載主軸）：走廊是給裡面的人走出來的，不是給外面的人衝進去的。目前判定線：台股收盤跌破 **42,449.70**＝死貓跳完成鈴；VIXTWN 收盤站上 **40**＝第二警報
- **對帳文化**：發信號→事後驗收（W5S2「兩盞燈試單」→W6 三週對帳 +2.4%；反彈篇立的兩條線，正等 FOMC/DRAM 對帳）
- **離場觸發器（現行有效）**：①DRAM 合約價實際轉跌 ②需求證據惡化（雲端 capex 下修/HBM 砍單）；儀表板更新觸發器：外資單日賣超回千億級（**已響一次：7/17 -1,883.15 億**）或 VIXTWN 站回 40（**未響：7/24 盤中 40.02 觸線、收 38.09**）
- 金句庫：「恐慌是故事，需求是存在」「同一個600億，多頭讀到需求，空頭讀到帳單」「誰在收租」「反彈只活了三天」「賣壓沒有消失，它在點名」

## 三、已發佈文章（連載脈絡，唯一真相在 content-calendar.md）

| 日期 | 篇名 | 主軸 |
|------|------|------|
| 6/26 | W5S2 台股抄底儀表板 | 四盞燈、兩盞亮=試單 |
| 7/2 | W6M 崩的是股價還是記憶體 | 記憶體五燈、股價vs報價 |
| 7/4 | W6M2 Burry 押紅燈我押綠燈 | Burry 戰績七案例、Karp 三鏈 |
| 7/9 | W7 海力士為什麼現在來美股 | ADR=擴產軍費、BI 報告 |
| 7/11 | W7M2 ADR掛牌後記：記憶體都撐住啦 | 三兄弟記分板、SpaceX 對照 |
| 7/17 | W6 恐慌喊到最大聲的那週 | CPI 3.5%+台積電證詞+三週對帳 |
| 7/21 | WC 世界盃踢完了，以賭球維生是否可行？ | $60B量體、兩篇論文、三案例、台灣運彩78%數學 |
| 7/25 | 反彈只活了三天 | 反彈五工具重讀；判定＝人道走廊關門中；42,449.70死貓跳完成鈴；VIXTWN收盤40第二警報 |

## 四、【現在最優先】排程中：條件式拆篇，FOMC 快層 + 八月慢層

反彈篇（7/25）立了三張考卷：FOMC、月底 DRAM 合約價、中東油價。下一步不是寫一篇，是**兩篇條件式拆篇**，7/27 當天已由本輪 session 設計完成骨架：

### 4a. FOMC 快層對帳番外（`drafts/2026-FOMC_corridor-check-draft.md`）
- 觀察窗：FOMC 7/28–29（聲明台灣時間 7/30 凌晨）+ 7/30 台股收盤
- **條件式發布**：文末列了 7 條發布門檻（Fed 明顯意外／2Y美債±10bp／Nasdaq或費半±1.5%+／台股跌破42,449.70／VIXTWN收40+／外資千億賣超／利多不漲或利空不跌），任一成立才發完整篇（建議 7/30 週四 16:30–18:30）；全部未達則改發 150–250 字 Note，模板已寫好
- 骨架已有：開場三選一（待 Jake 選當天真實情境）、Fed怎麼做/市場怎麼讀/台股按沒按門鈴 三段結構、五種行情分支的判讀模板、標題依結果五選一
- **這篇幾乎全是〔待補〕**，因為 FOMC 還沒開，7/27 這天只能把骨架和判斷邏輯寫死，數字要等 7/30 當天才填得進去

### 4b. 八月慢層與最終判定（`drafts/2026-AUG_corridor-verdict-draft.md`）
- 建議發佈：8/1（週六）
- **開頭季節性研究已經做完、是真數據不是待補**：S&P500 1950–2025，八月平均+0.04%／九月-0.63%／十月+0.90%；中期選舉年單獨拉出（19次樣本）也算好了；結論＝「季節性像氣候不是天氣」，反駁「八月一定跌」和「選前必跌」兩個坊間說法
- 也已經寫入兩則新慢層證據（7/24發生）：**SK Group×NVIDIA $500B+ 合作倡議**（含 SK hynix 下一代 HBM 長約）、**NAVER×NVIDIA×Brookfield 主權AI擴產 55MW→200MW**；黃仁勳開X帳號替開放權重模型站台的公開信也寫了，但明確標註「這張只能加分還不能蓋章」
- 待補：FOMC那篇的一句分數（不重複細節）、DRAM合約價實際月檢結果（TrendForce預估3Q26 Server DRAM合約價+13%~18%，但要等月底真實數字，不可用spot price代替）、本週台股/外資/融資/記憶體股數字、Jake本人部位動作、最終判定三選一（升級/維持/降級版文字都寫好了，依開獎結果留一個）
- 圖表規劃：`AUG-chart-seasonality-verdict.png`（左：季節性柱狀圖／右：三張考卷卡片）尚未產生

### 給接手者的具體下一步
1. 確認今天日期（系統 currentDate，不要用對話流推算，本專案吃過兩次虧）
2. 若已過 7/28–29 但還沒到 7/30：等 FOMC 結果，準備填 4a
3. 若已過 7/30：先看 4a 是否已發布/是否已改發 Note，若還沒處理，照發布門檻邏輯判斷並執行
4. 若已過 8/1：檢查 4b 是否已完成發布；若還沒，這是當前最優先任務，抓 DRAM 合約價與本週數據補完

## 五、其餘待辦與排程（詳見 content-calendar.md，唯一排程總表）

1. **W8 1999 持倉指南（順延中）**：研究檔＋回測程式全備（`drafts/gen_W8_backtest.py`，已煙霧測試）。**卡在等 Jake 上傳 Nasdaq Composite CSV**（stooq ^ndq，1997-06~2006-01，環境 egress 擋 FRED/Yahoo/stooq）。CSV 一到：`python gen_W8_backtest.py <csv>` 出三策略淨值＋換手紀錄＋圖。
2. **W9 國安基金九役**：`research/nsf-nine-battles-research.md`（出手線 -25%~-44%）。缺第 1–3 役精確指數 TWSE 核實。
3. **W10 ASIC「輝達之外錢流向誰」**：Jake 拍板。動工前需做賽道研究（博通/Marvell/世芯/創意）；素材＝Kenji Marvell 三部曲＋BI 報告 ASIC 數據。
4. 成長面：Notes 成稿庫在 `distribution/notes-ready-2026-07.md`；成長計畫在 `distribution/growth-plan-2026-06.md`。

## 六、市場現狀快照（截至 7/24 收盤，最後確認的完整數據點；7/25 之後看 content-calendar.md 與草稿內的最新待補）

- **台股**：7/17恐慌-2,953.71收42,671.27（史上最大跌點）→7/20續跌收**42,449.70（本波修正收盤低點，死貓跳判定基準）**→7/21-23反彈至44,850.81→7/24補跌-1,195.97收43,654.84（史上第9大跌點，外資-609.5億<千億未二響，VIXTWN盤中40.02未收上）
- **美股**：7/21費半+5.5%/MU+12%/SNDK+14%領漲→7/23 Nasdaq-2.15%把反彈吐光（Alphabet capex上修被讀成帳單、Tesla財報miss、紅海油輪布蘭特破$100）→7/24費半-4.25%記憶體被單獨點名（MU-6.99%/SNDK-10.79%/SKHY ADR-8.81%），前三天領漲者原路退回，大盤止穩（道瓊+0.46%）、布蘭特跌回$100下
- 美光下次財報 **9/23**；SanDisk財報 **8/5**；台積電除息 **9/16**；**FOMC 7/28-29**；月底DRAM合約價更新
- Jake部位：偏滿、續抱、有新資金會加；DRAM ETF照節奏撿

## 七、工作慣例（必守）

1. **數據紀律**（CLAUDE.md「Data Accuracy」節，血淚換來）：一切數字查證標來源；事件日期對官方行事曆；「唯一/第一」先窮舉反例；**動筆前先看系統 currentDate，絕對不要用對話流推算今天幾號**（本專案至少踩過兩次坑：世界盃決賽日期漂移、長session跨天誤判）；查不到標〔待補〕。
2. **草稿慣例**：文末放〔草稿製作註記，發佈前刪除〕列數據來源與待確認項；正文預留待補槽給 Jake 填。**FOMC/AUG兩篇還多一種慣例：條件式發布**（先寫判斷邏輯與門檻，數字待事件發生後才填，未達門檻可能改發精簡Note而非完整電子報）。
3. **圖表**：白底 JPM Daily Guide 版型（金色章頭方塊＋Serif Bold標題＋灰副標＋細線輕格線＋左下資料來源小字）；腳本存`drafts/gen_*.py`；渲染後必Read檢查排版；不出現「今天」等相對時間。**環境若缺CJK字型或matplotlib：`apt-get install -y fonts-noto-cjk` + `pip install --user matplotlib`；PDF大檔解析用`pip install --user pypdfium2`（pypdf在本環境因cryptography/rust綁定會crash，勿用）。**
4. **風格**：寫稿前讀`writing-style-guide.md`全部37條。要點：無破折號、斷言留餘地但結論敢說滿、中文同行來源模糊化/英文可點名、每個利多配風險註記、結尾「祝大家都上班摸魚炒股賺大錢」、免責`<以上純粹觀點分享不構成投資建議，數據均來自公開資源。>`。
5. **修錯**：已發佈文章的小錯＝Substack靜默修正不登道歉；框架級誤判才進後記檢討（示範：反彈篇v1判定被行情推翻，v2直接重寫，v1留檔`2026-REB_deadcat-draft.md`對照，不寫道歉段）。
6. **交付**：成稿＋圖用SendUserFile直接傳（repo連結對Jake是404，他不在分支上看）；重要決定更新`content-calendar.md`（唯一排程總表）並重傳。
7. **環境限制**：egress擋FRED/Yahoo/stooq/TWSE等數據站（403勿硬繞）；Substack文章WebFetch多403（用WebSearch摘要）；無Substack串接（發文靠Jake手動）；台股即時數據靠Jake截圖/PDF提供。
8. Gmail素材管線：Kenji（kenjiosone）、大叔美股（unclestocknotes）、App Economy、capitalcycle等；素材掃描存`market-intel/`。
9. **多工具接力慣例**：這條分支可能同時被Claude Code和Codex等不同工具編輯。**push前務必先`git fetch`+比對遠端HEAD**，若遠端有新commit先`git pull --rebase`（同LEARNINGS.md規則：多workflow寫同分支一律rebase-then-push），不要用force push覆蓋。交接檔（本檔）是唯一起點，但content-calendar.md的排程表才是唯一真相，兩者若有落差以calendar為準。

## 八、關鍵檔案地圖

```
personal/
├── content-calendar.md                    ← 排程總表（唯一真相，已更新至7/27）
├── writing-style-guide.md                 ← 37 條語氣規則
├── session-handoff-2026-07.md             ← 本檔
├── drafts/
│   ├── 2026-FOMC_corridor-check-draft.md  ← ★現在最優先，待7/28-29開獎
│   ├── 2026-AUG_corridor-verdict-draft.md ← ★8/1發佈，季節性研究已完成
│   ├── 2026-REB_deadcat-v2.md             ← 已發佈（7/25）
│   ├── REB-chart-deadcat.png / gen_REB_chart_deadcat.py
│   ├── 2026-REB_deadcat-draft.md          ← v1舊版，僅供對照勿用
│   ├── gen_W8_backtest.py                 ← 等 CSV
│   └── 2026-W6_signal-tracking-playbook.md ← 決策樹方法論範本
├── research/                              ← 查證數據庫
├── market-intel/                          ← Gmail 素材掃描
└── distribution/                          ← Notes 成稿庫、成長計畫
```

## 九、給下一個 session 的第一步建議

1. 確認今天日期（系統 currentDate，不要用對話流推算）
2. 讀 `content-calendar.md` 看排程現況（唯一真相）
3. 對照第四節「給接手者的具體下一步」判斷 FOMC/AUG 兩篇走到哪一步
4. 問 Jake 確認：FOMC番外發了嗎還是改Note了？部位這週有沒有動作？DRAM合約價數字有了嗎？
