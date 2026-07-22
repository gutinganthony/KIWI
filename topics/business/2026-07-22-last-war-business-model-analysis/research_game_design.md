# 《Last War: Survival》遊戲架構研究：表層極簡 vs 底層 4X/SLG 深度

**研究維度**：遊戲架構設計（本檔為主對話彙整用的分維度報告之一）
**查詢日期**：2026-07-22
**工具限制**：僅用 WebSearch / WebFetch，禁用 mcp__github__*

---

## 0. 方法論與可信度說明（請先讀，關係到下文怎麼判讀）

本環境對外站 WebFetch 幾乎全滅：24 次 WebFetch 嘗試中 **23 次被 403**，只有 1 次（GitHub Gist 一篇玩家半年心得長文）成功直接讀取全文。因此本報告絕大多數機制描述，是透過 WebSearch 對目標頁面做**摘要式檢索**取得，而非逐字讀取原始頁面全文。這代表：

- 具體數字（價格、留存率、營收）我盡量保留「原文引用」而非改寫，並註明出處，但仍有被摘要工具二次轉述失真的風險。
- 凡是重要數字，若不同來源有出入，我**並列呈現**而不是挑一個當「正確答案」，並標註「不確定：口徑不一」。
- 凡是只查到單一來源、無法交叉驗證的機制描述，標註「不確定：僅單一來源」。
- 完全查不到的項目，直接寫「查無」，不用訓練記憶填補。
- 全文用【事實】【推論】【不確定/軼事】標記關鍵判斷的性質。

---

## 1. 核心循環：新手期 → 中期 → 後期

### 1.1 廣告小遊戲在正式遊戲裡的真實定位

《Last War: Survival》的買量廣告以「拉門/數字合併」跑酷小遊戲聞名（玩家操控隊伍左右移動、撞數字門讓兵力翻倍、消滅殭屍潮），廣告中甚至找來演員 Antony Starr（《黑袍糾察隊》Homelander）客串。這類廣告长期被拿來當「掛羊頭賣狗肉」手遊廣告的代表案例，收錄進專門吐槽手遊廣告詐欺的網站 fakeadgames.com（Fake Ad Games 博物館，把廣告裡的假玩法重製成可玩網頁，並用 1–10 分的「Lie Score」評分廣告的欺騙程度）【事實，來源見來源清單】。

但值得注意的是，多個來源指出 Last War 的廣告手法**不是典型的純詐欺型 bait-and-switch**：廣告裡的拉門/數字合併玩法，在正式遊戲最初幾分鐘內**確實存在**，開場體驗與廣告基本一致；差別在於這段玩法會在教學階段之後迅速淡出、被基地經營取代，屬於「循序過渡」而非「掉包」（來源：Gamigion 產業分析）。另一方面，社群端也有反面聲音：X（Twitter）上有 Community Note 指出廣告影片內容與實際遊戲不符【不確定：兩種說法並存，可能取決於評測者玩到多深】。

真正關鍵的量化證據來自玩家社群整理：據 Reddit 社群共識彙整（經 Tenteck 網站整理）與 Ruthless Reviews 的實測評論，**廣告裡那種跑酷/數字門玩法，在正式遊戲中大約只占玩家實際遊玩內容的 20%，其餘約 80% 都是基地經營/資源管理**類玩法【不確定：這是玩家估計比例，非官方數據，但兩個獨立來源趨同】。換言之：**它不是主玩法，是入口誘餌兼新手教學殼，正式定位是點綴性的側玩法（Frontline Breakthrough 模式）**。

### 1.2 中期骨架：COK-like 4X 迴圈

多個來源（Baidu百科、Oreate AI Blog 等）將 Last War 的核心迴圈形容為「COK-like」（Clash of Kings 類）：採集資源、升級建築、生產部隊、透過戰役攻略地圖清野怪/拓展領土【事實，多來源一致】。三項核心資源為金幣（coin）、糧食（food）、鐵（iron）【事實】。

英雄養成是第二條主線：透過「酒館」（Tavern）用招募券抽卡（本質是課金誘因很強的 gacha 系統），稀有度分 SR（一般，主要靠日常任務/常駐招募取得）→ SSR（史詩，紫色，數值與技能明顯優於 SR）→ UR（傳說，最強一階）三階【事實，多篇攻略站一致】；不同資料對「英雄總數」說法不一，有來源說 30 名英雄，也有攻略資料庫聲稱收錄「200+ 英雄」（可能含重複計算的進化/晉升型態或資料庫本身持續擴充）【不確定：口徑不一】。

有一個特別的「軟保底」機制：「Wall of Honor」榮譽牆，在英雄專屬建築升到 20 級後解鎖，SSR 英雄晉升 UR 時，之前投入該英雄的所有已消耗碎片（含專屬碎片與通用紫色碎片）會全額退還進玩家背包——這不是傳統抽卡「抽 N 次保底出貨」的機制，而是「長期投入不會歸零、可轉換到下一階段」的沉沒成本安撫設計【事實，來源：Last War Vault】。

另有來源（單一，未交叉驗證）提到後期戰役關卡會混入 Roguelike 元素、類似《吸血鬼倖存者》的塔防/王關卡玩法，配合殭屍圍城的世界觀【不確定：僅單一來源(疑似轉述自中文產業文章)，未能交叉驗證細節】。

### 1.3 戰鬥的「自動化」本質

不論是野外清圖還是主線戰役，核心戰鬥流程被多篇獨立評論一致形容為「選好隊伍、排好陣型，然後看 AI 自動打」——玩家在戰鬥當下幾乎沒有即時操作介入的空間，決策點集中在**戰前配置**（帶哪些英雄、什麼陣型、什麼裝備/無人機組合），而非戰鬥過程本身【事實，多篇評論摘要一致；細節見第 6 節】。

### 1.4 後期：社交/伺服器層的接管

