---
title: 🖥️ Mac 手動功課清單（雲端做不到、只能在 Jake 電腦上做的事）
url: local
topic: technology
tags: [workflow, convention, manual-homework, cloud-limitations, checklist]
last_updated: 2026-07-06
---

# Mac 手動功課清單

## 這份檔案在幹嘛（慣例說明）

雲端 session（claude.ai/code）跑在隔離容器裡，有些事**做不到**：
- 抓被 403 擋掉的日本財經站（Yahoo!ファイナンス、kabutan、minkabu）、EDINET/TDnet、部分券商頁；
- 觸發需要 `actions:write` 的 GitHub 操作（整合 token 無此權限，Claude 代按會 403）；
- 讀你本機的 broker/下單環境。

**慣例**：每次雲端 session 結束時，把「雲端做不到、需要你在 Mac 上做」的事**集中 append 到本檔的「待辦」區**（而不是散在對話裡）。你在 Mac 開一個 local session（或自己動手）**一次清掉**，做完打勾、移到「已完成」區。這樣把散射的介入合併成單點，也不會漏。

> 為什麼放這裡：CLAUDE.md 的「KIWI 自動載入」清單有指向本檔，所以**每個新 session 開場就會看到有沒有積欠的手動功課**——系統提醒你，而不是你自己記。

---

## 🔴 待辦（依急迫度）

### 🟢 2026-08-19 六週懸案定讞：**EDINET 不是被雲端擋，是需要一把免費的 API key**（做完這一項，JEM 否證 #3 就自動化了）

2026-08-19 週報在 Actions runner 上實測（`已確認`）：

| 端點 | 結果 |
|---|---|
| `https://api.edinet-fsa.go.jp/api/v2/documents.json?date=...&type=2` | HTTP **200**，但 body ＝ `{"StatusCode": 401, "message": "Access denied due to invalid subscription key.Make sure to provide a valid key for an active subscription."}` |
| `https://disclosure.edinet-fsa.go.jp/api/v1/documents.json?...`（舊版） | HTTP **403**（v1 已淘汰）|
| 對照組 `https://www.release.tdnet.info/inbs/I_list_001_20260818.html` | HTTP **200**（TDnet 連三週正常）|

→ **結論：雲端到得了 EDINET，缺的只是訂閱金鑰。** 本檔頂部「抓被 403 擋掉的…EDINET」那句對 EDINET 也**不再成立**——它不是被擋，是沒帶 key。

- [ ] **申請 EDINET API 金鑰並放進 repo secret**（**約 5 分鐘，做完解鎖一條卡了六週的否證判定**）
  1. 開 https://api.edinet-fsa.go.jp/ （金融庁 EDINET API 申請頁）→ 註冊帳號 → 取得 **Subscription Key**（免費）
  2. GitHub → `gutinganthony/KIWI` → Settings → Secrets and variables → Actions → New repository secret
  3. Name 填 **`EDINET_API_KEY`**，Value 貼 key
  4. 用法備忘（給未來 session）：呼叫時帶 header `Ocp-Apim-Subscription-Key: <key>`，或 query 參數 `Subscription-Key=<key>`
  5. 驗收：下一次 Serenity 週報應能取得 **JEM 6855 FY3/26 有価証券報告書「主な相手先別販売実績」** → 判定否證 #3「單一 NAND 客戶 >30%」
  > ⚠️ 在 key 到位前，JEM 否證 #3 就是**無法判定**（不是「還沒做」）——請不要再把它列成每週待辦。

### 🟢 2026-08-09 好消息：TDnet 在 GitHub Actions runner 上**可以直連**（本檔頂部「做不到」清單需修正）

本檔開頭寫「抓被 403 擋掉的…EDINET/TDnet」是雲端做不到的事——**這一半已經不成立**。
2026-08-09 週報實測（Actions runner）：

| 來源 | 狀態 |
|---|---|
| `https://www.release.tdnet.info/inbs/I_list_<頁>_<YYYYMMDD>.html`（適時開示一覽） | ✅ **HTTP 200** |
| `https://www.release.tdnet.info/inbs/<docID>.pdf`（決算短信 PDF 原文） | ✅ **HTTP 200**，`pypdf` 可直接抽文字 |
| kabutan.jp | ❌ 403/405 |
| minkabu.jp | ❌ 403 |
| stooq.com（日線 CSV） | ❌ JS challenge |
| Yahoo Finance API | ❌ 連三週 429 |
| EDINET（有価証券報告書） | ⚠️ **本輪未測**，仍留 Mac |

→ **本週 9 份日本財報數字全部取自 TDnet 原文**（JEM／Yamaichi／santec／Towa／Tamura／JCU／Kohoku／Kokusai／岡本硝子）。

