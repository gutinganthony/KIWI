# LEARNINGS — 歷任 session 踩坑紀錄

> 每個 session 開始時讀本檔。格式與精簡規則見 agents/MAINTENANCE.md §3–§4。
> 已固化進制度檔的教訓不在此重複。**上次精簡：2026-09-24（36→18 條）**；前次 2026-07-15（17→12）。
> 精簡原則：同類合併、保留可執行的配方與 URL、刪掉已被後續事實推翻的條目。
> ⚠️ 第 10–14 條屬「判斷類」，依 MAINTENANCE §4 本應搬進 `agents/JUDGMENT.md`，
> 但改 JUDGMENT 判準需使用者同意，**尚未搬，待 Jake 裁決**。

## A. 環境與工具

- [常駐] 情境：對 Jake 的所有回覆｜規則：**一律繁體中文**（除非他指定其他語言）；程式碼/指令/專有名詞可保留英文。曾因模型切換漂移成英文被糾正。
- [2026-07-07 / 2026-08-19] 情境：本環境跑 Python / Bash｜規則三條：①pip 一律 `pip install --user`（否則撞 debian 系統套件衝突 PyJWT RECORD not found）②Bash 的 cwd **跨呼叫會延續**，一律用絕對路徑 `/home/user/KIWI/...`，不依賴前次 cd ③**side-mount／best-effort 腳本裡 import 含原生擴充的套件（pypdf→cryptography→pyo3）一律 `except BaseException` 並快取結果**——損壞的系統 `cryptography` 會拋繼承 `BaseException` 的 `PanicException`，`except Exception` 和 `except ImportError` **都攔不住**，會打掛宿主的每日 dashboard job。
- [2026-07-10 / 07-26 / 08-09 / 09-16] 情境：判斷某個外部站能不能抓｜**鐵律：「雲端 session 擋」「Actions runner 擋」「WebFetch 擋」是三條不同的 egress，每個環境各自實測一次，絕不跨環境沿用封鎖結論。** 已知：雲端 session 對日本開示站（tdnet／edinet／irbank／kabutan／minkabu／yahoo.co.jp）、多數金融站、x.com 一律 CONNECT 403；**但同樣的 TDnet 在 runner 上回 200**。**〔2026-09-24 新增｜來源：2026-09-16 session〕** 雲端新增封鎖：`lumentum.com`（**主對話 WebFetch 親測回 `EGRESS_BLOCKED`**）；另 businesswire、ecoc2026.org、lightcounting、oiforum、cw-wdm.org、sec.gov、stockanalysis、東財、雪球、新浪 **為 subagent 回報、主對話未逐站複測**。2026-09-24 主對話實測補充：**CNBC quote cache 與日經 NKD 在雲端皆 403**（週報的日股行情是 runner 抓的，雲端複製不了）。診斷指令（比反覆換 URL 硬試快）：`curl -sS --cacert /root/.ccr/ca-bundle.crt "$HTTPS_PROXY/__agentproxy/status"` 看 recentRelayFailures，可分辨「政策拒絕」與「連線問題」。規則：碰到雲端抓不到的站，先問「runner 抓不抓得到」，抓得到就寫進資料橋（側掛既有 workflow，不必動 `.github/workflows/` 也不必 actions:write），真的兩邊都不行才進 mac-manual-homework。
- [2026-07-26] 情境：一個 session 連續跑多個研究任務｜事實：**WebSearch 有 session 級上限 200 次**，用罄後主對話與 subagent 都不能再搜｜規則：搜尋密集的工作派給 subagent 且在 prompt 限定「最多 N 次、先列必查清單再搜」；接近上限先落檔，別讓額度耗盡卡死收尾。
- [2026-07-07 / 07-12 / 07-15] 情境：判斷 agent 或 MCP 工具能做什麼｜規則：**以當下 session 的實際工具 schema 與 `.claude/agents/<name>.md` 正文為準**，不要憑 tools 欄推斷用法（verifier 的唯讀約束寫在正文 rule 5，不在 tools 欄），也不要照舊文件硬呼叫。自訂 agent 剛建立當下不會立即生效（隔幾回合清單刷新後才出現）。`claude-code-remote` MCP 工具的可用性**依 surface 與連線狀態變動**（2026-07-12 曾整組不可用：list_repos 回 not available、add_repo/send_later 卡在核准流程且重試無用）——失敗就改用 `mcp__github__*` 或檔案落地替代，不重試第二次。
  ⚠️ **2026-09-24 更正**：曾有 session 寫下「2026-09 已可用」，但那是**憑工具出現在 schema 裡推論的，沒有實際呼叫過**。規則不變：**工具出現在 schema ≠ 可用**，要用就先打一次確認。

