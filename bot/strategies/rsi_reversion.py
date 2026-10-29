import pandas as pd

from ..registry import register


def _calc_rsi(series: pd.Series, window: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def rsi_reversion_run(df: pd.DataFrame, params: dict) -> dict:
    window = int(params["window"])
    oversold = float(params["oversold"])
    overbought = float(params["overbought"])
    rsi = _calc_rsi(df["close"], window)

    raw_signal = pd.Series(index=df.index, dtype=float)
    raw_signal[rsi < oversold] = 1.0
    raw_signal[rsi > overbought] = 0.0
    # hold state until opposing threshold is triggered
    positions = raw_signal.ffill().fillna(0.0)
    positions[rsi.isna()] = float("nan")
    return {"positions": positions, "extra_metrics": {}}


def rsi_reversion_detail(df: pd.DataFrame, params: dict) -> str:
    window = int(params["window"])
    rsi = _calc_rsi(df["close"], window).iloc[-1]
    if pd.isna(rsi):
        return None
    return f"RSI({window}): {rsi:.1f}"


register(
    name="rsi_reversion",
    description="long on oversold RSI, exit on overbought",
    params=[
        {"name": "window", "label": "rsi window", "min": 5, "max": 30, "step": 1, "default": 14},
        {"name": "oversold", "label": "oversold entry", "min": 15, "max": 45, "step": 1, "default": 30},
        {"name": "overbought", "label": "overbought exit", "min": 55, "max": 85, "step": 1, "default": 70},
    ],
    run=rsi_reversion_run,
    detail=rsi_reversion_detail,
)
