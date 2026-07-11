# vibe-lab run 2026-07-11T1221Z

- command:`vibe-trading alpha bench --zoo academic --universe csi300 --period 2024-2025 --top 10`
- exit:1・耗時 3s
- spec:`{"type": "alpha-bench", "zoo": "academic", "universe": "csi300", "period": "2024-2025", "top": 10, "note": "首發驗證:academic 因子池(10 個,含 Carhart 動能/52 週高點/Amihud 流動性等)在 csi300、2024-2025 的 IC bench。選 csi300 是因為它是 README 文件化的 happy path 且 tencent 源批次快;通過後再換 sp500 貼近 Serenity 池。"}`

## stdout

```
Bench: 10 alphas x csi300 x 2024-2025
ETA: ~3-5 min (cache hit) / ~10-20 min (cold fetch)
⠋ Benching                                          0/10 loading universe... 0:00:00
{
  "status": "error",
  "error": "universe load failed: TUSHARE_TOKEN not in agent/.env or environment; required for csi300 universe",
  "zoo": "academic",
  "universe": "csi300",
  "period": "2024-2025"
}
```

## stderr

```
alpha bench failed: universe load failed: TUSHARE_TOKEN not in agent/.env or environment; required for csi300 universe

How to fix:
  1. Register for a free token at https://tushare.pro/register
  2. Add 'TUSHARE_TOKEN=<your_token>' to agent/.env  (or ~/.vibe-trading/.env)
  3. Re-run this command
```
