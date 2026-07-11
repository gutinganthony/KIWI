#!/usr/bin/env bash
# vibe-trading MCP server 啟動器(.mcp.json 引用;雲端 session 容器每次全新,
# 首次啟動需 pip 安裝約 1-3 分鐘,期間 MCP 會晚一點才連上,屬正常)。
# setuptools 先升級是為了繞 Debian install_layout bug(見 agents/LEARNINGS.md)。
set -u
export PATH="$HOME/.local/bin:$PATH"
if ! command -v vibe-trading-mcp >/dev/null 2>&1; then
  pip install --user -q -U setuptools wheel >/dev/null 2>&1
  pip install --user -q vibe-trading-ai >/dev/null 2>&1
fi
exec vibe-trading-mcp