進入中後期，遊戲的挑戰重心會從「打野怪」轉移到聯盟政治、伺服器排名、跨服戰爭——這部分細節在第 3 節社交架構完整展開。簡言之：**表面上是一個殭屍題材動作遊戲，中期開始它其實已經是一個以「聯盟」為單位的社交/政治/資源調度遊戲**。

---

## 2. 進度牆：時間閘、資源缺口、加速道具經濟

### 2.1 建築/科技時間牆如何從「秒」膨脹到「兩週」

早期建築升級只需數秒到數分鐘；但到了後期，例如將某建築從 24 級升到 25 級，**耗時可達約兩週**，總部（HQ）等級的升級等待動輒數天到數週【事實，來源：多篇建築攻略站一致】。

「建造隊列」（construction queue）是核心的稀缺資源：玩家一開始只有有限的隊列數量（可同時進行的建築工程數），需額外購買才能解鎖更多隊列來平行施工【事實】。多篇攻略明確點出一個關鍵設計邏輯：**「時間才是真正的成本，不是資源」**——資源本身玩家通常都能生產出來，真正的瓶頸是「隊列空出來、輪到你蓋」這件事本身，而這件事只能用時間或用鑽石買加速道具解決【事實，來源：多篇攻略站一致觀點】。

一篇玩了半年的深度玩家心得（透過 GitHub Gist 直接讀到全文）把這個矛盾講得很白：「**等一天讓某件事完成，或者付 10 美元立刻拿到**」（"wait a day for something, or pay $10 to get it immediately"）——這句話幾乎就是整個進度牆設計哲學的濃縮版【事實，直接引用】。

### 2.2 VIP 系統把「等待」明碼標價

VIP 等級直接販售時間本身：VIP 3 提供 +10% 建造速度，VIP 11 提供 +50% 建造速度，VIP 7 解鎖多項自動化功能（大幅減少每日手動點擊的次數）【事實，來源：多篇 VIP 攻略一致】。玩家也可以完全繞開「累積 VIP 點數」的過程，直接用鑽石購買 VIP 天數：VIP 24 小時＝1,000 鑽石，VIP 7 天＝3,000 鑽石，VIP 30 天＝10,000 鑽石【事實，來源：VIP 攻略站】。

### 2.3 裝備/無人機系統：一口「無底深井」

無人機（Drone）系統是後期最深的數值坑之一，由四個子系統疊加構成：①「數據訓練」（用戰鬥經驗卡升級並把屬性轉換給英雄）、②「組件」（六件裝備式部件，直接加成戰鬥數值，三件同級組件可合成升一級）、③「戰鬥強化」（用多餘晶片升級，解鎖技能晶片系統）、④「技能晶片」（四種類型，各自加成特定數值、在戰鬥不同時機觸發，是後期影響最大的一層）【事實，來源：多篇無人機攻略一致】。

進度節奏上：1–150 級，每 5 級需要一次無人機零件；**150 級之後，變成每一級都要零件，且成本持續遞增**——這種設計確保玩家「練完這階段，永遠有下一階段等著課金加速」，是典型的「無限深度」付費軸【事實，來源：多篇攻略一致】。

### 2.4 免費玩 vs 付費跳過的結構性落差

綜合以上：新手期資源與時間都相對寬裕，付費壓力低；但每往後推進一個門檻（建築 20 級後、無人機 150 級後、賽季後期軍備競賽），「純靠時間換取進度」與「课金直接跳過等待」之間的落差就被系統性放大一次。這個結構被玩家心得歸納為典型的「pay for time」模型——免費玩家理論上都能達成同樣的最終數值，但代價是以「週」甚至「月」為單位的等待，而付費玩家可以把這個時間壓縮到幾乎即時【推論，綜合多個一致來源】。

---

## 3. 社交架構：聯盟、伺服器、跨服對抗、賽季制

### 3.1 聯盟制度：五級階級與義務

聯盟內分五個階級，R5 到 R1：**R5**（盟主，通常是創始人，唯一能任命/罷免 R4、指派官職、解散聯盟的人）、**R4**（官員，最多可有 6 席，可接受/踢除成員、發起集結、管理領地、啟動指派給該職位的聯盟技能，是聯盟的「營運骨幹」，理想上每位 R4 應該有明確分工而非全部做一樣的事）、R3/R2（骨幹與重要成員）、R1（新人）【事實，來源：多篇聯盟攻略站一致】。

日常義務層面：資源捐獻是最常見的貢獻方式，多篇攻略強調「每天穩定小額捐獻」比「偶爾大量捐獻」更有效率地累積貢獻點數，隱含遊戲鼓勵**每日登入儀式感**的設計【事實/推論】。集結（rally）機制上，有「頭銜」的 R4/R5 提供的集結傷害加成高於無頭銜的 R4，這進一步鞏固了聯盟內的階級分工必要性【事實】。

### 3.2 每日/每週的「軍備競賽」時間結構

**Arms Race（軍備競賽）**：每日個人競賽，於伺服器午夜重置，把一天切成六個 4 小時視窗，由五種主題輪流填入這六個時段：英雄培養（Hero Advancement）、城市建設（City Building）、部隊訓練（Unit Progression）、科技研發（Tech Research）、無人機強化（Drone Boost）。**在「對的」時段做「對的」行動，得分是平時的 2–3 倍**【事實，來源：多篇 Arms Race 攻略一致】。

**Alliance Duel（聯盟對決）**：每週一到週六進行，兩個聯盟以 PvE 任務積分對抗，計分規則的巧妙之處在於——**贏得整週的關鍵不是總分最高，而是「贏得比對手多的單日主題」**，即逐日結算勝負【事實】。更精妙的是，Alliance Duel 的每日主題刻意與 Arms Race 的每日主題重疊，讓玩家「一次行動、資源用一份，同時在兩個活動拿雙倍積分」——這是刻意設計的時間集中壓力，逼玩家在特定 4 小時窗口內密集消耗加速道具/資源【事實，來源：多篇攻略交叉一致，是本次研究中設計巧思最明確的一項證據】。

