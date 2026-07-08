---
title: Claude Code 使用行為分析 × 高效使用者對照 × 升級計畫
url: local
topic: technology
tags: [claude-code, workflow, usage-analysis, skills, mcp, automation, meta]
last_updated: 2026-07-08
---

# Claude Code 使用行為分析 × 高效使用者對照 × 升級計畫

> 產出：2026-07-08 session。方法：挖掘本 repo 的行為化石層（124 個人為 commit、15 個 PR、
> 45+ 篇 topics、6 支 workflows、交接檔與慣例檔），交叉一個 fresh-context 研究 agent
> 對 2026 年官方/社群高效 pattern 的查證報告（18 條，來源全數標註）。

## §0 資料基礎與限制（先講誠實的）

- **看得到**：這個 repo 的全部 git 歷史（2026-05 起）、PR、檔案結構、workflows、commit 訊息。
- **看不到**：你在本機 Mac 或其他 repo 的 session 逐字稿、純對話沒留痕的 session、實際工時與 token 用量。
- 因此「使用比例」以 **commit 為單位**估計，不是工時；純聊天型 session 被低估。
- 2026-04 的 14 篇 topics 是回填（commit 史從 5 月開始），四月行為只能從檔案內容側寫。

## §1 各類型工作使用比例（2026-05-01 ～ 07-08，124 個人為 commit）

| 工作類型 | 佔比 | 代表證據 |
|---|---|---|
| **Serenity 個股/供應鏈研究**（deep-dive、scorecard、獵殺、重定價、週報） | **~28%** | 06-12 單日 8 連發、06-26 HBM 系列 6 連發、07-06 Kokusai/TSE/JEM |
| **量化工程 avi-v5**（TSI/CRI 指標、回測引擎、dashboard、資料源） | **~27%** | 06-06~08 回測衝刺 14 commits、CRI v2 回測、台灣指標面板 |
| **自動化維運**（workflows、警報、部署、CI 權限除錯） | **~15%** | 週報 workflow 三代（PR #8→#12→#13）、Pages 卡住、numpy 2.x、OIDC |
| **總經/市場框架研究**（supercycle、Julius Baer、roadmap、倉位節奏） | **~11%** | memory-supercycle 五部曲、post-selloff roadmap |
| **制度/meta**（CLAUDE.md、skills 框架、sync、handoff、本次七件套） | **~6%** | 06-10 auto-load、07-06 handoff、07-08 制度 PR #15 |
| **創業/個人專案**（Redefine Fund、Yuni、sleep、AI copilot） | **~6%** | 06-03~05 Redefine 四連發 |
| **知識庫收錄**（讀物摘要入庫） | **~6%** | High Growth Handbook、BI outlook、Julius Baer |

**時間演變**：5 月＝基建期（dashboard 管線＋警報）→ 6 月上旬＝回測工程衝刺 →
6 月中起＝Serenity 深掘成為主流、維運稅固定 ~15% → 7 月＝節奏加速（7 天 32 commits）
且制度投資遞增。**你的重心已從「建工具」轉為「用工具做研究」，維運與制度是固定稅。**

## §2 行為慣性（從 commit 模式讀出來的你）

1. **深掘連發型**：單日對同一主題 6–9 個 commit（06-12、06-26），長 session 大交付。
2. **WIP→finalize 兩段式**：會標 DRAFT、"pending research agents"、"finalize locally with live data"——已有拆階段直覺。
3. **已自發使用 power-user 行為**（這點超前多數使用者）：adversarial review（BI blueprint v1.1）、
   獨立數字驗證（07-06「10/12 pass」）、research agents 並行、session 交接檔、排程週報、SessionStart hook。
4. **雲端/本機分工是被 403 逼出來的**：yfinance 只能 Mac 跑 → fetch_data.py + CSV；
   日本財經站被擋 → mac-manual-homework 慣例。這是你目前最大的結構性摩擦。
5. **維運稅會反覆發生且教訓散落**：Pages 靜默卡住、numpy 2.x 凍結、NaN、Actions 權限三連踩——
   每次都修好，但經驗只存在 commit 訊息裡（現在有 agents/LEARNINGS.md 可沉澱）。
6. **統計嚴謹度事後補課**：回測引擎先跑，再補 BH-FDR／out-of-sample／Wilson bounds（三次返工）——
   品質意識強，但屬「先做再修方法論」型。
7. **雙軌操作**：web session 走 PR（#2~#15、merge 後刪分支，衛生良好）；本機直推 main。

## §3 對照 2026 高效使用者 pattern（研究 agent 查證版）

### 你已經在前段班的（不用改）

