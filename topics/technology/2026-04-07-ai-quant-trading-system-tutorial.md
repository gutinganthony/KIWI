---
title: 为了让AI学会交易，我搭了一个量化交易系统（附完整教程）
url: https://x.com/nopinduoduo/status/2038919302695297299
source: X (Twitter) @nopinduoduo (我真的没有拼多多)
date_added: 2026-04-07
last_updated: 2026-04-07
topic: technology
tags: [AI, quant-trading, crypto, OKX, tutorial, system-design, simulation, LLM]
version: 1.0
---

## Summary

A hands-on tutorial thread by @nopinduoduo (77K views) documenting how they built a complete AI quantitative trading training system for their AI assistant "Jarvis." The core insight: feeding an AI investment theory ≠ making it able to trade. Like a new driver who passed all theory tests but still sweats on the first real drive, AI needs a simulation "driving school" before touching real money.

The system's key innovation is a **reflection & accumulation loop** — after every simulated trade, the AI reviews its own decisions, extracts reusable strategy templates, scores them, and builds a dynamic rule library. Each token spent becomes a permanent learning artifact.

## Key Takeaways

- **Theory ≠ Practice:** After feeding 420,000 words of investment articles, Jarvis said "I understand the theory, but I haven't traded in practice — I don't dare touch your money." The simulation system solves this.
- **42万字的作用是"安全护栏"，不是执行工具:** The knowledge base acts as guardrails (e.g., "low-volume breakouts are risky"), while the strategy library (built from simulation) is the actual execution tool. Both layers must work together.
- **OKX CLI makes setup trivial:** `npm install -g okx-trade-mcp okx-trade-cli` — one line replaces writing your own WebSocket connection code.
- **The reflection system is the real innovation:** Without post-trade review, every session starts from zero. The scoring formula filters strategies before they touch real money.
- **Strategy scoring gate:** Only strategies scoring > 0.6 enter the real trading system.

---

## System Architecture — 4-Stage Closed Loop

```
① 学习阶段 (Learning)
   └─ 42万字投资文章 → 知识库 (Knowledge base)

② 模拟交易 (Simulation Trading)  ← 本文重点
   └─ 真实行情 + 模拟执行 + 实时看板

③ 反思沉淀 (Reflection & Accumulation)  ← 核心创新
   └─ AI复盘 → 提取策略 → 评分 → 规则库

④ 真实交易 (Real Trading)
   └─ 加载验证策略 → 小额试水
        ↑                    ↓
        └───── 反馈循环 ─────┘
```

**AI decision flow (3-layer knowledge synthesis):**
1. **知识库 (42万字)** → safety guardrails: "Low-volume breakouts are risky"
2. **策略库 (simulation-derived)** → execution tool: "Breakout strategy: 68% win rate, avg 3.4% return"
3. **当前状态** → real-time context: "BTC broke 20-day MA, but volume is only 40% of average"
→ **Decision:** Don't act, wait for confirmation

---

## Technical Implementation

### Step 1 — Apply for OKX API Key
- Go to: https://www.okx.com/zh-hans/account/my-api
- Permissions: Start with **Read only** (balance, price). Add **Trade** permission later.
- Record: API Key, Secret Key, Passphrase

### Step 2 — Install OKX CLI
```bash
npm install -g okx-trade-mcp okx-trade-cli
okx --version
okx-trade-mcp --version
```

### Step 3 — Configure API Key
**Windows (PowerShell):**
```bash
mkdir "$env:USERPROFILE\.okx"
notepad "$env:USERPROFILE\.okx\config.toml"
```
**Mac/Linux:** `~/.okx/config.toml`

**Config file:**
```toml
default_profile = "demo"

[profiles.demo]
api_key = "your-API-Key"
secret_key = "your-Secret-Key"
passphrase = "your-Passphrase"
demo = true  # Critical: demo=true = simulation mode
```

**Test:**
```bash
okx --profile demo account balance
# Expected output: BTC 1 / OKB 100 / USDT 5000 / ETH 1 (virtual funds)
```

### Step 4 — Build Real-time Dashboard
Tech stack: **Next.js + TypeScript + Tailwind CSS**

Core features:
- Real-time account balance (auto-refresh every 10 seconds)
- Running strategy status
- Grid bot visualization
- Trade history query
- One-click review report generation

```bash
echo "OKX_API_KEY=xxx" > .env.local
echo "OKX_SECRET_KEY=xxx" >> .env.local
echo "OKX_PASSPHRASE=xxx" >> .env.local
```

---

## Reflection & Accumulation System

The most critical innovation. Without it, every session starts from zero.

### Workflow
1. **Auto post-trade review** — AI analyzes every trade using a fixed template:
   - What was the decision basis?
   - What was the market state?
   - Did the result match expectations?
   - What would I do differently?
   - What did I learn?

2. **Strategy extraction:**
   - Successful trades → Strategy templates
   - Failed trades → Rules to avoid

3. **Strategy scoring:**
   ```
   Score = (Win Rate × 0.4) + (Return Rate × 0.4) + ((1 - Risk Score) × 0.2)
   ```
   Only strategies scoring **> 0.6** enter the real trading system.

4. **Dynamic rule library** — persistent, ever-growing knowledge from real simulation experience

---

## First Simulated Trade (Example)

- **Time:** 2026-03-31 15:23
- **Decision:** Launch BTC-USDT grid trading bot
- **Parameters:** Range 64,000–70,000 USDT | 10 grids | 1,000 USDT capital
- **Rationale:** BTC oscillating near 67,000; range covers recent volatility; max loss per grid ~100 USDT
- **Jarvis's post-trade review:** "Initial unrealized loss is normal for grid strategy. The longer price oscillates within range, the higher the return."

---

## Update Log

- 2026-04-07 v1.0: Initial entry
