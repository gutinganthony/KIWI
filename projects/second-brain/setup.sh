#!/bin/bash
# ============================================================
# Second Brain Vault Setup Script
# 一鍵建立 Obsidian Second Brain 完整資料夾結構
# ============================================================

set -e

# Configuration
VAULT="${SECOND_BRAIN_PATH:-$HOME/SecondBrain}"
KIWI_PATH="${KIWI_PATH:-$HOME/KIWI}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_SOURCE="$SCRIPT_DIR/vault"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Second Brain Vault Setup${NC}"
echo -e "${BLUE}  Obsidian + Claude Code + KIWI${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# ---- Step 1: Create folder structure ----
echo -e "${GREEN}[1/6] Creating folder structure...${NC}"

mkdir -p "$VAULT"/{00-Inbox/{fleeting-notes,web-clips,ig-saved},01-Daily,02-Investment/{Market-Analysis,Thesis,Macro,Client-Notes,AVI-Log},03-Startup/{Idea-Backlog,Evaluations,Yuni,Competitive-Intel},04-Learning/{Articles,Books,Reports,Courses},05-AI-Toolkit/{Prompts,Workflows,Claude-Skills},06-Weekly-Review,Templates,Assets/{images,pdfs}}

echo "  Created 7 main folders + Templates + Assets"

# ---- Step 2: Copy vault files ----
echo -e "${GREEN}[2/6] Copying vault files...${NC}"

if [ -d "$VAULT_SOURCE" ]; then
    # Copy CLAUDE.md
    cp "$VAULT_SOURCE/CLAUDE.md" "$VAULT/CLAUDE.md"
    echo "  Copied CLAUDE.md"

    # Copy Templates
    cp "$VAULT_SOURCE/Templates/"*.md "$VAULT/Templates/" 2>/dev/null && \
        echo "  Copied $(ls "$VAULT_SOURCE/Templates/"*.md 2>/dev/null | wc -l) templates" || \
        echo -e "  ${YELLOW}Warning: No templates found to copy${NC}"

    # Copy Prompts
    cp "$VAULT_SOURCE/05-AI-Toolkit/Prompts/"*.md "$VAULT/05-AI-Toolkit/Prompts/" 2>/dev/null && \
        echo "  Copied $(ls "$VAULT_SOURCE/05-AI-Toolkit/Prompts/"*.md 2>/dev/null | wc -l) diagnosis prompts" || \
        echo -e "  ${YELLOW}Warning: No prompts found to copy${NC}"

    # Copy Workflows
    cp "$VAULT_SOURCE/05-AI-Toolkit/Workflows/"*.md "$VAULT/05-AI-Toolkit/Workflows/" 2>/dev/null && \
        echo "  Copied workflow files" || \
        echo -e "  ${YELLOW}Warning: No workflows found to copy${NC}"
else
    echo -e "  ${RED}Error: Vault source not found at $VAULT_SOURCE${NC}"
    echo "  Please run this script from the KIWI/projects/second-brain/ directory"
    exit 1
fi

# ---- Step 3: Create KIWI symlink ----
echo -e "${GREEN}[3/6] Creating KIWI symlink...${NC}"

if [ -d "$KIWI_PATH" ]; then
    ln -sf "$KIWI_PATH" "$VAULT/07-KIWI"
    echo "  Linked $VAULT/07-KIWI -> $KIWI_PATH"
else
    echo -e "  ${YELLOW}Warning: KIWI not found at $KIWI_PATH${NC}"
    echo "  Set KIWI_PATH env var to your KIWI directory and re-run"
    echo "  Skipping symlink creation..."
fi

# ---- Step 4: Initialize git ----
echo -e "${GREEN}[4/6] Initializing git repository...${NC}"

cd "$VAULT"

if [ ! -d ".git" ]; then
    git init -q
    git branch -M main

    # Create .gitignore
    cat > .gitignore << 'EOF'
# Obsidian workspace (changes frequently, not useful to track)
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/plugins/recent-files-obsidian/data.json
.trash/

# OS files
.DS_Store
Thumbs.db

# KIWI symlink (managed separately in its own repo)
07-KIWI/

# Sensitive client data (NEVER commit)
02-Investment/Client-Notes/

# Large binary files
Assets/pdfs/*.pdf
Assets/images/*.psd

# Temporary files
*.tmp
*~
EOF

    git add -A
    git commit -q -m "Initial vault setup"
    echo "  Git initialized with .gitignore"
    echo "  Initial commit created"
else
    echo "  Git already initialized, skipping..."
fi

# ---- Step 5: Create .obsidian config stub ----
echo -e "${GREEN}[5/6] Creating Obsidian config stubs...${NC}"

mkdir -p "$VAULT/.obsidian"

# Create minimal app config
cat > "$VAULT/.obsidian/app.json" << 'EOF'
{
  "newFileLocation": "folder",
  "newFileFolderPath": "00-Inbox",
  "newLinkFormat": "relative",
  "useMarkdownLinks": false,
  "showFrontmatter": true
}
EOF

# Create community plugins list (user still needs to install them)
cat > "$VAULT/.obsidian/community-plugins.json" << 'EOF'
[
  "templater-obsidian",
  "dataview",
  "calendar",
  "tag-wrangler",
  "obsidian-git",
  "nldates-obsidian",
  "obsidian-kanban",
  "obsidian-excalidraw-plugin",
  "periodic-notes"
]
EOF

echo "  Created .obsidian/app.json"
echo "  Created .obsidian/community-plugins.json"

# ---- Step 6: Print setup instructions ----
echo -e "${GREEN}[6/6] Setup complete!${NC}"
echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Next Steps${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo "  1. Open Obsidian → 'Open folder as vault' → select:"
echo -e "     ${YELLOW}$VAULT${NC}"
echo ""
echo "  2. Install required Community Plugins:"
echo -e "     ${GREEN}[必裝]${NC} Templater         — 模板系統"
echo -e "     ${GREEN}[必裝]${NC} Dataview          — 動態查詢"
echo -e "     ${GREEN}[必裝]${NC} Calendar          — 日曆介面"
echo -e "     ${GREEN}[必裝]${NC} Tag Wrangler      — 標籤管理"
echo -e "     ${GREEN}[必裝]${NC} Obsidian Git      — 自動備份"
echo -e "     ${YELLOW}[推薦]${NC} Natural Language Dates"
echo -e "     ${YELLOW}[推薦]${NC} Kanban"
echo -e "     ${YELLOW}[推薦]${NC} Excalidraw"
echo -e "     ${YELLOW}[推薦]${NC} Periodic Notes"
echo ""
echo "  3. Configure Templater:"
echo "     Settings → Templater → Template folder: Templates"
echo "     Settings → Templater → Trigger on new file: ON"
echo ""
echo "  4. Configure Obsidian Git:"
echo "     Settings → Obsidian Git → Auto backup: 30 min"
echo "     Settings → Obsidian Git → Auto pull: On startup"
echo ""
echo "  5. Start using:"
echo "     - Create today's daily note with Cmd/Ctrl+P → Templater"
echo "     - Use CLAUDE.md as context when working with Claude Code"
echo ""
echo -e "${GREEN}  Vault created at: $VAULT${NC}"
echo -e "${GREEN}  Total files: $(find "$VAULT" -name "*.md" | wc -l) markdown files${NC}"
echo ""
echo -e "${BLUE}  Happy thinking! 🧠${NC}"