## B. CI／版控／資料橋

- [2026-07-10 / 07-12 / 07-30] 情境：寫或改 GitHub Actions workflow｜五個坑：①commit 訊息**任何位置**出現字面 `[skip ci]`／`[ci skip]` 都會跳過觸發（要描述機制就寫「skip-ci 標記」）②fetch 落地的原始 API 回應要先估大小，>1MB 先瘦身再入版控（曾把 36MB leaderboard 回應每日 commit 進 repo）③多個 workflow 寫同一分支，commit-back 前一律 `git pull --rebase origin "${GITHUB_REF_NAME}"`，否則整份報告隨 runner 回收消失 ④**高頻（如 10 分鐘）輪詢的狀態一律走 `actions/cache`，不進版控**（一天 144 個 commit 會洗掉 git log），且設計成「cache 遺失＝只重建基準、不推播」⑤feature branch 新增的排程 workflow，**cron 只在 default branch 生效**，要明白提醒使用者「合併 main 才會開始跑」。
- [2026-07-27 / 08-19] 情境：新增資料橋產出路徑｜**同一個坑踩了兩層**：①`.md` 產出沒被 `update-dashboard.yml` 的 `git add ... *.csv` glob 涵蓋，每次抓完隨 runner 回收消失，一整天沒人發現 ②補上 glob 後檔案確實出現在 main，但**整檔只有兩行 `HTTPError: 403`，沉默失敗三週**｜規則：**驗收句是「repo 裡這個檔有沒有非空的、真實的內容」**——「腳本有跑」「檔案存在」「資料存在」是三件事。配套：狀態檔的副檔名要符合該目錄的 glob（收 `*.md` 的目錄寫 `.json` 一樣會消失）；產出檔在無資料時要明白寫「若連續多次為空，先確認可達性，不要當成沒有開示」。
- [2026-07-28 / 07-30] 情境：在工作分支上看資料或開 PR｜事實：**本 repo 的 main 每天被 bot 用 `auto: update dashboard data` 推進數次**，任何存活超過一天的分支看到的資料都是舊的｜規則：①判斷「某條管線是不是停更」前先 `git fetch origin main` 並用 `git log --oneline -3 -- <資料路徑>` 看該路徑的最新 commit，不要只看工作區檔案的時間戳；也先確認那幾天是不是週末/非交易日 ②**長命 feature branch 的 PR 絕不夾帶 CI 會寫的路徑**（`*/data/**`、`docs/**`）——曾累積 50 個衝突，解完又被下一個自動 commit 作廢。正解是把 PR 改成只含程式碼，資料檔由 main 的排程用新程式碼重生。

## C. 行情與財報資料源（週報重定價的命脈）