| Pattern | 你的對應物 |
|---|---|
| CLAUDE.md 極簡化＋按需載入（官方核心原則） | 2026-07-08 路由式 CLAUDE.md + agents/ 七件套 |
| 「錯第二次就寫回去」 | agents/LEARNINGS.md + MAINTENANCE 協議 |
| Subagent 隔離調查與大量讀檔 | agents/DISPATCH.md 指揮官守則 |
| Hooks 自動化 | SessionStart 裝 gstack、PreToolUse 擋 skill |
| Actions cron 排程 | 6 支生產 workflows |
| 大任務 handoff | 交接檔（07-06）＋ /context-save |
| fresh-context 驗收、對抗審查 | 你 07-06 已自發做；制度已寫進 DISPATCH §7 |

### 缺口與升級計畫（按對你的價值排序）

**1.（最高槓桿）金融數據源 skill/MCP 化——消掉「雲端查不到現價」的結構性摩擦** ★★
現況：重定價靠 WebSearch snippet 或回 Mac 跑 yfinance；DRAFT→Mac finalize 的迴圈一半是為了這個。
社群主流解：alpha-vantage-mcp、yfinance-mcp、investor-agent（awesome-mcp-servers 收錄；
Anthropic 官方無金融 MCP 推薦清單——查無）。
**但注意「MCP 堆疊症」反面訊號**（每個 MCP 常駐吃 context）：更省的做法是 **API key + 腳本 + skill**——
你已有 FinMind（台股）與 FRED key，補一個美股/日股 API（Alpha Vantage 免費層），
寫成 `projects/avi-v5/scripts/quote.py` ＋一個 `/reprice` skill，週報與臨時查價共用。
先在雲端 session 實測 API endpoint 是否過得了 proxy，再決定 skill 或 MCP。

**2. 知識庫補「lint」這一步（Karpathy LLM Wiki 範式的缺角）** ★★
你的 topics/INDEX 結構與該範式同構（raw=原文連結、wiki=摘要頁、CLAUDE.md=schema），
ingest 和 query 都有了，缺 **lint**：定期掃「矛盾主張（scorecard 說 buy、watchlist 已否證）、
過期估值快照、孤兒頁、INDEX/README 失聯」。對投資庫來說，過期主張有真實成本。
做法：一個 `/kiwi-lint` skill（月跑一次，或掛 Actions monthly cron），產出問題清單不自動改。

**3. 收錄文章流程 skill 化＋省 token 抽取** ★
「貼連結→摘要→入 topics→更新兩份索引」是你最高頻的固定流程，符合官方「同一指示第三次就 skill 化」判準。
順手抄 obsidian-skills（40.2k stars）的 **defuddle**（網頁→乾淨 markdown，省大量 token）。
給有副作用的 skill（週報、部署類）加 `disable-model-invocation: true`，只准你手動觸發。

**4. 週報 workflow 與 skill 合一** ★
官方支援 Actions 的 prompt 直接填 `/skill-name`——目前 serenity-weekly.yml 的指令與
skills/serenity/weekly-screen.md 是兩份定義，會漂移（你已為此踩過三代 workflow）。
統一成「workflow 只負責 cron + 呼叫 skill」。改 workflows 前先問過自己（CLAUDE.md §0 規則）。

**5. 給常設 subagent 開持久記憶** ★
官方 sub-agents 支援 frontmatter `memory: project`：讓 `.claude/agents/verifier.md` 跨 session
累積驗收經驗（「這 repo 的測試怎麼跑、上次抓到什麼」）。一行設定的事。

**6. Mac 端用 Claude in Chrome 清手動功課** ★
mac-manual-homework 裡的「403 站、需登入的頁面」在本機可用 `claude --chrome` 半自動化
（共用你已登入的 Chrome，遇 CAPTCHA 交還給你）。雲端做不到的事從「你手動」變「Claude 在你電腦上做」。
注意官方警告：按需開，不要常駐。

**7. 行為習慣兩條（零成本）**
- **糾正兩次就 /clear 重開**：官方明訂「乾淨 session＋更好的 prompt 幾乎總是贏過堆滿糾正的長 session」。
- **工程衝刺前先 spec/plan**：你的回測引擎三次方法論返工是教材案例；gstack 已有 /spec 與 /plan-eng-review，
  「一句話能描述 diff 就跳過 plan，否則先 plan」。

### 反面訊號對照（你要避免的）

- **CLAUDE.md 長回去**：制度已設 120 行警戒線——守住它。
- **MCP 堆疊症**：接新 MCP 前先問「skill+script 能不能解」；接了也只在需要的 session 用。
- **在被污染的 session 反覆糾正**：見上面第 7 條。

## §4 來源

研究 agent 查證報告（2026-07-08）：官方 code.claude.com（best-practices / memory / skills /
sub-agents / hooks-guide / routines / github-actions / chrome / mcp）全文直接驗證；
Karpathy LLM Wiki gist（2026-04-04）、kepano/obsidian-skills、punkpeye/awesome-mcp-servers 直接驗證；
Boris Cherny 工作流與 Simon Willison skills 文章因 proxy 403 改以 ≥3 獨立來源交叉核實。
Anthropic 官方金融 MCP 推薦：查無。
