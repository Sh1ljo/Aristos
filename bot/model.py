import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from .features import FEATURE_COLS


def walk_forward(
    df: pd.DataFrame,
    feature_cols: list[str],
    train_days: int = 500,
    step: int = 20,
    alpha: float = 1.0,
) -> pd.Series:
    preds = pd.Series(index=df.index, dtype=float)
    # range ends at len(df) so the final day always gets a prediction
    for start in range(train_days, len(df), step):
        train = df.iloc[start - train_days:start].dropna()
        test = df.iloc[start:start + step]
        scaler = StandardScaler().fit(train[feature_cols])
        model = Ridge(alpha=alpha).fit(scaler.transform(train[feature_cols]), train["target"])
        preds.iloc[start:start + step] = model.predict(scaler.transform(test[feature_cols]))
    return preds


def predict_next(df: pd.DataFrame) -> float:
    # dropna keeps the last row out: it has no target (tomorrow is unknown)
    train = df.dropna(subset=FEATURE_COLS + ["target"])
    scaler = StandardScaler().fit(train[FEATURE_COLS])
    model = Ridge(alpha=1.0).fit(scaler.transform(train[FEATURE_COLS]), train["target"])
    last = df.iloc[[-1]]
    return float(model.predict(scaler.transform(last[FEATURE_COLS]))[0])