- [2026-07-26 → 08-26 累積] 情境：抓現價／市值／P/E／多日收盤｜**Yahoo Finance API 已於 2026-08-02 全面 429 失效**（原 2026-07-26 建立的主源作廢）。現行備援鏈，全部實測通過：
  - **美股現價/市值**：CNBC quote cache `https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&symbols=<SYM>`。代碼：美股裸碼、日股 `6855.T-JP`、英股 `IQE-GB`、法股 `MRN-FR`、台股上市 `2408.TW-TW`、匯率 `JPY=`／`KRW=`／`TWD=`／`EUR=`／`GBP=`、指數 `.N225`／`.KS11`／`.SOX`。**三個坑：逗號批次查詢不支援（靜默回空）、查不到韓股、查不到台股上櫃。**
  - **日股日線**：日經 NKD `https://www.nikkei.com/nkd/company/history/dprice/?scode=<4碼>&ba=1`（`<tr>` 第 5 欄＝終値）。⭐ **「修正後終値」欄位已自動處理股票分割，不需人工換算**（Seikoh 8/27 原始 ¥27,600 → 修正後 ¥5,520）。
    **〔2026-09-24 新增｜來源：`skills/serenity/watchlist.md:42` 的週報教訓，本次精簡時併入｜證據等級：週報實測〕**
  - **歐股日線**：stockanalysis **HTML** 頁 `https://stockanalysis.com/quote/{epa|etr}/<SYM>/history/`（**不是 API**，國際代碼的 API 路徑全 400）。美股用 `/api/symbol/s/<US>/history`。
  - **韓股**：Naver `https://api.finance.naver.com/siseJson.naver?symbol=<6碼>&requestType=1&startTime=YYYYMMDD&endTime=YYYYMMDD&timeframe=day`（單引號需轉雙引號才能 json.loads）。
  - **台股（含上櫃）**：**FinMind `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id=<code>&start_date=...` 免 token、雲端可用**——mops/cnyes/moneydj/yahoo股市/goodinfo/statementdog/TWSE/TPEx 全被封鎖時，台股量化全靠它。＋TPEx 官方 openapi `https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes`（含 `Capitals`＝流通股數，可自算市值）作雙源交叉。
  - **A 股**：騰訊行情 `qt.gtimg.cn` 雲端可用；東財／雪球／新浪／Wind 全封鎖。⚠️ 只有行情、沒有基本面。
    **〔2026-09-24 新增｜來源：2026-09-16 session 的 A 股研究 subagent 回報｜證據等級：未經主對話實測，使用前先打一檔驗證〕**
  - **日本財報原文**：TDnet（**runner 可達**）`https://www.release.tdnet.info/inbs/I_list_<頁碼 001..>_<YYYYMMDD>.html` 與 `.../inbs/<docID>.pdf`；解析一覽頁要先 `re.split(r'<tr[^>]*>')` 再逐列解析 td，單一大 regex 跨欄比對抓不到。**日本標的的財報數字一律以決算短信原文為主源，不用新聞轉述、不用搜尋 snippet。**
  - **四條死路，不要再試**：Stooq（JS/PoW）、kabutan（AWS WAF）、WSJ（DataDome）、stockanalysis 國際 API 路徑。
  - **三個口徑陷阱**：①Yahoo／資料商的 `forwardPE` 對日韓小型股嚴重失真（Seikoh 124.9× vs 研究值 28×）——**只用 trailingPE/marketCap** ②CNBC 日股 `pe` 忽 trailing 忽 forward（連四週確認）③**ADR 的 `yrhiprice` 不可與母公司口徑互用**（SKHY 自高 −18.1% vs 母公司 −43.8%，差 26pp，匯率解釋不了）——ADR 的自高/回檔一律用母公司本地交易所日線重算。
  - **驗收方式**：用「三來源回傳的上週基準價 vs repo 記載的上週快照逐檔比對」，全對才敢往下算。
  - ⚠️ **多來源日內收盤差 2.3% 就足以翻轉一條觸發線**（Seikoh 9/2 CNBC ¥5,040 vs 另一源 ¥5,160，25× 線 ¥5,146 正好在中間）⇒ **當日收盤只有單一來源時不得作判定。**
    **〔2026-09-24 新增｜來源：`skills/serenity/watchlist.md:5,13` 的週報記載，本次精簡時併入｜證據等級：週報實測〕**

## D. 判斷紀律（⚠️ 依 MAINTENANCE §4 應搬 JUDGMENT.md，待 Jake 裁決）