**General's Trial（將軍試煉）**：約每兩週一次，混合 PvE 與 PvP 元素，玩家挑戰稱為「先鋒教官」（Vanguard Instructors）的高強度 AI Boss，共 9 個難度關卡，分「個人挑戰」與「聯盟挑戰」兩軌，聯盟挑戰是「有人打贏精英部隊、全員雨露均霑」的協作制設計【事實】。

### 3.3 跨服對抗：Warzone Duel / SvS

《Last War》的旗艦跨服活動稱為 **Warzone Duel**（伺服器戰/國戰），玩法是整個伺服器（稱為 warzone）聯合起來進攻對方伺服器的「首都」（Capitol），目標是把佔領進度推到 100%；若進攻方在時限內未達 100%，防守方直接判定獲勝。單次賽制歷時 2–3 週，會有 4 到 8 個 warzone 互相配對淘汰，戰鬥本身視雙方戰力可能 30 分鐘到 2 小時以上不等【事實，來源：多篇攻略一致；注意：同系列姊妹作《Last Z》裡的對應活動叫 "SvS/Capital Clash"，命名法在系列間略有差異，本報告以 Last War 官方稱呼 "Warzone Duel" 為準】。

一個值得記錄的玩家軼事：長期玩家心得（GitHub Gist）觀察到，伺服器內部頂尖聯盟之間會形成 **NAP（互不侵犯協議，Non-Aggression Pact）**，實質上鞏固既有強者的地位、排除後進者翻盤的可能性，形成階級固化的政治生態【不確定/軼事：單一資深玩家的觀察，屬合理但未經其他來源交叉驗證的說法】。

### 3.4 伺服器結構：開服節奏與合服

新伺服器大約**每 2–3 天開一個**【事實，來源：伺服器追蹤站】。當某伺服器人口過低，系統會**自動、免費**把它與另一伺服器合併，玩家沒有選擇權；若玩家想「主動」換伺服器，則要透過 **Transfer Surge**（轉服潮）機制——這個窗口通常開在每個賽季結束後 1–2 週，需要消耗遊戲內貨幣，且需要目的地伺服器「審核通過」才能轉入，沒有固定週期，需留意遊戲內公告【事實，來源：轉服攻略站一致】。

同一位長期玩家的心得另外提到：賽季 1 結束後，舊伺服器會被「鎖住」，只能在同一個「battlegroup」（戰鬥分組）內透過付費轉服流動——他將此稱為「計畫性衰退」（planned decay），認為這是刻意設計來驅動伺服器汰舊、逼玩家要嘛棄坑重練新服、要嘛課金轉服維持競爭力【不確定/軼事：單一玩家詮釋，但與下方「賽季制會重新分組 warzone」的官方機制描述方向一致，可信度中等】。

### 3.5 賽季制：從 Season 1 到 Season 6 的結構性大改版

Last War 已知賽季：**Season 1「Crimson Plague」**（含病毒抗性、職業系統、基因重組、領地新規則）、Season 5「Wild West」（城市只能在週三/週六被攻佔，引入三種全新賽季資源，明顯放慢節奏並製造策略瓶頸）、**Season 6「Shadow Rainforest」於 2026 年 4 月 13 日上線**，被形容為「遊戲史上最大結構性改版」——引入 4v4 陣營制（Factions）、聯盟盟約（Alliance Pacts）、以「漁場」（Fishing Grounds）取代原本的「據點」（Strongholds）、戰功制度（War Merit）、祭壇/聖所/前哨站爭奪戰，以及「英雄覺醒」系統；更關鍵的規則變化是：**Season 6 起，城市一旦被摧毀就永久消失、不能重建**，取代了先前「城市被打爛還能重建」的舊規則【事實，來源：多篇賽季攻略站交叉一致，且細節具體、可信度高】。**每個新賽季都會重新分組伺服器/warzone**，即前述「合服＋新分組」的官方機制【事實】。

Naavik/GameRefinery 的產業分析提到，Last War 的**第一個「賽季」機制於 2024 年 5 月正式上線**（對應 GameRefinery 當月市場報告所稱的 "The Crimson Plague"，應即 Season 1）【事實，來源：GameRefinery 2024-05 市場報告摘要】。以此推算，從 2023 年 8 月上市到 2026 年 4 月 Season 6 上線，約 33 個月內經歷 6 個賽季，平均每季約 5–6 個月，但實際步調並不均勻【推論：由上市日與各季上線日回推，非官方公告的固定週期】。

---

## 4. 付費點地圖：從 VIP 到禮包、通行證、抽卡、裝備線

### 4.1 VIP 系統：18 級、極端後段負荷的曲線

VIP 1 到 6 只需要累積 15,000 點，但 **VIP 18（滿級）需要累積 5,000 萬點**——曲線後段極度陡峭，明確是為「重氪玩家」而非一般玩家設計的等級帶【事實，來源：VIP 攻略站】。VIP 點數與鑽石可以 1:1 直接兌換，也可以直接付費買斷 VIP 天數（見第 2.2 節）。一篇玩家心得粗估，衝到 VIP 18 大約需要**累積花費 50 萬美元量級**【不確定：玩家個人估算，非官方公布數字，僅供量級參考】。

### 4.2 禮包定價梯度

