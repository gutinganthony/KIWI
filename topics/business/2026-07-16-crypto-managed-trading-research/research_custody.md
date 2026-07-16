# 交易所「託管／代客管理」研究報告
Binance・OKX・Bybit・Bitget — 一個人能否正式代管另一人的資金？

- 研究日期：2026-07-16
- 研究方法備註：**本環境對 binance.com / okx.com / bybit.com / bitget.com / ceffu.com 的直接抓取全被 proxy 403 擋下**，以下所有交易所官方頁內容均透過 WebSearch 的搜尋摘要取得，一律標註「未直接核對」。引文為搜尋結果轉述的原文，用前請自行點開連結複核。查不到的標「查無」。

---

## 第①節：機構級 managed sub-account／fund manager 方案

### 總覽（事實，未直接核對）

四所都有「投資人開子帳戶 → 綁定交易團隊 → 交易團隊只能下單、不能出金」的正式產品。差別在**交易團隊端的門檻**：

| 交易所 | 產品名 | 投資人端資格 | 交易團隊端資格 | 平台額外費用 |
|---|---|---|---|---|
| Binance | Managed Sub-Account | 企業帳戶或 VIP1+ 個人（KYC+2FA） | VIP／機構客戶（VIP3+ 可自助開通，其餘找客戶經理） | 未見額外費用；費率跟隨交易團隊 VIP 等級 |
| OKX | Managed Trading Sub-accounts | 一般用戶可申請（見不確定事項） | **機構認證 + VIP1 起 + 須持有基金管理類執照** | OKX 明言不另收費，只收標準交易費 |
| Bybit | Custodial Trading Subaccount | 一般用戶（主帳戶操作出入金） | 須聯繫機構業務代表申請**白名單**（機構導向） | 未見額外費用；費率跟隨交易團隊主帳戶 VIP |
| Bitget | Custodial trading sub-account（託管子帳戶） | 一般用戶（完成 KYC） | **帳戶持有 >50,000 USDT 或 VIP2+ 即可申請「委託交易員」** | 官方明言無建立/維護費用 |

### Binance（資格／成本／流程）

- **Managed Sub-Account**：
  - 資格（投資人端）：「Managed Sub-Account is available to corporate account users and VIP 1 (or higher) personal account users who have successfully completed all account registration requirements, identity verification and enabled 2FA.」「Managed Sub-accounts are exclusive for VIP users. VIP 3+ users can enable this feature directly from their account. Other users please contact your account manager.」（來源：Binance Support FAQ 0594748722704383a7c369046e489459，https://www.binance.com/en/support/faq/how-to-get-started-with-managed-sub-account-functions-and-frequently-asked-questions-0594748722704383a7c369046e489459 ，2026-07-16，未直接核對）
  - 成本：功能本身未見收費；實際門檻是 VIP1。2026-03-19 起 VIP1 門檻：持有 5 BNB＋30 日現貨量 100 萬 USD 或 30 日合約量 500 萬 USD（來源：datawallet.com/crypto/binance-vip-levels-explained、PR Newswire「Binance Expands VIP Access」2026-03，2026-07-16 查，非官方頁彙整，未直接核對）。
  - 流程：投資人（Account Owner）在主帳戶下建 managed sub-account（上限 10 個），綁定指定交易員（Designated Trader）email；交易員取得**只能交易的 API 權限**；「The Designated Trader is not able to withdraw assets from the Managed Sub-Account. Withdrawals from the Managed Sub-Account may only be made by the Account Owner.」錢一直在投資人自己的 Binance 主帳戶體系下。
