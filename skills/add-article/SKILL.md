# Add Article — 收錄文章/連結到知識庫

用途：把一個 URL 或一段內容收錄成 KIWI 知識庫條目。這是最高頻的固定流程，照步驟做，
不要即興改流程。

## 步驟

**1. 取得內容**
- 用 /browse 或 WebFetch 開 URL。**只抽正文**：標題、作者、日期、核心論點與數據；
  忽略導覽列、廣告、推薦閱讀、留言（省 token 原則，抽取時就過濾，不要全文塞進 context）。
- 站被 403 擋 → 按慣例 append 到 topics/technology/mac-manual-homework.md 待辦區，
  告知使用者，本次先用使用者提供的內容或摘要做。

**2. 寫條目** — 檔名 `topics/<主題>/YYYY-MM-DD-<英文slug>.md`，格式：

```markdown
---
title: 中文標題（可含原文標題）
url: 原始連結（本地產出寫 local）
topic: business|technology|health|science|society-culture|other
tags: [3-6 個小寫英文 tag]
last_updated: YYYY-MM-DD
---

# 標題

## 一句話結論
（這篇對 Jake 的核心價值是什麼）

## 關鍵論點
（3-8 條，數字保留原文精度並附出處段落）

## 與 KIWI 既有觀點的關聯（可選）
（與 watchlist/框架/舊條目一致或矛盾之處；矛盾要明寫，不要調和）

## 原文
連結 + 取用日期
```

**3. 三處索引同步（一處都不能漏——漂移就是這樣來的）**
- 該主題 `INDEX.md`：頂部加一列（Date | Title | Tags）。
- `README.md` RECENT_ENTRIES 區塊：加到最上面，**保持恰好 5 列**（擠掉最舊的）。
- `README.md` ALL_ENTRIES 區塊：按日期插入；Topics 計數表該主題 +1。

**4. 驗收（宣告完成前）**
- 原始連結實際開過（步驟 1 就做了）。
- 三處索引 read-back：新列的相對路徑 `test -f` 存在。
- 與既有條目矛盾時已在條目內明寫。

## 備註

- 一次收錄多篇：逐篇走完 2→3 再做下一篇，最後跑一次 skills/kiwi-lint/SKILL.md 檢查 A。
- 純個人筆記（非外部文章）也用本格式，url 寫 local。