- [2026-08-09] 情境：比對「價格 vs 觸發價」｜錯誤：把觸發價當常數，沿用 watchlist 寫死的價格帶｜事實：**觸發帶多半是「forward P/E × EPS 指引」算出來的，而 EPS 指引每季會被公司自己改寫**——2026-08-09 那週四檔同時上修，Yamaichi 的 15× 帶實際差 16–25%（而這一檔的偏差直接決定觸發響不響）、Kokusai 出現「價格沒到但估值早就到了」的錯配｜規則：**每月第一個週日全掃時用最新指引 EPS 重算全部價格型觸發帶，並就地標註「本觸發價依據的 EPS 指引版本日期」**；財報週任一標的上修/下修，該檔當週就要重算。配套：公司決算短信換算的標 `[推論-公司指引]`（**可**作觸發依據），資料商估值標 `[推論]`（**不可**）。
- [2026-08-02] 情境：市場流傳某個價格類的看空/看多論據｜錯誤傾向：媒體標題連寫「spot-price freefall」就當成出場鐘前哨｜事實：查 TrendForce 一手資料＝主流現貨價從未連續 2 週以上下跌，在跌的是**歐洲零售 DDR5 通道價**，不是合約層｜規則：**價格類論據一律要求「哪一層價格（合約／現貨／零售通道）＋一手來源＋連續幾週」三件齊備才採用**；只有標題形容詞就標 `unverified`，不得作為買賣依據。**〔2026-09-24 新增條款｜來源：2026-09-16 Lumentum/ECOC 傳聞核實 session〕同一把尺的第二個實例**：錨點雖真（會議、日期、講題皆可查），但貼文與官方新聞稿**同日**發布＝**資訊差為零**，且「大規模部署」是把講題的 `at Scale` 加碼譯寫。⇒ **判斷傳聞除了「真假」還要問「它在資訊鏈的哪一端」——消息可以完全屬實而毫無價值。** ⚠️ 該次結論的一手網域全被 403，全部停在搜尋引擎索引層，信心應讀作「傾向」而非「判定」。
- [2026-07-27 / 08-19] 情境：寫下任何會觸發真實動作的數字（出場條件、觸發閾值、前置門檻）｜兩個實例：①出場手冊 v1 有三處「聽起來很合理」的門檻其實無出處（村田「受注残比 <1.0」是憑空生出的）②把「mac-homework 積欠 ≤1 項」寫進閘門，實測 `grep -c` 是 **46 項**＝門檻永遠紅燈＝等於沒設門檻｜規則：**寫入前先實測當下數值；落地後派 fresh-context verifier 逐條核對「手冊寫什麼 vs 原檔實際寫什麼」。** 自己新增的量化修飾詞（「連兩季」「跌破 X」）必須就地標「此門檻為自訂、無出處」，不要刪掉也不要假裝有出處。門檻要設在「努力一下可達」的位置——不可達的門檻不是嚴格，是自我豁免的藉口。
- [2026-08-02 / 08-26] 情境：同一週多檔觸發同時命中，或想把一週的資金流寫成結構讀數｜事實：①2026-07-29 那週 7 個 🟢 觸發，**一週後有 3 檔的觸發依據自己消失**（V 型反彈）——等一週的成本是零，不等的成本是 3 筆買在恐慌價卻失去框架依據的部位 ②「SKH ₩40 兆買回 ⇒ 錢從設備商流進記憶體原廠」這個結構讀數**一週後被自己的資料證偽**（Samsung 宣布大 2.75 倍的回報、股價反而 −8.70%）｜規則：**同週 ≥3 檔觸發，先問「是不是同一個宏觀因子的不同切面」——是的話當成一個部位規模來配，並強制等下一個實體讀數（財報/營收）再執行**，不要按檔數配資。**「同源共同因子」要升格為結構讀數，必須橫跨至少兩個觀察週期且方向一致**；只有一週的資金流最多記成「輪動」。
- [2026-08-09] 情境：為跨市場的崩跌/暴漲寫敘事歸因｜錯誤：把日系標的暴跌歸因於三件全球性事件，**漏掉 7/28 的熊本地震（震度 7，TSMC JASM 避難、Renesas 停產）**，兩週後才在 JEM 的公告原文看到｜規則：**先檢查「這份原因清單能不能解釋各市場的漲跌幅差異」**；某地區明顯偏離而清單裡沒有該地區獨有的因子，就標「歸因不完整」去找地區性事件（天災、匯率、當地政策、指數調整），不要用全球因子硬套。

## E. 分析方法

