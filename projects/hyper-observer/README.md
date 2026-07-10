# hyper-observer — Hyperliquid 永續聰明錢唯讀觀察器

追蹤 Hyperliquid（永續合約 DEX）公開資料，找「持續獲利、風險可控、非刷量、仍活躍」的錢包。
本里程碑先做到「**存在性檢驗 ＋ 逐錢包 dossier**」；跟單模擬器是下一個里程碑（本次不做），
對齊姊妹專案 poly-observer 當初「先存在性、後模擬器」的節奏。

回答兩個問題：

1. **存在性**：Hyperliquid 上是否存在「風險調整後持續獲利」的聰明錢（而非一次性爆賺、爆倉賭徒、或刷量做市）？
2. **可觀察性**：對候選錢包逐日產 dossier，累積數據觀察前瞻持續性。

## 唯讀聲明

本專案**純唯讀**：只對 Hyperliquid 公開免金鑰端點發唯讀查詢：

- `POST https://api.hyperliquid.xyz/info`（免金鑰 info API，只查不改；body 帶 `{"type":..., "user":...}`）
- `GET https://stats-data.hyperliquid.xyz/Mainnet/leaderboard`（未文件化前端快取端點，脆弱）

**絕不**包含任何下單、簽章、私鑰、錢包連線、exchange endpoint（`/exchange`）程式碼；不構成投資建議。

## 架構

```
config.py         info 基底 URL＋type 清單＋leaderboard 端點＋所有永續分類門檻常數＋種子＋ground-truth
fetch.py          試打 leaderboard（脆弱、失敗退回 seeds）＋每錢包 POST info 抓
                  clearinghouseState / portfolio / userFills / userFunding
                  → data/snapshots/{UTC日期}/（wallets/*.json、leaderboard.json、meta.json）
                  → 維護 data/wallet_registry.json
classify.py       對 snapshot 每錢包算永續指標並分類：
                  consistent_winner / blowup_risk / wash_suspect / one_hit /
                  dormant / choppy / insufficient_data
                  → data/reports/verification_{date}.{md,json}
track_wallet.py   單錢包深度 dossier：目前持倉（方向/槓桿/強平價/未實現PnL）、portfolio 績效、
                  近 20 筆成交、新開倉/平倉偵測、timeline
                  → data/tracked/{addr}/（dossier_{date}.{md,json}、latest_raw.json、timeline.jsonl）
tests/            離線 fixtures ＋自測（不碰網路）
data/seeds.json   永遠納入宇宙的種子錢包（含 ground-truth 校驗用的已知爆倉戶 James Wynn）
.github/workflows/hyper-observer.yml   每日 06:45 台北自動跑＋commit-back 數據
```

資料流：`fetch → classify → track`，三支各自防禦（端點全掛只記 meta，不 crash），
確保 GitHub Actions 第一次遠端跑就能落地診斷資訊。

## 如何在本機跑

```bash
cd projects/hyper-observer
pip install -r requirements.txt          # 只需要 requests

python3 fetch.py --max-wallets 60        # 需要能連 Hyperliquid API 的網路環境
python3 classify.py --snapshot data/snapshots/$(date -u +%F)
python3 track_wallet.py --address 0x5078c2fbea2b2ad61bc840bc023e35fce56bedb6 \
        --snapshot data/snapshots/$(date -u +%F)

python3 tests/test_offline.py            # 離線自測（不碰網路）
```

## 永續分類定義（門檻在 config.py，可調）

永續合約「勝率」近乎無意義（緊停利寬停損／馬丁格爾可造 90%+ 勝率直到爆倉），
故用**風險調整 PnL＋profit factor＋量/PnL 比＋淨方向＋槓桿**取代天真勝率：

- `blowup_risk`：曾被強平（userFills 出現 liquidation）、或 PnL 曲線單日崩跌 >50% peak、
  或目前槓桿 ≥25x＋回撤 ≥60% — James Wynn 型高槓桿賭徒，判為壞（**安全性優先，最早判**）。
