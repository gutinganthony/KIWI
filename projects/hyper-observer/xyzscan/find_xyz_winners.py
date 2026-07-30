#!/usr/bin/env python3
"""找出在 HIP-3 builder dex（預設 xyz）上真正賺錢的錢包——三層漏斗，唯讀。

為什麼不能沿用現有的宇宙掃描
  現有 scan 的候選來自 Hyperliquid 排行榜（stats-data leaderboard），而排行榜的
  PnL 是**原生永續**的口徑。實測追蹤錢包 0x8bae35 近 30 天 2000 筆成交裡 1,766 筆
  在 xyz，但排行榜只反映他的原生績效——換句話說「xyz 專精的贏家」在排行榜上
  幾乎是隱形的。要找 xyz 贏家，必須先取得「在 xyz 上有活動的地址」這個母體。

三層漏斗（成本從低到高）
  L1 母體取得：訂閱 xyz 各幣的公開 trades 頻道，收集成交雙方地址與**窗內出現次數**
      （WS 的 trades 推播帶 users 欄）。收不到 → 退回排行榜母體（較弱，但不空手）。
  L2 便宜篩選：每個地址查一次 clearinghouseState(dex=xyz)（權重 2）→ 只留 xyz
      帳戶淨值達門檻者。這一層把數百個地址砍到數十個。
  L3 昂貴驗證：對倖存者用 userFillsByTime 分頁抓近 30 天成交 → **只取 coin 屬於
      xyz 的成交**算勝率／獲利因子／單筆集中度／強平次數，再套 winner 判準。

第一版實跑（2026-07-30）的教訓，已修進本版
  - 取樣偏誤：從成交流取樣，**出現機率與交易頻率成正比**，7 分鐘窗抓到的 842 個
    地址天生偏向做市型帳戶；第一版沒排序（照 hex 字串排），L3 預算全花在他們身上，
    60 個候選裡 54 個因「樣本觸頂」淘汰，等於什麼都沒驗證到。
    → L1 改記每個地址的窗內成交次數，**低頻優先**送進 L2/L3（本專案的結論是只有
      慢錢可跟，預算就該導向低頻端）。
  - 樣本窗太短：userFills 只回最近 2000 筆，高頻帳戶等於只看到不到一天，
    活躍跨度全被算成 0～1 天。→ 改用 userFillsByTime 分頁抓真正的 30 天窗；
    只有連分頁上限都填滿才是真高頻（該淘汰）。

刻意的判準設計（每一條都對應一個實際踩過的坑）
  - 勝率高 ≠ 賺錢：追蹤錢包在 xyz 勝率 58.3%，但平均虧 $410／平均賺 $188，
    獲利因子 0.64——實際是虧的。所以勝率與獲利因子**必須同時**過關，
    且加一條「平均虧損 / 平均獲利」上限。
  - 30 天窗內成交填滿分頁上限 → 做市／高頻型，不判為 winner。
  - 單筆最大獲利佔比過半 → 一次好運，不是本事。
  - 反覆強平 → 不論績效多好都不跟。
  - 硬性缺陷用明確 flag 記錄，不靠 reason 文字比對（改文案就靜默失效）。

唯讀：只 POST info API 的查詢型別與訂閱公開 WS 頻道。不下單、不簽章、無私鑰。
"""

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
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
    """訂閱 coins 的 trades 頻道 seconds 秒，回 (Counter{addr: 窗內成交次數}, n_trades)。

    為什麼要記次數而不只是地址集合：從成交流取樣，**出現機率與交易頻率成正比**，
    所以短窗抓到的名單天生偏向高頻做市型帳戶——而本專案的結論是「只有慢錢可跟」。
    次數讓 L1 可以反向排序（優先送出現次數少的），把有限的 L3 預算花在慢錢身上。

    ws_factory 供測試注入。任何失敗 → 回 (Counter(), 0) 並記 note（呼叫端退回排行榜母體）。
    """
    if ws_factory is None:
        try:
            import websocket  # type: ignore
        except ImportError as exc:
            meta.note(f"websocket-client 未安裝（{exc}），L1 退回排行榜母體")
            return set(), 0

        def ws_factory(url):
            return websocket.create_connection(url, timeout=xcfg.WS_TIMEOUT_SEC)

    seen, n_trades = Counter(), 0
    try:
        ws = ws_factory(xcfg.WS_URL)
    except Exception as exc:
        meta.note(f"WS 連線失敗（{type(exc).__name__}: {exc}），L1 退回排行榜母體")
        return Counter(), 0
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
                for a in found:
                    seen[a] += 1
    finally:
        try:
            ws.close()
        except Exception:
            pass
    meta.note(f"WS 收集 {seconds}s：{n_trades} 筆 {xcfg.DEX} 成交、{len(seen)} 個不重複地址")
    return seen, n_trades


