#!/usr/bin/env python3
"""找出在 HIP-3 builder dex（預設 xyz）上真正賺錢的錢包——三層漏斗，唯讀。

為什麼不能沿用現有的宇宙掃描
  現有 scan 的候選來自 Hyperliquid 排行榜（stats-data leaderboard），而排行榜的
  PnL 是**原生永續**的口徑。實測追蹤錢包 0x8bae35 近 30 天 2000 筆成交裡 1,766 筆
  在 xyz，但排行榜只反映他的原生績效——換句話說「xyz 專精的贏家」在排行榜上
  幾乎是隱形的。要找 xyz 贏家，必須先取得「在 xyz 上有活動的地址」這個母體。

三層漏斗（成本從低到高）
  L1 母體取得：訂閱 xyz 各幣的公開 trades 頻道，收集成交雙方地址（WS 的 trades
      推播帶 users 欄）。收不到 → 退回用排行榜地址當母體（較弱，但不會空手）。
  L2 便宜篩選：每個地址查一次 clearinghouseState(dex=xyz)（權重 2）→ 只留 xyz
      帳戶淨值達門檻者。這一層把數百個地址砍到數十個。
  L3 昂貴驗證：對倖存者查 userFills（權重可達 120）→ **只取 coin 屬於 xyz 的成交**
      算勝率／獲利因子／單筆集中度／強平次數，再套 winner 判準。

刻意的判準設計（每一條都對應一個實際踩過的坑）
  - 勝率高 ≠ 賺錢：追蹤錢包在 xyz 勝率 58.3%，但平均虧 $410／平均賺 $188，
    獲利因子 0.64——實際是虧的。所以勝率與獲利因子**必須同時**過關，
    且加一條「平均虧損 / 平均獲利」上限。
  - userFills 被 API 截斷在 2000 筆（近端窗）→ 樣本偏誤大，一律標 truncated
    且不判為 winner（與 classify.py 的 consistent_winner 同一規矩）。
  - 單筆最大獲利佔比過半 → 一次好運，不是本事。
  - 反覆強平 → 不論績效多好都不跟。

唯讀：只 POST info API 的查詢型別與訂閱公開 WS 頻道。不下單、不簽章、無私鑰。
"""

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import classify              # noqa: E402
import config                # noqa: E402
import fetch                 # noqa: E402
import xyz_config as xcfg    # noqa: E402


# ---------------------------------------------------------------------------
# L1：母體取得
# ---------------------------------------------------------------------------

def dex_coins(dex, meta, post_fn=None):
    """{"type":"meta","dex":dex} → 該 dex 的合約名清單（已含 "dex:" 前綴則照用）。"""
    post_fn = post_fn or fetch.http_post_info
    data, ok = post_fn({"type": "meta", "dex": dex}, f"meta:{dex}", meta)
    if not ok or not isinstance(data, dict):
        meta.note(f"meta(dex={dex}) 查詢失敗，無法列舉合約")
        return []
    universe = data.get("universe")
    if not isinstance(universe, list):
        return []
    coins = []
    for u in universe:
        if not isinstance(u, dict):
            continue
        name = u.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        name = name.strip()
        coins.append(name if ":" in name else f"{dex}:{name}")
    return coins


def is_dex_coin(coin, dex):
    """成交的 coin 是否屬於這個 builder dex。原生永續無 "dex:" 前綴。"""
    return isinstance(coin, str) and coin.startswith(f"{dex}:")


def parse_trade_users(msg, dex):
    """WS trades 推播 → 出現在 xyz 成交裡的地址集合（純函式，供離線測試）。

    形狀：{"channel":"trades","data":[{"coin":"xyz:META","users":["0x..","0x.."],...}]}
    users 缺失／格式怪 → 跳過該筆，不 crash（公開頻道欄位不保證）。
    """
    out = set()
    if not isinstance(msg, dict):
        return out
    if msg.get("channel") not in (None, "trades"):
        return out
    data = msg.get("data")
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return out
    for tr in data:
        if not isinstance(tr, dict):
            continue
        if not is_dex_coin(tr.get("coin"), dex):
            continue
        users = tr.get("users")
        if isinstance(users, str):
            users = [users]
        if not isinstance(users, list):
            continue
        for u in users:
            if isinstance(u, str) and u.startswith("0x") and len(u) == 42:
                out.add(u.lower())
    return out