- **Asset Management Sub-Account**（另一型，供投資人委託專業交易團隊）：「Asset Management Sub-accounts are exclusive for VIP users… please contact your account manager or email to vip@binance.com.」交易團隊同樣不能出金（來源：Binance Support FAQ 122f5fea8b954a29abcde94672d55e53，2026-07-16，未直接核對）。
- **Binance Fund Accounts**（2025 推出，針對資產管理人）：「Fund managers and their investors must pass KYC/KYB…fund managers have to be licensed or exempted in their jurisdictions to use the Fund Accounts product.」（來源：cointelegraph.com/news/binance-fund-accounts-portfolio-managers，2026-07-16，未直接核對）→ **需要執照，個人散戶不適用**。
- **Binance Link**（券商/平台接入方案）：「Link partners should be an institution with no less than 20,000 users」「maintain at least 10 million BUSD trading volume monthly and…1.2 million BUSD worth of deposits」（來源：https://www.binance.com/en/support/faq/what-is-binance-link-program-04b2a5c9a8174096b3508f270404508c ，2026-07-16，未直接核對）→ **純機構方案，個人完全構不到**。

### OKX（資格／成本／流程）

- 交易團隊端（現行 Rules 頁）：「To become a Trading Team, you need to first qualify as an institution on OKX and reach the level of VIP 1 minimum.」且「You must hold a license that legally permits fund management operations—such as an investment adviser, fund manager, or virtual asset service provider (VASP) license—issued by the applicable financial regulator.」另有屬地限制（原則上只能管理 OKX 提供服務且你完成開戶之司法轄區的本地投資人資金）；EEA 另加風控/內稽/季報年報義務。（來源：https://www.okx.com/en-us/help/rules-on-managed-trading-sub-accounts ，2026-07-16，未直接核對）
- 投資人端：「All users can apply to become investors (clients) for managed trading sub-accounts.」投資人自建 managed trading sub-account、輸入交易團隊 UID 綁定。（來源：https://www.okx.com/en-us/help/managed-trading-sub-account-feature-on-okx 與 step-by-step guide，2026-07-16，未直接核對）
- 出入金控制：「Trading Team could place trades and manage positions and yet has no permission over the deposit and withdrawal permission of the managed trading sub accounts unless expressly granted by the Investor.」出金只能經投資人主帳戶。
- 成本：「OKX does not take any additional fee for this feature」；分潤、費用、績效義務由投資人與交易團隊**場外書面協議**約定；綁定期間雙方適用兩者中較低的費率，交易量計入交易團隊主帳戶 VIP。
- **結論（推論）**：OKX 正式路徑對「台灣個人」實質關閉——需機構認證＋監管機關核發的基金管理類執照。

### Bybit（資格／成本／流程）

- 產品：「Bybit has introduced…a Custodial Trading Subaccount to meet the needs of investors to entrust their funds to professional trading teams for asset management.」（來源：https://www.bybit.com/en/help-center/article/Introduction-to-Custodial-Trading-Subaccount ，2026-07-16，未直接核對）
- 交易團隊端：「Trading teams must contact Bybit's institutional representative to apply for whitelisting to open a Custodial Trading Subaccount.」Bybit 機構服務頁明列服務對象：「entities that qualify as institutional participants including regulated hedge funds, proprietary trading firms, market makers, family offices, over-the-counter desks, and corporate treasuries.」（來源：https://www.bybit.com/en/institutional ，2026-07-16，未直接核對）→ 偏機構；未見公開的數字門檻（查無）。
- 流程：「Before managing an investor's Custodial Trading Subaccount, the investment agreement must be negotiated offline between the investor and the trading team.」「The trading team cannot withdraw funds from the Custodial Trading Subaccount. All deposits and withdrawals need to be performed via the investor's Main Account.」費率跟隨交易團隊主帳戶 VIP。
- 成本：未見額外費用（查無明文收費）。

### Bitget（資格／成本／流程）——四所中唯一個人搆得到的正式路徑

- 交易團隊（委託交易員）端：「If you hold more than 50,000 USDT in your Bitget account or you are VIP-2 level or higher, you can apply for delegated trader status at any time.」（來源：Bitget Support「Custodial sub-account rules」https://www.bitget.com/support/articles/12560603803137 與 https://www.bitget.com/apply-trading-team ，2026-07-16，未直接核對）→ **未見「必須是機構」的字樣；以資產或 VIP2 為門檻，個人可申請**（此點建議實際到 Bitget 頁面複核，因為是本研究最關鍵的個人可行性主張）。
- 投資人端：完成身分驗證的用戶即可建託管子帳戶（每人 10 個，可加開）；「The investor is the creator and owner of the custodial sub-account and is responsible for the allocation of funds…Have control over account permissions for deposit, withdrawal, unbinding, and freezing.」
- 流程：投資人發起委託後有 7 天等待期，委託交易員須在期內確認，否則自動取消。出入金權限在投資人手上。
- 成本：「There are no fees associated with creating and maintaining a custodial sub-account.」分潤同樣是雙方場外自行約定（推論：官方僅提供帳戶結構，不介入分潤）。

