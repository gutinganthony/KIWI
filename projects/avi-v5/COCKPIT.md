# 全局觀測台（Market Cockpit）— 設計、資料契約、回測結論、維運

> 公開頁：`docs/cockpit/index.html`（GitHub Pages）。資料層：`scripts/market_cockpit.py`。
> 追蹤清單：`config/cockpit_watch.json`。建立：2026-11-05（Jake 的 /goal：一眼看懂市場 regime、板塊強弱、資金流向，附回測）。

## 1. 它回答的三個問題

| 問題 | 指標 | 顯示 |
|---|---|---|
| 市場是多頭／盤整／空頭？ | **Regime Score**（−100…+100）＝趨勢 40% + 廣度 25% + 波動 20% + 信用 15%；狀態機含遲滯（進 ±25／出 ±10）與連續 3 日確認 | 大字狀態＋分數＋四支柱分解＋近兩年分數曲線與狀態色帶 |
| 強勢股／弱勢股在哪個板塊？ | **板塊強度** 0–100（3M/6M/12M 相對 SPY 超額報酬的橫斷面百分位，30/40/30 加權）＋ **RRG**（JdK RS-Ratio 63 日／RS-Momentum 21 日） | 排名長條＋RRG 散點（含 5 週軌跡）＋明細表 |
| 資金流入／流出哪個板塊？歷史平均？ | **流向強度**＝Chaikin 20 日淨資金流 ÷ 20 日成交金額（−1…+1）；對照自身 1 年均、5 年均、5 年百分位；成交金額佔比 vs 1 年均（注意力） | 發散長條（現值 + 兩條均值標記）＋摘要＋明細表 |

海外基金公司對應：Regime 四支柱 ≈ Ned Davis「趨勢＋廣度＋情緒」複合；RRG 是 Bloomberg／StockCharts 標準的板塊輪動圖；資金流向在沒有付費申贖資料時，賣方常用的價量代理就是 Chaikin money flow。

宇宙：SPY（基準）、11 個 SPDR 板塊（XLK XLC XLY XLF XLV XLI XLE XLB XLP XLU XLRE）+ SMH、輔助 RSP IWM QQQ HYG IEF TLT GLD ^VIX。資料：Yahoo chart API（免金鑰；**UA 必須是 `KIWI-cockpit/1.0 (+https://github.com/gutinganthony/KIWI)`**——curl 預設 UA 會 429，假冒瀏覽器 UA 會被本環境的安全分類器擋）。

## 2. 四支柱的細節（每項 clip 到 ±100）

- **趨勢**：SPY/200MA 距離（±10% → ±100）50%；50MA/200MA 距離（±5%）25%；200MA 20 日斜率（±2%）25%。
- **廣度**：板塊站上 200MA 比例 40%；站上 50MA 比例 30%；RSP/SPY 與 IWM/SPY 63 日相對變化（±5%）30%。
- **波動**：VIX 一年百分位（反向）40%；VIX vs 50 日均（±30%，反向）30%；SPY 20 日實現波動一年百分位（反向）30%。
- **信用**：HYG/IEF 比值 vs 63 日均（±3%）60%；20 日變化（±2%）40%。HYG 2007 才上市，之前權重自動重新正規化。

## 3. 回測結論（1993-12 → 2026-11，SPY；板塊 1999-06 →；樣本內、無成本）

