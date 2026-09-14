# LEARNINGS — 歷任 session 踩坑紀錄

> 每個 session 開始時讀本檔。格式與精簡規則見 `agents/MAINTENANCE.md` §3–§4。
> **本檔只收「環境事實／工具行為／資料格式陷阱」**——判斷類教訓已搬到 `agents/JUDGMENT.md`（§4 換路特例、§5 投資分析 5–15、§5 程式碼三條）。
> 已固化進制度檔的教訓不在此重複。上次精簡：**2026-09-14（39→14 條；判斷類 13 條搬 JUDGMENT，資料源／CI／環境三組合併）**。

## 使用者偏好

- **Jake 要求所有對他的回覆一律用繁體中文**（除非他特別指定其他語言）；程式碼／指令／專有名詞可保留英文。工作中曾漂移成英文被糾正——**不因模型切換或上下文語言漂移而改變**。

## 本環境的基本事實

- [2026-07-07] pip 安裝一律加 `--user`（直接裝撞 debian 系統套件衝突：PyJWT RECORD file not found）。
- [2026-07-07] **Bash 工具的工作目錄會跨呼叫延續**，但不保證——一律用絕對路徑 `/home/user/KIWI/...`，不依賴前一次呼叫留下的 cwd。
- [2026-07-10] **commit 訊息絕不出現字面 `[skip ci]`／`[ci skip]`**（GitHub 對訊息任何位置都會跳過觸發，曾導致 push 後 Actions 毫無反應）。要描述該機制就寫「skip-ci 標記」。
- [2026-07-12] 遠端 session 的整合 token **可以** push 含 `.github/workflows/` 新檔的 commit（實證成功），但 **cron schedule 只在 default branch 生效** → feature branch 上新增的排程 workflow 要明白提醒使用者「合併 main 才會開始跑」。token **沒有 `actions:write`**：不能 dispatch、不能 re-run（回 403）。
- [2026-08-19] side-mount／best-effort 腳本裡凡 import 或呼叫含原生擴充（pyo3/rust/cffi）的套件，**一律 `except BaseException` 並快取結果**——本容器的損壞 `cryptography`（缺 `_cffi_backend`）會拋繼承 `BaseException` 的 `PanicException`，`except Exception` 和 `except ImportError` 都攔不住，而宿主守衛通常也只有 `except Exception`。（2026-09-13 實測：`pypdf` 仍會觸發此 panic，**改用 `pymupdf` 可正常讀 PDF 文字與轉圖**。）
- [2026-09-14] **MCP server 的工具前綴會在 session 之間、甚至 session 中途改變**（本次 Google Drive／Gmail 由 `mcp__Google_Drive__*` 變成 `mcp__<uuid>__*`，舊名被標為已移除、ToolSearch 查不到）。**制度檔引用 MCP 工具只寫功能名（`read_file_content`）＋用途，不寫死前綴**；前綴是 session 級事實。同理 `claude-code-remote` 整組工具的可用性依 surface／連線狀態而定，失敗即回報並用替代方案（要 repo metadata 改用 `mcp__github__*`），不重試第二次。
- [2026-07-07 / 2026-07-15] 自訂 agent（`verifier`／`applier`）**可用**，但剛建立當下不會立即生效（清單刷新後才出現）；清單暫時沒列就退回 `general-purpose` + `agents/TEMPLATES.md` T5。**判斷自訂 agent 能做什麼要讀 `.claude/agents/<name>.md` 正文**，`tools` 欄只列「能碰哪些工具」，不代表「怎麼用它們」。
- [2026-07-26] **WebSearch 有 session 級上限 200 次**，用罄後主對話與 subagent 都不能再搜。一個 session 要跑多個研究任務時，把搜尋密集的工作派給 subagent 並在 prompt 裡限定「最多 N 次搜尋、先列必查清單再搜」；接近上限先把結果落檔。

