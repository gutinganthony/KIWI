# 模型調度守則（交付項 C）

> 讀者：未來每一個主對話模型（Sonnet 等級為預設）。
> 觸發條件見 CLAUDE.md §4。本檔是操作手冊：照做即可，不需要自行發明調度策略。

## §1 指揮官不下場

主對話（你）是指揮官。指揮官的 context 是全場最貴的資源——它一旦被原文塞滿，
後半場的推理品質就會崩。以下工作**一律派 subagent**，不要自己動手：

| 情境 | 門檻 | 派給誰 |
|---|---|---|
| 找檔案/找程式碼位置/掃 repo | 預估要開 3 個以上檔案，或搜尋範圍不確定 | Explore（唯讀） |
| 讀大檔或黑名單檔案 | CLAUDE.md §2 任一檔 | Explore，或先試 §5 jq 配方 |
| 查網頁/做研究 | 任何需要 >1 個網頁的研究 | general-purpose（可用 WebSearch/WebFetch/browse） |
| 批次改檔 | >3 個檔案的同型修改 | general-purpose 或 applier（見 §2） |
| 驗收產出 | 一律 | verifier（見 §2）或 fresh general-purpose |
| 設計實作計畫 | 涉及 >2 個模組的改動 | Plan |

主對話**可以**自己做的：讀 1–2 個已知路徑的小檔、單檔小修改、跑單一指令、
與使用者對話、彙整 subagent 回報、做最終判斷。

互不相依的派工，**在同一則訊息一次全發**（多個 Agent 呼叫並列），讓它們並行。
已派出去的搜尋不要自己再做一遍。
**並行僅限互相獨立的問題域**（不同檔案/子系統、無 shared state）：唯讀搜尋/研究可放心並行；
但**會寫到同一批檔案的實作或 applier subagent 必須串行**——兩個同時改同檔會互相覆蓋。

**WebSearch 有 session 級上限約 200 次**（主對話＋所有 subagent 共用，用罄就全部不能搜；2026-07-26 實測撞到）：
搜尋密集的研究派給 subagent，prompt 裡限定「最多 N 次搜尋、先列必查清單再搜」；接近上限先把已得結果落檔。
要抓外部資料（行情、開示、鏈上）先看 §8 的實測可達清單，不要盲試。

## §2 可用兵力（本環境實測，2026-07-07）

**內建 agent types**（Agent 工具的 `subagent_type`）：
`Explore`（唯讀搜索）、`general-purpose`（全工具）、`Plan`（規劃）、
`claude-code-guide`（查 Claude Code/API 官方文件）、`claude`（泛用）。

**自訂 agents**（`.claude/agents/*.md`，本 repo 已定義，若 session 的可用清單沒列出就退回用 general-purpose + TEMPLATES.md 模板）：
`verifier`（驗收員，sonnet + 高 effort）、`applier`(批次套用員，haiku + 低 effort)。
剛新增的 agent 定義要隔幾個回合（清單刷新後）才能派，剛建好就派會回「Agent type not found」。
判斷自訂 agent 能做什麼要讀 `.claude/agents/<name>.md` 正文——frontmatter 的 tools 欄只列「能碰哪些工具」，
約束寫在正文（例：verifier 有 Bash，但 rule 5 禁止改檔與動 git 狀態）。

**claude-code-remote MCP 工具**（list_repos／add_repo／send_later／create_trigger 等）：可用性依 surface 與連線狀態而定
（2026-07-12 整組失敗或卡在核准層；2026-09-24 list_repos 實測正常）。失敗一次就回報使用者並改用替代方案
（repo metadata → `mcp__github__*`；排程/推播 → 檔案落地），不重試。

**model 參數**（Agent 工具的 `model`）：`haiku`、`sonnet`、`opus`。
以當下 session 工具 schema 實際列出的為準；不要指定清單外的值。
不指定 = 繼承主對話模型（多數派工就用這個預設）。

