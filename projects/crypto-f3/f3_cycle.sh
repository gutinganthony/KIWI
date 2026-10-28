#!/usr/bin/env bash
# F3 機器人「一輪」：跑機器人 → 更新監控資料 → 存狀態 → 需要時推 Telegram。
# 由 .github/workflows/f3-bot.yml 每小時呼叫一次。需要的環境變數：MODE、CAPITAL、PERSIST、RUN_URL、
# KIWI_F3_HOME（狀態資料夾的上一層，裡面是 f3-bot-state 分支的 worktree）、OKX_*／TELEGRAM_*（各自可選）。
# 回傳值：機器人本身失敗時回傳 1（已自己推過失敗通知）。
set -uo pipefail
cd "$(dirname "$0")/../.."
out="$(mktemp)"
# 先拉狀態分支：手動「解除風控」可能在循環進行中改過狀態
if [ "$PERSIST" = "true" ] && ! git -C "$KIWI_F3_HOME" pull --quiet --rebase origin f3-bot-state 2>/dev/null; then
  git -C "$KIWI_F3_HOME" rebase --abort 2>/dev/null || true   # 衝突時保留本機狀態，不要卡在 rebase 中
fi
notify() { [ "${EVENT:-}" = "push" ] && return 0; python3 projects/avi-v5/scripts/notify_ops.py --title "$1" --url "$RUN_URL" "${@:2}" || true; }

if ! python3 projects/crypto-f3/f3_okx_bot.py --mode "$MODE" --v2 --capital "$CAPITAL" 2>&1 | tee "$out"; then
  notify "❌ F3 2.0 機器人執行失敗（$MODE）" --body "這一輪沒有跑完，可能漏掉進出場。下一小時會再試一次。錯誤：$(tail -3 "$out")"
  exit 1
fi

kind=""
# 有進場／出場／錯誤／漏 K 線才推播；每天台北 08 點那一輪另外推一次持倉摘要
if grep -qE '【進場】|【出場】|【風控】|❌|⚠️' "$out"; then
  kind="event"
elif [ "$(date -u +%H)" = "00" ]; then
  kind="daily"
fi

if [ "$PERSIST" = "true" ]; then
  # 監控台資料（規則手冊 §16、§17）；失敗不影響交易，只在每日摘要附上
  mon="$(mktemp)"
  python3 projects/crypto-f3/f3_monitor.py --home "$KIWI_F3_HOME/$MODE-F3-2.0" --mode "$MODE" > "$mon" 2>&1 || echo "（監控資料這一輪更新失敗）" >> "$mon"
  cat "$mon"
  [ "$kind" = "daily" ] && { echo; echo "── 監控 ──"; cat "$mon"; } >> "$out"

  ( cd "$KIWI_F3_HOME"
    git add -A
    if ! git diff --cached --quiet; then
      git commit --quiet -m "f3-bot: $MODE $(date -u +%Y-%m-%dT%H:%MZ)"
      ok=0
      for i in 1 2 3; do git push --quiet origin f3-bot-state && { ok=1; break; }; sleep $((i * 5)); git pull --quiet --rebase origin f3-bot-state || git rebase --abort 2>/dev/null || true; done
      [ "$ok" = 1 ] || echo "⚠️ 狀態沒有推上 f3-bot-state，下一輪會再推"
    fi )
fi

case "$kind" in
  event) notify "🤖 F3 2.0（$MODE）有交易動作" < "$out" ;;
  daily) notify "📋 F3 2.0（$MODE）每日持倉摘要" < "$out" ;;
esac
exit 0
