import numpy as np
import pandas as pd

from ..features import FEATURE_COLS
from ..model import predict_next, walk_forward
from ..registry import register


def linreg_run(df: pd.DataFrame, params: dict) -> dict:
    preds = walk_forward(
        df, FEATURE_COLS, train_days=int(params["train_days"]), step=int(params["step"]), alpha=params["alpha"]
    )
    positions = (preds > params["threshold"]).astype(float)
    has_target = df["target"].notna()
    # sign comparison only where both prediction and actual next-day return exist
    both = preds.notna() & has_target
    directional = float((np.sign(preds[both]) == np.sign(df["target"][both])).mean()) if both.any() else 0.0
    return {"positions": positions, "extra_metrics": {"directional_accuracy": directional}}


def linreg_detail(df: pd.DataFrame, params: dict) -> str:
    pred = predict_next(df)
    return f"pred {pred:+.2%}"


register(
    name="linreg",
    description="ridge regression on returns, walk-forward",
    params=[
        {"name": "threshold", "label": "threshold", "min": 0.0, "max": 0.005, "step": 0.0001, "default": 0.0005},
        {"name": "alpha", "label": "ridge alpha", "min": 0.1, "max": 10.0, "step": 0.1, "default": 1.0},
        {"name": "train_days", "label": "train days", "min": 100, "max": 1000, "step": 50, "default": 500},
        {"name": "step", "label": "step days", "min": 5, "max": 60, "step": 5, "default": 20},
    ],
    run=linreg_run,
    detail=linreg_detail,
)
