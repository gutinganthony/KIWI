# 《Last War: Survival》營收獲利結構與可複製性研究

**研究範圍**：營收模式細節＋可複製性評估（小團隊／個人＋AI）
**查詢日期**：2026-07-22（以下所有來源查詢日期均同此，不再逐條重複標註，除非另有說明）
**方法限制**：本研究僅用 WebSearch／WebFetch。本環境 WebFetch 對絕大多數外站回傳 403（本次嘗試 8 個站台，8 個全部失敗，清單見文末），故以下數字多數來自 WebSearch 工具回傳之搜尋引擎摘要／多來源交叉整理，並非我方直接讀取原始頁面全文核對。凡搜尋摘要內部有矛盾或無法二次驗證者，已於內文明確標註「不確定」。WebSearch 額度已於研究後段用罄（200/200），故清單中部分項目（如 37 Games、Scopely 團隊規模）標記「查無」，非徹底搜尋後仍查無，而是額度耗盡前未及查證，已如實註記。

---

## 摘要結論

1. **Last War 是「重買量＋重氪金＋重營運」的資本密集型生意，不是玩法或技術創新的產物**——核心數值放置（4X/COK-like）玩法在品類內已存在十年以上，其勝出關鍵是砸錢買量的規模、鯨魚玩家變現系統的精緻度、以及超過一年半的持續迭代與 LiveOps 投入。
2. **直接複製 Last War 這個「規模」對小團隊／個人＋AI 幾乣不可能**：這是資金門檻（數千萬至上億美元買量預算）、組織門檻（千人級發行公司）、時間門檻（開發 20 個月＋之後至少 12 個月買量迭代才起量）三重疊加的遊戲，AI 工具能壓低的是製作成本，壓不低買量的拍賣機制與資金鎖定期。
3. **但「SLG 賺錢公式」本身在縮小規模後仍可複製**：微信小游戲生態、SLG+輕度玩法融合（塔防/farm/卡牌）等次類型，已有真實的 5 人團隊案例（《遺棄之地》）在數日內衝進小游戲暢銷榜前段。個人＋AI 現實可行的路徑不是「做下一個 Last War」，而是「用 AI 低成本試錯，切入小游戲生態或混合休閒（hybrid-casual）等輕量賽道」。

---

## 1. 變現結構