## 雲端 session vs GitHub Actions runner（**兩個不同環境，封鎖結論不可跨環境沿用**）

- [2026-07-26 / 2026-08-09] **「某站雲端擋」與「某站 runner 擋」是兩件事，每個新環境各自實測一次。**
  - **雲端 session**：agent proxy 對多數外站 CONNECT 403（日本開示站 TDnet／EDINET／irbank／kabutan／minkabu／Yahoo!JP、台股 mops／cnyes／moneydj／goodinfo／TWSE／TPEx、多數財經站；**WebFetch 走另一條 egress 也同樣 403**）。診斷指令：`curl -sS --cacert /root/.ccr/ca-bundle.crt "$HTTPS_PROXY/__agentproxy/status"` 看 recentRelayFailures，比反覆試 curl 快。**雲端唯一穩定的台股量化來源是 FinMind（免 token）。**
  - **Actions runner**：不受雲端 proxy 封鎖。TDnet 一覽頁 `https://www.release.tdnet.info/inbs/I_list_<頁碼 001..>_<YYYYMMDD>.html` 與決算短信 PDF `https://www.release.tdnet.info/inbs/<docID>.pdf` 皆 200（一覽頁要先 `re.split(r'<tr[^>]*>')` 再逐列解析 `<td class="kjTime/kjCode/kjName/kjTitle">`，單一大 regex 跨欄會抓不到）；`disclosure2.edinet-fsa.go.jp` 網頁介面 200 **且不需金鑰**（API 才要）。
  - **規則**：碰到「雲端抓不到」的站，先問「runner 抓不抓得到」，抓得到就寫進資料橋，不要直接丟回 Mac 手動功課。判準：該資料會被重複需要 ＋ runner 可達。
  - **日本標的的財報數字一律以 TDnet 決算短信原文為主源**，不用新聞轉述、不用搜尋 snippet（曾一週抓到 9 份，直接翻轉三檔的觸發判定）。

## 行情資料來源鏈（重定價／價格判定用）

- [2026-08-02 / 2026-08-26] **Yahoo Finance 行情 API 已失效**（`query1`／`query2` 的 chart、quoteSummary、getcrumb 四端點在 runner 上全數 429，換 UA／cookie jar 皆無效），2026-07-26 訂為主源的那條路**不要再用**。現行備援鏈（逐檔實測通過）：
  - **報價（美／日／英／法／台上市＋匯率＋指數）**：CNBC quote cache `https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&symbols=<SYM>`，**需帶桌面 User-Agent**（否則 Akamai 回 Access Denied）。代碼格式：美股裸代碼、日股 `6855.T-JP`、英股 `IQE-GB`、法股 `MRN-FR`、**LPKF 是 `LPK-DE` 不是 `LPKF-DE`**、台股上市 `2408.TW-TW`、匯率 `JPY=`／`KRW=`／`TWD=`、指數 `.N225`／`.KS11`／`.SOX`。**三個坑：逗號批次不支援（靜默回空）、查不到韓股、查不到台股上櫃。** 另：其 `pe` 欄位會在 trailing／forward 之間漂移，`yrhiprice` 對 ADR 是 ADR 口徑（見 JUDGMENT §5-8）。
  - **韓股**：Naver `https://api.finance.naver.com/siseJson.naver?symbol=<6碼>&requestType=1&startTime=YYYYMMDD&endTime=YYYYMMDD&timeframe=day`（單引號需轉雙引號才能 `json.loads`）。
  - **台股（含上櫃）**：FinMind `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id=<code>&start_date=...`（免 key）＋ TPEx `https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes`（含 `Capitals` 可自算市值）雙源交叉。
  - **多日收盤判定（D2）**：CNBC 只給 `last` 與 `previous_day_closing`，週三場執行時亞股的 `last` 已是盤中 ⇒ 單靠 CNBC 算不出 D2。**日股日線走日經 NKD** `https://www.nikkei.com/nkd/company/history/dprice/?scode=<4碼>&ba=1`（`<tr>` 表格第 5 欄＝終値）；**歐股走 stockanalysis 國際 quote HTML 頁** `https://stockanalysis.com/quote/{epa|etr}/<SYM>/history/`（**API 路徑對國際代碼全 400，只有 HTML 頁可用**）；美股走 stockanalysis `/api/symbol/s/<US>/history`。
  - **已知擋死、不要再試**：stooq（JS/PoW）、kabutan（AWS WAF 403/405）、minkabu（403）、WSJ（DataDome）。
  - **開工前先用一檔（例如 MU）打一次主源確認沒被限流**；驗收方式＝三來源回傳的上週基準價 vs repo 記載的上週快照逐檔比對，對得上才往下算。

