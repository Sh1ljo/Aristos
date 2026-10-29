import pandas as pd

from ..registry import register


def buy_hold_run(df: pd.DataFrame, params: dict) -> dict:
    # always long, every bar, no timing
    positions = pd.Series(1.0, index=df.index)
    return {"positions": positions, "extra_metrics": {}}


def buy_hold_detail(df: pd.DataFrame, params: dict) -> str:
    return "always long, the benchmark"


register(
    name="buy_hold",
    description="buy on day one and hold, the benchmark",
    params=[],
    run=buy_hold_run,
    detail=buy_hold_detail,
)