**effort**：Agent 工具**沒有**逐次呼叫的 effort 參數。要控制 effort 只有兩條路：
(1) 用自訂 agent（frontmatter 可寫 `effort: low|medium|high|xhigh|max`）；
(2) Workflow 工具的 `agent()` 有 `effort` 選項——但 Workflow 需使用者明確授權（說「用 workflow」或開 ultracode）才能用，預設一律用 Agent 工具。

**model 指派表**：

| 任務性質 | model | 理由 |
|---|---|---|
| 機械套用已解出的 pattern、格式轉換、單檔摘要 | haiku | 便宜快，錯了損失小、易發現 |
| 搜尋定位、一般實作、審查、研究、驗收 | sonnet（或省略=繼承） | 預設主力 |
| 架構決策、連錯兩次的難題、多答案評審、模糊題 | opus | 只在 §6 條件成立時用 |

## §3 派工三件套

每個派工 prompt 必含三件事，缺一件就是壞派工（模板直接抄 agents/TEMPLATES.md）：

1. **目標與動機**：要達成什麼＋為什麼（動機讓 agent 在邊界情況做對取捨）。
2. **驗收條件**：可核對的清單，逐條寫。「做好」「高品質」不是驗收條件；
   「pytest 全過」「回報含 檔案:行號」「每個數字附來源」才是。
3. **回報格式**：明確規定回什麼、多長、什麼結構。

**輸入端衛生（和 §4 產出交接對稱）**：一個 dispatch 只描述「這一個子任務」，不是 session 的歷史。
派工 prompt 只放這個子任務要用的事實與 `檔案:行號`，不要把累積的前置摘要、對話歷史、其他任務的脈絡
整段貼進去。大量既有內容（現成報告、長資料）走檔案交接——寫成檔、prompt 只給路徑。
（反例：見過 42k 字的派工 prompt，九成是貼上的 session 歷史——那會直接汙染被派 agent 的 context。）

**壞派工**：「幫我看看 avi-v5 的訊號邏輯有沒有問題」
**好派工**：「目標：找出 projects/avi-v5/backtest/signals.py 中訊號計算與
projects/avi-v5/config/indicators.yaml 定義不一致之處（動機：dashboard 數字疑似偏高）。
驗收：每個不一致點附 signals.py 行號＋yaml 對應鍵名；沒有不一致也要明說並列出你核對過的函式。
回報：≤15 行，結論先行，格式『結論／證據清單／未檢查範圍』。」

## §4 回報合約（寫進每個派工 prompt）

subagent 的最終訊息是回給指揮官的資料，不是給人看的文章。合約：

- 結論先行，全文 ≤15 行。
- 位置一律 `檔案:行號`，不貼原文；必要引用 ≤3 行。
- 長產物（報告、大 diff、清單 >20 項）寫到檔案，回報只給路徑＋3 行摘要。
  臨時檔寫到 session scratchpad（系統提示有路徑）；要留存的寫進 repo。
- 失敗也照格式回報：做了什麼／卡在哪（附錯誤原文 ≤5 行）／建議下一步。
- 絕不回「整份檔案內容」。指揮官收到超約回報，摘要後立即丟棄原文。

## §5 大檔案配方

**通用規則**：碰任何未知大小的檔案，先 `wc -c 檔名`；>50KB 就不整讀，
用下列配方或派 Explore。JSON 先 `jq 'type' 檔名` + `jq 'keys' 或 '.[0]|keys'` 看形狀。
下列配方都假設在 repo root（/home/user/KIWI）執行；Bash 的 cwd 會跨呼叫延續，
拿不準就把檔名寫成絕對路徑。

**saved_posts.json**（FB 收藏貼文，array of `{fbid, label_values:[{label,value,href}], media, timestamp}`）。
**編碼陷阱**：內文與 label 全是 mojibake（UTF-8 bytes 被當 Latin-1 存），所以
(a) 不要用 label 名稱（如「網址」）做 select——永遠不會命中；
(b) 中文關鍵字直接搜＝永遠 0 命中，會誤報「查無」。英文與網址可直接搜。以下配方已實跑驗證：