- `wash_suspect`：量 ≥$1M 且 量/PnL 比 ≥500（巨量、PnL≈0），或無淨方向＋極短持倉＋高頻自成交 — 疑刷量，排除於 winner。
- `one_hit`：活躍跨度 <30 天，或單一最佳月 >70% 總 PnL — 一次性爆賺。
- `dormant`：閒置 >30 天且目前無持倉 — 無單可跟。
- `consistent_winner`：活躍 ≥60 天、總 PnL >$10k、回撤 <40% peak、profit factor ≥1.3、
  目前槓桿 ≤20x、正月比 ≥0.5，且非 wash/blowup — **值得進一步觀察、可能可跟的候選**。
- `choppy`：其餘；`insufficient_data`：無 portfolio PnL 曲線且成交 <5 筆。

分類優先序（安全性優先）：insufficient → blowup_risk → wash_suspect → dormant → one_hit → consistent_winner → choppy。

## 裁決口徑

consistent_winner ≥5 →「聰明錢存在（存在性檢驗通過；前瞻持續性需觀察器累積數據驗證）」；
1–4 →「弱存在」；0 →「未發現」。

## 輸出說明

| 檔案 | 內容 |
|---|---|
| `data/snapshots/{date}/wallets/{addr}.json` | 單錢包原始 info（clearinghouseState/portfolio/userFills/userFunding） |
| `data/snapshots/{date}/leaderboard.json` | leaderboard 原始回應＋解析出的地址清單（含失敗時的診斷） |
| `data/snapshots/{date}/meta.json` | 端點健康（status＋錯誤 body 前 200 字）、成功/失敗計數、耗時 |
| `data/wallet_registry.json` | 錢包出現紀錄：first_seen / last_seen / appearances |
| `data/reports/verification_{date}.{md,json}` | 存在性檢驗：端點健康 → 分類統計 → winner 明細 → ground-truth 校驗 → 裁決 |
| `data/tracked/{addr}/dossier_{date}.{md,json}` | 單錢包 dossier：持倉/績效/成交/新開倉偵測 |
| `data/tracked/{addr}/latest_raw.json` | 追蹤錢包原始 snapshot 持久化（prune 後仍存，供未來模擬器用） |
| `data/tracked/{addr}/timeline.jsonl` | 逐日一行：total_pnl / 持倉數 / 新開倉數 / 分類 |

## 與 poly-observer（Polymarket 版）的差異

| 維度 | poly-observer | hyper-observer |
|---|---|---|
| 標的 | 二元結果份額 0~1，全額擔保 | 槓桿永續合約，mark-to-market |
| API | 多個 REST GET 端點（data-api 等） | 單一 `POST /info`（免金鑰）＋脆弱 leaderboard GET |
| 方向/槓桿 | 無（1:1） | 多/空（szi 正負）＋3–50x 槓桿＋強平價＋資金費 |
| 已實現 PnL 來源 | activity 現金流近似（贏家倖存者偏誤：輸單無 REDEEM） | userFills.closedPnl（**贏輸平倉皆有值，無此偏誤**） |
| 「壞」分類 | mm_bot_like / degraded | **blowup_risk（爆倉）/ wash_suspect（刷量）** |
| ground-truth | xdd07070（dormant） | **James Wynn（blowup_risk，194 次強平、$100M→$900）** |
| 核心指標 | 月度 PnL＋正月比率＋頻率 | **profit factor＋回撤＋量/PnL 比＋淨方向＋槓桿** |

## 已知限制

- **倖存者偏差**：宇宙取自「今日」leaderboard（＋seeds），只看得到還在榜上的贏家；本檢驗證明「存在性」，非「跟得到」。
- **刷量污染**：Hyperliquid 空投以交易量計分，排行榜混雜大量 wash trading；分類器以量/PnL 比＋淨方向旗標排除疑似刷量戶，但無法百分百過濾。
- **leaderboard 脆弱**：未文件化端點可能 403／改 schema／加防爬；fetch.py 失敗時退回只用 seeds 並記 meta，不 crash。
- **種子未鏈上驗證**：seeds 地址來自 2026-07-10 研究快照，本環境未鏈上驗證；首次 CI 跑會用真 info API 覆核。
- **槓桿風險**：過往績效不保證未來不爆倉；consistent_winner 僅代表「值得觀察」，非「安全可跟」。
