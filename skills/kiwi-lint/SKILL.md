# KIWI Lint — 知識庫體檢

用途：定期掃知識庫的四類腐化。**產出報告，不自動修**；修復經使用者同意後派 subagent 執行。
頻率：每月一次，或大量收錄之後。歷史教訓：2026-07-08 首跑發現 README 索引漂移一個月
（30+ 篇未登記、計數三處全錯）。

## 檢查 A：索引一致性（檔案 vs INDEX vs README 三處）

```bash
# 每個主題的實際檔案數（頂層 .md，不含 INDEX.md）
for d in topics/*/; do n=$(ls "$d" | grep -v INDEX.md | grep -c '\.md$'); echo "$d $n"; done
```
逐項核對：(1) 上述數字 = README Topics 表的計數；(2) 每檔都在該主題 INDEX.md 有列；
(3) 有日期前綴的檔案都在 README 的 ALL_ENTRIES 區塊；(4) RECENT_ENTRIES = 全庫最新 5 篇。

## 檢查 B：斷鏈（索引指向不存在的檔案）

```bash
# 對每個 INDEX.md（在其目錄內執行語意）與 README.md（repo root 語意）：
grep -o '](\./[^)]*\.md)' <索引檔> | sed 's/](\.\///;s/)//' | while read f; do
  test -f "<基準目錄>/$f" || echo "BROKEN: $f"; done
```

## 檢查 C：過期主張（投資庫特有，最重要）

掃 topics/business/ 中含**觸發價、估值快照、目標價**的檔案，列出 `last_updated`
距今超過 60 天者。這些數字寫下時是對的，現在可能已失效（例：06-26 才發生過
「全複合體 melt-up → 十張 scorecard 全數降級」）。
產出：檔名 + 過期天數 + 內含的關鍵數字類型。是否重驗由使用者決定。

## 檢查 D：矛盾主張（派 subagent 做，主對話只收結論）

派一個 Explore agent：比對 skills/serenity/watchlist.md 的現役觸發/否證條件 vs
最近 30 天 topics/business/ 內同 ticker 的結論，回報「同一檔標的、兩處判斷相反」清單
（例：scorecard 說觀望、watchlist 還掛觸發買進）。只回報 檔案:行號 與矛盾點，不引長文。

## 回報格式

```
KIWI Lint 報告（日期）
A 索引：一致 / N 處漂移（清單）
B 斷鏈：無 / N 條（清單）
C 過期主張：N 檔（檔名+天數）
D 矛盾：無 / N 組（ticker + 兩處出處）
建議動作：≤5 條，附預估工作量
```
