# 摸魚記 Session 交接檔（2026-07-22）

> 給下一個 session 的 Claude：**先讀這份，再讀 `personal/content-calendar.md` 和 `personal/writing-style-guide.md`，就能無縫接軌。**
> 本檔是 6/26–7/22 這輪長 session 的完整交接。所有工作都在 git 分支 `claude/evaluate-business-opportunities-mJXMo`。

---

## 一、這是什麼專案

Jake（私人銀行 IFA）經營中文財經 Substack「**摸魚記**」，目標受眾是高收入專業人士，定位「私銀視角×量化框架」。Claude 的角色：研究查證、草稿撰寫、圖表製作、選題規劃、風格學習。Jake 是總編輯：他改稿、發佈，Claude 每次對照發佈版學語氣（成果在 style guide，已累積 37 條規則）。

## 二、品牌核心資產（跨文章複用的框架語彙）

- **抄底儀表板**：大盤四盞燈（VIXTWN／外資賣超／跌幅-20%／融資維持率）；記憶體五盞燈（①合約價方向②HBM長約③供給時鐘④需求真偽⑤籌碼溫度）
- **旋鈕不是開關**：亮燈數→倉位大小，不是進場/空手二選一
- **快層 vs 慢層**：股價情緒（快）vs 實體證據（慢：報價/需求/維持率）；「崩的是股價不是記憶體」
- **V型 vs U/L型刀**、**混血刀**（AI 疑慮刃＋通膨刃）
- **稀缺租**（可及性租 vs 地緣租）、**餅變大 vs 被抽血**（SKHY vs SpaceX 對照）
- **對帳文化**：發信號→事後驗收（W5S2 說「兩盞燈試單」→W6 三週對帳 +2.4% 蓋章）
- **離場觸發器（現行有效）**：①DRAM 合約價實際轉跌 ②需求證據惡化（雲端 capex 下修/HBM 砍單）；儀表板更新觸發器：外資單日賣超回千億級或 VIXTWN 站回 40
- 金句庫：「恐慌是故事，需求是存在」「同一個600億，多頭讀到需求，空頭讀到帳單」「誰在收租」

## 三、已發佈文章（連載脈絡）

| 日期 | 篇名 | 主軸 |
|------|------|------|
| 6/26 | W5S2 台股抄底儀表板 | 四盞燈、兩盞亮=試單 |
| 7/2 | W6M 崩的是股價還是記憶體 | 記憶體五燈、股價vs報價 |
| 7/4 | W6M2 Burry 押紅燈我押綠燈 | Burry 戰績七案例、Karp 三鏈 |
| 7/9 | W7 海力士為什麼現在來美股 | ADR=擴產軍費、BI 報告 |
| 7/11 | W7M2 ADR掛牌後記：記憶體都撐住啦 | 三兄弟記分板、SpaceX 對照 |
| 7/17 | W6 恐慌喊到最大聲的那週 | CPI 3.5%+台積電證詞+三週對帳 |

## 四、待辦與排程（詳見 content-calendar.md）

1. **世界盃特別篇（已完稿待發，優先）**：`drafts/2026-WC_betting-recap-draft.md`＋殺手圖 `WC-chart-breakeven.png`。決賽 7/19 已結束（西班牙 1:0 阿根廷），熱度衰減中，**越快發越好**。發文前：核沙烏地賠率、快查 Bloom/Benham、刪製作註記。
2. **反彈定性篇（框架已備）**：`research/rebound-deadcat-research.md`——「人道走廊 vs 死貓跳」，7/21 美股大反彈（費半+5.5%、美光+12%，台韓出口數據=慢層證據）。建議本週後半發，等第二根證據。五工具鑑定表已設計好。
3. **W8 1999 持倉指南（順延中）**：研究檔＋回測程式全備（`drafts/gen_W8_backtest.py`，已煙霧測試）。**卡在等 Jake 上傳 Nasdaq Composite CSV**（stooq ^ndq，1997-06~2006-01，環境 egress 擋 FRED/Yahoo/stooq）。CSV 一到：`python gen_W8_backtest.py <csv>` 出三策略淨值＋換手紀錄＋圖。
4. **W9 國安基金九役**：`research/nsf-nine-battles-research.md`（出手線 -25%~-44%、換算今日 35,800–38,200）。缺第 1–3 役精確指數 TWSE 核實。
5. **W10 ASIC「輝達之外錢流向誰」**：Jake 拍板。動工前需做賽道研究（博通/Marvell/世芯/創意）；素材＝Kenji Marvell 三部曲＋BI 報告 ASIC 數據。
6. **月底兩個開獎日**：DRAM 合約價更新（月底，DRAMeXchange；兆易創新警告的裁判）＋ FOMC（7 月底）。這兩個是 W6 對讀者的承諾，屆時要跟進。
7. 成長面：Notes 成稿庫在 `distribution/notes-ready-2026-07.md`（12+3 則）；成長計畫在 `distribution/growth-plan-2026-06.md`。

