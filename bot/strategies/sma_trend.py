import pandas as pd

from ..registry import register


def sma_trend_run(df: pd.DataFrame, params: dict) -> dict:
    window = int(params["window"])
    # positions before the first full SMA window are NaN, treated as flat by the backtester
    sma = df["close"].rolling(window).mean()
    positions = (df["close"] > sma).astype(float)
    positions[sma.isna()] = float("nan")
    return {"positions": positions, "extra_metrics": {}}


def sma_trend_detail(df: pd.DataFrame, params: dict) -> str:
    window = int(params["window"])
    sma = df["close"].rolling(window).mean().iloc[-1]
    if pd.isna(sma):
        return None
    gap = df["close"].iloc[-1] / sma - 1
    return f"close vs SMA{window}: {gap:+.2%}"


register(
    name="sma_trend",
    description="long while close above its simple moving average",
    params=[
        {"name": "window", "label": "sma window", "min": 20, "max": 250, "step": 5, "default": 200},
    ],
    run=sma_trend_run,
    detail=sma_trend_detail,
)