def collect_via_websocket(coins, seconds, meta, ws_factory=None):
    """訂閱 coins 的 trades 頻道 seconds 秒，回 (addresses, n_trades)。

    ws_factory 供測試注入。任何失敗 → 回 (set(), 0) 並記 note（呼叫端退回排行榜母體）。
    """
    if ws_factory is None:
        try:
            import websocket  # type: ignore
        except ImportError as exc:
            meta.note(f"websocket-client 未安裝（{exc}），L1 退回排行榜母體")
            return set(), 0

        def ws_factory(url):
            return websocket.create_connection(url, timeout=xcfg.WS_TIMEOUT_SEC)

    addrs, n_trades = set(), 0
    try:
        ws = ws_factory(xcfg.WS_URL)
    except Exception as exc:
        meta.note(f"WS 連線失敗（{type(exc).__name__}: {exc}），L1 退回排行榜母體")
        return set(), 0
    try:
        for coin in coins[: xcfg.WS_MAX_COINS]:
            ws.send(json.dumps({"method": "subscribe",
                                "subscription": {"type": "trades", "coin": coin}}))
        deadline = time.time() + seconds
        while time.time() < deadline:
            try:
                raw = ws.recv()
            except Exception as exc:
                meta.note(f"WS 接收中斷（{type(exc).__name__}: {exc}），沿用已收集的地址")
                break
            if not raw:
                continue
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            found = parse_trade_users(msg, xcfg.DEX)
            if found:
                n_trades += 1
                addrs |= found
    finally:
        try:
            ws.close()
        except Exception:
            pass
    meta.note(f"WS 收集 {seconds}s：{n_trades} 筆 {xcfg.DEX} 成交、{len(addrs)} 個不重複地址")
    return addrs, n_trades


def collect_via_leaderboard(meta, get_fn=None):
    """退路母體：排行榜地址（原生口徑，對 xyz 專精者覆蓋率差，只當備援）。"""
    raw, ok = fetch.fetch_leaderboard(meta, get_fn=get_fn)
    if not ok:
        meta.note("排行榜也抓不到 → L1 無母體")
        return set()
    addrs = fetch.extract_addresses(raw, limit=xcfg.LEADERBOARD_FALLBACK_LIMIT)
    return {a.lower() for a in addrs if isinstance(a, str)}


# ---------------------------------------------------------------------------
# L2：便宜篩選（clearinghouseState(dex)）
# ---------------------------------------------------------------------------

def screen_addresses(addrs, meta, post_fn=None):
    """回 [{"address", "account_value", "n_positions", "position_value"}]，已過門檻並排序。"""
    post_fn = post_fn or fetch.http_post_info
    kept = []
    for addr in addrs:
        data, ok = post_fn({"type": "clearinghouseState", "user": addr, "dex": xcfg.DEX},
                           f"chs:{xcfg.DEX}:{addr[:10]}", meta)
        if not ok:
            continue
        acct = classify.account_summary(data)
        pos = classify.parse_positions(data)
        av = acct["account_value"]
        if av is None or av < xcfg.L2_MIN_ACCOUNT_VALUE:
            continue
        kept.append({"address": addr, "account_value": av, "n_positions": len(pos),
                     "position_value": round(sum(p["position_value"] for p in pos
                                                 if p["position_value"] is not None), 2)})
    kept.sort(key=lambda r: -(r["account_value"] or 0))
    return kept[: xcfg.L2_MAX_SURVIVORS]


# ---------------------------------------------------------------------------
# L3：xyz-only 績效
# ---------------------------------------------------------------------------