常規禮包區間大致落在 **$0.99 到 $19.99**；另有 **$99.99 的「Standard Pack」**（常態折扣後約 $79.99）；目前查到最高單一已知禮包，是名為「Black Market Cash All-In-One」的組合包，定價約 **$333.99**（原價 $384.99，約 77 折）【事實，來源：多篇禮包攻略/評比站交叉一致】。是否存在更高階、如同業界其他 4X 遊戲常見的 $999 量級超大額禮包，**查無明確證據**，本報告不做臆測【查無】。另有提到「Whale+」等級——在官方合作的 Discord 社群裡給高額消費聯盟領袖專屬認證與 VIP 頻道，屬於社交地位／身份可視化的變現手法，而非單純道具販售【不確定：僅單一來源提及，細節未交叉驗證】。

### 4.3 通行證（Pass）體系

戰鬥通行證（Battle Pass）分免費軌 + 兩個付費軌：Advanced（約值 $4.99）與 Premium（約值 $19.99），均以「Gold Bricks」這種代幣計價購買【事實，來源：通行證攻略站】。另有 **Super Monthly Pass，定價 $24.99**（全球標準定價）【事實】。還有限定的「英雄成長通行證」（Hero Growth Battle Pass），定價約 £4.99，只在賽季中特定週開放 5–6 天【事實，來源：Last War Handbook】。此外一度存在「Custom Weekly Pass」，分 $5 與 $20 兩種版本，但**已在 2026 年的貨幣化架構調整中被移除**（見 4.5 節）【事實】。

### 4.4 裝備/無人機：多線並行的深度養成

見第 2.3 節詳述的無人機四層子系統。核心結論：Last War 至少同時經營「英雄」「無人機」「建築/科技」「賽季限定資源」四條並行的數值養成線，彼此互相依賴（例如無人機的「數據訓練」子系統會把屬性轉換給英雄），刻意讓玩家的資源與時間分配決策變得複雜，也拉長了每一條線各自的付費週期【事實+推論】。

### 4.5 2026 年的貨幣化「急煞車」：移除高單價彈窗禮包

一個值得特別記錄的近期變化：**2026 年初，開發商移除了 $20、$50、$100 這三檔「彈窗式」高單價禮包，以及前述 Custom Weekly Pass**，轉向以「通行證」為主的模式，並向所有玩家的信箱發送一次性補償包。官方對外說法是希望玩家「專注在交朋友、享受遊戲」而非持續感受課金壓力，並意在「放慢」已經定義了高階版本環境的軍備競賽式數值攀升節奏【事實，來源：多篇玩家社群/攻略站報導交叉一致，含多支相關 YouTube 影片討論】。是否為玩家流失壓力、輿論壓力（含 4.6 節南韓集體申訴）或純粹長期 LTV 優化所致，**查無官方明確歸因，本報告不做定論**，但時間點上與監管爭議相近，值得注意【推論/不確定】。

### 4.6 貨幣化爭議：南韓集體申訴

2025 年 1 月 31 日，南韓玩家對政府提出檢舉並展開集體法律行動（ClassActionU 網站設有專門的 mass arbitration claim 頁面，惟該頁本身被 403 擋下，資訊經由其他報導轉述），核心指控包括：玩家申請退款後帳號遭「信用分數」機制扣分並限制使用，須額外付費才能解除限制；部分玩家也指控遊戲內「限時折扣」的折扣幅度與「限時」訴求並非真實稀缺性，涉嫌違反消費者保護法規中對誤導性行銷的規範【事實/指控性質，來源：多篇報導交叉一致，但因原始一手頁面被 403，細節（求償金額、參與人數等）未能核實，建議人工複查】。截至查詢時，未查到 FirstFun / FUNFLY 官方對此的公開回應【查無官方回應】。

### 4.7 營收規模：不同資料商口徑並列

营收數字在不同資料商/時間點之間差異頗大，以下並列呈現、不強行統一：

- 2023 年 8 月上市首月，營收僅約 **28.7 萬美元**（PocketGamer.biz／AppMagic 估算）
- 2024 年單月營收從 1 月的約 **3,000 萬美元**成長到 12 月的約 **1.38 億美元**，年增幅約 360%（同上）
- 2024 年 9 月 14 日，累計營收單日跨過 10 億美元門檻，當月（9月）營收約 **1.745 億美元**，創當時單月紀錄（同上）
- 2024 全年營收約 **11 億美元**，名列 2024 年全球手遊營收前五名（Naavik／Sensor Tower 口徑）
- 2025 年 1 月單月營收約 **2.11–2.12 億美元**，2 月 14 日單日玩家消費達 **1,160 萬美元**，創單日紀錄（PocketGamer.biz／AppMagic）
- 累計終身營收於 **2025 年 2 月 15 日突破 20 億美元**（同上，最常被引用的「里程碑」數字）
- 另有資料商稱「18 個月內營收達 16 億美元」（FoxData 標題數字，與上述 20 億美元的口徑/統計截止時間點不同，兩者不必然矛盾但無法直接對齊）
- 亦有較新的搜尋結果綜合提到「終身營收約 26–35 億美元、其中 2025 全年約 16.5 億美元」，但此數字原始出處與統計方法在檢索過程中無法精確定位，**標記為不確定**
- 有分析形容其每次下載可帶來的營收（ARPD）約 **18 美元**，並形容這是「鯨魚與中額付費者的機器，而非走量產品」——但此段文字的原始一手出處在檢索中同樣無法精確定位到單一權威來源，**標記為不確定**

**小結（推論）**：儘管精確數字各家不一，所有來源都指向同一個量級結論——這是一款自 2023 年 8 月上市以來、在 2024–2025 年間營收呈現爆炸性成長，並穩居全球手遊營收前 2–5 名的超級現象級產品，累計營收確定在「數十億美元」量級。

---

## 5. LiveOps 節奏：每日、每週、賽季、更新頻率

