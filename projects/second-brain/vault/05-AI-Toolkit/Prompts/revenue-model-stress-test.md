---
type: prompt
created: 2026-05-10T00:00
updated: 2026-05-10T00:00
tags: [prompt, startup/evaluation, revenue, unit-economics]
status: active
---

# 收入模式壓力測試（Revenue Model Stress Test）

> 6 項測試：單位經濟學拆解、三情境 12 個月模型、敏感度分析、基準比較、致命問題、Pivot 經濟學。

## 使用方式

將以下 prompt 完整貼入 Claude，替換 `{placeholder}` 後送出。適合在確認 idea 值得追之後，深度驗證財務可行性。

---

## Prompt

你是一位 SaaS metrics 專家，曾任 Bessemer Venture Partners 營運合夥人，審核過 200+ 家早期公司的商業模式。你用數字說話，不接受模糊的「可以再調整」。

**產品資訊：**
- 產品名稱：{product_name}
- 定價模式：{pricing}（月訂閱 $X / 按次 $Y / Freemium / 佣金 Z%）
- 目標客群：{target_segment}
- 目前數據：{current_data}（用戶數、MRR、churn rate、ARPU、轉換率）
- 主要成本結構：{cost_structure}（伺服器、人力、行銷、其他）

---

### Test 1：單位經濟學拆解（Unit Economics Decomposition）

**客戶獲取成本（CAC）完整拆解：**

| 渠道 | 月支出 | 獲得客戶數 | CAC | 品質評估 |
|------|--------|-----------|-----|----------|

- Blended CAC = ?
- Organic vs Paid 比例 = ?
- CAC 趨勢：隨規模是上升還是下降？為什麼？

**客戶終身價值（LTV）計算：**

```
LTV = ARPU × Gross Margin % × (1 / Monthly Churn Rate)
```

- ARPU breakdown（各方案的加權平均）
- Gross Margin 是否包含了所有真實成本？（customer support? server cost?）
- Churn rate 是否用足夠長的 cohort 計算？

**LTV:CAC Ratio 判定：**
| 情境 | LTV:CAC | 健康嗎？ | 行動建議 |
|------|---------|----------|----------|
| < 1x | 🔴 | 燒錢死 | 立即停止獲客 |
| 1-3x | 🟡 | 危險 | 必須改善 |
| 3-5x | 🟢 | 健康 | 可加速 |
| > 5x | 🔵 | 過於保守？ | 該花更多錢獲客 |

---

### Test 2：三情境 12 個月模型（Three-Scenario Model）

建立三種情境的 12 個月財務模型：

**假設表：**
| 變數 | 悲觀 | 基準 | 樂觀 |
|------|------|------|------|
| 月新增用戶 | | | |
| Monthly Churn | | | |
| ARPU | | | |
| CAC | | | |
| Fixed Cost/月 | | | |

**12 個月 P&L 預測（基準情境）：**

| 月份 | 新用戶 | 流失 | 活躍用戶 | MRR | COGS | Gross Profit | OpEx | Net | Runway |
|------|--------|------|----------|-----|------|-------------|------|-----|--------|

- 何時達到盈虧平衡（break-even）？
- 需要多少資金才能撐到 break-even？
- 如果比預期慢 2 倍，結果如何？

---

### Test 3：敏感度分析（Sensitivity Analysis）

找出模型中最脆弱的變數：

| 變數變化 | 對 12 個月累計虧損的影響 | 對 break-even 時間的影響 |
|----------|-------------------------|------------------------|
| Churn +5% | | |
| CAC +50% | | |
| ARPU -20% | | |
| Growth rate -50% | | |

**最致命的單一變數是哪個？** 如果只能改善一個指標，應該是哪個？

---

### Test 4：基準比較（Benchmark Comparison）

與同類成功公司比較：

| 指標 | 你的數字 | 行業 Top 25% | 行業中位數 | 行業 Bottom 25% | 你的位置 |
|------|----------|-------------|-----------|----------------|----------|
| LTV:CAC | | | | | |
| Monthly Churn | | | | | |
| Gross Margin | | | | | |
| Net Revenue Retention | | | | | |
| Payback Period | | | | | |

哪些指標遠低於標準？這是暫時的還是結構性的？

---

### Test 5：致命問題（Kill Shot Questions）

回答以下問題，只接受「是/否 + 數字佐證」：

1. **沒有融資能活嗎？** 純靠營收，幾個月後能自給自足？
2. **盈虧平衡需要多少付費用戶？** 這個數字在你的市場中現實嗎？
3. **如果最大獲客渠道明天消失？**（例：Apple 改政策、Google 演算法改變）營收會掉多少？
4. **這個定價在台灣市場合理嗎？** 台灣用戶的付費意願 vs 你的假設
5. **你的毛利率能支撐請人嗎？** 還是永遠只能一個人做？
6. **這個模式有 power law 嗎？** 還是線性成長，永遠不會有爆發點？

---

### Test 6：Pivot 經濟學（Pivot Economics）

如果需要 pivot：

- 目前已投入的成本中，哪些可以帶到新方向？（可重用資產）
- 哪些是完全沉沒的？
- Pivot 的「重置成本」估算
- 最可能的 3 個 pivot 方向：

| Pivot 方向 | 可重用比例 | 新的 Unit Economics 估算 | 風險 |
|------------|-----------|------------------------|------|

---

### 最終判決

**這個收入模式的健康程度：**

- 🟢 Viable — 數字站得住腳，問題在執行
- 🟡 Fixable — 需要調整 {specific_changes} 才能 work
- 🔴 Broken — 根本性問題，需要重新設計商業模式

**如果你是投資人，你會投嗎？** 為什麼？

**創辦人下一步：**
- 最需要驗證的 1 個假設
- 最需要改善的 1 個指標
- 做出 kill/continue 決定的 deadline

---

## 輸出要求

- 所有數字附計算過程
- 明確標示哪些是假設（需驗證）vs 事實（已有數據）
- 如果提供的數據不足以做判斷，列出「需要的數據清單」
- 不做樂觀的外推——用 base case 做決策，用 bull case 做夢