---

## 第②節：交易所託管品牌（custody）服務對象

**共同結論（事實＋推論）：四所的託管品牌全部是機構導向，對「台灣個人幫朋友管錢」皆不可用。**

- **Ceffu（前 Binance Custody）**：定位「compliant, institutional-grade custody platform」，客戶為 corporate customers，需通過 **KYB**（Know Your Business）——即**只收法人**。Binance VIP/機構客戶可用 **MirrorX** 把資產放 Ceffu 冷儲、鏡像到 Binance 交易（off-exchange settlement）。費用：官方費表 PDF（Ceffu-Fee-Structure-EN.pdf）顯示託管費分級計費，AUC <1,000 萬美元的級距年費率 0.24%（此數字來自搜尋摘要引用該 PDF，未直接核對；PDF 本身 403）。最低資產門檻：查無公開數字，官方要求聯繫 sales@ceffu.com。（來源：ceffu.com/en/about-us、ceffu.com/download/Ceffu-Fee-Structure-EN.pdf、binance.com MirrorX blog，2026-07-16，未直接核對）
- **OKX**：無自營零售託管品牌；機構客戶透過與 **Komainu**（受監管第三方託管人）的合作（Komainu Connect，2023-06 上線、2024-11 擴大）做 off-exchange custody——資產放 Komainu、在 OKX 交易，支援現貨與衍生品、自動損益結算。明確面向 institutional clients（首發客戶為 CoinShares）。個人資格：無此選項（查無任何個人版）。（來源：https://www.okx.com/learn/okx-komainu-enhanced-custody 、komainu.com，2026-07-16，未直接核對）
- **Bybit**：無自營託管品牌；機構透過 **Copper ClearLoop** 與 **Fireblocks Off-Exchange** 做資產不上所的交易結算。服務對象同上述機構清單。（來源：copper.co 公告、fireblocks.com，2026-07-16，未直接核對）
- **Bitget**：有「**Bitget Custody**」頁（bitget.com/custody），標明「for institutions & VIPs」；方案包括 Copper ClearLoop、Cactus Custody（Oasis 帳戶）、Fireblocks Network Link、MPC 協同託管。最低門檻數字：查無公開，需洽機構業務。（來源：https://www.bitget.com/custody ，2026-07-16，未直接核對）

註（概念釐清，推論）：這些託管品牌解決的是「機構的資產不想放在交易所熱錢包」的對手方風險問題，**不是**「A 代管 B 的錢」的代客關係。即使門檻搆得到，它也不提供你要的功能；「代客」功能對應的是第①節的 managed/custodial sub-account。

---

## 第③節：個人替代路徑——朋友帳戶開「只能交易、不能出金」的 API key

### 技術面：四所的 API 權限設計都支援（事實，未直接核對）

