#!/usr/bin/env python3
"""xyz 贏家掃描的離線測試——不打網路，注入 fake post/get/ws。

驗收重點
  1. 只算 xyz 的成交（原生成交不能混進 xyz 績效）
  2. 「高勝率但賣尾部」必須被擋（追蹤錢包在 xyz 的真實型態：勝率 58%、pf 0.64）
  3. 樣本截斷／強平／一次好運 → 不得判 winner
  4. WS 解析容錯（缺 users、非 xyz 幣、畸形訊息）
  5. WS 失敗 → 退回排行榜母體，不空手而回
  6. L2 門檻與上限確實生效
  7. 報告在任何欄位為 None 時都不 crash
"""

import sys
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
XYZ_DIR = HERE.parent
sys.path.insert(0, str(XYZ_DIR))
sys.path.insert(0, str(XYZ_DIR.parent))

import find_xyz_winners as fx   # noqa: E402
import xyz_config as xcfg       # noqa: E402

CHECKS = 0
FAILURES = []
# parse_fills 把時間正規化成 epoch 秒，測試也一律用秒
DAY = 86_400
NOW = time.time()


def check(cond, msg):
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"  ok: {msg}")
    else:
        FAILURES.append(msg)
        print(f"  FAIL: {msg}")


def fills(specs, coin="xyz:META", start_days_ago=40):
    """specs: [(closed_pnl, n)] → 攤平成成交清單，時間平均分布在 start_days_ago 內。"""
    out, i = [], 0
    total = sum(n for _, n in specs)
    for pnl, n in specs:
        for _ in range(n):
            out.append({"coin": coin, "closed_pnl": float(pnl),
                        "ts": NOW - int(start_days_ago * DAY * (total - i) / max(total, 1)),
                        "is_liquidation": False, "px": 1.0, "sz": 1.0,
                        "side": "B", "fee": 0.0, "dir": "Close Long"})
            i += 1
    return out


