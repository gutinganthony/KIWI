# Harness 診斷報告（交付項 A）

> 建立：2026-07-07，Fable 5 制度建立 session。
> 目的：記錄本環境最漏 token、最容易失焦、最容易出錯的前三名問題與具體修法。
> 後續所有制度檔案（CLAUDE.md、agents/DISPATCH.md、agents/JUDGMENT.md）都以本報告為依據。

---

## 問題 1：Session 開始無條件載入 ~50KB 分析檔（最大的 token 漏洞 + 失焦源頭）

**證據**：舊版 CLAUDE.md（備份在 `agents/backups/CLAUDE.md.2026-07-07.bak`）要求
「每次 session 開始，自動讀取以下檔案」：

| 檔案 | 大小 |
|---|---|
| docs/KIWI_INDEX_FRAMEWORK.md | 18.6 KB |
| skills/serenity/SKILL.md | 4.5 KB |
| skills/serenity/watchlist.md | 22.4 KB |
| skills/wavetrend/SKILL.md | 4.2 KB |
| **合計** | **~49.7 KB 中文 ≈ 估 15–25k tokens** |

**影響**：
- 每個 session 都燒這筆 token，即使任務是「加一篇文章到知識庫」這種與選股完全無關的事。
- 比 token 更嚴重的是**失焦**：watchlist 的 22KB 觸發／否證條件會污染注意力，
  弱模型容易把無關任務往選股框架上硬套，或在回答中夾帶不相干的持股觀點。

**修法（已實施於新版 CLAUDE.md §3）**：改為「任務路由表」——
使用者請求匹配到分析類型時才讀對應檔案，其餘任務一律不讀。
預估省下 80% 以上的常駐開銷，且無功能損失（觸發語句原樣保留在路由表）。

---

## 問題 2：巨檔直讀炸 context（最快的單次失敗模式）

**證據**：repo 內有四個弱模型會忍不住直接 Read 或用 grep content 模式輸出的檔案：

| 檔案 | 大小 | 內容 |
|---|---|---|
| saved_collections.json | 2.5 MB | FB 收藏。array，每筆 ~1.6KB：`{fbid, label_values:[{label,value,href}], media, timestamp}` |
| saved_posts.json | 1.0 MB | 同結構 |
| docs/index.html | 115 KB | dashboard 網頁原始碼 |
| docs/history.json | 35 KB | ACT 指數歷史，平行陣列 `{d:日期, a:AVI, c:CRI, t:TSI}` |

一次 Read saved_collections.json 的前 2000 行可能吃掉 50k–100k tokens，
直接摧毀整個 session 的可用 context——而且是在任務剛開始的時候。

**修法（已實施）**：
- CLAUDE.md §2 常駐黑名單（很短，值得常駐）。
- agents/DISPATCH.md §5 提供每個檔案的安全查詢配方（jq 切片／搜尋範例、
  何時改派 Explore subagent）。

---

## 問題 3：主對話下場做批量工作 + 沒有跨 session 記憶（慢性失血）

**證據**：
- (a) 舊制度沒有任何派工紀律：主對話自己讀多檔、掃 repo、查網頁、批次改檔，
  context 被中間過程（檔案原文、搜尋結果、網頁全文）塞滿，
  到任務後半段推理品質明顯下降——這對弱模型的傷害比對強模型大得多。
- (b) 沒有 LEARNINGS 機制：每個 session 重新發現同樣的環境事實
  （遠端環境沒有 gh CLI、git log 被每日 auto-commit 洗版、docs/ 是公開網站），
  並重犯同樣的錯。

**修法（已實施）**：
- agents/DISPATCH.md：指揮官不下場守則 + 派工三件套 + 回報合約 + 升降級路徑。
- agents/LEARNINGS.md：教訓回寫檔（格式與精簡規則見 agents/MAINTENANCE.md），
  很短且常駐載入，讓環境事實只需發現一次。

---

## 額外陷阱（不到前三名，但必須記錄）

1. **docs/ = 公開網站**。`.github/workflows/deploy-pages.yml` 會把整個 `docs/`
   部署到公開 GitHub Pages。任何私人筆記、內部規則、金鑰、個人資料寫進 docs/
   就等於公開發表。制度檔案因此放在 `agents/`，不放 `docs/`。
2. **git log 洗版**。每天 1–2 個 `auto: update dashboard data` commit。
   查人為變更用：`git log --oneline --invert-grep --grep='auto: update dashboard'`
3. **遠端環境沒有 gh CLI**。GitHub 操作一律用 `mcp__github__*` MCP 工具
   （先用 ToolSearch 載入 schema）。
4. **gstack SessionStart hook** 在全新 container 會重新 clone + build（約 1–2 分鐘）。
   這是時間成本不是 token 成本（輸出已被 harness 持久化到檔案），不需修。
5. **投資分析的編造風險**。這個 repo 的產出影響真金白銀的決策；弱模型跑分析時
   最大的品質風險不是 token 而是編造數字。判準見 agents/JUDGMENT.md §5。
