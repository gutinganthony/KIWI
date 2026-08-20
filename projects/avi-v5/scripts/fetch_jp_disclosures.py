#!/usr/bin/env python3
"""日本個股開示資料橋 + 出場條件監控（在 GitHub Actions runner 上跑）。

為什麼重寫（2026-08-19）：舊版以 irbank.net 為資料源，**在 runner 上一樣 403**
——證據是 2026-07-28 落地的 6855_JEM.md、6834_Seikoh.md 全檔只有兩行
「HTTPError: HTTP Error 403: Forbidden URL=https://irbank.net/...」，
整整三週沒人發現（管線是好的，壞的是資料源）。
改用 TDnet：`agents/LEARNINGS.md` 2026-08-09 實測 runner 對
`www.release.tdnet.info` 的一覽頁與決算短信 PDF 皆回 HTTP 200。

本橋現在做兩件事：
  ① **開示抓取**：掃 TDnet 適時開示一覽，累積目標代碼的開示清單（含 PDF 連結）。
     用途：JEM 否證 #1（再增資/CB/業績下修）、各檔裁判日的原文來源。
  ② **出場條件監控**：對 6981 村田 / 6857 Advantest 抽決算短信數字，
     產出 `EXIT_MONITOR.md`——補 `skills/serenity/exit-playbook.md` §7 缺口③
     （「村田與 Advantest 的觸發條件缺自動監控」）。

⚠️ **三個設計約束，改本檔前先讀**：
  1. **狀態檔必須是 `.md`**。`update-dashboard.yml` 的 commit 段只有
     `git add projects/avi-v5/data/ext/jp_disclosures/*.md`——**寫成 .json 會不進版控**，
     等於沒做（同 LEARNINGS 2026-07-27 的坑）。狀態存在 `_state.md` 的 ```json 區塊裡。
  2. **exit code 恆為 0**。本檔是側掛在 fetch_backtest_ext.py 的 best-effort 任務，
     絕不可弄壞宿主 job。
  3. **雲端 session 測不了**（本站對 agent proxy 403，實測回 000）。
     解析邏輯用 `--selftest` 對內建 fixture 離線驗證；**live 行為只能在 runner 上驗收**。

用法：
  python3 scripts/fetch_jp_disclosures.py [--days 7] [--code 6981] [--force]
  python3 scripts/fetch_jp_disclosures.py --selftest    # 離線解析自測，不連網
"""

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "ext" / "jp_disclosures"
STATE = OUT / "_state.md"
MONITOR = OUT / "EXIT_MONITOR.md"

TDNET_LIST = "https://www.release.tdnet.info/inbs/I_list_{page:03d}_{ymd}.html"
TDNET_DOC = "https://www.release.tdnet.info/inbs/{docid}"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# 目標代碼。TDnet 的 kjCode 是 5 碼（4 碼代碼 + 尾碼 0），比對時取前 4 碼。
TARGETS = {
    "6855": {"name": "JEM", "why": "否證 #1 再增資/CB/業績下修"},
    "6834": {"name": "Seikoh", "why": "加碼 A 裁判日、9/1 分割"},
    "6777": {"name": "santec", "why": "🟢 觸發中，事件面追蹤"},
    "6981": {"name": "Murata", "why": "🔻 2026-08 已強制出場 → 三條轉為 exit-playbook §2.3 的再進場檢核條件"},
    "6857": {"name": "Advantest", "why": "🔻 2026-08 已強制出場 → 四條轉為 exit-playbook §2.4 的再進場檢核條件"},
}

# 從決算短信 PDF 內文抽數字。值以「百万円」為多，這裡只抽原始字串與數值，
# 單位換算交給讀檔的人——**不要在這裡做聰明的單位推斷**（錯了看不出來）。
METRIC_PATTERNS = {
    "売上高": r"売上高[^\d\-−]{0,40}?([\d,]{4,})",
    "売上総利益": r"売上総利益[^\d\-−]{0,40}?([\d,]{4,})",
    "営業利益": r"営業利益[^\d\-−]{0,40}?([\d,]{4,})",
    "受注高": r"受注高[^\d\-−]{0,40}?([\d,]{4,})",
    "受注残高": r"受注残高[^\d\-−]{0,40}?([\d,]{4,})",
}