| 交易所 | 權限粒度 | 出金權限預設 | 備註 |
|---|---|---|---|
| Binance | Enable Reading / Enable Spot & Margin Trading / Enable Futures / Enable Withdrawals 等分開勾選 | `enableWithdrawals` 預設 **false**；且**必須先綁 IP 白名單才能開出金** | 無 IP 限制的 key 建立 90 天後或閒置 30 天自動刪除（來源：developers.binance.com/docs/wallet/account/api-key-permission、Binance 2021-07 API 權限公告，2026-07-16，未直接核對） |
| OKX | Read / Trade / Withdraw 三權限勾選＋IP 綁定 | Withdraw 需另外勾選 | （來源：okx.com/docs-v5、okx.com/en-us/help/api-faq，2026-07-16，未直接核對） |
| Bybit | read-only / read-write；出金相關權限獨立 | 出金非預設 | 2026-02-10 起法幣相關權限只能在建 key 時經瀏覽器設定、主 API key 的 IP 白名單不可再經 API 增刪（來源：bybit-exchange.github.io/docs/v5/user/*，2026-07-16，未直接核對） |
| Bitget | 唯讀 / 交易 / 劃轉 / 出金分開授權；每 UID 10 把 key | 出金需勾選且**僅限 IP 白名單** | （來源：bitget.com/api-doc/common/quick-start，2026-07-16，未直接核對） |

→ 技術上「朋友開帳戶，把 Read+Trade（不含 Withdraw/Transfer）的 API key 給你操盤」在四所都做得到，且出金鑰匙天然留在朋友手上。

### ToS 面：這條路在四所條款下都有明確風險

各所條款關於「帳戶借用／代操第三人資金」的原文（皆為搜尋摘要轉述之引文，2026-07-16，未直接核對）：

- **Binance**（Terms of Use，bnbstatic ToU PDF / binance.com/en/terms）：
  - 「You must ensure that any Binance Account(s) registered under your name will not be used by any person other than yourself or, with respect to Corporate Binance Accounts, your Permitted Users…」
  - 「as an individual user, you will use your Binance Account only for yourself, and not on behalf of any third party, unless you have obtained our prior written consent.」
  - 另：Binance 保留對「非帳戶註冊人使用帳戶」暫停/凍結/取消帳戶的權利。
  - → 朋友授權你操作＝朋友違反「不得由他人使用」；你若在自己帳戶裡收朋友的錢來操作＝你違反「不得代第三人使用」。**兩個方向都踩線，除非取得 Binance 事前書面同意（managed sub-account 正是這個「同意」的產品化形式）。**
- **OKX**（Terms of Service，okx.com/help/360021813691）：
  - 「By registering an Account with OKX, you agree and represent that you will use the Account only for yourself and not on behalf of any third party, unless previously approved by OKX.」
  - OKX 保留在「you have permitted an unauthorised third party to use your Account」時暫停/終止帳戶的權利。
- **Bybit**（Bybit Platform Terms and Conditions，bybit.com help center）：
  - 「You shall not sell, lease or otherwise provide access to the Site or Platform to any third party, nor act as a service bureau or otherwise use the Site or Platform on behalf of any third party.」
  - → 「provide access to any third party」直接涵蓋把帳戶/API 給別人用；「act as a service bureau…on behalf of any third party」直接涵蓋代操。
- **Bitget**（Terms of Use，bitget.com/support/articles/360014944032）：
  - 不得分享帳密或「grant access to their account to any third party」；
  - 「Users may not assign their account…by way of donation, lending, leasing, transfer or otherwise without the consent of the website.」
  - 使用服務須「solely for their personal benefit…do not employ the services on behalf of third parties…unless they have obtained prior approval.」
  - 但 Bitget 另有《API Key Terms of Use》（bitget.com/support/articles/12560603797947）：「you should not share your API Keys with any third party **with whom you do not wish to share control of your Account**」，且帳戶持有人須對被授權之第三方的一切行為負責——措辭上比其他三所寬（暗示「你願意分享控制權」的第三方是被設想到的），但責任完全在帳戶持有人身上。

### 綜合判斷（明確標註：推論）

1. **給軟體 vs 給人**：四所實務上大規模容忍「把 API key 接給第三方**軟體/平台**」（交易機器人、組合追蹤、跟單平台——甚至有官方 broker/Link 計畫給這些服務商）。但「把 key 給另一個**自然人**做全權代操」正是 ToS「on behalf of any third party／不得由他人使用」條款針對的情境。文字上並無「給軟體可以、給人不行」的區分——這是執法實務的差異，不是條款豁免。
2. **執法風險型態**：主要觸發點是風控訊號（異地登入、IP 不符、出入金模式異常、被檢舉、出事後糾紛鬧到客服）。後果從要求重新 KYC、凍結帳戶、到終止帳戶沒收優惠。Binance 2025-10 曾一次封 600+ 帳戶（該案主因是未授權第三方工具刷 Alpha，但官方同場重申 account-sharing 違反 ToS）。平時「朋友帳戶＋你的 IP 下單」不必然被抓，但**一旦出糾紛（虧損、遺產、離婚、報警），帳戶共用事實會使雙方對交易所都失去條款保護**。
3. **正式 vs 非正式的實際差異**：managed/custodial sub-account 做的事和「trade-only API key」技術上幾乎一樣（都是只交易不出金），差別在於**交易所知情並認可這段代客關係**——這正是「prior written consent / previously approved」的實現方式。既然 Bitget 的正式門檻低到 5 萬 USDT/VIP2，個人想合規代操，把關係搬進 Bitget 託管子帳戶（或把朋友和你都升到 Binance VIP1 用 managed sub-account）比裸 API key 授權安全得多。
4. **台灣法規疊加（推論＋事實混合，非法律意見）**：2026-06-30 立法院三讀《虛擬資產服務法》，VASP 由登記制改許可制，監理涵蓋交換商、交易平台商、移轉商、**保管商**等 7 類；現行洗錢防制法第 6 條：未完成登記提供虛擬資產服務者有 2 年以下刑責（來源：sfb.gov.tw、blockcast.it 2026-06-30、ctee.com.tw，2026-07-16）。**若代操收費、經常性、對不特定人**，恐落入「提供虛擬資產服務之事業或人員」而需登記/許可；單純無償幫一位朋友屬灰色地帶。此段非法律意見，涉及收費代操前應諮詢律師。

### 對使用者情境的可行路徑排序（推論）

1. **Bitget 託管子帳戶**：朋友開戶做投資人、你帳戶放 ≥50,000 USDT（或到 VIP2）申請委託交易員 → 四所中唯一個人搆得到的「交易所知情」路徑。分潤自行私下協議。
2. **Binance managed sub-account**：需要朋友（投資人端）先到 VIP1（30 日現貨 100 萬 USD 或合約 500 萬 USD＋5 BNB）——門檻在「量」，小資金不現實。
3. **裸 API key（朋友帳戶開 Read+Trade key 給你）**：技術完全可行、出金鑰匙在朋友手上，但**四所 ToS 均可解讀為違約**；風險承擔者主要是朋友（帳戶可能被凍），你則承擔代操糾紛與台灣法規風險。若走此路：不開 Withdraw/Transfer 權限、綁 IP 白名單、雙方簽書面協議、金額控制在朋友可承受損失內。
4. **OKX / Bybit 正式路徑**：對台灣個人實質關閉（機構認證＋執照 / 機構白名單）。

---

## 不確定事項與查無清單

- **OKX 投資人端門檻**：一版文件寫「All users can apply to become investors」，另一版搜尋摘要出現「VIP level >=1 or self-owned funds >=5mm USDT if you need to apply」（疑為舊版交易團隊條件被混入摘要）。兩者矛盾，未直接核對，以官方現行 Rules 頁為準。
- **Bybit 投資人端是否也要白名單**：搜尋結果只明確說交易團隊要白名單；投資人端流程未見門檻，但無法排除也需申請。查無明文。
- **Ceffu 最低資產門檻**：查無公開數字；費率 0.24%（AUC<10M 級距）來自搜尋摘要引用官方費表 PDF，未直接核對。
- **Binance managed sub-account 交易團隊端的明文數字門檻**：官方 FAQ 只寫 VIP 專屬與聯繫客戶經理，查無公開數字。
- **Bitget「委託交易員」是否另有審核條件**（如面談、協議）：僅見資產/VIP 門檻與申請字樣，細節查無。
- 所有交易所頁面均因 proxy 403 未能直接核對原文，引文全部來自 WebSearch 摘要——關鍵決策（尤其 Bitget 5 萬 USDT 門檻與各所 ToS 原文）請在能直連的環境（Mac 手動功課）點開來源複核。

## 完整來源清單（查詢日期均為 2026-07-16）

1. Binance Managed Sub-Account FAQ — https://www.binance.com/en/support/faq/how-to-get-started-with-managed-sub-account-functions-and-frequently-asked-questions-0594748722704383a7c369046e489459
2. Binance Asset Management Sub-Account FAQ — https://www.binance.com/en/support/faq/asset-management-sub-account-functions-and-frequently-asked-questions-122f5fea8b954a29abcde94672d55e53
3. Binance Link Program — https://www.binance.com/en/support/faq/what-is-binance-link-program-04b2a5c9a8174096b3508f270404508c
4. Binance Terms of Use（PDF）— https://bin.bnbstatic.com/static/cms/cg08ou2ak0tn7mcplvfg/file/47a848de135d5747a84c1f66307920fe3d23eca2f500accc64e136f1499ba387.pdf ；https://www.binance.com/en/terms
5. Binance API key permission — https://developers.binance.com/docs/wallet/account/api-key-permission
6. Binance VIP 門檻 2026-03 更新 — https://www.datawallet.com/crypto/binance-vip-levels-explained ；PR Newswire「Binance Expands VIP Access」
7. Binance Fund Accounts — https://cointelegraph.com/news/binance-fund-accounts-portfolio-managers
8. Ceffu — https://www.ceffu.com/en/about-us ；費表 https://www.ceffu.com/download/Ceffu-Fee-Structure-EN.pdf ；MirrorX https://www.binance.com/en/blog/vip/keep-your-institutional-assets-in-thirdparty-custody-when-trading-on-binance-with-mirrorx-7578047330993855911
9. OKX Rules on Managed Trading Sub-accounts — https://www.okx.com/en-us/help/rules-on-managed-trading-sub-accounts
10. OKX Managed Trading Sub Account Feature / Step-by-step — https://www.okx.com/en-us/help/managed-trading-sub-account-feature-on-okx ；https://www.okx.com/en-us/help/step-by-step-guide-to-managed-trading-sub-accounts
11. OKX Terms of Service — https://www.okx.com/help/360021813691
12. OKX × Komainu — https://www.okx.com/learn/okx-komainu-enhanced-custody
13. OKX API — https://www.okx.com/docs-v5/en/ ；https://www.okx.com/en-us/help/api-faq
14. Bybit Custodial Trading Subaccount — https://www.bybit.com/en/help-center/article/Introduction-to-Custodial-Trading-Subaccount ；FAQ 同站
15. Bybit Institutional — https://www.bybit.com/en/institutional
16. Bybit Platform Terms and Conditions — https://www.bybit.com/en/help-center/article/Bybit-Platform-Terms-and-Conditions ；https://www.bybit.com/en/legal/terms-of-service
17. Bybit API 文件 — https://bybit-exchange.github.io/docs/v5/user/create-subuid-apikey
18. Bybit × Copper ClearLoop — https://copper.co/en/insights/company-news/bybit-enhances-institutional-trading-infrastructure-by-integrating-clearloop
19. Bitget 託管子帳戶規則/申請 — https://www.bitget.com/support/articles/12560603803137 ；https://www.bitget.com/apply-trading-team ；用戶手冊 https://www.bitget.com/support/articles/12560603803859
20. Bitget Terms of Use — https://www.bitget.com/support/articles/360014944032-terms-of-use ；API Key Terms of Use https://www.bitget.com/support/articles/12560603797947
21. Bitget Custody — https://www.bitget.com/custody ；API 文件 https://www.bitget.com/api-doc/common/quick-start
22. 台灣：金管會證期局 VASP 專區 https://www.sfb.gov.tw/ch/home.jsp?id=1053&parentpath=0,8 ；《虛擬資產服務法》三讀報導 https://blockcast.it/2026/06/30/taiwan-passes-virtual-asset-act-vasp-licensing-to-open-in-q1/ ；https://www.ctee.com.tw/news/20260630701986-430301
23. Binance 封禁 600+ 帳戶（2025-10）— https://www.theblock.co/post/375278/binance-bans-more-than-600-accounts-over-unauthorized-third-party-tools
