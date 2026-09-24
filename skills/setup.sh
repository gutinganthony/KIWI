#!/bin/bash
# KIWI Skills 安裝腳本
# 用法：bash skills/setup.sh
# 把 skills/ 目錄下的所有 skill 安裝到 ~/.claude/skills/

SKILLS_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="$HOME/.claude/skills"

echo "=== KIWI Skills 安裝 ==="
echo "來源：$SKILLS_DIR"
echo "目標：$TARGET_DIR"
echo ""

mkdir -p "$TARGET_DIR"

installed=0
for skill_path in "$SKILLS_DIR"/*/; do
    skill_name=$(basename "$skill_path")
    # 跳過非 skill 目錄（沒有 SKILL.md 的）
    if [ ! -f "$skill_path/SKILL.md" ]; then
        continue
    fi
    dest="$TARGET_DIR/$skill_name"
    mkdir -p "$dest"
    cp "$skill_path/SKILL.md" "$dest/SKILL.md"
    # 有附程式的 skill（目前只有 llm-council 的 scripts/query_llms.py）要連程式一起裝，
    # 否則 SKILL.md 裝好了、叫的腳本卻不存在。只複製 scripts/，不複製其他資料檔
    # （例如 serenity 的 holdings.md／watchlist.md），避免在 ~/.claude 留下會過期的副本。
    if [ -d "$skill_path/scripts" ]; then
        rm -rf "$dest/scripts"
        cp -R "$skill_path/scripts" "$dest/scripts"
    fi
    echo "✓ 安裝：$skill_name"
    installed=$((installed + 1))
done

echo ""
echo "完成！安裝了 $installed 個 skill。"
echo "請重啟 Claude Code 讓 skill 生效。"