def collect_via_leaderboard(meta, get_fn=None):
    """退路母體：排行榜地址（原生口徑，對 xyz 專精者覆蓋率差，只當備援）。"""
    raw, ok = fetch.fetch_leaderboard(meta, get_fn=get_fn)
    if not ok:
        meta.note("排行榜也抓不到 → L1 無母體")
        return Counter()
    addrs = fetch.extract_addresses(raw, limit=xcfg.LEADERBOARD_FALLBACK_LIMIT)
    # 排行榜沒有頻率資訊 → 次數記 0（排序時與「窗內只出現一次」同級最優先）
    return Counter({a.lower(): 0 for a in addrs if isinstance(a, str)})


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
        # 未實現損益一併帶走：只算 closedPnl 會漏掉「從不認賠」的人（見 xyz_config）。
        upnl = [p["unrealized_pnl"] for p in pos if p["unrealized_pnl"] is not None]
        notional = round(sum(p["position_value"] for p in pos
                             if p["position_value"] is not None), 2)
        kept.append({"address": addr, "account_value": av, "n_positions": len(pos),
                     "position_value": notional,
                     "unrealized_pnl": round(sum(upnl), 2) if upnl else None,
                     "leverage_now": round(notional / av, 2) if av > 0 else None})
    kept.sort(key=lambda r: -(r["account_value"] or 0))
    return kept[: xcfg.L2_MAX_SURVIVORS]


# ---------------------------------------------------------------------------
# L3：xyz-only 績效
# ---------------------------------------------------------------------------

def fetch_fills_window(addr, meta, post_fn=None, days=None):
    """用 userFillsByTime 分頁抓「近 days 天」的成交。回 (fills_raw, hit_page_cap)。

    為什麼不用 userFills：它只回**最近 2000 筆**，對高頻帳戶等於只看到不到一天的
    樣本——第一版掃描 54 個候選全部觸頂、活躍跨度算出 0 天，整批被「樣本截斷／
    跨度不足」淘汰，等於什麼都沒驗證到。userFillsByTime 可以指定時間窗並分頁，
    才拿得到真正的 30 天樣本；只有連 PAGE_CAP 頁都填滿才是真高頻（該淘汰）。

    每頁 startTime 前進到「上一頁最後一筆時間 +1ms」，避免同一筆重複計入。
    """
    post_fn = post_fn or fetch.http_post_info
    days = days or xcfg.FILL_WINDOW_DAYS
    start_ms = int((time.time() - days * 86_400) * 1000)
    out, hit_cap = [], False
    for page in range(xcfg.FILL_PAGE_CAP):
        data, ok = post_fn({"type": "userFillsByTime", "user": addr,
                            "startTime": start_ms},
                           f"userFillsByTime:{addr[:10]}:p{page}", meta)
        if not ok:
            break
        rows = data if isinstance(data, list) else []
        if not rows:
            break
        out.extend(rows)
        if len(rows) < config.MAX_USER_FILLS:
            break            # 未滿頁 → 這個時間窗已抓完
        times = [r.get("time") for r in rows
                 if isinstance(r, dict) and isinstance(r.get("time"), (int, float))]
        if not times:
            break
        next_start = int(max(times)) + 1
        if next_start <= start_ms:   # 防禦：時間沒前進就停，不無限迴圈
            break
        start_ms = next_start
        if page == xcfg.FILL_PAGE_CAP - 1:
            hit_cap = True
    return out, hit_cap