**✅ 可從本清單移除的一項**：**「JEM TDnet 開示清單（7/3–7/6）」——雲端可自己做，不必等 Mac。**
（JEM 的另一件功課「FY3/26 有価証券報告書客戶表」在 **EDINET**，尚未實測，**保留在下方**。）

### 2026-08-09 新增／保留

- [ ] **JEM 6855 FY3/26 有価証券報告書客戶表**（EDINET）——否證 #3「單一 NAND 客戶 >30%」**連四週無法判定**。
      ⚠️ 注意：JEM 8/7 的通期上修理由只寫「**メモリー向け**プローブカード需要の急拡大」，**未區分 DRAM/HBM 與 NAND**，所以財報本身解不了這條。
      **順帶請試一次 EDINET 在 runner 上通不通**——若通，這件功課也能自動化。
- [ ] **Mersen H1 2026 新聞稿原文**抓 DC 分項季銷售（T5 首驗）。⚠️ **急迫性已下降**：價格 €40.68 > 觸發 B 的 €38 上限，即使數字達標觸發 B 的價格門也已關上（連兩週）。
- [ ] **`agents/loops/weekly-repricing-audit.md` 憲章改版**（可在雲端做，但屬制度變更需你點頭）：
      ①主源由 Yahoo 改為 **CNBC quote cache（需帶桌面 UA）／Naver siseJson／FinMind** 鏈；
      ②**新增 TDnet 為日股一手揭露源**；③記下已知坑：LPKF 代碼是 `LPK-DE` 非 `LPKF-DE`、CNBC 逗號批次不支援且查不到韓股/台股上櫃。


### 站著的（長期）
- [ ] **需要「手動觸發 workflow」時只能你按**（2026-07-30 確認）。雲端 session 的整合 token **沒有 `actions:write`**：`POST /actions/workflows/<file>/dispatches` 回 `403 Resource not accessible by integration`。能做的是「推 commit 觸發 push trigger」與「讀 run/log/artifact」，不能 dispatch、不能 re-run。
  - 位置：Actions 分頁 → 選那支 workflow → 右上 **Run workflow**。
  - 常用兩支：`Hyper Observer`（重抓錢包資料）→ 跑完再按 `Monitor Build`（重建公開頁）。
  - 繞道：資料若已存在，我可以在本地離線重建產物並開 PR，你按一次 merge 即可（`deploy-pages` 會自動上線）。

- [ ] **GitHub Pages deploy 卡住時去按 Re-run failed jobs**（自 2026-07-03 起偶發，Pages 後端暫時性錯誤、非程式問題）。
  - ✅ 現在已有失敗推播（`deploy-pages.yml` → Telegram），收到通知再去按即可，不用自己巡邏網站。
  - 位置：Actions 分頁 → Deploy Dashboard to GitHub Pages → Re-run failed jobs；或等下次自動 deploy。

### 2026-08-05 session 產生的（Serenity 週度輕量週報）
- [ ] **JEM 6855 兩件功課 — 連三週未清，8/7 Q1 只剩 2 天**（最急，卡住一條否證判定）。
  ①**TDnet 開示清單 7/3–7/6** ②**FY3/26 有価証券報告書的客戶表**（NAND 客戶占比／Micron 系是否回到 >10%）。
  **否證 #3「有報單一 NAND 客戶 >30% → HBM 敘事降級」至今無法判定**，而 8/7 Q1 就到。
  雲端擋點：EDINET/TDnet 與 kabutan/minkabu 皆 403。
  → 這兩件不清，JEM 的首批建倉在框架上是「否證未驗完就進場」。（首批區 ¥6,400–6,800；8/4 收 ¥6,490 在區內、8/5 盤中 ¥7,190 已穿出）
- [ ] **CNBC quote cache 的 User-Agent 坑（制度層，補進 loop 憲章）**。
  2026-08-05 實測：CNBC `quote.cnbc.com/quote-html-webservice/...` **不帶桌面 User-Agent 會被 Akamai 回 `Access Denied`**（8/2 那次沒遇到）。
  另 **LPKF 的正確代碼是 `LPK-DE`**，`LPKF-DE` 回 `code:1` 查無。
  **Yahoo Finance API 連兩週全數 429**（8/5 再測 `query2/v8/finance/chart` 仍 429）→ 備援鏈已可視為常態主源，`agents/loops/weekly-repricing-audit.md` §HOW TO WORK 該正式改版（改制度檔前依 `agents/MAINTENANCE.md` 應先確認）。
