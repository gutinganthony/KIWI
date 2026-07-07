# KIWI — Claude 作業守則

> 本檔只放「每個 session 都用得到」的規則與路由。細節放 `agents/` 下的制度檔，按需讀取。
> 若本檔引用的檔案不存在：代表該制度未完成，忽略該引用即可，不要自己補寫該檔。
> 改本檔前先讀 `agents/MAINTENANCE.md`。舊版備份在 `agents/backups/CLAUDE.md.2026-07-07.bak`。

## 0. 環境事實（直接信，不要重新查證）

- 遠端 session **沒有 `gh` CLI**：GitHub 操作一律用 `mcp__github__*` MCP 工具（先用 ToolSearch 載入 schema）。
- **`docs/` 會被整包部署到公開 GitHub Pages**（見 .github/workflows/deploy-pages.yml）。私人筆記、內部規則、金鑰、個人資料嚴禁寫入 docs/。
- git log 每天被 `auto: update dashboard data` commit 洗版。查人為變更：`git log --oneline --invert-grep --grep='auto: update dashboard'`
- `.github/workflows/` 是真實生產管線（每日 dashboard 更新、每日 Telegram/LINE 警報、每週六 Serenity 週報、Pages 部署）。**改 workflows 前先問使用者。**
- session 開始時，若 `agents/LEARNINGS.md` 存在就讀它（很短，是歷任 session 的踩坑紀錄）。除此之外**不要**在 session 開始預讀任何分析檔——見 §3 路由。

## 1. gstack（必要，全域安裝）

動手前驗證：`test -d ~/.claude/skills/gstack/bin && echo GSTACK_OK || echo GSTACK_MISSING`

若 GSTACK_MISSING：停止工作，請使用者安裝：
`git clone --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup --team`，然後重啟工具。
（遠端 session 的 SessionStart hook 通常已自動裝好。）不要跳過、不要繞過 gstack 錯誤。
gstack 檔案路徑一律用 `~/.claude/skills/gstack/...`（全域路徑）。網頁瀏覽一律用 /browse。

## 2. 大檔案黑名單（絕不直接 Read，絕不用 grep 的 content 模式輸出內容）

| 檔案 | 大小 | 安全用法 |
|---|---|---|
| saved_collections.json | 2.5 MB | jq 配方見 agents/DISPATCH.md §5 |
| saved_posts.json | 1.0 MB | 同上 |
| docs/index.html | 115 KB | 只能派 subagent 讀；主對話最多 Read 指定小範圍（<100 行） |
| docs/history.json | 35 KB | jq 切片，例：`jq '{d:.d[-10:],a:.a[-10:],c:.c[-10:],t:.t[-10:]}' docs/history.json` |

違反此表＝context 直接炸掉、任務失敗。需要更複雜的查詢 → agents/DISPATCH.md §5。

## 3. 任務路由（按需載入）

先判斷使用者要什麼，**只讀**對應那一列的檔案：

| 請求類型 | 讀這些檔 |
|---|---|
| 「用 Serenity 框架分析 $TICKER」 | skills/serenity/SKILL.md + skills/serenity/watchlist.md |
| 「跑 Serenity 週報」 | skills/serenity/weekly-screen.md + 上列兩檔 |
| ACT / AVI / CRI / TSI 指數判讀 | docs/KIWI_INDEX_FRAMEWORK.md |
| 「用 WaveTrend 分析 $TICKER」 | skills/wavetrend/SKILL.md |
| 三合一分析（Serenity + WaveTrend + ACT） | 上列全部 |
| 新增文章/連結到知識庫 | README.md 看格式 → 寫入 topics/<主題>/ → 更新該主題 INDEX.md 與 README.md 的索引表 |
| 改 avi-v5 程式 | projects/avi-v5/ARCHITECTURE.md（改 CPI 相關再加 CPI_ARCHITECTURE.md） |

其餘任務一律不讀上表檔案。新增分析模組：在 `skills/` 下建資料夾寫 SKILL.md，然後在上表加一列。

## 4. 派工與模型調度

符合以下任一條件，**先讀 `agents/DISPATCH.md` 再動手**：

- 要讀 3 個以上檔案，或碰任何 §2 黑名單檔案
- 要掃 repo、查網頁、做研究、批次改檔（>3 檔）
- 要派 subagent、選 model、或驗收產出（含驗收自己的）

核心原則：主對話是指揮官——大量讀取與批次工作派給 subagent，主對話只保留結論與 `檔案:行號`。

## 5. 品質與判斷

- 宣告「完成」之前：跑 `agents/JUDGMENT.md` §2 的完成檢查表。
- 連續出錯、想升級模型、想中斷問使用者、懷疑方向錯了：查 `agents/JUDGMENT.md` 對應章節，按判準行動。
- 踩到新坑：按 `agents/MAINTENANCE.md` 的格式把教訓寫進 `agents/LEARNINGS.md`。
- 派工用的 prompt 模板（搜尋/實作/重構/研究/審查）：抄 `agents/TEMPLATES.md`，填空後使用。

## 6. Skill routing

使用者請求匹配到 skill 時用 Skill 工具呼叫；拿不準就呼叫。重點對照：

- 產品想法/腦力激盪 → /office-hours ・ 策略/範圍 → /plan-ceo-review ・ 架構 → /plan-eng-review
- 設計系統/計畫審查 → /design-consultation 或 /plan-design-review ・ 完整審查管線 → /autoplan
- Bug/錯誤 → /investigate ・ QA/測試網站行為 → /qa 或 /qa-only ・ Code review → /review
- 視覺打磨 → /design-review ・ 出貨/部署/PR → /ship 或 /land-and-deploy
- 存進度 → /context-save ・ 恢復上下文 → /context-restore

## 7. 制度檔案索引（agents/）

| 檔案 | 內容 | 什麼時候讀 |
|---|---|---|
| DIAGNOSIS.md | harness 三大漏洞診斷 | 想了解制度為何這樣設計時 |
| DISPATCH.md | 模型調度守則＋大檔案配方 | §4 條件觸發時（最常用） |
| JUDGMENT.md | 判斷力 rubric：升級/完成/求助/轉向/品質底線 | 卡住或要宣告完成時 |
| TEMPLATES.md | 派工 prompt 模板五份 | 每次派 subagent 前 |
| MAINTENANCE.md | 制度檔案的修改權限與教訓回寫格式 | 要改制度檔或寫 LEARNINGS 前 |
| LEARNINGS.md | 歷任 session 踩坑紀錄 | 每個 session 開始 |
| LETTER.md | 制度建立 session 給未來 session 的信 | 接手大任務或制度出現退化跡象時 |
