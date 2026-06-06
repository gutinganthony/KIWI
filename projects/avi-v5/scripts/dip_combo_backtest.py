#!/usr/bin/env python3
"""
抄底指標組合回測引擎 — 找出「勝率最高」的指標組合（美股 + 台股）
=================================================================
用真實歷史數據（GitHub 公開資料集，已對照已知崩盤值驗證）回測：
  美股：S&P500 日線(1990–2021，含 2000/2008/2020 三大崩盤) + CBOE VIX(1990+) + CNN Fear&Greed(2011+)
  台股：TAIEX 日線(2011–2022，含 2020 COVID) + 自建波動率恐懼代理

方法：
  1. 對每個指標定義「抄底觸發條件」(oversold/fear)；牛熊(200DMA)當過濾。
  2. 窮舉 單 / 雙 / 三 條件 AND 組合。
  3. 事件去叢集(gap=21交易日)；算 +21/63/126/252 日後報酬。
  4. 「勝率」= 之後報酬>0 的比例；和「無條件基準勝率」比較，用二項檢定算 p 值(單尾 greater)。
  5. 篩選：樣本數達門檻 + 統計顯著(p<0.05) → 依勝率排序，找最佳組合。

用法：python scripts/dip_combo_backtest.py [--market US|TW] [--horizon 63] [--min-n 12]
資料檔在 projects/avi-v5/data/（vix.csv fng.csv spx.csv spx_investpy.csv voo.csv taiex.csv）。
"""
import argparse, itertools, warnings
import numpy as np, pandas as pd
from scipy.stats import binomtest
warnings.filterwarnings("ignore")
DATA = __import__("pathlib").Path(__file__).resolve().parent.parent / "data"
HOR = {"1M": 21, "3M": 63, "6M": 126, "12M": 252}

# ── 資料載入 ──────────────────────────────────────────────────────────────────
def load_spx():
    a = pd.read_csv(DATA/"spx.csv", parse_dates=["Date"]).set_index("Date")["Close"].sort_index()
    a = a[a.index <= "2019-12-23"]
    b = pd.read_csv(DATA/"spx_investpy.csv", parse_dates=["Date"]).set_index("Date")["Close"].sort_index()
    b = b[(b.index > "2019-12-23") & (b.index <= "2020-12-31")]
    v = pd.read_csv(DATA/"voo.csv", parse_dates=["Date"]).set_index("Date")["Close"].sort_index()
    scale = b.loc[:"2020-12-31"].iloc[-1] / v.asof(b.loc[:"2020-12-31"].index[-1])
    v = v[v.index > "2020-12-31"] * scale
    s = pd.concat([a, b, v]); s = s[~s.index.duplicated()].sort_index()
    return s.rename("close")

def load_vix():
    return pd.read_csv(DATA/"vix.csv", parse_dates=["DATE"]).set_index("DATE")["CLOSE"].sort_index().rename("vix")

def load_fng():
    return pd.read_csv(DATA/"fng.csv", parse_dates=["Date"]).set_index("Date")["Fear Greed"].sort_index().rename("fng")

def load_taiex():
    df = pd.read_csv(DATA/"taiex.csv")
    df.columns = ["date","close","open","high","low","vol","chg"]
    def pdate(s):
        s=str(s).replace("年","-").replace("月","-").replace("日","")
        return pd.to_datetime(s, errors="coerce")
    df["date"]=df["date"].map(pdate)
    df["close"]=df["close"].astype(str).str.replace(",","").astype(float)
    return df.dropna(subset=["date"]).set_index("date")["close"].sort_index().rename("close")

# ── 指標 ──────────────────────────────────────────────────────────────────────
def rsi(close, n=14):
    d=close.diff(); up=d.clip(lower=0).rolling(n).mean(); dn=(-d.clip(upper=0)).rolling(n).mean()
    return 100-100/(1+up/dn.replace(0,np.nan))

def build_panel(close, vix=None, fng=None):
    df=pd.DataFrame({"close":close})
    df["sma200"]=close.rolling(200).mean()
    df["sma50"]=close.rolling(50).mean()
    df["rsi"]=rsi(close)
    df["dd"]=close/close.rolling(252).max()-1.0          # 距 52 週高點回檔
    df["dist50"]=close/df["sma50"]-1.0
    df["above200"]=close>=df["sma200"]
    df["rvol"]=close.pct_change().rolling(20).std()*np.sqrt(252)   # 20日年化已實現波動(台股恐懼代理)
    df["rvol_p"]=df["rvol"].rolling(252).rank(pct=True)            # 一年內波動分位
    if vix is not None: df["vix"]=vix.reindex(df.index).ffill(limit=2)
    if fng is not None: df["fng"]=fng.reindex(df.index)            # 不前填，缺=非2011+
    return df

# ── 觸發條件 ──────────────────────────────────────────────────────────────────
def triggers_US(df):
    t={}
    for x in (25,30,35,40): t[f"VIX>={x}"]=df["vix"]>=x
    for x in (25,20,15,10): t[f"FNG<={x}"]=df["fng"]<=x
    for x in (35,30,25):    t[f"RSI<={x}"]=df["rsi"]<=x
    for x in (10,15,20):    t[f"DD<=-{x}%"]=df["dd"]<=-x/100
    return t

