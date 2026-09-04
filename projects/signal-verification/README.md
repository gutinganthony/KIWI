# signal-verification — 訊號有效性回測腳本（2026-09-03）

跑出 `topics/business/2026-09-03-signal-verification-credit-rpoc-tw-revenue.md` 的一手結果。
**資料源：FinMind API（免金鑰公開端點）。本雲端容器可達；FRED／Yahoo／SEC／stockanalysis 皆被 egress 擋。**

依序執行（01 會產出 `rev.json`，02 產出 `taiex.json`，03/04 讀這兩個檔）：

```bash
python3 01_build_tw_revenue_series.py   # 12 檔台股科技籃子月營收 → rev.json
python3 02_taiex_peaks_leadlag.py       # TAIEX 月收盤、>=20% 回檔、領先/落後 → taiex.json
python3 03_false_positive_test.py       # 減速規則 vs 基準的假訊號檢定
python3 04_conditioned_and_reverse.py   # 條件化版本 + 反向（加速）檢定
python3 05_tw_cooling_financials.py     # 冷卻/電源族群 PER/PBR/毛利/營益/月營收
```

## 主要結論（2026-09-03 實跑）
- 樣本 281 個月（2003-03 → 2026-07），籃子 12 檔全程連續。
- **「月營收 YoY 減速」不是賣訊**：所有參數組的訊號後 12M 報酬（+14.7%~+19.4%）都**優於**基準（+10.8%）。
- **「YoY 轉負」落後指數頂 8–11 個月**，不可用。
- 僅「3MA ≥25% 且急遽減速」子集為負向（12M −10.7%、平均最大回檔 −25.9% vs 基準 −12.2%），**但 n=3**。
- **反向：YoY 加速（3MA 創 12 個月新高）反而是看多訊號**（12M +17.2%、負率 18%）。

⚠️ 月營收資料最早 2002-02 ⇒ **2000 年那次崩盤無法檢定**。
