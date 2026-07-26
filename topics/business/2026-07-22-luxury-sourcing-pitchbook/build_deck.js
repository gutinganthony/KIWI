const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
pres.author = "Jake";
pres.title = "精品級供應鏈接入服務 — 合作討論";

// Palette: luxury leather goods tones
const INK = "1C1C1E";      // near-black charcoal (dominant)
const CAMEL = "B08D57";    // camel / bronze accent
const CREAMTXT = "EDE8E1"; // light text on dark
const MUTED = "6E6E73";    // muted gray on light
const CARD = "F2F0ED";     // subtle warm card fill
const WHITE = "FFFFFF";
const RED = "9B2C2C";
const GREEN = "3F6B52";

const HF = "Cambria";  // header font
const BF = "Calibri";  // body font

// ---------- helpers ----------
function darkSlide() {
  const s = pres.addSlide();
  s.background = { color: INK };
  return s;
}
function lightSlide() {
  const s = pres.addSlide();
  s.background = { color: WHITE };
  return s;
}
function title(s, text, opts = {}) {
  s.addText(text, {
    x: 0.6, y: opts.y || 0.45, w: 12.1, h: 0.75,
    fontFace: HF, fontSize: opts.size || 34, bold: true,
    color: opts.color || INK, align: "left", margin: 0,
  });
}
function kicker(s, text, color) {
  s.addText(text, {
    x: 0.6, y: 0.2, w: 12.1, h: 0.3,
    fontFace: BF, fontSize: 12, bold: true, charSpacing: 2,
    color: color || CAMEL, align: "left", margin: 0,
  });
}
function numCircle(s, n, x, y, d, fill, txtColor) {
  s.addShape(pres.ShapeType.ellipse, {
    x, y, w: d, h: d, fill: { color: fill || CAMEL },
  });
  s.addText(String(n), {
    x, y, w: d, h: d, fontFace: HF, fontSize: d > 0.5 ? 18 : 13,
    bold: true, color: txtColor || WHITE, align: "center", valign: "middle", margin: 0,
  });
}
function footnote(s, text, color) {
  s.addText(text, {
    x: 0.6, y: 6.92, w: 12.1, h: 0.3,
    fontFace: BF, fontSize: 9.5, italic: true,
    color: color || MUTED, align: "left", margin: 0,
  });
}

// ============ 1. COVER ============
{
  const s = darkSlide();
  s.addShape(pres.ShapeType.ellipse, { x: 10.2, y: -1.4, w: 4.6, h: 4.6, fill: { color: CAMEL }, transparency: 82 });
  s.addShape(pres.ShapeType.ellipse, { x: 11.4, y: 4.6, w: 2.8, h: 2.8, fill: { color: CAMEL }, transparency: 88 });
  s.addText("合作提案 · 內部討論用", {
    x: 0.9, y: 1.5, w: 9, h: 0.35, fontFace: BF, fontSize: 13, bold: true,
    charSpacing: 3, color: CAMEL, margin: 0,
  });
  s.addText("精品級供應鏈\n接入服務", {
    x: 0.9, y: 2.05, w: 9.2, h: 2.1, fontFace: HF, fontSize: 52, bold: true,
    color: WHITE, lineSpacing: 58, margin: 0,
  });
  s.addText("把十年精品採購的供應商網絡與品質標準，\n變成新銳品牌買得到的服務", {
    x: 0.9, y: 4.3, w: 9.2, h: 0.9, fontFace: BF, fontSize: 17,
    color: CREAMTXT, lineSpacing: 28, margin: 0,
  });
  s.addShape(pres.ShapeType.line, { x: 0.9, y: 5.55, w: 2.2, h: 0, line: { color: CAMEL, width: 2 } });
  s.addText("Jake（策略 · 驗證 · 行銷）　×　夥伴（供應鏈 · 品質 · 執行）", {
    x: 0.9, y: 5.8, w: 10, h: 0.35, fontFace: BF, fontSize: 14, color: CREAMTXT, margin: 0,
  });
  s.addText("2026.07.22　v1.1（含市場占位查證）", {
    x: 0.9, y: 6.25, w: 10, h: 0.3, fontFace: BF, fontSize: 11, color: MUTED, margin: 0,
  });
  s.addNotes("這份是給我們兩人討論用的，不是對外募資簡報。目標：一個小時內把「做不做、怎麼分工、怎麼驗證」談出結論。");
}

