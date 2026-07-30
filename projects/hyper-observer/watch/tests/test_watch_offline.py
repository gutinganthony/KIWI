#!/usr/bin/env python3
"""哨兵離線測試——不打網路，用 fake post_fn 餵 clearinghouseState 回應。

驗收重點（每一條都對應一個真實會發生的假警報／漏報）：
  1. 首次執行只建基準、不推播（cache 遺失不該把既有部位全報成新開倉）
  2. 新開倉／平倉／加倉／減倉分別偵測得到，且門檻以下的抖動不推播
  3. builder dex 的部位算得到（xyz 盲點迴歸）
  4. 全端點失敗 → 保留舊基準、不推播（資料缺失 ≠ 全部平倉）
  5. 冷卻只壓制加減倉，不壓制開倉／平倉
  6. 狀態檔可重複讀寫、體積受控（冷卻紀錄過期清掉）
"""

import json
import os
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
WATCH_DIR = HERE.parent
sys.path.insert(0, str(WATCH_DIR))
sys.path.insert(0, str(WATCH_DIR.parent))

import watch          # noqa: E402
import watch_config as wcfg  # noqa: E402

CHECKS = 0
FAILURES = []


def check(cond, msg):
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"  ok: {msg}")
    else:
        FAILURES.append(msg)
        print(f"  FAIL: {msg}")


def chs(positions, account_value=100000.0):
    """組一個 clearinghouseState 回應。positions: [(coin, szi, entry, notional, lev)]"""
    return {
        "marginSummary": {"accountValue": str(account_value)},
        "assetPositions": [
            {"position": {"coin": c, "szi": str(sz), "entryPx": str(px),
                          "positionValue": str(ntl), "unrealizedPnl": "0",
                          "leverage": {"value": str(lev), "type": "isolated"},
                          "liquidationPx": None, "marginUsed": "1", "maxLeverage": "20",
                          "cumFunding": {"allTime": "0"}}}
            for c, sz, px, ntl, lev in positions
        ],
    }


def make_post(native, by_dex=None, dexs=("xyz",), fail=()):
    """回一個 fake post_fn。fail 內含 "native"/dex 名 → 該查詢回失敗。"""
    calls = []

    def post_fn(body, name, meta):
        calls.append(body)
        t = body.get("type")
        if t == "perpDexs":
            return [None] + [{"name": d} for d in dexs], True
        if t == "clearinghouseState":
            dex = body.get("dex")
            if dex is None:
                if "native" in fail:
                    return None, False
                return native, True
            if dex in fail:
                return None, False
            return (by_dex or {}).get(dex, chs([], 0.0)), True
        return None, False

    post_fn.calls = calls
    return post_fn


def args_ns(state, dry_run=False):
    return types.SimpleNamespace(state=state, out_message="", test_notify=False, dry_run=dry_run)


def one_wallet_only():
    """把 TRACKED_WALLETS 縮成一個，測試才好斷言。回原值供還原。"""
    import config
    original = config.TRACKED_WALLETS
    config.TRACKED_WALLETS = [{"address": "0x" + "ab" * 20, "label": "test-wallet"}]
    return original, config


