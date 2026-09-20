import json, subprocess, time, os, sys
TICKERS = ["GOOGL","MSFT","NVDA","META","AMZN","AAPL","AVGO","AMD","TSM","QQQ","SPY","SMH"]
os.makedirs("px", exist_ok=True)
ok, bad = [], []
for t in TICKERS:
    out = f"px/{t}.csv"
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        ok.append(t); continue
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?range=10y&interval=1d&events=div%2Csplit"
    for attempt in range(4):
        r = subprocess.run(["curl","-s","--max-time","40","-A","Mozilla/5.0",url],
                           capture_output=True, text=True)
        try:
            j = json.loads(r.stdout)
            res = j["chart"]["result"][0]
            ts = res["timestamp"]; q = res["indicators"]["quote"][0]
            adj = res["indicators"].get("adjclose",[{}])[0].get("adjclose", q["close"])
            rows = ["date,open,high,low,close,adjclose,volume"]
            for i,s in enumerate(ts):
                d = time.strftime("%Y-%m-%d", time.gmtime(s))
                c, a, v = q["close"][i], adj[i], q["volume"][i]
                o, h, l = q["open"][i], q["high"][i], q["low"][i]
                if c is None or a is None: continue
                rows.append(f"{d},{o},{h},{l},{c},{a},{v}")
            open(out,"w").write("\n".join(rows))
            ok.append(t); break
        except Exception as e:
            if attempt == 3: bad.append((t, str(e)[:60]))
            time.sleep(2*(attempt+1))
print("成功:", " ".join(ok))
if bad: print("失敗:", bad)
for t in ok:
    lines = open(f"px/{t}.csv").read().strip().split("\n")
    print(f"  {t:6s} n={len(lines)-1:5d}  {lines[1].split(',')[0]} ~ {lines[-1].split(',')[0]}  最後收盤 {lines[-1].split(',')[4]}")