// ============ 2. 一句話 ============
{
  const s = lightSlide();
  kicker(s, "我 們 要 做 什 麼");
  s.addText("「用精品的供應鏈標準，\n做你的品牌。」", {
    x: 0.6, y: 0.9, w: 8.4, h: 1.9, fontFace: HF, fontSize: 38, bold: true,
    color: INK, lineSpacing: 48, margin: 0,
  });
  s.addText("服務對象：想做出精品級品質、但吃不到精品供應鏈的新銳設計師品牌、高端訂製與品牌禮贈需求方。", {
    x: 0.6, y: 2.95, w: 8.4, h: 0.8, fontFace: BF, fontSize: 15, color: MUTED, lineSpacing: 24, margin: 0,
  });

  const items = [
    ["01", "選 · 配對", "從品類需求反推供應商：誰做得出這個品質、願不願意接小單、真實成本多少。"],
    ["02", "打樣 · 開發", "帶著品牌走完打樣到定版，翻譯「設計語言」成「工廠語言」。"],
    ["03", "量產 · 駐廠 QC", "小批量生產與親自驗貨，對品質負責——不是介紹完就走的中介。"],
  ];
  let y = 3.95;
  items.forEach(([n, h, d]) => {
    s.addShape(pres.ShapeType.roundRect, { x: 0.6, y, w: 12.1, h: 0.88, fill: { color: CARD }, rectRadius: 0.06 });
    numCircle(s, n, 0.85, y + 0.19, 0.5);
    s.addText(h, { x: 1.55, y: y + 0.13, w: 2.2, h: 0.32, fontFace: HF, fontSize: 15, bold: true, color: INK, margin: 0 });
    s.addText(d, { x: 1.55, y: y + 0.45, w: 10.8, h: 0.34, fontFace: BF, fontSize: 12.5, color: MUTED, margin: 0 });
    y += 1.0;
  });
  s.addNotes("這一頁要先對齊：我們賣的是「執行與品質責任」，不是「介紹工廠」。介紹費模式已經被 1688 殺死了。");
}

// ============ 3. 為什麼是我們 ============
{
  const s = lightSlide();
  kicker(s, "為 什 麼 是 我 們");
  title(s, "兩邊的資產剛好互補", { y: 0.55 });

  // left card
  s.addShape(pres.ShapeType.roundRect, { x: 0.6, y: 1.6, w: 5.85, h: 3.3, fill: { color: INK }, rectRadius: 0.08 });
  s.addText("夥伴｜供給側的鑰匙", { x: 0.95, y: 1.85, w: 5.2, h: 0.35, fontFace: HF, fontSize: 17, bold: true, color: CAMEL, margin: 0 });
  s.addText([
    { text: "供應商地圖：長三角/亞洲精品級廠、真實成本與起訂量", options: { bullet: true, breakLine: true } },
    { text: "品質之眼：一眼分辨精品級與量販級的 QC 能力", options: { bullet: true, breakLine: true } },
    { text: "買手紀律：SKU 規劃、訂貨與售罄率思維", options: { bullet: true, breakLine: true } },
    { text: "十年 Burberry 上海採購 · 現有完整時間投入", options: { bullet: true } },
  ], { x: 0.95, y: 2.35, w: 5.2, h: 2.3, fontFace: BF, fontSize: 13, color: CREAMTXT, paraSpaceAfter: 10, margin: 0 });

  // right card
  s.addShape(pres.ShapeType.roundRect, { x: 6.85, y: 1.6, w: 5.85, h: 3.3, fill: { color: CARD }, rectRadius: 0.08 });
  s.addText("Jake｜需求側的方法", { x: 7.2, y: 1.85, w: 5.2, h: 0.35, fontFace: HF, fontSize: 17, bold: true, color: INK, margin: 0 });
  s.addText([
    { text: "驗證方法論：訪談設計、真 offer 測試、停損判準", options: { bullet: true, breakLine: true } },
    { text: "行銷操盤：內容獲客與品牌敘事", options: { bullet: true, breakLine: true } },
    { text: "研究基礎設施：市場、法規、競品的快速掃描能力", options: { bullet: true, breakLine: true } },
    { text: "資本與財務紀律：P&L、單位經濟、風險控管", options: { bullet: true } },
  ], { x: 7.2, y: 2.35, w: 5.2, h: 2.3, fontFace: BF, fontSize: 13, color: INK, paraSpaceAfter: 10, margin: 0 });

  s.addShape(pres.ShapeType.roundRect, { x: 0.6, y: 5.15, w: 12.1, h: 1.15, fill: { color: CAMEL }, rectRadius: 0.08 });
  s.addText("交點：他握著「供給側瓶頸的鑰匙」，我握著「需求側驗證與放大的方法」。\n最好的生意會出現在這個交點上——而不是各自單獨能做的事情裡。", {
    x: 1.0, y: 5.3, w: 11.3, h: 0.85, fontFace: HF, fontSize: 15.5, bold: true, color: WHITE, lineSpacing: 24, margin: 0,
  });
  footnote(s, "誠實提醒：這個組合的最大隱藏風險不是市場，是「需要督促的執行者 × 沒空督促的策略者」——解法見第 10 頁。");
}

