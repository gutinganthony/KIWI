# 本益比模型重建：研究筆記（2026-10-01 起）

使用者決定把模型打掉重來，從學術上「本益比怎麼來的」一步一步拆解。這個資料夾放每一步的研究底稿。

| 檔案 | 內容 |
|---|---|
| `01_theory_lineage.md` | 第 1 步（理論）：Graham & Dodd、Williams、Gordon、Miller-Modigliani、Leibowitz-Kogelman、Ohlson／AEG、Penman、Campbell-Shiller、Vuolteenaho 的推導、公式、假設與總表 |
| `02_empirical_evidence.md` | 第 1 步（實證）：什麼真的決定個股本益比、盈餘消息 vs 折現率消息、倍數估值與 12 個月目標價的已知準確度 |
| `03_tech_valuation_evidence.md` | 科技股相關：Pástor-Veronesi 不確定性、Schwartz-Moon、研發費用化與 SBC、各估值模型的準確度賽馬、成長衰減速度 |
| `04_theory_comparison_for_tech.md` | **理論比較的結論**：各理論逐項評分、三種典型科技公司試算、建議的模型骨架與可驗證的假說 |
| `05_aeg_orbit_test_and_design.md` | 第 2 步：AEG 與本益比軌道詳解、在 S&P 500 上的實測（AEG 照理論失敗、軌道＝舊模型基準）、反推長期成長的示範與實作規劃、週期股與虧損股方案 |
| `aeg_lab.py`、`reverse_demo.py` | 第 2 步的回測與示範程式（輸出在 `results/aeg_lab*`） |
| `tech_archetypes.py` | 三種典型科技公司（穩定巨頭、高成長、週期）套 Gordon、PVGO、AEG、兩階段軌道的試算 |
| `pe_check.py`、`cs_check.py` | 理論公式的數值驗算（Gordon＝MM＝L&K、兩階段、OJ、Penman、Ohlson、Campbell-Shiller） |

**限制**：研究時 WebFetch 被網路代理擋下，所有出處都只看到期刊／出版社頁面與搜尋摘要，沒有逐字核對原文全文；
報告裡每條都標了可信度（事實／二手／推論／不確定、A／B／C）。推導出的公式已用上面兩支腳本驗算。
