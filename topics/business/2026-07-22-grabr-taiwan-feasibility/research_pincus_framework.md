# Mark Pincus「創新預算 / Proven-Better-New」框架研究報告

## 0. 先講結論：inno.tw 原文取不到

- `https://inno.tw/teardowns/pincus-innovation-budget/` 本身、`r.jina.ai` 代理、`web.archive.org` 快取均嘗試，**全部失敗**（環境層級 WebFetch 對所有網址一律回 403，連 en.wikipedia.org 都拿不到，判定是這個 session 的 WebFetch 工具系統性失效，非該網址特有問題）。
- 因此本報告**無法**逐字核對 inno.tw 這篇文章原文用詞、判準表述順序、或作者自己下的案例。以下內容是用 WebSearch（AI 摘要式搜尋，非逐字爬取）拼出的框架，來源是 Pincus 本人多篇訪談／Podcast 的轉載摘要，以及一篇中文轉譯（Labsology）。
- **inno.tw 文章標題用「innovation budget（創新預算）」一詞，但這個詞在其他任何來源（Lenny's Newsletter、fs.blog、Inc.com、Zynga 相關報導）中都沒有查到 Pincus 本人使用這個確切用語。** 高度懷疑「創新預算」是 inno.tw 自己對 Pincus「Proven-Better-New」框架的中文編輯框架／比喻（把「New 只能佔一小部分」的紀律，比喻成一筆有限的預算），但**這只是推論，未經原文證實**。

---

## 1. 核心命題（一句話）

> 把產品拆成「已驗證（Proven）／變得更好（Better）／全新（New）」三層，**New 只能有一個、且必須被隔離**，這樣才能在它失敗時精準診斷是哪裡壞了，而不會拖垮整個產品。

（來源：多篇 Pincus 訪談摘要之綜合轉述，非 inno.tw 原文逐字句——信心等級：中高，多個獨立來源交叉一致）

---

## 2. 具體判準／規則（逐條，標明來源類型）

1. **三層定義**（其他來源—Pincus 訪談轉載一致）
   - *Proven*：拆解「在你的目標受眾與情境下，已經被驗證有效」的東西——不是抽象地看某個模式有沒有效，而是針對你的確切受眾/使用情境去解構。
   - *Better*：找出小幅、明確的改進。
   - *New*：真正未經驗證的新賭注。

2. **Better 的判準是「10 個裡面 10 個目標用戶都毫不猶豫說『是，這樣比較好』」**（其他來源—多篇轉載一致提到此量化門檻）。常見的 Better 是很樸素的東西：價格、少一個下載步驟、移除摩擦。

3. **區分 Better 與 New 的判準**（其他來源—轉載摘要）：
   - 如果一個改動**要求用戶學習新行為**，或**任何人會遲疑這是不是真的比較好**，那它就不是 Better，而是 New。
   - 換言之，「New」不是你自己主觀認定的創新，而是「用上述兩個測試篩掉 Better 之後剩下的東西」。

4. **New 只能有一個、且必須被隔離（isolate the innovation）**（其他來源—多篇轉載一致，此為框架的核心論證）：
   - 論證邏輯：大多數創業者把所有假設打包進同一個產品，一旦失敗無法診斷哪個環節壞了；把「New」隔離出來，失敗時才知道要怪誰。
   - 沒有查到 inno.tw 或 Pincus 本人明確說「只能創新『幾個』變數」的具體數字（例如 1 個或最多幾個）；查到的說法都是「the one new thing」「isolate the innovation」，語氣上是**盡量收斂到單一變數**，但沒有查到一個像「創新代幣（innovation tokens）只給 3 個」那樣的明確配額數字。→ **標記為「查無精確配額規則」**。

5. **順序不可跳過**（其他來源—Labsology 中文轉譯）：必須先精熟 Proven，才能判斷什麼是 Better；必須先確認 Better 的假設，才能騰出空間做 New 的實驗。三步驟不能打亂順序或跳過。

6. **「All new fails」心法**（其他來源—多篇轉載一致）：這是 Zynga 內部的口號/信念，帶統計論證色彩（例如引用「App Store 上一年所有新 App 100% 都失敗」這類說法）。這不是反對創新，而是反過來論證「New 必須被隔離、且要有失敗的心理預期」的理由。

