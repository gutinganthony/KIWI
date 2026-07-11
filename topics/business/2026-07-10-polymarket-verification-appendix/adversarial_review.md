# 對抗性複核：waveking1314〈Polymarket跟單指南〉結論草稿

複核日：2026-07-10 ｜ 複核員角色：對抗性（盡力找結論錯誤/過度延伸）
方法：4 份底稿逐條檢視 ＋ WebSearch 獨立再驗證（官方頁面 WebFetch 仍 403，見各條註記）

---

## 總裁定（先行）

**主結論站得住。** 核心判定「不建議使用者執行此做法」在五個攻擊面下全數存活；沒有任何承重牆倒塌。
需要的修正只有兩處「加註」，皆不改變結論方向：
- (加註 A) −$311.4k 這個精確數字是**單一追蹤站（lines.com，僅計大額單，爬取日未知）**，報告應標為單源估值而非既成事實；崩盤「方向」本身則是多源收斂、穩固。
- (加註 B) 應明確**區分「作者＋範例不可信」與「基本選錢包方法論本身合法」**——後者被中立來源背書，結論不宜連帶否定（但註記：我方未讀到原文方法論段落，X 被擋，此加註基於任務轉述）。

---

## 攻擊面 1：台灣 close-only（承重牆）→ 判定：**不成立（結論成立）**

**獨立再驗證結果：確認台灣 = close-only，且非過時/誤讀。**
- 多個 2026 年獨立來源一致把 **Singapore / Poland / Thailand / Taiwan** 列為 4 個 close-only 國家（可平倉、不可開新倉）：
  - https://www.datawallet.com/crypto/polymarket-restricted-countries
  - https://laikalabs.ai/prediction-markets/polymarket-restricted-countries-list
  - https://www.coinrithm.com/en/blog/polymarket-countries-and-availability
  - https://www.ccn.com/education/crypto/countries-banned-restricted-polymarket-kalshi/ （新聞站，非導覽站，獨立性較高）
- 趨勢方向相符：CCN「10+ 國已封鎖/限制」＋ 2026 監管收緊，close-only 不可能已被悄悄解除。
- 「政治盤 vs 全平台」細節：有來源提到台灣特別禁「政治投注盤」。但綜合判讀結論一致——**close-only 是平台級**，任何類別（含電競/運動）都不能開新倉。故此細節**無法拯救**本文（本文教學的第 1 步＝開新倉，仍被擋）。

**兩個誠實caveat（不改結論，但需寫入報告透明度）：**
1. 官方 help 頁 `help.polymarket.com/...geographic-restrictions` 本 session WebFetch 仍回 **403**，未能直取官方原文；上述全為二手聚合站/新聞站交叉。惟四站彼此獨立且一致，先驗性造假機率低。
2. close-only 是 **polymarket.com 前端 IP geoblock**；透過跟單 bot（Kreo 開嵌入式錢包）或 VPN，技術上仍可能開倉——但這是**違反 ToS、資金凍結風險**，反而**強化**「不要做」的結論，不是反例。建議把「合規上做不到」精修為「合規做不到；非合規可繞但有凍結風險」。

## 攻擊面 2：錢包身分歸屬 / −$311k 是否張冠李戴 → 判定：**不成立**

**獨立再驗證：0x25e28169…9a09 = @xdd07070，且 −$311.4k 明確屬於同一錢包，非誤植他人。**
- 身分交叉：esports.net、cryptonews.net、@0xTengen_ 推文、polymarket.com/@xdd07070、lines.com/whales/profile/xdd07070 全指向同一 xdd07070。
- −$311.4k 崩盤數據：我方獨立搜尋直接命中 **lines.com/whales/profile/xdd07070**，回傳 $498.9k 量、10 筆、2 勝 6 敗、25% 勝率、−76.9% ROI、−$311.4k、2026 運動盤 0-8、最後單 $33.4k THEMONGOLZ ~3 個月前——與底稿逐字吻合，且掛在 **xdd07070 本人檔案**下，**不是另一個錢包**。
- 來源：https://www.lines.com/whales/profile/xdd07070 ／ https://www.esports.net/news/polymarket-user-generates-118000-in-a-month-of-esports-wagers/ ／ https://x.com/0xTengen_/status/2024580594643157249
- 底稿檔：wallet_verify.md §1、§3。→ 張冠李戴指控不成立。

## 攻擊面 3：證據鏈弱點（數字來自快照/媒體轉述）→ 判定：**部分成立（需加註）**