// ============ 4. 機會點 ============
{
  const s = lightSlide();
  kicker(s, "機 會 點");
  title(s, "為什麼是現在：四個同時打開的窗口", { y: 0.55 });

  const cards = [
    ["關稅重整期", "美國成衣關稅 2025 年 14.7% → 35.1%，65% 買家已在分散採購，但普遍受品質問題所苦、完整重整要 12–18 個月以上。", "品質與 QC 能力，正是重整期最稀缺的東西。"],
    ["精品透明化危機", "2024–25 義大利精品轉包血汗工廠司法調查（Loro Piana／Valentino／Dior／Armani 供應鏈）。", "「經審核、可溯源」變成能賣錢的敘事。"],
    ["利基資訊仍稀缺", "通用代工中介已被 1688／阿里透明化殺死，但「精品層代工中介」查無具名業者。", "十年內部知識在這一層仍有真實稀缺性。"],
    ["小單技術成熟", "百件級快反產能已成立（如犀牛智造）；義大利平台 MakersValley 甚至做到 1 件起訂。", "「高工藝 × 極小單」的營運模式存在先例。"],
  ];
  const pos = [[0.6, 1.55], [6.85, 1.55], [0.6, 4.05], [6.85, 4.05]];
  cards.forEach(([h, d, so], i) => {
    const [x, y] = pos[i];
    s.addShape(pres.ShapeType.roundRect, { x, y, w: 5.85, h: 2.25, fill: { color: CARD }, rectRadius: 0.08 });
    numCircle(s, i + 1, x + 0.3, y + 0.28, 0.42);
    s.addText(h, { x: x + 0.85, y: y + 0.28, w: 4.7, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: INK, valign: "middle", margin: 0 });
    s.addText(d, { x: x + 0.32, y: y + 0.82, w: 5.2, h: 0.85, fontFace: BF, fontSize: 12, color: MUTED, lineSpacing: 17, margin: 0 });
    s.addText("→ " + so, { x: x + 0.32, y: y + 1.72, w: 5.2, h: 0.4, fontFace: BF, fontSize: 12, bold: true, color: CAMEL, lineSpacing: 16, margin: 0 });
  });
  footnote(s, "資料：2026-07-22 網路查證（搜尋摘要層級，未經全文核實）；關稅數字為公開報導引用。");
}

// ============ 5. 市場實證（案例） ============
{
  const s = lightSlide();
  kicker(s, "案 例 · 市 場 實 證");
  title(s, "這個品類已經有人做——他們證明了什麼", { y: 0.55 });

  const rows = [
    ["Pietra", "美國 · sourcing 市集", "募資 $36M ｜ 28 人", "多年後模式未變，仍在營運", "品類能活，但沒有爆發"],
    ["Italic", "美國 · 同廠平替", "募資 $86.9M ｜ 71 人", "已從強制會員牆鬆綁為一般電商", "重資本也難把它做大"],
    ["MakersValley", "義大利 · 媒合平台", "1 件起訂", "高工藝 × 極小單的模式先例", "小單門檻可以被設計掉"],
    ["Sourcify / Maker's Row", "美國 · 找廠平台", "通用品類為主", "非精品層，資訊透明化受害者", "通用中介的價值已被侵蝕"],
    ["QIMA", "香港起家 · 驗廠檢驗", "規模化 B2B 服務", "把「品質查核」做成產品", "QC 本身就是可收費的產品"],
  ];
  // header
  const cols = [0.6, 3.05, 5.55, 7.55, 10.35];
  const widths = [2.4, 2.45, 1.95, 2.75, 2.35];
  const heads = ["業者", "定位", "規模／特徵", "現況", "對我們的意義"];
  heads.forEach((h, i) => {
    s.addText(h, { x: cols[i], y: 1.55, w: widths[i], h: 0.3, fontFace: BF, fontSize: 11, bold: true, charSpacing: 1, color: CAMEL, margin: 0 });
  });
  let y = 1.95;
  rows.forEach((r, ri) => {
    if (ri % 2 === 0) {
      s.addShape(pres.ShapeType.rect, { x: 0.5, y: y - 0.06, w: 12.3, h: 0.92, fill: { color: CARD } });
    }
    r.forEach((cell, ci) => {
      s.addText(cell, {
        x: cols[ci], y: y, w: widths[ci], h: 0.8,
        fontFace: ci === 0 ? HF : BF, fontSize: ci === 0 ? 13.5 : 11.5,
        bold: ci === 0, color: ci === 4 ? INK : MUTED, valign: "middle", lineSpacing: 15, margin: 0,
      });
    });
    y += 0.98;
  });
  footnote(s, "查證日 2026-07-22。募資與人數為公開資料庫數字；未查到任何專門經營「精品層代工中介」的具名中國／香港業者。");
  s.addNotes("重點不是抄他們，是他們替我們把天花板和地板都測出來了：品類能活（地板），但別做 VC 夢（天花板）。");
}

