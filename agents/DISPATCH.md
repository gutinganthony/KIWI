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

## §2 可用兵力（本環境實測，2026-07-07）

**內建 agent types**（Agent 工具的 `subagent_type`）：
`Explore`（唯讀搜索）、`general-purpose`（全工具）、`Plan`（規劃）、
`claude-code-guide`（查 Claude Code/API 官方文件）、`claude`（泛用）。

**自訂 agents**（`.claude/agents/*.md`，本 repo 已定義，若 session 的可用清單沒列出就退回用 general-purpose + TEMPLATES.md 模板）：
`verifier`（驗收員，sonnet + 高 effort）、`applier`(批次套用員，haiku + 低 effort)。

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

**壞派工**：「幫我看看 avi-v5 的訊號邏輯有沒有問題」
**好派工**：「目標：找出 projects/avi-v5/backtest/signals.py 中訊號計算與
config/indicators.yaml 定義不一致之處（動機：dashboard 數字疑似偏高）。
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

**saved_posts.json / saved_collections.json**（FB 收藏，array of
`{fbid, label_values:[{label,value,href}], media, timestamp}`，label 有「網址」「說明文字」等）：

```bash
# 筆數
jq 'length' saved_posts.json
# 關鍵字搜尋（回 timestamp + 網址，最多 20 筆；中文關鍵字可直接用）
jq -r '.[] | select([.label_values[]?.value // ""] | join(" ") | test("關鍵字"; "i"))
  | [(.timestamp // "?"), ([.label_values[]? | select(.label=="網址") | .value] | first // "no-url")]
  | @tsv' saved_posts.json | head -20
# 取第 N 筆完整內容（單筆約 1.6KB，安全）
jq '.[N]' saved_posts.json
```

**docs/history.json**（ACT 指數歷史，平行陣列 d=日期/a=AVI/c=CRI/t=TSI）：

```bash
# 最近 10 天
jq '{d:.d[-10:],a:.a[-10:],c:.c[-10:],t:.t[-10:]}' docs/history.json
# 查特定日期的值：先找 index，再取值
jq -r '(.d | index("2026-07-01")) as $i | {date:.d[$i], avi:.a[$i], cri:.c[$i], tsi:.t[$i]}' docs/history.json
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
| 程式碼 | 跑測試（avi-v5：`cd projects/avi-v5 && python -m pytest tests/ -x -q`）或實跑腳本。「測試過」的唯一證據是貼出的執行輸出，不是推測 |
| 高風險判斷（投資結論、刪除、對外發布、改 workflows） | 第二意見：派一個 opus agent，prompt 明說「找出這個結論錯的理由」（對抗立場）；或生 3 個獨立答案、派評審比對選優。二選一，不可跳過 |

verifier 的 prompt 只給：驗收條件、受驗檔案路徑、回報格式。
**不要**把你的推理過程或期望結論塞給它——那會把它變成橡皮圖章。
