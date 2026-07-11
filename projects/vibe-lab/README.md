# vibe-lab — 用 GitHub Actions 跑 Vibe-Trading 的運算臂

> 為什麼存在:雲端 Claude Code session 的 proxy 封鎖所有行情源(yahoo/tencent/stooq 實測全擋),
> 但 GitHub Actions runner 網路自由(poly-observer、tw-funnel 已兩次證實)。
> 本專案把 HKUDS/Vibe-Trading 的確定性功能(alpha bench、回測)搬到 Actions 上跑,
> 結果 commit 回 repo,任何裝置的任何 session 都能讀。評估文:
> topics/technology/2026-07-11-vibe-trading-hkuds-evaluation.md

## 使用方式(任何 session 皆可)

1. 改 `job.json`(見下方 spec),commit + push 到本分支。
2. push 觸發 `.github/workflows/vibe-lab.yml`(paths 過濾只認 job.json 與 workflow 本身,
   結果 commit-back 不會自我觸發)。
3. 跑完後結果出現在 `results/latest.md`(以及帶時間戳的歷史檔)。

## job.json spec(v1)

```json
{
  "type": "alpha-bench",          // v1 支援:alpha-bench ・ alpha-list
  "zoo": "academic",              // alpha-bench 必填:academic/qlib158/alpha101/gtja191/fundamental
  "universe": "sp500",            // alpha-bench 必填:sp500/btc-usdt 免 token;csi300 需 repo Secret TUSHARE_TOKEN(run #1 實測,成分股清單非免費行情)
  "period": "2024-2025",          // YYYY-YYYY 或 YYYY-MM-DD/YYYY-MM-DD
  "top": 10,                      // 保留前 N 名
  "note": "人看的說明,程式不讀"
}
```

## 邊界與守則(沿用 repo LEARNINGS)

- **零 LLM key**:v1 只跑確定性功能。未來要加 swarm 類 job,先放 `DEEPSEEK_API_KEY`
  進 repo Secrets(workflow 已預留 env 傳遞)。
- **repo 體積**:結果檔在 runner 端就地裁切(頭 500 行+尾 200 行),>900KB 的檔在
  commit 前刪除。原始大檔絕不入版控。
- **commit-back 一律 rebase-then-push**;commit 訊息不含 skip-ci 方括號字樣。
- vibe-trading 版本迭代快(0.1.x Beta),workflow 裝的是 PyPI 最新版;
  哪天跑掛了先懷疑 upstream breaking change,pin 版本再試。