// ============ 6. 三個結論 ============
{
  const s = darkSlide();
  kicker(s, "案 例 帶 來 的 三 個 結 論", CAMEL);
  title(s, "地板、天花板、以及那道縫", { y: 0.55, color: WHITE });

  const stats = [
    ["地板", "存在", "頭部業者活了多年沒死。\n這門生意能養活人。", GREEN],
    ["天花板", "有限", "燒掉 $36M / $86.9M\n仍是小眾生意。別做 VC 夢。", CAMEL],
    ["那道縫", "空白", "精品層代工中介\n查無具名業者。", WHITE],
  ];
  stats.forEach(([label, big, desc, col], i) => {
    const x = 0.6 + i * 4.15;
    s.addShape(pres.ShapeType.roundRect, { x, y: 1.75, w: 3.85, h: 3.5, fill: { color: "2A2A2E" }, rectRadius: 0.08 });
    s.addText(label, { x: x + 0.4, y: 2.05, w: 3.1, h: 0.35, fontFace: BF, fontSize: 13, bold: true, charSpacing: 2, color: MUTED, margin: 0 });
    s.addText(big, { x: x + 0.4, y: 2.45, w: 3.1, h: 1.0, fontFace: HF, fontSize: 44, bold: true, color: col, margin: 0 });
    s.addText(desc, { x: x + 0.4, y: 3.6, w: 3.15, h: 1.3, fontFace: BF, fontSize: 13, color: CREAMTXT, lineSpacing: 20, margin: 0 });
  });

  s.addText("結論：這是一門「現金流 ＋ 市場情報」的生意，不是規模生意。\n它的最大價值，是用最低成本探出「哪個品類的需求最兇」，再決定要不要升級成自有品牌或二手精品。", {
    x: 0.6, y: 5.6, w: 12.1, h: 1.0, fontFace: HF, fontSize: 15.5, bold: true, color: WHITE, lineSpacing: 25, margin: 0,
  });
}

// ============ 7. 商業模式 ============
{
  const s = lightSlide();
  kicker(s, "商 業 模 式");
  title(s, "三層收費：專案 · 佣金 · 月費", { y: 0.55 });

  const tiers = [
    ["打樣／開發專案費", "US$150 – 2,000", "約 NT$5,000 – 65,000", "一次性。從需求釐清到定版打樣，含供應商配對。", "現金流最快、也是最好的信任測試門檻。"],
    ["量產佣金", "3% – 10%", "隨訂單金額遞減", "按實際下單金額抽成，含駐廠 QC 與交期管理。", "客戶成長我們就成長，但要靠訂單量堆。"],
    ["月度 Retainer", "US$300 – 5,000", "約 NT$1萬 – 16萬 / 月", "長期供應鏈顧問：品類規劃、年度開發、供應商維護。", "唯一能讓收入穩定、可預測的一層。"],
  ];
  let y = 1.5;
  tiers.forEach(([name, price, sub, desc, note], i) => {
    s.addShape(pres.ShapeType.roundRect, { x: 0.6, y, w: 12.1, h: 1.55, fill: { color: i === 2 ? CARD : WHITE }, line: { color: "DDD8D1", width: 1 }, rectRadius: 0.08 });
    numCircle(s, i + 1, 0.95, y + 0.5, 0.55);
    s.addText(name, { x: 1.75, y: y + 0.22, w: 3.3, h: 0.4, fontFace: HF, fontSize: 16, bold: true, color: INK, margin: 0 });
    s.addText(desc, { x: 1.75, y: y + 0.68, w: 4.9, h: 0.7, fontFace: BF, fontSize: 12, color: MUTED, lineSpacing: 17, margin: 0 });
    s.addText(price, { x: 6.9, y: y + 0.28, w: 2.6, h: 0.45, fontFace: HF, fontSize: 21, bold: true, color: CAMEL, margin: 0 });
    s.addText(sub, { x: 6.9, y: y + 0.78, w: 2.6, h: 0.3, fontFace: BF, fontSize: 11, color: MUTED, margin: 0 });
    s.addText(note, { x: 9.7, y: y + 0.35, w: 2.85, h: 0.85, fontFace: BF, fontSize: 11.5, italic: true, color: INK, lineSpacing: 16, margin: 0 });
    y += 1.68;
  });
  footnote(s, "行情來源多為 sourcing agent 自營網站宣稱值，非審計數據——請當「量級參考」而非定價依據。我們的高執行密度定位應收上緣。");
}