- **Regime**：多頭 67% 時間／盤整 17%／空頭 17%。空頭期年化波動 32%（多頭 13%）、未來 21 日跌 >5% 機率 19%（多頭 5%）、P10 −8.2%（多頭 −3.5%）。**空頭期的平均前瞻報酬不是負的**（確認延遲 3 日，急跌多發生在進入空頭之前）——這個指標的價值在尾部風險，不在報酬方向。曝險規則（多 100／盤 50／空 0）：CAGR 8.6% vs 買進持有 10.8%，但 MDD −27% vs −51%、Sharpe 0.82 vs 0.73。
- **板塊動能**：Top3 CAGR 10.7% / Sharpe 0.66 / MDD −41%；Bottom3 7.1% / 0.36 / −60%；SPY 8.2% / 0.54 / −51%。Top3−Bottom3 年化 +2.7%、t = 0.9（**薄**）。回看期比較：1M 反向（−3.8%/年）、3M ≈ 0、6M +2.1%、12M +1.5%、12-1 +1.9% → 強度分數不含 1M。主要價值是**避開 Bottom 3**。
- **RRG 象限**：四象限的未來 21 日超額都在 ±0.2% 內、勝率 ≈ 50% → **描述工具，不是預測工具**。
- **資金流代理**：月頻 IC −0.026（t −1.3）、四分位價差 −4%/年、極端流入／流出後 21 日超額 ≈ 0 → **描述現況可用，預測不行**。頁面上明講。
- Regime × 板塊熱圖（各狀態下的板塊月超額均值）在 `backtest.json.sectors.regime_heatmap`。

## 4. 資料契約

`docs/cockpit/data.json`（~37 KB）：`asof, regime{state,label,score,since,days,pillars{...parts},spy,vix,breadth,hyg_ief,history{dates,score,state,spy,ma200}(504 日),episodes}, sectors[]{symbol,name,rank,strength,rs_ratio,rs_mom,quadrant,trail[6][2],ret{1w..1y},exc{...},above50,above200,flow{intensity,pct,label,avg_1y,avg_5y,z_1y,net20_usd,dv20_usd,share,share_avg_1y},spark[60]}, flows{ranking,inflow,outflow,total_net20_usd}, aux{QQQ,IWM,RSP,TLT,GLD,HYG}, watch[], method{}`。
`docs/cockpit/backtest.json`（~28 KB）：`regime{stats,base,transition,strategy,equity,episodes,n_switches}, sectors{sector_momentum{horizons,top3,bottom3,spy,equal_weight,long_short,by_rank,yearly_top3_minus_spy,equity},rrg,regime_heatmap}, flows{ic,quartile_spread,extreme}, caveats[]`。

快速讀法（主對話用 jq，不要整檔 Read）：
```bash
jq -c '.regime|{state,score,since,pillars:(.pillars|map_values(.score))}' docs/cockpit/data.json
jq -r '.sectors[]|[.rank,.symbol,.strength,.quadrant,.flow.pct,.flow.label]|@tsv' docs/cockpit/data.json
```

## 5. 「我的持倉」分頁（2026-11-05 Jake：不讀持倉表，改成 dashboard 可增減持倉）

- 部位存在瀏覽器 `localStorage`（key `kiwi.cockpit.holdings.v1`），**不上傳、不進 repo、公開頁不會洩漏**；匯出／匯入 JSON 跨裝置。
- 每筆：代碼、名稱、板塊、股數、成本、現價（選填）、幣別、備註。表格把每筆對到所屬板塊的強度排名／RRG／資金流；代碼若在 `config/cockpit_watch.json` 就再加個股自己的趨勢／RS／資金流（Yahoo 代碼：台股上市 `2303.TW`、上櫃 `8271.TWO`——**8271.TWO 在 Yahoo 回「No data」**，待查正確代碼）。
- 板塊曝險長條以市值（同幣別）計算，旁邊附該板塊的排名與資金流狀態；regime 對照只列回測裡的曝險規則，標明非建議。

## 5b. 台股版（2026-11-05 加入；Jake：「請加入台股板塊」）

頁面上方「美股 · S&P 板塊 ／ 台股 · 類股」切換，①–④ 整套換成台股資料；⑤ 持倉的板塊下拉同時列兩個市場。

