import pandas as pd

FEATURE_COLS = [
    "ret_1",
    "ret_2",
    "ret_5",
    "ret_10",
    "vol_10",
    "rsi_14",
    "sma20_dist",
    "vol_chg_20",
]


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss
    return 1 - 1 / (1 + rs)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ret"] = out["close"] / out["close"].shift(1) - 1
    out["ret_1"] = out["ret"]
    out["ret_2"] = out["close"] / out["close"].shift(2) - 1
    out["ret_5"] = out["close"] / out["close"].shift(5) - 1
    out["ret_10"] = out["close"] / out["close"].shift(10) - 1
    out["vol_10"] = out["ret"].rolling(10).std()
    out["rsi_14"] = _rsi(out["close"], 14)
    out["sma20_dist"] = out["close"] / out["close"].rolling(20).mean() - 1
    out["vol_chg_20"] = out["volume"] / out["volume"].rolling(20).mean() - 1
    out["target"] = out["close"].shift(-1) / out["close"] - 1
    return out