## CI 與版控陷阱

- [2026-07-10 / 2026-07-27] **任何 CI 會自動 commit 的產物，落地前先估大小**（曾把 36MB 原始 API 回應整包 commit，且每日排程會重複）——大型原始回應在工作區就地消化成摘要，版控只收 <1MB 的產物。**且新增任何資料橋產出路徑後，立刻確認它被某個 `git add` glob 涵蓋**（曾因 glob 只收 `*.csv` 而 `.md` 產出每次隨 runner 回收消失、一天都沒生效）。**驗收句是「repo 裡這個檔有沒有非空的、真實的內容」**——「檔案存在」和「資料存在」是兩件事（曾有檔案整份只有兩行 403 錯誤訊息、沉默失敗三週沒人發現）。
- [2026-07-10] **多個 workflow 寫同一分支時，commit-back 段在 push 前一律 `git pull --rebase origin "${GITHUB_REF_NAME}"`**（曾因裸 push 被拒，整份跑了 14 分鐘的掃描報告隨 runner 回收消失）。
- [2026-07-30] **本 repo 的長命 feature branch PR 絕不夾帶 CI 會寫的路徑**（`*/data/**`、`docs/**`）——main 的排程每天寫好幾次同一批資料檔，逐次解衝突是追不上的跑步機（曾累積 50 個衝突）。正解：把 PR 改成只含程式碼，資料檔完全不碰，合併後由 main 的排程用新程式碼重生。
- [2026-07-30] **高頻（10 分鐘級）輪詢型 workflow 的狀態一律走 `actions/cache`，不進版控**（一天 144 個 commit 會洗掉 git log 並與資料檔衝突）；並設計成「cache 遺失＝只重建基準、不推播」，否則每次 cache 過期就把既有部位全報成新事件（假警報最大來源）。

## 資料格式陷阱

- [2026-07-30] `classify.parse_fills` 的 `_norm_ts` **已把時間正規化成 epoch 秒**（Hyperliquid API 原始欄位是毫秒）——用毫秒運算會讓「最後成交距今」算成兩萬多天、全被淘汰，掃描永遠回 0 個候選。
- [2026-08-17] **同一毫秒內的多筆成交，陣列順序與真實撮合順序無關**（2000 筆成交裡 1991 次相鄰比對有 1799 次對不上，因為大單在薄簿一次撮合拆成數十筆）。用 `startPosition` 類欄位重建部位序列時：批次原子化（同毫秒視為不可分批次，淨變化＝全部 signed delta 加總，對順序不敏感）＋鏈頭回推，且**每個批次獨立回推、不沿用前一批次的累加值**（對強平／ADL／資金費用造成的 fills 外變化才有自癒能力）。驗收＝重建結果的損益加總與原始 `closedPnl` 直接加總分毫不差（見 `projects/hyper-observer/classify.py` 的 `aggregate_round_trips`）。
- `saved_posts.json` 的內文與 label 全是 mojibake（UTF-8 bytes 被當 Latin-1 存）：**中文關鍵字直接搜永遠 0 命中**（會誤報「查無」），要先轉換；也不要用 label 名稱做 select。配方見 `agents/DISPATCH.md` §5。
