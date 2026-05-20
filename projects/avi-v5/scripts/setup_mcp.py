#!/usr/bin/env python3
"""TradingView MCP 安裝設定精靈

執行這個腳本，它會：
1. 檢查所有套件是否安裝好
2. 自動偵測你的專案路徑
3. 印出你需要貼進 ~/.claude/settings.json 的完整設定內容

用法：
    cd ~/KIWI/projects/avi-v5
    python3 scripts/setup_mcp.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SEP = "=" * 60


def check(label: str, ok: bool, fix: str = "") -> bool:
    icon = "✅" if ok else "❌"
    print(f"  {icon}  {label}")
    if not ok and fix:
        print(f"       → 修復：{fix}")
    return ok


def main():
    print(SEP)
    print("  TradingView MCP 安裝設定精靈")
    print(SEP)

    all_ok = True

    # ── 1. Python 版本 ──
    print("\n【1】Python 版本")
    py_ok = sys.version_info >= (3, 9)
    all_ok &= check(
        f"Python {sys.version.split()[0]}",
        py_ok,
        fix="請升級到 Python 3.9 以上"
    )

    # ── 2. 套件檢查 ──
    print("\n【2】套件安裝狀態")
    packages = {
        "mcp": "pip3 install mcp",
        "playwright": "pip3 install playwright",
        "dotenv": "pip3 install python-dotenv",
        "yfinance": "pip3 install yfinance",
        "pandas": "pip3 install pandas",
        "fredapi": "pip3 install fredapi",
    }
    for pkg, fix in packages.items():
        try:
            __import__(pkg if pkg != "dotenv" else "dotenv")
            check(pkg, True)
        except ImportError:
            check(pkg, False, fix=fix)
            all_ok = False

    # ── 3. Playwright Chromium ──
    print("\n【3】Playwright Chromium 瀏覽器")
    try:
        from playwright.sync_api import sync_playwright
        _p = sync_playwright().start()
        exe = Path(_p.chromium.executable_path)
        chromium_ok = exe.exists()
        _p.stop()
    except Exception:
        chromium_ok = False

    check(
        "Chromium 已安裝",
        chromium_ok,
        fix="playwright install chromium"
    )
    if not chromium_ok:
        all_ok = False

    # ── 4. .env 檔案 ──
    print("\n【4】.env 設定")
    env_path = PROJECT_ROOT / ".env"
    env_exists = env_path.exists()
    check(
        f".env 檔案存在（{env_path}）",
        env_exists,
        fix=f'echo "FRED_API_KEY=你的KEY" > {env_path}'
    )
    if env_exists:
        content = env_path.read_text()
        fred_ok = "FRED_API_KEY" in content and len(content.strip()) > 20
        check(
            "FRED_API_KEY 已設定",
            fred_ok,
            fix=f"在 {env_path} 加入：FRED_API_KEY=你的KEY"
        )

    # ── 5. MCP 檔案結構 ──
    print("\n【5】MCP 檔案結構")
    files_to_check = [
        "mcp_tradingview/server.py",
        "mcp_tradingview/tradingview_bridge.py",
        "mcp_tradingview/tools/chart_tools.py",
        "mcp_tradingview/tools/pine_tools.py",
        "pine/cpi_indicator.pine",
        "pine/tsi_indicator.pine",
        "pine/avi_composite.pine",
        "src/pine_export.py",
    ]
    for f in files_to_check:
        exists = (PROJECT_ROOT / f).exists()
        check(f, exists, fix=f"git pull origin claude/tradingview-mcp-phase-5-wOPl8")
        all_ok &= exists

    # ── 6. 生成 settings.json 設定 ──
    print(f"\n{SEP}")
    print("  Claude Code MCP 設定")
    print(SEP)

    settings_path = Path.home() / ".claude" / "settings.json"
    cwd = str(PROJECT_ROOT)

    config_block = {
        "mcpServers": {
            "tradingview": {
                "command": "python",
                "args": ["mcp_tradingview/server.py"],
                "cwd": cwd,
                "env": {
                    "TV_SESSION_COOKIE": "【在這裡貼上你的 sessionid cookie】",
                    "TV_HEADLESS": "1",
                    "FRED_API_KEY": "8181079f96c8210790797e299aca965a"
                }
            }
        }
    }

    print(f"\n把下面這段設定加到：{settings_path}")
    print(f"（如果檔案不存在，直接新建就好）\n")
    print(json.dumps(config_block, indent=2, ensure_ascii=False))

    # ── 7. 如何取得 Session Cookie ──
    print(f"\n{SEP}")
    print("  如何取得 TradingView Session Cookie")
    print(SEP)
    print("""
  步驟：
  1. 用 Chrome 打開 https://www.tradingview.com 並登入
  2. 按 F12 打開開發者工具
  3. 點上方「Application」分頁（可能要點 >> 才看得到）
  4. 左側展開「Cookies」→ 點「https://www.tradingview.com」
  5. 在右側列表找到名稱是「sessionid」的那一行
  6. 複製「Value」欄位的內容（一長串英文數字）
  7. 貼到上方設定的 TV_SESSION_COOKIE 裡
""")

    # ── 8. 最終狀態 ──
    print(SEP)
    if all_ok:
        print("  ✅  所有檢查通過！設定好 settings.json 後就能使用。")
        print()
        print("  使用方式：在 Claude Code 對話裡說：")
        print("    「幫我更新 TradingView 的 AVI 指標」")
    else:
        print("  ❌  還有項目需要修復（看上方的修復指令）")
        print()
        print("  修復完成後再執行一次這個腳本確認：")
        print(f"    python3 {Path(__file__).name}")
    print(SEP)


if __name__ == "__main__":
    main()