**收入構成**：Last War 幾乎全部營收來自 IAP（App 內購買），廣告變現占比極低甚至可忽略——遊戲內原生展示廣告很少，僅有「觀看廣告換取獎勵」的獎勵式廣告（rewarded video）作為輔助機制，並非營收支柱。來源：[Udonis blog（透過 WebSearch 摘要）](https://www.blog.udonis.co/statistics/last-war-survival)、[MAF blog（透過 WebSearch 摘要）](https://maf.ad/en/blog/last-war-survival/)，查詢日期 2026-07-22。**性質：事實（多來源交叉一致）**。

**變現機制細節**（事實，來源同上＋[FoxAdvert](https://foxadvert.com/en/digital-marketing-blog/how-does-last-war-survival-game-make-huge-profits-despite-half-of-its-ratings-being-1star/)搜尋摘要）：
- **VIP 永久進度軌道**：累積付費解鎖建造/研究/訓練/治療加速，付費與遊戲核心體驗深度綁定，不是單純「付錢變強」而是「付錢變快」。
- **Battle Pass（賽季戰令）＋ Monthly Pass（訂閱制月卡）**：覆蓋中低額穩定付費玩家。
- **英雄抽卡（Gacha）機制**：隨機掉落製造重複消費動機。
- **禮包輪替**：新手禮包、中額值感包、PvP 事件期間的高額限時禮包，隨賽季/戰爭事件動態調整。

**關鍵財務指標**（第三方估計，來源 WebSearch 摘要交叉 Sensor Tower／Naavik／Udonis 系列文章，查詢日期 2026-07-22）：
- 單次下載平均營收（revenue per download）：約 **$18**——品類內多數同型遊戲僅個位數美元，此為極端值，顯示 Last War 是「鯨魚與中額付費者」機器，非走量產品。
- iOS 美國市場 ARPDAU：約 **$16／日**（僅美國 iOS 這一高價值切片，非全球混合值）。
- 全平台混合月活躍用戶月營收：約 **$5／月**。
- **注意（不確定）**：上述兩個數字若直接换算會不一致（$16/日 若延伸至全月遠超 $5/月），合理解釋是前者為美國 iOS 高值用戶切片、後者為全球混合 MAU 平均，但因無法直接讀取原始方法論頁面（Sensor Tower 頁面 403），無法確認兩者統計口徑是否一致，列為「不確定」，僅供量級參考。
- DAU/MAU 比例：約 **16.3%**（中重度 4X 遊戲的典型模式：核心玩家每日登入，長尾玩家間歇性回歸）。
- 月活躍用戶（MAU）：全平台約 **1,710 萬**，其中 iOS 約 **900 萬**。
- iOS vs Android 營收占比：約 **55% : 45%**，App Store 略勝，反映 iOS 用戶單價更高（此為單一搜尋摘要來源，未能交叉第二來源獨立驗證，列為**第三方估計，信心中等**）。

**iOS / Android / 第三方支付（web shop）分布**：官方 Last War 是否有網頁直充管道（bypass app store 拆成）——**查無高品質來源**。搜尋僅返回大量「代充平台」廣告內容農場網站（LootBar、LDShop、TopUpLive 等第三方代充網站），這類站台商業動機是導流其代充服務，內容不具查證價值，故不採信、不引用其具體數字。若 Jake 需要這塊資訊，建議直接人工訪問 Last War 官網確認是否有官方 web shop。

---

## 2. 成本結構

**平台抽成**：App Store／Google Play 標準抽成 **30%**（年營收前 $100 萬美元部分兩大平台均降至 **15%**，超過部分維持 30%）。來源：[Statista 全球商店抽成統計（WebSearch 摘要）](https://www.statista.com/statistics/975776/revenue-split-leading-digital-content-store-worldwide/)，查詢日期 2026-07-22。**性質：事實**（平台規則公開資訊，跨多來源一致）。

**買量（UA）占營收比例**——這是 SLG 品類成本結構中最關鍵、也是最傷本的一項：
- 新品階段：**50%–60%** 營收再投入買量（範例：《末日：最後生還者》Doomsday: Last Survivors 類產品）。
- 成熟穩定期：**30%–35%**（範例：《王國紀元》King's Chronicle 類產品）。
來源：WebSearch 摘要整理自中國遊戲產業報導群（騰訊新聞／GameRes／知乎相關文章），查詢日期 2026-07-22。**性質：第三方估計，原始出處單篇文章名稱不明確，建議本機二次查證**。
- **矛盾點需揭露**：另有一則搜尋摘要提到「SLG 平均行銷預算占營收 9%」，與上述 30–60% 差距懸殊。9% 這個數字疑似指「已進入超長線穩定期、幾乎停止買量的老產品」的維持性行銷支出，或是統計口徑不同（例如只算純廣告代理費而非全部買量媒體費）；因兩者證據強度不對等（30–60% 有多篇獨立文章交叉、且與「SLG 是買量成本最高品類」的產業共識吻合），本報告採信 **30–60%** 區間，9% 數字列為存疑不採用，特此揭露避免誤導。

**買量單價（CPI）**：
- 中國市場：Android 約 **人民幣 60–80 元**，iOS 約 **人民幣 100–120 元**（約合 $8–11 / $14–17 美元，依匯率換算）。來源：知乎/GameRes 群搜尋摘要，查詢日期 2026-07-22。
- 全球市場另一口徑：2023 年初 SLG 基準 CPI 約 **$30**，2023 年底漲至 **$40 以上**（漲幅逾 30%）。來源：WebSearch 摘要（lancaric.me 系列文章），查詢日期 2026-07-22。
- 兩個口徑差距大（中國本地 CPI vs 全球歐美市場 CPI），屬正常現象（區域市場購買力與競價強度不同），非矛盾，但**性質：第三方估計，區域口徑需注意不要混用**。

**淨利率量級**：
- 一般行動遊戲產業基準：新創/早期studio 淨利率約 **5%–10%**，營運成熟、變現優化後可達 **20%–30%**。來源：WebSearch 摘要一般產業分析文章，查詢日期 2026-07-22。**性質：第三方估計，非 SLG 專屬，屬泛用型基準，SLG 因買量占比更高，實際淨利率可能低於此區間，尤其在買量投入期**。
- SLG 立項回本示意（中文產業文章案例）：若研發成本 1,000 萬人民幣，發行分成約 20%，則至少需要 **5,000 萬人民幣流水**才能勉強回本——這只是打平研發成本，尚未計入買量與營運支出。來源：[GameRes〈發行公司玩不起的SLG遊戲〉（WebSearch 摘要）](https://www.gameres.com/780614.html)，查詢日期 2026-07-22。**性質：產業案例式推算，非 Last War 專屬數字，但可作為品類量級參照**。

**我方推算的損益結構輪廓**（明確標示：這是本報告自行組裝多個獨立來源數字而成的推論，非單一來源直接提供，僅供量級參考）：

| 項目 | 占營收比例（估） | 依據 |
|---|---|---|
| 平台抽成 | ~25–30%（iOS/Android 混合，扣除部分小開發者優惠） | Statista |
| 買量/UA | 30%（成熟期）至 60%（成長期） | 產業報導交叉 |
| 研發＋LiveOps＋伺服器＋當地化＋管理費用 | 估 10–20%（缺乏直接數字，為餘額推算） | 本報告推論 |
| **淨利率** | **成長期可能個位數甚至虧損；規模化成熟期樂觀情境下 10–20%+** | 本報告推論，信心中等偏低 |

**團隊規模參照**（事實，用以衡量「做到 Last War 這個量級」需要多大組織）：
- FunPlus（同賽道另一巨頭，State of Survival/Top War 系列發行商）：CTO 受訪提及團隊規模達 **1,700 人**。來源：[GameLook／脈脈（WebSearch 摘要）](http://www.gamelook.com.cn/2021/10/458252)，查詢日期 2026-07-22。
- Century Games（Whiteout Survival 開發商）：全球員工 **超過 1,000 人**。來源：[Century Games 官網 About Us（WebSearch 摘要）](https://www.centurygames.com/about-us/)，查詢日期 2026-07-22。
- Lilith Games（Rise of Kingdoms 開發商）：全球員工 **超過 2,300 人**。來源：[PocketGamer.biz（WebSearch 摘要）](https://www.pocketgamer.biz/inside-mobile-hitmaker-lilith-games/)，查詢日期 2026-07-22。
- **FirstFun／元趣娛樂（Last War 原開發商）本身的員工人數：查無**。多次搜尋（含中文「元趣娛樂 員工規模」等關鍵字）均未找到具體數字，WebSearch 額度已於此項查證前用罄，如實註記為「查無」而非「無此資訊」。

**開發時程**（事實）：Last War 於 **2021 年 12 月 20 日**開始開發，**2023 年 8 月 2 日**全球上線，開發期約 **1 年 8 個月**。上線首月營收僅 **$287,000**，遠非爆款起手——真正放量發生在其後：2024 年 1 月月營收約 $30M，成長至 2024 年 12 月 $138M（成長 360%）。來源：WebSearch 摘要交叉多篇文章（含 IMDb 上線日期、Udonis/PocketGamer 營收數列），查詢日期 2026-07-22。**這一點對可複製性評估極關鍵**：Last War 不是「上線即爆」，而是開發 20 個月 + 上線後又花約 5 個月才開始真正放量、之後再花 11 個月才衝到月營收 $138M 高峰——完整週期是 **從立項到規模化變現，約需 2.5–3 年**。

---

## 3. 同型競品公式對照

所有同品類競品共享一個底層結構：**輕度題材外皮（末日/軍事/生存）＋COK-like（Clash of Kings 系）長線數值養成核心 ＋ 重買量獲客 ＋ 鯨魚導向的付費深度**。差異主要在「外皮創意」與「玩法融合方向」。

| 遊戲 | 開發/發行商 | 累積營收（第三方估計） | 差異化公式 | 來源 |
|---|---|---|---|---|
| **Last War: Survival** | FirstFun→FUNFLY PTE | 累積約 **$3.5B**（2025 年單年 $1.65B–2.12B，各來源口徑略異） | 現代軍事末日題材＋大量「誤導性/釣魚式」買量廣告（含知名影星背書：Homelander 演員 Antony Starr 2024 Q4 戰役單波帶來 1,250 萬下載）＋數學小遊戲式可玩廣告（占買量曝光量逾 50%） | Udonis/MAF/Wikipedia 系列 WebSearch 摘要 |
| **Whiteout Survival** | Century Games（母公司 Century Huatong） | 累積超過 **$3B**（截至2025年中） | 冰封末日生存題材，與 Last War 月度互別苗頭爭奪全球營收榜 #1/#2（如 2025 年 8 月：Whiteout $136M #1、Last War $130M #2） | PocketGamer/Gamelight WebSearch 摘要 |
| **Top War: Battle Game** | 團隊背景與 Last War 有淵源（**不確定**，單一搜尋摘要提及「開發團隊亦開發過 Top War」，未能二次驗證，信心低） | 累積約 **$1.1B** | 更卡通化/輕度美術風格，主打更廣泛休閒受眾 | Sensor Tower via WebSearch 摘要 |
| **Evony: The King's Return** | Top Games Inc. | 累積約 **$1B**，2 億下載；2025 年單年 $169M | 老牌 COK-like 始祖之一，題材為中世紀奇幻戰爭，靠品牌長尾與極高付費深度（真人主播代言廣告聞名） | Yahoo Finance/Udonis WebSearch 摘要 |
| **Puzzles & Survival** | 37 Games（三七互娱） | 2025 年 **$363M**（**不確定**：搜尋摘要語意含糊，此數字可能是 37 Games 公司整體營收而非單一遊戲，需本機複查釐清） | 三消（match-3）玩法接入 SLG 數值系統，是「玩法融合」代表作 | WebSearch 摘要 |
| **Monopoly GO!** | Scopely | 2025 年 **$963M**（**不確定**：同樣可能是 Scopely 公司整體營收而非單一遊戲；另有數字指 Monopoly GO 單在 Google Play 即達 $591M） | 非 SLG 而是骰子擲點＋收集＋好友互動的休閒品類，列入對照組是為展示「非數值堆疊」也能做到頂級營收規模，證明買量+社交裂變+高頻活動的組合不限於 SLG 玩法 | WebSearch 摘要 |
| **Rise of Kingdoms（万国觉醒）** | Lilith Games | 玩家數 **1 億+**（2023年12月公布） | COK-like 元老級產品，2018 年即建立品類地位，是「先發優勢仍在發威」的案例 | WebSearch 摘要 |
| **Kingshot** | Century Games/Century Huatong | 2025 新黑馬，據報高峰月流水 **$5 億+**人民幣（約$70M+）／另一口徑稱年流水超 **40 億人民幣**（約$550M）（**兩口徑不完全一致，列為不確定量級參考**） | 融合輕度塔防（tower defense）玩法降低上手門檻 | 中文產業報導 WebSearch 摘要 |

**Last War 在公式上的差異化總結**（推論，基於以上事實整合）：Last War 與 Whiteout Survival 的核心數值玩法幾乎同構，勝負關鍵不在玩法創新，而在（1）買量創意的侵略性與規模（含被批評的「誤導性廣告」爭議，反而成功轉化為病毒式話題行銷素材）、（2）明星代言的密集度與精準選角（鎖定歐美 30–50 歲男性核心受眾熟悉的動作片/影集明星）、（3）持續 LiveOps 節奏（Alliance Duel、Zombie Siege、Arms Race 等固定活動循環＋賽季聯動）。這些都是「執行力與資本規模」的競爭，而非「產品創新」的競爭。

---

## 4. 成功要件

要複製 Last War 這個量級，依上述事實推論出的必要條件（推論，附推理依據）：

1. **資本量級**：SLG 新品期買量占營收 30–60%，且需要在營收尚未起量前就先行投入——Last War 上線首月僅 $287K 營收，但同期買量支出必然遠高於此（否則無法在 5 個月後就衝到月營收 $30M 量級的用戶基礎）。**推論**：新品階段至少需要準備「數百萬美元至千萬美元級」的先期買量資金池，且要承受 6–12 個月「投入大於回收」的現金流負值期，這是典型的風險資本或大型發行商財力量級，非個人或小團隊自籌資金可承受。
2. **團隊規模與職能**：對照 FunPlus（1,700人）、Century Games（1,000+人）、Lilith（2,300+人）三家同賽道公司的員工規模，即便扣除這些公司同時營運多款產品的稀釋效果，單一 SLG 大作要撐起「買量創意量產＋多地區在地化＋即時伺服器維運＋LiveOps 活動策劃＋客服＋數據分析」等職能，實務上需要**數十人至上百人的專職團隊**，且需具備「買量素材工業化量產」與「跨區域發行」兩項小團隊通常欠缺的能力。
3. **LiveOps 運營能力**：Last War 維持固定節奏的聯盟戰、殭屍圍城、軍備競賽等活動循環，加上賽季戰令與月卡訂閱制——這代表上線後需要**常態化、長達數年的內容產出節奏**，不是一次性開發完就結束。
4. **時程**：從立項到開始規模化變現，Last War 案例顯示約需 **2.5–3 年**（開發 20 個月 + 放量爬坡約 11–17 個月）。這代表資金必須能撐住這麼長的「零回收期」，對小團隊是極大的現金流壓力。

**結論（推論）**：以上四項要件疊加，構成的是一個典型的「發行公司／規模化遊戲廠商」的能力組合，而非「產品團隊」的能力組合——即使產品本身（核心玩法程式碼）可以由極小團隊甚至個人＋AI 在數月內做出可玩版本，**真正卡住小團隊的不是「做遊戲」的能力，而是「買量＋長線運營＋資本承受力」這三項規模化能力**。

---

## 5. 失敗率

**產業共識：SLG 是死亡率最高的品類之一**，主要原因與具體證據：

- **買量成本全品類最高**：因付費轉換率低、營收高度集中於鯨魚玩家，SLG 是行動遊戲買量市場中「單位獲客成本最高」的品類。來源：WebSearch 摘要交叉多篇中文產業報導，查詢日期 2026-07-22。**性質：產業共識，多來源一致，信心高**。
- **具體案例——大廠翻車**：網易（NetEase）自研單機 SLG《萬民長歌：三國》專案已被曝**砍掉，團隊解散**。來源：[新浪財經（WebSearch 摘要）](https://t.cj.sina.com.cn/articles/view/1654203637/629924f50200141oe)，查詢日期 2026-07-22。**性質：事實（單一來源，未能二次交叉驗證，但來源為財經媒體，信心中高）**。
- **中小創業團隊倖存率極低的質化描述**：「像樂狗和星合能這樣體量的 SLG 初創團隊，在過去 2~3 年裡非常的多，但最後成功跑出來的寥寥無幾。」來源：[手游那點事（WebSearch 摘要）](https://www.yfchuhai.com/article/6906.html)，查詢日期 2026-07-22。**性質：業內觀察評論，非統計數字，屬定性證據**。
- **產業文章標題本身即為強烈信號**：GameRes 一篇分析文章標題為〈發行公司玩不起的 SLG 遊戲 看完 80% 的 SLG 團隊要絕望〉。**重要澄清**：「80%」出現在標題中，是作者的修辭式概括，並非嚴謹統計數字（我方未能讀取全文核實其統計方法，WebFetch 對此站也可能受限），**不應引用為精確失敗率，僅作為產業情緒與論述基調的佐證**。

**失敗的結構性原因**（推論，基於前述事實鏈）：
1. CPI 逐年上升（中國市場數據顯示買量成本較前一年上漲達 5 倍的極端案例存在）但多數新進團隊的 LTV（用戶終身價值）模型沒有同步跟上，導致 LTV < CPI，買量即虧損。
2. 小團隊沒有「先發品牌效應」與「規模化議價能力」（大廠買量能拿到更好的 CPM/CPI 議價、有更成熟的 creative testing pipeline），在同一買量拍賣池中與 Last War、Whiteout Survival 這類巨頭競價，天然處於劣勢。
3. SLG 的長回本週期（本報告估算 2.5–3 年）意味著資金鏈稍有中斷即滿盤皆輸，這對缺乏外部融資的小團隊是結構性死穴。

---

## 6. 小團隊現實路徑（含反面訊號）

這是本報告被要求主動尋找的「反面訊號」區塊——即便上述證據顯示直接複製 Last War 幾乎不可能，仍存在小團隊成功打入相鄰賽道的真實案例：

### 反面訊號一：《遺棄之地》——5 人團隊做進 SLG/策略塔防融合品類暢銷榜
- 開發團隊僅 **5 人**，2025 年 11 月中旬於微信小遊戲＋iOS 上線，主打「中式民俗恐怖」題材＋橫版手操策略塔防玩法。
- 上線首日 iOS 端流水僅人民幣 **10.7 萬元**，但之後快速成長，第 5 天日流水已達 **78 萬元**，上線至今 5 天累積流水約 **250 萬元人民幣**。
- 成功衝進抖音小遊戲暢銷榜第一、微信小遊戲暢銷榜前 6 名、iOS 遊戲暢銷榜 TOP 15。
- 變現模式為 IAA（獎勵廣告）+ IAP 混合，IAP 仍是營收支柱（禮包/戰令/永久特權卡）。
來源：[游戏陀螺／17173／知乎系列文章（WebSearch 摘要）](https://www.youxituoluo.com/534067.html)，查詢日期 2026-07-22。**性質：事實，多篇中文產業媒體交叉報導，信心高**。
**意義**：這證明「小團隊＋差異化題材外皮＋輕度化玩法設計」確實能在**小遊戲生態**（而非傳統 App Store 頭部 SLG 賽道）以極低起始成本切入策略養成品類並獲得真實流水，是本報告找到最具體、最貼近 Jake 動機的正面反例。

### 反面訊號二：《三國：冰河時代》——融合類 SLG 黑馬
- 由途游遊戲推出，2025 年國內 SLG 市場最大黑馬之一，iOS 端月流水穩定在 **人民幣 5,000 萬元以上**，2025 全年預估流水約 **人民幣 3.87 億元**。
來源：WebSearch 摘要（中文產業報導），查詢日期 2026-07-22。**性質：第三方估計，非 5 人以下微型團隊，但仍遠小於 Last War/Whiteout 級別團隊規模，證明「中型團隊＋融合玩法創意」仍有機會空間**。

### 反面訊號三：Habby／Archero——小團隊打造混合休閒（hybrid-casual）爆款的歷史先例
- 最初 Demo 僅 **2 人**（1 製作人+1 工程師）不到一個月做出，正式掛名團隊 **11 人**（2 工程師、4 美術、1 遊戲設計師）。
- 2019 年上線首月營收 $850 萬美元、1,000 萬下載；2019 全年營收達 **$1.81 億美元**。
來源：WebSearch 摘要（WN Hub／Bayjinger／Deconstructor of Fun 系列），查詢日期 2026-07-22。**性質：事實，多來源交叉**。
**重要限定**：Archero 是 **hybrid-casual（混合休閒）品類，不是 SLG**，單用戶付費深度遠低於 SLG，證明的是「小團隊可以做出破億美元營收產品」這件事本身可行，但走的是完全不同的品類與變現邏輯（更低 CPI、更廣受眾、更依賴玩法病毒性而非鯨魚付費）。

### 反面訊號四（帶保留）：Death by AI——AI 遊戲爆紅案例，但非真正「個人」
- Discord 平台上的 AI 派對遊戲，病毒式增長。
- **關鍵澄清**：背後公司 Little Umbrella 在爆紅後已**募資 $200 萬美元**，創辦團隊含前 Meta 設計主管、前 AppLovin 高層等經驗豐富人士，**並非真正的「一人+AI」白手起家案例**。
來源：[GamesBeat（WebSearch 摘要）](https://gamesbeat.com/little-umbrella-makes-the-funding-rain-after-success-of-death-by-ai-social-game/)，查詢日期 2026-07-22。**性質：事實，但需澄清避免誤用為「solo+AI」佐證**。
**本報告在此明確澄清**：搜尋範圍內**查無**真正意義上「一人＋AI 工具、零外部資金、達到 SLG 或近似量級營收」的案例。這是誠實的「查無」，而非該現象不存在——2026 年 AI 輔助獨立開發雖已是常態（70%+ 獨立開發者使用 AI 工具，據稱可提升 30–50% 生產力），但目前查得到的成功案例，多半仍涉及種子輪募資、多人團隊或發行商合作，而非純粹單人。

### 結構性機會：微信小遊戲生態——目前對小團隊最友善的低成本試錯管道
- 微信小遊戲生態現有 **50 萬+ 開發者**，其中 **80% 團隊規模低於 30 人**。
- 目前已有 **80+ 款遊戲日活破百萬**、**300+ 款遊戲季流水破千萬人民幣**。
- 微信 2026 年推出「內購付費激勵計畫」，單款首發新遊最高可獲 **人民幣 7,000 萬元支持**（平台補貼/流量支持，非現金直接給付，需複查細節）。
- AI 創作平台 SOON 案例：開發者可用**低於人民幣 2 萬元（約 $2,800 美元）成本、2 週內**完成 AI 小遊戲的商業驗證（案例：《腦洞怪物大亂鬥》上線 9 天吸引超 2.5 萬用戶）。
來源：WebSearch 摘要（搜狐／虎嗠／36氪／知乎系列），查詢日期 2026-07-22。**性質：第三方報導數字，平台自身動機是推廣其生態，數字需保留一定行銷色彩折扣，但多篇獨立報導方向一致，信心中等**。

**這一節對 Jake 的直接意涵（推論）**：如果目標是「個人＋AI 做一個賺錢遊戲」，現實中最近的可行路徑**不是模仿 Last War 的資本密集玩法**，而是模仿《遺棄之地》或 SOON 平台案例的模式——用 AI 大幅壓低單次試錯成本（$2,000–3,000 美元量級即可完成一次驗證），選擇微信小遊戲或同類低 CPI/免買量依賴的發行管道，靠題材差異化與輕度玩法融合尋找利基，而非在傳統 App Store 買量拍賣場上與千人團隊的巨頭正面競價。

---

## 7. 2026 年窗口：這套公式還有效嗎？

**市場總量仍在成長**：全球策略遊戲（Strategy Games）市場規模 2025/2026 年估值約 **$284–286 億美元**，預估成長至 2034/2035 年 **$606–617 億美元**，年複合成長率約 **8.7%–9.0%**。來源：WebSearch 摘要（Verified Market Research／MarkWide Research 等市場研究機構），查詢日期 2026-07-22。**性質：第三方市場預測，此類報告方法論通常較寬鬆（常涵蓋 PC/主機策略遊戲，非純手遊 SLG），信心中等**。

**但紅海化訊號明確且密集**：
- 中文產業報導標題直指：「超 70 款，多位知名製作人操刀：遊戲圈將面臨一大批 SLG 冲入」——顯示 2026 年有**逾 70 款新 SLG 產品**在研發／即將上線，且不乏知名製作人親自操刀。來源：[東方財富網／手游那點事（WebSearch 摘要）](https://caifuhao.eastmoney.com/news/20260519231428169233950)，查詢日期 2026-07-22。
- 三七互娱、巨人網絡、Bilibili、網易等大廠正在「SLG + 小遊戲」賽道掀起新一輪用戶爭奪戰。來源：[每經網（WebSearch 摘要）](https://www.nbd.com.cn/articles/2025-05-29/3893369.html)，查詢日期 2026-07-22。
- Last War 自身數據也顯示品類進入成熟期：下載量已於 **2026 年初隨假期行銷高峰觸頂後急速降溫**，營收也從高峰回落，雖然目前仍維持**月營收 $8,000 萬美元以上**、尚未「崩盤」，但成長動能明顯放緩。來源：WebSearch 摘要（appfigures／mobilegamer.biz 系列），查詢日期 2026-07-22。

**新機會點在哪裡（推論，基於上述事實整合）**：
1. **「SLG+」融合次類型是目前最活躍的差異化方向**：塔防（Kingshot）、三消（Puzzles & Survival）、農場經營、卡牌等玩法與 SLG 數值系統融合，目的是用更低門檻的輕度玩法吸引泛用戶、同時保留 SLG 的長線付費深度，藉此降低對純買量的依賴、提高自然/口碑流量占比。
2. **微信小遊戲生態的結構性補貼與流量分潤，正在替代部分傳統買量需求**——這是 2026 年新出現、對小團隊尤其有利的通路變化，值得持續關注。
3. **題材/文化差異化仍有空間**：《遺棄之地》用「中式民俗恐怖」這個過去 SLG 罕用的題材切入,證明即使核心玩法高度同質化的品類，題材創新仍能帶來顯著的差異化流量。
4. Last War 本身進入「成熟期防守戰」，這代表：**現在才要用同樣打法（COK-like 硬核數值＋大規模買量）正面切入 4X SLG 頭部賽道，時機已晚**——市場領先者已建立品牌、LTV模型、買量渠道的複合優勢，新進者的邊際 CPI 只會更高、競爭更激烈,此為「紅海」判斷的核心推理依據。

---

## 8. 可複製性總評估（推論鏈，明確標示為推論）

**問題**：Last War 的營收模式，能否被小團隊或個人＋AI 複製？

**推理鏈**：
1. Last War 的成功公式 = 成熟 COK-like 核心玩法（非創新）＋ 大規模持續買量（新品期 50–60% 營收再投入）＋ 鯨魚導向精緻付費系統＋ 千人級組織的 LiveOps 與買量創意產能＋ 2.5–3 年的資本鎖定期。
2. 這五個要素中，AI 工具能實質壓低成本的只有「核心玩法開發」這一項（程式碼、部分美術、部分素材生成）；買量預算是真金白銀的資本風險，AI 無法把它變不需要；千人組織的持續運營能力也不是 AI 生產力工具能一次性替代的（需要長期人力，即便每人生產力提升 30–50%，也無法把千人團隊壓縮到個人規模仍完成同等產出量）。
3. 更關鍵的是买量拍賣機制：CPI 由市場出價競爭決定,小團隊即使用 AI 生成再多素材，也是在與 Last War、Whiteout Survival 這類巨頭同一個競價池裡出價,资本量級劣勢無法被「效率」抵銷,只能被「資本」抵銷。
4. 因此：**直接以 1:1 規模複製 Last War 的營收模式，對小團隊或個人＋AI 而言，在 2026 年是不可行的**——這不是「難」的問題，是資本結構性門檻的問題。**（信心：高，此結論由多組獨立事實交叉支持，非單一來源推測）**
5. 但「SLG 賺錢的底層邏輯」——輕度題材外皮 + 長線數值黏著 + 訂閱/賽季付費——這個**模式本身**可以在**縮小 100 倍以上規模**後於微信小遊戲等低 CPI/免買量依賴生態中複製，已有《遺棄之地》5 人團隊的真實案例佐證。**（信心：中高，有具體案例支持，但案例數量有限，尚不足以稱為「已驗證的普遍路徑」）**
6. 對 Jake 的實務建議方向（推論，供決策參考，非事實陳述）：若目標是「賺錢」而非「一定要做 SLG」，個人＋AI 現實可行度較高的路徑排序建議為：（a）微信小遊戲或同類低買量依賴平台的輕度策略/塔防融合小品，善用 AI 壓低單次試錯成本至數千美元量級，快速多次試錯；（b）若堅持 SLG 賽道，務實路徑是**成為某個發行商的小型外部開發合作方**（發行商出買量資本與運營資源，團隊出創意與核心玩法），而非獨立扛下整個買量與運營鏈；（c）直接對標 Last War 的規模化正面競爭，在目前已知的資本與組織門檻下，判定為**不可行**。

---

## 來源清單

以下依研究節次列出主要引用來源（均透過 WebSearch 工具取得摘要，查詢日期均為 2026-07-22，URL 為 WebSearch 結果中列出之原始來源頁面）：

1. Udonis Blog — Last War: Survival Revenue & Player Count Statistics — https://www.blog.udonis.co/statistics/last-war-survival
2. MAF Blog — Last War Survival: The Secrets Behind Its $2.6 Billion Revenue — https://maf.ad/en/blog/last-war-survival/
3. Naavik — Why Last War Is Winning the 4X Game — https://naavik.co/digest/how-last-war-is-winning-the-4x-game/
4. FoxData — How "Last War: Survival" Raked in $1.6 Billion in a Mere 18 Months — https://foxdata.com/en/blogs/how-last-war-survival-raked-in-16-billion-in-a-mere-18-months/
5. FoxAdvert — How Does Last War: Survival Game Make Huge Profits — https://foxadvert.com/en/digital-marketing-blog/how-does-last-war-survival-game-make-huge-profits-despite-half-of-its-ratings-being-1star/
6. PocketGamer.biz — Last War: Survival surpasses $2bn — https://www.pocketgamer.biz/last-war-survival-surpasses-2bn-after-record-player-spending-in-early-2025/
7. TechNode — Last War: Survival Game boosts FirstFun to fifth in Chinese mobile game publishers — https://technode.com/2024/03/21/last-war-survival-game-boosts-firstfun-to-fifth-in-chinese-mobile-game-publishers/
8. Wikipedia — Last War: Survival Game — https://en.wikipedia.org/wiki/Last_War:_Survival_Game
9. Century Games 官網 About Us — https://www.centurygames.com/about-us/
10. PocketGamer.biz — Inside mobile hitmaker Lilith Games — https://www.pocketgamer.biz/inside-mobile-hitmaker-lilith-games/
11. GameLook／脈脈 — FunPlus CTO 分享 SLG 成功方法論（1,700人團隊） — http://www.gamelook.com.cn/2021/10/458252
12. GameRes — 發行公司玩不起的SLG遊戲 看完80%的SLG團隊要絕望 — https://www.gameres.com/780614.html
13. 手游那點事 — "我們這裡的SLG團隊都快沒了" — https://www.yfchuhai.com/article/6906.html
14. 新浪財經 — 網易《萬民長歌：三國》項目被砍團隊解散 — https://t.cj.sina.com.cn/articles/view/1654203637/629924f50200141oe
15. 游戏陀螺 — 11月小游戏观察｜五人团队打造，微恐塔防小游戏成新黑马《遗弃之地》 — https://www.youxituoluo.com/534067.html
16. 17173 — 豪腾再发爆款《遗弃之地》深度分析 — https://news.17173.com/content/12042025/223342491.shtml
17. WN Hub — Case study: Archero $181M — https://wnhub.io/news/other/item-17800
18. GamesBeat — Little Umbrella募资$2M（Death by AI） — https://gamesbeat.com/little-umbrella-makes-the-funding-rain-after-success-of-death-by-ai-social-game/
19. 东方财富网 — 超70款SLG冲入游戏圈 — https://caifuhao.eastmoney.com/news/20260519231428169233950
20. 每经网 — 抢滩"SLG+小游戏" — https://www.nbd.com.cn/articles/2025-05-29/3893369.html
21. Statista — Global app store commission rates — https://www.statista.com/statistics/975776/revenue-split-leading-digital-content-store-worldwide/
22. Yahoo Finance — Evony developer Top Games Inc. — https://finance.yahoo.com/news/things-know-evony-king-return-171500094.html
23. 快出海 — FirstFun 元趣娱乐公司资料 — https://www.kchuhai.com/company/view-13794.html
24. 广大大 — 元趣娱乐Last War营收登顶报道 — https://guangdada.net/blog/126583
25. 搜狐／虎嗠／36氪／知乎（微信小游戏生态与SOON平台案例，多篇綜合） — 代表性連結：https://www.huxiu.com/article/4848132.html ；https://36kr.com/p/3827371744678535

---

## 被 403 擋掉、值得本機複查的頁面

以下頁面本次全數以 WebFetch 直接讀取時回傳 **HTTP 403 Forbidden**（每站僅嘗試 1 次，依規則未重試），僅能透過 WebSearch 摘要間接取得片段資訊，若 Jake 本機瀏覽器有權限，建議優先人工複查以下頁面以核實/補完數字（尤其是標記「不確定」的 ARPDAU/ARPPU 相關數字）：

1. https://naavik.co/digest/how-last-war-is-winning-the-4x-game/ （Naavik 深度分析，含買量策略與競品比較的完整數據，價值最高，強烈建議優先複查）
2. https://www.blog.udonis.co/statistics/last-war-survival （完整歷史營收/玩家數列表）
3. https://maf.ad/en/blog/last-war-survival/ （變現機制與ARPDAU方法論細節）
4. https://foxdata.com/en/blogs/how-last-war-survival-raked-in-16-billion-in-a-mere-18-months/
5. https://foxadvert.com/en/digital-marketing-blog/how-does-last-war-survival-game-make-huge-profits-despite-half-of-its-ratings-being-1star/
6. https://en.wikipedia.org/wiki/Last_War:_Survival_Game （基礎事實查核用，一般應可讀取，本次仍403，建議直接重試）
7. https://www.pocketgamer.biz/last-war-survival-surpasses-2bn-after-record-player-spending-in-early-2025/
8. https://technode.com/2024/03/21/last-war-survival-game-boosts-firstfun-to-fifth-in-chinese-mobile-game-publishers/ （FirstFun團隊/公司規模資訊可能藏在全文中，本報告未能查到員工人數，此頁值得複查）

**額外標記——因 WebSearch 額度於研究後段（約完成 24 次搜尋後）用罄而未及查證的項目**（非403，是額度限制，建議後續 session 補查）：
- 37 Games（Puzzles & Survival 發行商）團隊規模
- Scopely（Monopoly GO 發行商）團隊規模與 Monopoly GO 單一遊戲營收（vs 公司整體營收）的精確拆分
- FirstFun／元趣娛樂 LinkedIn 或其他管道的員工人數
- AI 生成買量素材在 SLG 品類 2026 年最新滲透率數字
