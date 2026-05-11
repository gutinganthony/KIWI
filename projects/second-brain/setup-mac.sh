#!/bin/bash
# ============================================================
# Second Brain Vault Setup — macOS 版本
# 支援 iCloud Drive 同步，多台 Mac 共用
# ============================================================

set -e

# ---- 設定路徑 ----
# 預設放在 iCloud Drive 的 Obsidian 資料夾（多台 Mac 自動同步）
ICLOUD_OBSIDIAN="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"
VAULT="${SECOND_BRAIN_PATH:-$ICLOUD_OBSIDIAN/SecondBrain}"

# 如果 iCloud Obsidian 資料夾不存在，改用本機
if [ ! -d "$ICLOUD_OBSIDIAN" ]; then
    echo "⚠️  iCloud Drive 的 Obsidian 資料夾不存在"
    echo "   使用本機路徑: ~/SecondBrain"
    echo "   (如果你之後想用 iCloud，先在 Obsidian 開啟 iCloud 同步再重跑此腳本)"
    VAULT="$HOME/SecondBrain"
fi

KIWI_PATH="${KIWI_PATH:-$HOME/KIWI}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_SOURCE="$SCRIPT_DIR/vault"

echo "================================================"
echo "  Second Brain Vault Setup (macOS)"
echo "  Obsidian + Claude Code + KIWI"
echo "================================================"
echo ""
echo "  Vault 位置: $VAULT"
echo ""

# ---- Step 1: 建立資料夾 ----
echo "[1/6] 建立資料夾結構..."

mkdir -p "$VAULT"/{00-Inbox/{fleeting-notes,web-clips,ig-saved},01-Daily,02-Investment/{Market-Analysis,Thesis,Macro,Client-Notes,AVI-Log},03-Startup/{Idea-Backlog,Evaluations,Yuni,Competitive-Intel},04-Learning/{Articles,Books,Reports,Courses},05-AI-Toolkit/{Prompts,Workflows,Claude-Skills},06-Weekly-Review,Templates,Assets/{images,pdfs}}

echo "  ✅ 建立 7 個主資料夾 + Templates + Assets"

# ---- Step 2: 複製檔案 ----
echo "[2/6] 複製 vault 檔案..."

if [ -d "$VAULT_SOURCE" ]; then
    cp "$VAULT_SOURCE/CLAUDE.md" "$VAULT/CLAUDE.md"
    echo "  ✅ CLAUDE.md"

    cp "$VAULT_SOURCE/Templates/"*.md "$VAULT/Templates/" 2>/dev/null && \
        echo "  ✅ 7 個 Obsidian 模板" || true

    cp "$VAULT_SOURCE/05-AI-Toolkit/Prompts/"*.md "$VAULT/05-AI-Toolkit/Prompts/" 2>/dev/null && \
        echo "  ✅ 6 個 McKinsey 診斷 Prompt" || true

    cp "$VAULT_SOURCE/05-AI-Toolkit/Workflows/"*.md "$VAULT/05-AI-Toolkit/Workflows/" 2>/dev/null && \
        echo "  ✅ 報告情報管線 Workflow" || true
else
    echo "  ❌ 找不到 vault 來源: $VAULT_SOURCE"
    echo "  請從 KIWI/projects/second-brain/ 目錄執行此腳本"
    exit 1
fi

# ---- Step 3: KIWI symlink ----
echo "[3/6] 建立 KIWI 連結..."

if [ -d "$KIWI_PATH" ]; then
    ln -sf "$KIWI_PATH" "$VAULT/07-KIWI"
    echo "  ✅ 07-KIWI → $KIWI_PATH"
else
    echo "  ⚠️  KIWI 不在 $KIWI_PATH"
    echo "  之後執行: ln -s /你的/KIWI/路徑 $VAULT/07-KIWI"
fi

# ---- Step 4: Git 初始化 ----
echo "[4/6] 初始化 Git..."

cd "$VAULT"

if [ ! -d ".git" ]; then
    git init -q
    git branch -M main

    cat > .gitignore << 'GITIGNORE'
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/plugins/recent-files-obsidian/data.json
.trash/
.DS_Store
07-KIWI/
02-Investment/Client-Notes/
Assets/pdfs/*.pdf
Assets/images/*.psd
*.tmp
*~
GITIGNORE

    git add -A
    git commit -q -m "Initial vault setup"
    echo "  ✅ Git 初始化完成"
else
    echo "  ⏭  Git 已存在，跳過"
fi

# ---- Step 5: Obsidian 設定 ----
echo "[5/6] 建立 Obsidian 設定..."

mkdir -p "$VAULT/.obsidian"

cat > "$VAULT/.obsidian/app.json" << 'EOF'
{
  "newFileLocation": "folder",
  "newFileFolderPath": "00-Inbox",
  "newLinkFormat": "relative",
  "useMarkdownLinks": false,
  "showFrontmatter": true
}
EOF

cat > "$VAULT/.obsidian/community-plugins.json" << 'EOF'
[
  "templater-obsidian",
  "dataview",
  "calendar",
  "tag-wrangler",
  "obsidian-git",
  "nldates-obsidian",
  "periodic-notes"
]
EOF

echo "  ✅ Obsidian 基本設定"

# ---- Step 6: 完成 ----
echo "[6/6] 完成！"
echo ""
echo "================================================"
echo "  接下來你要做的事"
echo "================================================"
echo ""
echo "  1️⃣  下載 Obsidian → https://obsidian.md"
echo ""
echo "  2️⃣  打開 Obsidian → 'Open folder as vault' → 選擇:"
echo "      $VAULT"
echo ""
echo "  3️⃣  安裝 Plugin（Settings → Community Plugins → Browse）:"
echo "      [必裝] Templater       → 設 Template folder: Templates"
echo "      [必裝] Dataview        → 動態查詢"
echo "      [必裝] Calendar        → 日曆介面"
echo "      [必裝] Tag Wrangler    → 標籤管理"
echo "      [必裝] Obsidian Git    → Auto backup: 30 min"
echo ""
echo "  4️⃣  建立第一篇日誌:"
echo "      Cmd+P → Templater → Insert Template → tpl-daily-journal"
echo ""
echo "  📂 Vault 位置: $VAULT"
echo "  📄 總檔案數: $(find "$VAULT" -name "*.md" | wc -l | tr -d ' ') 個 Markdown"
echo ""
TOTAL_SIZE=$(du -sh "$VAULT" 2>/dev/null | cut -f1)
echo "  💾 總大小: $TOTAL_SIZE"
echo ""
echo "  🔄 多台 Mac 同步: 如果 Vault 在 iCloud Drive 裡，"
echo "     另一台 Mac 的 Obsidian 直接選同一個 iCloud 路徑即可"
echo ""
