"""三種典型科技公司，套各家本益比理論會得到什麼（示意，不是預測任何股票）。

    python3 research/tech_archetypes.py

r＝10 年期 4.6% ＋ 股權風險溢酬 5%＝9.6%。forward P/E＝今天股價 ÷ 下一年 EPS。
"""
import numpy as np
from scipy.optimize import brentq

R = 0.096
ARCH = {  # 名稱：forward P/E、下一年→再下一年 EPS 成長 g2、ROE、派發率
    "A 穩定巨頭（MSFT/AAPL 型）": dict(pe=30, g2=0.12, roe=0.35, payout=0.30),
    "B 高成長（NVDA 型）":       dict(pe=35, g2=0.35, roe=0.50, payout=0.02),
    "C 週期（MU 型，景氣高點）":  dict(pe=10, g2=-0.20, roe=0.30, payout=0.05),
}


def gordon_pe(g, roe, r=R):                      # forward P/E＝(1 − g/ROE)/(r − g)
    return (1 - g / roe) / (r - g)


def gordon_implied_g(pe, roe, r=R):
    return brentq(lambda g: gordon_pe(g, roe, r) - pe, -0.5, r - 1e-6)


def oj_pe(g2, lt, payout, r=R):                  # Ohlson-Juettner-Nauroth：lt＝γ−1（異常盈餘成長的長期成長率）
    return (g2 - lt + r * payout) / (r * (r - lt))


def oj_implied_lt(pe, g2, payout, r=R):
    return brentq(lambda x: oj_pe(g2, x, payout, r) - pe, -0.9, r - 1e-6)


def two_stage(gh, n, roe, gn=0.04, roe_n=0.20, r=R, horizon=400):
    """兩階段：前 n 年 EPS 以 gh 成長、派發 1 − gh/ROE（成長靠再投資）；之後 gn、派發 1 − gn/ROE_n。
    回傳第 0–5 年初的 forward P/E（市場預期不變時的軌道，Leibowitz 1999）。"""
    payout_h = max(0.0, 1 - gh / roe)
    T = n + horizon
    g = np.where(np.arange(T) < n, gh, gn)
    eps = np.cumprod(np.r_[1.0, 1 + g[:-1]])                 # EPS_1 … EPS_T
    pay = np.where(np.arange(T) < n, payout_h, 1 - gn / roe_n)
    div = pay * eps
    disc = (1 + R) ** -np.arange(1, T + 1)
    price = np.array([np.sum(div[k:] * disc[: T - k]) for k in range(6)])   # 第 k 年初的價格
    return price / eps[:6]                                     # forward P/E 軌道


def implied_n(pe, gh, roe):
    """高成長要維持幾年，今天的 forward P/E 才說得通（取最接近的整數年）。"""
    pes = [two_stage(gh, n, roe)[0] for n in range(0, 41)]
    n = int(np.argmin([abs(x - pe) for x in pes]))
    return n if abs(pes[n] - pe) / pe < 0.15 else None


for name, a in ARCH.items():
    print(f"\n== {name}：forward P/E {a['pe']}、下一年 EPS 成長 {a['g2']:+.0%}、ROE {a['roe']:.0%}")
    no_growth = 1 / R
    print(f"  MM／Leibowitz：不成長的本益比 1/r＝{no_growth:.1f}；股價裡「成長機會」占 {1 - no_growth / a['pe']:.0%}")
    try:
        g = gordon_implied_g(a["pe"], a["roe"])
        up, dn = gordon_pe(g, a["roe"], R - 0.01), gordon_pe(g, a["roe"], R + 0.01)
        print(f"  Gordon：隱含永續成長 {g:.1%}；r 少 1 個百分點 → 本益比 {up:.0f}（{up / a['pe'] - 1:+.0%}），"
              f"多 1 個百分點 → {dn:.0f}（{dn / a['pe'] - 1:+.0%}）")
    except ValueError:
        print("  Gordon：解不出合理的永續成長（本益比低於 1/r 又要正成長）")
    try:
        lt = oj_implied_lt(a["pe"], a["g2"], a["payout"])
        print(f"  OJ（用下一年、再下一年 EPS）：隱含長期異常盈餘成長 {lt:+.1%}")
    except ValueError:
        print("  OJ：解不出來（再下一年 EPS 下滑時，模型的「異常盈餘成長」一開始就是負的，參數化不適用）")
    if a["g2"] > 0:
        gh = a["g2"]
        n = implied_n(a["pe"], gh, a["roe"])
        if n is not None:
            orbit = two_stage(gh, n, a["roe"])
            print(f"  兩階段（{gh:.0%} 成長後降到 4%）：隱含高成長 {n} 年；預期不變時 forward P/E 軌道 "
                  + " → ".join(f"{x:.1f}" for x in orbit[:4]))
    else:
        norm = a["pe"] * (1 + a["g2"])
        print(f"  Molodovsky／Penman：若下一年 EPS 是景氣高點、再下一年回落 {a['g2']:.0%}，"
              f"用再下一年 EPS 算的本益比是 {a['pe'] / (1 + a['g2']):.1f}（低本益比是暫時性高盈餘造成的）")
