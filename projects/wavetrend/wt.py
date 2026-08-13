#!/usr/bin/env python3
"""WaveTrend Oscillator（LazyBear）計算器 — 依 skills/wavetrend/SKILL.md 公式實作。

輸入：JSON 檔，格式 [{"stock":"3081","name":"聯亞","data":[{"d":"2025-08-01","o":..,"h":..,"l":..,"c":..,"v":..}, ...]}, ...]
輸出：每檔的 WT1/WT2 現值、區間、最近交叉訊號、背離檢查

公式（n1=10 通道、n2=21 平均）：
  hlc3 = (h+l+c)/3
  esa  = EMA(hlc3, n1)
  d    = EMA(|hlc3-esa|, n1)
  ci   = (hlc3-esa) / (0.015*d)
  wt1  = EMA(ci, n2)
  wt2  = SMA(wt1, 4)
水位：±60 極度、±53 一般、0 中軸
"""
import json, sys

N1, N2 = 10, 21

def ema(xs, n):
    k = 2.0/(n+1); out=[]; prev=None
    for x in xs:
        prev = x if prev is None else x*k + prev*(1-k)
        out.append(prev)
    return out

def sma(xs, n):
    out=[]
    for i in range(len(xs)):
        w = xs[max(0,i-n+1):i+1]
        out.append(sum(w)/len(w))
    return out

def wavetrend(bars):
    hlc3 = [(b["h"]+b["l"]+b["c"])/3 for b in bars]
    esa  = ema(hlc3, N1)
    dev  = ema([abs(a-b) for a,b in zip(hlc3, esa)], N1)
    ci   = [ (a-b)/(0.015*d) if d else 0.0 for a,b,d in zip(hlc3, esa, dev) ]
    wt1  = ema(ci, N2)
    wt2  = sma(wt1, 4)
    return wt1, wt2

def zone(v):
    if v >= 60: return "極度超買"
    if v >= 53: return "超買"
    if v <= -60: return "極度超賣"
    if v <= -53: return "超賣"
    return "中性"

def analyze(rec):
    bars = rec["data"]
    if len(bars) < 60:
        return {"stock":rec["stock"], "error":f"資料不足({len(bars)}根)"}
    wt1, wt2 = wavetrend(bars)
    n = len(bars)
    cur1, cur2 = wt1[-1], wt2[-1]
    # 最近一次交叉（往回找 60 根）
    cross = None
    for i in range(n-1, max(0, n-61), -1):
        prev_d = wt1[i-1]-wt2[i-1]; cur_d = wt1[i]-wt2[i]
        if prev_d <= 0 < cur_d:
            cross = {"type":"黃金交叉","idx":i,"days_ago":n-1-i,"date":bars[i]["d"],
                     "wt1":round(wt1[i],1),"wt2":round(wt2[i],1),"zone":zone(wt1[i])}; break
        if prev_d >= 0 > cur_d:
            cross = {"type":"死亡交叉","idx":i,"days_ago":n-1-i,"date":bars[i]["d"],
                     "wt1":round(wt1[i],1),"wt2":round(wt2[i],1),"zone":zone(wt1[i])}; break
    # 訊號強度
    strength = "無"
    if cross:
        z = cross["zone"]
        if cross["type"]=="黃金交叉":
            strength = "最強" if z=="極度超賣" else ("強" if z=="超賣" else "中等")
        else:
            strength = "最強" if z=="極度超買" else ("強" if z=="超買" else "中等")
    # 背離檢查（近 40 根 vs 前 40 根的價格/WT1 極值）
    div = "無"
    if n >= 80:
        rec40 = bars[-40:]; prev40 = bars[-80:-40]
        pl_r = min(b["l"] for b in rec40); pl_p = min(b["l"] for b in prev40)
        ph_r = max(b["h"] for b in rec40); ph_p = max(b["h"] for b in prev40)
        w_r_lo = min(wt1[-40:]); w_p_lo = min(wt1[-80:-40])
        w_r_hi = max(wt1[-40:]); w_p_hi = max(wt1[-80:-40])
        if pl_r < pl_p and w_r_lo > w_p_lo: div = "🟢 牛市背離（價創低、WT未創低）"
        elif ph_r > ph_p and w_r_hi < w_p_hi: div = "🔴 熊市背離（價創高、WT未創高）"
    # 價格資訊
    close = bars[-1]["c"]; hi52 = max(b["h"] for b in bars); lo52 = min(b["l"] for b in bars)
    return {"stock":rec["stock"], "name":rec.get("name",""), "last_date":bars[-1]["d"],
            "close":close, "hi":hi52, "lo":lo52, "from_hi_pct":round((close/hi52-1)*100,1),
            "wt1":round(cur1,1), "wt2":round(cur2,1), "zone":zone(cur1),
            "trend":"上行" if cur1>cur2 else "下行",
            "cross":cross, "strength":strength, "divergence":div, "bars":n}

if __name__ == "__main__":
    recs = json.load(open(sys.argv[1], encoding="utf-8"))
    if isinstance(recs, dict): recs=[recs]
    out=[analyze(r) for r in recs]
    print(json.dumps(out, ensure_ascii=False, indent=2))