7. **本能 vs 想法（instincts vs ideas）**（其他來源—多篇轉載一致）：Pincus 認為「本能」（創業者對市場/用戶的直覺）約 95% 是對的，但「想法」（把本能具體轉譯成產品設計方案的嘗試）約 75% 是錯的。這個落差就是大部分產品失敗發生的地方——暗示 PBN 框架的作用，是幫本能「正確」的部分，用紀律去約束「想法」容易出錯的轉譯過程。

（以上第 2–7 條均為「其他來源」，不是 inno.tw 原文逐字句；第 1 條的三層架構亦同。**沒有任何一條是我方推論外加的新規則**——第 4 條末尾的「查無精確配額」是我方對搜尋結果空缺的誠實標記，不是我編造的判準。）

---

## 3. 檢查表／步驟／評分方法

- 沒有查到 inno.tw 或 Pincus 原始出處提供正式的「打勾檢查表」格式。查到的是**三步驟流程**（可視為簡化檢查表）：
  1. 研究/拆解已經在你的目標受眾中被驗證的東西（Proven）。
  2. 針對其中找出「10/10 目標用戶會毫不猶豫同意更好」的具體改進（Better）。
  3. 只留一個「連你自己都預期可能失敗」的全新元素，把它隔離出來測試（New）。
- 執行工具（其他來源—轉載提及）：Zynga 內部建了「failure machines（失敗機器）」——在寫程式碼之前，用簡單系統對真實用戶快速測試上百個概念構想，篩出方向。
- 「Minimum Idea State」一詞在轉載摘要中出現過（意指用這個框架更快建立起對想法的信念/驗證），但沒有查到具體操作定義，**標記為查無細節**。

---

## 4. 案例

- **Zynga Poker**（其他來源—多篇一致）：Proven＝線上撲克本身早已存在且被驗證；Better＝做到免下載、容易上手（10/10 用戶會同意「更方便」）；New＝把它變成「社交」的——這是唯一的新賭注，也是 Zynga 的第一個爆款起點。
- **整體成績**（其他來源）：Zynga 頭 10 款主力遊戲中有 8 款成為重大成功（含 FarmVille 等），常被用來佐證 PBN 框架的命中率。
- inno.tw 文章本身舉了什麼案例、有沒有額外案例（例如是否討論過「複製商業模式到新市場」的案例）——**查無，取不到原文**。

---

## 5. 套用到「複製既有商業模式到新市場」（Grabr → 台灣）

**原文／相關來源均未直接涵蓋「跨國複製商業模式」這個應用場景**——所有查到的訪談與轉載都是在講「單一產品/單一市場內」的功能與設計創新，不是「把整套模式搬到新國家」。以下是**我方延伸推論**，非任何來源主張：

- **Proven**＝Grabr（或該類跨境代購媒合）在原市場已被驗證的核心機制與單位經濟：媒合誘因結構、信任機制、抽成/定價模式。移植到台灣前，要先拆解清楚「在原市場，究竟是哪個具體機制被驗證有效」，而不是含糊地說「這個模式在國外有效」。
- **Better** ＝在台灣情境下，哪些改動是「10 個台灣目標用戶會毫不猶豫同意更好」的——例如比既有集運/代購管道更快、更便宜、媒合品質更好——且**不需要用戶學習全新行為**。這些改動仍歸類為 Better，不算創新賭注。
- **New** ＝真正未經驗證、且台灣情境特有的那一個變數——例如某種信任/金流機制、或鎖定的特定利基族群/場景。依框架紀律，**應該只挑一個當作「New」去隔離測試**，其餘（法規、金流、物流、既有競爭者格局、關務認知等）能歸進 Proven 或 Better 的就不要混進 New，避免「跨國搬模式」把一堆真正未知的變數（法規環境、付款習慣、信任文化）都打包成一個大賭注——這正是 PBN 論證所警告的「打包假設、失敗時無法診斷」的失敗模式。
- **注意**：把整個「搬到新市場」本身當作唯一的 New，可能是偷懶的分類——框架的精神要求你把新市場裡「哪個環節具體沒被驗證」拆解到更細的顆粒度，而不是籠統地把「台灣」當成一個新變數。

