# LEARNINGS — 歷任 session 踩坑紀錄

> 每個 session 開始時讀本檔。格式與精簡規則見 agents/MAINTENANCE.md §3–§4。
> 已固化進制度檔的教訓不在此重複。上次精簡：2026-07-15（17→12 條）。

- [2026-07-07] 情境：派 verifier/applier 自訂 agent｜事實：**已確認可用**——.claude/agents/*.md 會被載入，但建立當下不會立即生效（同 session 內隔幾個回合、清單刷新後才出現；剛建立就派用會回「Agent type not found」）｜規則：直接用 subagent_type: verifier / applier；清單暫時沒有就用 general-purpose + agents/TEMPLATES.md T5 代替。
- [2026-07-07] 情境：在 avi-v5 或本環境裝 pip 依賴｜錯誤：`pip install -r requirements.txt` 撞 debian 系統套件衝突（PyJWT RECORD file not found）｜正解：加 `--user`｜規則：本環境 pip 安裝一律用 `pip install --user`。
- [2026-07-07] 情境：Bash 工具跨呼叫的工作目錄會延續｜錯誤：上一個指令 cd 進子目錄後，下一個指令用相對路徑找不到檔案｜正解：一律用絕對路徑（/home/user/KIWI/...）｜規則：Bash 指令不依賴前一次呼叫留下的 cwd。
- [2026-07-10] 情境：查證外部網站與鏈上數據｜事實：WebFetch 可用性**依環境網路政策而定**——某些 session 整體 403（連 example.com 都擋），但 2026-07-15 這個 session 對 github.com／raw.githubusercontent.com WebFetch 正常；agent proxy 對多數外站（polymarket、etherscan、t.me、x.com 等）CONNECT 常 403｜正解：先試 WebFetch，被 403 才退 WebSearch 多來源交叉；數字標「快照非即時」，頁面級驗證回寫 mac-manual-homework｜規則：不要預設全站皆擋、也不要浪費回合硬試已知擋的站；查證派 subagent。
- [2026-07-10] 情境：push 後 GitHub Actions 毫無反應（run 數 0、workflow 未註冊）｜錯誤：commit 訊息的說明文字裡含字面 [skip ci]（描述防迴圈機制），GitHub 對訊息任何位置的 [skip ci]/[ci skip] 都會跳過觸發｜正解：推一個乾淨訊息、且觸及 workflow paths 過濾的 commit 重新觸發｜規則：commit 訊息絕不出現字面 [skip ci]，要描述機制就寫「skip-ci 標記」。
- [2026-07-10] 情境：用 Polymarket activity feed 重建錢包已實現 PnL 做跟單模擬｜錯誤：直接 recovered(SELL+REDEEM)−cost(BUY) 得出 300%+ ROI、100% 勝率的假獲利｜事實：(1) 輸的部位不產生 REDEEM 事件（只有贏了領獎才有）→ 重建 PnL 系統性只看到贏家、嚴重高估；(2) 高頻錢包 activity 1500 筆上限只涵蓋約 12h，視窗內「只結算無買入」的幽靈市場把前期建倉獲利當 cost=0 純利｜正解：只算「買入+出場都在視窗內」的完整 round-trip；截斷+短窗+結算全為贏家時工具要明白拒答（reliable=False）｜規則：凡從交易流重建績效，先問「輸家看得到嗎、視窗夠長嗎」，唯一可信 PnL 來源是 user-pnl-api 曲線。
- [2026-07-10] 情境：使用者明確要求回覆語言｜事實：Jake 要求**所有對他的回覆一律用繁體中文**（除非他特別指定其他語言）；工作中曾漂移成英文被糾正｜正解：每個 session 全程繁體中文回覆，程式碼/指令/專有名詞可保留英文｜規則：對使用者的所有訊息以繁體中文撰寫，不因模型切換或上下文語言漂移。
- [2026-07-10] 情境：CI commit-back 把 36MB 的 leaderboard 原始回應整包 commit 進 repo（且每日排程會重複）｜錯誤：fetch 落地原始 API 回應前沒檢查大小｜正解：大型原始回應在 CI 工作區就地消化成衍生摘要，版控只收 <1MB 的摘要/報告；已發生的肥 commit 在分支未合併前用 reset+重組提交移除｜規則：任何 CI 會自動 commit 的產物，落地前先估大小；>1MB 就先瘦身再入版控。
- [2026-07-10] 情境：兩支 CI workflow 各自 commit-back 到同一分支｜錯誤：hyper 掃描跑 14 分鐘期間 poly-shadow 先推了 commit，hyper 的裸 git push 被拒→整份掃描報告隨 runner 回收消失｜正解：所有 commit-back 段在 push 前加 `git pull --rebase origin "${GITHUB_REF_NAME}"`｜規則：多 workflow 寫同分支，commit-back 一律 rebase-then-push。
- [2026-07-12] 情境：新增 GitHub Actions workflow 檔｜事實：遠端 session 的整合 token **可以**直接 git push 含 .github/workflows/ 新檔的 commit（實證成功，agenda-reminder.yml）；但 cron schedule 只在 default branch 生效｜規則：feature branch 上新增的排程 workflow，要明白提醒使用者「合併 main 才會開始跑」。
- [2026-07-12] 情境：呼叫 claude-code-remote MCP server 的工具（list_repos、add_repo、send_later、create_trigger 等）｜事實：這個 surface 對整組工具不是回「not available for account-owned sessions」（list_repos）就是「requires approval」的連線層卡住（add_repo/send_later，非使用者拒絕、核准流程未觸達使用者、重試無用）｜正解：要 repo metadata 改用 mcp__github__* 工具；排程/推播用檔案落地替代｜規則：claude-code-remote 工具失敗即回報使用者並用替代方案，不重試第二次（本 session 曾見它們一度斷線又重連，可用性依 surface/連線狀態而定）。
- [2026-07-15] 情境：判斷自訂 agent 的能力邊界｜錯誤：research subagent 憑「verifier 工具清單含 Bash」就斷定它無唯讀約束，沒讀 .claude/agents/verifier.md 正文（rule 5 早已禁止改檔/git 狀態）｜正解：agent 的實際約束寫在定義正文/frontmatter，tools 欄只列「能碰哪些工具」，不代表「怎麼用它們」｜規則：判斷自訂 agent 能做什麼，讀 .claude/agents/<name>.md 正文，不要只憑 tools 欄推斷。
