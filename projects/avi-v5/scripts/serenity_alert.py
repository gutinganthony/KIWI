#!/usr/bin/env python3
"""Diff two Serenity data.json snapshots and emit an alert line-set for ACTIONABLE
changes ONLY. Empty output = nothing worth pinging about (so the caller stays silent).

What counts as actionable (matches the user's ask 「重大變化或燈號轉換」):
  1. 宏觀燈號翻轉  — a macro signal's state changed (ok/watch/alert enum flip)
  2. 🟢/🔴 觸發    — a position newly gained a 🟢 (buy/trigger hit) or 🔴 (sell/falsify) in its direction
  3. 🔀 分層變動   — a position moved tier (e.g. trigger→buy, or a holding flipped)
  4. 📊/🟣 大跳動  — a position's weekly move newly carries the >15% 🚩 flag
  5. 🟣 持倉變化   — any holding-tier position whose direction text changed

Design: pure stdlib, best-effort — never raises (a crashing alert step would only
mask the run). Prints alert to stdout (one line per item) or nothing.

Usage: python3 serenity_alert.py OLD_data.json NEW_data.json
"""
import json
import sys

SEV = {"ok": 0, "watch": 1, "alert": 2}
DOT = {"ok": "🟢", "watch": "🟡", "alert": "🔴"}


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def by_key(items, key):
    return {it.get(key): it for it in (items or []) if it.get(key)}


def main():
    if len(sys.argv) < 3:
        return
    old, new = load(sys.argv[1]), load(sys.argv[2])
    lines = []

    # 1) Macro light flips (the controlled ok/watch/alert enum = low-noise, high-signal)
    om = by_key(old.get("macro"), "signal")
    for sig, m in by_key(new.get("macro"), "signal").items():
        ns, os_ = m.get("state"), om.get(sig, {}).get("state")
        if os_ and ns and os_ != ns:
            trend = "⚠️ 惡化" if SEV.get(ns, 0) > SEV.get(os_, 0) else "改善"
            note = (m.get("note") or "")[:70]
            lines.append(f"燈號翻轉：{sig} {DOT.get(os_,'')}{os_}→{DOT.get(ns,'')}{ns}（{trend}）｜{note}")

    # 2-5) Position-level changes, matched by ticker
    op = by_key(old.get("positions"), "ticker")
    for tk, p in by_key(new.get("positions"), "ticker").items():
        o = op.get(tk, {})
        name = p.get("name", tk)
        price = p.get("price", "")
        d_new, d_old = p.get("direction", ""), o.get("direction", "")
        wk_new, wk_old = str(p.get("wk", "")), str(o.get("wk", ""))
        holding = p.get("tier") == "holding"

        # newly-appearing 🟢 / 🔴 in the direction field
        for emo, label in (("🔴", "賣出/否證"), ("🟢", "買進/觸發")):
            if emo in d_new and emo not in d_old:
                lines.append(f"{emo} {label}命中：{name}（{tk}）｜{d_new[:36]}｜現價 {price}")

        # tier change
        if o.get("tier") and o.get("tier") != p.get("tier"):
            lines.append(f"🔀 分層變動：{name}（{tk}）{o.get('tier')}→{p.get('tier')}")

        # newly-flagged >15% move
        if "🚩" in wk_new and "🚩" not in wk_old:
            tag = "🟣 持倉大跳動" if holding else "📊 大跳動"
            lines.append(f"{tag}：{name}（{tk}）{wk_new}｜現價 {price}")

        # holding tier: any direction-text change is worth surfacing to the owner
        if holding and d_old and d_new != d_old and "🟢" not in d_new and "🔴" not in d_new:
            lines.append(f"🟣 持倉狀態變化：{name}（{tk}）→ {d_new[:50]}")

    # de-dup, preserve order
    seen, out = set(), []
    for ln in lines:
        if ln not in seen:
            seen.add(ln)
            out.append(ln)

    if out:
        print("\n".join(out))


if __name__ == "__main__":
    main()
