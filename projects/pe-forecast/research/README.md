# 本益比模型重建：研究筆記（2026-10-01 起）

使用者決定把模型打掉重來，從學術上「本益比怎麼來的」一步一步拆解。這個資料夾放每一步的研究底稿。

| 檔案 | 內容 |
|---|---|
| `01_theory_lineage.md` | 第 1 步（理論）：Graham & Dodd、Williams、Gordon、Miller-Modigliani、Leibowitz-Kogelman、Ohlson／AEG、Penman、Campbell-Shiller、Vuolteenaho 的推導、公式、假設與總表 |
| `02_empirical_evidence.md` | 第 1 步（實證）：什麼真的決定個股本益比、盈餘消息 vs 折現率消息、倍數估值與 12 個月目標價的已知準確度 |
| `pe_check.py`、`cs_check.py` | 理論公式的數值驗算（Gordon＝MM＝L&K、兩階段、OJ、Penman、Ohlson、Campbell-Shiller） |

**限制**：研究時 WebFetch 被網路代理擋下，所有出處都只看到期刊／出版社頁面與搜尋摘要，沒有逐字核對原文全文；
報告裡每條都標了可信度（事實／二手／推論／不確定、A／B／C）。推導出的公式已用上面兩支腳本驗算。