- [2026-08-13] 情境：任何時間敏感的分析｜**踩坑**：把使用者上傳 CSV 的下載時戳（20260729）當成當天日期並寫進派工 prompt，agent 照此抓資料得出「全類股跌停、不要進場」——**實際當天是 8/13，7/29 是波段最低點，此後族群反彈 24–73%**｜鐵律：①**系統 context 的 `currentDate` 是權威來源**，不可從檔名、使用者敘述或先前訊息推斷 ②時間敏感分析第一步用 API 確認「最新可得交易日」 ③派 agent 時**不要在 prompt 寫死日期**，改要求它先確認並回報。
- [2026-08-21] 情境：某個資料源需要金鑰而使用者註冊失敗卡住（EDINET 卡了六週），或探測到某站可達｜正解：①**「需要金鑰」是 API 的性質，不是資料的性質**——同一份公開資料常有不需金鑰的網頁/鏡像路徑（實測 `api.edinet-fsa.go.jp` 需金鑰，但 `disclosure2.edinet-fsa.go.jp` 網頁介面回 200 且完全不需金鑰）②**寫探測器讓 runner 去試，不要自己猜，而且一定要放一個已知可達的對照組**（本例用 TDnet），否則分不出「站掛了」與「runner 網路掛了」③**首頁回 200 ≠ 取得到你要的文件**——EDINET 是 .NET WebForms（viewstate/postback），**未見過真實 HTML 前不寫解析器**，否則會造出第二個「檔案有、內容是錯誤訊息」的沉默失敗橋｜規則：任何清單型解析器都要輸出「解析出幾列」，否則空結果永遠有兩種解釋。
- [2026-07-10 / 07-30 / 08-17] 情境：從交易流（Polymarket activity、Hyperliquid userFills）重建績效或部位｜三個獨立的坑：①**輸的部位不產生 REDEEM 事件**→重建 PnL 只看到贏家，算出 300% ROI／100% 勝率的假獲利 ②**同一毫秒內的成交，陣列順序與真實撮合順序無關**（2000 筆裡 1799 次相鄰比對對不上）→要批次原子化＋鏈頭回推，且每批次獨立回推才對強平/ADL 有自癒能力 ③**重用既有 parser 前先確認它輸出的單位**（`_norm_ts` 已轉成 epoch 秒，用毫秒運算會讓掃描永遠回 0 個候選）｜規則：重建績效前先問「**輸家看得到嗎／視窗夠長嗎／順序可信嗎／單位對嗎**」；驗收＝重建損益加總必須與原始 closedPnl 分毫不差；離線測試一定要放「應該通過」的正向案例，只測「該被擋的有被擋」不會發現全域淘汰的缺陷。

## F. 持倉

- [2026-09-16] 情境：任何組合層判讀（集中度／曝險／出場鐘涵蓋率），或「要不要買/賣某條賽道」的判斷｜事實：**持倉權威鏈已連續失效三次，每次型態都不同**——① 2026-08-20 `watchlist.md` 持倉表過期，推出「100% 記憶體週期」的錯誤組合判讀；② 2026-09-07 Jake 口頭更新未回寫 Sheet，導致對**已出場一週的 2492 華新科**跑完整 Serenity Step 1–9；③ **2026-09-16 Jake 直接換了一張新 Sheet**，`CLAUDE.md` §0 寫死的舊 fileId 回 `Requested entity was not found`，差點對**已於 2026-09 出場的 COHX** 討論加碼｜正解：現行權威是 Google Sheet「**KIWI 持倉表**」fileId **`1FPmLpXYVgm8Xrsv6Gs01bC-SlKytcEdmXF7NC2vUqJ4`**。**舊 fileId 讀不到時第一假設是換檔、不是沒權限**，改用 `mcp__Google_Drive__search_files`，query 必須是 `mimeType = 'application/vnd.google-apps.spreadsheet'`（**不支援** `name contains` 或裸關鍵字，會回 `Unsupported query field`），在結果標題找「KIWI 持倉表」｜規則：**持倉讀取失敗＝必須排查到底，不可降級為「用快照並註明可能過期」就繼續做判斷**。**過期的持倉不是資訊缺口，它會主動生出錯誤結論**，而且錯的方向永遠是「對一個不存在的部位給建議」。
