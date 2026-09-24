"""小工具：穩健迴歸與評分。只用 numpy。"""
import numpy as np


def huber_ols(X, y, c=1.345, iters=30):
    """Huber IRLS。X 已含常數欄。回傳係數。

    財報資料有一次性減損、稅務調整等極端值，普通 OLS 會被一兩季的怪數字拖走。
    """
    ok = np.all(np.isfinite(X), axis=1) & np.isfinite(y)
    X, y = X[ok], y[ok]
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    for _ in range(iters):
        r = y - X @ beta
        s = 1.4826 * np.median(np.abs(r - np.median(r))) + 1e-12
        w = np.minimum(1.0, c * s / np.maximum(np.abs(r), 1e-12))
        sw = np.sqrt(w)
        nb = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)[0]
        if np.max(np.abs(nb - beta)) < 1e-8:
            beta = nb
            break
        beta = nb
    return beta


def winsor(x, lo=0.01, hi=0.99):
    x = np.asarray(x, float)
    ok = np.isfinite(x)
    if ok.sum() < 10:
        return x
    a, b = np.quantile(x[ok], [lo, hi])
    return np.clip(x, a, b)


def spearman(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3:
        return np.nan
    ra = np.argsort(np.argsort(a[ok]))
    rb = np.argsort(np.argsort(b[ok]))
    return float(np.corrcoef(ra, rb)[0, 1])
