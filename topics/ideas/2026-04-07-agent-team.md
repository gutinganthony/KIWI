---
title: Agent Team
date_added: 2026-04-07
last_updated: 2026-04-07
topic: ideas
tags: [AI, agents, productivity, automation, multi-agent, LLM, workflow]
version: 1.0
---

## Summary

一個由多個 AI Agent 組成的協作團隊，能夠處理複雜的多步驟任務。每個 Agent 有明確的角色分工（如研究員、寫作者、審稿者、執行者），透過協調機制共同完成單一 Agent 難以勝任的工作。

核心概念是將大型任務拆解成子任務，分配給專精的 Agent，最後由統籌 Agent 整合輸出。這種架構特別適合需要跨域知識、長流程執行、或需要自我檢查與迭代的任務類型。

## Key Takeaways

- 多 Agent 協作可突破單一 LLM 的 context 限制與能力邊界
- 角色分工讓每個 Agent 的 prompt 更聚焦，輸出品質更高
- 核心挑戰：Agent 間的溝通協議、狀態同步、錯誤處理
- 可應用場景：自動化研究報告、程式碼生成與審查、內容創作流水線

## Potential Architecture

- **Orchestrator Agent**：任務拆解、分配、結果整合
- **Research Agent**：網路搜尋、資料蒐集、事實查核
- **Writer Agent**：根據研究結果生成文字內容
- **Critic Agent**：審查輸出品質、提出修改建議
- **Executor Agent**：執行具體操作（API 呼叫、程式碼執行等）

## Potential Use Cases

- 自動化競品分析報告
- 程式碼 review + 重構建議
- 多語言內容翻譯與本地化
- 客服自動化（問題分類 → 解答生成 → 品質把關）

## Update Log

- 2026-04-07 v1.0: Initial entry
