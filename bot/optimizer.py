from .backtest import DEFAULT_COST, run_on_df
from .data import load_ohlcv
from .features import build_features
from .registry import defaults, get
from . import strategies  # noqa: F401 - import registers all strategies

MAX_COMBOS_PER_REQUEST = 100


def _validate_combo(strategy: str, combo: dict) -> dict:
    declared = {p["name"]: p for p in get(strategy)["params"]}
    params = defaults(strategy)
    for name, value in (combo or {}).items():
        if name not in declared:
            raise ValueError(f"unknown param '{name}' for strategy '{strategy}'")
        p = declared[name]
        v = float(value)
        if v < p["min"] - 1e-9 or v > p["max"] + 1e-9:
            raise ValueError(f"param '{name}' value {v} outside [{p['min']}, {p['max']}]")
        params[name] = v
    return params


def run_optimizer_batch(strategy: str, ticker: str, combos: list, cost: float = DEFAULT_COST, years: int = 10) -> dict:
    ticker = ticker.upper()
    if not isinstance(combos, list) or not combos:
        raise ValueError("combos must be a non-empty list")
    if len(combos) > MAX_COMBOS_PER_REQUEST:
        raise ValueError(f"too many combos in one request: {len(combos)} (max {MAX_COMBOS_PER_REQUEST})")
    df = build_features(load_ohlcv(ticker, years=years))
    results = []
    for combo in combos:
        params = _validate_combo(strategy, combo)
        payload = run_on_df(df, strategy, ticker=ticker, params=params, cost=cost)
        results.append({"params": params, "metrics": payload["metrics"]})
    return {"strategy": strategy, "ticker": ticker, "count": len(results), "results": results}