def triggers_TW(df):
    t={}
    for x in (35,30,25):    t[f"RSI<={x}"]=df["rsi"]<=x
    for x in (10,15,20):    t[f"DD<=-{x}%"]=df["dd"]<=-x/100
    for x in (8,12,15):     t[f"dist50<=-{x}%"]=df["dist50"]<=-x/100
    for x in (0.90,0.95):   t[f"RVOL_p>={x}"]=df["rvol_p"]>=x      # 波動飆高=恐懼代理
    return t

FILTERS={"ABOVE_200DMA":lambda d:d["above200"], "BELOW_200DMA":lambda d:~d["above200"]}

# ── 回測 ──────────────────────────────────────────────────────────────────────
def decluster(idx_bool, gap=21):
    days=list(np.where(idx_bool.values)[0]); kept=[]; last=-10**9
    for p in days:
        if p-last>=gap: kept.append(p); last=p
    return kept

def fwd_returns(close, pos, h):
    c=close.values; out=[]
    for p in pos:
        out.append(c[p+h]/c[p]-1 if p+h<len(c) else np.nan)
    return np.array(out,float)

def dd_after(close, pos, h=252):
    c=close.values; out=[]
    for p in pos:
        e=min(p+h,len(c)-1); out.append(c[p:e+1].min()/c[p]-1 if e>p else np.nan)
    return np.array(out,float)

def base_rate(close,h):
    c=close.values
    if len(c)<=h: return np.nan
    r=[c[p+h]/c[p]-1 for p in range(len(c)-h)]
    return np.mean(np.array(r)>0)

_COLMAP={"VIX":"vix","FNG":"fng","RSI":"rsi","DD":"dd","dist50":"dist50","RVOL":"rvol_p"}
def referenced_cols(names, filt):
    cols=set()
    for nm in names:
        for k,c in _COLMAP.items():
            if nm.startswith(k): cols.add(c)
    if filt: cols.add("sma200")
    return cols

def matched_start(df, cols):
    """期間配對：取所有引用指標都可用(non-NaN)的最早日 → 避免拿牛市子期間和長期基準比。"""
    starts=[df[c].first_valid_index() for c in cols if c in df]
    starts=[s for s in starts if s is not None]
    return max(starts) if starts else df.index[0]

def evaluate(df, cond, horizon, min_n, names, filt):
    cols=referenced_cols(names, filt)
    t0=matched_start(df, cols)
    sub=df.loc[t0:]
    base=base_rate(sub["close"].dropna(), horizon)
    if base is None or np.isnan(base): return None
    cond=cond.loc[t0:]
    pos=decluster(cond.fillna(False), 21)
    if len(pos)<min_n: return None
    r=fwd_returns(sub["close"],pos,horizon); r=r[~np.isnan(r)]
    if len(r)<min_n: return None
    wins=int((r>0).sum()); n=len(r); wr=wins/n
    p=binomtest(wins,n,min(base,0.999),alternative="greater").pvalue
    dda=dd_after(sub["close"],pos); dda=dda[~np.isnan(dda)]
    return dict(n=n,win=wr*100,avg=r.mean()*100,med=np.median(r)*100,
                dd_avg=dda.mean()*100,dd_worst=dda.min()*100,p=p,
                base=base*100,since=str(t0.date()))

def search(df, trig, horizon, min_n):
    keys=list(trig); rows=[]
    for k in keys:
        r=evaluate(df,trig[k],horizon,min_n,{k},None)
        if r: rows.append(({k},None,r))
    for combo in itertools.combinations(keys,2):
        r=evaluate(df,trig[combo[0]]&trig[combo[1]],horizon,min_n,set(combo),None)
        if r: rows.append((set(combo),None,r))
    for combo in itertools.combinations(keys,2):
        for fn,ff in FILTERS.items():
            r=evaluate(df,trig[combo[0]]&trig[combo[1]]&ff(df),horizon,min_n,set(combo),fn)
            if r: rows.append((set(combo),fn,r))
    for k in keys:
        for fn,ff in FILTERS.items():
            r=evaluate(df,trig[k]&ff(df),horizon,min_n,{k},fn)
            if r: rows.append(({k},fn,r))
    return rows

def fmt(rows, horizon, topn=18):
    rows=[x for x in rows if x[2]["p"]<0.05]
    rows.sort(key=lambda x:(-x[2]["win"], x[2]["p"], -x[2]["n"]))
    hn=[k for k,v in HOR.items() if v==horizon][0]
    print(f"\n  （勝率=之後 {hn} 正報酬比例；vs 期間配對基準；p<0.05 顯著；去叢集 gap=21）")
    print(f"  {'組合':<42}{'起算':>11}{'基準':>6}{'n':>4}{'勝率':>7}{'平均':>7}{'續跌':>7}{'p值':>7}")
    print("  "+"-"*92)
    seen=set()
    for cond,filt,r in rows:
        name=" + ".join(sorted(cond))+(f" [{filt}]" if filt else "")
        if name in seen: continue
        seen.add(name)
        print(f"  {name:<42}{r['since']:>11}{r['base']:>5.0f}%{r['n']:>4}{r['win']:>6.0f}%"
              f"{r['avg']:>6.1f}%{r['dd_avg']:>6.1f}%{r['p']:>7.3f}")
        if len(seen)>=topn: break