- [ ] **Yamaichi 6941 / Tamura 6768 的 8/5 Q1 決算短信**（本週報發稿時 14:10 JST 尚未發布）。
  Yamaichi 的 **營益年化 run-rate ≥¥13B** 是本檔**唯一還活著的觸發路徑**（價格路徑已失效：¥10,010 vs 觸發 ¥6,700–7,200，高 39%）；
  Tamura 看 **OP ≥¥14 億且段利潤率回 5%+**（三條件第 2 條）。
  → 下輪（週日）週報會自動補判，但若你想早一步看，去 TDnet 抓決算短信 PDF。

### 2026-08-02 session 產生的（Serenity 全掃週報，8 月財報群前）
- [ ] **Mersen H1 2026 新聞稿原文 → 抓 data center 分項銷售**（急，決定一個觸發判定）。
  本週已確認的 H1 數字：營收 €6.11 億（organic +3.9%）、EBITDA €9,740 萬（15.9%）、經常營業利益 €5,650 萬（9.2%）、**全年指引上修**（organic 4–6%、EBITDA 率 16–16.5%、營業利益率 9.0–9.5%）。
  **但雲端 WebSearch 抓不到 DC 分項**——唯一可得的 DC 數字仍是 Q1 2026 的 €1,000 萬。
  Serenity 買進觸發 B 明文要求「**H1 DC 季銷售 ≥€15M ＋ 首次給 DC 專項目標/具名客戶**」，兩項皆未獲驗證 → 本週判定 **觸發 B ❌ 不成立**、降級條件亦標 `unverified`。
  要看的頁：`mersen.com` → Group → News & Events / Financial results → 2026 H1 press release + slide deck。
  **要抓三件**：①H1 或 Q2 的 DC 銷售金額 ②有無 DC 專項年度目標 ③有無具名客戶。
  → 決定 T5 燈（AI 電力確認）與 Mersen 是否進入分批（現價 €37.24，已低於觸發 B 的 €38 價格條件）。
- [ ] **Yahoo Finance 行情 API 是否恢復**（制度層，影響每週重定價）。
  本 runner 2026-08-02 實測 **query1／query2／quoteSummary／getcrumb 四個端點全數回 HTTP 429 "Too Many Requests"**，`agents/loops/weekly-repricing-audit.md` 寫死的主源全掛。
  本週已建立並實測通過的備援鏈：**CNBC quote cache**（`source="Exchange"`，美/日/英/法/台上市＋匯率，附 trailing P/E 與市值；**坑：逗號批次不支援、查不到韓股、查不到台股上櫃**）＋ **Naver `siseJson`**（韓股）＋ **FinMind `TaiwanStockPrice` + TPEx openapi**（台股含上櫃）。
  → 若 Yahoo 持續 429，該把備援鏈正式寫進 loop 憲章 §HOW TO WORK（本 session 未自行改憲章，改制度檔前依 `agents/MAINTENANCE.md` 應先確認）。
- [ ] **Ayar Labs 到底有沒有被 NVIDIA 收購**（兩說並存，影響 IPO 管線判斷）。
  本 repo 07-15 週報記載「已被 NVIDIA ~$6.5B 收購、IPO 取消」；本週搜尋**查無該併購佐證**，反而查到「2026-03 完成 $500M Series E、與 Wiwynn 在 OFC 2026 發表 1,024 加速器機櫃級參考設計」。
  → 兩說必須有一個是錯的，請以一手來源（NVIDIA newsroom / Ayar Labs newsroom）定讞。

