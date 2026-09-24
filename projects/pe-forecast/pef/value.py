"""模組 V：基本面價值（最小 DCF）。

只用第一性原理的量：營收路徑、淨利率路徑、再投資效率（S/C）、折現率。
全部向量化，一次算 N 個（公司 × 時點）。

    營收：前 3 年用模組 E 的預測，之後成長率以半衰期 H 年衰退到 g_inf
    淨利率：前 3 年用模組 E 的預測，之後以半衰期 HM 年收斂到結構淨利率 m_bar
    FCF_j = 營收_j × 淨利率_j − (營收_j − 營收_{j−1}) / SC
    r     = 10 年期殖利率 + theta0 + theta1 × sigma
    V_s   = 站在第 s 年看的價值 = Σ_{j=s+1}^{s+10} FCF_j/(1+r)^(j−s) + 終值
"""
import numpy as np

YEARS = 15          # 路徑長度（第 3 年起算還要 10 年 + 終值）
HM = 1.5            # 淨利率收斂半衰期（年），固定——不是要校準的參數
SPREAD_MIN = 0.02   # r − g_inf 下限，避免終值爆掉
G_CLIP = (-0.40, 0.80)


def build_path(R0, rev3, m3, m_bar, H, g_inf):
    """回傳 (R, E)：形狀 (N, YEARS+1)，第 0 欄是錨點（今天的 TTM）。

    rev3, m3：形狀 (N, 3)，模組 E 對第 1–3 年 TTM 營收、淨利率的預測。
    """
    N = len(R0)
    R = np.empty((N, YEARS + 1))
    m = np.empty((N, YEARS + 1))
    R[:, 0] = R0
    R[:, 1:4] = rev3
    m[:, 0] = np.nan
    m[:, 1:4] = m3
    g3 = np.clip(np.log(rev3[:, 2] / rev3[:, 1]), *G_CLIP)
    for j in range(4, YEARS + 1):
        g = g_inf + (g3 - g_inf) * 0.5 ** ((j - 3) / H)
        R[:, j] = R[:, j - 1] * np.exp(g)
        m[:, j] = m_bar + (m3[:, 2] - m_bar) * 0.5 ** ((j - 3) / HM)
    E = R * m
    return R, E


def value_at(R, E, sc, r, g_inf, s):
    """站在第 s 年（整數 0..3）的權益價值。R、E 來自 build_path。"""
    s = int(s)
    reinv = np.diff(R, axis=1) / sc[:, None]           # 第 j 年的再投資，j=1..YEARS
    fcf = E[:, 1:] - reinv                              # 索引 j-1 ↔ 第 j 年
    V = np.zeros(len(R))
    for j in range(s + 1, s + 11):
        V += fcf[:, j - 1] / (1 + r) ** (j - s)
    # 終值：第 s+10 年的盈餘以 g_inf 永續，再投資率 g_inf/SC × 營收
    j_t = s + 10
    fcf_t = E[:, j_t] * (1 + g_inf) - R[:, j_t] * (1 + g_inf) * (g_inf / (1 + g_inf)) / sc
    tv = fcf_t / np.maximum(r - g_inf, SPREAD_MIN)
    V += tv / (1 + r) ** 10
    return V


def discount_rate(y10, sigma, theta0, theta1):
    return y10 + theta0 + theta1 * sigma


def intrinsic(R0, rev3, m3, m_bar, sc, y10, sigma, params, s=0.0, floor=True):
    """總價值（與營收同單位）。s 可以是 0、0.5、1、2、3（年）；非整數用幾何內插。

    params: dict(theta0, theta1, H, g_inf)
    回傳 (V, floored)：floored 標記 V≤0 被墊底的觀測值。
    """
    R, E = build_path(R0, rev3, m3, m_bar, params["H"], params["g_inf"])
    r = discount_rate(y10, sigma, params["theta0"], params["theta1"])
    lo, hi = int(np.floor(s)), int(np.ceil(s))
    V_lo = value_at(R, E, sc, r, params["g_inf"], lo)
    if hi == lo:
        V = V_lo
    else:
        V_hi = value_at(R, E, sc, r, params["g_inf"], hi)
        w = s - lo
        V = np.where((V_lo > 0) & (V_hi > 0),
                     np.exp((1 - w) * np.log(np.maximum(V_lo, 1e-9)) + w * np.log(np.maximum(V_hi, 1e-9))),
                     (1 - w) * V_lo + w * V_hi)
    if not floor:                       # 反推隱含利潤率要用未墊底的線性值
        return V, np.zeros(len(V), bool)
    # 墊底：價值不可能 ≤ 0（有限責任），也避免 log 爆掉。墊在「當年營收 × 2%」
    R_s = R[:, lo] if hi == lo else np.exp((1 - (s - lo)) * np.log(R[:, lo]) + (s - lo) * np.log(R[:, hi]))
    floor = 0.02 * R_s
    floored = V < floor
    return np.maximum(V, floor), floored
