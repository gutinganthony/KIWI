"""Historical crisis definitions for AVI backtesting.

Five major S&P 500 drawdown episodes used to evaluate the AVI's ability
to provide early warning before market peaks.
"""

CRISES = [
    {
        "name": "Asian/LTCM 1997-98",
        "peak": "1998-07-17",
        "trough": "1998-10-08",
        "drawdown": -0.19,
    },
    {
        "name": "Dot-com 2000",
        "peak": "2000-03-24",
        "trough": "2002-10-09",
        "drawdown": -0.49,
    },
    {
        "name": "GFC 2007-09",
        "peak": "2007-10-09",
        "trough": "2009-03-09",
        "drawdown": -0.57,
    },
    {
        "name": "COVID 2020",
        "peak": "2020-02-19",
        "trough": "2020-03-23",
        "drawdown": -0.34,
    },
    {
        "name": "Rate Hike 2022",
        "peak": "2022-01-03",
        "trough": "2022-10-12",
        "drawdown": -0.25,
    },
]
