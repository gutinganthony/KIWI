"""
摸魚記 W8 回測：泡沫裡三種策略的下場（Nasdaq Composite 1998–2005）
======================================================================
策略：
  A. 1998 年底離場、持現金（T-bill 近似，年化利率參數化）
  B. 抱到底 Buy & Hold（1998/12/31 進場）
  C. 趨勢擇時：收盤 > N 日均線→持股，跌破→轉現金（賺 T-bill）
     - 日資料用 200 日均線（SMA200，經典版）
     - 月資料自動改用 10 個月均線（≈200 日，Faber/GTAA 標準代理）

資料來源（擇一，環境無法直接抓，需 Jake 下載上傳）：
  · stooq：https://stooq.com/q/d/?s=^ndq  → 下載 CSV（Date,Open,High,Low,Close,Volume）
  · 或任何含 Date + Close 欄的 Nasdaq Composite 日/月 CSV（1997-06 ~ 2006-01）
用法：python gen_W8_backtest.py <path_to_csv>

紅線：本檔不內嵌任何價格數字。無 CSV 不會產出「假」淨值。
"""
import sys, os, csv
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ── 參數 ──
START = "1998-12-31"          # 策略起算日（$100 投入）
END   = "2005-12-31"          # 觀察終點
TBILL_ANNUAL = 0.035          # 現金部位年化（T-bill 近似；1999-2000約5%、2001後大降，取保守中值。可調）
MA_DAYS = 200                 # 日資料用 200 日
MA_MONTHS = 10                # 月資料用 10 個月

SANS = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SERIF_B = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
for p in (SANS, SERIF_B):
    if os.path.exists(p):
        fm.fontManager.addfont(p)
sans = fm.FontProperties(fname=SANS)
serif_b = fm.FontProperties(fname=SERIF_B)
matplotlib.rcParams['font.family'] = sans.get_name()
matplotlib.rcParams['axes.unicode_minus'] = False

BG="#ffffff"; INK="#1a1a1a"; GREY="#6b6b6b"; LGRID="#d9d9d9"
GOLD="#b8954a"; RED="#b23b32"; GREEN="#2e7d4f"; SLATE="#4a5d7a"


def load_csv(path):
    """自動偵測 Date/Close 欄，回傳 [(date, close)] 升冪。相容 stooq / Yahoo。"""
    rows = []
    with open(path, newline='') as f:
        rdr = csv.DictReader(f)
        cols = {c.lower().strip(): c for c in rdr.fieldnames}
        dcol = cols.get('date')
        ccol = cols.get('close') or cols.get('adj close') or cols.get('zamkniecie')
        if not dcol or not ccol:
            sys.exit(f"CSV 需含 Date 與 Close 欄，實際欄位：{rdr.fieldnames}")
        for r in rdr:
            ds, cs = r[dcol].strip(), r[ccol].strip()
            if not ds or not cs:
                continue
            d = None
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
                try:
                    d = datetime.strptime(ds, fmt); break
                except ValueError:
                    continue
            if d is None:
                continue
            try:
                c = float(cs.replace(',', ''))
            except ValueError:
                continue
            rows.append((d, c))
    rows.sort(key=lambda x: x[0])
    return rows


def daily_rate(annual, n_periods_per_year):
    return (1 + annual) ** (1.0 / n_periods_per_year) - 1