- **崩盤「方向」是多源收斂、穩固**：2026 運動盤 0-8、持倉 $0.00（polymarket.com 快照）、鏈上餘額 ~$1.9k（layerhub/etherscan）、最後可證交易 ~4 月——四條獨立指標同向，結論方向不脆弱。
- **但精確數字 −$311.4k 是單源**：僅 lines.com 一站，且該站**只追蹤大額單**、爬取日期未知；−311.4k/−76.9% 隱含成本基礎 ~$405k（非 $498.9k 量），非同一分母，屬追蹤站自算。→ 報告若把「−$311k」當硬事實會過度延伸；應標為「據 lines.com 鯨魚追蹤（僅大額單、單源、爬取日未知）」。底稿其實已如此標註（wallet_verify.md §3 明列「不等於終身 PnL」），**主要問題在結論草稿的濃縮句把 caveat 丟了**。
- 同理 `$1,883.65` 鏈上餘額、`持倉 $0` 皆為**單源、時點快照**，7/10 當下可能已變；結論用「~$1.9k / $0」時應保留「快照」語氣。
- 附帶發現（母體悲觀值偏挑）：strategy_viability.md 引「92.4% 不賺錢」是最悲觀那一版；我方獨立搜尋另得「僅 12.7% 用戶獲利／學術研究 70-84% 不獲利／活躍錢包（≥5 筆）約 23% 終身正 PnL」。方向一致（散戶多輸），但 92.4% 屬 cherry-pessimistic，報告宜給區間而非single最悲觀值。來源：https://polycopy.app/best-polymarket-traders

## 攻擊面 4：是否過度修正——方法論獨立價值 → 判定：**部分成立（需加註）**

- 中立來源確實背書「以穩定性/多月track record/回撤/市場類別/避開做市與內幕」篩選錢包這套方法：
  - Polycopy「Copy Score 70+ → 勝率 67.7%、平均 +5.76%／未過濾≈擲硬幣」https://polycopy.app/polymarket-trading-strategies
  - Medium「How To Find The BEST Polymarket Wallets To Copy Trade (Without Getting Rekt)」https://medium.com/@0xmega/how-to-find-the-best-polymarket-wallets-to-copy-trade-without-getting-rekt-26dd65123324
- 故「篩選方法論」有獨立價值，結論**不應連帶把方法論一起否定**。建議加一句：「作者與範例錢包不可信 ≠ 基本選錢包原則無效；後者與中立來源一致，但仍受滑點/逆選擇/流動性上限的結構性天花板壓制（見攻擊面 5），且台灣 close-only 使其對本案讀者無法落地。」
- **反制此加註的 caveat**：我方**從未讀到 waveking 原文的方法論段落**（x.com 全程 403），「文章含此方法論」係任務簡報轉述。若原文其實只是包裝話術、無實質篩選規則，則此加註不適用。→ 因此列「部分成立」而非「成立」。

## 攻擊面 5：「散戶跟單=負期望」是否講太死 → 判定：**不成立（結論已正確scoped）**

- 結論草稿的原句是「**天真**跟單扣除滑點費用為負期望」——已限定「天真（不過濾）」，未宣稱一切跟單皆負期望。
- strategy_viability.md §4 明確給了情境 B（紀律過濾）+2~5%/月上緣，並非一竿子打死。
- 我方找到的「反例」——beachboy4 終身 +$4.3M、23% 活躍錢包終身正 PnL、Copy Score 過濾 67.7% 勝率——都只證明「**經嚴格過濾**可正期望」，**不**反駁「天真跟單負期望」，也不反駁「別照抄這篇（範例已爆倉、作者有返佣動機）」。
- 故結論無需修改。這些數據反而印證：全域式悲觀措辭必須嚴格 scoped 在「天真」二字，否則會被此類反例攻破——結論草稿做對了。

---

## 需修正清單（給主結論）

1. **[加註，必要]** 將「−$311k／持倉$0／餘額~$1.9k」標為**單源時點快照（lines.com 僅大額單、爬取日未知）**；崩盤方向多源穩固，但精確數字不得當硬事實。
2. **[加註，必要]** 明確切分「作者＋範例錢包不可信」與「基本選錢包方法論本身合法（中立來源背書）」；同時註記我方未讀到原文方法論段落。
3. **[潤飾，建議]** 台灣「合規做不到」→ 補「非合規可用 bot/VPN 繞過但違 ToS、有凍結風險」，使承重牆更精確且更強。
4. **[潤飾，建議]** 母體不獲利比例給區間（~70-92%）而非單一最悲觀 92.4%。
5. **[透明度]** 全部關鍵鏈上數字皆二手快照（官方頁 403），報告應保留此限制聲明並列入 Mac 手動複核。

**主結論「不建議使用者執行此做法」：站得住，不需推翻。** 五攻擊面：1 不成立、2 不成立、3 部分成立、4 部分成立、5 不成立。無承重牆崩塌。
