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
    echo "✓ 安裝：$skill_name"
    installed=$((installed + 1))
done

echo ""
echo "完成！安裝了 $installed 個 skill。"
echo "請重啟 Claude Code 讓 skill 生效。"
