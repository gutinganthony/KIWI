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

### 站著的（長期）
- [ ] **GitHub Pages deploy 卡住時去按 Re-run failed jobs**（自 2026-07-03 起偶發，Pages 後端暫時性錯誤、非程式問題）。
  - 🔒 **真・needs me 的理由**：重跑 workflow 需要 `actions:write`，整合 token 無此權限（Claude 代按會 403）。**這條永遠不會自動化。**
  - ✅ 現在已有失敗推播（`deploy-pages.yml` → Telegram），收到通知再去按即可，不用自己巡邏網站。
  - 位置：Actions 分頁 → Deploy Dashboard to GitHub Pages → Re-run failed jobs；或等下次自動 deploy。

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
- [x] ~~**Yahoo!ファイナンス 6855 時系列**：判別 7/6 單日跌幅是 -10.4% 還是 -14.3%~~
  → **2026-07-28 結案：兩個都不對，正解 −3.74%。** 不必你查——資料早就在 repo 裡
  （`projects/avi-v5/data/ext/JEM.csv`，由 runner 用 yfinance 抓的 6855.T 交易所日線，
  ticker 對照見 `projects/avi-v5/scripts/fetch_backtest_ext.py:34`）。**詳見下方「已完成」區的完整數字與後續影響。**
  - 三項全過 → JEM 首批建倉區 ¥6,400–6,800 紀律恢復有效（第二關 8/7 Q1 財報再定第二批）。

### 2026-07-12 session 產生的（LFI 第四錶）
- [x] ~~**上線驗證 LFI 第四錶**~~ → **2026-07-28 結案：有真讀數，不是「--」**。
  不必開網頁——`docs/index.html` 內嵌資料是 `"lfi":{"score":17.9`（`docs/history.json` 最新日期 2026-07-27）。第四錶正常運作。
- [x] ~~**上線驗證「連續維持天數」標注**~~ → **2026-07-28 結案：欄位有正常帶出**，
  實際值 `days_ge_80":0`、`days_ge_90":0`、`days_ge_95":0`。**「0」是正確的，不是壞掉**——
  ⚠️ **因為 LFI 已從 07-10 的 84.8 崩到 17.9**，連續維持天數當然歸零。
  當初寫這條時的預期（「X 應該 ≥1 且逐日遞增」）建立在 LFI 續留 ≥80 的假設上，該假設已被推翻。
  **這個 −67 點的擺盪本身可能值得看一眼**（判讀依據在 `topics/business/2026-07-12-act-fourth-meter-lfi-and-serenity-throttle-validation.md`，
  不在 `docs/KIWI_INDEX_FRAMEWORK.md`——後者查無 LFI）。
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
- [ ] **日股估值三檔複核**（quote 站被雲端 403，全為搜尋摘要層）：HDS 6324 預估 PER ~152/PBR 8.3、THK 6481 PER ~36.7、IKO 6480 現價 ~¥2,041（7/14）。
  > 🔄 **2026-07-28 部分自動化**：三檔已加進價格資料橋
  > （`projects/avi-v5/scripts/fetch_backtest_ext.py` 的 TICKERS，共 15 檔）→ 下次 dashboard 更新後
  > `projects/avi-v5/data/ext/HarmonicDrive.csv`、`THK.csv`、`IKO.csv` 會自動落地（2019 迄今日線）。
  > 落地路徑已被 `update-dashboard.yml` 的 `git add ...data/ext/*.csv` 涵蓋 ✅。
  > **這只解掉「現價」那一問**（IKO ¥2,041 可自動複核）；**預估 PER/PBR 仍未解**——
  > 需走 quoteSummary + crumb 路徑（`agents/LEARNINGS.md` 2026-07-26），且 Yahoo 的 forwardPE
  > 對日本小型股嚴重失真、不可直接採信。**PER/PBR 這一半仍留在你的清單上。**
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

### ~~2026-07-10 session 產生的（Polymarket 跟單文查證）~~ → **2026-07-28 整組作廢**
> 三項（t.me bot 真偽／polymarketanalytics 站點核對／X 帳號粉絲數）**全部刪除，不必做**。
> 理由：前提已消失——這些是「二次確認」用的，而決策早已定讞
> （判定為導流文、不建議執行；且 `topics/business/2026-07-10-polymarket-copy-trading-guide-verification.md` v1.1
> 已由 poly-observer CI 直查推翻媒體的「−$311k 爆倉」說法）。
> **沒有任何待決動作依賴這三項的答案**，做完也不會改變任何事。