## 五、市場現狀快照（截至 7/22）

- 台股 7/16 收 45,624.98（6/26 為 44,571.76）；VIXTWN 34.74（恐慌區>30 內）；融資維持率 182.88%（分子效應警告已寫過）；外資 7/16 賣超 483 億
- 7/13 韓國熔斷（海力士 -15.4% 史上最大）→ 7/16 台積電法說（capex 上修 600-640 億、全年 +40%、GM 67.7%）→ 7/16 美股賣證詞（TSM -4%、費半 -4.91%）→ **7/21 大反彈**（費半 +5.5%、美光 +12%、SNDK +14%，台韓出口數據驅動）
- 美光下次財報 **9/23**；SanDisk 財報 **8/5**；台積電除息 **9/16**（配 7 元）
- Burry 放空美光 @1,051.87（7/2）；SKHY 發行價 $149、首日收 168.01
- Jake 部位：偏滿、續抱、有新資金會加；DRAM ETF 照節奏撿

## 六、工作慣例（必守）

1. **數據紀律**（CLAUDE.md「Data Accuracy」節，血淚換來）：一切數字查證標來源；事件日期對官方行事曆（美光 FQ、台積電季配息 3/6/9/12 月中、FOMC、CPI）；「唯一/第一」先窮舉反例（SNDK 教訓）；**動筆前先看系統 currentDate**（世界盃教訓）；查不到標〔待補〕。
2. **草稿慣例**：文末放〔草稿製作註記，發佈前刪除〕列數據來源與待確認項；正文預留待補槽給 Jake 填。
3. **圖表**：白底 JPM Daily Guide 版型（金色章頭方塊＋Serif Bold 標題＋灰副標＋細線輕格線＋左下資料來源小字）；腳本存 `drafts/gen_*.py`；渲染後必 Read 檢查排版；Jake 不要圖上出現「今天」等相對時間、不要多餘註腳文字。
4. **風格**：寫稿前讀 `writing-style-guide.md` 全部 37 條。要點：無破折號、斷言留餘地但結論敢說滿、中文同行來源模糊化/英文可點名、每個利多配風險註記、番外術語白話化、結尾「祝大家都上班摸魚炒股賺大錢」、免責 `<以上純粹觀點分享不構成投資建議，數據均來自公開資源。>`。
5. **修錯**：已發佈文章的小錯＝Substack 靜默修正不登道歉；框架級誤判才進後記檢討。
6. **交付**：成稿＋圖用 SendUserFile 直接傳（repo 連結對 Jake 是 404，他不在分支上看）；重要決定更新 `content-calendar.md`（唯一排程總表）並重傳。
7. **環境限制**：egress 擋 FRED/Yahoo/stooq/TWSE 等數據站（403 勿硬繞）；Substack 文章 WebFetch 多 403（用 WebSearch 摘要）；無 Substack 串接（發文靠 Jake 手動）；台股即時數據靠 Jake 截圖提供。
8. Gmail 素材管線：Kenji（kenjiosone）、大叔美股（unclestocknotes，付費已訂）、App Economy、capitalcycle 等；素材掃描存 `market-intel/`。

## 七、關鍵檔案地圖

```
personal/
├── content-calendar.md            ← 排程總表（唯一真相）
├── writing-style-guide.md         ← 37 條語氣規則（每次發佈後更新）
├── session-handoff-2026-07.md     ← 本檔
├── drafts/                        ← 草稿+圖表腳本+PNG（gen_*.py 可重跑）
│   ├── 2026-WC_betting-recap-draft.md   ← 待發
│   ├── gen_W8_backtest.py               ← 等 CSV
│   └── 2026-W6_signal-tracking-playbook.md ← 決策樹方法論範本
├── research/                      ← 查證數據庫（各篇一檔，含來源連結）
├── market-intel/                  ← Gmail 素材掃描
└── distribution/                  ← Notes 成稿庫、成長計畫
```

## 八、給下一個 session 的第一步建議

1. 確認今天日期（系統 currentDate）
2. 讀 `content-calendar.md` 看排程現況
3. 問 Jake：世界盃篇發了沒？反彈篇要不要動工？CSV 有了沒？
4. 若月底已到：主動提醒 DRAM 合約價＋FOMC 開獎（W6 的讀者承諾）