```bash
# 筆數
jq 'length' saved_posts.json
# 英文/網址關鍵字搜尋（回 timestamp + 第一個 http 開頭的 value，最多 20 筆）
jq -r '.[] | select([.label_values[]?.value // ""] | join(" ") | test("instagram"; "i"))
  | [(.timestamp // "?"), ([.label_values[]?.value // "" | select(startswith("http"))] | first // "no-url")]
  | @tsv' saved_posts.json | head -20
# 中文關鍵字：先轉成 mojibake 再搜（實測：直接搜 0 命中，轉換後才命中）
KW=$(python3 -c "print('關鍵字'.encode('utf-8').decode('latin-1'))")
jq -r --arg kw "$KW" '.[] | select([.label_values[]?.value // ""] | join(" ") | test($kw))
  | ([.label_values[]?.value // "" | select(startswith("http"))] | first // "no-url")' saved_posts.json | head -20
# 取第 N 筆完整內容（posts 單筆約 1.6KB，安全；此配方不適用 collections！）
jq '.[N]' saved_posts.json
```

**saved_collections.json**（FB 收藏合輯）：**結構與 posts 不同且異質**——只有 5 筆，
但單筆可達 1.4MB（label_values 內有 `{dict,title}`、`{label,timestamp_value}`、`{label,value}` 三種形狀，深層巢狀）。
**絕不可 `jq '.[N]'` 整筆取出**。安全配方（已實跑驗證，輸出 5 行）：

```bash
# 總覽（每筆的時間、id、項目數）
jq -c '.[] | {timestamp: (.timestamp // "?"), fbid: (.fbid // "?"), items: (.label_values | length)}' saved_collections.json
# 再深入：逐層先看 keys/type/大小，確認 <2KB 才取值
jq -r '.[0].label_values[] | [(.label // "?"), (.value|type), ((.value|tostring)|length)] | @tsv' saved_collections.json
```
上面兩招不夠用時派 Explore agent 處理，不要在主對話硬挖。posts 的搜尋配方對本檔無效（結構不同，會靜默回空）。

**docs/history.json**（ACT 指數歷史，平行陣列 d=日期/a=AVI/c=CRI/t=TSI）：

```bash
# 最近 10 天
jq '{d:.d[-10:],a:.a[-10:],c:.c[-10:],t:.t[-10:]}' docs/history.json
# 查特定日期的值（注意：d 陣列有缺日——非交易日不入列，必須做 null 防護）
jq -r '(.d | index("2026-07-01")) as $i
  | if $i == null then "該日無資料（非交易日或缺資料）"
    else {date:.d[$i], avi:.a[$i], cri:.c[$i], tsi:.t[$i]} end' docs/history.json
```

**docs/index.html**（115KB dashboard）：主對話只允許
`Grep`（pattern, path=docs/index.html, output_mode=content, head_limit≤30, -n=true）定位後
`Read` 指定 <100 行範圍。要理解整體結構 → 派 Explore。

**docs/taiwan_data.json**（6KB，可直接 Read）。

## §6 升降級路徑

- **haiku 錯 1 次 → 直接升 sonnet 重派**。不給 haiku 第二次機會，不值得。
- **sonnet 同一子任務連錯 2 次 → 升 opus**，且派工 prompt 必附完整失敗軌跡：
  原始目標、兩次嘗試各做了什麼、實際輸出／錯誤訊息、驗收哪一條不過。
  沒有失敗軌跡的升級是浪費——opus 會把前兩次的錯再犯一遍。
- **opus 解出之後 → 降級套用**：把解法寫成配方（步驟＋一個已驗證的範例），
  之後同型工作用 haiku/sonnet 照配方批次做，並把配方寫進 agents/LEARNINGS.md。
- **批次工作先打樣**：拿 1 件用 sonnet 做，verifier 驗收通過後，
  剩餘的用 haiku 批次套用＋抽查 20%（至少 2 件）。
- **同一件事最多重試兩輪**（初次＋2 次重試＝3 次嘗試）。仍失敗 → 停手，
  按 agents/JUDGMENT.md §3 整理現狀問使用者。繼續硬試只會燒 token 加深錯誤。