// ============ 8. 單位經濟 ============
{
  const s = lightSlide();
  kicker(s, "單 位 經 濟");
  title(s, "溫飽線：我們需要幾個活躍客戶？", { y: 0.55 });

  s.addChart(pres.ChartType.bar, [
    {
      name: "年營收（萬元台幣）",
      labels: ["保守情境\n10 客戶", "中性情境\n12 客戶", "積極情境\n15 客戶"],
      values: [250, 540, 900],
    },
  ], {
    x: 0.6, y: 1.55, w: 6.6, h: 4.2,
    barDir: "col", chartColors: [CAMEL],
    showTitle: false, showLegend: false,
    showValue: true, dataLabelPosition: "outEnd",
    dataLabelColor: INK, dataLabelFontFace: BF, dataLabelFontSize: 12, dataLabelFormatCode: '#,##0"萬"',
    catAxisLabelColor: INK, catAxisLabelFontFace: BF, catAxisLabelFontSize: 11,
    valAxisLabelColor: MUTED, valAxisLabelFontFace: BF, valAxisLabelFontSize: 10,
    valGridLine: { color: "E8E4DF", size: 1 }, catGridLine: { style: "none" },
    valAxisMaxVal: 1000, barGapWidthPct: 60,
  });

  s.addShape(pres.ShapeType.roundRect, { x: 7.5, y: 1.55, w: 5.2, h: 2.0, fill: { color: CARD }, rectRadius: 0.08 });
  s.addText("情境模型的假設", { x: 7.85, y: 1.75, w: 4.5, h: 0.35, fontFace: HF, fontSize: 15, bold: true, color: INK, margin: 0 });
  s.addText([
    { text: "每客戶年貢獻 NT$25–60 萬（打樣 + 佣金 + 月費混合）", options: { bullet: true, breakLine: true } },
    { text: "無庫存、無買量；主要成本＝兩人時間與差旅", options: { bullet: true, breakLine: true } },
    { text: "獲客靠內容與轉介紹，不靠廣告預算", options: { bullet: true } },
  ], { x: 7.85, y: 2.2, w: 4.5, h: 1.25, fontFace: BF, fontSize: 11.5, color: MUTED, paraSpaceAfter: 8, margin: 0 });

  s.addShape(pres.ShapeType.roundRect, { x: 7.5, y: 3.75, w: 5.2, h: 2.0, fill: { color: INK }, rectRadius: 0.08 });
  s.addText("關鍵數字", { x: 7.85, y: 3.95, w: 4.5, h: 0.35, fontFace: BF, fontSize: 12, bold: true, charSpacing: 2, color: CAMEL, margin: 0 });
  s.addText("8 – 15", { x: 7.85, y: 4.3, w: 4.5, h: 0.7, fontFace: HF, fontSize: 40, bold: true, color: WHITE, margin: 0 });
  s.addText("個活躍客戶＝兩人溫飽線。\n盈虧平衡極低，這是它作為「起手式」最大的優點。", {
    x: 7.85, y: 5.02, w: 4.5, h: 0.65, fontFace: BF, fontSize: 12, color: CREAMTXT, lineSpacing: 18, margin: 0,
  });
  footnote(s, "情境模型，非預測。收入結構會隨第一批客戶的真實成交金額大幅修正——第 12 頁的 pilot 就是要把這張表換成真數字。");
}

// ============ 9. 分工 ============
{
  const s = lightSlide();
  kicker(s, "結 構 · 分 工");
  title(s, "誰負責什麼：一個引擎，一個舵", { y: 0.55 });

  const rows = [
    ["策略 · 選題 · 驗證設計", "主責", "參與"],
    ["供給端：找廠 · 選品 · 談判 · QC · 交付", "—", "主責"],
    ["顧客訪談", "共同（互為盲編碼）", "共同"],
    ["行銷內容與獲客", "主責（設計）", "素材與案例產出"],
    ["財務 · P&L · 定價紀律", "主責", "提供成本數據"],
    ["日常推進與交付節奏", "不介入", "引擎"],
  ];
  const cx = [0.6, 6.6, 9.75];
  const cw = [5.85, 3.0, 2.95];
  ["工作領域", "Jake", "夥伴"].forEach((h, i) => {
    s.addText(h, { x: cx[i], y: 1.5, w: cw[i], h: 0.3, fontFace: BF, fontSize: 11, bold: true, charSpacing: 1, color: CAMEL, margin: 0 });
  });
  let y = 1.9;
  rows.forEach((r, ri) => {
    if (ri % 2 === 0) s.addShape(pres.ShapeType.rect, { x: 0.5, y: y - 0.05, w: 12.3, h: 0.66, fill: { color: CARD } });
    s.addText(r[0], { x: cx[0], y, w: cw[0], h: 0.56, fontFace: BF, fontSize: 13, color: INK, valign: "middle", margin: 0 });
    [1, 2].forEach((ci) => {
      const isMain = r[ci] === "主責" || r[ci] === "引擎";
      s.addText(r[ci], {
        x: cx[ci], y, w: cw[ci], h: 0.56, fontFace: BF, fontSize: 12.5,
        bold: isMain, color: isMain ? CAMEL : MUTED, valign: "middle", margin: 0,
      });
    });
    y += 0.72;
  });

  s.addShape(pres.ShapeType.roundRect, { x: 0.6, y: 6.15, w: 12.1, h: 0.72, fill: { color: INK }, rectRadius: 0.06 });
  s.addText("原則：日常推進由夥伴主導，Jake 不當監工——督促必須是系統，不是某個人的注意力（下一頁）。", {
    x: 1.0, y: 6.28, w: 11.3, h: 0.45, fontFace: HF, fontSize: 14, bold: true, color: WHITE, valign: "middle", margin: 0,
  });
}

