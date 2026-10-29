import pandas as pd

from ..registry import register


def ema_cross_run(df: pd.DataFrame, params: dict) -> dict:
    fast = int(params["fast"])
    slow = int(params["slow"])
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    positions = (ema_fast > ema_slow).astype(float)
    # warm up period until slow EMA has enough data
    positions.iloc[:slow] = float("nan")
    return {"positions": positions, "extra_metrics": {}}


def ema_cross_detail(df: pd.DataFrame, params: dict) -> str:
    fast = int(params["fast"])
    slow = int(params["slow"])
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean().iloc[-1]
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean().iloc[-1]
    spread = (ema_fast / ema_slow - 1) if ema_slow else 0.0
    return f"EMA{fast}/EMA{slow} spread: {spread:+.2%}"


register(
    name="ema_cross",
    description="golden cross: long when fast EMA is above slow EMA",
    params=[
        {"name": "fast", "label": "fast ema", "min": 5, "max": 50, "step": 1, "default": 12},
        {"name": "slow", "label": "slow ema", "min": 20, "max": 200, "step": 5, "default": 50},
    ],
    run=ema_cross_run,
    detail=ema_cross_detail,
)