## §7 驗證不自驗

寫產出的人不能當自己的驗收員——包括你。分工：

| 產出類型 | 驗法 |
|---|---|
| 檔案落地／完整性 | 主對話直接 Read 抽查關鍵段落（工具輸出不會說謊，這個可以自己做） |
| 內容品質／正確性 | 派 fresh-context verifier：給它驗收條件清單，不給你的結論，讓它獨立核對 |
| 程式碼 | 實跑驗證。**avi-v5 沒有可用的 pytest 套件**（tests/test_cpi_validation.py 是直接執行的驗證腳本，pytest 只會誤收一個名叫 test_event 的 helper 函式）。驗證配方（已實跑驗證）：`cd projects/avi-v5 && pip install -q --user -r requirements.txt`（首次需要，系統 python 沒裝依賴；直接 pip install 會撞 debian 套件衝突，必須 --user）→ `python3 tests/test_cpi_validation.py`（碰過 CPI/訊號邏輯時）＋實跑你改動的腳本。「驗證過」的唯一證據是貼出的執行輸出，不是推測 |
| 高風險判斷（投資結論、刪除、對外發布、改 workflows） | 第二意見：派一個 opus agent，prompt 明說「找出這個結論錯的理由」（對抗立場）；或生 3 個獨立答案、派評審比對選優。二選一，不可跳過 |

**驗收員唯讀鐵律**：任何驗收/審查 subagent 對受驗 checkout 是**唯讀**的——不得改動任何檔案，
也不得動 git index/HEAD/branch。要比對別的 revision 用 `git worktree add /tmp/review-<SHA>`，絕不移動 HEAD。
自訂 verifier agent 已內建此約束（.claude/agents/verifier.md rule 5）；**但退回用 general-purpose 當驗收員時
（T5 模板路徑），那個 agent 帶完整寫入權，必須在 prompt 裡明講唯讀**，否則它可能手滑改壞受驗物、讓驗收失去獨立性。

verifier 的 prompt 只給：驗收條件、受驗檔案路徑、回報格式。
**不要**把你的推理過程或期望結論塞給它——那會把它變成橡皮圖章。

## §8 外部資料可達性（實測事實；自 LEARNINGS 搬入，2026-09-24）

有**兩個執行環境**，封鎖結論**不可互相沿用**——新站要在兩邊各自實測一次：

- **雲端 session（主對話與 subagent）**：流量走 agent proxy，多數外站 CONNECT 回 403。已實測擋：polymarket、etherscan、t.me、x.com；
  日本 TDnet、EDINET、irbank、kabutan、minkabu、finance.yahoo.co.jp、kabupro；台灣 mops、cnyes、moneydj、Yahoo 股市、goodinfo、
  statementdog、TWSE、TPEx；CNBC 報價（2026-08-21）；日經 NKD（2026-09-24 回 000）。WebFetch 走另一條 egress，但日本站實測一樣 403。
  整體可用性依環境網路政策而定（有 session 連 example.com 都 403，也有 session 的 github.com／raw.githubusercontent.com 正常）。
  **FinMind API 可用、免 token**（台股股價/月營收/三大法人/融資券/財報的主要活路）。
  做法：先試 WebFetch，被 403 才退 WebSearch 多來源交叉；數字標「快照非即時」；做不到的頁面級驗證回寫 mac-manual-homework。
  診斷：`curl -sS --cacert /root/.ccr/ca-bundle.crt "$HTTPS_PROXY/__agentproxy/status"` 看 `recentRelayFailures`，
  分辨是政策拒絕還是連線問題——不要一直換 URL 硬試。
- **GitHub Actions runner**：不走雲端 proxy。雲端抓不到的資料，先問「runner 抓不抓得到」；抓得到、且會重複用到，就寫進資料橋
  （範例：`projects/avi-v5/scripts/fetch_jp_disclosures.py`，接在 `update-dashboard.yml` 本來就會跑的 `fetch_backtest_ext.py` 最後，
  所以不用改 workflows），不要直接丟進 Mac 功課清單。資料橋的驗收規則見 LEARNINGS。