// ============ 10. 督促系統 + 合夥條款 ============
{
  const s = lightSlide();
  kicker(s, "結 構 · 合 作 機 制");
  title(s, "把「督促」設計成系統", { y: 0.55 });
  s.addText("這案最大的隱藏風險不是市場，是「需要人督促的執行者 × 沒空督促的策略者」。\n解法不是硬擠時間，是用節奏與記分板取代注意力。", {
    x: 0.6, y: 1.32, w: 12.1, h: 0.7, fontFace: BF, fontSize: 13.5, color: MUTED, lineSpacing: 21, margin: 0,
  });

  const mechs = [
    ["週一戰略會", "90 分鐘", "Jake 主持，決策當場記錄。這是 Jake 的最低承諾，也是唯一固定投入。"],
    ["每日三行日報", "非同步", "做了什麼／下一步／卡在哪。可用機器人自動催收，不靠人情催。"],
    ["月度 P&L 對帳", "每月一次", "真實成本與收入攤在桌上，避免「感覺有在動」的錯覺。"],
  ];
  let x = 0.6;
  mechs.forEach(([h, tag, d], i) => {
    s.addShape(pres.ShapeType.roundRect, { x, y: 2.2, w: 3.85, h: 2.05, fill: { color: CARD }, rectRadius: 0.08 });
    numCircle(s, i + 1, x + 0.32, y_ = 2.45, 0.46);
    s.addText(h, { x: x + 0.9, y: 2.45, w: 2.6, h: 0.45, fontFace: HF, fontSize: 16, bold: true, color: INK, valign: "middle", margin: 0 });
    s.addText(tag, { x: x + 0.32, y: 3.02, w: 3.2, h: 0.28, fontFace: BF, fontSize: 11, bold: true, charSpacing: 1, color: CAMEL, margin: 0 });
    s.addText(d, { x: x + 0.32, y: 3.32, w: 3.25, h: 0.85, fontFace: BF, fontSize: 12, color: MUTED, lineSpacing: 17, margin: 0 });
    x += 4.15;
  });

  s.addShape(pres.ShapeType.roundRect, { x: 0.6, y: 4.55, w: 12.1, h: 1.95, fill: { color: INK }, rectRadius: 0.08 });
  s.addText("合夥條款：90 天試合作，先不談股權", { x: 1.0, y: 4.75, w: 11.3, h: 0.4, fontFace: HF, fontSize: 18, bold: true, color: CAMEL, margin: 0 });
  s.addText([
    { text: "先設 3 個里程碑合作一輪；90 天後依實際貢獻談分配——保護生意，也保護友誼。", options: { bullet: true, breakLine: true } },
    { text: "正式成立時股權一律 vesting 4 年 / 1 年 cliff，沒有例外。", options: { bullet: true, breakLine: true } },
    { text: "開工前先各自寫下：想做多大、能投入多少時間與錢、三年後想要什麼——寫下來，不是用講的。", options: { bullet: true } },
  ], { x: 1.0, y: 5.2, w: 11.2, h: 1.15, fontFace: BF, fontSize: 12.5, color: CREAMTXT, paraSpaceAfter: 6, margin: 0 });
  s.addNotes("90 天試合作的隱藏考題：夥伴在只有週會督促的情況下，能不能自驅推進。這比生意本身更需要被驗證。");
}