DISCLOSURE_FLAGS = [
    ("増資", "🚩 JEM 否證 #1：再增資"),
    ("新株予約権", "🚩 JEM 否證 #1：新股預約權/CB"),
    ("転換社債", "🚩 JEM 否證 #1：CB"),
    ("下方修正", "🚩 業績下修"),
    ("業績予想の修正", "⚠️ 業績預想修正（上/下修需看內文）"),
    ("決算短信", "📄 決算短信（本橋會嘗試抽數字）"),
    ("株式分割", "📌 股票分割（觸發價需換算）"),
    ("価格改定", "⚠️ 村田條件②相關：價格改定"),
]


def get(url, timeout=25, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "ja,en;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    if binary:
        return raw
    for enc in ("utf-8", "cp932", "euc-jp"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _txt(s):
    s = re.sub(r"(?s)<[^>]+>", "", s)
    return re.sub(r"[ \t　\r\n]+", " ", html.unescape(s)).strip()


def parse_list_page(htmls):
    """解析 TDnet 適時開示一覽頁 → [{time, code, name, title, docid}]。

    LEARNINGS 2026-08-09：一覽頁是 <tr> 內多個 <td class="kjTime/kjCode/kjName/kjTitle">，
    **用單一大 regex 跨欄比對會抓不到**——必須先 split <tr> 再逐列解析 td。
    """
    rows = []
    for chunk in re.split(r"(?i)<tr[^>]*>", htmls)[1:]:
        cells = {}
        for m in re.finditer(r'(?is)<td[^>]*class="(kj[A-Za-z]+)"[^>]*>(.*?)</td>', chunk):
            cells[m.group(1)] = m.group(2)
        if "kjCode" not in cells or "kjTitle" not in cells:
            continue
        code = _txt(cells["kjCode"])
        if not re.fullmatch(r"\d{4,5}", code):
            continue
        link = re.search(r'(?is)<a[^>]+href="([^"]+\.pdf)"', cells["kjTitle"])
        rows.append({
            "time": _txt(cells.get("kjTime", "")),
            "code": code,
            "code4": code[:4],
            "name": _txt(cells.get("kjName", "")),
            "title": _txt(cells["kjTitle"]),
            "docid": (link.group(1).rsplit("/", 1)[-1] if link else ""),
        })
    return rows


def extract_metrics(text):
    """從決算短信內文抽數字。抓不到就不放進 dict——**不要填 0 或 None 冒充有值**。"""
    out = {}
    for key, pat in METRIC_PATTERNS.items():
        m = re.search(pat, text)
        if m:
            try:
                out[key] = int(m.group(1).replace(",", ""))
            except ValueError:
                continue
    return out


_PDF_READER = "unset"  # "unset" | None（不可用）| PdfReader


def _pdf_reader():
    """取得 PdfReader，取不到回 None。整段用 BaseException 包，理由如下——

    ⚠️ **必須是 BaseException，不能只是 Exception**：2026-08-19 實測，環境若有損壞的
    系統 `cryptography`（缺 `_cffi_backend`），`from pypdf import PdfReader` 會拋
    pyo3 的 `PanicException`，而**它繼承 BaseException，`except Exception` 攔不住**。
    宿主 `fetch_backtest_ext.run_jp_bridge()` 的守衛正是 `except Exception`，
    漏過去就會打掛每日 dashboard job。本橋的設計約束 2（exit code 恆為 0）在此落實。
    """
    global _PDF_READER
    if _PDF_READER == "unset":
        try:
            from pypdf import PdfReader
            _PDF_READER = PdfReader
        except BaseException as e:  # noqa: BLE001 — 見上方說明，刻意攔到 BaseException
            print(f"⚠️ pypdf 不可用（{type(e).__name__}）：開示清單仍會產出，"
                  f"但決算短信數字抽取本輪停用")
            _PDF_READER = None
    return _PDF_READER


def pdf_text(raw):
    """決算短信 PDF → 文字。pypdf 不可用時回 None（不是空字串，要能分辨）。"""
    import io
    reader_cls = _pdf_reader()
    if reader_cls is None:
        return None
    try:
        reader = reader_cls(io.BytesIO(raw))
        return "\n".join((p.extract_text() or "") for p in reader.pages[:12])
    except BaseException:  # noqa: BLE001 — best-effort，同上：不可讓 panic 逃逸
        return None


def load_state():
    if not STATE.exists():
        return {"disclosures": {}, "metrics": {}}
    m = re.search(r"(?s)```json\n(.*?)\n```", STATE.read_text(encoding="utf-8"))
    if not m:
        return {"disclosures": {}, "metrics": {}}
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return {"disclosures": {}, "metrics": {}}


def save_state(state, now):
    STATE.write_text(
        "# _state — jp_disclosures 資料橋狀態（機器讀寫，勿手改）\n\n"
        f"> 更新：{now}。**存成 .md 是刻意的**——`update-dashboard.yml` 的 commit 段\n"
        "> 只 `git add .../jp_disclosures/*.md`，寫成 .json 會不進版控（LEARNINGS 2026-07-27）。\n\n"
        "```json\n" + json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True) + "\n```\n",
        encoding="utf-8")


def flags_for(title):
    return [label for kw, label in DISCLOSURE_FLAGS if kw in title]


def render_code_md(code, meta, items, now):
    lines = [f"# {code} {meta['name']} — TDnet 適時開示累積清單",
             "",
             f"> 由 `fetch_jp_disclosures.py` 在 GitHub Actions runner 抓取"
             f"（雲端 session 對 TDnet 403，實測回 000）。更新：{now}",
             f"> 用途：{meta['why']}",
             "",
             "⚠️ **TDnet 一覽頁只保留約 31 天**，本檔為累積結果——早於本橋建立日的開示不會有。",
             ""]
    if not items:
        lines += ["（目前尚無累積到的開示。若連續多次執行後仍為空，"
                  "先確認 runner 對 TDnet 的可達性——不要假設「沒開示」。）", ""]
    else:
        lines += ["| 日期 | 時間 | 標題 | 標記 | PDF |", "|---|---|---|---|---|"]
        for it in sorted(items, key=lambda x: (x["date"], x["time"]), reverse=True):
            fl = " ".join(it.get("flags", [])) or "—"
            pdf = f"[原文]({TDNET_DOC.format(docid=it['docid'])})" if it.get("docid") else "—"
            lines.append(f"| {it['date']} | {it['time']} | {it['title']} | {fl} | {pdf} |")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------- 出場監控

def _trend(series):
    """series: [(date, value), ...] 已排序。回 (方向, 說明)。"""
    if len(series) < 3:
        return "無法判定", f"樣本 {len(series)} 期（<3，算不出「連兩季」）"
    (_, a), (_, b), (_, c) = series[-3:]
    if a > b > c:
        return "🔴 連兩期下行", f"{a} → {b} → {c}"
    if a < b < c:
        return "🟢 連兩期上行", f"{a} → {b} → {c}"
    return "🟡 未成序列", f"{a} → {b} → {c}"


def render_monitor(state, now):
    met = state.get("metrics", {})

    def series(code, key):
        rows = met.get(code, [])
        out = [(r["date"], r["values"][key]) for r in rows if key in r.get("values", {})]
        return sorted(out)

    adv_gm = []
    for r in sorted(met.get("6857", []), key=lambda x: x["date"]):
        v = r.get("values", {})
        if v.get("売上高") and v.get("売上総利益"):
            adv_gm.append((r["date"], round(100 * v["売上総利益"] / v["売上高"], 2)))
    adv_dir, adv_note = _trend(adv_gm)

    mur = series("6981", "受注残高")
    mur_dir, mur_note = _trend(mur)

    return "\n".join([
        "# EXIT_MONITOR — 村田 6981 ／ Advantest 6857 條件自動監控",
        "",
        f"> 由 `fetch_jp_disclosures.py` 產出。更新：{now}",
        "> 補 `skills/serenity/exit-playbook.md` §7 缺口③。**權威條件定義仍在 exit-playbook §2.3／§2.4，本檔只報數字。**",
        "",
        "> 🔻 **2026-08 用途變更**：兩檔已因家庭資金需求**強制出場（非框架因素）**，"
        "本檔監控的因此**不再是出場條件，而是再進場評估的輸入**。要重新建倉須重跑 Serenity Step 1–9，"
        "**不可用本檔的綠燈當建倉理由**——這些條件的角色是「建倉之後」的出場線。",
        "",
        "## ⚠️ 先讀：這 7 條裡只有 2 條能真的自動化",
        "",
        "| 分級 | 條件 | 為什麼 |",
        "|---|---|---|",
        "| **A 可全自動** | Advantest 毛利率連兩季反轉下行 | 決算短信有 売上高／売上総利益，可直接算 |",
        "| **A 可全自動** | 村田 受注残（比值） | 決算短信/補足資料有 受注残高 |",
        "| **B 半自動** | 村田 7/1 漲價被撤回或折讓 | 只能靠開示標題含「価格改定」觸發人工判讀 |",
        "| **B 半自動** | Teradyne SoC/GPU 份額連兩季上升 | 需 TER 季報拆分，且雙方未必揭露可比份額 |",
        "| **C 不可自動** | NVIDIA 週期暫停 | 新聞/節奏判斷，無結構化來源 |",
        "| **D 已有燈** | AI capex 指引下修（村田③／Advantest④＝T6） | 週報宏觀燈已涵蓋，**不重複造** |",
        "",
        "**因此本檔不是「自動賣訊」，是「把能算的算出來、把該人工看的標出來」。**",
        "",
        "## A 級：自動判定結果",
        "",
        "### Advantest 6857 — 毛利率（exit-playbook §2.4 條件②「毛利率連兩季反轉下行」）",
        f"- 判定：**{adv_dir}**",
        f"- 序列（毛利率 %）：{adv_note}",
        "- ⚠️ 「連兩季」是 exit-playbook 自訂的量化修飾（原 watchlist 無時間長度），"
        "本檔沿用該定義：需 3 期資料才成立。",
        "- ⚠️ 売上総利益 通常**不在決算短信首頁摘要**，在後段連結損益計算書；"
        "抽取為 best-effort，**首次有數字時務必人工核對一次原文 PDF**。",
        "",
        "### 村田 6981 — 受注残高（exit-playbook §2.3 條件①）",
        f"- 判定：**{mur_dir}**",
        f"- 序列（受注残高，原始單位）：{mur_note}",
        "- 🔧 **門檻「受注残比 <1.0」是 exit-playbook 自訂、原始文件查無出處**"
        "（原文只有現值 1.27／2018 峰 1.25）。**本檔只報趨勢，不代為判定觸發。**",
        "",
        "## B/C 級：需人工判讀（本橋只負責把原文找出來）",
        "",
        "見各代碼的 `<code>_<name>.md`，標記欄含 ⚠️/🚩 者即為需判讀項。",
        "",
        "## 驗收狀態",
        "",
        "- [ ] **runner live 驗收未完成**：本檔的解析邏輯僅經 `--selftest` 離線驗證；"
        "雲端 session 對 TDnet 回 000，無法實測。**合併 main 後看本檔有沒有出現真實數字。**",
        "- 驗收句（同 LEARNINGS 2026-07-27）：**repo 裡這個檔有沒有非空的序列**，"
        "不是「腳本有沒有跑成功」。",
        "",
    ])


# ---------------------------------------------------------------- selftest

FIXTURE = """
<table><tr><td class="kjTime">09:00</td><td class="kjCode">68570</td>
<td class="kjName">アドバンテスト</td>
<td class="kjTitle"><a href="140120260813512345.pdf">2027年3月期 第1四半期決算短信〔ＩＦＲＳ〕（連結）</a></td></tr>
<tr><td class="kjTime">15:30</td><td class="kjCode">69810</td>
<td class="kjName">村田製作所</td>
<td class="kjTitle"><a href="140120260805598765.pdf">価格改定に関するお知らせ</a></td></tr>
<tr><td class="kjTime">16:00</td><td class="kjCode">68550</td>
<td class="kjName">日本電子材料</td>
<td class="kjTitle"><a href="140120260807511111.pdf">業績予想の修正に関するお知らせ</a></td></tr>
<tr><td class="kjTime">10:00</td><td class="kjCode">12345</td>
<td class="kjName">無関係</td><td class="kjTitle">その他</td></tr></table>
"""

FIXTURE_PDF_TEXT = """
連結損益計算書
売上高 　　　　　　 185,432
売上総利益 　　　　 108,765
営業利益 　　　　　  74,210
受注残高 　　　　　 412,000
"""


def selftest():
    rows = parse_list_page(FIXTURE)
    assert len(rows) == 4, f"應解析 4 列，實得 {len(rows)}"
    adv = [r for r in rows if r["code4"] == "6857"]
    assert len(adv) == 1 and adv[0]["docid"] == "140120260813512345.pdf", adv
    assert "決算短信" in adv[0]["title"], adv[0]["title"]
    mur = [r for r in rows if r["code4"] == "6981"][0]
    assert "⚠️ 村田條件②相關：價格改定" in flags_for(mur["title"]), flags_for(mur["title"])
    jem = [r for r in rows if r["code4"] == "6855"][0]
    assert any("業績" in f for f in flags_for(jem["title"])), flags_for(jem["title"])
    assert [r for r in rows if r["code4"] == "1234"], "非目標代碼也應被解析（過濾在後段）"

    m = extract_metrics(FIXTURE_PDF_TEXT)
    assert m["売上高"] == 185432 and m["売上総利益"] == 108765, m
    assert m["受注残高"] == 412000, m
    assert round(100 * m["売上総利益"] / m["売上高"], 2) == 58.65, m

    # 趨勢：不足 3 期必須說「無法判定」，不可猜
    assert _trend([("a", 60.0), ("b", 59.0)])[0] == "無法判定"
    assert _trend([("a", 60.0), ("b", 59.0), ("c", 58.0)])[0] == "🔴 連兩期下行"
    assert _trend([("a", 58.0), ("b", 59.0), ("c", 60.0)])[0] == "🟢 連兩期上行"
    assert _trend([("a", 60.0), ("b", 58.0), ("c", 59.0)])[0] == "🟡 未成序列"
    print("✅ selftest 全過（解析 / 抽數 / 趨勢 / 標記）")
    return 0


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7, help="回掃天數（TDnet 只留約 31 天）")
    ap.add_argument("--code", help="只處理單一代碼")
    ap.add_argument("--force", action="store_true", help="忽略已抓過的 docid，重抓 PDF")
    ap.add_argument("--selftest", action="store_true", help="離線解析自測，不連網")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    state = load_state()
    state.setdefault("disclosures", {})
    state.setdefault("metrics", {})
    codes = [args.code] if args.code else list(TARGETS)
    seen_docids = {d["docid"] for c in state["disclosures"].values() for d in c if d.get("docid")}

    new_rows, pages_ok, pages_fail = [], 0, 0
    for back in range(args.days):
        ymd = (datetime.now(timezone.utc) - timedelta(days=back)).strftime("%Y%m%d")
        for page in range(1, 12):
            url = TDNET_LIST.format(page=page, ymd=ymd)
            try:
                htmls = get(url)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    break  # 該日頁數用盡
                pages_fail += 1
                break
            except Exception:  # noqa: BLE001
                pages_fail += 1
                break
            pages_ok += 1
            rows = parse_list_page(htmls)
            if not rows:
                break
            for r in rows:
                if r["code4"] in codes:
                    r["date"] = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
                    r["flags"] = flags_for(r["title"])
                    new_rows.append(r)
            time.sleep(1.2)

    if pages_ok == 0:
        print(f"⚠️ TDnet 一覽頁 0 頁成功（失敗 {pages_fail}）——"
              f"**先確認 runner 可達性，不要當成「沒有開示」**")

    added = 0
    for r in new_rows:
        bucket = state["disclosures"].setdefault(r["code4"], [])
        if any(d.get("docid") == r["docid"] and d.get("date") == r["date"] for d in bucket):
            continue
        bucket.append({k: r[k] for k in ("date", "time", "title", "docid", "flags")})
        added += 1

        if "決算短信" in r["title"] and r["docid"] and (args.force or r["docid"] not in seen_docids):
            try:
                text = pdf_text(get(TDNET_DOC.format(docid=r["docid"]), binary=True))
            except Exception:  # noqa: BLE001
                text = None
            if text is None:
                print(f"⚠️ {r['code4']} {r['docid']}：PDF 取得或解析失敗"
                      f"（pypdf 缺席？runner 需 `pip install --user pypdf`）")
            else:
                vals = extract_metrics(text)
                if vals:
                    state["metrics"].setdefault(r["code4"], []).append(
                        {"date": r["date"], "docid": r["docid"], "values": vals})
                    print(f"📄 {r['code4']} {r['date']} 抽到 {list(vals)}")
                else:
                    print(f"⚠️ {r['code4']} {r['docid']}：PDF 有文字但抽不到任何指標"
                          f"（格式可能不同，需人工看原文）")
            time.sleep(1.2)

    for code in codes:
        meta = TARGETS.get(code)
        if not meta:
            print(f"⚠️ 未知代碼 {code}，跳過")
            continue
        (OUT / f"{code}_{meta['name']}.md").write_text(
            render_code_md(code, meta, state["disclosures"].get(code, []), now), encoding="utf-8")

    MONITOR.write_text(render_monitor(state, now), encoding="utf-8")
    save_state(state, now)
    print(f"jp_disclosures: 頁 {pages_ok} 成功/{pages_fail} 失敗、新增開示 {added} 筆 @ {now}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