### 2026-07-06 session 產生的（JEM 第一關收尾，加碼前必做）
> 🔄 **2026-07-26 狀態更新：已改由資料橋自動處理，先別自己做。** 本 session 實測雲端 agent proxy 對 **TDnet／EDINET／irbank／kabutan／minkabu／Yahoo!JP／JEM 官網 全部 CONNECT 403**（curl 與 WebFetch 皆然）→ 新增 `scripts/fetch_jp_disclosures.py` 掛在 dashboard workflow（一天 3 次）的 `fetch_backtest_ext.py` 後面，由 Actions runner 抓 irbank 的 `/ir`（開示一覽）與 `/customers`（有報 相手先別販売実績），落地 `data/ext/jp_disclosures/6855_JEM.md`。**下次 bot 跑完就有檔；若檔內是 403 錯誤訊息（代表 runner 也被擋），才需要你在 Mac 上手動做下面兩項。**
>
> 🔴 **2026-07-27 修正：上面那座橋一天都沒生效過，原因不是被擋，是產出從沒被 commit。**
> `update-dashboard.yml` 的 commit 段只有 `git add projects/avi-v5/data/ext/*.csv`，
> 而橋的產出是 `.md`，**不被那個 glob 涵蓋 → 每次抓完就隨 runner 回收消失**（＝ `agents/LEARNINGS.md` 2026-07-10 那個坑的翻版）。
> 已在 `update-dashboard.yml` 補上 `git add projects/avi-v5/data/ext/jp_disclosures/*.md`。
> ⚠️ **此修正在 feature branch 上，要合併 main 之後 bot 才會照新版跑**（cron 只認 default branch）。
> 合併後下一次 dashboard 更新（一天 3 次）就會出現 `projects/avi-v5/data/ext/jp_disclosures/6855_JEM.md`。
> **在那個檔出現之前，下面兩項都不必你動手。** 檔案出現後若內容是 403 錯誤訊息，才輪到你在 Mac 上手動做。
- [ ] **TDnet 7 月適時開示清單**（等橋）：確認 JEM（6855）無再增資/CB/下修。→ 否證 #1。**搜尋層已知：7/11 與 7/24 各有一則開示（PDF 123KB／106KB），標題未取得**——多半是例行的自己株式取得狀況報告，但需確認。
- [ ] **JEM FY3/26 有報「主な相手先別販売実績」**（等橋）：查 NAND 單一客戶占比、**Micron 系是否回到 >10%（＝最強確認）**。→ 否證 #2。**搜尋層已取得部分答案：有報註記「Micron Memory Japan 與 MICRON MEMORY TAIWAN 前事業年度合計未達總銷售 10%」——即 Micron 系在前一年度 <10%；當年度（FY3/26）數字未取得，最強確認訊號尚未成立也尚未推翻。**
- [ ] **Yahoo!ファイナンス 6855 時系列**：核對 7/3 與 7/6 兩日收盤，判別 7/6 單日跌幅是 -10.4% 還是 -14.3%（兩快照矛盾，複核 agent 無法裁決）。
  - 三項全過 → JEM 首批建倉區 ¥6,400–6,800 紀律恢復有效（第二關 8/7 Q1 財報再定第二批）。

### 2026-07-12 session 產生的（LFI 第四錶）
- [ ] **上線驗證 LFI 第四錶**：bot 下次跑 update-dashboard 後，開 https://gutinganthony.github.io/KIWI/ 看第四張紫色錶卡（LFI）有沒有出現真讀數（不是「--」）；失敗會有 Telegram 推播。
- [ ] **上線驗證「連續維持天數」標注**：同一張 LFI 卡片底部應出現「目前水位已連續維持 ≥80 X · ≥90 Y · ≥95 Z 交易日」那一行（bot 下次跑才會帶出 `days_ge_*`，在那之前該行隱藏是正常的）。07-10 讀數已到 84.8，若持續 ≥80，X 應該 ≥1 且逐日遞增。
- [ ] **（可選）真標的驗證節流閥**：資料橋補齊 JEM/Towa/Kokusai 等真股歷史後（~1 週），重跑 `scripts/serenity_throttle_validation.py` 改用真標的，確認「節流閥別硬加」的結論在真標的上也成立。
### 2026-07-12 session 產生的（llm-council-skill 評估）
- [ ] **安裝 gcpdev/llm-council-skill 到 Mac 本機 Claude Code**（雲端跑不了：容器 proxy 會擋 OpenAI/Gemini 的 API 呼叫）。
  > ✅ **2026-07-27：擋住這項的「程式碼未逐行審查」已解除。判定＝有條件可安裝。**
  > 全部可執行程式碼只有 212 行的 `llm-council/scripts/query_llms.py`，已逐行讀完；
  > 發布的 `llm-council.skill` bundle 與 repo 原始碼 `diff` 結果 **IDENTICAL**（無夾帶）。
  > - **網路端點乾淨**：全檔只有兩個 URL，都是官方——`:90` `api.openai.com/v1/chat/completions`、
  >   `:114` `generativelanguage.googleapis.com/...`。無第三方轉發／telemetry／分析。唯一 HTTP 庫是 `requests`。
  > - **資料外送範圍乾淨**：payload 只有 `:144` `" ".join(sys.argv[1:])` 拼出的 prompt。
  >   不讀檔、不列目錄、不夾帶系統資訊或對話歷史——**夾帶什麼完全由主對話決定**（所以下面那條紅線還是要守）。
  > - **本機副作用基本乾淨**：無 `eval`/`exec`/`pickle`/`curl|bash`、無寫檔、不碰 `~/.ssh`、不下載遠端程式碼。
  > - **依賴乾淨**：無 requirements.txt/package.json，唯一第三方 import 是 `requests`，其餘全標準庫。
  >
  > ⚠️ **安裝前必須處理的三件事**：
  > 1. **Gemini 金鑰會在 API 失敗時明文進逐字稿**（唯一實質風險）。`:114` 把 key 放在 URL query string，
  >    而 `:128` `return f"Error querying Gemini ({model}): {str(e)}"` 會把 `raise_for_status()`（`:124`）
  >    產生的**含完整 URL 的例外訊息原樣印到 stdout** → 任何 4xx/5xx 都會讓 `?key=AIza...` 進入
  >    Claude context 與 `~/.claude/projects/*.jsonl`。
  >    **修法**：把 `:128` 改成 `return f"Error querying Gemini ({model}): {str(e).split('?key=')[0]}"`。
  >    不想改就接受它，並定期輪替該 key。
  > 2. **它會執行 PATH 上叫 `gemini` / `codex` 的執行檔**（`:48-53`、`:70-75` 的 `subprocess.run`，
  >    list 形式、`shell=False`，安全；但 README/SKILL.md 完全沒提這件事，只講 API）。
  >    你的 gstack 有 `/codex`，PATH 上**很可能真的有 `codex`** → 它會走 CLI 而不是 API。
  >    **安裝前先跑 `which gemini codex`**，確認跳出來的是你認得的工具。
  > 3. `.env` 放在專案 CWD 並**列入 `.gitignore`**（`references/SETUP.md:87-89` 有提醒）。
  >
  > **步驟**：clone repo → 把 `llm-council/` 資料夾放進 `~/.claude/skills/` → `.env` 填
  > `OPENAI_API_KEY`/`GEMINI_API_KEY` → 套用上面第 1 點的修改 → `which gemini codex` 確認。
  > 用法：對話裡打「Consult the council: ＜問題＞」。
  > **⚠️ 紅線不變：只拿它問技術/通用問題，別把 KIWI 持倉、部位、fund 細節餵給它**——內容會送到 OpenAI 和 Google。
  > ChatGPT 本來就是 council 兩席之一，免額外設定。