// ============ 11. 客戶交付流程 ============
{
  const s = lightSlide();
  kicker(s, "流 程 · 客 戶 交 付");
  title(s, "一個案子怎麼從詢問走到出貨", { y: 0.55 });

  const steps = [
    ["需求釐清", "品類 · 品質等級 · 數量 · 預算 · 時程"],
    ["供應商配對", "從供給清單反推 2–3 家候選"],
    ["打樣開發", "把設計語言翻譯成工廠語言"],
    ["報價定版", "真實成本攤開，客戶確認"],
    ["小批量產", "排程 · 物料 · 交期管理"],
    ["駐廠 QC", "親自驗貨，品質責任在我們"],
    ["交付物流", "含關務與跨境安排"],
    ["復盤回購", "售罄數據回饋下一季開發"],
  ];
  const perRow = 4;
  steps.forEach(([h, d], i) => {
    const col = i % perRow, row = Math.floor(i / perRow);
    const x = 0.6 + col * 3.1, y = 1.6 + row * 2.35;
    s.addShape(pres.ShapeType.roundRect, { x, y, w: 2.85, h: 1.95, fill: { color: row === 0 ? CARD : WHITE }, line: { color: "DDD8D1", width: 1 }, rectRadius: 0.08 });
    numCircle(s, i + 1, x + 0.28, y + 0.25, 0.44);
    s.addText(h, { x: x + 0.28, y: y + 0.82, w: 2.3, h: 0.35, fontFace: HF, fontSize: 15, bold: true, color: INK, margin: 0 });
    s.addText(d, { x: x + 0.28, y: y + 1.18, w: 2.35, h: 0.62, fontFace: BF, fontSize: 11, color: MUTED, lineSpacing: 15, margin: 0 });
    if (col < perRow - 1 && i < steps.length - 1) {
      s.addText("→", { x: x + 2.87, y: y + 0.72, w: 0.24, h: 0.4, fontFace: BF, fontSize: 16, color: CAMEL, align: "center", margin: 0 });
    }
  });
  s.addShape(pres.ShapeType.roundRect, { x: 0.6, y: 6.32, w: 12.1, h: 0.62, fill: { color: CAMEL }, rectRadius: 0.06 });
  s.addText("收費落點：① 打樣專案費　→　⑤⑥ 量產佣金　→　⑧ 轉為月度 retainer", {
    x: 1.0, y: 6.42, w: 11.3, h: 0.42, fontFace: HF, fontSize: 13.5, bold: true, color: WHITE, valign: "middle", margin: 0,
  });
}

// ============ 12. 90 天驗證 ============
{
  const s = lightSlide();
  kicker(s, "流 程 · 驗 證 路 線 圖");
  title(s, "90 天內知道這門生意成不成立", { y: 0.55 });

  const phases = [
    ["第 1–2 週", "驗供給（不是先找客戶）", [
      "法務檢查：競業／保密條款與供應商端風險",
      "產出「小單友善」供給清單：品類 × 起訂量 × 打樣週期 × 報價",
      "門檻：≥ 8 家願接小單的精品級廠",
    ], CAMEL],
    ["第 3–6 週", "驗需求", [
      "8–10 場目標客戶訪談（設計師品牌／高端訂製／品牌禮贈）",
      "收尾遞出真 offer：付費打樣專案訂金",
      "冷樣本 ≥ 3；兩人互為盲編碼，避免自我說服",
    ], INK],
    ["第 7–12 週", "驗交付與經濟", [
      "完整交付 3 個付費專案",
      "四指標裁決：交付品質／回購／轉介紹／實際時薪",
      "把第 8 頁的情境模型換成真實數字",
    ], GREEN],
  ];
  let y = 1.5;
  phases.forEach(([wk, name, items, col]) => {
    s.addShape(pres.ShapeType.roundRect, { x: 0.6, y, w: 2.5, h: 1.6, fill: { color: col }, rectRadius: 0.08 });
    s.addText(wk, { x: 0.75, y: y + 0.28, w: 2.2, h: 0.4, fontFace: HF, fontSize: 19, bold: true, color: WHITE, margin: 0 });
    s.addText(name, { x: 0.75, y: y + 0.78, w: 2.25, h: 0.6, fontFace: BF, fontSize: 12.5, color: WHITE, lineSpacing: 17, margin: 0 });
    s.addShape(pres.ShapeType.roundRect, { x: 3.3, y, w: 9.4, h: 1.6, fill: { color: CARD }, rectRadius: 0.08 });
    s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } })), {
      x: 3.65, y: y + 0.22, w: 8.8, h: 1.2, fontFace: BF, fontSize: 12.5, color: INK, paraSpaceAfter: 6, margin: 0,
    });
    y += 1.75;
  });
  footnote(s, "順序是刻意的：先驗供給再驗需求。供給清單湊不出來，後面的客戶訪談就沒有東西可賣。");
}

