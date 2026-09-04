# _SOURCE_PROBE — 有価証券報告書來源探測（JEM 否證 #3）

> 由 `fetch_jp_disclosures.py` 在 runner 上執行。更新：2026-09-04T22:36:27+00:00
> **為什麼有這支**：2026-08-20 Jake 多次嘗試註冊 EDINET API key 失敗（登入問題）。
> 與其讓他繼續跟註冊表單纏鬥，不如讓 runner 直接回報**哪一條路是通的**。

**怎麼讀**：`200` ＝這條路通（但仍要看 body 是不是錯誤訊息，見 EDINET 那列的前例）；
`403/404` ＝這條不通或路徑錯；`ERR` ＝連線層失敗。
**對照組 TDnet 若也失敗 → 是 runner 網路問題，不是站點問題，先別改資料源。**

| 來源 | 狀態 | 備註 | body 前 180 字 |
|---|---|---|---|
| [EDINET v2 API（無 key）](https://api.edinet-fsa.go.jp/api/v2/documents.json?date=2026-08-18&type=2) | **200** | 已知：HTTP 200 但 body 為 401 invalid subscription key | `{"StatusCode": 401,"message": "Access denied due to invalid subscription key.Make sure to provide a valid key for an active subscription."}` |
| [EDINET 網頁介面（不需 key？）](https://disclosure2.edinet-fsa.go.jp/WEEK0010.aspx) | **200** | 未驗證：網頁 UI 若可達，或可不透過 API 取文件 | `<!DOCTYPE html> <html lang="ja"> <head> <meta name="viewport" content="width=device-width,initial-scale=1"/> <meta name="description" content="EDINETの閲覧サイトです。有価証券報告書、有価証券届出書、大量保有報告` |
| [有報キャッチャー ufocatch 首頁](https://ufocatch.com/) | **200** | 未驗證：EDINET/TDnet XBRL 的第三方鏡像，宣稱免費且不需金鑰 | `<!DOCTYPE html> <html lang="ja"> <head>     <!-- Google Tag Manager -->     <script>(function(w,d,s,l,i){w[l]=w[l]//[];w[l].push({'gtm.start':     new Date().getTime(),event:'` |
| [ufocatch Atom（候選路徑，純猜測）](https://resource.ufocatch.com/atom/edinetx/query/6855) | **403** | ⚠️ 路徑為猜測，回 404 不代表服務不存在，只代表這個路徑不對 | `<!DOCTYPE html>
<!--[if lt IE 7]> <html class="no-js ie6 oldie" lang="en-US"> <![endif]-->
<!--[if IE 7]>    <html class="no-js ie7 oldie" lang="en-US"> <![endif]-->
<!--[if IE 8]>` |
| [JEM 公司 IR 站](https://www.jem-net.co.jp/) | **200** | 未驗證：雲端 403；runner 未測 | `<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja-jp` |
| [TDnet 一覽（對照組）](https://www.release.tdnet.info/inbs/I_list_001_20260818.html) | **200** | 已知：runner 可達 HTTP 200 —— 若這條也失敗，代表是 runner 網路問題不是站點問題 | `<!DOCTYPE html> <html> <head> <title>適時開示情報閲覧サービス - 開示情報一覧</title> <meta content="text/html" charset="UTF-8" http-equiv="content-type"> <meta name="robots" content="noindex,no` |
| [ufocatch 檢索頁（猜測）](https://ufocatch.com/Search.aspx?q=6855) | **404** | ⚠️ 猜測路徑。回 404 只代表這個路徑不對，不代表服務不可用 | `<!DOCTYPE html>
<html>
    <head>
        <title>リソースが見つかりませんでした。</title>
        <meta name="viewport" content="width=device-width" />
        <style>
         body {font-fa` |
| [ufocatch 說明頁（已知存在）](https://ufocatch.com/about.aspx) | **200** | 對照：此頁確實存在。若它 200 而檢索頁 404 → 站可用、只是路徑要找 | `<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> <html xmlns="http://www.w3.org/1999/xhtml" > <head id="c` |
| [EDINET 書類検索（猜測）](https://disclosure2.edinet-fsa.go.jp/week0020.aspx) | **200** | ⚠️ 猜測路徑（WEEK0010 是首頁，書類検索可能是別的 aspx） | `<!DOCTYPE html> <html lang="ja"> <head> <meta name="viewport" content="width=device-width,initial-scale=1"/> <meta name="description" content="開示情報利用者用トップ画面（英語）"/> <meta name="appl` |

## 下一步（給未來 session）

1. 若 **ufocatch 首頁 200** → 值得投資去找它真正的 API/檔案路徑（Atom 那列的猜測路徑不對不代表服務不可用）。
2. 若 **EDINET 網頁介面 200** → 可走網頁抓取路線，**完全繞過 API key**，Jake 的註冊問題就不必解決。
3. 若全數失敗且 TDnet 也失敗 → 是 runner 網路，不要改資料源。
4. **在有 200 的路徑被實際抓到內容之前，JEM 否證 #3 的狀態是「無法判定」，不是「還沒做」。**


## 結構樣本（僅限回 200 者，供下一輪實作抓取用）

### EDINET v2 API（無 key）
`https://api.edinet-fsa.go.jp/api/v2/documents.json?date=2026-08-18&type=2`

```html
{"StatusCode": 401,"message": "Access denied due to invalid subscription key.Make sure to provide a valid key for an active subscription."}
```

### EDINET 網頁介面（不需 key？）
`https://disclosure2.edinet-fsa.go.jp/WEEK0010.aspx`

```html
<!DOCTYPE html> <html lang="ja"> <head> <meta name="viewport" content="width=device-width,initial-scale=1"/> <meta name="description" content="EDINETの閲覧サイトです。有価証券報告書、有価証券届出書、大量保有報告書、公開買付届出書等の開示書類を閲覧できます。"/> <meta name="apple-mobile-web-app-capable" content="yes"/> <!--[if IE]><meta http-equiv="page-enter" content="blendTrans(Duration=0.1)"/><![endif]--> <meta name="fragment" content="!"/> <meta http-equiv="content-type" content="text/html; charset=UTF-8"/> <title>EDINET</title> <link rel="stylesheet" type="text/css" href="bootstrap/css/bootstrap.min.css?202682016474931"/> <link id="gxtheme_css_reference" rel="stylesheet" type="text/css" href="Resources/Japanese/ThemeBlue.css?202682016474931" /> <link rel="stylesheet" type="text/css" href="DVelop/Bootstrap/Shared/fontawesome_v5/css/fontawesome.min.css"/> <link rel="stylesheet" type="text/css" href="DVelop/Bootstrap/Shared/fontawesome_v5/css/all.min.css"/> <link rel="stylesheet" type="text/css" href="DVelop/Bootstrap/Shared/DVelopBootstrap.css"/> <script type="text/javascript" src="jquery.js?2136580" ></script><script type="text/javascript" src="bootstrap/js/bootstrap.min.js?202682016474931" ></script><script type="text/javascript" src="gxgral.js?2136580" ></script><script type="text/javascript" src="gxcfg.js?20268201645714" ></script><script type="text/javascript" src="js/CommonJS.js?20260828182232" ></script><script typ
```

### 有報キャッチャー ufocatch 首頁
`https://ufocatch.com/`

```html
<!DOCTYPE html> <html lang="ja"> <head>     <!-- Google Tag Manager -->     <script>(function(w,d,s,l,i){w[l]=w[l]//[];w[l].push({'gtm.start':     new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],     j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=     'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);     })(window,document,'script','dataLayer','GTM-KQ5J3GZM');</script>     <!-- End Google Tag Manager -->     <meta charset="utf-8" />     <meta name="viewport" content="width=device-width, initial-scale=1.0" />     <meta content="text/html; charset=utf-8" http-equiv="Content-Type" />     <meta name="google-site-verification" content="Me5AYZ0nFZgkYjEfhSMHKiX-3RtBCC4Pu3oj79fryxo" />     <meta name="description" content="EDINETやTDnetで公表された企業開示情報をご提供するサービスです。XBRLを活用し、会社属性情報などをデータ化しています。" />     <meta name="twitter:card" content="summary" />     <meta name="twitter:site" content="@ufocatch" />     <meta property="og:url" content="https://ufocatch.com/" />     <meta property="og:title" content="有報キャッチャー" />     <meta property="og:description" content="EDINETやTDnetで公表された企業開示情報をご提供するサービスです。XBRLを活用し、会社属性情報などをデータ化しています。" />     <meta property="og:image" content="http://ufocatc
```

### JEM 公司 IR 站
`https://www.jem-net.co.jp/`

```html
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja-jp" lang="ja-jp" dir="ltr"> <head> <link rel="stylesheet" href="/templates/business/css/normalize.css" type="text/css" media="print,screen" /> <link rel="stylesheet" href="/templates/business/css/template.css" type="text/css" media="print,screen" /> <link rel="stylesheet" media="screen and (max-width: 640px)" href="/templates/business/css/responsive.css" type="text/css" /> <script type="text/javascript"> if ((navigator.userAgent.indexOf('iPhone') > 0) // navigator.userAgent.indexOf('iPod') > 0 // navigator.userAgent.indexOf('Android') > 0) { document.write('<meta name="viewport" content="width=device-width">'); }else{ document.write('<meta name="format-detection" content="telephone=no">');     } </script>  <base href="https://www.jem-net.co.jp/" /> 	<meta http-equiv="content-type" content="text/html; charset=utf-8" /> 	<meta name="keywords" content="半導体,プローブカード,研究,開発,検査用部品,製造" /> 	<meta name="robots" content="index, follow" /> 	<meta name="description" content="日本電子材料株式会社は、兵庫県尼崎市に本社を置くプローブカード（半導体検査用部品）のメーカーです。" /> 	<title>日本電子材料株式会社-半導体検査用部品プローブカードの研究開発製造</title> 	<link href="/templates/business/favic
```

### TDnet 一覽（對照組）
`https://www.release.tdnet.info/inbs/I_list_001_20260818.html`

```html
<!DOCTYPE html> <html> <head> <title>適時開示情報閲覧サービス - 開示情報一覧</title> <meta content="text/html" charset="UTF-8" http-equiv="content-type"> <meta name="robots" content="noindex,nofollow"> <meta http-equiv="Pragma" content="no-cache"> <meta http-equiv="Cache-Control" content="no-cache"> <meta http-equiv="Expires" content="0"> <script type="text/javascript" charset="UTF-8" src="./js/I_JAVASCRIPT.js"></script> <script type="text/javascript" charset="UTF-8" src="./js/I_MENSEKI.js"></script> <script type="text/javascript" charset="UTF-8" src="./runtime/jquery-1.8.3.min.js"></script> <script type="text/javascript"> <!--   $(document).ready(function(){     $(".pagerTd > DIV >  DIV[onClick]").mousedown(function(event){       event.currentTarget.setAttribute("id","pager_active");     });     $(".pagerTd > DIV > DIV[onClick]").mouseup(function(event){       event.currentTarget.removeAttribute("id");     });     $(".pagerTd > DIV > DIV[onClick]").mouseleave(function(event){       event.currentTarget.removeAttribute("id");     });      $(".xbrl-mask > DIV > A").mousedown(function(event){       event.currentTarget.setAttribute("id","xbrl-button_active");     });     $(".xbrl-mask > DIV > A").mouseup(function(event){       event.currentTarget.removeAttribute("id");     });     $(".xbrl-mask > DIV > A").mouseleave(function(event){       event.currentTarget.removeAttribute("id");     });   }); // --> </script> <link rel="st
```

### ufocatch 說明頁（已知存在）
`https://ufocatch.com/about.aspx`

```html
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> <html xmlns="http://www.w3.org/1999/xhtml" > <head id="ctl00_Head1"> <script async src="//pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script> <script>     (adsbygoogle = window.adsbygoogle // []).push({         google_ad_client: "ca-pub-4898449747359627",         enable_page_level_ads: true     }); </script>   <!-- Global site tag (gtag.js) - Google Analytics --> <script async src="https://www.googletagmanager.com/gtag/js?id=G-XW2DDSJZ1G"></script> <script>     window.dataLayer = window.dataLayer // [];     function gtag() { dataLayer.push(arguments); }     gtag('js', new Date());      gtag('config', 'G-XW2DDSJZ1G'); </script>  <title> 	有価証券報告書、決算書、財務諸表の分析・ダウンロード - 有報キャッチャー </title><meta content="text/html; charset=utf-8" http-equiv="Content-Type" /><meta name="google-site-verification" content="Me5AYZ0nFZgkYjEfhSMHKiX-3RtBCC4Pu3oj79fryxo" /><meta name="description" content="EDINETやTDnetで公表された企業開示情報をご提供するサービスです。XBRLを活用し、会社属性情報などをデータ化しています。" />  <script src="//code.jquery.com/jquery-1.7.1.min.js" type="text/javascript"></script> <link rel="Stylesheet" href="css/master.css" /><link rel="Stylesheet" href="css/news.css" /><link rel="Stylesheet" href="
```

### EDINET 書類検索（猜測）
`https://disclosure2.edinet-fsa.go.jp/week0020.aspx`

```html
<!DOCTYPE html> <html lang="ja"> <head> <meta name="viewport" content="width=device-width,initial-scale=1"/> <meta name="description" content="開示情報利用者用トップ画面（英語）"/> <meta name="apple-mobile-web-app-capable" content="yes"/> <!--[if IE]><meta http-equiv="page-enter" content="blendTrans(Duration=0.1)"/><![endif]--> <meta name="fragment" content="!"/> <meta http-equiv="content-type" content="text/html; charset=UTF-8"/> <title>EDINET</title> <link rel="stylesheet" type="text/css" href="bootstrap/css/bootstrap.min.css?202682016474931"/> <link id="gxtheme_css_reference" rel="stylesheet" type="text/css" href="Resources/Japanese/ThemeBlue.css?202682016474931" /> <link rel="stylesheet" type="text/css" href="DVelop/Bootstrap/Shared/fontawesome_v5/css/fontawesome.min.css"/> <link rel="stylesheet" type="text/css" href="DVelop/Bootstrap/Shared/fontawesome_v5/css/all.min.css"/> <link rel="stylesheet" type="text/css" href="DVelop/Bootstrap/Shared/DVelopBootstrap.css"/> <script type="text/javascript" src="jquery.js?2136580" ></script><script type="text/javascript" src="bootstrap/js/bootstrap.min.js?202682016474931" ></script><script type="text/javascript" src="gxgral.js?2136580" ></script><script type="text/javascript" src="gxcfg.js?202682016464954" ></script><script type="text/javascript" src="Window/InNewWindowRender.js" ></script><script type="text/javascript" src="js/CommonJS.js?20260828182232" ></script><script type="text/javascript" src="js/Scrolltop.js?
```


## TDnet 解析診斷

- 回溯嘗試：20260903(0列)
- 測試頁：`https://www.release.tdnet.info/inbs/I_list_001_20260903.html`
- HTML 長度：53,981 字元
- `parse_list_page` 解析出的列數：**0**
- 其中命中目標代碼：**0**

實際出現的 class 值（前 40 個）：
```
evennew-L kjTime, evennew-M kjCode, evennew-M kjName, evennew-M kjPlace, evennew-M kjTitle, evennew-M kjXbrl, evennew-R kjHistroy, header-L, header-M, header-R, kaijiSum, oddnew-L kjTime, oddnew-M kjCode, oddnew-M kjName, oddnew-M kjPlace, oddnew-M kjTitle, oddnew-M kjXbrl, oddnew-R kjHistroy, pager-L, pager-M, pager-O, pager-R, pagerTd, style002, xbrl-button, xbrl-mask
```

其中以 `kj` 開頭者：**無 ← 這就是解析失敗的原因**

`<tr>` 標籤數：**109**

```html
<!DOCTYPE html>
<html>
<head>
<title>適時開示情報閲覧サービス - 開示情報一覧</title>
<meta content="text/html" charset="UTF-8" http-equiv="content-type">
<meta name="robots" content="noindex,nofollow">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Cache-Control" content="no-cache">
<meta http-equiv="Expires" content="0">
<script type="text/javascript" charset="UTF-8" src="./js/I_JAVASCRIPT.js"></script>
<script type="text/javascript" charset="UTF-8" src="./js/I_MENSEKI.js"></script>
<script type="text/javascript" charset="UTF-8" src="./runtime/jquery-1.8.3.min.js"></script>
<script type="text/javascript">
<!--
  $(document).ready(function(){
    $(".pagerTd > DIV >  DIV[onClick]").mousedown(function(event){
      event.currentTarget.setAttribute("id","pager_active");
    });
    $(".pagerTd > DIV > DIV[onClick]").mouseup(function(event){
      event.currentTarget.removeAttribute("id");
    });
    $(".pagerTd > DIV > DIV[onClick]").mouseleave(function(event){
      event.currentTarget.removeAttribute("id");
    });

    $(".xbrl-mask > DIV > A").mousedown(function(event){
      event.currentTarget.setAttribute("id","xbrl-button_active");
    });
    $(".xbrl-mask > DIV > A").mouseup(function(event){
      event.currentTarget.removeAttribute("id");
    });
    $(".xbrl-mask > DIV > A").mouseleave(function(event){
      event.currentTarget.removeAttribute("id");
    });
  });
// -->
</script>
<link rel="stylesheet" href="./css/I_STYLE.css" m
```

→ ⚠️ **解析出 0 列＝解析器與實際 HTML 不符**（不是「沒開示」）。比對上方 HTML 與 `parse_list_page` 的 td class 假設。