### 2026-07-16 session 產生的（幫朋友代管資金研究——僅在你決定要做時才需核對）
- [ ] **核對 Bitget 託管子帳戶門檻**（bitget.com/support 被雲端擋）：「>50,000 USDT 或 VIP2 可申請委託交易員、投資人保留出入金權、無建立費」——這是唯一個人可行的正式代管路徑，數字全來自搜尋摘要未直接核對。
- [ ] **核對 Binance/Bybit/Bitget 帶單門檻與台灣可用性**（官網全被雲端擋；OKX 已直接核對免查）：Binance 合約帶單 1,000 USDT＋服務清單含台灣；Bybit 100 USDT＋Pro 版台灣可用性；Bitget 帶單台灣可用性（查無官方證據）。待核頁面清單見 `topics/business/2026-07-16-crypto-managed-trading-research/research_copytrading.md` 附錄。
- [ ] **（決定行動前必做）law.moj.gov.tw 核對法條原文**：銀行法 5-1/29/29-1/125（雲端僅 GitHub 鏡像間接核對）、《虛擬資產服務法》三讀條文與總統公布日、期交法 §3/§112——法規線報告所有判決字號皆為轉述，引用前須 law.judicial.gov.tw 複核。＋諮詢熟悉虛擬資產的執業律師。

### 2026-07-24 session 產生的（物理 AI 研究——低急迫，深掘/建倉前才需核）
- [ ] **日股估值三檔複核**（quote 站被雲端 403，全為搜尋摘要層）：HDS 6324 預估 PER ~152/PBR 8.3、THK 6481 PER ~36.7、IKO 6480 現價 ~¥2,041（7/14）——kabutan/Yahoo!ファイナンス 各花 1 分鐘。
- [ ] **和大 1536 Optimus 拉貨狀態查證**：Yahoo 股市有「Optimus 拉貨喊停」報導，與 Tesla 產線未啟動互相印證——確認和大是否已實際出貨/出貨中斷（月營收＋法說紀錄）。

### 2026-07-26 session 產生的（Serenity 週報 — 只剩「雲端真的做不到」的項）
> ✅ **上一批「補 live 現價」的功課全部由 2026-07-26 週報自動結案**——發現本 runner 可直連交易所級行情 API（見 `agents/LEARNINGS.md` 2026-07-26 條），全名單價格/市值/trailing P/E 已取得精確值，**不需要你在 Mac 上補價了**。以下是剩下真正需要你的：
- [ ] **JEM 6855 兩件建倉前功課（仍未清，唯一擋住執行的東西）**：①TDnet 7 月適時開示清單確認無再增資/CB/下修；②FY3/26 有価証券報告書「主な相手先別販売実績」查 NAND 單一客戶占比與 **Micron 系是否 >10%（＝最強確認）**。現價 ¥6,280 已跌破首批區 ¥6,400–6,800 下緣、朝 <¥5,800 最大加碼區走，**功課清掉才有部位可談**。
  > 🔄 **2026-07-27：不要自己做，等橋。** 橋沒生效的根因已找到並修好（是 commit glob 漏收 `.md`，不是被擋），
  > 詳見本檔上方 2026-07-06 段的紅字。**合併 main 後下一次 dashboard 更新就會有檔**。
