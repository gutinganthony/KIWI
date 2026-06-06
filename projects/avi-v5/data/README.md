# 回測數據（dip_combo_backtest.py 用）

CSV 不入 git（大、可重新下載）。重建方式：

```python
import requests
base="https://raw.githubusercontent.com"
files={
 "vix.csv":"/datasets/finance-vix/main/data/vix-daily.csv",                # CBOE VIX 1990+
 "fng.csv":"/whit3rabbit/fear-greed-data/main/fear-greed.csv",             # CNN F&G 2011+
 "spx.csv":"/fja05680/dow-sp500-100-years/main/SP500.csv",                 # ^GSPC 1927-2019
 # spx_investpy.csv / voo.csv 取自 danielsobrado/notebooks_invest 接合到 2021
 "taiex.csv":"/VickykciV/Stock-Market-Network/main/Taiwan%20Weighted%20TWII%20Historical%20Data.csv", # 2011-2022
}
for n,p in files.items(): open(f"data/{n}","w").write(requests.get(base+p,timeout=40).text)
```

已對照已知值驗真：VIX 2020-03-16=82.69、2008-11-20=80.86、2018-02-05=37.32；F&G 2020-03-23=5.0。