| 項目 | 台股做法 | 檔案 |
|---|---|---|
| 指數 | 證交所 20 個類股價格指數 + 發行量加權（TAIEX）。歷史 2019-01 → 今一次性從 TradingView 取得（`TWSE:IX00xx`，與證交所 2026-11-04 收盤逐檔核對一致）；之後每日由證交所 `MI_INDEX?type=IND` 追加 | `data/tw/tv/IX00xx.json`、`data/tw/sector_index.csv` |
| Regime | 趨勢 45% + 廣度 35% + 波動 20%（沒有免費 VIX／信用利差）。門檻同美股 | `scripts/market_cockpit_tw.py` |
| 強弱／RRG | 同美股版，基準 = TAIEX | 同上 |
| 資金流向 | **真實法人資金**：證交所 T86 三大法人每檔買賣超股數 × 當日收盤價（`MI_INDEX?type=ALLBUT0999`），依 `t187ap03_L` 產業別彙總 → 20 日淨買超 ÷ 20 日成交金額；外資／投信／自營分列 | `scripts/fetch_tw_sectors.py` → `data/tw/sector_flow.csv` |
| 輔助 | 外資台指期淨部位、融資強度（沿用 `docs/taiwan_data.json`） | — |

**證交所 WAF 速率限制**（2026-11-05 實測）：連續約 15 個請求後回 307 導向「因為安全性考量…」，封鎖持續 ≥10 分鐘；`fetch_tw_sectors.py` 每請求睡 12 秒、被擋睡 10 分鐘、可續跑。法人流向歷史因此只能**逐日累積**（2025-11 起回填中；每日 runner 跑 `--update` 會順便往回補），百分位與 1 年均值在樣本滿 60／120 日前不顯示，回測在滿 6 個月前不算。

台股回測重點（2019-01 → 2026-11，價格指數、無成本）：類股動能 **Top5 − Bottom5 年化 +18%、t = 2.3**；回看期越長越強（6M +19.5% t 2.7、12-1 +22.9% t 2.7）——與美股「薄」的結果形成對比。RRG 領先象限比落後象限未來 21 日超額高 1.3 個百分點（但所有象限絕對超額為負：加權指數由台積電主導，多數類股本來就跑輸）。Regime 曝險規則：CAGR 17.5% vs 買進持有 20.2%，MDD −13% vs −29%。

## 6. 維運

- 本機／雲端 session 重算：`cd projects/avi-v5 && python3 scripts/market_cockpit.py --cache <scratch>/cache`（約 30 秒；快取只給研究用）。
- **每日自動更新尚未接上**：需要在 `.github/workflows/update-dashboard.yml` 的「Update crash-risk board data」之後加兩步，並把產出加進 `git add`。改 workflow 要 Jake 核准（CLAUDE.md §0），所以本輪只把 patch 寫在這裡：

```yaml
      # 全局觀測台（docs/cockpit/）台股資料：證交所類股指數追加 + 三大法人流向（每日 3 個請求 + 往回補歷史）。
      # 證交所 WAF 很兇，腳本自己限速；跑不完就下次續。best-effort。
      - name: Fetch TW sector data for cockpit (best-effort)
        working-directory: projects/avi-v5
        timeout-minutes: 25
        continue-on-error: true
        run: python scripts/fetch_tw_sectors.py --update --sleep 8 --cooldown 120 --max-block 3 || true

      # 全局觀測台（docs/cockpit/）：regime / 板塊強弱 / 資金流向 + 回測，美股 + 台股。2026-11-05 建立。best-effort，永不擋 dashboard。
      - name: Update market cockpit data (best-effort)
        working-directory: projects/avi-v5
        timeout-minutes: 8
        continue-on-error: true
        run: python scripts/market_cockpit.py || true
```
```yaml
          git add docs/cockpit/*.json projects/avi-v5/data/tw/*.csv projects/avi-v5/data/tw/holidays.txt 2>/dev/null || true
```
- 圖表用 cdn.jsdelivr 的 Chart.js 4.4.0（與主頁相同）。雲端容器打不到任何 CDN；要本機截圖測試就 `npm pack chart.js@4.4.0` 後用 Playwright `page.route` 餵本機檔。頁面在 Chart.js 載不到時會退化成「表格仍可讀、圖表位置顯示提示」。
- 本頁沒有 Telegram 推播；若要「regime 切換時推播」，在 daily-alert 讀 `data.json.regime.state` 與前一日比較即可（未做）。