// ============ 13. 風險 ============
{
  const s = lightSlide();
  kicker(s, "風 險 與 停 損");
  title(s, "五個風險，兩條紅線", { y: 0.55 });

  const risks = [
    ["競業與保密", "他的離職協議是否有競業／NDA？更關鍵是供應商端——一線精品代工廠常被品牌綁保密與獨家。", "紅線", RED],
    ["MOQ 錯配", "「精品級 × 小單 × 有佐證」的組合公開查無。百件小單技術可行，但那是快時尚證明的。", "第一考題", RED],
    ["需求薄度", "台灣／亞洲願付精品級製造成本的客戶密度未知，可能要修正客群定義。", "訪談裁決", CAMEL],
    ["地緣逆風", "美國客戶去中國化中；主力客群應設定台／日／東南亞，或延伸越南雙軌。", "可控", MUTED],
    ["中介價值侵蝕", "1688 已殺死資訊差中介；防禦必須建立在 QC 執行與品質責任，而非介紹。", "定位解", MUTED],
  ];
  let y = 1.5;
  risks.forEach(([name, desc, tag, col]) => {
    s.addShape(pres.ShapeType.roundRect, { x: 0.6, y, w: 12.1, h: 0.92, fill: { color: CARD }, rectRadius: 0.06 });
    s.addText(name, { x: 0.95, y: y + 0.1, w: 2.4, h: 0.72, fontFace: HF, fontSize: 15, bold: true, color: INK, valign: "middle", margin: 0 });
    s.addText(desc, { x: 3.45, y: y + 0.1, w: 7.4, h: 0.72, fontFace: BF, fontSize: 11.5, color: MUTED, valign: "middle", lineSpacing: 16, margin: 0 });
    s.addShape(pres.ShapeType.roundRect, { x: 11.0, y: y + 0.24, w: 1.45, h: 0.44, fill: { color: col }, rectRadius: 0.08 });
    s.addText(tag, { x: 11.0, y: y + 0.24, w: 1.45, h: 0.44, fontFace: BF, fontSize: 11, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0 });
    y += 1.02;
  });

  s.addShape(pres.ShapeType.roundRect, { x: 0.6, y: 6.15, w: 12.1, h: 0.75, fill: { color: INK }, rectRadius: 0.06 });
  s.addText("Kill criteria（事前講好）：法務不過 ＝ 停　｜　供給清單 < 8 家 ＝ 轉做跨境二手精品　｜　訪談 offer 零轉化 ＝ 換客群或收攤", {
    x: 1.0, y: 6.28, w: 11.3, h: 0.5, fontFace: HF, fontSize: 13, bold: true, color: WHITE, valign: "middle", margin: 0,
  });
}

// ============ 14. 下一步 ============
{
  const s = darkSlide();
  s.addShape(pres.ShapeType.ellipse, { x: -1.6, y: 4.6, w: 4.4, h: 4.4, fill: { color: CAMEL }, transparency: 86 });
  kicker(s, "下 一 步", CAMEL);
  title(s, "兩週內要發生的四件事", { y: 0.55, color: WHITE });

  const acts = [
    ["對齊談話", "各自寫下目標、可投入的時間與錢、三年後想要什麼（2 小時）"],
    ["法務檢查", "競業／保密條款盤點——這是紅線，先查再動任何一家廠"],
    ["供給清單", "≥ 8 家願接小單的精品級廠：品類 × MOQ × 打樣週期 × 報價"],
    ["訪談名單", "10 個目標客戶具名清單，含 ≥ 3 個非人脈的冷樣本"],
  ];
  let y = 1.5;
  acts.forEach(([h, d], i) => {
    s.addShape(pres.ShapeType.roundRect, { x: 0.6, y, w: 6.9, h: 0.95, fill: { color: "2A2A2E" }, rectRadius: 0.06 });
    numCircle(s, i + 1, 0.9, y + 0.24, 0.47);
    s.addText(h, { x: 1.55, y: y + 0.12, w: 2.0, h: 0.35, fontFace: HF, fontSize: 15, bold: true, color: CAMEL, margin: 0 });
    s.addText(d, { x: 1.55, y: y + 0.46, w: 5.7, h: 0.4, fontFace: BF, fontSize: 11.5, color: CREAMTXT, margin: 0 });
    y += 1.06;
  });

  s.addShape(pres.ShapeType.roundRect, { x: 7.9, y: 1.5, w: 4.8, h: 4.05, fill: { color: CAMEL }, rectRadius: 0.08 });
  s.addText("今天要談出結論的五題", { x: 8.25, y: 1.75, w: 4.1, h: 0.4, fontFace: HF, fontSize: 17, bold: true, color: WHITE, margin: 0 });
  s.addText([
    { text: "這門生意的天花板，我們兩個都能接受嗎？", options: { bullet: true, breakLine: true } },
    { text: "他的競業／保密狀況實際上是什麼？", options: { bullet: true, breakLine: true } },
    { text: "供給清單兩週內拿得出來嗎？", options: { bullet: true, breakLine: true } },
    { text: "各自能投入多少時間？錢從哪裡來？", options: { bullet: true, breakLine: true } },
    { text: "90 天後如果數字不好看，我們願意收手嗎？", options: { bullet: true } },
  ], { x: 8.25, y: 2.3, w: 4.15, h: 3.0, fontFace: BF, fontSize: 13, color: WHITE, paraSpaceAfter: 12, margin: 0 });

  s.addText("先驗供給，再驗需求，最後才驗經濟。\n每一關都設好停損——這樣就算不做，我們也只花了 90 天，換到一整份市場情報。", {
    x: 0.6, y: 5.85, w: 12.1, h: 0.9, fontFace: HF, fontSize: 14.5, bold: true, color: CREAMTXT, lineSpacing: 23, margin: 0,
  });
}

pres.writeFile({ fileName: "/tmp/claude-0/-home-user-KIWI/a4b12570-e6f9-58ab-9368-765fb1f37307/scratchpad/精品供應鏈接入服務_合作討論_20260722.pptx" })
  .then((f) => console.log("WROTE:", f));
