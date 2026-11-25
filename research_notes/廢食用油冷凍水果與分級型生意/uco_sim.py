# 廢食用油（UCO）新進者單位經濟。事實來源 r4-uco-supply.md、r4-saf-demand.md；(A)=假設
FX = 32.0
print("== 價格（元/公斤）==")
for usd in (795, 1045, 1172, 1190):
    print(f"  亞洲 FOB {usd} 美元/噸 = {usd*FX/1000:.1f} 元/公斤")
print("  收購價：10-15（2026，弱來源）；永瑞機台 18（2023）；35.5-37（約 2022）")

print("\n== 每公斤淨利（元）：FOB 售價 - 收購 - 收運(A) - 處理與損耗(A) - 檢驗認證出口(A) ==")
print("  FOB  收購  收運  處理損耗  檢驗認證出口  淨利")
cases = [
 ("樂觀", 37.5, 12, 4, 2.5, 1.5),
 ("中間", 33.4, 15, 6, 3.0, 2.0),
 ("搶貨", 33.4, 22, 6, 3.0, 2.0),
 ("價跌", 25.4, 15, 6, 3.0, 2.0),
 ("2022重演", 37.5, 36, 6, 3.0, 2.0),
]
res = {}
for name, fob, buy, col, proc, cert in cases:
    net = fob - buy - col - proc - cert
    res[name] = net
    print(f"  {name:8s} {fob:5.1f} {buy:5.1f} {col:4.1f}   {proc:4.1f}       {cert:4.1f}      {net:6.1f}")

print("\n== 新進者年度損益（萬元），另扣固定費用(A) 1,500 萬（人事、認證稽核、廠租、車輛折舊）==")
total = 90000
for share in (0.03, 0.05, 0.10):
    t = total*share
    row = [f"{name}:{(net*t*1000-1.5e7)/1e4:8,.0f}" for name, net in res.items()]
    print(f"  市占 {share:.0%}（{t:,.0f} 噸，營收約 {t*1000*33.4/1e8:.1f} 億元） " + " | ".join(row))

print("\n== 市場規模 ==")
print(f"  收購端年貨值：{total*1000*10/1e8:.0f}-{total*1000*18/1e8:.0f} 億元（9 萬噸 × 10-18 元）")
print(f"  出口端年貨值：{total*1000*31/1e8:.0f}-{total*1000*35/1e8:.0f} 億元")
print(f"  未回收的理論量（永瑞自估 20 萬噸 - 9 萬噸）：11 萬噸；拿到其中 10% = 1.1 萬噸，出口貨值約 {11000*1000*33.4/1e8:.1f} 億元")
print(f"  台灣 2026 年 SAF 國內供給 6,500 噸 → 需 UCO 約 0.8-1.3 萬噸，占回收量 {8000/total:.0%}-{13000/total:.0%}")
print(f"  2030 民航局口徑 SAF 2 萬噸 → 需 UCO 約 2.4-4 萬噸，占回收量 {24000/total:.0%}-{40000/total:.0%}")
