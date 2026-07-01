#!/bin/bash
# SessionStart hook: ensure gstack is installed globally (required by CLAUDE.md).
# Designed for Claude Code on the web — the remote container starts fresh, so
# this re-installs gstack when missing. Idempotent: exits immediately when
# gstack is already present (container state is cached after the hook runs).
set -euo pipefail

# Only run in remote (web) sessions; local machines manage gstack themselves.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

GSTACK_DIR="$HOME/.claude/skills/gstack"

# Fast path: already installed.
if [ -d "$GSTACK_DIR/bin" ]; then
  exit 0
fi

if ! command -v bun >/dev/null 2>&1; then
  echo "gstack install skipped: bun is not available in this container." >&2
  echo "Skills will be blocked until gstack is installed (see CLAUDE.md)." >&2
  exit 0
fi

echo "Installing gstack..." >&2
rm -rf "$GSTACK_DIR"
git clone --depth 1 https://github.com/garrytan/gstack.git "$GSTACK_DIR"

cd "$GSTACK_DIR"
bun install --frozen-lockfile 2>/dev/null || bun install

# The web environment's network policy blocks cdn.playwright.dev (Playwright's
# browser CDN), so ./setup's "bunx playwright install chromium" would fail.
# storage.googleapis.com IS allowed, and it hosts the identical Chrome for
# Testing builds — pre-place them where Playwright expects, then setup's
# browser check passes and the download is skipped.
PW_DIR="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright}"
PWC_DIR="$(dirname "$(node -e "console.log(require.resolve('playwright-core/package.json'))")")"
read -r CR_REV CR_VER < <(node -e "
  const b = require('$PWC_DIR/browsers.json').browsers;
  const c = b.find(x => x.name === 'chromium');
  console.log(c.revision, c.browserVersion);
")
CFT_BASE="https://storage.googleapis.com/chrome-for-testing-public/$CR_VER/linux64"

if [ ! -x "$PW_DIR/chromium-$CR_REV/chrome-linux64/chrome" ]; then
  mkdir -p "$PW_DIR/chromium-$CR_REV"
  curl -fsSL "$CFT_BASE/chrome-linux64.zip" -o /tmp/cft-chrome.zip
  unzip -oq /tmp/cft-chrome.zip -d "$PW_DIR/chromium-$CR_REV/"
  rm -f /tmp/cft-chrome.zip
  touch "$PW_DIR/chromium-$CR_REV/INSTALLATION_COMPLETE"
fi

if [ ! -x "$PW_DIR/chromium_headless_shell-$CR_REV/chrome-headless-shell-linux64/chrome-headless-shell" ]; then
  mkdir -p "$PW_DIR/chromium_headless_shell-$CR_REV"
  curl -fsSL "$CFT_BASE/chrome-headless-shell-linux64.zip" -o /tmp/cft-shell.zip
  unzip -oq /tmp/cft-shell.zip -d "$PW_DIR/chromium_headless_shell-$CR_REV/"
  rm -f /tmp/cft-shell.zip
  touch "$PW_DIR/chromium_headless_shell-$CR_REV/INSTALLATION_COMPLETE"
fi

# Chrome's runtime shared libraries (best-effort; the base image may already
# have them, and some configured apt PPAs 403 under the network policy).
bunx playwright install-deps chromium >/dev/null 2>&1 || true

./setup --team
echo "gstack installed." >&2
