# _SOURCE_PROBE — 有価証券報告書來源探測（JEM 否證 #3）

> 由 `fetch_jp_disclosures.py` 在 runner 上執行。更新：2026-08-23T03:03:52+00:00
> **為什麼有這支**：2026-08-20 Jake 多次嘗試註冊 EDINET API key 失敗（登入問題）。
> 與其讓他繼續跟註冊表單纏鬥，不如讓 runner 直接回報**哪一條路是通的**。

**怎麼讀**：`200` ＝這條路通（但仍要看 body 是不是錯誤訊息，見 EDINET 那列的前例）；
`403/404` ＝這條不通或路徑錯；`ERR` ＝連線層失敗。
**對照組 TDnet 若也失敗 → 是 runner 網路問題，不是站點問題，先別改資料源。**

| 來源 | 狀態 | 備註 | body 前 180 字 |
|---|---|---|---|
| [EDINET v2 API（無 key）](https://api.edinet-fsa.go.jp/api/v2/documents.json?date=2026-08-18&type=2) | **200** | 已知：HTTP 200 但 body 為 401 invalid subscription key | `{"StatusCode": 401,"message": "Access denied due to invalid subscription key.Make sure to provide a valid key for an active subscription."}` |
| [EDINET 網頁介面（不需 key？）](https://disclosure2.edinet-fsa.go.jp/WEEK0010.aspx) | **200** | 未驗證：網頁 UI 若可達，或可不透過 API 取文件 | `<!DOCTYPE html> <html lang="ja"> <head> <meta name="viewport" content="width=device-width,initial-scale=1"/> <meta name="description" content="EDINETの閲覧サイトです。有�` |
| [有報キャッチャー ufocatch 首頁](https://ufocatch.com/) | **200** | 未驗證：EDINET/TDnet XBRL 的第三方鏡像，宣稱免費且不需金鑰 | `<!DOCTYPE html> <html lang="ja"> <head>     <!-- Google Tag Manager -->     <script>(function(w,d,s,l,i){w[l]=w[l]//[];w[l].push({'gtm.start':     new Date().getTime(),event` |
| [ufocatch Atom（候選路徑，純猜測）](https://resource.ufocatch.com/atom/edinetx/query/6855) | **404** | ⚠️ 路徑為猜測，回 404 不代表服務不存在，只代表這個路徑不對 | `<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv` |
| [JEM 公司 IR 站](https://www.jem-net.co.jp/) | **200** | 未驗證：雲端 403；runner 未測 | `<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja-jp` |
| [TDnet 一覽（對照組）](https://www.release.tdnet.info/inbs/I_list_001_20260818.html) | **200** | 已知：runner 可達 HTTP 200 —— 若這條也失敗，代表是 runner 網路問題不是站點問題 | `<!DOCTYPE html> <html> <head> <title>適時開示情報閲覧サービス - 開示情報一覧</title> <meta content="text/html" charset="UTF-8" http-equiv="content-type"> <me` |

## 下一步（給未來 session）

1. 若 **ufocatch 首頁 200** → 值得投資去找它真正的 API/檔案路徑（Atom 那列的猜測路徑不對不代表服務不可用）。
2. 若 **EDINET 網頁介面 200** → 可走網頁抓取路線，**完全繞過 API key**，Jake 的註冊問題就不必解決。
3. 若全數失敗且 TDnet 也失敗 → 是 runner 網路，不要改資料源。
4. **在有 200 的路徑被實際抓到內容之前，JEM 否證 #3 的狀態是「無法判定」，不是「還沒做」。**