- [ ] **群翊 6664 七月營收（~8/10 公布）＝否證線裁判**：查 TWSE/Goodinfo 月營收 YoY。<10% → 5 月(+7.92%)+7 月成立、六月(+19.32%)變孤點、否證壓力回來；≥10% → 買進條件續成立。**本週價格已進 NT$330–360 觸發區、六月營收 ≥10%＝兩條件成立，這是唯一未結的變數。**
- [ ] **Seikoh 6834 中國 SINY 合資的曝險評估（需讀一手 TDnet PDF）**：`https://www.release.tdnet.info/inbs/140120260716595447.pdf`（7/17 公告）——查合資公司出資比例、是否可能推升中國營收占比、有無技術授權條款。**這是 🟢 觸發名單裡首次出現中國曝險**，Serenity 對中國是原則性排除，權益法不立即否決但要定性。
- [ ] **（低優先）Intekplus 064290 券商目標價時效確認**：查到的 TP ₩18,000 遠低於現價 ₩30,500，疑為 2026/3 舊報告。若確為舊件則不構成降評理由，本週報已暫降為觀察待重評。

### 2026-07-26 session 產生的（研究環境封鎖清單擴大 — 只在需要一手核對時才做）
> 本 session 實測：**雲端對台股/日股/韓股的公開資訊站幾乎全滅**（curl、WebFetch、browse 三條路皆 403），且 WebSearch 有 session 上限 200 次（本 session 用罄）。診斷指令：`curl -sS --cacert /root/.ccr/ca-bundle.crt "$HTTPS_PROXY/__agentproxy/status"` 看 recentRelayFailures。
- [ ] **群翊 6664 下單前必核 5 項**（僅在你決定要買時才需要；複核結論是暫緩至 8/14）：①CB 群翊二 66642 最新流通餘額（已轉換多少→剩餘稀釋真實%）②內部人近三月申報轉讓 ③現金流量表與合約負債拆解（訂單能見度硬證據）④中國營收占比最新值（否證線 45%）與單一客戶占比 ⑤群翊一 66641 是否仍有餘額。被擋站台完整清單見 `topics/business/2026-07-26-groupup-research/research_groupup.md` §附錄 C（18 站）。
- [ ] **（可選）記憶體判定的一手核對**：八因子判定全部數字皆二手（信心僅 45–55%）。若要提升信心，在 Mac 上核對 TrendForce 4Q26 合約價預估、Samsung/SKH 存貨（7/28–30 公布）、Micron SCA 條款（FY26Q3 10-Q）。

### 2026-07-28 session 產生的（NVDA 供應商融資——影響記憶體減倉時鐘，優先度中高）
> 本 session 搜尋額度用罄＋Reuters/CNBC 全被 403，**「NVDA 對 OpenAI 擔保 2,500 億＋融資 3,500 億」與「NVDA CDS 走闊」皆未查證**。分析已完成但建立在假設上（`topics/business/2026-07-28-nvda-vendor-financing-two-sided-review.md`）。
- [ ] **核實 NVDA–OpenAI 安排**：金額、形式（擔保／直接融資／認股權證／GPU 回購保障）、**會計處理是否表外或有負債**。
- [ ] **NVDA CDS 利差**實際變化幅度與起點（判斷市場定價的強度）。
- [ ] **NVDA 最近一季應收帳款／合約資產／DSO 對營收的相對變化**（供應商融資的財報足跡）。
- [ ] AMD 等同業是否有等價安排（判斷是「戰略前瞻」還是「產業級爭客競賽」——後者意義相反）。

### 2026-07-29 session 產生的（HBM 位元拆解——決定記憶體情境②/③，優先度高）
> 雲端對 TrendForce／Micron IR／IDC／Counterpoint／SemiAnalysis 全數 403，搜尋額度用罄。模型已建好（`projects/avi-v5/scripts/hbm_bit_split.py`），**只缺輸入數據；拿到就改 ASSUMPTIONS 重跑，答案機械式掉出來**。
- [ ] **① HBM 佔 DRAM「晶圓」比重的時間序列（決定性，優先做這個）**：TrendForce 或三大廠法說。⚠️ 多數公開資料給的是**位元或營收**佔比，要換算成晶圓佔比（需 trade ratio）——這是最容易出錯的一步。**要的是變化量（Δs），不是水位。**
- [ ] ② trade ratio r：HBM 每位元消耗的晶圓面積是傳統 DRAM 的幾倍（業界常引用 2–3×，需確認）。
- [ ] ③ 若能直接找到「分產品位元供給成長（HBM vs 傳統）」的數據，可跳過整個模型。
- [ ] ④ 核實 IDC「2026 年 DRAM 位元供給 +16% YoY」這個錨點本身。

