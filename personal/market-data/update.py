"""
摸魚記市場數據更新腳本
在你自己的電腦上跑，會把關鍵數字存進 today.json 並提示 commit。

用法：
  python personal/market-data/update.py

需要安裝：pip install requests yfinance
"""
import json
import datetime
import sys

today = datetime.date.today().isoformat()

data = {
    "date": today,
    "note": "由 update.py 產生，在本機跑後 commit 進 repo",
    "tw_market": {
        "taiex_close": None,        # 加權指數收盤
        "taiex_high_ytd": None,     # 今年高點
        "taiex_drawdown_pct": None, # 自高點回檔 %
        "vixtwn": None,             # 台指選擇權波動率指數（VIXTWN）
        "foreign_net_buy_today": None,  # 外資今日買賣超（億，負=賣超）
        "foreign_net_buy_mtd": None,    # 外資本月累計買賣超（億）
        "margin_maintenance_ratio": None,  # 大盤融資維持率 %
        "margin_balance": None,     # 融資餘額（億）
    },
    "sources": {
        "vixtwn": "https://mis.taifex.com.tw/futures/VolatilityQuotes/",
        "margin": "https://www.macromicro.me/charts/53117/taiwan-taiex-maintenance-margin",
        "foreign": "https://www.twse.com.tw/zh/trading/foreign/bfi82u.html",
        "taiex": "https://tw.stock.yahoo.com/quote/%5ETWII",
    }
}

# 嘗試用 yfinance 抓加權指數（本機通常不被擋）
try:
    import yfinance as yf
    twii = yf.Ticker("^TWII")
    hist = twii.history(period="5d")
    if not hist.empty:
        close = round(float(hist["Close"].iloc[-1]), 2)
        data["tw_market"]["taiex_close"] = close
        print(f"TAIEX 收盤：{close}")
except ImportError:
    print("yfinance 未安裝，跳過自動抓取（pip install yfinance）")
except Exception as e:
    print(f"yfinance 抓取失敗：{e}")

# 需要手動填入的數字
print("\n請手動填入以下數字（直接按 Enter 跳過）：")

fields = [
    ("vixtwn", "VIXTWN 目前值（玩股網 https://www.wantgoo.com/index/vixtwn）"),
    ("margin_maintenance_ratio", "大盤融資維持率 %（MacroMicro https://www.macromicro.me/charts/53117）"),
    ("foreign_net_buy_today", "外資今日買賣超 億（負數 = 賣超）"),
    ("foreign_net_buy_mtd", "外資本月累計買賣超 億"),
    ("taiex_high_ytd", "今年高點（算回檔幅度用）"),
]

for key, label in fields:
    val = input(f"  {label}: ").strip()
    if val:
        try:
            data["tw_market"][key] = float(val)
        except ValueError:
            data["tw_market"][key] = val

# 計算回檔幅度
close = data["tw_market"].get("taiex_close")
high = data["tw_market"].get("taiex_high_ytd")
if close and high:
    drawdown = round((close - high) / high * 100, 2)
    data["tw_market"]["taiex_drawdown_pct"] = drawdown
    print(f"\n自高點回檔：{drawdown}%")

# 存檔
out = "personal/market-data/today.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"\n已存至 {out}")
print("接下來：git add personal/market-data/today.json && git commit -m 'data: update market data {}'".format(today))
