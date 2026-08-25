#!/usr/bin/env python3
"""每週可重跑的雙線篩選（A 高檔強勢 / B 落後放量）。

用法：
    python3 weekly_screen.py                 # 增量更新價格後產生報告
    python3 weekly_screen.py --no-fetch      # 只用既有快取，不打 API
    python3 weekly_screen.py --full          # 全 universe 重抓（每月一次）

設計依據見 topics/business/2026-08-14-tw-surge-stock-anatomy.md 第二~四部。
三件事是規則的一部分，不可省略：
  1. 門檻每次重算（成交金額前 30% 的絕對值 2026H1 是 16 億、2026-08 是 4.24 億，差 4 倍）
  2. B 線只在多頭/打底完成後啟用（空頭期歷史表現是負的）
  3. 排除項只用來剔除，不用來排序
"""
import argparse, json, os, sys, time, statistics as st
import urllib.request, urllib.error

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get('SURGE_CACHE', os.path.join(BASE, 'cache'))
os.makedirs(CACHE, exist_ok=True)
sys.path.insert(0, BASE)
from adjust import shock_days, adjust                      # noqa: E402

API = ('https://api.finmindtrade.com/api/v4/data?dataset={ds}&data_id={sid}'
       '&start_date={a}&end_date={b}')
RATE_PER_HOUR = 700          # 免費層實測上限約 600-850/hr；超過會回 402/403
INTERVAL = 3600.0 / RATE_PER_HOUR
_next = [0.0]

def call(ds, sid, a, b):
    """FinMind 的配額狀態是用真正的 HTTP 402/403 回的，urlopen 會直接拋例外。"""
    for _ in range(40):
        w = max(0.0, _next[0] - time.time())
        if w: time.sleep(w)
        _next[0] = time.time() + INTERVAL
        try:
            r = json.load(urllib.request.urlopen(API.format(ds=ds, sid=sid, a=a, b=b), timeout=40))
            if r.get('status') == 200:
                return r.get('data', [])
            time.sleep(30)
        except urllib.error.HTTPError as e:
            body = {}
            try: body = json.loads(e.read().decode() or '{}')
            except Exception: pass
            wait = int(body.get('retry_after') or (900 if e.code == 403 else 300)) + 20
            print(f'  quota/ban ({e.code}), sleeping {wait}s', flush=True)
            time.sleep(wait)
        except Exception:
            time.sleep(20)
    return None

def universe():
    p = os.path.join(CACHE, 'info.json')
    if not os.path.exists(p):
        d = call('TaiwanStockInfo', '', '', '') or []
        json.dump(d, open(p, 'w'))
    d = json.load(open(p))
    meta = {}
    for r in d:
        sid = r.get('stock_id', '')
        if r.get('type') in ('twse', 'tpex') and len(sid) == 4 and sid.isdigit() and not sid.startswith('0'):
            meta.setdefault(sid, {'name': r.get('stock_name', ''), 'industry': r.get('industry_category', '')})
    return meta

def load_px():
    p = os.path.join(CACHE, 'px.json')
    return json.load(open(p)) if os.path.exists(p) else {}

def save_px(px):
    json.dump(px, open(os.path.join(CACHE, 'px.json'), 'w'), separators=(',', ':'))

def refresh(px, meta, full, today):
    """增量：只補快取最後一天之後的 bar。缺乏歷史的標的自動補滿 400 天。"""
    ids = sorted(meta)
    if not full:
        liquid = [s for s, d in px.items()
                  if d.get('m') and sum(d['m'][-20:])/20 >= 15_000_000]
        ids = sorted(set(liquid) | {s for s in ids if s not in px})
        print(f'增量更新 {len(ids)} 檔（流動性子集＋新標的）')
    else:
        print(f'全量更新 {len(ids)} 檔')
    for n, sid in enumerate(ids, 1):
        cur = px.get(sid)
        start = '2024-01-01' if not cur else cur['dt'][-1]
        d = call('TaiwanStockPrice', sid, start, today)
        if not d: continue
        new = {'dt': [x['date'] for x in d], 'h': [x['max'] for x in d], 'l': [x['min'] for x in d],
               'c': [x['close'] for x in d], 'v': [x['Trading_Volume'] for x in d],
               'm': [x['Trading_money'] for x in d]}
        if cur:
            keep = [i for i, dd in enumerate(new['dt']) if dd > cur['dt'][-1]]
            for k in ('dt', 'h', 'l', 'c', 'v', 'm'):
                cur[k] = (cur[k] + [new[k][i] for i in keep])[-500:]
        else:
            px[sid] = {k: new[k][-500:] for k in new}
        if n % 200 == 0:
            save_px(px); print(f'  {n}/{len(ids)}', flush=True)
    save_px(px)