# ── 統計嚴謹度：Wilson 下界 / BH-FDR 多重比較 / 樣本外 ─────────────────────────
def wilson_lb(k, n, z=1.96):
    if n == 0: return 0.0
    p = k/n; d = 1 + z*z/n
    centre = p + z*z/(2*n)
    margin = z*((p*(1-p)/n + z*z/(4*n*n))**0.5)
    return (centre - margin)/d * 100

def bh_survive(pvals, q=0.05):
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    kmax = -1
    for rank, i in enumerate(order):
        if pvals[i] <= (rank+1)/m*q: kmax = rank
    keep = set(order[r] for r in range(kmax+1)) if kmax >= 0 else set()
    return [i in keep for i in range(m)]

def oos(df, cond, h, split):
    cond = cond.reindex(df.index).fillna(False); c = df["close"].values; idx = df.index
    def wr(mask):
        pos = decluster(mask, 21); r = [c[p+h]/c[p]-1 for p in pos if p+h < len(c)]
        return (len(r), (np.mean(np.array(r) > 0)*100 if r else float("nan")))
    return wr(cond & (idx < split)), wr(cond & (idx >= split))

def robust_report(df, trig, horizon, min_n, split, hn):
    rows = search(df, trig, horizon, min_n)
    if not rows:
        print("  無組合達樣本門檻"); return
    pvals = [r["p"] for _,_,r in rows]
    keep = bh_survive(pvals, 0.05)
    surv = [(c,f,r) for (c,f,r),k in zip(rows,keep) if k]
    surv.sort(key=lambda x:(-x[2]["win"], x[2]["p"]))
    print(f"\n  === 統計嚴謹版（{hn}）：共測 {len(rows)} 組合 → BH-FDR(q<0.05) 存活 {len(surv)} 組 ===")
    print(f"  樣本外切點 {split}（train=之前 / test=之後，test 含近期崩盤）")
    print(f"  {'組合':<40}{'n':>4}{'勝率':>6}{'Wilson下界':>10}{'train':>11}{'test':>11}")
    print("  "+"-"*84)
    seen=set()
    for cond,filt,r in surv[:14]:
        name=" + ".join(sorted(cond))+(f" [{filt}]" if filt else "")
        if name in seen: continue
        seen.add(name)
        # rebuild boolean for OOS
        b=None
        for k in cond: b=trig[k] if b is None else b&trig[k]
        if filt: b=b&FILTERS[filt](df)
        (ntr,wtr),(nte,wte)=oos(df,b,horizon,split)
        wlb=wilson_lb(round(r["win"]/100*r["n"]), r["n"])
        print(f"  {name:<40}{r['n']:>4}{r['win']:>5.0f}%{wlb:>9.0f}%"
              f"{f'{ntr}/{wtr:.0f}%':>11}{f'{nte}/{wte:.0f}%':>11}")
    print("  註：Wilson 下界=保守真實勝率(95%CI下緣)；train/test 都高=非過度配適。")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--market",default="US",choices=["US","TW"])
    ap.add_argument("--horizon",type=int,default=63)
    ap.add_argument("--min-n",type=int,default=12)
    ap.add_argument("--robust",action="store_true",help="輸出 FDR+Wilson+樣本外 嚴謹版")
    a=ap.parse_args()
    if a.market=="US":
        close=load_spx(); df=build_panel(close,load_vix(),load_fng())
        trig=triggers_US(df)
        print(f"== 美股 S&P500 抄底組合回測 ==  區間 {df.index.min().date()}~{df.index.max().date()}"
              f"  ({len(df)} 日)  指標:VIX/FNG/RSI/回檔/200DMA")
    else:
        close=load_taiex(); df=build_panel(close)
        trig=triggers_TW(df)
        print(f"== 台股 TAIEX 抄底組合回測 ==  區間 {df.index.min().date()}~{df.index.max().date()}"
              f"  ({len(df)} 日)  指標:RSI/回檔/距50DMA/波動分位/200DMA")
    hn=[k for k,v in HOR.items() if v==a.horizon][0]
    rows=search(df,trig,a.horizon,a.min_n)
    fmt(rows,a.horizon)
    print("\n  註：勝率為『之後 N 日正報酬』比例；續跌avg=訊號後 12 月內平均最大續跌(買太早的痛)。")
    if a.robust:
        split = "2008-01-01" if a.market=="US" else "2017-01-01"
        robust_report(df,trig,a.horizon,a.min_n,split,hn)

if __name__=="__main__":
    main()