**每日層**：Arms Race（6 個 4 小時視窗、5 主題循環）、VIP 每日寶箱（VIP 等級越高內容越好）、每日 1 次免費英雄招募 + 1 次免費倖存者招募、雷達任務（Radar Missions）每 6 小時刷新一批（依等級不同，8–13 個不等，任務類型含清殭屍、擊殺 Doom Elite/Doom Walker 精英怪、採集資源、營救倖存者、偶發稀有挖掘任務）、每日聯盟捐獻、以及像 Carnival Login 這類 7 天一輪的登入獎勵活動【事實，來源：多篇每日任務攻略站交叉一致】。

**每週層**：Alliance Duel（週一至週六，每日主題輪替、與 Arms Race 刻意重疊計分，見 3.2 節）。

**約每兩週層**：General's Trial（9 難度關卡、活動視窗約 3 天）。

**多週層**：Warzone Duel/SvS 跨服賽制（2–3 週賽程，4–8 個 warzone 配對淘汰）。

**賽季層**：約每 5–6 個月一次重大版本改版（見 3.5 節），每季更換主打英雄（例：Season 1 Mason、Season 2 Violet、Season 3 Scarlett、Season 4 Sarah、Season 5 Venom、Season 6 Braz），每季也常伴隨地圖重製、新資源系統、新玩法模組（如 Season 6 的 4v4 陣營戰）【事實】。

**版本更新**：查到 2 月與 3 月 19 日的具體更新紀錄，內容包含 UI/體驗優化（如集卡車標記更清楚、聯盟介面升級）與規則調整（例如「聯盟紀錄」保存天數從 90 天砍到 30 天；加速道具超額使用後，多出的部分會透過信箱以 1 分鐘加速道具形式退還）——顯示至少維持**月更**的節奏，且會有系統性的規則微調而非只是活動輪替【事實，來源：更新公告攻略摘要】。加上 4.5 節提到的 2026 年初大型貨幣化架構重組，顯示這款遊戲即便上市已近 3 年，仍在持續進行結構性調整，而非單純的「內容添加式」營運【推論】。

---

## 6. 「空虛感」的來源：為什麼前期刻意做得像洗腦爽感小遊戲

這部分整合前面各節的線索，做設計意圖層級的解讀，**以推論為主**，但每個推論都附有旁證：

**(1) 戰鬥自動化是核心「淺」感受的直接來源。** 多篇獨立評論一致形容核心 PvE 玩法是「選隊伍、排陣型，然後看 AI 打」——玩家在戰鬥當下幾乎沒有即時操作可做，唯一的決策密度集中在戰前配置。這意味著一個只是「玩過/看過」的輕度玩家，感受到的互動幾乎全是點擊選單、等待數值跑完，幾乎不會遇到需要臨場反應的「玩法」時刻【事實：多來源一致；推論：這是「空虛感」最直接的機制成因】。

**(2) 大量一鍵/掛機式便利設計刻意降低操作密度。** 資源建築離線累積產出（但有時數上限，需要定期而非隨時回收）、集卡車一鍵全收、隨機傳送一鍵離開戰場——這些設計把「必須持續盯著螢幕」的要求降到最低，讓遊戲能被「順手點一點」地消費，而非要求連續專注的玩法投入【事實，來源：多篇機制說明一致】。

**(3) 廣告小遊戲即開場關卡，是刻意壓低獲客成本（CPI）的產業標準手法。** 產業分析（Gamigion、AppSamurai 等買量/UA 專業媒體）明確指出：把廣告素材直接做成遊戲的開場關卡，是近年 hybrid-casual／混合休閒品類的標準打法——先用最大眾化、門檻最低的玩法（廣告同款）吸引低成本安裝，讓玩家在最初 5–15 分鐘內就感受到「這遊戲上手即懂、有樂趣」，再無縫過渡進真正承擔留存與變現任務的核心系統（在本例中就是 4X／SLG 骨架）。產業分析同時指出，若一味追求最低 CPI，會讓漏斗灌入大量「玩兩局就跑」的低意願用戶，因此這個過渡設計本身需要拿捏平衡【事實，來源：Gamigion、AppSamurai 產業文章交叉一致；推論：Last War 的開場即是這套打法的具體實例】。

**(4) 中文產業評論明確把這個設計動機講白了：「去燒腦化」以擴大目標市場。** 一篇中文產業文章（ok-power.com）直接指出，Last War 這類遊戲「在 SLG 基礎上自然融入休閒玩法，降低了理解門檻與上手門檻，讓 SLG 品類的遊戲體驗不再那麼枯燥燒腦」——也就是說，「做得不燒腦、不硬核」本身就是一個**主動的商業策略**，目的是把傳統只有重度策略玩家才會碰的 SLG 品類，擴大到願意被抖音/社群廣告吸引進來的一般輕度手遊玩家【事實：該文措辭明確；推論：這正是 Jake 所感受到的「空虛」在產品策略語言裡的正式說法】。

**(5) 這不是新手團隊的意外設計，而是資深 4X 變現老手的又一輪迭代。** FirstFun 與另一間關係密切的工作室 RiverGame，兩者創辦人都出身自 ELEX Technology——一間 2014 年以約 4.33 億美元賣給中國買家的老牌 4X 手遊公司。這意味著 Last War 的整套「COK-like 核心骨架 + hyper-casual 買量外殼」打法，並非團隊摸索試錯的產物，而是一批深諳 4X 手遊變現機制的資深團隊，把已驗證有效的核心玩法，包裝進新一代更低門檻、更利於短影音買量的入口介面【事實：公司背景與人才淵源部分經多來源交叉確認；推論：這解釋了整體設計的「熟練度」與「刻意感」】。