def main():
    original, config = one_wallet_only()
    tmpdir = tempfile.mkdtemp(prefix="hyper-watch-test-")
    state_path = os.path.join(tmpdir, "state.json")
    try:
        print("[1] 首次執行只建基準、不推播")
        native = chs([("BTC", 1.0, 60000, 60000, 5)])
        by_dex = {"xyz": chs([("xyz:META", 100.0, 500, 50000, 20)], 40000.0)}
        post = make_post(native, by_dex)
        msg, summ = watch.run(args_ns(state_path), post_fn=post)
        check(msg is None, "首次執行不產生訊息")
        check(summ["is_fresh"] is True, "首次執行標記 is_fresh")
        check(summ["n_events"] == 0, "首次執行 0 個事件")
        check(summ["wallets"][0]["n_positions"] == 2,
              f"原生+xyz 聯集 2 個部位（實得 {summ['wallets'][0]['n_positions']}）")
        check(summ["wallets"][0]["account_value"] == 140000.0,
              f"帳戶淨值聯集 = 100000+40000（實得 {summ['wallets'][0]['account_value']}）")
        check(os.path.exists(state_path), "狀態檔已寫出")

        print("[2] 完全沒變 → 不推播")
        msg, summ = watch.run(args_ns(state_path), post_fn=make_post(native, by_dex))
        check(msg is None and summ["n_events"] == 0, "無變化 → 無事件、無訊息")
        check(summ["is_fresh"] is False, "第二次執行不再是 fresh")

        print("[3] 新開倉（原生新增一個部位）")
        native2 = chs([("BTC", 1.0, 60000, 60000, 5), ("ETH", 10.0, 3000, 30000, 3)])
        msg, summ = watch.run(args_ns(state_path), post_fn=make_post(native2, by_dex))
        check(summ["n_events"] == 1, f"1 個事件（實得 {summ['n_events']}）")
        check(msg is not None and "新開倉" in msg and "ETH" in msg, "訊息含「新開倉」與 ETH")
        check("原生" in msg, "訊息標示場所為「原生」")

        print("[4] xyz 平倉 → 偵測得到且標示場所 xyz")
        msg, summ = watch.run(args_ns(state_path),
                              post_fn=make_post(native2, {"xyz": chs([], 40000.0)}))
        check(summ["n_events"] == 1, f"1 個平倉事件（實得 {summ['n_events']}）")
        check(msg is not None and "平倉" in msg and "xyz" in msg, "訊息含「平倉」與 xyz 場所")

        print("[5] 加倉／減倉門檻")
        # 目前基準：BTC 1.0、ETH 10.0（xyz 已平）
        small = chs([("BTC", 1.05, 60000, 63000, 5), ("ETH", 10.0, 3000, 30000, 3)])
        msg, summ = watch.run(args_ns(state_path),
                              post_fn=make_post(small, {"xyz": chs([], 40000.0)}))
        check(summ["n_events"] == 0,
              f"+5% < 門檻 {wcfg.WATCH_SIZE_CHANGE_PCT:.0%} → 不推播（實得 {summ['n_events']}）")
        big = chs([("BTC", 1.60, 60000, 96000, 5), ("ETH", 10.0, 3000, 30000, 3)])
        msg, summ = watch.run(args_ns(state_path),
                              post_fn=make_post(big, {"xyz": chs([], 40000.0)}))
        check(summ["n_events"] == 1, f"+52% ≥ 門檻 → 推播（實得 {summ['n_events']}）")
        check(msg is not None and "加倉" in msg, "訊息含「加倉」")
        check("+52%" in msg or "+53%" in msg, f"訊息含變化百分比（msg={msg!r}）")

        print("[6] 冷卻：加減倉被壓制，平倉不被壓制")
        bigger = chs([("BTC", 2.40, 60000, 144000, 5), ("ETH", 10.0, 3000, 30000, 3)])
        msg, summ = watch.run(args_ns(state_path),
                              post_fn=make_post(bigger, {"xyz": chs([], 40000.0)}))
        check(summ["n_events"] == 0 and summ["suppressed"] == 1,
              f"冷卻內的再次加倉被壓制（events={summ['n_events']}, "
              f"suppressed={summ['suppressed']}）")
        closed = chs([("ETH", 10.0, 3000, 30000, 3)])
        msg, summ = watch.run(args_ns(state_path),
                              post_fn=make_post(closed, {"xyz": chs([], 40000.0)}))
        check(summ["n_events"] == 1 and msg is not None and "平倉" in msg,
              "平倉不受冷卻壓制")

        print("[7] 全端點失敗 → 保留基準、不推播")
        before = json.load(open(state_path, encoding="utf-8"))
        post = make_post(closed, {"xyz": chs([], 0.0)}, fail=("native", "xyz"))
        msg, summ = watch.run(args_ns(state_path), post_fn=post)
        check(msg is None and summ["n_events"] == 0, "全失敗 → 不推播")
        check(summ["wallets"][0].get("skipped") == "all_endpoints_failed",
              "標記 skipped=all_endpoints_failed")
        after = json.load(open(state_path, encoding="utf-8"))
        addr = list(before["wallets"])[0]
        check(after["wallets"][addr]["positions"] == before["wallets"][addr]["positions"],
              "基準持倉未被清空（資料缺失 ≠ 全部平倉）")

        print("[8] 部分 dex 失敗 → 其他場所照常運作")
        post = make_post(closed, {"xyz": chs([], 0.0)}, fail=("xyz",))
        msg, summ = watch.run(args_ns(state_path), post_fn=post)
        check(summ["endpoint_failures"] >= 1, "記錄到端點失敗數")
        check(summ["wallets"][0].get("skipped") is None, "未整筆跳過（原生仍有資料）")

        print("[9] dry-run 不寫狀態")
        snapshot = Path(state_path).read_text(encoding="utf-8")
        watch.run(args_ns(state_path, dry_run=True),
                  post_fn=make_post(chs([("SOL", 500.0, 150, 75000, 4)]), {}))
        check(Path(state_path).read_text(encoding="utf-8") == snapshot, "dry-run 後狀態檔不變")

        print("[10] 純函式：diff / cooldown / key")
        old = {"|BTC|long": {"szi": 1.0, "notional": 100.0, "coin": "BTC",
                             "side": "long", "dex": ""}}
        new = {"|BTC|short": {"szi": 1.0, "notional": 100.0, "coin": "BTC",
                              "side": "short", "dex": ""}}
        evs = watch.diff_positions(old, new, 0.2)
        types_ = sorted(e["type"] for e in evs)
        check(types_ == ["closed", "opened"],
              f"多空對翻 = 一平一開（實得 {types_}）")
        evs = watch.diff_positions({}, {}, 0.2)
        check(evs == [], "空對空 → 無事件")
        k = watch.position_key({"dex": "xyz", "coin": "xyz:META", "side": "long"})
        check(k == "xyz|xyz:META|long", f"key 格式（實得 {k}）")
        kept, sup = watch.apply_cooldown(
            [{"type": "increased", "key": "a", "new": {}, "old": {}, "pct": 0.5}],
            {"a": 999_999_999_999}, 999_999_999_999, 3600)
        check(kept == [] and sup == 1, "cooldown 壓制加倉")
        kept, sup = watch.apply_cooldown(
            [{"type": "opened", "key": "a", "new": {}, "old": {}, "pct": None}],
            {"a": 999_999_999_999}, 999_999_999_999, 3600)
        check(len(kept) == 1 and sup == 0, "cooldown 不壓制開倉")

        print("[11] 訊息長度上限")
        many = {f"|C{i}|long": {"szi": 1.0, "notional": 1000.0, "coin": f"C{i}",
                                "side": "long", "dex": ""} for i in range(40)}
        # 直接餵 40 個新部位（先清基準）
        st, _ = watch.load_state(state_path)
        st["wallets"][addr]["positions"] = {}
        watch.save_state(state_path, st)
        pos = [(f"C{i}", 1.0, 100, 1000, 2) for i in range(40)]
        msg, summ = watch.run(args_ns(state_path), post_fn=make_post(chs(pos), {}))
        check(summ["n_events"] == wcfg.WATCH_MAX_EVENTS_PER_MESSAGE + 1,
              f"事件數截到上限+1 行摘要（實得 {summ['n_events']}）")
        check("另有" in msg, "訊息含「另有 N 個變動未列出」")
        check(len(msg) < 3500, f"訊息長度 < Telegram 4096 上限（實得 {len(msg)}）")

        print("[12] 狀態檔健全性")
        st, fresh = watch.load_state(state_path)
        check(fresh is False and st["version"] == watch.STATE_VERSION, "狀態檔可重讀且版本正確")
        Path(state_path).write_text("{not json", encoding="utf-8")
        st, fresh = watch.load_state(state_path)
        check(fresh is True and st["wallets"] == {}, "壞掉的狀態檔 → 退回建基準模式（不 crash）")
        Path(state_path).write_text('{"version": 99, "wallets": {"a": {}}}', encoding="utf-8")
        st, fresh = watch.load_state(state_path)
        check(fresh is True and st["wallets"] == {}, "版本不符 → 退回建基準模式")

        print("[13] 測試訊息與唯讀保證")
        tm = watch.test_message()
        check("測試推播" in tm and "唯讀" in tm, "測試訊息內容正確")
        src = (WATCH_DIR / "watch.py").read_text(encoding="utf-8")
        for bad in ("place_order", "private_key", "eth_account", "signature",
                    "/exchange", "wallet.sign"):
            check(bad not in src, f"watch.py 不含 {bad}（唯讀保證）")
        check('"type": "clearinghouseState"' in src, "只查 clearinghouseState（唯讀 info）")

        print("[14] 只呼叫允許的 info type")
        post = make_post(closed, {"xyz": chs([], 1.0)})
        watch.run(args_ns(state_path), post_fn=post)
        used = sorted({c.get("type") for c in post.calls})
        check(used == ["clearinghouseState", "perpDexs"],
              f"只用了 clearinghouseState / perpDexs（實得 {used}）")
    finally:
        config.TRACKED_WALLETS = original

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
