# alloc-backtest：台幣計價的股債配置回測

報告：`topics/business/2026-11-17-allocation-backtest-50-bond-us-tw.md`

## 檔案
| 檔案 | 作用 |
|---|---|
| `alloc_load.py` | 讀 Yahoo chart JSON（還原價優先） |
| `tw0050.py` | 用 FinMind 原始收盤＋現金股利＋2025-06-18 一拆四，重建 0050 含息日報酬；內建漲跌幅檢查 |
| `alloc_bt.py` | 月底序列、美元資產×FRED 匯率換成台幣、組合（每年 12 月再平衡）、績效統計；直接執行會印主表 |
| `alloc_ext.py` | 美股比重掃描、總經情境（升息／10 年債／CPI）之後 12 個月報酬 |
| `alloc_mc.py` | 以 12 個月為一塊的 block bootstrap；債券平均值換成目前殖利率；可設股票報酬折減 |

## 資料（不進 repo，放在程式上一層的 `alloc/`、`alloc2/`）
```bash
# alloc/：Yahoo（瀏覽器 UA；用 period1/period2，不要用 range=max，否則會拿到月線）
for t in QQQ SPY AGG IEF TLT BND SHY VCIT LQD ^TWII ^GSPC ^NDX; do f=$(echo $t | tr '=^' '__')
  curl -s -A 'Mozilla/5.0' -o alloc/$f.json "https://query1.finance.yahoo.com/v8/finance/chart/$t?period1=631152000&period2=1795000000&interval=1d&events=div%2Csplit"; sleep 1; done
# alloc2/：FRED 與 FinMind
for id in DEXTAUS FEDFUNDS CPIAUCSL DGS10 DGS2 BAMLC0A0CMEY; do curl -s -o alloc2/$id.csv "https://fred.stlouisfed.org/graph/fredgraph.csv?id=$id"; done
curl -s -o alloc2/fm0050.json "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id=0050&start_date=2003-06-01"
curl -s -o alloc2/fmdiv.json  "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockDividend&data_id=0050&start_date=2003-01-01"
```
⚠️ 不要用 Yahoo `0050.TW`（2014 年前的分割調整錯誤）和 `TWD=X`（有假跳動）。詳見 `agents/LEARNINGS.md` 2026-11-17。

`alloc_bt.py` 裡的 `END` 是資料截止日，更新資料後要改。
