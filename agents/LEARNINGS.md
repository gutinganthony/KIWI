# LEARNINGS — 歷任 session 踩坑紀錄

> 每個 session 開始時讀本檔。格式與精簡規則見 agents/MAINTENANCE.md §3–§4。
> 已固化進制度檔的教訓不在此重複。上次精簡：尚未（2026-07-07 建檔）。

- [2026-07-07] 情境：想查 repo 可見性｜錯誤：呼叫 mcp__Claude_Code_Remote__list_repos｜正解：account-owned session 不支援（回 "not available for account-owned sessions"）｜規則：這類 session 不要用 list_repos；要 repo metadata 用 mcp__github__* 工具。
- [2026-07-07] 情境：想派 verifier/applier 自訂 agent｜事實：**已確認可用**——.claude/agents/*.md 會被載入，但建立當下不會立即生效（同 session 內隔了幾個回合、清單刷新後才出現；剛建立就派用會回「Agent type not found」）｜規則：直接用 subagent_type: verifier / applier；若清單暫時沒有，用 general-purpose + agents/TEMPLATES.md T5 代替即可。
- [2026-07-07] 情境：想指定 subagent 的 effort｜事實：Agent 工具沒有 effort 參數（只有 model）；effort 只能寫在自訂 agent frontmatter 或 Workflow 的 agent() 選項｜規則：不要在 Agent 呼叫塞 effort，會 InputValidationError。
- [2026-07-07] 情境：Workflow 工具很強大想常用｜事實：Workflow 需要使用者明確授權（說「用 workflow」／開 ultracode）才可以用｜規則：預設一律用 Agent 工具派工；使用者沒開口就不要呼叫 Workflow。
- [2026-07-07] 情境：在 avi-v5 裝依賴｜錯誤：`pip install -r requirements.txt` 撞 debian 系統套件衝突（PyJWT RECORD file not found）｜正解：加 `--user`｜規則：本環境 pip 安裝一律用 `pip install --user`。
- [2026-07-07] 情境：Bash 工具跨呼叫的工作目錄會延續｜錯誤：上一個指令 cd 進子目錄後，下一個指令用相對路徑找不到檔案｜正解：一律用絕對路徑（/home/user/KIWI/...）｜規則：Bash 指令不依賴前一次呼叫留下的 cwd。
- [2026-07-10] 情境：查證外部網站與鏈上數據｜事實：本環境 WebFetch 整體 403（連 example.com 都擋），agent proxy 對大量外站（polymarket.com、data-api、etherscan、t.me、x.com、medium.com 等）CONNECT 一律 403，只有 WebSearch（搜尋索引快照）可用｜正解：網路查證派 subagent 用 WebSearch 多來源交叉，數字標註「快照非即時」，頁面級驗證回寫 mac-manual-homework 待辦｜規則：不要浪費回合對外站試 WebFetch/curl，直接用 WebSearch。
- [2026-07-10] 情境：push 後 GitHub Actions 毫無反應（run 數 0、workflow 未註冊）｜錯誤：commit 訊息的「說明文字」裡含字面 [skip ci]（描述防迴圈機制），GitHub 對訊息任何位置的 [skip ci]/[ci skip] 都會跳過觸發｜正解：推一個乾淨訊息、且觸及 workflow paths 過濾的 commit 重新觸發｜規則：commit 訊息絕不出現字面 [skip ci]，要描述機制就寫「skip-ci 標記」。
- [2026-07-10] 情境：用 Polymarket activity feed 重建錢包已實現 PnL 做跟單模擬｜錯誤：直接 recovered(SELL+REDEEM)−cost(BUY) 得出 300%+ ROI、100% 勝率的假獲利｜事實：(1) 輸的部位不產生 REDEEM 事件（只有贏了領獎才有）→ 重建 PnL 系統性只看到贏家、嚴重高估；(2) 高頻錢包 activity 1500 筆上限只涵蓋約 12h，視窗內「只結算無買入」的幽靈市場把前期建倉的獲利當 cost=0 純利｜正解：只算「買入+出場都在視窗內」的完整 round-trip；截斷+短窗+結算全為贏家時工具要明白拒答（reliable=False），不可印獲利數字｜規則：凡從交易流重建績效，先問「輸家看得到嗎、視窗夠長嗎」，唯一可信的 PnL 來源是 user-pnl-api 曲線。
- [2026-07-10] 情境：使用者明確要求回覆語言｜事實：Jake 要求**所有對他的回覆一律用繁體中文**（除非他特別指定其他語言）；工作中曾漂移成英文回覆被糾正｜正解：每個 session 全程繁體中文回覆，程式碼/指令/專有名詞可保留英文｜規則：對使用者的所有訊息以繁體中文撰寫，不得因模型切換或上下文語言而漂移。
- [2026-07-10] 情境：CI commit-back 把 36MB 的 leaderboard 原始回應整包 commit 進 repo（且每日排程會重複發生）｜錯誤：fetch 落地原始 API 回應前沒檢查大小｜正解：大型原始回應在 CI 工作區就地消化成衍生摘要，版控只收 <1MB 的摘要/報告；已發生的肥 commit 在分支未合併前用 reset+重組提交移除｜規則：任何 CI 會自動 commit 的產物，落地前先估大小；>1MB 就先瘦身再入版控。
- [2026-07-10] 情境：兩支 CI workflow 各自 commit-back 到同一分支｜錯誤：hyper 掃描跑 14 分鐘期間 poly-shadow 先推了 commit，hyper 的裸 git push 被拒→整份掃描報告隨 runner 回收消失｜正解：所有 commit-back 段在 push 前加 `git pull --rebase origin "${GITHUB_REF_NAME}"`｜規則：多 workflow 寫同分支，commit-back 一律 rebase-then-push。
- [2026-07-12] 情境：新增 GitHub Actions workflow 檔｜事實：遠端 session 的整合 token **可以**直接 git push 含 .github/workflows/ 新檔的 commit（實證成功，agenda-reminder.yml）；但 cron schedule 只在 default branch 生效｜規則：feature branch 上新增的排程 workflow，要明白提醒使用者「合併 main 才會開始跑」。
- [2026-07-12] 情境：派 subagent 研究 session scope 外的第三方 GitHub repo｜錯誤：派工 prompt 只寫「用 WebSearch」，沒有明文禁止 mcp__github__* 搜尋類工具，subagent 用 GitHub code search 跨 scope 查了外部 repo（查公開資料、使用者點名目標，無實害，但違反 session 的 repo scope 守則）｜正解：外部 repo 研究的派工 prompt 必須明寫「只准 WebSearch，禁用 mcp__github__* 工具」｜規則：凡研究不在 session scope 的 repo，派工時逐字加上工具白名單。
- [2026-07-12] 情境：想把 scope 外的 repo 拉進 session 審查程式碼｜事實：add_repo 需要使用者在介面核准，本 surface 回「MCP tool call requires approval」且核准流程未觸達使用者（重試一次仍同）｜規則：add_repo 失敗＝改走 WebSearch 快照研究＋請使用者貼關鍵檔案，不要繞過權限模型直接 clone。
- [2026-07-12] 情境：使用者要求盯進度/新增任務的機制｜事實：已建 AGENDA.md（root）＝使用者任務板，格式 `- [ ] YYYY-MM-DD | 標題 | 摘要`，週六 08:15 TST 由 agenda-reminder.yml 推播；每月第一個週六附自檢清單｜規則：涉及使用者目標/待辦的更新優先寫 AGENDA.md（📌 任務區），不要另建新機制。