**綜合推論**：Jake 感受到的「空虛」，精準地說，是他觀察到了這套產品漏斗**刻意設計成不燒腦、不需要玩法技巧**的最上層切片——前幾分鐘到最初幾天的輕量體驗。而遊戲真正意義上的「深度」，並不在「玩法可操作性」這個維度上（這維度確實刻意做淺），而是被轉移、隱藏進另一組平行系統裡：聯盟社交義務、跨服競賽排名的長期投入、賽季重置帶來的持續性焦慮、無人機/裝備多層數值坑的長期規劃、以及消費階梯本身的複雜度。這些系統只有玩家投入數週甚至數月、開始承擔社交義務（聯盟捐獻、集結、跨服戰）之後才會顯現——這正是「深度延遲揭露」的產品設計：太早暴露完整複雜度，會嚇跑本來就對硬核 SLG 沒興趣、靠低門檻廣告吸引進來的大部隊安裝用戶，傷害整體轉換率與 CPI 效率。

---

## 7. 反面訊號：對照 Jake「空虛」直覺的重要證據

以下證據不是要推翻「其實很深」的結論，而是提供**另一面同樣重要的事實**：這個「延遲揭露的深度」對相當一部分玩家而言，**沒有兌現成真正的樂趣或黏著度**，甚至某種意義上反過來坐實了「空洞」的批評。這對 Jake 的直覺是重要的對照證據，不應被省略：

1. **留存率明顯遜於同類型龍頭。** Last War 在 iOS 美國市場的 D1/D7/D30 留存率分別為 **34% / 11% / 4%**，對比同賽道龍頭《Whiteout Survival》的 **42% / 17% / 8%**，全面落後（來源：Naavik，2025-01-22）。D30 只剩 4%，意味著新安裝的玩家裡，**超過 96% 在 30 天內已經流失**。這代表 Last War 能維持頭部營收規模，靠的主要是極高強度、持續不斷的付費買量（UA），而不是靠「內容深度」本身把人留住【事實+推論】。
2. **多篇獨立評論不約而同用負面字眼形容遊戲**：「soulless（沒有靈魂）」「overcommercialized（過度商業化）」，並明確指出小遊戲元素「很快變得無聊而重複」（gets pretty repetitive fast）【事實，多來源摘要一致】。
3. **南韓玩家集體申訴/檢舉（2025-01-31）**，指控退款後帳號遭懲罰性限制、限時折扣涉嫌不實——顯示至少一部分付費玩家對其貨幣化手法的觀感是「掠奪性」而非「有深度所以值得」【事實/指控性質，見 4.6 節，原始頁面被 403，建議人工複查】。
4. **玩家直接抱怨「課金到位前幾乎玩不下去」**，需要花費「數百美元」才能在各條養成線（月卡、週卡、VIP、英雄卡池等）都跟上進度【不確定：玩家評論彙整轉述，未見一手原文，但多篇評論方向一致】。
5. **存在一整條第三方外掛/代管機器人產業**（GodLikeBots、gnbots.com、boostbot.org，甚至有玩家在 GitHub 公開自製的 bot 腳本），其存在理由是玩家反映**每天要花 4–6 小時**手動收資源、練兵、管理基地，晚上不掛機「進度就是零」、會被開外掛的對手拉開差距，遊戲因此「感覺像苦差事而不是樂趣」【事實：多個 bot 服務商網站與說明頁一致描述此需求】。這是一條非常重要的反直覺證據：**對真正想維持競爭力、長期黏著的玩家來說，這遊戲一點都不「空虛輕鬆」，而是重複勞動繁重到催生出一整條自動化代管產業**——玩家想用機器人把「無聊但必要」的部分外包出去，恰恰說明遊戲的「深度」在很多老玩家眼中，體感上更接近「粗重的重複勞動」而非「引人入勝的策略樂趣」。
6. **開發商 2026 年初主動撤下高單價彈窗禮包與週卡**（見 4.5 節），不論真正動機為何，這個「開發商自己踩剎車」的動作本身，間接說明先前的貨幣化強度確實已經超出至少一部分市場可接受的範圍【推論】。
7. **長期玩家心得直言「在高階賽事裡技巧幾乎不重要」**，一位投入約 25 萬美元的玩家足以直接主宰每週活動，遊戲實質上是「课金者資助免費玩家娛樂」的結構（GitHub Gist 全文引用）——這句話某種意義上**正好印證了 Jake「內容淺」的直覺**：可主動操作、靠技巧決勝負的玩法空間確實很薄；真正「深」的是消費階梯的複雜度，而不是玩法本身的策略深度【不確定/軼事：單一資深玩家的第一手觀察，但與整體證據方向一致】。

**這一節的結論**：Jake 的「空虛」直覺，在「可主動操作的玩法密度／技巧決勝負空間」這個維度上，其實**沒有錯**——核心戰鬥高度自動化、早期教學刻意做成無腦爽感、玩家能主動決策並展現技巧的空間確實稀薄。但這個「淺」是一個經過精密計算的產品決策，其商業目的從來就不是「讓每個人都覺得好玩」，而是最大化「低成本安裝 → 留存過篩 → 轉化為長期付費」這條漏斗的效率。遊戲真正的複雜度，並不在「玩法」層，而轉移到了「社交義務 + 賽季時間表 + 多層數值養成 + 消費階梯設計」這個平行的系統裡——而這個系統，絕大多數只是「玩過/看過」的輕度玩家（包括 Jake）根本不會觸及，因為它是刻意設計成要等你先課金或先重度投入之後才會顯現的。

---

## 來源清單

以下依主題分類列出本次研究實際引用/檢索到的來源。除特別標註「直接讀取全文」者，其餘均透過 WebSearch 摘要檢索取得，未能讀取原始頁面全文（詳見第 0 節方法論說明），查詢日期一律為 **2026-07-22**。

**直接讀取全文（WebFetch 成功）**
- GitHub Gist（Adachi91）〈Last War: Survival - Thoughts After Half a Year Playing It〉— https://gist.github.com/Adachi91/60a458ec3fbf542be5ec6cada0c41e7e