def main():
    print("[1] dex_fill_stats 只算 xyz")
    mixed = fills([(100, 10)], coin="xyz:META") + fills([(1000, 10)], coin="BTC")
    s = fx.dex_fill_stats(mixed, "xyz", now_sec=NOW)
    check(s["n_fills_dex"] == 10, f"只數 xyz 的 10 筆（實得 {s['n_fills_dex']}）")
    check(s["n_fills_total"] == 20, "總筆數仍記 20")
    check(abs(s["net_closed_pnl"] - 1000) < 1e-6,
          f"淨損益只算 xyz 的 $1000（實得 {s['net_closed_pnl']}）")
    check(abs(s["dex_share_of_fills"] - 0.5) < 1e-9, "xyz 占比 50%")
    check(fx.is_dex_coin("xyz:META", "xyz") and not fx.is_dex_coin("BTC", "xyz"),
          "is_dex_coin 只認前綴")

    print("[2] 高勝率但賣尾部 → 必須擋掉（追蹤錢包在 xyz 的真實型態）")
    tail = fills([(188, 35), (-410, 25)])          # 勝率 58.3%、pf 0.64
    s = fx.dex_fill_stats(tail, "xyz", now_sec=NOW)
    check(abs(s["win_rate"] - 35/60) < 1e-9, f"勝率 58.3%（實得 {s['win_rate']:.3f}）")
    check(s["profit_factor"] < 1.0, f"獲利因子 <1（實得 {s['profit_factor']:.2f}）")
    v, reasons = fx.judge(s)
    check(v == "reject", f"判定 reject（實得 {v}）")
    check(any("獲利因子" in r for r in reasons), "理由列出獲利因子不過")
    check(any("平均虧損" in r for r in reasons), "理由列出虧／賺比值不過")

    print("[3] 真 winner")
    good = fills([(500, 40), (-150, 20)])          # 勝率 66.7%、pf 6.7
    s = fx.dex_fill_stats(good, "xyz", now_sec=NOW)
    v, reasons = fx.judge(s)
    check(v == "winner", f"判定 winner（實得 {v}，reasons={reasons}）")
    check(s["profit_factor"] > 1.3 and s["win_rate"] > 0.55, "同時滿足獲利因子與勝率")

    print("[4] 硬性缺陷不得判 winner")
    s = fx.dex_fill_stats(good, "xyz", now_sec=NOW)
    s["n_liquidations"] = xcfg.MAX_LIQUIDATIONS
    v, _ = fx.judge(s)
    check(v == "reject", f"強平達上限 → reject（實得 {v}）")
    s = fx.dex_fill_stats(good, "xyz", now_sec=NOW)
    s["sample_truncated"] = True
    v, reasons = fx.judge(s)
    check(v == "reject" and any("上限" in r for r in reasons),
          f"樣本截斷 → reject（實得 {v}）")
    onehit = fills([(10000, 1), (100, 39), (-50, 20)])
    s = fx.dex_fill_stats(onehit, "xyz", now_sec=NOW)
    check(s["top_trade_share_of_profit"] > 0.5,
          f"單筆占毛利 >50%（實得 {s['top_trade_share_of_profit']:.2f}）")
    v, _ = fx.judge(s)
    check(v == "reject", f"一次好運 → reject（實得 {v}）")

    print("[5] 樣本不足與停手")
    s = fx.dex_fill_stats(fills([(100, 5)]), "xyz", now_sec=NOW)
    v, reasons = fx.judge(s)
    check(v == "insufficient_data", f"5 筆 → insufficient_data（實得 {v}）")
    check(len(reasons) == 1 and "樣本不足" in reasons[0], "只回一條「樣本不足」")
    idle = fills([(500, 40), (-150, 20)], start_days_ago=90)
    idle = [dict(f, ts=f["ts"] - 30 * DAY) for f in idle]
    s = fx.dex_fill_stats(idle, "xyz", now_sec=NOW)
    v, reasons = fx.judge(s)
    check(any("停手" in r for r in reasons), f"停手被抓到（reasons={reasons}）")

    print("[6] near_miss 分級")
    soso = fills([(300, 33), (-100, 27)])   # 勝率 55%、賠率 3.0、pf 3.67
    s = fx.dex_fill_stats(soso, "xyz", now_sec=NOW)
    s["net_closed_pnl"] = 100.0             # 只有損益一項不過
    v, reasons = fx.judge(s)
    check(v == "near_miss" and len(reasons) == 1,
          f"僅一項不過且非硬性 → near_miss（實得 {v}, {reasons}）")

    print("[7] 除以零／None 防護")
    s = fx.dex_fill_stats([], "xyz", now_sec=NOW)
    check(s["profit_factor"] is None and s["win_rate"] is None, "空清單 → None，不臆造")
    check(s["span_days"] == 0.0 and s["days_since_last_fill"] is None, "空清單的跨度為 0")
    allwin = fills([(100, 40)])
    s = fx.dex_fill_stats(allwin, "xyz", now_sec=NOW)
    check(s["profit_factor"] == 999.0, f"零虧損 → pf 哨兵值 999（實得 {s['profit_factor']}）")
    check(s["loss_to_win_ratio"] is None, "零虧損 → 虧／賺比值 None（不除以零）")

    print("[8] WS 解析容錯")
    ok_msg = {"channel": "trades", "data": [
        {"coin": "xyz:META", "users": ["0x" + "a" * 40, "0x" + "b" * 40]},
        {"coin": "BTC", "users": ["0x" + "c" * 40]},
        {"coin": "xyz:META"},
        {"coin": "xyz:META", "users": "0x" + "d" * 40},
        {"coin": "xyz:META", "users": ["short", None, 123]},
    ]}
    found = fx.parse_trade_users(ok_msg, "xyz")
    check(found == {"0x" + "a" * 40, "0x" + "b" * 40, "0x" + "d" * 40},
          f"只收 xyz 的合法地址（實得 {len(found)} 個）")
    for bad in (None, [], "str", {"channel": "l2Book", "data": []},
                {"channel": "trades", "data": "x"}, {"channel": "trades"}):
        check(fx.parse_trade_users(bad, "xyz") == set(), f"畸形訊息不 crash：{bad!r}")

    print("[9] WS 失敗 → 退回排行榜母體")
    lb_addrs = ["0x" + f"{i:040x}" for i in range(1, 51)]
    calls = {"chs": 0, "fills": 0}

    def post_fn(body, name, meta):
        t = body.get("type")
        if t == "meta":
            return {"universe": [{"name": "META"}, {"name": "xyz:GOLD"}]}, True
        if t == "clearinghouseState":
            calls["chs"] += 1
            idx = int(body["user"][-4:], 16)
            av = 100_000.0 if idx % 2 == 0 else 1_000.0   # 一半過門檻
            return {"marginSummary": {"accountValue": str(av)},
                    "assetPositions": [{"position": {
                        "coin": "xyz:META", "szi": "1", "entryPx": "1",
                        "positionValue": "1000", "unrealizedPnl": "0",
                        "leverage": {"value": "5", "type": "isolated"},
                        "liquidationPx": None, "marginUsed": "1", "maxLeverage": "20",
                        "cumFunding": {"allTime": "0"}}}]}, True
        if t == "userFillsByTime":
            calls["fills"] += 1
            check_start.append(body.get("startTime"))
            return [{"coin": "xyz:META", "closedPnl": "500", "time": int((NOW - 3 * DAY) * 1000),
                     "px": "1", "sz": "1", "side": "B", "fee": "0", "dir": "Close Long"}
                    for _ in range(40)] + \
                   [{"coin": "xyz:META", "closedPnl": "-150", "time": int((NOW - 40 * DAY) * 1000),
                     "px": "1", "sz": "1", "side": "A", "fee": "0", "dir": "Close Long"}
                    for _ in range(20)], True
        return None, False

    check_start = []

    def get_fn(url, name, meta):
        return {"leaderboardRows": [{"ethAddress": a} for a in lb_addrs]}, True

    def ws_factory(url):
        raise OSError("connection refused (test)")

    args = types.SimpleNamespace(ws_seconds=1, out_json="", out_md="")
    result = fx.run(args, post_fn=post_fn, get_fn=get_fn, ws_factory=ws_factory)
    check("排行榜備援" in result["l1_method"], f"L1 方法標明備援（實得 {result['l1_method']}）")
    check(result["l1_addresses"] == 50, f"母體 50 個（實得 {result['l1_addresses']}）")
    check(result["l2_survivors"] == 25,
          f"L2 只留過門檻的 25 個（實得 {result['l2_survivors']}）")
    check(calls["fills"] == 25, f"L3 只對倖存者打 userFills（實得 {calls['fills']} 次）")
    check(result["n_winners"] == 25, f"全部判 winner（實得 {result['n_winners']}）")
    check(any("WS 連線失敗" in n for n in result["notes"]), "備註記錄 WS 失敗原因")

    print("[10] WS 成功路徑")

    class FakeWS:
        def __init__(self):
            self.sent = []
            self._msgs = [
                '{"channel":"subscriptionResponse"}',
                '{"channel":"trades","data":[{"coin":"xyz:META","users":'
                '["0x' + "1" * 40 + '","0x' + "2" * 40 + '"]}]}',
                'not json',
                '{"channel":"trades","data":[{"coin":"xyz:GOLD","users":'
                '["0x' + "3" * 40 + '"]}]}',
            ]

        def send(self, s):
            self.sent.append(s)

        def recv(self):
            if self._msgs:
                return self._msgs.pop(0)
            raise OSError("closed")

        def close(self):
            pass

    fake = FakeWS()
    seen, n_trades = fx.collect_via_websocket(["xyz:META", "xyz:GOLD"], 5,
                                              fx.fetch.Meta(), ws_factory=lambda u: fake)
    check(len(seen) == 3, f"收到 3 個地址（實得 {len(seen)}）")
    check(seen["0x" + "1" * 40] == 1 and seen["0x" + "3" * 40] == 1,
          "每個地址都記到窗內成交次數")
    check(n_trades == 2, f"數到 2 筆 xyz 成交（實得 {n_trades}）")
    check(len(fake.sent) == 2 and all("subscribe" in s for s in fake.sent),
          "對每個合約各送一次 subscribe")
    check(all('"trades"' in s for s in fake.sent), "只訂閱 trades 頻道（唯讀）")

    print("[11] dex_coins 前綴補齊與容錯")
    meta = fx.fetch.Meta()
    coins = fx.dex_coins("xyz", meta, post_fn=post_fn)
    check(coins == ["xyz:META", "xyz:GOLD"], f"無前綴的補上 dex:（實得 {coins}）")
    coins = fx.dex_coins("xyz", meta, post_fn=lambda *a, **k: (None, False))
    check(coins == [], "meta 查詢失敗 → 回空清單不 crash")
    coins = fx.dex_coins("xyz", meta, post_fn=lambda *a, **k: ({"universe": "bad"}, True))
    check(coins == [], "universe 型別錯 → 回空清單")

    print("[12] 報告渲染（含 None 欄位）")
    md = fx.render_report(result)
    check("# xyz builder dex 贏家掃描" in md, "報告有標題")
    check("| L1 母體 |" in md and "| L3 驗證 |" in md, "報告有漏斗表")
    check("判準" in md and "賠率" in md and "避免大虧" in md,
          "報告載明判準（含賠率主關卡與避免大虧）")
    empty = {"dex": "xyz", "generated_at": "2026-07-30T00:00:00+00:00",
             "l1_method": "none", "l1_addresses": 0, "l2_survivors": 0,
             "n_winners": 0, "n_near_miss": 0, "notes": [],
             "wallets": [{"address": "0xdead", "account_value": None, "n_positions": 0,
                          "position_value": None, "verdict": "winner", "reasons": [],
                          "stats": fx.dex_fill_stats([], "xyz", now_sec=NOW)}]}
    md2 = fx.render_report(empty)
    check("?" in md2 and "0xdead" in md2, "全 None 的錢包也能渲染（印 ? 不 crash）")

    print("[13] 唯讀保證")
    src = (XYZ_DIR / "find_xyz_winners.py").read_text(encoding="utf-8")
    for bad in ("place_order", "private_key", "eth_account", "sign(", "/exchange"):
        check(bad not in src, f"不含 {bad}")
    check('"method": "subscribe"' in src, "WS 只做 subscribe")
    for t in ('"type": "meta"', '"type": "clearinghouseState"',
              '"type": "userFillsByTime"'):
        check(t in src, f"使用唯讀查詢 {t}")

    print("[15] userFillsByTime 分頁（第一版用 userFills 只看得到最近 2000 筆）")
    pages = []

    def paging_post(n_pages_full, rows_last=5):
        """回一個 post_fn：前 n_pages_full 頁滿頁，最後一頁只回 rows_last 筆。"""
        state = {"page": 0}

        def fn(body, name, meta):
            if body.get("type") != "userFillsByTime":
                return None, False
            pages.append(body.get("startTime"))
            i = state["page"]
            state["page"] += 1
            n = 2000 if i < n_pages_full else rows_last
            base = int((NOW - 30 * DAY + i * DAY) * 1000)
            return [{"coin": "xyz:META", "closedPnl": "1", "time": base + j,
                     "px": "1", "sz": "1", "side": "B", "fee": "0", "dir": "Close Long"}
                    for j in range(n)], True
        return fn

    pages.clear()
    raw, hit_cap = fx.fetch_fills_window("0xabc", fx.fetch.Meta(),
                                         post_fn=paging_post(2), days=30)
    check(len(raw) == 4005, f"三頁合計 4005 筆（實得 {len(raw)}）")
    check(hit_cap is False, "未滿頁即停 → 不算觸及分頁上限")
    check(len(pages) == 3, f"共 3 次請求（實得 {len(pages)}）")
    check(pages == sorted(pages) and len(set(pages)) == 3,
          f"startTime 每頁嚴格前進，不重複計入（實得 {pages}）")

    pages.clear()
    raw, hit_cap = fx.fetch_fills_window("0xabc", fx.fetch.Meta(),
                                         post_fn=paging_post(99), days=30)
    check(hit_cap is True, "每頁都滿 → 觸及分頁上限（判為做市／高頻型）")
    check(len(pages) == xcfg.FILL_PAGE_CAP,
          f"請求數受 FILL_PAGE_CAP 限制（實得 {len(pages)}）")
    s_trunc = fx.dex_fill_stats(fx.classify.parse_fills(raw), "xyz",
                                now_sec=NOW, truncated=hit_cap)
    check(s_trunc["sample_truncated"] is True, "truncated 由呼叫端傳入而非猜總筆數")
    v, reasons = fx.judge(s_trunc)
    check(v == "reject" and any("分頁上限" in r for r in reasons),
          f"觸頂 → 硬性淘汰（實得 {v}）")

    pages.clear()
    raw, hit_cap = fx.fetch_fills_window("0xabc", fx.fetch.Meta(),
                                         post_fn=lambda *a, **k: (None, False))
    check(raw == [] and hit_cap is False, "首頁失敗 → 回空清單不 crash")
    raw, _ = fx.fetch_fills_window("0xabc", fx.fetch.Meta(),
                                   post_fn=lambda *a, **k: ([], True))
    check(raw == [], "空頁 → 立即停止")

    print("[16] L1 依窗內成交次數排序：低頻優先（避開做市型帳戶）")
    hi, lo = "0x" + "1" * 40, "0x" + "9" * 40
    order_seen = []

    def order_post(body, name, meta):
        t = body.get("type")
        if t == "meta":
            return {"universe": [{"name": "META"}]}, True
        if t == "clearinghouseState":
            order_seen.append(body["user"])
            return {"marginSummary": {"accountValue": "1"}, "assetPositions": []}, True
        return None, False

    class ManyTrades:
        """hi 出現 5 次、lo 只出現 1 次。"""
        def __init__(self):
            self._msgs = ['{"channel":"trades","data":[{"coin":"xyz:META","users":["'
                          + hi + '"]}]}'] * 5 + \
                         ['{"channel":"trades","data":[{"coin":"xyz:META","users":["'
                          + lo + '"]}]}']

        def send(self, s):
            pass

        def recv(self):
            if self._msgs:
                return self._msgs.pop(0)
            raise OSError("closed")

        def close(self):
            pass

    args2 = types.SimpleNamespace(ws_seconds=1, out_json="", out_md="")
    res2 = fx.run(args2, post_fn=order_post, get_fn=lambda *a, **k: (None, False),
                  ws_factory=lambda u: ManyTrades())
    check(order_seen[:2] == [lo, hi],
          f"低頻地址先送進 L2（實得 {[a[:6] for a in order_seen[:2]]}）")
    check(any("窗內成交次數分布" in n for n in res2["notes"]),
          "備註揭露頻率分布（讓取樣偏誤看得見）")

    print("[17] 硬性判定不靠字串比對（迴歸：改文案曾讓截斷錢包降級成 near_miss）")
    src_judge = (XYZ_DIR / "find_xyz_winners.py").read_text(encoding="utf-8")
    check("is_hard=True" in src_judge, "硬性缺陷用明確 flag 標記")
    check('"偏誤" in r' not in src_judge, "不再用 reason 文字判硬性")

    print("[18] 賠率主關卡（大賺小虧）與勝率降級")
    # 0x6691da5f 的真實型態：勝率 46.2%、平均賺 $66／平均虧 $18（賠率 3.67）
    low_wr_high_payoff = fills([(66, 46), (-18, 54)])
    s = fx.dex_fill_stats(low_wr_high_payoff, "xyz", now_sec=NOW)
    s["unrealized_pnl"] = 0.0
    s["net_closed_pnl"] = 53_000.0
    check(round(s["win_to_loss_ratio"], 2) == 3.67,
          f"賠率 3.67（實得 {s['win_to_loss_ratio']:.2f}）")
    v, reasons = fx.judge(s)
    check(v == "winner",
          f"低勝率但高賠率 → winner（舊判準會擋掉；實得 {v}, {reasons}）")

    # 反例：勝率高但賠率不足（0x3acd3c8a：勝率 53.4%、$115/$85＝賠率 1.35）
    high_wr_low_payoff = fills([(115, 53), (-85, 47)])
    s = fx.dex_fill_stats(high_wr_low_payoff, "xyz", now_sec=NOW)
    s["unrealized_pnl"] = 0.0
    s["net_closed_pnl"] = 24_000.0
    v, reasons = fx.judge(s)
    check(any("賠率" in r for r in reasons), f"賠率不足被點名（reasons={reasons}）")

    # 勝率 30%（低於樂透型下限）→ 仍要被擋
    lottery = fills([(500, 30), (-50, 70)])
    s = fx.dex_fill_stats(lottery, "xyz", now_sec=NOW)
    s["unrealized_pnl"] = 0.0
    s["net_closed_pnl"] = 11_500.0
    v, reasons = fx.judge(s)
    check(any("勝率" in r for r in reasons),
          f"勝率 30% < 40% 下限仍被點名（reasons={reasons}）")

    print("[19] 避免大虧：單筆最大虧損佔毛利")
    big_loss = fills([(100, 60), (-1500, 1), (-20, 20)])
    s = fx.dex_fill_stats(big_loss, "xyz", now_sec=NOW)
    check(s["worst_loss"] == 1500.0, f"抓到最大單筆虧損（實得 {s['worst_loss']}）")
    check(s["worst_loss_share_of_profit"] == 0.25,
          f"佔毛利 25%（實得 {s['worst_loss_share_of_profit']:.2f}）")
    huge = fills([(100, 60), (-3000, 1), (-20, 20)])
    s = fx.dex_fill_stats(huge, "xyz", now_sec=NOW)
    s["unrealized_pnl"] = 0.0
    v, reasons = fx.judge(s)
    check(any("大虧" in r for r in reasons),
          f"單筆虧損佔毛利 50% 被點名（reasons={reasons}）")

    print("[20] 未實現損益：補「從不認賠」的盲點")
    clean = fills([(500, 40), (-150, 20)])
    s = fx.dex_fill_stats(clean, "xyz", now_sec=NOW)
    s["unrealized_pnl"] = -20_000.0          # 已實現 +$17k、未實現 -$20k
    v, reasons = fx.judge(s)
    check(s["total_pnl"] == -3_000.0,
          f"總損益 = 已實現＋未實現（實得 {s['total_pnl']}）")
    check(v == "reject" and any("抱虧不認" in r for r in reasons),
          f"未實現虧損吃掉獲利 → 硬性淘汰（實得 {v}）")

    s = fx.dex_fill_stats(clean, "xyz", now_sec=NOW)
    s["unrealized_pnl"] = -1_000.0           # 小幅帳面虧損，仍在容許範圍
    v, _ = fx.judge(s)
    check(v == "winner", f"小幅未實現虧損不影響判定（實得 {v}）")

    s = fx.dex_fill_stats(clean, "xyz", now_sec=NOW)
    s["unrealized_pnl"] = None               # 缺資料
    v, reasons = fx.judge(s)
    check(v == "winner" and s["total_pnl"] == s["net_closed_pnl"],
          "未實現缺資料 → 只用已實現，不臆造")

    # 0x2171b50b 的型態：100% 勝率、零虧損樣本
    perfect = fills([(809, 78)])
    s = fx.dex_fill_stats(perfect, "xyz", now_sec=NOW)
    s["unrealized_pnl"] = 0.0
    check(s["win_to_loss_ratio"] is None, "零虧損 → 賠率 None（不給 inf）")
    v, reasons = fx.judge(s)
    check(v == "reject" and any("從不認賠" in r for r in reasons),
          f"100% 勝率零虧損 → 硬性不予判定（實得 {v}, {reasons}）")

    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)} of {CHECKS} checks)")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print(f"ALL TESTS PASSED ({CHECKS} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
