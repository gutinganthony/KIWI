#!/usr/bin/env python3
"""
在「本機(Mac，可連 Yahoo/CNN)」抓【完整最新】資料 → 寫成回測引擎要的 CSV。
雲端容器被擋(yfinance/FRED)，所以這支要在你 Mac 上跑；跑完資料就到 2026。

用法（在 projects/avi-v5/ 目錄下）：
  python scripts/fetch_data.py
然後：
  python scripts/dip_combo_backtest.py --market US --horizon 126 --robust
"""
import pathlib, sys
try:
    import pandas as pd, yfinance as yf, requests
except ImportError:
    sys.exit("請先安裝：pip install pandas numpy scipy yfinance requests")

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(exist_ok=True)

def dl(ticker, start="1990-01-01"):
    print(f"  抓 {ticker} …", end=" ", flush=True)
    df = yf.download(ticker, start=start, auto_adjust=False, progress=False)
    if df is None or df.empty:
        sys.exit(f"\n{ticker} 抓不到（檢查網路/代碼）")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df = df.reset_index()
    print(f"{df['Date'].min().date()} → {df['Date'].max().date()}（{len(df)} 列）")
    return df

print("== 下載完整最新資料 ==")
# VIX → DATE,OPEN,HIGH,LOW,CLOSE（引擎 load_vix 要這格式）
v = dl("^VIX").rename(columns={"Date":"DATE","Open":"OPEN","High":"HIGH","Low":"LOW","Close":"CLOSE"})
v[["DATE","OPEN","HIGH","LOW","CLOSE"]].to_csv(DATA/"vix.csv", index=False)

# S&P 500（1950 起）→ 標準 Date,Open,High,Low,Close,...
dl("^GSPC", start="1950-01-01").to_csv(DATA/"spx.csv", index=False)

# TAIEX（1997 起）
dl("^TWII", start="1997-01-01").to_csv(DATA/"taiex.csv", index=False)

# CNN Fear & Greed 完整歷史（2011→今，用自動更新的 GitHub 鏡像）
print("  抓 CNN Fear&Greed …", end=" ", flush=True)
fng = requests.get("https://raw.githubusercontent.com/whit3rabbit/fear-greed-data/main/fear-greed.csv", timeout=60).text
(DATA/"fng.csv").write_text(fng)
print(f"{fng.count(chr(10))} 列")

# 移除舊的雲端接合檔（若存在），避免引擎走接合舊路徑
for f in ("spx_investpy.csv", "voo.csv", "spx_try.csv"):
    p = DATA/f
    if p.exists(): p.unlink()

print("\n✅ 完成。資料都在 data/。接著跑：")
print("   python scripts/dip_combo_backtest.py --market US --horizon 126 --robust")
print("   python scripts/dip_combo_backtest.py --market TW --horizon 252 --robust")
