# 《Last War: Survival》心理學機制拆解報告

**研究對象**：手遊《Last War: Survival》（開發商 First Fun／北京元趣娛樂，發行商 FUNFLY PTE. LTD，2023 年 8 月上線）
**查詢日期**：2026-07-22（全文所有來源查詢日期同一天，不再逐條重複標註）
**方法限制聲明**：本次研究僅用 WebSearch／WebFetch。WebFetch 在本環境對外站命中率極低——共嘗試 27 次，**26 次遭 403、1 次因工具層級封鎖（web.archive.org）、僅 1 次成功**（gist.github.com 玩家心得全文）。因此報告中大量結論來自 **WebSearch 回傳的摘要片段**而非全文閱讀；凡屬此類，標註「（WebSearch 摘要，原頁 403 未讀全文）」以示與直接讀原文的證據強度不同。WebSearch 額度在研究過程中被用盡（session 共用額度，非本任務獨占），故最後階段補查改用 WebFetch 硬闖新網域，效果有限。以下所有心理機制主張皆按「事實／推論／不確定」三類標註。

---

## 0. 背景事實核查

- 開發商 First Fun（北京元趣娛樂），發行商 FUNFLY PTE. LTD，2023 年 8 月上線。**事實**（WebSearch 摘要，Wikipedia 頁面 403 未讀全文）。
- 營收里程碑：2025-02-15 突破 20 億美元累計玩家消費；2025 年 12 月累計下載約 1.6 億、營收約 26 億美元；2024 全年營收逾 13.1 億美元（Apple 6 億＋Google Play 7.1 億），為 2024 年全球前五大營收手遊；2025 年 11 月單月營收 1.104 億美元，登上全球營收榜首。**事實**（[thinkingdata.io](https://thinkingdata.io/customer-stories/last-war-survival-case-study/)、[pocketgamer.biz](https://www.pocketgamer.biz/last-war-survival-surpasses-2bn-after-record-player-spending-in-early-2025/)、[maf.ad](https://maf.ad/en/blog/last-war-survival/)、[foxadvert.com](https://foxadvert.com/en/digital-marketing-blog/from-1star-reviews-to-13-billion-the-untold-story-of-last-wars-success/) 之 WebSearch 摘要，原頁皆 403）。
- 每下載營收效率約 18 美元／每活躍用戶月均營收約 5 美元，遠高於同類型遊戲的個位數水準。**事實**（WebSearch 摘要綜合多篇來源，原頁 403）。
- 超過半數 App Store／Google Play 評論為 1 星，但營收持續居冠——這個「評分與營收背離」的悖論本身被多篇產業分析文章當作案例討論。**事實**（[foxadvert.com](https://foxadvert.com/en/digital-marketing-blog/from-1star-reviews-to-13-billion-the-untold-story-of-last-wars-success/) WebSearch 摘要）。

---

## 1. 廣告心理：「故意玩爛」為何有效、bait-and-switch 為何留得住人

### 1.1 理論框架（通識，不附來源）
- **能力錯覺／達克效應（Dunning-Kruger Effect）**：低勝任者高估自己能力，看到廣告角色犯蠢會產生「我上我也行」的修正衝動。
- **勝任動機／自我決定理論（White 1959; Deci & Ryan）**：人類有內在的「勝任需求」，看到簡單任務被搞砸，會激發想證明自己能做到的衝動——這比部分文章使用的「reactance（心理抗拒）」一詞更精確；reactance 原意是「自由被剝奪後的抗拒」，與此處「想證明自己更行」的動機機制並不完全相同，此為本報告的**推論性澄清**。
- **登門檻效應／承諾遞增（Foot-in-the-door, Freedman & Fraser 1966）**：先讓對象接受一個小請求（玩 30 秒的簡單小遊戲），會提高其接受後續更大請求（深度投入本體遊戲）的機率。

### 1.2 本遊戲實例（事實，附來源）
- 產業觀察者稱 Last War 的手法是「bait-and-switch done right」：廣告中的躲避／消除小遊戲玩法，**確實**在遊戲開場前幾分鐘真實存在——玩家一打開遊戲，前 4-5 分鐘約 60% 以上時間就是廣告裡那款跑酷／射擊小遊戲，之後才逐漸過渡到 4X 基地經營主體。整體而言，廣告中呈現的玩法只占實際遊戲時間的 20%，其餘 80% 是基地管理。**事實**（[thinkingdata.io](https://thinkingdata.io/customer-stories/last-war-survival-case-study/)、[gfrfund.com](https://gfrfund.com/blog/last-war-mobile-game) 之 WebSearch 摘要，原頁 403）。
- 2024 Q4，官方甚至正面回應「假廣告」爭議，找演員 Antony Starr 拍攝主打「這是真遊戲」的行銷戰役，標語為「開發商真的做出了廣告裡那款遊戲」，單此戰役帶來逾 1250 萬次下載。網路對 Starr 廣告的反應多是困惑與吐槽（「他每支廣告都一臉痛苦」），但也有分析認為找知名演員代言本身就是一種「這遊戲不是騙局」的權威背書策略。**事實**（[Forbes](https://www.forbes.com/sites/callumbooth/2024/10/24/anthony-starrs-fake-mobile-game-adverts-explained/) 之 WebSearch 摘要，原頁 403；TikTok 討論串佐證輿論反應）。
- 學術與產業文章描述「假可玩廣告（fake playables）」的另一層操縱：不只是玩法失真，而是連「互動的可能性」本身都是假的（delayed skip button、誤導性互動提示、自動跳轉商店）——此為手遊廣告產業共通手法的學術描述，**非**專門針對 Last War 的研究，此處為**推論**其同樣適用於本遊戲的廣告策略類型。**推論**（[arxiv.org/2512.17819](https://arxiv.org/pdf/2512.17819)，原研究對象是兒童 App，套用到本遊戲需謹慎）。

### 1.3 為何「被騙」的玩家仍然留下（推論，基於已查證事實的合理推理）
把 §1.2 的事實串起來看：這不是單純的「騙進來就跑不掉」，而是一個**漸進式承諾漏斗**——
1. 廣告的簡單小遊戲本身就是遊戲開場的一部分（不是完全捏造），玩家不會一進門就發現「被騙」，認知失調被降到最低；
2. 前幾分鐘的成功體驗（登門檻效應第一步）建立起「我在玩」的沉浸感；
3. 接著缺乏明顯斷點地滑入 4X 主體，此時玩家已投入時間與帳號進度（見第 2 節沉沒成本）；
4. 一旦被拉進聯盟社交網路（見第 3 節），退出的心理成本已從「刪掉一個 App」升級為「放棄一段社交關係與集體目標」。
換言之，廣告端的「溫和誘導」與遊戲端的「留存機制」是同一套設計邏輯的兩個階段，接口做得平滑，才是所謂「bait-and-switch done right」的真正含義。

---

## 2. 留存心理

### 2.1 損失規避（Loss Aversion，理論通識不附來源）
本遊戲實例：基地被攻擊會損失資源（木材、石料、糧食）、部隊傷亡、城牆耐久度下降；若防禦連續失敗導致「城市起火」，基地甚至會被隨機傳送到地圖其他位置，等同失去經營多時的地理位置與周邊部署。**事實**（[medievalfun.com](https://medievalfun.com/last-war-survival-game-how-to-defend-your-base-city/)、[godlikebots.com](https://godlikebots.com/last-war-survival-base-on-fire-how-to-recover-and-rebuild/) 之 WebSearch 摘要，原頁未直接讀取全文）。損失規避理論預期：玩家對「已擁有資源被搶走」的痛苦感受，遠大於「同等資源尚未獲得」的缺憾感，因此攻擊/被攻擊機制比單純的「獎勵」機制更能驅動玩家回歸遊戲護盤或報復。**推論**（機制與理論的對應關係為本報告推論，未見專文明確以「損失規避」一詞分析本遊戲）。

### 2.2 沉沒成本（Sunk Cost Fallacy，理論通識不附來源）
最有力的證據來自一位實際玩了半年的玩家第一手心得（本報告唯一成功 WebFetch 全文的來源）：
- 該玩家原本打算完全不課金，但半年後改變主意，坦言陷入「就算月收入不到 10 萬美元也會被誘導持續消費以『跟上進度』」的循環。
- 遊戲內有「今日免費等一天、或現在花 10 美元立即完成」的抉擇設計，且明白告知「你不付錢，別人會付，他們明天就會超前你」——直接把沉沒成本焦慮轉化為即時付費壓力。
- 更關鍵的「計劃性報廢」設計：舊制下玩家可以在舊伺服器持續投入重建社群；但現行制度下，每個賽季結束後伺服器會被鎖定，玩家只能靠付費轉服才能延續投入，否則等於被迫放棄先前累積的一切、重新開始。這種「強迫重置」本質上是把玩家的沉沒成本武器化，逼迫用付費來保護既有投入。
以上**事實**（[GitHub Gist 玩家半年心得](https://gist.github.com/Adachi91/60a458ec3fbf542be5ec6cada0c41e7e)，全文已讀取）。
另外，每日任務、每日簽到（VIP 積分 200 點／日）、每 6 小時刷新的「秘密任務」（雷達等級愈高、任務愈多）等設計，讓玩家持續往帳號裡「存入」時間成本，使中斷遊戲的心理門檻隨投入時間增加而升高。**事實**（[lastwarhandbook.com](https://lastwarhandbook.com/guides/daily-tasks-guide) 等站台之 WebSearch 摘要）。

### 2.3 未完成效應／蔡加尼克效應（Zeigarnik Effect，理論通識不附來源）
遊戲內大量倒數計時器：活動頁面顯示剩餘時間、殭屍入侵下一波倒數、「嘉年華登入」活動連續 7 天簽到、季節活動 10-14 天。這類設計理論上會觸發「未完成任務占用心理頻寬」的效應，讓玩家即使不在遊戲內也會惦記著要回去領取或完成。**事實**（倒數計時器與活動長度為 WebSearch 摘要查證之事實；「Zeigarnik 效應」這個具體心理學名稱**查無**任何一篇論及本遊戲的文章明確提及，此處僅為理論套用的**推論**）。

### 2.4 變動比率增強（Variable Ratio Reinforcement，理論通識不附來源）
本遊戲的英雄招募（gacha）機制屬於此類設計，但**查無**針對 Last War 具體抽卡機率（UR/SSR 機率數字）的可靠來源——這方面的 WebSearch 查詢在額度用盡前未能執行，列為**查無**。不過同類機制的一般性學術研究可作為理論佐證：普利茅斯大學研究發現，抽卡開箱時的腦部活動模式與吃角子老虎機類似，稀有獎勵會引發更強的喚起反應（arousal）、心跳加快與更強烈的「再抽一次」衝動；開箱前的動畫本身就透過多巴胺分泌的預期效應而讓人上癮，這與遊戲的實際獎勵無關，是純粹的「期待」被設計成愉悅來源。**事實，但屬通則研究非本遊戲專文**（[PMC7882574](https://pmc.ncbi.nlm.nih.gov/articles/PMC7882574/) 之 WebSearch 摘要，原頁 403 未讀全文）。

---

## 3. 社交心理

### 3.1 聯盟義務與互惠壓力
理論框架：互惠原則（Cialdini）——接受他人幫助後會產生「回報」的心理壓力。本遊戲實例：加入聯盟後，玩家會開始感受到「要對得起隊友」的社交壓力，即使已不享受遊戲本身，也會因「隊友仰賴你出力」而持續遊玩；遊戲因此從娛樂變成一種義務性的雜務，難以停止是因為「停下來會讓隊友失望」。這是一種明確被歸類為「dark pattern」的機制——「社交義務／公會（Social Obligation / Guilds）」。**事實**（[darkpattern.games](https://www.darkpattern.games/pattern/21/social-obligation-guilds.html) 之 WebSearch 摘要，原頁 403 未讀全文；一般性學術研究佐證群體遊玩會提高互惠行為與社會地位，見 [Dmitri Williams 團隊研究](http://dmitriwilliams.com/wp-content/uploads/2022/04/Group-Play-and-Reciprocity-CHB-2022.pdf)）。

### 3.2 階級與權力（聯盟幹部）
聯盟（最多 100 人）內設有 R1-R5 階級，R5（盟主）握有實質權力：設定 3 字元的聯盟標籤（顯示在成員名字旁）、聯盟名稱、招募政策與語言偏好。**事實**（WebSearch 摘要，[packsify.com](https://www.packsify.com/blogs/last-war-survival-alliance-guide) 原頁 403）。這代表遊戲提供了一套現實生活中未必人人可得的「組織領導權」體驗——在現實職場可能只是基層員工的玩家，在遊戲內可以是統率上百人的「盟主」。**推論**：此階級制度本身即是對「權力與地位需求」的直接補償設計，尤其對照第 5 節的目標客群分析更為合理，但目前**查無**任何訪談或設計文件明確承認此為刻意設計動機。

### 3.3 「我服 vs 敵服」的最小團體效應
理論框架：最小團體範式（Minimal Group Paradigm, Tajfel）——即使分組標準完全隨機瑣碎，人類仍會迅速產生「我群 vs 他群」的偏私與敵意，這是形成緊密團體與集體認同最基本的心理機制。本遊戲實例：「跨服戰爭（KvK, Kingdom vs Kingdom）」是連續多天的跨服對戰，整個伺服器被拉去對打另一個伺服器，是遊戲內最高規格的常態內容，也是取得最佳裝備、英雄殘片與稱號的來源；此外「聯盟對決 VS」則是與另一伺服器聯盟進行為期 6 天、逐日不同挑戰的競賽，玩家可以查看對手伺服器整個賽季的成長數據來備戰。**事實**（WebSearch 摘要，多個攻略站台如 [lastwartutorial.com](https://www.lastwartutorial.com/duel-vs/)、[lastwar.farm](https://www.lastwar.farm/last-war-server-tracker)）。**推論**：伺服器與伺服器對抗的設計，等於人工製造出一個放大版的最小團體實驗場——玩家對「本服」的認同與對「敵服」的敵意，會被系統性地用來驅動戰爭動員與消費（見 3.4）。

### 3.4 集體榮譽綁架個人付費
半年玩家心得提到兩個具體機制：其一，頂級聯盟之間會形成「非侵略協議」，且這類協議偏好吸納大額消費者加入——換言之，課金能力本身變成社交資本，影響玩家能否進入強勢聯盟；其二，聯盟內只要有一人購買禮包，全體成員都能獲得小額獎勵，這種設計把個人消費行為包裝成「造福全隊」的集體貢獻，強化了「為了聯盟而課金」的道德誘因。**事實**（[GitHub Gist 玩家心得](https://gist.github.com/Adachi91/60a458ec3fbf542be5ec6cada0c41e7e)全文）。

---

## 4. 付費心理

### 4.1 價格錨定與禮包梯度
理論框架：錨定效應（Kahneman & Tversky）與階梯定價——先讓消費者接觸低價選項降低付費心理門檻，再逐步用「原價 vs 折扣價」製造價值錯覺，誘導往高價位移動。本遊戲實例：官方禮包從 0.99 美元起跳，一路到 99.99 美元（常以「原價 99.99、折扣後 79.99」的錨定方式呈現），另有 156 美元的「全合一組合包」。新手期常見 1-3 美元的「首購優惠」，內容物刻意設計得「划算感」很重（額外建造隊列、UR 英雄等），目的是讓玩家完成「第一次付費」這個心理門檻突破——一旦破戒，後續付費的心理阻力會顯著降低（此為**推論**，基於「登門檻效應」＋「首購優惠」設計動機的合理推斷）。**事實部分**（WebSearch 摘要，[topuplive.com](https://www.topuplive.com/lastwar/)、[thinkingdata.io](https://thinkingdata.io/customer-stories/last-war-survival-case-study/) 等站台，原頁多數 403）。此外，遊戲內販售的基地外觀「皮膚」定價 100-500 美元起，且附帶永久性能力加成——這模糊了「純外觀消費」與「數值付費」的界線，讓玩家難以用「只是好看」來合理化不去比較戰力影響。**事實**（GitHub Gist 玩家心得全文）。

### 4.2 鯨魚生態：免費玩家是鯨魚的內容與觀眾
理論框架（通識）：手遊產業將付費玩家分為鯨魚（重氪）、海豚（中氪）、小魚（免費／微氪）。產業數據顯示：鯨魚約占付費玩家的 10-15%（或全玩家的 0.15%），卻貢獻 50-70% 的內購營收；小魚可能占玩家數 90%，卻貢獻不到 10% 營收。**事實**（WebSearch 摘要，多篇產業文章交叉確認，如 [udonis.co](https://www.blog.udonis.co/mobile-marketing/mobile-games/mobile-games-whales)）。產業論述將此描述為「共生生態」：鯨魚的消費補貼了小魚的免費體驗，而龐大的免費玩家基數則讓遊戲的社交面（多人互動、聯盟戰、伺服器戰）有意義——沒有足夠的「觀眾」與「對手」，鯨魚砸錢買來的強度就沒有展示與碾壓的對象。**事實（生態論述）+ 推論（套用到 Last War 的具體效果）**：本遊戲的伺服器戰、聯盟排行、KvK 設計，結構上正好需要大量免費玩家作為「戰場的其他人」，讓鯨魚的支配感有具體對象可以施展——這點在本研究中**查無**專文明確以「Last War 的免費玩家＝鯨魚的觀眾」為題討論，屬本報告推論。

### 4.3 限時 FOMO
VIP 積分在特定活動期間會有 30-50% 的回饋加成，聯盟成員若把鑽石消費集中在這個「返利窗口」內使用，可比窗口外消費多獲得 1.5 倍的 VIP 進度效率。另外，只買禮包卻不買月卡的玩家，其 VIP 投資效率被估算僅約 70%（相對於買月卡者的 100%），月卡還額外開放第四路行軍隊伍，直接影響聯盟協同作戰能力。**事實**（WebSearch 摘要，[theriagames.com](https://theriagames.com/guide/last-war-survival-vip-points-guide/)、[packsify.com](https://www.packsify.com/blogs/last-war-survival-vip-points-showdown)，原頁 403）。這種「限時倍率」設計精準地把 FOMO（怕錯過）與「不消費就是效率損失」的損失規避感受疊加在一起。

### 4.4 VIP 進度條的承諾一致性
理論框架：承諾一致性（Cialdini）——人一旦公開或實質投入某個方向（如已升到 VIP 10），會傾向持續投入以維持自我形象與先前決策的一致性，中途放棄會產生「先前投入都浪費了」的認知失調。本遊戲實例：VIP 系統共 18 級，靠每日登入（200 點／日）、聯盟贈禮、活動獎勵可緩慢免費累積，但等級愈高所需點數愈高。關於「衝到 VIP 18 要花多少錢」，本研究查到**兩個差距懸殊的數字**，需明確標註為**不確定**：
- 產業攻略站（WebSearch 摘要，[packsify.com](https://www.packsify.com/blogs/last-war-survival-vip-18-cost)，原頁 403）估算「優化購買策略下」約 1.5-2.5 萬美元；
- 而本研究唯一完整讀取全文的玩家半年心得（社群估算）指出 VIP 18 約需 50 萬美元。
兩者相差近 20-30 倍，可能反映「理論最優路徑」與「真實市場／玩家社群共識」之間的巨大落差，也可能是不同計算基準（例如是否計入活動期間的點數貶值、匯率、地區定價差異）所致。本報告**不採信任一數字為定論**，僅並陳供交叉參考。

---

## 5. 目標客群心理：給「有錢沒時間」的中年男性設計的遊戲

### 5.1 支配感／成就感補償
人口統計事實：美、英、日、韓等市場中，策略類手遊玩家 65-69% 為男性，多數集中在 25-44 歲；付費玩家中 53% 表示遊玩動機是「沉浸在另一個世界的幻想感」，43% 表示動機是「在遊戲中獲得進展與成就感」。**事實**（WebSearch 摘要，多篇產業報告交叉確認，如 [maf.ad 人口統計](https://maf.ad/en/blog/mobile-gamers-demographics/)）。「中年男性藉由遊戲補償現實中年危機／職場天花板」是一個廣為流傳的通俗心理學敘事，本研究**查無**任何直接訪談 Last War 玩家或開發商證實此因果關係的文章——這部分必須明確標註為**推論**：把「玩家多為 25-44 歲男性」＋「動機偏向幻想沉浸與成就感」＋「聯盟 R5 提供現實中少見的組織領導權」（見 3.2）三個查證過的事實串起來，合理推測遊戲設計精準命中了「現實成就感有限、但仍有經濟餘裕與地位渴望」的中年男性族群，讓其在遊戲裡當「戰爭領主」——但這是本報告的推論鏈，不是查證到的因果研究結論。

### 5.2 低操作門檻＋高數值深度
理論與事實結合：Idle 類設計理念強調「尊重玩家時間」——不需要學複雜操作，關掉 App 之後進度仍會持續累積，適合無法時刻專注的忙碌成年玩家；而低 APM（每分鐘操作數）但系統複雜的設計，可以做到「操作簡單、但策略天花板高」，讓沒有反應速度優勢、但有耐心規劃資源分配的玩家一樣能建立起「精通感」。**事實（理論通則）**（WebSearch 摘要綜合多篇 idle game 設計文章）。這與 Reddit 玩家社群的具體抱怨互相印證：本遊戲**絕大多數營收來自販售「時間加速道具（Time Accelerators）」**——建築／科研／訓練的等待時間動輒數天，免費玩家只能乾等，付費玩家能在幾分鐘內完成同樣進度。**事實**（WebSearch 摘要，Reddit 社群討論綜合）。

### 5.3 為什麼「空虛簡單」是賣點而不是缺點（本報告核心推論）
把 §5.2 的兩個事實疊在一起看，可以得出一個關鵼推論：**遊戲的「空虛感」本身就是被販售的商品**。核心邏輯是——
1. 遊戲刻意把大部分「玩法」設計成被動等待（升級倒數、行軍時間、建築排隊），這正是 idle 設計哲學「尊重玩家時間」的另一面：你不需要投入注意力，但你也**幾乎沒有事可做**；
2. 這個「空」不是設計失敗，而是製造出一個明確的付費痛點——等待本身變得可以被「加速道具」直接買斷，時間 = 金錢的兌換關係被具體化、商品化；
3. 對「有錢沒時間」的客群來說，操作簡單代表不需要學習成本、不需要長時間盯著螢幕操作；而數值深度（英雄搭配、資源分配、聯盟戰術）則保留了「策略遊戲」的自尊敘事——玩家可以告訴自己「我在玩一個有深度的戰略遊戲」，而不是「我在等進度條跑完」；
4. 因此「空虛簡單」對其他客群（例如想要即時操作反饋、追求手感的核心玩家）是缺點，但對本遊戲鎖定的客群（時間稀缺、但願意用金錢購買效率與地位的中年男性）而言，恰恰是「不用花心思、只要花錢」的產品承諾——這正是遊戲從廣告階段就在傳達的訊息（簡單到廣告裡看起來像 4 歲小孩都能玩），一路貫穿到付費設計（花錢＝跳過等待＝跳過"空虛"）。
以上為**推論**，基於已查證的「時間加速道具是主要營收來源」＋「idle 設計理念」＋「目標客群人口統計」三組事實的合理串接，並非直接引用某篇文章的明確論述。

---

## 6. 倫理面：Dark Patterns 討論

學術與產業界對這類遊戲設計已有系統性批評，但本研究**查無任何一篇明確以「Last War: Survival」為研究對象或案例點名**的學術論文——以下引用的論文多是分析「2024 年最高營收 F2P 遊戲」或「頭部課金手遊」整體樣本，Last War 身為 2024 年前五大營收手遊，**極可能**被包含在樣本內，但**未經全文確認**，此點列為**不確定**。
- 《Dark Patterns in Games: An Empirical Study of Their Harmfulness》（2025）分析 2024 年最高營收 F2P 遊戲中的黑暗模式作為核心變現策略，按時間、金錢、社交三個維度分類。**事實**（WebSearch 摘要，[scitepress.org PDF](https://www.scitepress.org/Papers/2025/133658/133658.pdf)，原頁未直接讀取全文）。
- 《Level Up or Game Over: Exploring How Dark Patterns Shape Mobile Games》（2024）訪談玩家後歸納出最常被提及的黑暗模式：付費致勝（Pay to Win）、預約式遊玩（Playing by Appointment）、每日獎勵、人為稀缺（Artificial Deficit）、沉沒成本利用（Invested Value）、轉蛋與戰利品箱——受訪玩家多以「被騙」「令人挫折」描述這些機制的感受。**事實**（WebSearch 摘要，[arxiv.org/2412.05039](https://arxiv.org/pdf/2412.05039)，原頁 403）。
- 一份針對 1,496 款手遊使用者生成資料的分析，發現超過 85,000 個黑暗模式實例，顯示操縱性設計在手遊產業已是普遍現象而非個案。**事實**（WebSearch 摘要）。
- 本遊戲本身的具體爭議：有評測整理指出，Last War 的退款政策具爭議性——傳聞退款會導致遊戲內「信用分數」被扣、甚至帳號被封鎖，被部分輿論批評為「中國遊戲公司的霸道條款」；同時，該篇分析也指出 Last War 這種「四位數心算」式的假廣告手法，已被其他中國量產型 SLG 手遊競相仿效，成為該品類的行業標準套路。**事實，但證據強度中等**（WebSearch 摘要，[namuwiki](https://en.namu.wiki/w/%EB%9D%BC%EC%8A%A4%ED%8A%B8%20%EC%9B%8C:%20%EC%84%9C%EB%B0%94%EC%9D%B4%EB%B2%8C) 為維基型協作百科，可信度低於一手新聞或官方公告，此處退款政策細節未見第二來源交叉驗證，列為**不確定**）。
- 學術界對「付費致勝」的態度並非全盤負面：有研究專門探討玩家對競技類遊戲內購「公平性」的主觀感受，顯示玩家對「付費致勝」與「付費作弊」有不同的道德評價光譜，不是所有付費機制都被玩家一致視為不公。另一份代表性人口樣本研究則發現「付費致勝」遊戲與賭博傾向存在相關性。**事實**（WebSearch 摘要，[ACM DL](https://dl.acm.org/doi/10.1145/3549510)、[PMC9411233](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9411233/)）。

---

## 7. 反面訊號（已主動查找）

本研究特別查詢「dark pattern 效力被高估／玩家理性消費」角度，誠實回報結果：**搜尋結果幾乎一面倒支持「黑暗模式確實有效且被廣泛採用」的論述，未查到有份量的學術文章主張這類機制「效力被誇大」**。但仍找到幾個可視為反面或修正訊號的材料，如實列出：

1. **「bait-and-switch done right」本身就是對「純欺騙論」的部分修正**：多篇產業分析強調，Last War 的廣告小遊戲「確實存在」於本體遊戲開場，並非無中生有的純捏造畫面，這使其有別於同類「完全造假」的廣告手法，一定程度反駁了「玩家純粹被騙」的簡化敘事。（[thinkingdata.io](https://thinkingdata.io/customer-stories/last-war-survival-case-study/) WebSearch 摘要）
2. **鯨魚生態的產業論述本身帶有「良性補貼」框架**：部分產業文章將「鯨魚支撐免費玩家體驗」描述為一種互利生態，而非單向剝削，且指出「只顧鯨魚」的策略其實風險高、不可持續，促使產業近年轉向更均衡的多層級付費設計。（[udonis.co](https://www.blog.udonis.co/mobile-marketing/mobile-games/market-whales) WebSearch 摘要）
3. **玩家對「公平性」的評價存在光譜，非鐵板一塊**：學術研究顯示玩家會區分「付費致勝」與「付費作弊」，顯示玩家並非全數視類似機制為不可接受，部分消費行為背後可能有玩家自己權衡過的合理性判斷。（ACM 論文摘要）
4. **玩家自身的能動性證據**：本研究唯一完整讀取的第一手玩家心得，作者本人在深入體驗後選擇「抵抗付費壓力、建議只玩免費內容」，顯示即使身處這套設計中，玩家仍保有辨識機制並做出理性選擇的能力，並非所有人都會被機制「俘虜」。（GitHub Gist 全文）
5. **SLG 品類本身正出現「反其道而行」的市場訊號**：中文遊戲產業討論指出，傳統 SLG「又肝又氪」模式近年正面臨挑戰，部分新作開始標榜「不強迫肝、不強迫課金」以爭取年輕客群，顯示 Last War 這種重氪重肝模式並非業界唯一或必然的成功公式，而是鎖定特定客群（如本報告第 5 節分析）的策略選擇，非不可挑戰的鐵律。（WebSearch 摘要，中文遊戲媒體綜合）

**結論**：反面訊號存在，但強度普遍弱於正面（機制確實有效）的證據；且反面訊號多屬「修正敘事的簡化程度」與「非全部玩家都受害」，並未推翻「這些心理機制被系統性運用於留存與付費設計」這個核心判斷。

---

## 8. 來源清單

| # | 標題／說明 | URL | 查詢日期 | 取得方式 |
|---|---|---|---|---|
| 1 | The $2 Billion Bait-and-Switch: Inside Last War: Survival's Success | https://thinkingdata.io/customer-stories/last-war-survival-case-study/ | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 2 | Why Last War Is Winning the 4X Game | https://naavik.co/digest/how-last-war-is-winning-the-4x-game/ | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 3 | Last War Survival: The Secrets Behind Its $2.6 Billion Revenue | https://maf.ad/en/blog/last-war-survival/ | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 4 | How Last War: Survival Raked in $1.6 Billion in 18 Months | https://foxdata.com/en/blogs/how-last-war-survival-raked-in-16-billion-in-a-mere-18-months/ | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 5 | How Does Last War Make Huge Profits Despite 1-Star Ratings | https://foxadvert.com/en/digital-marketing-blog/how-does-last-war-survival-game-make-huge-profits-despite-half-of-its-ratings-being-1star/ | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 6 | From 1-Star Reviews to $1.3 Billion | https://foxadvert.com/en/digital-marketing-blog/from-1star-reviews-to-13-billion-the-untold-story-of-last-wars-success/ | 2026-07-22 | WebSearch 摘要 |
| 7 | Last War: Survival surpasses $2bn (PocketGamer.biz) | https://www.pocketgamer.biz/last-war-survival-surpasses-2bn-after-record-player-spending-in-early-2025/ | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 8 | Last War: Survival Game — Thoughts After Half a Year Playing It | https://gist.github.com/Adachi91/60a458ec3fbf542be5ec6cada0c41e7e | 2026-07-22 | **WebFetch 全文（唯一成功）** |
| 9 | Antony Starr's 'Fake Mobile Game' Adverts, Explained (Forbes) | https://www.forbes.com/sites/callumbooth/2024/10/24/anthony-starrs-fake-mobile-game-adverts-explained/ | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 10 | Why Mobile Game "Fail" Ads Work: The Psychology Behind It | https://upperechelon.gg/why-mobile-game-fail-ads-work-the-psychology-behind-it/ | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 11 | Leveraging Cognitive Biases in Mobile Game Ads | https://segwise.ai/blog/cognitive-biases-in-mobile-game-ads | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 12 | Playful but Persuasive: Deceptive Designs in Mobile Apps for Children | https://arxiv.org/pdf/2512.17819 | 2026-07-22 | WebSearch 摘要 |
| 13 | DarkPattern.games — Social Obligation / Guilds | https://www.darkpattern.games/pattern/21/social-obligation-guilds.html | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 14 | DarkPattern.games — Pay to Win | https://www.darkpattern.games/pattern/18/pay-to-win.html | 2026-07-22 | WebSearch 摘要 |
| 15 | Level Up or Game Over: Exploring How Dark Patterns Shape Mobile Games | https://arxiv.org/pdf/2412.05039 | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 16 | Dark Patterns in Games: An Empirical Study of Their Harmfulness | https://www.scitepress.org/Papers/2025/133658/133658.pdf | 2026-07-22 | WebSearch 摘要 |
| 17 | Pay to Win or Pay to Cheat（ACM，玩家公平性感知研究） | https://dl.acm.org/doi/10.1145/3549510 | 2026-07-22 | WebSearch 摘要 |
| 18 | Pay-to-Win Gaming and its Interrelation with Gambling | https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9411233/ | 2026-07-22 | WebSearch 摘要 |
| 19 | Rare Loot Box Rewards Trigger Larger Arousal（普利茅斯大學研究） | https://pmc.ncbi.nlm.nih.gov/articles/PMC7882574/ | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 20 | Last War: Survival — NamuWiki（退款政策爭議） | https://en.namu.wiki/w/%EB%9D%BC%EC%8A%A4%ED%8A%B8%20%EC%9B%8C:%20%EC%84%9C%EB%B0%94%EC%9D%B4%EB%B2%8C | 2026-07-22 | WebSearch 摘要 |
| 21 | Last War Survival VIP 18 花費 | https://www.packsify.com/blogs/last-war-survival-vip-18-cost | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 22 | Last War VIP Points Guide (TheriaGames) | https://theriagames.com/guide/last-war-survival-vip-points-guide/ | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 23 | Last War VIP 積分實戰效率（Packsify） | https://www.packsify.com/blogs/last-war-survival-vip-points-showdown | 2026-07-22 | WebSearch 摘要 |
| 24 | Last War Survival Alliance Guide（R1-R5 階級） | https://www.packsify.com/blogs/last-war-survival-alliance-guide | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 25 | Alliance Duel VS 說明 | https://www.lastwartutorial.com/duel-vs/ | 2026-07-22 | WebSearch 摘要 |
| 26 | Last War Server Tracker（KvK 相關） | https://www.lastwar.farm/last-war-server-tracker | 2026-07-22 | WebSearch 摘要 |
| 27 | Mobile Gamers Demographics（maf.ad 人口統計） | https://maf.ad/en/blog/mobile-gamers-demographics/ | 2026-07-22 | WebSearch 摘要 |
| 28 | What Is a Whale in Gaming（Udonis 鯨魚生態） | https://www.blog.udonis.co/mobile-marketing/mobile-games/mobile-games-whales | 2026-07-22 | WebSearch 摘要 |
| 29 | How to Market to Whales（Udonis） | https://www.blog.udonis.co/mobile-marketing/mobile-games/market-whales | 2026-07-22 | WebSearch 摘要 |
| 30 | Last War Survival Base Defense（基地被攻擊機制） | https://medievalfun.com/last-war-survival-game-how-to-defend-your-base-city/ | 2026-07-22 | WebSearch 摘要 |
| 31 | Last War Survival Base On Fire（基地起火機制） | https://godlikebots.com/last-war-survival-base-on-fire-how-to-recover-and-rebuild/ | 2026-07-22 | WebSearch 摘要 |
| 32 | Last War Daily Tasks Guide（每日任務設計） | https://lastwarhandbook.com/guides/daily-tasks-guide | 2026-07-22 | WebSearch 摘要 |
| 33 | Group Play and Reciprocity（互惠與群體遊玩學術研究） | http://dmitriwilliams.com/wp-content/uploads/2022/04/Group-Play-and-Reciprocity-CHB-2022.pdf | 2026-07-22 | WebSearch 摘要 |
| 34 | From Gameplay to Marketing: Inside Last War | https://gfrfund.com/blog/last-war-mobile-game | 2026-07-22 | WebSearch 摘要（原頁 403） |
| 35 | Last War: Survival Game（Wikipedia） | https://en.wikipedia.org/wiki/Last_War:_Survival_Game | 2026-07-22 | WebSearch 摘要（原頁 403） |

理論通識（損失規避、沉沒成本、變動比率增強、Zeigarnik 效應、互惠原則、最小團體範式、承諾一致性、錨定效應、登門檻效應、達克效應）依任務指示不逐條附來源，屬心理學教科書級別共識知識。

---

## 9. 被 403 擋掉、值得本機複查的頁面（依價值排序）

以下頁面在 WebSearch 摘要中顯示內容豐富、但 WebFetch 皆遭 403，若使用者本機瀏覽器或其他管道可讀取，建議優先複查，資訊密度可能遠高於本報告已用的摘要片段：

1. **https://thinkingdata.io/customer-stories/last-war-survival-case-study/** — 官方案例研究，很可能有完整轉化漏斗數據與客戶（First Fun）視角的第一手說法，是本報告多處「bait-and-switch」細節的源頭，非常值得全文複查。
2. **https://naavik.co/digest/how-last-war-is-winning-the-4x-game/** — 產業分析媒體 Naavik 的深度拆解文，標題直指「為何 Last War 能贏得 4X 賽道」，推測內容深度高，本報告完全沒能讀到全文，是最大缺口。
3. **https://www.gamerefinery.com/what-drives-success-in-4x-strategy-slg-games-part-1/** 與 **part-2** — GameRefinery 是專業手遊市場研究機構，這兩篇專門分析 4X/SLG 品類成功要素，可能含玩家動機的量化數據，本報告完全未讀到內容。
4. **https://arxiv.org/pdf/2412.05039**（Level Up or Game Over 論文）— 學術論文原文，本報告只拿到摘要層級資訊，若能讀全文可補上研究方法、樣本數、玩家訪談逐字稿等細節，大幅提升第 6 節的證據強度。
5. **https://en.wikipedia.org/wiki/Last_War:_Survival_Game** — 維基百科條目通常資訊完整且有註腳可延伸查證，本報告連這個最基本的百科頁面都被 403，建議優先複查以核實背景事實段落。
6. **https://gfrfund.com/blog/last-war-mobile-game** — 標題顯示涵蓋「玩法到行銷」的完整分析，且提及日本／美國市場對比，可能補足本報告缺乏的地區差異視角。
7. **https://www.forbes.com/sites/callumbooth/2024/10/24/anthony-starrs-fake-mobile-game-adverts-explained/** — Forbes 為主流媒體，若能讀全文，Antony Starr 代言爭議的第 1.2 節可補上更可靠的一手引述。
8. **https://www.packsify.com/blogs/last-war-survival-vip-18-cost** — 用於解決第 4.4 節「VIP 18 要花多少錢」兩個數字互相矛盾（1.5-2.5萬 vs 50萬美元）的疑點，值得優先複查以判斷哪個數字更可信。
9. **https://www.arcadepunks.com/is-last-war-survival-a-real-game-complete-analysis/** — 標題顯示是完整分析文，可能有獨立於本報告已用來源的觀點。
10. **https://andrewprogames.com/**（該篇中文無課玩家心得）— 中文玩家第一手心得，若能讀取，可補足本報告偏英文來源的視角落差，且更貼近台灣╱華語圈玩家的具體感受描述。

另有 **web.archive.org**（Wayback Machine）在本環境被工具層級整體封鎖（非 403，是「Claude Code 無法從 web.archive.org 取得」），這代表連「查歷史存檔」這條路線也走不通——若使用者本機環境沒有這個限制，透過 Wayback Machine 讀取上述 403 頁面的存檔版本，是最可能一次解決多數缺口的方法。

---

## 字數與完整度自我檢查
本報告以繁體中文撰寫，含六大研究項目逐項覆蓋（廣告心理、留存心理、社交心理、付費心理、目標客群心理、倫理面）、理論與實例分開陳述、事實/推論/不確定三類標籤明確區分、反面訊號專節、來源清單與 403 複查清單兩節皆已完成，正文（不含表格與清單）字數遠超過 2500 字要求。
