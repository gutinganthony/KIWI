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
    # ⚠️ 2026-09-04 修正：原本只 cp SKILL.md，會讓帶 scripts/ 的 skill 裝成半殘
    #（llm-council 的 SKILL.md 叫你跑 scripts/query_llms.py，但那支檔案根本沒被複製過去）。
    # 改為整個資料夾同步，並先清掉舊版避免留下孤兒檔。
    rm -rf "$dest"
    cp -R "$skill_path" "$dest"
    extra=""
    if [ -d "$dest/scripts" ]; then
        chmod +x "$dest"/scripts/*.py 2>/dev/null
        extra=" （含 scripts/）"
    fi
    echo "✓ 安裝：$skill_name$extra"
    installed=$((installed + 1))
done

echo ""
echo "完成！安裝了 $installed 個 skill。"

# --- llm-council 專屬檢查：它是 CLI 優先、API key 只是 fallback ---
if [ -d "$TARGET_DIR/llm-council" ]; then
    echo ""
    echo "--- llm-council 環境檢查 ---"
    have_gemini=0; have_codex=0
    command -v gemini >/dev/null 2>&1 && have_gemini=1
    command -v codex  >/dev/null 2>&1 && have_codex=1
    [ $have_gemini -eq 1 ] && echo "✓ gemini CLI：$(command -v gemini)" || echo "✗ gemini CLI：找不到"
    [ $have_codex  -eq 1 ] && echo "✓ codex  CLI：$(command -v codex)"  || echo "✗ codex  CLI：找不到"
    if [ $have_gemini -eq 1 ] && [ $have_codex -eq 1 ]; then
        echo "→ 兩個 CLI 都在，llm-council 會走 CLI，**不需要任何 API key**。"
    else
        if [ -f "$SKILLS_DIR/../.env" ]; then
            echo "→ 有 CLI 缺席，但偵測到 repo 根目錄的 .env（fallback 可用）。"
        else
            echo "→ 有 CLI 缺席，且 repo 根目錄沒有 .env。"
            echo "  缺席的那一邊會回 'Error: ... not found'（另一邊仍可用）。"
            echo "  要補的話：在 repo 根目錄（不是 skill 目錄）建 .env，填 OPENAI_API_KEY= / GEMINI_API_KEY="
        fi
    fi
    python3 -c "import requests" 2>/dev/null \
        && echo "✓ python requests 已安裝" \
        || echo "✗ python requests 未安裝（只有走 API fallback 時才需要）：pip3 install requests"
fi

echo ""
echo "請重啟 Claude Code 讓 skill 生效。"