def build(px, meta, shock):
    last = max(d['dt'][-1] for d in px.values() if d.get('dt'))
    rows = []
    for sid, d in px.items():
        # ETF 與非本表標的不進篩選（快取可能含有先前研究抓進來的 0xxx）
        if sid not in meta or sid.startswith('0'): continue
        if not d.get('dt') or d['dt'][-1] != last or len(d['c']) < 260: continue
        c, _ = adjust(d['dt'], d['c'], shock)
        i = len(c) - 1
        if c[i] <= 0: continue
        hi52 = max(c[i-239:i+1])
        rows.append({'id': sid, **meta.get(sid, {'name': '', 'industry': ''}),
                     'px': d['c'][i], 'turn20': sum(d['m'][i-19:i+1])/20,
                     'from52h': c[i]/hi52-1, 'ret60': c[i]/c[i-60]-1,
                     'ret120': c[i]/c[i-120]-1,
                     'ma60': c[i]/(sum(c[i-59:i+1])/60)-1})
    return last, rows

def regime(rows):
    med60 = st.median([x['ret60'] for x in rows])
    above = sum(1 for x in rows if x['ma60'] > 0)/len(rows)
    state = 'UP' if (med60 > 0 and above > 0.5) else ('DOWN' if (med60 < -0.05 or above < 0.35) else 'MIXED')
    return state, med60, st.median([x['ret120'] for x in rows]), above

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-fetch', action='store_true')
    ap.add_argument('--full', action='store_true')
    ap.add_argument('--today', default=time.strftime('%Y-%m-%d'))
    ap.add_argument('--out')
    a = ap.parse_args()

    meta = universe(); px = load_px()
    if not a.no_fetch: refresh(px, meta, a.full, a.today)
    tmp = os.path.join(CACHE, '_px.ndjson')
    with open(tmp, 'w') as fh:
        for sid, d in px.items():
            fh.write(json.dumps({'id': sid, **d}, separators=(',', ':')) + '\n')
    shock, _ = shock_days(tmp)
    last, rows = build(px, meta, shock)
    state, m60, m120, above = regime(rows)

    liq = [x for x in rows if x['turn20'] >= 20_000_000]
    for f in ('turn20', 'from52h'):
        v = sorted(liq, key=lambda x: x[f])
        for k, x in enumerate(v): x['p_'+f] = k/max(1, len(v)-1)
    tq = sorted(x['turn20'] for x in liq)
    cut = tq[int(len(tq)*0.70)]
    A = sorted([x for x in liq if x['p_from52h'] >= 0.80 and x['p_turn20'] >= 0.70],
               key=lambda x: -(x['p_from52h']+x['p_turn20']))
    B = sorted([x for x in liq if x['from52h'] <= -0.30 and x['p_turn20'] >= 0.70],
               key=lambda x: -x['p_turn20'])

    # 排除項需要籌碼，只對入選名單補抓
    need = [x['id'] for x in (A[:40] + B[:40])]
    chips = json.load(open(os.path.join(CACHE, 'chips.json'))) if os.path.exists(os.path.join(CACHE, 'chips.json')) else {}
    if not a.no_fetch:
        a0 = (time.strftime('%Y-%m-%d', time.localtime(time.time()-200*86400)))
        for sid in need:
            e = chips.setdefault(sid, {})
            if e.get('asof') == last: continue
            ii = call('TaiwanStockInstitutionalInvestorsBuySell', sid, a0, a.today) or []
            mg = call('TaiwanStockMarginPurchaseShortSale', sid, a0, a.today) or []
            agg = {}
            for x in ii:
                k = agg.setdefault(x['date'], 0)
                if x['name'] in ('Foreign_Investor', 'Foreign_Dealer_Self'):
                    agg[x['date']] = k + x['buy'] - x['sell']
            e['fi'] = [agg[k] for k in sorted(agg)][-60:]
            if mg and mg[-1].get('MarginPurchaseLimit'):
                sh = mg[-1]['MarginPurchaseLimit']*4
                e['mgpct'] = mg[-1]['MarginPurchaseTodayBalance']/sh*100
                e['srat'] = (mg[-1]['ShortSaleTodayBalance']/mg[-1]['MarginPurchaseTodayBalance']*100
                             if mg[-1]['MarginPurchaseTodayBalance'] else 0.0)
            e['asof'] = last
        json.dump(chips, open(os.path.join(CACHE, 'chips.json'), 'w'))
    for x in liq:
        e = chips.get(x['id'])
        if not e: continue
        d = px[x['id']]
        vol60 = sum(d['v'][-60:]) or 1
        if e.get('fi'): x['fi60_sh'] = sum(e['fi'])/vol60
        if e.get('mgpct') is not None: x['mgpct'] = e['mgpct']; x['srat'] = e.get('srat')
    fis = sorted(x['fi60_sh'] for x in liq if x.get('fi60_sh') is not None)
    ficut = fis[int(len(fis)*0.10)] if len(fis) >= 20 else None

    def rejected(x):
        bad = []
        if ficut is not None and x.get('fi60_sh') is not None and x['fi60_sh'] <= ficut: bad.append('外資墊底')
        if x.get('mgpct') is not None and x['mgpct'] > 6: bad.append(f"融資{x['mgpct']:.1f}%")
        if x.get('fi60_sh') is None or x.get('mgpct') is None: bad.append('籌碼n/a')
        return bad

    L = []
    L.append(f'# 台股雙線篩選 — {last}\n')
    L.append(f'*由 `projects/surge-scan/weekly_screen.py` 產生。規則依據見 '
             f'`topics/business/2026-08-14-tw-surge-stock-anatomy.md` §19–§25。非投資建議。*\n')
    L.append('## 市況判讀\n')
    L.append('| 指標 | 讀數 |\n|---|---|')
    L.append(f'| 個股 60 日報酬中位數 | {m60*100:+.1f}% |')
    L.append(f'| 個股 120 日報酬中位數 | {m120*100:+.1f}% |')
    L.append(f'| 站上 60 日均線比例 | {above*100:.0f}% |')
    L.append(f'| **判定** | **{state}** |')
    L.append(f'| **B 線開關** | **{"開啟" if state=="UP" else ("關閉" if state=="DOWN" else "謹慎/減碼")}** |\n')
    L.append(f'流動性門檻後 {len(liq)} 檔；**成交金額前 30% 門檻 = NT${cut/1e8:.2f} 億/日**'
             f'（此值每次重算，不可寫死）。\n')
    for title, lst, note in [
        ('A 線 高檔強勢（距 52 週高前 20% ＋ 成交金額前 30%）', A, ''),
        ('B 線 落後放量（距高 ≤ −30% ＋ 成交金額前 30%）', B,
         '' if state == 'UP' else f'\n> ⚠️ 市況判定為 {state}，**B 線應關閉**，以下僅供觀察。\n')]:
        L.append(f'## {title}\n{note}')
        L.append('| 代號 | 名稱 | 收盤 | 日均額(億) | 距52高 | 60日 | 外資60日 | 融資% | 券資% | 判定 |')
        L.append('|---|---|---|---|---|---|---|---|---|---|')
        for x in lst[:25]:
            bad = rejected(x)
            fi = f"{x['fi60_sh']*100:+.2f}%" if x.get('fi60_sh') is not None else 'n/a'
            mp = f"{x['mgpct']:.1f}" if x.get('mgpct') is not None else 'n/a'
            sr = f"{x['srat']:.1f}" if x.get('srat') is not None else 'n/a'
            L.append(f"| {x['id']} | {x['name']} | {x['px']:.1f} | {x['turn20']/1e8:.1f} | "
                     f"{x['from52h']*100:.0f}% | {x['ret60']*100:+.0f}% | {fi} | {mp} | {sr} | "
                     f"{'✅ 通過' if not bad else '❌ ' + '/'.join(bad)} |")
        L.append(f'\n{len(lst)} 檔命中，{len([x for x in lst if not rejected(x)])} 檔通過排除項。\n')
    L.append('## 使用限制（每次都要重讀）\n')
    L.append('1. **這是候選池，不是買進名單。** A 線樣本外「持有一年中位數 −3.9%」，只是優於基準 −10.1%。')
    L.append('   它提高的是抓到大波段的機率（16.6% vs 12.1%），不是勝率。')
    L.append('2. **尾部策略，必須分散。** A+B 合併清單中位數 +0.5%、平均 +38.7%、中位回檔 −30.8%。挑三檔重壓最可能虧錢。')
    L.append('3. **排除項只剔除、不排序。** 外資買超「多」沒有加分（信賴區間與基準重疊），只有「墊底」有意義。')
    L.append('4. **B 線的開關不能用個股籌碼判斷**（已檢定否決），只能用市況。')
    L.append('5. 規則以 2025-08 前的資料驗證，之後的清單無回測支撐；未計交易成本與滑價。')
    out = a.out or os.path.join(BASE, f'screen-{last}.md')
    open(out, 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L[:24]))
    print(f'\n寫出：{out}')

if __name__ == '__main__':
    main()
