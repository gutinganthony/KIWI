# agents/loops — Loop 憲章

> 什麼是 loop、為什麼要寫憲章：`topics/technology/2026-07-27-loop-engineering.md`

## 用法

每份憲章是一段**可直接貼進 Claude Code 的完整指令**。兩種跑法：

- 有 `/goal` 指令時：`/goal` + 貼上憲章正文（Claude 會自己續跑到驗收條件全過為止）
- 沒有 `/goal` 時：直接把憲章正文貼進對話（一樣能跑，差別是要人工起頭、不會自動續輪）

**每份憲章都自帶一個狀態檔路徑。** 那個檔是 loop 的記憶——loop 每輪先讀它，
所以中斷後可以精準接手，不會重做已完成的項目。狀態檔不要手動刪。

## 現有憲章

| 憲章 | 型態 | 狀態檔 | 解決什麼 |
|---|---|---|---|
| `weekly-repricing-audit.md` | `/goal` | `projects/avi-v5/data/loop-state/repricing.md` | 週報價格誤植（07-22 曾 9 檔錯值並產出假觸發判定） |
| `mac-homework-clearing.md` | `/goal` | `topics/technology/mac-manual-homework.md` 本身 | 手動功課積欠（>14 天＝月度自檢的執行力警訊） |

## 寫新憲章的鐵律（KIWI 專用，違反就不要寫）

1. **GOAL 必須是「某個檔案／某個決策被更新」，不是「產出一份分析」。**
   理由：月度自檢第 7 題「深掘檔數 ÷ 實際執行動作數 >5:1＝研究代償發作」。
   loop 會讓研究產能暴增，目標寫成「分析」只會更快產出沒人執行的研究。
2. **必須寫死搜尋預算**（每項最多 N 次 WebSearch）。WebSearch 有 session 級 200 次上限，曾用罄卡死收尾。
3. **驗收條件必須可機械核對**。「查證過」「品質好」不是驗收條件；
   「每個數字附 API 回應時間戳」「每個連結回 HTTP 200」才是。
4. **模糊題不要寫成 loop。** 需要 Jake 本人做價值判斷的（要不要買、部位多大、策略方向）
   一律走 "needs me" 出口，不要讓 loop 代決。