---

## 6. 鄰近框架：innovation tokens（Dan McKinley,《Choose Boring Technology》）

- **與 inno.tw 該文的關係：未查到證實引用**——沒有搜尋結果顯示 inno.tw 這篇文章有提到或引用 McKinley。以下純粹是任務要求核對的「鄰近框架」，**不代表 Pincus 或 inno.tw 有使用**。
- 內容（其他來源，McKinley 原文相關轉載，信心中高）：一個組織/專案一開始大約只有 3 個「innovation tokens（創新代幣）」，每次採用一項需要陡峭學習曲線的新技術/新概念就花掉一個代幣；供應量長期固定，其餘技術選擇應該用「無聊但成熟」的方案。核心比喻同樣是「創新配額有限，要挑對地方花」，與 PBN「New 要收斂、要隔離」精神相通，但 McKinley 談的是工程技術選型，Pincus 談的是產品設計決策，領域不同。

---

## 來源清單

**查無（嘗試但失敗）：**
- https://inno.tw/teardowns/pincus-innovation-budget/（WebFetch 403；r.jina.ai 代理 403；web.archive.org 無法存取）
- https://www.lennysnewsletter.com/p/the-common-pattern-behind-successful （WebFetch 403）
- https://fs.blog/knowledge-project-podcast/mark-pincus/ （WebFetch 403）
- https://www.inc.com/chris-morris/mark-pincus-12-7-billion-company-formula-for-startup-ideas/91376014 （WebFetch 403）
- https://finance.biggo.com/news/eed8ad303ac0d027 （WebFetch 403）
- https://nextbigwhat.com/master-product-ideas-mark-pincuss-winning-framework-explained/ （WebFetch 403）
- https://www.sourcery.vc/p/breaking-mark-pincus-on-how-to-build （WebFetch 403）
- https://labsology.com/insight/...Pincus...3步成功心法/ （WebFetch 403）
- https://en.wikipedia.org/wiki/Mark_Pincus （WebFetch 403，用於確認 WebFetch 是否系統性失效）

**其他來源（透過 WebSearch AI 摘要取得，非逐字全文，以下為本報告內容依據）：**
- Lenny's Newsletter podcast — "The hidden pattern behind successful products | Mark Pincus (Founder of Zynga)" https://www.lennysnewsletter.com/p/the-common-pattern-behind-successful
- fs.blog Knowledge Project — "Proven, Better, New: Mark Pincus on the Rules of Innovation" https://fs.blog/knowledge-project-podcast/mark-pincus/
- Inc.com — "Mark Pincus Built a $12.7 Billion Company. His Formula for Startup Ideas Starts With 2 Simple Lists" https://www.inc.com/chris-morris/mark-pincus-12-7-billion-company-formula-for-startup-ideas/91376014
- BigGo Finance — "Mark Pincus: 'A B+ Is the Enemy of an A'..." https://finance.biggo.com/news/eed8ad303ac0d027
- nextbigwhat.com — "Master Product Ideas: Mark Pincus's Winning Framework Explained" https://nextbigwhat.com/master-product-ideas-mark-pincuss-winning-framework-explained/
- sourcery.vc — "BREAKING: Mark Pincus on How to Build Billion-Dollar Products" https://www.sourcery.vc/p/breaking-mark-pincus-on-how-to-build
- Labsology 法博思品牌顧問公司（中文轉譯）— "別再從零發明產品！Pincus 的「驗證後做更好」3 步成功心法" https://labsology.com/insight/...
- mcfunley.com — Dan McKinley, "Choose Boring Technology" https://mcfunley.com/choose-boring-technology（McKinley 原始出處，鄰近框架）
- 另有多個轉載/摘要來源（20VC substack、James Altucher Show、cryptobriefing.com、startuparchive.org、podchemy.com、dealroom.co、batlab.substack.com 等）在 WebSearch 摘要中被列為交叉印證來源，內容與上列一致，未逐一 WebFetch。

**搜尋次數：WebSearch 共 15 次（已達硬上限）；WebFetch 嘗試 9 次，全部 403 失敗。**
