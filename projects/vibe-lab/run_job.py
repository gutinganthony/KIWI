#!/usr/bin/env python3
"""vibe-lab job runner:讀 job.json → 跑 vibe-trading CLI → 結果寫 results/。

設計原則(見 README.md):確定性功能、零 LLM key、輸出裁切防肥、
失敗也要留下可讀的結果檔(commit-back 步驟 if: always() 會照收)。
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
MAX_HEAD, MAX_TAIL = 500, 200          # 輸出裁切:頭/尾各留這麼多行
CLI_TIMEOUT = 2400                     # 單一 CLI 呼叫上限 40 分鐘(workflow 總限 45)

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def run_cli(args):
    env = dict(os.environ, NO_COLOR="1", TERM="dumb", COLUMNS="160")
    t0 = time.time()
    try:
        p = subprocess.run(args, capture_output=True, text=True,
                           timeout=CLI_TIMEOUT, env=env)
        return p.stdout, p.stderr, p.returncode, time.time() - t0
    except subprocess.TimeoutExpired as e:
        out = e.stdout if isinstance(e.stdout, str) else ""
        return out, f"TIMEOUT after {CLI_TIMEOUT}s", -1, time.time() - t0


def clip(text):
    lines = ANSI.sub("", text or "").splitlines()
    if len(lines) > MAX_HEAD + MAX_TAIL:
        omitted = len(lines) - MAX_HEAD - MAX_TAIL
        lines = lines[:MAX_HEAD] + ["", f"...[裁切 {omitted} 行]...", ""] + lines[-MAX_TAIL:]
    return "\n".join(lines)


def build_args(spec):
    jtype = spec.get("type", "")
    if jtype == "alpha-bench":
        return ["vibe-trading", "alpha", "bench",
                "--zoo", str(spec["zoo"]),
                "--universe", str(spec["universe"]),
                "--period", str(spec["period"]),
                "--top", str(spec.get("top", 20))]
    if jtype == "alpha-list":
        args = ["vibe-trading", "alpha", "list", "--limit", str(spec.get("limit", 20))]
        if spec.get("zoo"):
            args += ["--zoo", str(spec["zoo"])]
        return args
    return None


def main():
    spec = json.loads((HERE / "job.json").read_text(encoding="utf-8"))
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    RESULTS.mkdir(exist_ok=True)

    args = build_args(spec)
    if args is None:
        body = (f"# vibe-lab run {stamp}\n\n"
                f"不支援的 job type:`{spec.get('type')!r}`(v1 支援 alpha-bench / alpha-list)\n")
        (RESULTS / "latest.md").write_text(body, encoding="utf-8")
        print("unsupported job type", file=sys.stderr)
        return 1

    out, err, code, dur = run_cli(args)
    body = (f"# vibe-lab run {stamp}\n\n"
            f"- command:`{' '.join(args)}`\n"
            f"- exit:{code}・耗時 {dur:.0f}s\n"
            f"- spec:`{json.dumps(spec, ensure_ascii=False)}`\n\n"
            f"## stdout\n\n```\n{clip(out)}\n```\n\n"
            f"## stderr\n\n```\n{clip(err)}\n```\n")
    slug = f"{stamp}-{spec['type']}"
    (RESULTS / f"{slug}.md").write_text(body, encoding="utf-8")
    (RESULTS / "latest.md").write_text(body, encoding="utf-8")
    print(f"wrote results/{slug}.md (exit {code})")
    return 0 if code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