### 2026-07-29 週報 session 產生的（行情 API 退化——優先度中，影響每週報告精度）
> **Yahoo `quoteSummary` 端點本週起要求 crumb 驗證**（雲端 runner 直接吃 `HTTP 401 Invalid Crumb`），
> 而 07-26 才剛把它訂為市值/P/E 的主源。**`chart` 端點不受影響、價格照常可抓**——退化的只有
> 市值、trailing/forward P/E、P/B 這幾項「基本面欄位」。
> 本週的因應：市值改用「7/24 精算值 × 價格變動 × 匯率變動」推導（股數不變前提下是恆等式，已標 [推論]），
> **forward P/E 本週整個取不到，故 07-29 週報未用其做任何觸發判定**。
- [ ] **在 Mac 上確認 `quoteSummary` 是否只擋雲端 IP**（本機瀏覽器 cookie 環境通常能過）。若能過，
      考慮把「每週一次的市值/P-E 快照」變成 Mac 側的手動輸出，貼回 repo 給週報吃。
- [ ] **或找替代源**：Stooq、FinMind（台股，見下方 07-11 項）、各交易所官方 API。
      目標是恢復 **forward P/E**——它是 Serenity 觸發線（如 Seikoh 加碼 B ¥17,900＝fwd 25×、
      Mersen fwd 13×、MEC fwd 20–22×）的直接輸入，缺了就只能用價格代理。

### 2026-07-11 session 產生的（台股漏斗數據源）
- [ ] **註冊 FinMind 免費帳號取得 API token**（finmindtrade.com）→ 放進 GitHub repo Settings → Secrets → `FINMIND_TOKEN`。
  > ⚠️ **2026-07-27 查核：這項的價值比原本以為的小很多，先看完再決定要不要花時間。**
  > 實測證據在 `projects/tw-funnel/data/meta_latest.json:19,37`——最近一次 CI 跑，
  > `TaiwanStockInstitutionalInvestorsBuySell` 與 `TaiwanStockPrice` 兩個 dataset 回 **400**，
  > 訊息是 `"Your level is register. Please update your user level..."`＝**帳號層級不足，指向付費 Sponsor 層**。
  > 也就是說**免費註冊層的 token 大概率仍然解不開這兩項**[推論——未實際拿 token 驗證]。
  > **token 真正買到的是配額**：`projects/tw-funnel/config.py:41` 註記匿名額度低、註冊後 600 req/hr，
  > 而管線常態 ~53 req/日、尖峰 ~107 req/日（`config.py:58-64`）。目前唯一成功的 FinMind 項目是
  > **月營收逐檔（68/69 檔成功**，`meta_latest.json:44-51`）——那也是吃配額最兇的一項。
  > **結論：註冊仍值得做（5 分鐘、保住月營收這條線的配額穩定性），但不要期待它解鎖法人買賣超與價格。**
  > 沒有 token 也不會壞：`projects/tw-funnel/fetch_data.py:655,660,697,732` 都有 TWSE fallback
  > （法人→T86 OpenAPI→RWD 回溯 7 個交易日；價格→STOCK_DAY_ALL；月營收→t187ap05_L 全市場），
  > 兩源皆掛時沿用既有 state（`:688,715`），workflow 每步帶 `|| true`，永遠 exit 0。
  >
  > **照這個順序點（5 分鐘）**：
  > 1. finmindtrade.com 註冊 → 登入後在會員頁複製 API token
  > 2. GitHub → `gutinganthony/KIWI` → Settings → Secrets and variables → Actions → New repository secret
  > 3. Name 填 **`FINMIND_TOKEN`**（大小寫需完全一致——注入點 `.github/workflows/tw-funnel.yml:43`，
  >    程式讀取點 `projects/tw-funnel/fetch_data.py:195-197`，兩邊都用這個名字）
  > 4. Value 貼 token → Add secret
  > 5. 驗收：下一次 tw-funnel 跑完，看 `projects/tw-funnel/data/meta_latest.json` 裡
  >    月營收那項的成功檔數是否維持 68–69/69，且沒有出現配額類錯誤
  > ~~2026-07-27 曾誤報「tw-funnel 停更 3 天」~~ → **2026-07-28 撤回，是誤判、不需要你做任何事**。
  > 當時看到的 `generated_at` 停在 07-24 是**分支基準點造成的假象**（工作分支比 main 舊 12 個 commit）。
  > 合併 main 後實際值是 `2026-07-27T12:46:40Z`，且 07-24(五)→07-27(一) 的空檔正好是週末無台股交易日。
  > **管線一直是好的。**
- [ ] （低優先）雲端 WebFetch 被 403 擋的站 +1：`stockanalysis.com`（TSM 估值頁）。雲端已用 WebSearch 摘要繞過，僅在需要精確 P/B 等單一指標時在 Mac 上手動查。

