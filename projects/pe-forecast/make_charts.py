#!/usr/bin/env python3
"""README 用的圖：MU 與 MSFT「12 個月前的預測」vs 實際本益比。先跑 pe_forecast.py backtest。"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np               # noqa: E402
import pandas as pd              # noqa: E402
from matplotlib import font_manager  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pef.features import attach_future  # noqa: E402
from pef.load import panel              # noqa: E402

# 顏色：驗證過的分類色前三格（dataviz 參考色盤，light 模式）
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
C_ACT, C_MODEL, C_RW = "#2a78d6", "#eb6834", "#1baf7a"
for f in ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",):
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()


def series(df, pred, t, h=12):
    f = attach_future(df, h)[["ticker", "month", f"ln_pe_f{h}", f"ep_f{h}", "ln_pe"]]
    d = pred[pred["ticker"] == t].merge(f, on=["ticker", "month"])
    d["target"] = d["month"] + pd.DateOffset(months=h)
    d["actual"] = np.exp(d[f"ln_pe_f{h}"])
    d["model"] = np.where(d[f"ni_hat_{h}"] > 0, np.exp(d[f"lnpe_hat_{h}"]), np.nan)
    d["rw"] = np.exp(d["ln_pe"])
    d["loss"] = d[f"ep_f{h}"] <= 0
    return d.dropna(subset=[f"ep_f{h}"]).set_index("target").sort_index()


def main():
    df, _ = panel()
    pred = pd.read_csv(os.path.join(HERE, "results", "predictions.csv.gz"), parse_dates=["month"])
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), facecolor=SURFACE)
    for ax, t, title in zip(axes, ("MU", "MSFT"), ("美光 MU：方向抓得到，轉折的幅度常慢半拍",
                                                  "微軟 MSFT：盈餘平穩，誤差小；2018 尖峰是稅改一次性費用")):
        d = series(df, pred, t)
        ax.set_facecolor(SURFACE)
        # 虧損期間：本益比沒有定義，畫成灰帶
        loss = d["loss"].to_numpy()
        idx = d.index
        i = 0
        while i < len(loss):
            if loss[i]:
                j = i
                while j + 1 < len(loss) and loss[j + 1]:
                    j += 1
                ax.axvspan(idx[i] - pd.Timedelta(days=15), idx[j] + pd.Timedelta(days=15), color=GRID, lw=0, zorder=0)
                ax.text(idx[i] + (idx[j] - idx[i]) / 2, 150, "虧損", ha="center", va="center", color=INK2, fontsize=9)
                i = j + 1
            else:
                i += 1
        cap = lambda s: s.clip(upper=200)
        ax.plot(idx, cap(d["rw"]), color=C_RW, lw=1.6, ls=(0, (4, 3)), label="12 個月前的本益比（隨機漫步）")
        ax.plot(idx, cap(d["model"]), color=C_MODEL, lw=2, label="模型 12 個月前的預測")
        ax.plot(idx, cap(d["actual"]), color=C_ACT, lw=2, label="實際本益比（TTM）")
        ax.set_yscale("log")
        ax.set_ylim(2, 250)
        ax.set_yticks([3, 5, 10, 20, 50, 100, 200])
        ax.set_yticklabels(["3", "5", "10", "20", "50", "100", "≥200"])
        ax.grid(axis="y", color=GRID, lw=0.8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GRID)
        ax.tick_params(colors=INK2, labelsize=9)
        ax.set_title(title, loc="left", color=INK, fontsize=11)
        # 直接標註（線尾）
        last = d.dropna(subset=["actual"]).iloc[-1]
        ax.annotate(f"實際 {last['actual']:.1f}", (d.dropna(subset=['actual']).index[-1], last["actual"]),
                    xytext=(6, 6), textcoords="offset points", color=INK, fontsize=9)
        lm = d.dropna(subset=["model"]).iloc[-1]
        ax.annotate(f"模型 {lm['model']:.1f}", (d.dropna(subset=['model']).index[-1], lm["model"]),
                    xytext=(6, -12), textcoords="offset points", color=INK, fontsize=9)
        e_m = np.nanmedian(np.abs(np.log(d["model"]) - np.log(d["actual"])))
        e_r = np.nanmedian(np.abs(np.log(d["rw"]) - np.log(d["actual"])))
        ax.text(0.01, 0.02, f"中位 ln 誤差：模型 {e_m:.2f}　隨機漫步 {e_r:.2f}", transform=ax.transAxes, color=INK2, fontsize=9)
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h[::-1], lab[::-1], loc="upper center", ncol=3, frameon=False, fontsize=9, labelcolor=INK)
    fig.text(0.01, 0.005, "橫軸＝被預測的月份。資料：SEC XBRL 財報（首次申報值）＋月底股價；每年只用當時已公告的資料重估。",
             color=INK2, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 0.92))
    out = os.path.join(HERE, "results", "mu_msft_12m.png")
    fig.savefig(out, dpi=130, facecolor=SURFACE)
    print(out)


if __name__ == "__main__":
    main()
