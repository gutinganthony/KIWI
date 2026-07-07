# LEARNINGS — 歷任 session 踩坑紀錄

> 每個 session 開始時讀本檔。格式與精簡規則見 agents/MAINTENANCE.md §3–§4。
> 已固化進制度檔的教訓不在此重複。上次精簡：尚未（2026-07-07 建檔）。

- [2026-07-07] 情境：想查 repo 可見性｜錯誤：呼叫 mcp__Claude_Code_Remote__list_repos｜正解：account-owned session 不支援（回 "not available for account-owned sessions"）｜規則：這類 session 不要用 list_repos；要 repo metadata 用 mcp__github__* 工具。
- [2026-07-07] 情境：想派 verifier/applier 自訂 agent｜事實：agent 清單在 session 開始時快照——本 session 中途建立 .claude/agents/verifier.md 後立即派用，回錯「Agent type 'verifier' not found」；全新 session 是否載入尚未驗證｜規則：第一次要派用時，看 Agent 工具可用類型清單——有 verifier 就直接用，並把本條改成「已確認可用」；沒有就用 general-purpose + agents/TEMPLATES.md T5 代替，並把本條改成「已確認不可用（日期）」。
- [2026-07-07] 情境：想指定 subagent 的 effort｜事實：Agent 工具沒有 effort 參數（只有 model）；effort 只能寫在自訂 agent frontmatter 或 Workflow 的 agent() 選項｜規則：不要在 Agent 呼叫塞 effort，會 InputValidationError。
- [2026-07-07] 情境：Workflow 工具很強大想常用｜事實：Workflow 需要使用者明確授權（說「用 workflow」／開 ultracode）才可以用｜規則：預設一律用 Agent 工具派工；使用者沒開口就不要呼叫 Workflow。
- [2026-07-07] 情境：在 avi-v5 裝依賴｜錯誤：`pip install -r requirements.txt` 撞 debian 系統套件衝突（PyJWT RECORD file not found）｜正解：加 `--user`｜規則：本環境 pip 安裝一律用 `pip install --user`。
- [2026-07-07] 情境：Bash 工具跨呼叫的工作目錄會延續｜錯誤：上一個指令 cd 進子目錄後，下一個指令用相對路徑找不到檔案｜正解：一律用絕對路徑（/home/user/KIWI/...）｜規則：Bash 指令不依賴前一次呼叫留下的 cwd。