### 2026-07-10 session 產生的（Polymarket 跟單文查證——優先度低：雲端查證結論已足夠明確〔判定為導流文，不建議執行〕，以下僅在你想二次確認時做）
- [ ] 開 t.me/KreoPolyBot 預覽確認 bot 真偽；開 t.me/polymarketsig、t.me/duanlang1000x、t.me/polyalpha1 查群人數與付費層級（t.me 被擋）
- [ ] 開 polymarketanalytics.com/traders 與 /pricing、docs.kreo.app 核對篩選器/價格/費率與返佣原文（站點被擋，僅搜尋摘要層取得）
- [ ] 登入 X 核對 @waveking1314 粉絲數、開號日、歷史貼文主題（搜尋摘要顯示 ~42.8K 粉、2023-03 開號，未直接核對）

### 2026-07-07 session 產生的（AXW/AIR TRF 研究）
- [ ] **AIR TRF 真實利差序列建檔（文獻查證：DataMine 有免費日檔！）**：註冊 CME DataMine → 拉 AIR TRF 免費 CSV（欄位 `DLY_FUND` FID#10335、`ACC_FUND` #10337）→ 建歷史序列存進 `projects/avi-v5/data/ext/air_trf.csv` → 跑與 `lev_stress_proxy` 的相關性（報告 §8 否證 ②）。備用免費儀表板：snippet.finance「S&P 500 Futures Financing」（2012 迄今）。每週順手記一次 CME 產品頁的近月 bps 與分位數。

---

## ✅ 已完成（做完從上面移下來，保留紀錄）

- [x] ~~本機 curl Polymarket data-api 複核範例錢包精確數字~~ → **2026-07-10 由 poly-observer CI（GitHub Actions runner 不受雲端封鎖）直查完成**，且推翻了媒體快照的「−$311k 爆倉」說法（實為終身 +$176,445、4/12 後停止交易、持倉 $0）。詳見 topics/business/2026-07-10-polymarket-copy-trading-guide-verification.md v1.1。

---

## Update Log
- 2026-07-06 v1.0：建立慣例＋seed JEM 三項＋Pages re-run 站著的一項。搭配 `notify_ops.py` 失敗推播（建議 2）與 CLAUDE.md 開場指標。
- 2026-07-27：清帳一輪（AGENDA 四項逾期任務）。**JEM 兩件**＝找到資料橋失效根因（`update-dashboard.yml` 的 commit glob 只收 `*.csv`、漏掉橋產出的 `.md`）並修好 → 從「你要做」降級為「等合併 main」。**llm-council** ＝逐行原始碼審查完成（212 行全讀＋bundle 與原始碼 diff 一致），判定有條件可安裝，補上三個安裝前條件（Gemini key 洩漏修法、`which gemini codex`、`.gitignore`）。**FinMind** ＝補上精確點擊步驟，並查出免費註冊層對法人買賣超/價格兩個 dataset 仍回 400（付費層才解），下修這項的預期價值。**新增**：tw-funnel 資料停更 3 天（07-24 之後）待你查 Actions。清帳方法論已固化成 `agents/loops/mac-homework-clearing.md`。

### 2026-07-26 session 產生的（海關細碼一次性驗證 SOP）
- [ ] **（可選，5 分鐘）台灣海關細碼出口序列手動拉取**——自動化已確認被驗證碼擋死（不繞過），但**手動一次查詢就能拿全部資料**：
  1. 開 https://portal.sw.nat.gov.tw/APGA/GA30 （綜合查詢）
  2. **進出口別**：勾「出口總值(含復出口)」
  3. **期間**：選「按月」，起 **民國114年6月** → 迄 **民國115年6月**（＝2025/06–2026/06，13 個月）
  4. **貨品**：選「指定貨品號列」，貼入這串（逗號分隔）：
     `851762,900110,854470,854149,847150,847330,854232,848620,848690,847950,848340,850131,853710,853400,841459,841950,850440`
     （光通訊/伺服器/記憶體/半設備/機器人零件/PCB/散熱電源）
  5. **國家(地區)別**：選「合計」
  6. **數值**：勾「金額(美元)」（⚠️「數量」限 11 碼貨品，6 碼查不到——要算隱含 ASP 得改用 11 碼 CCC）
  7. **輸出**：選「下載CSV」
  8. 輸入驗證碼 → 送出 → 存檔
  9. 把 CSV 丟給 Claude session（或放進 repo `data/customs-probe/`）→ 我做細碼 vs 個股月營收的領先性回測
  - 背景與完整逆向工程結果：`topics/business/2026-07-12-taiwan-customs-data-stock-method.md` §6.6