def dex_fill_stats(fills, dex, now_sec=None, window_days=30, truncated=None):
    """只取 dex 的成交算績效。回 dict（純函式，供離線測試）。

    時間單位：classify.parse_fills 已把 ts 正規化成 **epoch 秒**（不是毫秒）。
    這裡一律用秒運算——曾經寫成毫秒，結果每個錢包的「最後成交距今」都算成兩萬多天、
    全部被「已停手」條件淘汰，掃描永遠回 0 個候選（離線測試抓到的）。

    重要：Hyperliquid 的 closedPnl 對贏、輸的平倉都有值，所以這裡沒有贏家倖存者偏誤。
    truncated 由呼叫端（fetch_fills_window）傳入：只有分頁抓到上限才算樣本不完整。
    不再用「總筆數 >= 2000」猜——那是 userFills 單次上限的殘留語意，會把正常的
    30 天樣本誤判成截斷。
    """
    total_fills = len(fills)
    # 舊語意（總筆數觸及單次上限）僅在呼叫端沒給 truncated 時當退路使用。
    truncated = bool(truncated) if truncated is not None \
        else (total_fills >= config.MAX_USER_FILLS)
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
    # 賠率＝平均獲利 ÷ 平均虧損（主關卡）。零虧損 → None 而非 inf：
    # 「樣本內沒有虧損」在本判準是**可疑**（可能從不認賠），交給未實現那關處理。
    win_to_loss = (avg_win / avg_loss) if (avg_win and avg_loss and avg_loss > 1e-9) else None
    net = gross_profit - gross_loss
    top_share = (max(wins) / gross_profit) if wins and gross_profit > 1e-9 else None
    worst_loss = abs(min(losses)) if losses else 0.0
    worst_loss_share = (worst_loss / gross_profit) if gross_profit > 1e-9 else None

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
        "win_to_loss_ratio": win_to_loss,
        "worst_loss": worst_loss,
        "worst_loss_share_of_profit": worst_loss_share,
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

    目標型態：**大賺、小賺、小虧，避免大虧**。量化成三根支柱：
      - 賠率（平均獲利 ÷ 平均虧損）≥ MIN_WIN_TO_LOSS ——「賺的顯著大於虧的」
      - 單筆最大虧損佔毛利 ≤ MAX_WORST_LOSS_SHARE ——「沒有一次大虧」
      - 總損益（已實現＋未實現）≥ MIN_NET_PNL ——「加總真的是賺的」
    勝率退居為「排除樂透型」的下限（見 xyz_config 對耦合的說明），不再是主關卡。

    未實現損益（stats["unrealized_pnl"]，由 L2 的 clearinghouseState 帶入）為 None
    時跳過相關判定並在理由裡註明——不臆造，缺資料就說缺資料。

    硬性缺陷用明確 is_hard flag，不靠 reason 字串比對（改文案曾讓判定靜默失效）。
    """
    reasons, hard = [], False

    def fail(text, is_hard=False):
        nonlocal hard
        reasons.append(text)
        hard = hard or is_hard

    if stats["n_closed_fills"] < xcfg.MIN_CLOSED_FILLS:
        return "insufficient_data", [
            f"平倉樣本 {stats['n_closed_fills']} < {xcfg.MIN_CLOSED_FILLS} 筆（樣本不足，不判定）"]
    if stats["sample_truncated"]:
        fail(f"{xcfg.FILL_WINDOW_DAYS} 天窗內成交超過 "
             f"{xcfg.FILL_PAGE_CAP * config.MAX_USER_FILLS:,} 筆（分頁上限，"
             "屬做市／高頻型，非可跟單對象）", is_hard=True)
    if stats["span_days"] < xcfg.MIN_SPAN_DAYS:
        fail(f"活躍跨度 {stats['span_days']:.0f} < {xcfg.MIN_SPAN_DAYS} 天")

    # ── 總損益（已實現＋未實現）─────────────────────────────────────────
    realized = stats["net_closed_pnl"]
    unreal = stats.get("unrealized_pnl")
    total = realized + unreal if unreal is not None else realized
    stats["total_pnl"] = total
    if total < xcfg.MIN_NET_PNL:
        label = "總損益（含未實現）" if unreal is not None else "已實現損益（未實現資料缺）"
        fail(f"{xcfg.DEX} {label} ${total:,.0f} < ${xcfg.MIN_NET_PNL:,.0f}")

    # ── 抱虧不認：未實現虧損吃掉多少已實現獲利 ──────────────────────────
    if unreal is not None and unreal < 0 and realized > 1e-9:
        share = abs(unreal) / realized
        stats["unrealized_loss_share"] = share
        if share > xcfg.MAX_UNREALIZED_LOSS_SHARE:
            fail(f"未實現虧損 ${abs(unreal):,.0f} 吃掉已實現獲利的 {share:.0%}"
                 f" > {xcfg.MAX_UNREALIZED_LOSS_SHARE:.0%}（抱虧不認，已實現數字失真）",
                 is_hard=True)

    # ── 賠率：主關卡 ────────────────────────────────────────────────────
    wtl = stats.get("win_to_loss_ratio")
    if wtl is None:
        fail("樣本內沒有任何虧損平倉，算不出賠率——可能從不認賠，不予判定",
             is_hard=True)
    elif wtl < xcfg.MIN_WIN_TO_LOSS:
        fail(f"賠率（平均獲利÷平均虧損）{wtl:.2f} < {xcfg.MIN_WIN_TO_LOSS}"
             "（賺的沒有顯著大於虧的）")

    # ── 避免大虧 ────────────────────────────────────────────────────────
    worst = stats.get("worst_loss_share_of_profit")
    if worst is not None and worst > xcfg.MAX_WORST_LOSS_SHARE:
        fail(f"單筆最大虧損 ${stats['worst_loss']:,.0f} 佔毛利 {worst:.0%}"
             f" > {xcfg.MAX_WORST_LOSS_SHARE:.0%}（出現過大虧）")

    # ── 其餘 ────────────────────────────────────────────────────────────
    pf = stats["profit_factor"]
    if pf is None or pf < xcfg.MIN_PROFIT_FACTOR:
        fail(f"獲利因子 {pf if pf is None else round(pf, 2)} < {xcfg.MIN_PROFIT_FACTOR}")
    wr = stats["win_rate"]
    if wr is None or wr < xcfg.MIN_WIN_RATE:
        fail(f"勝率 {'?' if wr is None else format(wr, '.1%')} < {xcfg.MIN_WIN_RATE:.0%}"
             "（樂透型下限，非主關卡）")
    top = stats["top_trade_share_of_profit"]
    if top is not None and top > xcfg.MAX_TOP_TRADE_SHARE:
        fail(f"單筆最大獲利占毛利 {top:.0%} > {xcfg.MAX_TOP_TRADE_SHARE:.0%}（一次好運）",
             is_hard=True)
    if stats["n_liquidations"] >= xcfg.MAX_LIQUIDATIONS:
        fail(f"強平 {stats['n_liquidations']} 次 >= {xcfg.MAX_LIQUIDATIONS}", is_hard=True)
    if stats["days_since_last_fill"] is not None and \
            stats["days_since_last_fill"] > xcfg.MAX_IDLE_DAYS:
        fail(f"最後成交距今 {stats['days_since_last_fill']:.0f} 天 "
             f"> {xcfg.MAX_IDLE_DAYS}（已停手）")

    if not reasons:
        return "winner", []
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
        f"- {dex} 總損益 **{_fmt_money(s.get('total_pnl'))}**"
        f"（已實現 {_fmt_money(s['net_closed_pnl'])}"
        f"＋未實現 {_fmt_money(r.get('unrealized_pnl'))}）"
        f"｜獲利因子 {_num(s['profit_factor'])}｜勝率 {_pct(s['win_rate'])}"
        f"（{s['n_closed_fills']} 筆平倉）",
        f"- **賠率 {_num(s.get('win_to_loss_ratio'))}**"
        + (" ⭐" if (s.get("win_to_loss_ratio") or 0) >= xcfg.STRONG_WIN_TO_LOSS else "")
        + f"（平均獲利 {_fmt_money(s['avg_win'])} ÷ 平均虧損 {_fmt_money(s['avg_loss'])}）"
        f"｜單筆最大虧損 {_fmt_money(s.get('worst_loss'))}"
        f"（佔毛利 {_pct(s.get('worst_loss_share_of_profit'), 0)}）",
        f"- {dex} 帳戶淨值 {_fmt_money(r['account_value'])}"
        f"｜目前 {r['n_positions']} 個部位・名目 {_fmt_money(r['position_value'])}"
        f"・實質槓桿 {_num(r.get('leverage_now'))}x",
        f"- {dex} 成交 {s['n_fills_dex']} 筆（占全部 {_pct(s['dex_share_of_fills'], 0)}）"
        f"｜近 30 天 {s['n_fills_dex_30d']} 筆｜{s['n_coins']} 個合約"
        f"｜跨度 {s['span_days']:.0f} 天｜最後成交 {s['days_since_last_fill']} 天前",
        f"- L1 取樣窗內出現 {r.get('trades_in_window', '?')} 次"
        "（次數低＝非做市型，本掃描刻意優先驗證低頻端）",
        f"- 強平 {s['n_liquidations']} 次｜單筆最大獲利占毛利 "
        f"{_pct(s['top_trade_share_of_profit'], 0)}"
        + ("｜⚠ 成交填滿分頁上限（做市／高頻型）" if s["sample_truncated"] else ""),
    ]


def render_report(result):
    dex = result["dex"]
    L = [f"# {dex} builder dex 贏家掃描 — {result['generated_at'][:16]}Z", "",
         "## 漏斗", "",
         "| 層 | 方法 | 進 | 出 |", "|---|---|---:|---:|",
         f"| L1 母體 | {result['l1_method']} | — | {result['l1_addresses']} |",
         f"| L1 排序 | 窗內成交次數**低頻優先**（避開做市型帳戶） | "
         f"{result['l1_addresses']} | 取前 {xcfg.L1_MAX_ADDRESSES} |",
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
          f"- **賠率（平均獲利÷平均虧損）≥ {xcfg.MIN_WIN_TO_LOSS}**，達 "
          f"{xcfg.STRONG_WIN_TO_LOSS} 標 ⭐——主關卡，對應「大賺、小賺、小虧」",
          f"- **單筆最大虧損佔毛利 ≤ {_pct(xcfg.MAX_WORST_LOSS_SHARE, 0)}**——對應「避免大虧」",
          f"- **總損益（已實現＋未實現）≥ {_fmt_money(xcfg.MIN_NET_PNL)}**；未實現虧損"
          f"吃掉已實現獲利逾 {_pct(xcfg.MAX_UNREALIZED_LOSS_SHARE, 0)} → 硬性淘汰"
          "（抱虧不認：只算 closedPnl 的話，從不認賠的人數字會完美無瑕）",
          f"- 獲利因子 ≥ {xcfg.MIN_PROFIT_FACTOR}（地板）、勝率 ≥ "
          f"{_pct(xcfg.MIN_WIN_RATE, 0)}（僅排除樂透型，非主關卡——勝率與賠率在數學上"
          "耦合，同時要求兩者高等於要求極端值，會把最會賺的人擋掉）",
          f"- 單筆最大獲利占毛利 ≤ {_pct(xcfg.MAX_TOP_TRADE_SHARE, 0)}"
          f"、強平 < {xcfg.MAX_LIQUIDATIONS} 次",
          f"- 最後成交 ≤ {xcfg.MAX_IDLE_DAYS} 天前",
          f"- 成交樣本＝userFillsByTime 分頁抓近 {xcfg.FILL_WINDOW_DAYS} 天；"
          f"填滿 {xcfg.FILL_PAGE_CAP} 頁上限（{xcfg.FILL_PAGE_CAP * config.MAX_USER_FILLS:,} 筆）"
          "＝做市／高頻型，一律不判 winner",
          "",
          "### 已知的取樣限制（誠實揭露）", "",
          "從公開成交流取樣，**被抓到的機率與交易頻率成正比**——真正低頻的慢錢"
          "（幾天才動一次）在幾分鐘的收集窗裡可能完全沒出現。所以「0 winner」的正確"
          "讀法是「這批被抓到的活躍帳戶裡沒有可跟對象」，不是「xyz 上沒有贏家」。"
          "要覆蓋更慢的族群，得拉長收集窗（多次執行累積母體），不是放寬判準。", "",
          "唯讀掃描：只查公開 info API 與公開 trades 頻道，無下單／簽章／私鑰。"]
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

    l1_method, seen = f"WS trades（{args.ws_seconds}s）", Counter()
    if coins and args.ws_seconds > 0:
        seen, _ = collect_via_websocket(coins, args.ws_seconds, meta, ws_factory=ws_factory)
    if len(seen) < xcfg.L1_MIN_ADDRESSES:
        extra = collect_via_leaderboard(meta, get_fn=get_fn)
        if extra:
            l1_method = (f"WS trades（{len(seen)} 個）＋排行榜備援（{len(extra)} 個）"
                         if seen else "排行榜備援（WS 無母體）")
            for a, c in extra.items():
                seen.setdefault(a, c)

    # 關鍵排序：**窗內成交次數少的優先**。從成交流取樣天生偏向高頻做市型帳戶，
    # 第一版沒排序（照 hex 字串排）→ L3 預算全花在做市商身上，54 個全部樣本觸頂。
    # 本專案的結論是只有慢錢可跟，所以這裡刻意把預算導向低頻端。
    ordered = sorted(seen.items(), key=lambda kv: (kv[1], kv[0]))
    if seen:
        counts = sorted(seen.values())
        med = counts[len(counts) // 2]
        meta.note(f"窗內成交次數分布：median {med}、最高 {counts[-1]}"
                  f"；只出現 1 次的 {sum(1 for c in counts if c == 1)} 個"
                  f"（L1 優先送低頻端，避開做市型帳戶）")
    addrs = [a for a, _ in ordered][: xcfg.L1_MAX_ADDRESSES]

    survivors = screen_addresses(addrs, meta, post_fn=post_fn)
    for row in survivors:
        row["trades_in_window"] = seen.get(row["address"], 0)

    wallets = []
    now_sec = time.time()
    for row in survivors:
        raw, hit_cap = fetch_fills_window(row["address"], meta, post_fn=post_fn)
        if not raw:
            continue
        stats = dex_fill_stats(classify.parse_fills(raw), xcfg.DEX, now_sec=now_sec,
                              window_days=xcfg.FILL_WINDOW_DAYS, truncated=hit_cap)
        # L2 的 clearinghouseState(dex=xyz) 已帶回當下未實現損益，注入後 judge 才看得到
        # 「已實現漂亮但帳面在虧」的抱虧不認型（只算 closedPnl 的盲點）。
        stats["unrealized_pnl"] = row.get("unrealized_pnl")
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