def dex_fill_stats(fills, dex, now_sec=None, window_days=30):
    """只取 dex 的成交算績效。回 dict（純函式，供離線測試）。

    時間單位：classify.parse_fills 已把 ts 正規化成 **epoch 秒**（不是毫秒）。
    這裡一律用秒運算——曾經寫成毫秒，結果每個錢包的「最後成交距今」都算成兩萬多天、
    全部被「已停手」條件淘汰，掃描永遠回 0 個候選（離線測試抓到的）。

    重要：Hyperliquid 的 closedPnl 對贏、輸的平倉都有值，所以這裡沒有贏家倖存者偏誤。
    但 userFills 只回近端 config.MAX_USER_FILLS 筆——若總筆數觸頂，30 天窗可能被切掉
    一半，勝率／獲利因子就只反映近端樣本，必須標 truncated。
    """
    total_fills = len(fills)
    truncated = total_fills >= config.MAX_USER_FILLS
    dex_fills = [f for f in fills if is_dex_coin(f.get("coin"), dex)]
    if now_sec is None:
        now_sec = time.time()
    cutoff = now_sec - window_days * 86_400
    recent = [f for f in dex_fills if (f.get("ts") or 0) >= cutoff]

    closed = [f for f in dex_fills if f.get("closed_pnl")]
    wins = [f["closed_pnl"] for f in closed if f["closed_pnl"] > 0]
    losses = [f["closed_pnl"] for f in closed if f["closed_pnl"] < 0]
    gross_profit, gross_loss = sum(wins), abs(sum(losses))
    n_closed = len(wins) + len(losses)

    pf = None
    if gross_loss > 1e-9:
        pf = gross_profit / gross_loss
    elif gross_profit > 1e-9:
        pf = 999.0
    avg_win = (gross_profit / len(wins)) if wins else None
    avg_loss = (gross_loss / len(losses)) if losses else None
    loss_to_win = (avg_loss / avg_win) if (avg_win and avg_loss and avg_win > 1e-9) else None
    net = gross_profit - gross_loss
    top_share = (max(wins) / gross_profit) if wins and gross_profit > 1e-9 else None

    ts = [f["ts"] for f in dex_fills if f.get("ts")]
    span_days = ((max(ts) - min(ts)) / 86_400) if len(ts) >= 2 else 0.0
    last_days = ((now_sec - max(ts)) / 86_400) if ts else None

    return {
        "n_fills_total": total_fills,
        "n_fills_dex": len(dex_fills),
        "n_fills_dex_30d": len(recent),
        "dex_share_of_fills": (len(dex_fills) / total_fills) if total_fills else None,
        "sample_truncated": truncated,
        "n_closed_fills": n_closed,
        "win_rate": (len(wins) / n_closed) if n_closed else None,
        "profit_factor": pf,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "loss_to_win_ratio": loss_to_win,
        "net_closed_pnl": net,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "top_trade_share_of_profit": top_share,
        "n_liquidations": sum(1 for f in dex_fills if f.get("is_liquidation")),
        "n_coins": len({f.get("coin") for f in dex_fills}),
        "span_days": round(span_days, 1),
        "days_since_last_fill": round(last_days, 1) if last_days is not None else None,
    }


def judge(stats):
    """回 (verdict, reasons)。verdict ∈ winner / near_miss / reject / insufficient_data。

    reasons 一律列出**所有**未過的條件（不是第一個），這樣報告能直接看出他敗在哪。
    """
    reasons = []
    if stats["n_closed_fills"] < xcfg.MIN_CLOSED_FILLS:
        return "insufficient_data", [
            f"平倉樣本 {stats['n_closed_fills']} < {xcfg.MIN_CLOSED_FILLS} 筆（樣本不足，不判定）"]
    if stats["sample_truncated"]:
        reasons.append(f"userFills 觸及 {config.MAX_USER_FILLS} 筆上限（近端樣本偏誤，"
                       "勝率/獲利因子不可信）")
    if stats["span_days"] < xcfg.MIN_SPAN_DAYS:
        reasons.append(f"活躍跨度 {stats['span_days']:.0f} < {xcfg.MIN_SPAN_DAYS} 天")
    if stats["net_closed_pnl"] < xcfg.MIN_NET_PNL:
        reasons.append(f"{xcfg.DEX} 已實現淨損益 ${stats['net_closed_pnl']:,.0f} "
                       f"< ${xcfg.MIN_NET_PNL:,.0f}")
    pf = stats["profit_factor"]
    if pf is None or pf < xcfg.MIN_PROFIT_FACTOR:
        reasons.append(f"獲利因子 {pf if pf is None else round(pf, 2)} < {xcfg.MIN_PROFIT_FACTOR}")
    wr = stats["win_rate"]
    if wr is None or wr < xcfg.MIN_WIN_RATE:
        reasons.append(f"勝率 {'?' if wr is None else f'{wr:.1%}'} < {xcfg.MIN_WIN_RATE:.0%}")
    ltw = stats["loss_to_win_ratio"]
    if ltw is not None and ltw > xcfg.MAX_LOSS_TO_WIN:
        reasons.append(f"平均虧損／平均獲利 {ltw:.1f} > {xcfg.MAX_LOSS_TO_WIN}"
                       "（高勝率但單筆虧損遠大於獲利＝賣尾部風險）")
    top = stats["top_trade_share_of_profit"]
    if top is not None and top > xcfg.MAX_TOP_TRADE_SHARE:
        reasons.append(f"單筆最大獲利占毛利 {top:.0%} > {xcfg.MAX_TOP_TRADE_SHARE:.0%}（一次好運）")
    if stats["n_liquidations"] >= xcfg.MAX_LIQUIDATIONS:
        reasons.append(f"強平 {stats['n_liquidations']} 次 >= {xcfg.MAX_LIQUIDATIONS}")
    if stats["days_since_last_fill"] is not None and \
            stats["days_since_last_fill"] > xcfg.MAX_IDLE_DAYS:
        reasons.append(f"最後成交距今 {stats['days_since_last_fill']:.0f} 天 "
                       f"> {xcfg.MAX_IDLE_DAYS}（已停手）")
    if not reasons:
        return "winner", []
    hard = [r for r in reasons if "偏誤" in r or "強平" in r or "一次好運" in r]
    if len(reasons) <= xcfg.NEAR_MISS_MAX_FAILS and not hard:
        return "near_miss", reasons
    return "reject", reasons


