# 研究報告:《MECCHA CHAMELEON》(めっちゃカメレオン) 遊戲架構設計分析

**查詢日期:2026-07-22 ｜ 研究者:Claude subagent ｜ 工具:WebSearch(用掉25次,額度25次全數用完) + WebFetch(嘗試9次,全數403)**

---

## 摘要結論

《MECCHA CHAMELEON》的「簡單」不是偷懶,是精準的雙重設計:規則簡單到直播觀眾10秒看懂(服務**傳播**),但塗色機制藏著材質/光影/滴管等真實美術工具與「見落としランキング」計分深度(服務**表演與重玩**)。它用「揮發性UGC」(每局塗色即棄)取代傳統皮膚/進度系統當作內容引擎,靠P2P免費架構(零廣告、零伺服器費)把買斷價全部留作利潤,25天賣破1500萬套。但這個架構的代價已經浮現:SteamDB顯示近30天同時在線暴跌84.2%,作弊與好友系統穩定性問題未完全解決,且「有朋友」與「野排/單人」的體驗品質落差巨大——這正是買斷制派對遊戲「爆紅但壽命未知」的核心矛盾,與 Last War 靠付費階梯持續拉長 LTV 的架構邏輯截然不同。

---

## 一、研究方法與限制

- 依指示僅用 WebSearch / WebFetch。WebSearch 共執行 **25 次**(額度用罄)。
- WebFetch 嘗試 9 次(含 Steam 商店頁本身、電ファミ、GAME Watch、PC Gamer、Gamerch wiki、Famitsu、GameWith、Steam 負評頁、日文維基百科),**全部回傳 403**。已用 `curl $HTTPS_PROXY/__agentproxy/status` 確認 proxy 本身無 relay failure 紀錄,判斷是目標網站(Steam 與多數日系遊戲媒體)自身的反爬蟲/機器人防護擋下 WebFetch,而非 proxy 政策阻擋。因此本報告**完全基於 WebSearch 回傳的摘要/引用片段**,未能直接讀取原始全文,細節深度受限於搜尋引擎摘要的完整性。403 清單見文末。
- 凡標記【事實】者為多來源互相印證或官方/主流媒體單一來源明確陳述;【推論】為根據多筆事實合理推導但無直接文獻明說;【不確定】為證據不足或來源衝突,列出但不下定論。

---

## 二、逐項研究發現

### 1. 核心循環

