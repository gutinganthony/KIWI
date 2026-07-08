#!/usr/bin/env python3
"""
WaveTrend 振盪器（LazyBear 版）— 判斷個股/大盤的超買超賣與多空轉折
==================================================================
公式(LazyBear WaveTrend Oscillator)：
  ap = hlc3;  esa = EMA(ap, n1);  d = EMA(|ap-esa|, n1)
  ci = (ap-esa)/(0.015*d);  tci = EMA(ci, n2)
  WT1 = tci;  WT2 = SMA(WT1, 4)
訊號：WT1>OB(+60)=超買/偏空; WT1<OS(-60)=超賣/偏多(抄底); WT1 上穿 WT2=多方交叉。
附帶：距 200DMA、RSI14、距 52 週高點回檔，作為多空位階輔助。

用法：
  本機 Mac(可連 Yahoo)：python scripts/wavetrend.py --ticker ^GSPC ^TWII ^N225 ^VIX PLAB COHR MTRN COHU 6213.TW 6820.TWO 6643.TWO 3363.TWO 5384.T 4109.T AAOI 6830.TWO
  雲端(讀本地CSV)       ：python scripts/wavetrend.py --csv data/vix.csv
"""
import argparse, sys
import numpy as np, pandas as pd
N1, N2, OB, OS = 10, 21, 60.0, -60.0

def ema(s, n): return s.ewm(span=n, adjust=False).mean()
def rsi(c, n=14):
    d=c.diff(); up=d.clip(lower=0).rolling(n).mean(); dn=(-d.clip(upper=0)).rolling(n).mean()
    return 100-100/(1+up/dn.replace(0,np.nan))

def wavetrend(df):
    ap=(df["high"]+df["low"]+df["close"])/3
    esa=ema(ap,N1); d=ema((ap-esa).abs(),N1)
    ci=(ap-esa)/(0.015*d.replace(0,np.nan))
    wt1=ema(ci,N2); wt2=wt1.rolling(4).mean()
    return wt1, wt2

def load_csv(path):
    df=pd.read_csv(path)
    # 中文 investing.com 格式(日期/收盘/开盘/高/低)轉英文
    zh={"日期":"date","收盘":"close","开盘":"open","高":"high","低":"low"}
    if any(c in df.columns for c in zh): df=df.rename(columns=zh)
    cols={str(c).lower():c for c in df.columns}
    dcol=cols.get("date") or cols.get("datetime")
    if dcol is None: sys.exit(f"找不到日期欄(欄位={list(df.columns)})")
    df[dcol]=pd.to_datetime(df[dcol].astype(str).str.replace("年","-").str.replace("月","-").str.replace("日",""),errors="coerce")
    out=pd.DataFrame({"date":df[dcol]})
    for k in ("open","high","low","close"):
        src=cols.get(k) or cols.get("adj close" if k=="close" else k)
        out[k]=pd.to_numeric(df[src].astype(str).str.replace(",",""),errors="coerce") if src else np.nan
    # 若無 H/L（如某些指數檔），用 close 代
    for k in ("high","low","open"):
        if out[k].isna().all(): out[k]=out["close"]
    return out.dropna(subset=["date","close"]).set_index("date").sort_index()

def analyze(name, df):
    if len(df)<60: print(f"{name:<10} 資料不足({len(df)})"); return
    wt1,wt2=wavetrend(df); c=df["close"]
    sma200=c.rolling(200).mean(); r=rsi(c); dd=c/c.rolling(252).max()-1
    i=-1
    w1,w2=wt1.iloc[i],wt2.iloc[i]
    zone="超買🔴" if w1>OB else ("超賣🟢" if w1<OS else "中性⚪")
    # 近 3 日交叉
    cross=""
    for k in (-1,-2,-3):
        if wt1.iloc[k]>wt2.iloc[k] and wt1.iloc[k-1]<=wt2.iloc[k-1]: cross="近期多方交叉↑"; break
        if wt1.iloc[k]<wt2.iloc[k] and wt1.iloc[k-1]>=wt2.iloc[k-1]: cross="近期空方交叉↓"; break
    reg = "站上200DMA🐂" if (pd.notna(sma200.iloc[i]) and c.iloc[i]>=sma200.iloc[i]) else "跌破200DMA🐻"
    dist=(c.iloc[i]/sma200.iloc[i]-1)*100 if pd.notna(sma200.iloc[i]) else np.nan
    print(f"{name:<10} {str(df.index[i].date())}  收{c.iloc[i]:.1f}  WT1={w1:6.1f} WT2={w2:6.1f} {zone} {cross}")
    print(f"           RSI={r.iloc[i]:.0f}  距52w高 {dd.iloc[i]*100:+.1f}%  {reg}(距200DMA {dist:+.1f}%)")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ticker",nargs="+"); ap.add_argument("--csv")
    ap.add_argument("--start",default="2015-01-01")
    a=ap.parse_args()
    print(f"=== WaveTrend (n1={N1},n2={N2},OB=+{OB:.0f},OS={OS:.0f}) ===")
    if a.csv:
        analyze(a.csv.split('/')[-1], load_csv(a.csv)); return
    import yfinance as yf
    for t in a.ticker:
        try:
            df=yf.download(t,start=a.start,auto_adjust=False,progress=False)
            if isinstance(df.columns,pd.MultiIndex): df.columns=[x[0] for x in df.columns]
            df=df.rename(columns=str.lower)[["open","high","low","close"]]
            analyze(t,df)
        except Exception as e: print(f"{t:<10} ERR {e}")

if __name__=="__main__": main()