**產業/營收分析類（經 WebSearch 摘要）**
- Naavik〈Why Last War Is Winning the 4X Game〉(2025-01-22) — https://naavik.co/digest/how-last-war-is-winning-the-4x-game/
- GameRefinery〈Hybridization Is the Key for the Latest 4X Strategy Success Stories〉— https://www.gamerefinery.com/hybridization-is-the-key-for-the-latest-4x-strategy-success-stories/
- GameRefinery〈The Rise of Hybridization in Mobile Games〉— https://www.gamerefinery.com/the-rise-of-hybridization-in-mobile-games-how-developers-are-genre-mashing-their-way-to-success/
- PocketGamer.biz〈Last War: Survival surpasses $2bn after record player spending in early 2025〉— https://www.pocketgamer.biz/last-war-survival-surpasses-2bn-after-record-player-spending-in-early-2025/
- GameMakers〈Cracking the 4X Code: First Fun and RiverGame's Billion-Dollar Strategy〉— https://www.gamemakers.com/p/cracking-the-4x-code-first-fun-and
- GameMakers〈Last War Surviving and Thriving at #2 Revenue Worldwide〉— https://www.gamemakers.com/p/last-war-surviving-and-thriving-at
- FoxData〈How "Last War: Survival" Raked in $1.6 Billion in a Mere 18 Months!〉— https://foxdata.com/en/blogs/how-last-war-survival-raked-in-16-billion-in-a-mere-18-months/
- FoxAdvert〈From 1-Star Reviews to $1.3 Billion: The Untold Story of Last War's Success〉— https://foxadvert.com/en/digital-marketing-blog/from-1star-reviews-to-13-billion-the-untold-story-of-last-wars-success/
- MAF.ad〈Last War Survival: The Secrets Behind Its $2.6 Billion Revenue〉— https://maf.ad/en/blog/last-war-survival/
- TechNode〈Last War: Survival Game boosts FirstFun to fifth in Chinese mobile game publishers〉(2024-03-21) — https://technode.com/2024/03/21/last-war-survival-game-boosts-firstfun-to-fifth-in-chinese-mobile-game-publishers/
- блог Udonis〈Last War: Survival Revenue & Player Count Statistics (2022–2026)〉— https://www.blog.udonis.co/statistics/last-war-survival

**評測/玩家觀點類**
- Ruthless Reviews〈Last War Survival Game Review: My Honest Take After Playing for Weeks〉— https://www.ruthlessreviews.com/featured-posts/last-war-survival-game-review-my-honest-take-after-playing-for-weeks/
- ArcadePunks〈Is Last War: Survival a Real Game? Complete Analysis〉— https://www.arcadepunks.com/is-last-war-survival-a-real-game-complete-analysis/
- PlayScored〈Last War: Survival Review: Ads vs. Reality〉— https://playscored.com/review/last-war-survival-review
- Tenteck〈Last War Survival Game Reddit: An Honest Review〉— https://tenteck.com/last-war-survival-game-reddit-review/
- Medium（Kayla L）〈How Mobile Game Last War: Survival Makes Money〉— https://medium.com/@kayla.devwork/how-mobile-game-last-war-survival-makes-money-9c68c744105b
- malvasiabianca.org 個人部落格〈last war: survival〉(2025-11) — https://malvasiabianca.org/archives/2025/11/last-war-survival/
- Andy Zhang 個人部落格〈(Game Review) Last War: Survival Game〉— https://andyzhang.me/blog/game-review-last-war.html

**廣告 vs 實際玩法類**
- Gamigion〈Ad creatives vs actual gameplay: Bait and Switch done right〉— https://www.gamigion.com/ad-creatives-vs-actual-gameplay-bait-and-switch-done-right/
- Gamigion〈How Last War and WhiteOut Survival Expand Their Player Base〉— https://www.gamigion.com/how-last-war-and-whiteout-survival-expand-their-player-base/
- Gamigion〈Bolting proven hyper-casual hooks onto your onboarding?〉— https://www.gamigion.com/bolting-proven-hyper-casual-hooks-onto-your-onboarding/
- Fake Ad Games 博物館 — https://fakeadgames.com/
- AppSamurai〈Hybrid-Casual Games UA Playbook: How to Acquire and Retain Users〉— https://appsamurai.com/blog/hybrid-casual-games-ua-playbook-how-to-acquire-and-retain-users/

**法律/監管爭議類**
- ClassActionU〈Last War: Survival〉mass arbitration claim 頁面 — https://classactionu.org/mass-arbitrations/current-claims/last-war-survival/