### 2026-07-07 session 產生的（AXW/AIR TRF 研究）
- [ ] **AIR TRF 真實利差序列建檔（文獻查證：DataMine 有免費日檔！）**：註冊 CME DataMine → 拉 AIR TRF 免費 CSV（欄位 `DLY_FUND` FID#10335、`ACC_FUND` #10337）→ 建歷史序列存進 `projects/avi-v5/data/ext/air_trf.csv` → 跑與 `lev_stress_proxy` 的相關性（報告 §8 否證 ②）。備用免費儀表板：snippet.finance「S&P 500 Futures Financing」（2012 迄今）。每週順手記一次 CME 產品頁的近月 bps 與分位數。

---

## ✅ 已完成（做完從上面移下來，保留紀錄）

- [x] ~~本機 curl Polymarket data-api 複核範例錢包精確數字~~ → **2026-07-10 由 poly-observer CI（GitHub Actions runner 不受雲端封鎖）直查完成**，且推翻了媒體快照的「−$311k 爆倉」說法（實為終身 +$176,445、4/12 後停止交易、持倉 $0）。詳見 topics/business/2026-07-10-polymarket-copy-trading-guide-verification.md v1.1。

- [x] ~~**JEM 6855 7/6 單日跌幅裁決（-10.4% vs -14.3%）**~~ → **2026-07-28 結案：兩個都不對。**
  **正解：7/6 收盤 ¥7,460、單日 −3.74%。** 證據＝`projects/avi-v5/data/ext/JEM.csv`
  （runner 用 yfinance 抓的 6855.T 交易所日線，2019-01-04 起共 1,833 個交易日；
  ticker 對照 `projects/avi-v5/scripts/fetch_backtest_ext.py:34`）。7 月初完整日線：

  | 日期 | 收盤 | 單日 |
  |---|---|---|
  | 7/1 | ¥8,280 | — |
  | 7/2 | ¥7,520 | **−9.18%**（當週最大單日跌幅） |
  | 7/3 | ¥7,750 | +3.06% |
  | **7/6** | **¥7,460** | **−3.74%** |
  | 7/7 | ¥6,970 | −6.57% |
  | 7/8 | ¥6,770 | −2.87% |
  | 7/9 | ¥6,930 | +2.36% |
  | 7/10 | ¥7,330 | +5.77% |

  **那兩個矛盾數字是怎麼來的**：−14.3% ＝ 拿 `watchlist.md` 記的 ¥6,640 去比 7/3 的 ¥7,750
  （＝比較了非相鄰快照）；−10.4% 則兩邊都對不上。**7 月初沒有任何一天跌超過 10%。**

  ⚠️ **後續影響（需要你看一眼）**：`skills/serenity/watchlist.md:44` 記的
  「¥6,640（7/6 收，單日 -10.4%）**✅ 首批建倉區**」**價格是錯的**——
  真實 7/6 收盤 ¥7,460 **高於首批區 ¥6,400–6,800 上緣 9.7%**，當天根本不在建倉區內。
  **不影響目前決策**（7/24 現價 ¥6,280 由交易所級 API 取得、確實已跌破下緣），
  但那條歷史註記與「✅ 首批建倉區」標記應更正。已於 watchlist 就地標註。

---

## Update Log
- 2026-07-06 v1.0：建立慣例＋seed JEM 三項＋Pages re-run 站著的一項。搭配 `notify_ops.py` 失敗推播（建議 2）與 CLAUDE.md 開場指標。
- **2026-07-28：第一次用 `agents/loops/mac-homework-clearing.md` 憲章跑清帳，本輪處理 8 項。**
  A（已自動化）1：日股估值三檔加進價格橋（`fetch_backtest_ext.py` TICKERS 15 檔），只解現價、PER/PBR 仍留清單。
  B（已直接完成）3：JEM 7/6 跌幅裁決（正解 −3.74%，兩個選項都不對，且揪出 watchlist 價格誤植）、
  LFI 第四錶有真讀數 17.9、連續維持天數欄位正常（值為 0 是對的，因 LFI 從 84.8 崩到 17.9）。
  C（作廢）3：Polymarket 三項二次確認全刪（決策已定讞，沒有動作依賴它們）。
  D（真 needs me）1：Pages re-run（需 actions:write，永遠不會自動化）。
  **關鍵發現：三項「等你做」的功課其實資料早就在 repo 裡**——沒人去看而已。
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
