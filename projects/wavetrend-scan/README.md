# wavetrend-scan：WaveTrend 全市場適用性掃描

找出美股／台股中 WaveTrend（`skills/wavetrend/SKILL.md` 參數）訊號最有效的股票，並檢驗「有效」是否只是運氣。
結果與解讀見 `topics/business/2026-09-30-wavetrend-universe-scan-us-tw.md`。

## 重跑步驟（在本資料夾執行；資料寫入 `scan/`，不入庫）

```bash
mkdir -p scan/us scan/tw
# 1. 股票清單（FinMind 免費版可取）
curl -s -o scan/tw_info.json "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo"
curl -s -o scan/us_info.json "https://api.finmindtrade.com/api/v4/data?dataset=USStockInfo"
# 2. 下載日線（美股：FinMind；台股：Yahoo query1，約 2,100 檔）
python3 dl.py us
python3 dl.py tw
# 3. 大盤序列：scan/idx_spy.json.gz（SPY）與 scan/idx_0050.json.gz（0050.TW），格式同個股檔
# 4. 分析與排名
pip install numpy
python3 wtscan.py us && python3 rank.py us
python3 wtscan.py tw && python3 rank.py tw
```

## 注意
- ⚠️ **不要同時開多個 `dl.py` 寫同一個資料夾**——2026-09-30 這樣做造成 8 個 gzip 檔損毀（`wtscan` 讀取時會報錯，刪掉重抓即可）。
- 台股 Yahoo 資料品質差：`wtscan.load(tw=True)` 會把超過漲跌幅限制（2015-06-01 前 7.5%、之後 10.5%）的單日變動視為公司行動或資料錯誤並接合；接合 >10 次的股票直接排除。
- 評分＝前半段（2009-07～2017）與後半段（2018～2026-09）z 分數中較差者；`rank.py` 會同時輸出「訊號日期隨機平移」的對照分數。