def run(path):
    data = load_csv(path)
    start_dt = datetime.strptime(START, "%Y-%m-%d")
    end_dt = datetime.strptime(END, "%Y-%m-%d")
    data = [(d, c) for d, c in data if d <= end_dt]
    if not data:
        sys.exit("CSV 範圍不含觀察期間")

    # 判定日或月頻率
    gaps = [(data[i][0]-data[i-1][0]).days for i in range(1, min(len(data), 30))]
    is_monthly = (sum(gaps)/len(gaps)) > 20 if gaps else False
    ma_win = MA_MONTHS if is_monthly else MA_DAYS
    periods_per_year = 12 if is_monthly else 252
    rf = daily_rate(TBILL_ANNUAL, periods_per_year)
    freq = "月" if is_monthly else "日"

    # 對齊起點：找 >= START 的第一根
    idx0 = next((i for i, (d, _) in enumerate(data) if d >= start_dt), None)
    if idx0 is None:
        sys.exit("CSV 不含起算日之後的資料")
    base_close = data[idx0][1]

    dates, navA, navB, navC = [], [], [], []
    trades = []            # 策略C 換手紀錄
    a = 1.0; c_val = 1.0; c_in_market = True
    prev_state = True
    for i in range(idx0, len(data)):
        d, close = data[i]
        # B：買入持有
        b = close / base_close
        # A：全期持現金
        a *= (1 + rf)
        # C：以「前一根收盤 vs 前一根的 MA」決定本根持有狀態（避免用當根未來資訊）
        if i >= ma_win:
            ma_prev = sum(x[1] for x in data[i-ma_win:i]) / ma_win
            state = data[i-1][1] > ma_prev
        else:
            state = True
        if state != prev_state:
            trades.append((d, close, "進場" if state else "出場"))
        if state:
            c_val *= (close / data[i-1][1]) if i > idx0 else 1.0
        else:
            c_val *= (1 + rf)
        prev_state = state
        dates.append(d); navA.append(a*100); navB.append(b*100); navC.append(c_val*100)

    # ── 主控台輸出 ──
    def at(target):
        best = min(range(len(dates)), key=lambda i: abs((dates[i]-datetime.strptime(target,"%Y-%m-%d")).days))
        return dates[best], navA[best], navB[best], navC[best]
    print(f"\n=== W8 回測（{freq}頻、MA{ma_win}、T-bill {TBILL_ANNUAL:.1%}）===")
    print(f"資料 {data[0][0].date()} ~ {data[-1][0].date()}，共 {len(data)} 根\n")
    print(f"{'時點':<12}{'A現金':>10}{'B抱到底':>10}{'C趨勢':>10}")
    for t in ("1999-12-31","2000-03-10","2000-12-31","2002-10-09","2002-12-31","2005-12-31"):
        dd,aa,bb,cc = at(t)
        print(f"{t:<12}{aa:>10.1f}{bb:>10.1f}{cc:>10.1f}")
    print(f"\n策略C 換手（前 20 筆）：")
    for d,px,act in trades[:20]:
        print(f"  {d.date()}  {act}  Nasdaq={px:.1f}")
    print(f"  ……共 {len(trades)} 次換手")
    # B 的極端
    lo_i = min(range(len(navB)), key=lambda i: navB[i])
    print(f"\nB 最低點：{dates[lo_i].date()} → ${navB[lo_i]:.1f}")

    # ── 圖 1：三策略淨值曲線 ──
    fig, ax = plt.subplots(figsize=(13, 7.2), facecolor=BG)
    ax.set_facecolor(BG)
    fig.text(0.052, 0.935, "■", color=GOLD, fontsize=13)
    fig.text(0.075, 0.928, "泡沫裡的三種人：1999 進場後的七年", color=INK,
             fontsize=18.5, fontproperties=serif_b)
    fig.lines.append(plt.Line2D([0.052,0.965],[0.895,0.895], transform=fig.transFigure, color=INK, lw=0.8))

    ax.plot(dates, navB, color=RED, lw=2.0, label="抱到底")
    ax.plot(dates, navC, color=GREEN, lw=2.0, label=f"趨勢擇時（{ma_win}{freq}均線）")
    ax.plot(dates, navA, color=SLATE, lw=1.6, ls=(0,(4,2)), label="1998 年底離場持現金")
    ax.axhline(100, color=GREY, lw=0.8, ls=':')

    for t, lab in (("2000-03-10","頂點 5,048"),):
        dd = at(t)[0]
        ax.axvline(dd, color=INK, lw=0.9, ls=(0,(4,3)))
        ax.text(dd, ax.get_ylim()[1], "  "+lab, color=INK, fontsize=9, va='top')

    ax.set_ylabel("淨值（1998/12/31 = 100）", color=GREY, fontsize=10)
    ax.tick_params(colors=GREY)
    ax.yaxis.grid(True, color=LGRID, lw=0.7); ax.set_axisbelow(True)
    for s in ('top','right'): ax.spines[s].set_visible(False)
    for s in ('left','bottom'): ax.spines[s].set_color(GREY)
    leg = ax.legend(loc='upper right', frameon=False, fontsize=10.5)
    for txt in leg.get_texts(): txt.set_color(INK)

    fig.text(0.052, 0.045,
             f"資料來源：Nasdaq Composite（{freq}收盤，{data[0][0].year}–{data[-1][0].year}），摸魚記回測。"
             f"策略C＝收盤跌破 {ma_win}{freq}均線轉現金；現金以年化 {TBILL_ANNUAL:.1%} 近似 T-bill。價格指數不含股息稅費。\n"
             "過往表現並非未來業績的可靠指標。",
             color=GREY, fontsize=7.8, linespacing=1.7, va='top')

    out = '/home/user/KIWI/personal/drafts/W8-chart-strategies.png'
    plt.subplots_adjust(top=0.87, bottom=0.13, left=0.075, right=0.965)
    plt.savefig(out, dpi=170, facecolor=BG); plt.close()
    print(f"\nDone -> {out}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：python gen_W8_backtest.py <nasdaq_csv>")
        print("需要一份含 Date + Close 欄的 Nasdaq Composite 日或月 CSV（1997-06~2006-01）")
        print("下載：https://stooq.com/q/d/?s=^ndq （或 Yahoo ^IXIC 歷史資料匯出）")
        sys.exit(1)
    run(sys.argv[1])