# ---------------------------------------------------------------------------
# 報告
# ---------------------------------------------------------------------------

def _fmt_money(v):
    if v is None:
        return "?"
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"${v/1_000:.0f}k"
    return f"${v:,.0f}"


def _pct(v, digits=1):
    return "?" if v is None else f"{v*100:.{digits}f}%"


def _num(v, digits=2):
    return "?" if v is None else f"{round(v, digits)}"


def _wallet_lines(r, dex):
    """單一錢包的報告區塊。所有可能為 None 的數值都走 _pct/_num/_fmt_money。"""
    s = r["stats"]
    return [
        f"### `{r['address']}`",
        "",
        f"- {dex} 帳戶淨值 {_fmt_money(r['account_value'])}"
        f"／目前 {r['n_positions']} 個部位（名目 {_fmt_money(r['position_value'])}）",
        f"- {dex} 已實現淨損益 **{_fmt_money(s['net_closed_pnl'])}**"
        f"｜獲利因子 **{_num(s['profit_factor'])}**｜勝率 **{_pct(s['win_rate'])}**"
        f"（{s['n_closed_fills']} 筆平倉）",
        f"- 平均獲利 {_fmt_money(s['avg_win'])}／平均虧損 {_fmt_money(s['avg_loss'])}"
        f"（虧／賺比值 {_num(s['loss_to_win_ratio'])}）",
        f"- {dex} 成交 {s['n_fills_dex']} 筆（占全部 {_pct(s['dex_share_of_fills'], 0)}）"
        f"｜近 30 天 {s['n_fills_dex_30d']} 筆｜{s['n_coins']} 個合約"
        f"｜跨度 {s['span_days']:.0f} 天｜最後成交 {s['days_since_last_fill']} 天前",
        f"- 強平 {s['n_liquidations']} 次｜單筆最大獲利占毛利 "
        f"{_pct(s['top_trade_share_of_profit'], 0)}"
        + ("｜⚠ userFills 樣本已截斷" if s["sample_truncated"] else ""),
    ]


