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
    soso = fills([(300, 33), (-200, 27)])   # 勝率 55%、pf 1.83
    s = fx.dex_fill_stats(soso, "xyz", now_sec=NOW)
    s["net_closed_pnl"] = 100.0             # 只有淨損益一項不過
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
        if t == "userFills":
            calls["fills"] += 1
            return [{"coin": "xyz:META", "closedPnl": "500", "time": int((NOW - 3 * DAY) * 1000),
                     "px": "1", "sz": "1", "side": "B", "fee": "0", "dir": "Close Long"}
                    for _ in range(40)] + \
                   [{"coin": "xyz:META", "closedPnl": "-150", "time": int((NOW - 40 * DAY) * 1000),
                     "px": "1", "sz": "1", "side": "A", "fee": "0", "dir": "Close Long"}
                    for _ in range(20)], True
        return None, False

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
    addrs, n_trades = fx.collect_via_websocket(["xyz:META", "xyz:GOLD"], 5,
                                               fx.fetch.Meta(), ws_factory=lambda u: fake)
    check(len(addrs) == 3, f"收到 3 個地址（實得 {len(addrs)}）")
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
    check("判準" in md and "平均虧損／平均獲利" in md, "報告載明判準（含關鍵那條）")
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
    for t in ('"type": "meta"', '"type": "clearinghouseState"', '"type": "userFills"'):
        check(t in src, f"使用唯讀查詢 {t}")

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
