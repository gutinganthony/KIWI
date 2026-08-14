# surge-scan — 台股飆股特徵的 case-control 掃描

支撐 `topics/business/2026-08-14-tw-surge-stock-anatomy.md` 的資料管線。
資料源：FinMind API v4 免費層（免 token）。**雲端 session 唯一可用的台股量化資料源**，
其餘（MOPS / TWSE / TPEx OpenAPI / Yahoo / 鉅亨 / MoneyDJ / Goodinfo）皆被 egress proxy 擋。

## 執行順序

```bash
python3 fetch_prices.py    # 全市場日 K -> prices.ndjson（約 2,100 次請求）
python3 fetch_chips2.py    # 法人 + 月營收，只抓飆股 + 對照樣本 -> chips.ndjson
python3 scan.py            # 取樣股票日 + 點時特徵 -> scan.json
python3 analyze.py         # 特徵分十分位、訓練/樣本外切分
python3 outcomes.py        # 用「可實現的持有報酬」複驗（不是最大漲幅）
python3 turnover.py        # 拆解「成交金額大」vs「爆量」
python3 validate.py        # 排除 ETF、分層複驗、個案回測
```

兩支 fetch 都可**續跑**（讀既有輸出跳過已完成標的），中斷後直接重跑即可。

## ⚠️ FinMind 免費層限流（實測 2026-08-14）

| 狀態碼 | 意義 | 處理 |
|---|---|---|
| 402 | 時數配額用盡 | 睡 600 秒再試 |
| 403 `ip banned` | 打太兇被暫時封鎖，回應含 `retry_after` 秒數 | 睡 `retry_after + 30` |

`fetch_prices.py` 用 8 執行緒無節流跑完 2,162 檔後即觸發封鎖。
`fetch_chips2.py` 已改為**單執行緒、每次請求間隔 6 秒**（≈600 req/hr）。
要抓全市場多個資料集時，請沿用節流版，不要用並行版。

不支援的用法：`data_id` 不接受逗號分隔多檔；省略 `data_id` 的整批下載需付費層。

## adjust.py — 為什麼一定要用

台股正常日內限制 ±10%，單日收盤變動超過 ±11.5% 幾乎必為公司行動
（減資、股票分割、大額除權、新上市首日、暫停交易後復牌），**不是可交易的漲幅**。
不處理的話，國巨 2025-08-25 的 1:4 分割（546 → 143）會被當成崩跌，
反向的減資則會被當成飆漲。

但 ±10% 並非永遠成立：2024-08-05（日圓套利平倉）與 2025-04-07~10（關稅崩跌）
全市場多檔越界，那是真實行情。因此 `adjust.py` 以**跨截面中位數報酬**
（|median| ≥ 4.5%）自動辨識全市場震盪日，只中性化**個股獨有**的越界日。

## 點時（point-in-time）鐵律

`TaiwanStockMonthRevenue` 的 `date` 欄是**所屬月份的次月 1 日，不是公布日**。
台股法定公布時點為次月 10 日前，故 `scan.py` 以「次月 11 日起可得」計算，
否則會偷看未來、把落後指標誤判成領先指標。

## 評估鐵律

用「未來 60 日**最大**漲幅」評估策略會系統性偏好高波動股，而且你賣不到最高點。
所有結論都必須以 `outcomes.py` 的**持有到期報酬 + 期間最大回檔**複驗。
