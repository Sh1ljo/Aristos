# Architecture

Pipeline:

```
yfinance -> bot/data.py -> bot/features.py -> bot/model.py -> bot/backtest.py -> bot/server.py -> static/index.html
```

## Module contracts

These signatures are the contract between modules. Change them only if you update
every caller and this document.

### bot/data.py

- `load_ohlcv(ticker: str, years: int = 10) -> pd.DataFrame`
  Downloads daily OHLCV with yfinance, caches to `data/{TICKER}.csv`, returns the
  cached file on later runs. Index is a DatetimeIndex named `date`. Columns:
  `open, high, low, close, volume`. Adjusted close goes into `close`. No NaNs.
- `AVAILABLE_TICKERS: list[str]` - tickers offered in the UI (SPY, AAPL, MSFT,
  GLD, QQQ - keep the list small, they are just free liquid defaults).

### bot/features.py

- `build_features(df: pd.DataFrame) -> pd.DataFrame`
  Adds feature columns and `target`. `target = close.shift(-1) / close - 1`.
  Also adds `ret = close / close.shift(1) - 1` used by the backtest.
  No feature may use data from day t+1 or later.
- `FEATURE_COLS: list[str]` - names of the feature columns.

Features (from plan.md): returns over last 1/2/5/10 days, 10-day rolling vol,
RSI(14) scaled 0-1, close/SMA20 - 1, volume vs 20-day average volume.

### bot/model.py

- `walk_forward(df: pd.DataFrame, feature_cols, train_days=500, step=20, alpha=1.0) -> pd.Series`
  Rolling-window predictions, one per day, each made by a model trained only on
  the previous `train_days` days. Scaler fitted on the training window only.
- `predict_next(df: pd.DataFrame) -> float`
  Trains on all available data and predicts tomorrow's return.

### Strategy registry (bot/registry.py, bot/strategies/)

The backtester, server and UI are strategy-agnostic. A strategy is a plain
function plus metadata, registered at import time:

- `bot/registry.py`
  - `STRATEGIES: dict[str, dict]` - name -> strategy definition
  - `register(name, description, params, run, detail=None) -> None`
  - `get(name: str) -> dict` - raises a clean error for unknown names
- `bot/strategies/__init__.py` imports every strategy module so they register
  themselves. Add a new strategy = add one file + one import line.

A strategy definition:

- `name: str` - unique id used in URLs (e.g. "linreg")
- `description: str` - one line shown in the UI
- `params: list[dict]` - declared so the UI can render controls without knowing
  the strategy. Each param: `{"name", "label", "min", "max", "step", "default"}`
  (all numbers; the UI renders a slider per param).
- `run(df: pd.DataFrame, params: dict) -> dict`
  `df` is the full featured frame from `build_features` (OHLCV columns included).
  Returns `{"positions": pd.Series, "extra_metrics": dict}`.
  `positions` is the target position per day (0 = flat, 1 = long) using only
  data up to that day. Warm-up days may be NaN (treated as flat).
  `extra_metrics` may be empty; the backtester merges it into `metrics`.
- `detail(df: pd.DataFrame, params: dict) -> str` (optional)
  One short line for the signal panel (e.g. "pred +0.13%"), or None.

Current strategies:
- `linreg` (strategies/linreg.py) - Ridge walk-forward; params: threshold,
  alpha, train_days, step. Extra metric: directional_accuracy.
- `sma_trend` (strategies/sma_trend.py) - long when close > SMA(n);
  param: window. The minimal example to copy for new strategies.

### bot/backtest.py

- `run_backtest(strategy: str, ticker: str, params: dict, cost=0.0005, years=10) -> dict`
  Generic pipeline for any registered strategy. Returns the JSON payload for
  `/api/run`:

```
{
  "strategy": "linreg",
  "ticker": "SPY",
  "dates": [...],        # ISO date strings
  "price": [...],        # close prices
  "equity": [...],       # strategy equity curve (starts at 1.0)
  "buy_hold": [...],     # buy-and-hold equity curve (starts at 1.0)
  "trades": [{"date": "...", "side": "buy"|"sell", "price": 0.0}, ...],
  "metrics": {
    "total_return": 0.0, "cagr": 0.0, "sharpe": 0.0, "max_drawdown": 0.0,
    "win_rate": 0.0, "trades": 0, "time_in_market": 0.0,
    "bh_total_return": 0.0, "bh_cagr": 0.0, "bh_sharpe": 0.0, "bh_max_drawdown": 0.0
    # plus whatever extra_metrics the strategy returned
  }
}
```

- `signal_today(strategy: str, ticker: str, params: dict) -> dict`
  -> `{"strategy": ..., "ticker": ..., "date": ..., "signal": "LONG" | "FLAT",
  "position": 0.0 | 1.0, "detail": "pred +0.13%" | null}`
- `main()` so `python -m bot.backtest SPY linreg` prints strategy vs buy-and-hold.

Backtest rules: the strategy's position signal is applied from the NEXT bar
(`positions.shift(1)`), trades pay `cost` per side, long-or-flat only.

### bot/server.py

- `GET /api/tickers` -> `{"tickers": [...]}`
- `GET /api/strategies` -> `{"strategies": [{"name", "description", "params": [...]}, ...]}`
  (params exactly as declared in the registry)
- `GET /api/run?strategy=linreg&ticker=SPY&cost=0.0005&years=10&threshold=0.0005&alpha=1.0`
  -> run_backtest payload. Undeclared query params are ignored; declared
  params missing from the query fall back to their defaults. Unknown strategy
  or ticker -> 400/500 JSON error, no hang.
- `GET /api/signal?strategy=linreg&ticker=SPY&threshold=...` -> signal_today payload
- `GET /` serves `static/index.html`.

## UI

`static/index.html` is one self-contained file (inline CSS/JS, chart via
lightweight-charts CDN). Per plan.md section 4: pure black background, minimal
panels, count-up metrics, equity line that draws itself, pulsing signal dot.
The header has a ticker selector, a strategy selector, and one slider per
strategy param (rendered from `/api/strategies`), so new strategies appear in
the UI without any UI change.