**遊戲機制攻略類（用於核實具體數值機制，非設計意圖分析）**
- Last War Vault〈SSR to UR Upgrade Guide〉— https://www.lastwarvault.com/guides/general/ssr-ur-upgrade-guide/
- Last War Vault〈Server Merge & Migration Guide〉— https://lastwarvault.com/guides/general/server-merge-migration-guide/
- Last War Vault〈Pack & Spending Tier List〉— https://lastwarvault.com/guides/general/pack-tier-list/
- LDShop〈Last War VIP Guide: All 18 Levels, Benefits & Best Strategy〉— https://www.ldshop.gg/blog/last-war-survival/last-war-vip-guide.html
- LDShop〈Last War: Survival Alliance Duel Guide〉— https://www.ldshop.gg/blog/last-war-survival/alliance-duel.html
- LDShop〈Last War Drone Parts Per Level: Upgrade Cost & Strategy Guide〉— https://www.ldshop.gg/blog/last-war-survival/drone-upgrade-guide.html
- LDShop〈Last War: Survival – Complete R4 & R5 Alliance Officer Guide〉— https://www.ldshop.gg/blog/last-war-survival/r4-r5-guide.html
- Packsify〈Last War VIP Guide: Which Levels Actually Matter (2026)〉— https://www.packsify.com/blogs/last-war-survival-vip-points-showdown
- Packsify〈Last War: Survival Best Packs to Buy (2026 Guide)〉— https://www.packsify.com/blogs/last-war-survival-best-packs-to-buy
- Last War Handbook〈Warzone Duel Guide (2026): Server War & Capitol Strategy〉— https://lastwarhandbook.com/guides/warzone-duel-server-war-guide
- Last War Handbook〈Season System & Battle Pass Guide〉— https://lastwarhandbook.com/guides/season-system-battle-pass-guide
- Last War Handbook〈Events Guide (2026): Daily, Weekly & Monthly Events〉— https://lastwarhandbook.com/guides/events-guide
- Cpt Hedgehog's Battle HQ〈Season 6 Ultimate Guide - Lost Rainforest〉— https://cpt-hedge.com/guides/season-6-ultimate-guide
- Cpt Hedgehog's Battle HQ〈Season 5 Ultimate Guide - Wild West〉— https://cpt-hedge.com/guides/season-5-ultimate-guide
- U7buy〈Last War Survival Season 6 Complete Guide〉— https://www.u7buy.com/blog/last-war-survival-season-6-guide/
- Root-Nation〈Last War Survival Pack Guide: $0.99 vs $4.99 vs $19.99 Value〉— https://root-nation.com/en/games-en/games-articles-en/en-last-war-survival-pack-guide-0-99-vs-4-99-vs-19-99-value/
- LastWarTutorial〈Win Daily Arms Race event in Last War〉— https://www.lastwartutorial.com/arms-race/

**自動化/外掛產業類（反面訊號證據）**
- GodLikeBots〈Last War Survival Bot〉— https://godlikebots.com/last-war-survival-bot/
- GNBots〈Last War Bot - Auto Rally, Digs & Map Scan〉— https://www.gnbots.com/shop/last-war-survival-bot/
- BoostBot〈Last War Survival Bot〉— https://boostbot.org/last-war-survival-bot/

**其他背景資料**
- 維基百科〈Last War: Survival Game〉— https://en.wikipedia.org/wiki/Last_War:_Survival_Game （WebFetch 被 403，內容經 WebSearch 摘要轉述）
- OK-Power（中文產業文章）〈SLG"leisure"趨勢確立〉— https://www.ok-power.com/article/21539400.html
- Oreate AI Blog〈Beyond the Apocalypse: Unpacking the 'Last War: Survival' Phenomenon〉— https://www.oreateai.com/blog/beyond-the-apocalypse-unpacking-the-last-war-survival-phenomenon/16b22daa9ce6a51f88a1cbf50853c4b6

---

## 被 403 擋掉、值得本機（有 Reddit/瀏覽器登入權限的環境）複查的頁面

以下頁面 WebFetch 全部回傳 HTTP 403（或無法連線），僅能靠 WebSearch 摘要取得片段內容，**若有能繞過反爬蟲的瀏覽器環境（如本機 /browse 或已登入 cookies 的瀏覽器），強烈建議複查**，因為這些頁面明顯包含比摘要更豐富的一手內容：

1. **`old.reddit.com/r/LastWarMobileGame/`**（WebFetch 直接回傳「無法連線」而非 403）—— 最高優先。本報告完全沒能直接讀到 r/LastWarMobileGame 的原始貼文/留言，所有玩家社群意見都是透過其他網站「轉述 Reddit 共識」取得的二手資料，**建議務必人工複查原始 subreddit**，尤其搜尋「boring」「empty」「quit」「refund」關鍵字的高讚留言串。
2. `https://classactionu.org/mass-arbitrations/current-claims/last-war-survival/` —— 南韓集體申訴/法律行動的一手說明頁，目前所有細節（求償金額、參與人數、具體條款）都是轉述，值得核實。
3. `https://gist.github.com/Adachi91/60a458ec3fbf542be5ec6cada0c41e7e` —— 本次唯一成功直接讀取的頁面，內容非常有價值（半年深度玩家心得），**建議人工完整通讀原文**（本報告只摘錄了重點），可能還有更多未被摘要覆蓋的細節。
4. `https://en.wikipedia.org/wiki/Last_War:_Survival_Game` —— 維基百科條目通常是查核發行日期、公司結構、爭議章節最省時的地方，本次連維基百科都被 403，建議直接複查。
5. `https://naavik.co/digest/how-last-war-is-winning-the-4x-game/` —— 付費/專業產業分析媒體，本報告引用的留存率數字（34/11/4 vs 42/17/8）即出自此文摘要，建議核實原文是否有更多留存/LTV 細節。
6. `https://www.gamemakers.com/p/cracking-the-4x-code-first-fun-and` 及 `https://www.gamemakers.com/p/last-war-surviving-and-thriving-at` —— 兩篇對 FirstFun/RiverGame 商業策略最完整的深度報導，本報告只拿到摘要，原文可能有更多關於「刻意設計簡單」的直接引述。
7. `https://www.ruthlessreviews.com/featured-posts/last-war-survival-game-review-my-honest-take-after-playing-for-weeks/` —— 「Frontline Breakthrough 僅占約 20% 遊戲內容」這個關鍵數字的源頭之一，建議核實原文完整脈絡。
8. `https://malvasiabianca.org/archives/2025/11/last-war-survival/` 與 `https://andyzhang.me/blog/game-review-last-war.html` —— 兩篇個人部落格深度心得，完全沒能讀到內容，可能有獨特的一手觀察角度。
9. `https://tenteck.com/last-war-survival-game-reddit-review/` —— 聲稱彙整 Reddit 社群共識的二手整理文，本報告引用了它轉述的「20% vs 80%」數字，建議核實其彙整方法是否可靠。
10. `https://wiki.lastwar.com/` —— 官方/半官方 Wiki，理論上應是最權威的機制細節來源，本次完全無法讀取，建議優先複查以核實本報告所有具體數值機制描述。

---

（報告完）