def render_report(result):
    dex = result["dex"]
    L = [f"# {dex} builder dex 贏家掃描 — {result['generated_at'][:16]}Z", "",
         "## 漏斗", "",
         "| 層 | 方法 | 進 | 出 |", "|---|---|---:|---:|",
         f"| L1 母體 | {result['l1_method']} | — | {result['l1_addresses']} |",
         f"| L2 篩選 | {dex} 帳戶淨值 ≥ {_fmt_money(xcfg.L2_MIN_ACCOUNT_VALUE)} | "
         f"{result['l1_addresses']} | {result['l2_survivors']} |",
         f"| L3 驗證 | {dex}-only 成交績效判準 | {result['l2_survivors']} | "
         f"{result['n_winners']} winner／{result['n_near_miss']} near-miss |", ""]
    if result.get("notes"):
        L += ["### 執行備註", ""] + [f"- {n}" for n in result["notes"]] + [""]

    groups = [("winner", "✅ Winner（全部判準過關）"),
              ("near_miss", "🟡 Near-miss（差一兩項，值得放觀察名單）"),
              ("reject", "❌ Reject"),
              ("insufficient_data", "⚪ 樣本不足（不判定）")]
    for key, title in groups:
        rows = [r for r in result["wallets"] if r["verdict"] == key]
        if not rows:
            continue
        if key in ("reject", "insufficient_data"):
            L += [f"## {title}：{len(rows)} 個", ""]
            if key == "reject":
                counter = defaultdict(int)
                for r in rows:
                    for reason in r["reasons"]:
                        counter[reason.split("（")[0].split(" <")[0].split(" >")[0]] += 1
                L += ["最常見的淘汰原因：", ""]
                L += [f"- {k}：{v} 個" for k, v in
                      sorted(counter.items(), key=lambda kv: -kv[1])[:6]] + [""]
            continue
        L += [f"## {title}", ""]
        for r in rows:
            L += _wallet_lines(r, dex)
            if r["reasons"]:
                L += ["- 未過的判準：" + "；".join(r["reasons"])]
            L += [""]

    L += ["## 判準（config: xyzscan/xyz_config.py）", "",
          f"- 平倉樣本 ≥ {xcfg.MIN_CLOSED_FILLS} 筆、活躍跨度 ≥ {xcfg.MIN_SPAN_DAYS} 天",
          f"- 獲利因子 ≥ {xcfg.MIN_PROFIT_FACTOR}、勝率 ≥ {_pct(xcfg.MIN_WIN_RATE, 0)}"
          f"、淨損益 ≥ {_fmt_money(xcfg.MIN_NET_PNL)}",
          f"- 平均虧損／平均獲利 ≤ {xcfg.MAX_LOSS_TO_WIN}（擋「高勝率但賣尾部」——"
          "追蹤錢包在 xyz 就是這型：勝率 58%、獲利因子 0.64）",
          f"- 單筆最大獲利占毛利 ≤ {_pct(xcfg.MAX_TOP_TRADE_SHARE, 0)}"
          f"、強平 < {xcfg.MAX_LIQUIDATIONS} 次",
          f"- 最後成交 ≤ {xcfg.MAX_IDLE_DAYS} 天前；userFills 觸頂（樣本截斷）一律不判 winner",
          "", "唯讀掃描：只查公開 info API 與公開 trades 頻道，無下單／簽章／私鑰。"]
    return "\n".join(L)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run(args, post_fn=None, get_fn=None, ws_factory=None):
    meta = fetch.Meta()
    post_fn = post_fn or fetch.http_post_info

    coins = dex_coins(xcfg.DEX, meta, post_fn=post_fn)
    meta.note(f"{xcfg.DEX} 合約數：{len(coins)}"
              + (f"（前幾個：{', '.join(coins[:6])}）" if coins else ""))

    l1_method, addrs = f"WS trades（{args.ws_seconds}s）", set()
    if coins and args.ws_seconds > 0:
        addrs, _ = collect_via_websocket(coins, args.ws_seconds, meta, ws_factory=ws_factory)
    if len(addrs) < xcfg.L1_MIN_ADDRESSES:
        extra = collect_via_leaderboard(meta, get_fn=get_fn)
        if extra:
            l1_method = (f"WS trades（{len(addrs)} 個）＋排行榜備援（{len(extra)} 個）"
                         if addrs else "排行榜備援（WS 無母體）")
            addrs |= extra
    addrs = sorted(addrs)[: xcfg.L1_MAX_ADDRESSES]

    survivors = screen_addresses(addrs, meta, post_fn=post_fn)

    wallets = []
    now_sec = time.time()
    for row in survivors:
        raw, ok = post_fn({"type": "userFills", "user": row["address"]},
                          f"userFills:{row['address'][:10]}", meta)
        if not ok:
            continue
        stats = dex_fill_stats(classify.parse_fills(raw), xcfg.DEX, now_sec=now_sec)
        verdict, reasons = judge(stats)
        wallets.append({**row, "stats": stats, "verdict": verdict, "reasons": reasons})

    order = {"winner": 0, "near_miss": 1, "reject": 2, "insufficient_data": 3}
    wallets.sort(key=lambda w: (order[w["verdict"]], -(w["stats"]["net_closed_pnl"] or 0)))

    return {
        "dex": xcfg.DEX,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "l1_method": l1_method,
        "l1_addresses": len(addrs),
        "l2_survivors": len(survivors),
        "n_winners": sum(1 for w in wallets if w["verdict"] == "winner"),
        "n_near_miss": sum(1 for w in wallets if w["verdict"] == "near_miss"),
        "wallets": wallets,
        "notes": meta.notes,
        "requests_ok": meta.requests_ok,
        "requests_failed": meta.requests_failed,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=f"{xcfg.DEX} builder dex 贏家掃描（唯讀）")
    p.add_argument("--ws-seconds", type=int, default=xcfg.WS_COLLECT_SEC,
                   help="訂閱 trades 頻道收集地址的秒數（0＝跳過，直接用排行榜母體）")
    p.add_argument("--out-json", default="", help="結果 JSON 落地路徑（可省略）")
    p.add_argument("--out-md", default="", help="報告 Markdown 落地路徑（可省略）")
    args = p.parse_args(argv)

    result = run(args)
    report = render_report(result)
    print()
    print(report)
    if args.out_json:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(
            json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if args.out_md:
        Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_md).write_text(report + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