**行情資料源鏈（runner 實測，週報重定價用；最後更新 2026-08-26）**。
開工前先拿一檔（如 MU）試打本表來源，確認沒被限流；再用「各來源回傳的上週基準收盤 vs repo 快照，逐檔比對」當正確性驗收，全對才往下算：

| 市場／用途 | 來源 | 注意 |
|---|---|---|
| 報價＋trailing P/E＋市值（美、日、英/法、台上市、匯率、指數） | CNBC quote cache `https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&symbols=<SYM>`（桌面 UA） | 代碼：美股裸代碼、`6855.T-JP`、`IQE-GB`、`MRN-FR`、`2408.TW-TW`、`JPY=`／`KRW=`／`TWD=`／`EUR=`／`GBP=`、`.N225`／`.KS11`／`.SOX`。坑：①逗號批次不支援（靜默回空）②查不到韓股、台股上櫃 ③只有 `last`＋`previous_day_closing` 兩個價格點，週三場亞洲的 `last` 是盤中 → 做不出連兩收盤判定 ④日股 `pe` 忽 trailing 忽 forward ⑤ADR 的 `yrhiprice` 跟母公司口徑不同（SKHY −18% vs 母公司 −44%）→ ADR 的自高回檔改用母公司本地日線算 |
| 日股日線 | 日經 NKD `https://www.nikkei.com/nkd/company/history/dprice/?scode=<4碼>&ba=1` | `<tr>` 第 5 欄＝終値 |
| 歐股日線 | stockanalysis quote **HTML** 頁 `https://stockanalysis.com/quote/<epa 或 etr>/<SYM>/history/` | 同站國際代碼 API `/api/symbol/s/...` 全 400；`lse/`、`lon/` 404 |
| 美股日線 | stockanalysis `/api/symbol/s/<US>/history`（報價另有 `/api/quotes/s/<US>/`） | 只接受美股代碼 |
| 韓股日線 | Naver `https://api.finance.naver.com/siseJson.naver?symbol=<6碼>&requestType=1&startTime=YYYYMMDD&endTime=YYYYMMDD&timeframe=day` | 單引號轉雙引號才能 `json.loads`；12 個月最高價可當韓股與 ADR 的 52 週高 |
| 台股（含上櫃） | FinMind `https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id=<code>&start_date=...`＋TPEx `https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes` | 兩源交叉；TPEx 的 `Capitals`（流通股數）可自算市值 |
| 日本決算短信 | TDnet 一覽 `https://www.release.tdnet.info/inbs/I_list_<001..>_<YYYYMMDD>.html`＋原文 `/inbs/<docID>.pdf` | 一覽頁先 `re.split(r'<tr[^>]*>')` 再逐列解析 td；**class 是多 token（`class="oddnew-M kjCode"`），要按 token 找 `kjTime/kjCode/kjName/kjTitle`**（只認整串會 0 列，2026-08-19～09-24 因此空了五週）；PDF 用 `pip install --user pypdf` 抽字 |
| 日本有報 | `disclosure2.edinet-fsa.go.jp` 網頁介面 | 免金鑰（要金鑰的是 `api.edinet-fsa.go.jp`）；.NET WebForms，先存 HTML 樣本再寫解析器 |

**已知不通，不要再試**：Yahoo Finance API（2026-08-02 起 runner 上 query1／query2／quoteSummary／getcrumb 全回 429）、
Stooq（JS/PoW 挑戰）、kabutan（AWS WAF）、WSJ（DataDome）、minkabu、irbank（runner 也 403）。
注意區分：**yfinance 套件在 runner 仍可用**（每日 dashboard 管線 `fetch_data.py` 靠它，`docs/history.json` 至 2026-09-23 仍有新資料；未測過日韓小型股），
**FRED 在 runner 可用**（`fetch_credit_spreads.py`；雲端 session 對 fred.stlouisfed.org 是 connect_rejected）。
`agents/loops/weekly-repricing-audit.md`、`agents/loops/mac-homework-clearing.md` 已於 2026-09-24 改指向本節。
