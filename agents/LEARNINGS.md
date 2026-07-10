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