**基本規則【事實,多來源印證,查詢日期2026-07-22】**
玩家分為「鬼隊」(ハンター/Oni/Seeker)與「隱藏隊」(カメレオン/Hider)。官方 Steam 頁建議 2–10 人,技術上限約 24 人,但因採 P2P 房主連線架構,人數建議控制在 15 人以內以免不穩定。
來源:[Gamerch 攻略Wiki](https://gamerch.com/mecha-chameleon/990906)、[Yahoo!知恵袋討論](https://detail.chiebukuro.yahoo.co.jp/qa/question_detail/q10329013955)、[みんなのインディー](https://minna-no-indie.com/articles/meccha-chameleon-drawing-disguise-review/)(經 WebSearch 摘要)

**回合流程(三階段)【事實】**
1. **準備階段**:隱藏方在地圖上自由探索、選擇姿勢(pose)並將全白的身體塗色偽裝成場景一部分;鬼隊此時被鎖在出生房等待。
2. **搜索階段**:鬼隊被放出,開始逐一檢查場景中「看起來不對勁」的物件。
3. **結算**:時間歸零時若仍有至少一名隱藏方未被發現,隱藏方獲勝;若鬼隊在時限內找出全部隱藏方,鬼隊獲勝。
休閒場次的準備時間常見約 90 秒,但**確切數字非固定值,依房主(host)/大廳自訂設定浮動**,官方未見公布統一跨模式的秒數表。
來源:綜合多篇英文攻略站摘要(mobalytics.gg、games.gg、9puz.com 等,經 WebSearch 匯總,原文未逐一驗證)【不確定:精確計時數字】

**塗色機制操作細節【事實,查詢日期2026-07-22】**
不是選預設色塊而已,是一套真正的繪圖工具:
- `F` 鍵切換塗色模式,左鍵塗色,右鍵拖曳調整筆刷粗細(大範圍用粗筆刷、細節用細筆刷是攻略站建議手法)。
- 兩種取色(滴管)方式:「3D 滴管」取物體受光後的「亮部」色;「畫面滴管」直接取螢幕顯示色(含陰影)。二者取色結果不同,是進階技巧的分水嶺。
- 進階材質參數:Metallic(金屬感/鏡面反光)、Roughness(粗糙度/是否反光)、Emissive(自發光,v2.9.0 新增,會讓塗色發光)。
- Pose(姿勢)機制與塗色連動:蜷縮成球、平躺、貼牆會改變朝向鬼隊的「面」,玩家必須依「當前姿勢下實際會被看到的面」重新判斷該塗哪裡——這代表塗色不是一次性完稿,而是需要空間推理。
來源:[skypenguin.net 筆刷教學](https://skypenguin.net/2026/06/19/post-153976/)、[skypenguin.net 滴管教學](https://skypenguin.net/2026/06/14/post-153299/)、[note.com 3.0.0操作說明](https://note.com/reiroom/n/n09e91719d881)(經 WebSearch 摘要匯總)

**地圖/場景設計【事實】**
地圖持續透過免費更新新增,確認至少包含大阪(Osaka,v1.2.0/6.13新增)、Sugarland(v1.4.0/6.18)、Penguin Hotel(v1.7.0/6.22)、デスバーガー(Death Burger)等。6/29 更新讓「かくれんぼの屋敷」地圖的物件改為隨機配置,官方預告未來將推廣到全地圖——這是刻意針對「地圖被玩家記熟後失去驚喜感」問題的架構性解法。
來源:[4Gamer 6/29報導](https://www.4gamer.net/games/007/G100712/20260629022/)(經 WebSearch 摘要)

---

### 2. 「表演性」設計

這是本次研究中**證據品質最高的一節**,主要來自一篇日本遊戲設計專業人士(白坂公一)在 note.com 發表的分析文章,經 WebSearch 摘要取得核心論點:

> 【推論援引自單一分析文章,未查證原文全文,查詢日期2026-07-22】該文核心論點是「本作把『不完全』放進遊戲設計核心」——玩家自認為完美融入背景,但從旁觀角度看往往是「笨拙地緊貼在背景上的變色龍」。這種**「自我認知與旁觀者觀感的落差」**正是留給觀眾最大的「吐槽空間」(ツッコミの余白),也是文章標題所稱「揮發性UGC與大喜利式遊戲設計」的核心——大喜利(ōgiri)是日本一種即興妙答的喜劇形式,強調「答案本身不需要正確,好笑就好」。
> 來源:[白坂公一 note.com](https://note.com/shira_game/n/n1b287a35eb7f)、另一篇分析[だいき note.com「12の秘密」](https://note.com/ms_daiki/n/n5bcd5b11dffd)

**「見落としランキング」(Overlooked Ranking)系統【事實】**
遊戲內建量化「明明在鬼隊視線範圍內卻沒被抓到」的驚險瞬間,把「差一點被抓到」這種喜劇張力轉化成可比較、可炫耀的分數——直接把表演性瞬間變成遊戲內建的成就感來源,而非只是觀眾主觀感受。

**「揮發性UGC」框架的商業/設計意義【推論,合理但屬轉述分析文章的推導】**
每一輪的塗色都是限定當局、用完即丟的創作。相比傳統「永久皮膚」需要玩家投入設計壓力並承受長期評判,一次性塗色降低了創作焦慮,同時每局都能產生視覺上獨一無二的新內容——同時服務了「可玩性」(每局不同的解謎挑戰)與「可看性」(每局都是新素材,直播不會顯得重複)。

**直播/實況生態【事實,多來源印證】**
- 「配信映え」(直播畫面吸睛度)被多篇報導點名為爆紅主因之一,場景中散布的彩色物件提升視覺豐富度。
- 「視聴者參加型」(觀眾參與模式)容易架設,主播與觀眾能共享「這局誰是變色龍」的懸疑感。
- v1.8.0(6/24)一次新增 **11 種表情動作(emotes)**,擴充非語言表演手段。
- 已促成大型多主播聯合直播企劃,並與知名日本 YouTuber(HIKAKIN)等進行合作企劃(v1500萬本紀念,7月)。
來源:[4Gamer emote更新報導](https://www.4gamer.net/games/007/G100712/20260624025/)、[Game*Spark 1500萬本+聯名預告](https://www.gamespark.jp/article/2026/07/05/168844.html)(經WebSearch摘要)

**與 Among Us 的「社交推理表演性」比較【推論,未查得直接文獻對照,自行推導,需標註不確定】**
搜尋未找到任何評論或分析文章直接把兩款遊戲並列比較架構(僅搜到不相關的《Among Us》3D同人影片)。以下屬**研究者根據雙方已知機制的推論**:
- Among Us 的表演性核心是**語言表演**——「說謊/辯論」的 discussion 環節,喜劇效果來自玩家臨場的說謊技巧與被拆穿的尷尬。
- MECCHA CHAMELEON 的表演性核心是**視覺/空間表演**——喜劇效果來自「自認完美融入 vs. 實際看起來很怪」的落差,以及「差點被抓到」的懸疑張力,較少依賴語言互動(遊戲進行中隱藏方通常需要保持靜止安靜)。
- 兩者共通點:都利用「場內玩家與場外觀眾資訊不對等」製造喜劇效果,且勝負機制本身就是茶餘飯後的話題(誰輸了要接受什麼懲罰/糗態)。

---

### 3. 內容量與重玩性

**模式【事實,查詢日期2026-07-22】**
官方確認至少 3 個核心模式:
- **Normal(經典捉迷藏)**:2–4 人,步調較放鬆,定位為新手友善的入門模式。
- **Increasing Oni / 感染模式**:6–10 人,被抓到的隱藏方會加入鬼隊(滾雪球式),緊張感隨回合遞增。
- **Double / 雙人速攻模式**:適用全滿房。
另有 **「逆算チキンレース」**(反向雞戰模式,7/3新增):鬼隊改為「靠隱藏玩家外觀線索推測藏匿位置得分」的玩法,是對核心找人機制的變體延伸。
來源:[mecha-chameleon.net 模式介紹](https://mecha-chameleon.net/game-modes)、[4Gamer 7/3報導](https://www.4gamer.net/games/007/G100712/20260703007/)(經WebSearch摘要,英文攻略站內容未逐一查證原文)

**Steam Workshop(創意工坊)【事實,單一評論來源但具體數字明確】**
PC Gamer 系媒體 RetroGems 的評測指出,截稿時已有 **99 張玩家自製地圖** 透過 Workshop 釋出,被評為「撐起內容量」的重要來源。這代表官方地圖更新之外,還有社群自製內容補位。
來源:[RetroGems 評測](https://retrogems.fr/en/meccha-chameleon-review-pc/)(經WebSearch摘要)

**進度/解鎖/數值成長系統【查無,列為不確定項】**
專門搜尋「実績」「アンロック」「称号」「コスチューム」「進行度」等關鍵字,**未取得任何具體結果**——搜尋引擎僅回傳與問題無關的一般攻略頁。目前可確認的「進步感」來源是**單局內**的技能表現(畫技、隱藏技巧熟練度)與「見落としランキング」這類單局計分,而非典型 live-service 遊戲常見的「跨局數值成長」或「付費/解鎖外觀收藏」。這點需要玩家自行查證 Steam 成就頁確認,本報告**查無證據不代表不存在**,只代表本次搜尋額度內找不到。

**機制深度隨更新增加【事實】**
- v2.0.0:隱藏方新增「分身」機制,最多可製造兩個分身誤導鬼隊;鬼隊新增 TPS(第三人稱)視角選項。
- v2.9.0:塗色新增 Emissive(自發光)材質參數。
這類更新顯示團隊持續往「同一套核心機制加深策略/美術深度」的方向擴充,而非單純堆疊新模式。
來源:[Famitsu 2.0.0報導標題](https://www.famitsu.com/article/202606/79631)(WebFetch 403,僅取得 WebSearch 標題與摘要)

---

### 4. 多人架構

**架構型態【事實,查詢日期2026-07-22,重要發現】**
遊戲採 **P2P(玩家主機/host-based)架構,而非官方專屬伺服器**——這與開發者反覆公開強調「伺服器費用為零」完全吻合。房間穩不穩定直接取決於房主(host)自己的網路連線品質,官方也因此建議人數上限抓在 15 人以內(即使技術上限是 24 人)。
來源:綜合[gamewith訪談摘要](https://gamewith.jp/gamedb/17059/articles/59486)提及「サーバー費もゼロ」與多篇「依host連線品質」的攻略站說明(經WebSearch摘要交叉印證)

**配對機制【事實】**
**沒有智慧配對(matchmaking)系統**,採取的是「公開伺服器瀏覽/自由加入」模式(類似傳統 FPS 的 server browser 文化):只要主機沒設為私人,任何人都能自由進出該房間。搜尋未找到「好友組隊後自動幫忙補位陌生人」這類官方配對功能的證據。
來源:[Yahoo!知恵袋討論](https://detail.chiebukuro.yahoo.co.jp/qa/question_detail/q13329235003)、[しっとり情報局](https://shittokitai.com/im-playing-chameleon-with-two-friends-in-a-random-match/)(經WebSearch摘要)

**平台/跨平台【事實】**
純 PC(Steam/Windows)平台,搜尋全程未出現任何 crossplay(跨平台)或主機版/手機版的證據——僅在開發者訪談中提到「PC版以外的可能性」被媒體追問,語氣是「尚未確定的未來可能性」,而非已實裝功能。
來源:[Game*Spark 開發者訪談標題](https://www.gamespark.jp/article/2026/06/19/168187.html)(WebFetch 403,僅取得標題)

**單人內容【事實,查無官方單人模式】**
**沒有官方單人/離線模式**。Steam 討論區已有多篇玩家直接發文詢問「有沒有練習模式」(標題如"Is there a practice mode")且未見官方正式回應實裝,顯示需求存在但未被滿足。目前唯一變通方案是玩家自己開一個**加密的私人房**,一個人在裡面練習塗色,並非遊戲原生設計的單人內容。
來源:[Steam討論區"Solo Mode"](https://steamcommunity.com/app/4704690/discussions/0/562534952466584073/)、[Steam討論區"Is there a practice mode"](https://steamcommunity.com/app/4704690/discussions/0/571541539431402815/)(WebFetch對Steam頁403,僅取得WebSearch索引到的討論串標題與摘要)

---

### 5. 商業化架構

**價格與版本【事實,查詢日期2026-07-22】**
單一版本,買斷制,約 **$5.99**(依地區/貨幣調整)。**沒有 DLC、沒有季票、沒有內購/微交易、沒有月費**——所有玩家花同樣的錢拿到同樣的內容,這點被多篇英文比價/攻略站一致確認。
來源:[gg.deals比價頁](https://gg.deals/game/meccha-chameleon/)、多篇價格指南站(經WebSearch摘要交叉印證,個別站點內容未逐一查證原文)

**更新頻率【事實】**
免費更新節奏極高,發售(6/10)至今(約6週)版號已知至少推進到 2.9.0/3.0.0,幾乎每週甚至更頻繁推送新地圖、新模式、新角色(如6/25新增角色「キューブ」)、防作弊修正與 UI 功能(如封鎖玩家名牌顯示、隱藏觀戰UI)。這代表商業模式雖是一次性買斷,但團隊仍以近似「早期存取/live-service」的節奏在維運——用免費更新延續話題熱度與媒體曝光,而非直接跟玩家收二次費用。
來源:[4Gamer新角色報導](https://www.4gamer.net/games/007/G100712/20260625023/)、[Steam新聞1.9.0](https://store.steampowered.com/news/app/4704690/view/688635449342689544?l=japanese)(經WebSearch摘要)

**行銷成本【事實,開發者親口確認】**
開發者多次公開強調**廣告費為零**,爆紅完全依賴玩家自發直播/社群傳播。與 HIKAKIN 等名人的合作屬於「爆紅之後」的免費流量置換型行銷,而非付費導流買量。
來源:[gamewith訪談](https://gamewith.jp/gamedb/17059/articles/59486)、[denfaminicogamer訪談報導摘要](https://news.denfaminicogamer.jp/interview/260630w)(經WebSearch摘要,原文WebFetch皆403)

**營收估算【推論,非官方數字,務必標註】**
以「1500萬套 × $5.99」簡單相乘約為 **8,985萬美元流水**——這是研究者用銷量乘單價的粗略估算,**未計入區域定價差異、Steam平台抽成(通常30%)、稅務**,且**未查到開發商自行揭露的實際營收數字**,僅供量級參考,不可視為精確財報數據。

---

### 6. 與 Last War 的架構對照(本節以推論為主,明確標註)

【以下屬研究者根據雙方已知架構特徵的推導比較,非直接引用的文獻對照,查詢日期2026-07-22】

兩者的「簡單」表面相似,但服務的商業目的完全不同:

| 面向 | Last War(手遊買量) | MECCHA CHAMELEON(買斷派對遊戲) |
|---|---|---|
| 簡單服務誰 | 廣告素材的「10秒看懂」轉換率,降低 CPI | 直播觀眾的「10秒看懂」認知門檻,方便跟播/二創 |
| 深度藏哪 | 付費階梯(加速道具、抽卡、戰令)——用**金錢**買深度 | 畫技/心理戰/創意——用**技巧**買深度,課金買不到 |
| 表演素材製造者 | 開發商付費製作的廣告影片(數字很爽的視覺) | 玩家與觀眾自發產生的 UGC(塗色失敗的喜劇瞬間) |
| 獲客成本 | 持續買量,CAC 是核心 KPI | 零廣告費,靠自然傳播,無 CAC 概念 |
| 商業模式終點 | 靠營運與付費階梯拉長 LTV,長期經營 | 買斷制沒有回頭付費機制,熱度衰退後收入曲線本質上封頂 |
| 誰承受留存壓力 | 開發商需持續對投資人/股東證明 DAU、LTV | 沒有這層壓力——「爆紅 25 天回本」本身就是完整的商業終局 |

這個對照也解釋了本報告發現的「反面訊號」:Last War 用付費階梯延長生命週期是**架構自帶的解法**;而 MECCHA CHAMELEON 選擇買斷制+零課金,代表它**架構上沒有留客的金錢誘因**,SteamDB 顯示的同時在線人數暴跌某種程度上是這個商業選擇的自然結果,而非單純的「遊戲玩膩了」——這兩者需要區分開來看待。

---

## 三、反面訊號(對「買斷制派對遊戲壽命」的關鍵對照證據)

1. **【事實,量化證據,查詢日期2026-07-22】同時在線人數暴跌**:SteamDB 顯示尖峰為 **340,534 人**(2026/6/21,發售第11天),但**近30天同時在線人數下滑 84.2%**,目前約 3.3 萬人上下。這是病毒式爆紅派對遊戲典型的衰退曲線(可對照 Fall Guys、Party Animals 等同類前例,但本次搜尋未直接查證該類比是否有文獻明說,屬經驗性聯想,不算查證結果)。
來源:[SteamDB相關X貼文摘要](https://x.com/SteamDB/status/2066549555248677046)、[SteamDB Steam群組公告](https://steamcommunity.com/groups/SteamDB/announcements/detail/671745681362257533)(經WebSearch摘要)

2. **【事實】作弊爭議未完全解決**:出現「自動塗色作弊」(程式自動抓取背景色貼到身體上,直接破壞遊戲最核心的「畫技定生死」精神)、鬼隊武器連射作弊、大量灌水「推薦/vouch」作弊。7/7 的 v2.5.1 更新只處理了連射與推薦濫用兩項,**自動塗色作弊未見官方對策**,社群甚至自發搞出非官方的「作弊者公開處刑箭頭」機制頂替官方防線。
來源:[AUTOMATON報導](https://automaton-media.com/articles/newsjp/20260708-453827/)、[Game*Spark防作弊更新報導](https://www.gamespark.jp/article/2026/07/08/168968.html)(經WebSearch摘要)

3. **【事實,評論來源明確】「Friend Problem」**:PC Gamer 系評測站 RetroGems 標題直指本作有「朋友問題」——好友邀請系統不穩定、缺乏檢舉/管理工具(moderation tools)、介面卡頓,結論是「紙上是神作,要交付完整體驗還需要修補」。
來源:[RetroGems評測](https://retrogems.fr/en/meccha-chameleon-review-pc/)

4. **【推論,單一綜合摘要來源,建議視為方向性訊號而非精確統計】公開野房體驗品質落差**:根據 WebSearch 對多篇評論的綜合摘要,公開/野排場次常「退化」成單純躲暗角而非展現塗色創意,「藝術性」要素若不是跟朋友一起玩幾乎會被忽略——代表核心賣點(塗色創意/表演性)高度依賴「有沒有固定朋友團」這個前提,單人野排的長期黏著度可能顯著低於朋友局。

5. **【事實】無官方單人/練習模式**:僅能用私人房繞道,Steam 討論區已有多篇玩家請願,尚未見官方正式回應或實裝時程。對沒有固定朋友團的玩家,上手門檻與練習手段存在缺口——這與第4點互為因果。

6. **【不確定,收斂結論】未找到付費外觀/數值成長系統**:意味著沒有典型 live-service 遊戲常用來「續命拉長 LTV」的機制(輪轉皮膚、battle pass、賽季)。買斷制決定了此作幾乎沒有「回頭付費」的商業誘因,這與第1點在線人數暴跌互為同一個「架構選擇」的一體兩面,而非兩個獨立問題。

7. **【不確定,來源衝突,需標註】Steam 好評率數字在不同時間點/不同轉述來源間不一致**:SteamDB 早期快照顯示 76.44%(6/15)→80.10%(6/20);另有綜合評測站籠統引述「84–85%」區間;Denfaminicogamer 報導的敘事是評價等級從「やや好評」(約70–79%區間)逐漸爬升到「非常に好評」(約80–94%區間);使用者提供的背景資訊則是「約3.5萬則評論、90%好評」。**本報告無法排除這是抓取時間點不同、或「近期評論」與「所有評論」兩種統計口徑混淆所致**,建議直接查 Steam 商店頁(本次 WebFetch 403 未能驗證)取得當下最準確數字。這個震盪本身也側面印證第2、3點(作弊+好友系統問題)在早期確實影響過評分,後續靠高頻更新逐步回穩。

---

## 四、事實/推論/不確定總覽(快速索引)

- **高信心事實**:2人團隊/2個月開發、零廣告費、P2P架構(故零伺服器費)、買斷$5.99無DLC無課金、銷售里程碑時間軸(4Gamer/Game*Spark/denfaminicogamer多方印證)、SteamDB峰值34萬人與近期84.2%下滑、作弊爭議與部分修補、RetroGems的Friend Problem評測結論、塗色操作細節(F鍵/滴管/材質參數)、三種官方模式與Workshop 99張地圖。
- **合理推論(已標註)**:揮發性UGC設計哲學的商業效果解讀、與Among Us的表演性機制對比、與Last War的架構對照整節、營收估算數字。
- **不確定/查無(已標註)**:精確回合計時秒數的跨模式統一數值、是否存在數值成長或外觀解鎖系統、Steam好評率的當前精確數字、公開野房體驗劣化的量化比例。

---

## 五、來源清單(依 WebSearch 匯總出現的可信度分層)

**官方/一手**
- MECCHA CHAMELEON Steam商店頁 https://store.steampowered.com/app/4704690/MECCHA_CHAMELEON/ (WebFetch 403,僅有WebSearch索引片段)
- 開發者 Lemorion(レモリオン)Twitter/X https://x.com/lemorion1224

**日本主流遊戲媒體(經WebSearch摘要引用,原文多數WebFetch 403)**
- 4Gamer.net(多篇更新/銷售報導) https://www.4gamer.net/games/007/G100712/
- 電ファミニコゲーマー(開發者訪談) https://news.denfaminicogamer.jp/interview/260630w
- ファミ通.com(2.0.0更新報導) https://www.famitsu.com/article/202606/79631
- Game*Spark(多篇,含開發者訪談、防作弊更新、1500萬本報導) https://www.gamespark.jp/
- GAME Watch(配信爆紅分析) https://game.watch.impress.co.jp/docs/kikaku/2118862.html
- AUTOMATON(作弊爭議報導) https://automaton-media.com/articles/newsjp/20260708-453827/
- ゲームウィズ GameWith(開發者訪談) https://gamewith.jp/gamedb/17059/articles/59486

**攻略Wiki/社群分析(經WebSearch摘要)**
- Gamerch 攻略Wiki https://gamerch.com/mecha-chameleon/
- note.com 遊戲設計分析(白坂公一) https://note.com/shira_game/n/n1b287a35eb7f
- note.com 12個秘密分析(だいき) https://note.com/ms_daiki/n/n5bcd5b11dffd
- skypenguin.net 操作教學系列 https://skypenguin.net/

**國際媒體評測**
- PC Gamer評測 https://www.pcgamer.com/games/sports/meccha-chameleon-review/ (WebFetch 403)
- RetroGems評測("Friend Problem") https://retrogems.fr/en/meccha-chameleon-review-pc/
- Game8評測 (經WebSearch摘要引用分數86)
- Metacritic critic/user reviews https://www.metacritic.com/game/meccha-chameleon/

**數據/統計**
- SteamDB https://steamdb.info/app/4704690/ 及其X帳號貼文
- Steam Community討論區(單人模式/練習模式請願) https://steamcommunity.com/app/4704690/discussions/

**低信度/需自行複核(SEO內容農場特徵明顯,本報告僅作交叉印證輔助,未單獨採信)**
- mechachameleon.org、meccha-chameleon.wiki、mecha-chameleon.net、mecchachameleon.io、mecchachameleonwiki.com/.net、mechachameleon.games 等一系列近似域名站點——這些站點在短時間內針對單一爆紅遊戲大量產出雷同的「攻略/價格/人數」內容,結構高度相似,疑似程式化SEO內容農場,本報告只在多個獨立信源交叉印證時才採用其中的具體數字,未單獨引用其獨家說法。

---

## 六、WebFetch 403 複查清單(共9次嘗試,全數403,建議使用者以 /browse 或人工瀏覽器複查)

| # | URL | 嘗試目的 |
|---|---|---|
| 1 | https://store.steampowered.com/app/4704690/MECCHA_CHAMELEON/ | 官方商店頁一手資料(簡介/評論數/好評率/標籤) |
| 2 | https://news.denfaminicogamer.jp/interview/260630w | 開發者訪談全文 |
| 3 | https://game.watch.impress.co.jp/docs/kikaku/2118862.html | 爆紅原因深度分析全文 |
| 4 | https://www.pcgamer.com/games/sports/meccha-chameleon-review/ | 專業評測全文 |
| 5 | https://gamerch.com/mecha-chameleon/ | 攻略Wiki總覽(規則/地圖/模式完整清單) |
| 6 | https://www.famitsu.com/article/202606/79631 | 2.0.0更新內容全文 |
| 7 | https://gamewith.jp/gamedb/17059/articles/59486 | 開發者訪談全文 |
| 8 | https://steamcommunity.com/app/4704690/negativereviews/?browsefilter=toprated | Steam負評原文列表 |
| 9 | https://ja.wikipedia.org/wiki/めっちゃカメレオン | 結構化總覽條目全文 |

以上皆確認非 proxy 政策阻擋(`recentRelayFailures` 為空),屬目標站台自身的反爬蟲防護。若需要這些頁面的完整原文(特別是 #1 官方頁面與 #2/#7 開發者訪談全文),建議由主對話透過 `/browse`(依 CLAUDE.md §1 工具分工守則,互動式瀏覽走 /browse 而非 WebFetch)人工複查。
