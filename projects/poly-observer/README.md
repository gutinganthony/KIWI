# poly-observer — Polymarket 聰明錢唯讀觀察器

追蹤 Polymarket 公開排行榜錢包，回答兩個問題：

1. **存在性**：排行榜上是否存在「可持續獲利」的聰明錢錢包（而非一次性爆紅或做市機器人）？
2. **可觀察性**：建立每日 watchlist，累積數據觀察這些錢包的前瞻持續性。

## 唯讀聲明

本專案**純唯讀**：只對 Polymarket 公開免金鑰 API 發 HTTP GET。
不含任何下單、私鑰、簽章、錢包連線程式碼；不構成投資建議。

## 架構

```
config.py              端點清單（含 fallback）＋所有分類/警示門檻常數
fetch.py               抓 leaderboard（1m/all）＋每錢包 activity/positions/value/pnl 曲線
                       → data/snapshots/{UTC日期}/（wallets/*.json、leaderboard.json、meta.json）
                       → 維護 data/wallet_registry.json
verify_smart_money.py  對 snapshot 每錢包算指標並分類：
                       mm_bot_like / one_hit / consistent_winner / degraded /
                       choppy / insufficient_data
                       → data/reports/verification_{date}.{md,json}
analyze.py             watchlist 維護＋每日異動（新進/退出/退化警示）
                       → data/watchlist.json、data/reports/daily_{date}.md
tests/                 離線 fixtures ＋自測（不碰網路）
data/seeds.json        永遠納入宇宙的種子錢包（含 ground-truth 校驗用的已知爆倉戶）
.github/workflows/poly-observer.yml   每日 06:30 台北自動跑＋commit-back 數據
```

資料流：`fetch → verify → analyze`，三支各自防禦（端點全掛只記 meta，不 crash），
確保 GitHub Actions 第一次遠端跑就能落地診斷資訊。

## 如何在本機跑

```bash
cd projects/poly-observer
pip install -r requirements.txt          # 只需要 requests

python3 fetch.py --max-wallets 60        # 需要能連 Polymarket API 的網路環境
python3 verify_smart_money.py --snapshot data/snapshots/$(date -u +%F)
python3 analyze.py --snapshot data/snapshots/$(date -u +%F)

python3 tests/test_offline.py            # 離線自測（不碰網路）
```

## 輸出說明

| 檔案 | 內容 |
|---|---|
| `data/snapshots/{date}/wallets/{addr}.json` | 單錢包原始數據（activity/positions/value/pnl 曲線） |
| `data/snapshots/{date}/leaderboard.json` | 兩窗排行榜原始回應 |
| `data/snapshots/{date}/meta.json` | 端點健康（status＋錯誤 body 前 200 字）、成功/失敗計數、耗時 |
| `data/wallet_registry.json` | 錢包出現紀錄：first_seen / last_seen / appearances |
| `data/reports/verification_{date}.md` | 存在性檢驗：端點健康 → 分類統計 → winner 明細 → ground-truth 校驗 → 裁決 |
| `data/reports/verification_{date}.json` | 同上，機器可讀完整指標 |
| `data/watchlist.json` | consistent_winner 全收，含逐日指標快照歷史（退出者標 active=false 留檔） |
| `data/reports/daily_{date}.md` | 每日異動：新進/退出/退化警示（30 天 PnL 轉負、頻率暴增 3x、類別漂移） |

### 分類定義（門檻在 config.py，可調）

- `mm_bot_like`：>1500 筆/月，或平均單筆持有 <1 小時 — 做市/套利機器人，不可跟
- `one_hit`：最佳單月 >70% 總 PnL，或活躍 <2 個月 — 一次性爆紅
- `consistent_winner`：活躍 ≥3 月、正月比 ≥0.6、總 PnL >$10k、回撤 <50% peak、頻率 5–1500 筆/月
- `degraded`：曾符合 consistent 條件但近 30 天 PnL < −15% × 總 PnL
- `choppy`：其餘；`insufficient_data`：資料不足（無 PnL 曲線且交易 <5 筆）

### 裁決口徑

consistent_winner ≥5 → 「聰明錢存在（存在性檢驗通過；前瞻持續性需觀察器累積數據驗證）」；
1–4 → 「弱存在」；0 → 「未發現」。

## 已知限制

- **倖存者偏差**：宇宙取自「今日」排行榜，只看得到還在榜上的贏家；本檢驗證明「存在性」，非「跟得到」。
- pnl 曲線缺失時以 activity 現金流近似（排除 REDEEM），標 `low_confidence`。
- activity 每錢包上限 1500 筆，超高頻錢包的頻率指標為下限估計（`activity_truncated` 有標）。
