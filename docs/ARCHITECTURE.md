# Architecture

Pipeline:

```
yfinance -> bot/data.py -> bot/features.py -> bot/backtest.py -> bot/server.py -> static/index.html
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

- `name: str` - unique id used in URLs (e.g. "ema_cross")
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

Current strategies (benchmarks; new strategies must beat these):
- `buy_hold` (strategies/buy_hold.py) - buy on day one and hold; no params.
  The baseline every other strategy is compared against.
- `ema_cross` (strategies/ema_cross.py) - golden cross: long when fast EMA > slow EMA;
  params: fast, slow.
- `rsi_reversion` (strategies/rsi_reversion.py) - long on oversold RSI, exit on overbought;
  params: window, oversold, overbought.

### bot/backtest.py

- `run_backtest(strategy: str, ticker: str, params: dict, cost=0.0005, years=10) -> dict`
  Generic pipeline for any registered strategy: loads + features the data, then
  delegates to `run_on_df`. Returns the JSON payload for `/api/run`:

```
{
  "strategy": "ema_cross",
  "ticker": "SPY",
  "dates": [...],        # ISO date strings
  "price": [...],        # close prices
  "equity": [...],       # strategy equity curve (starts at 1.0)
  "buy_hold": [...],     # buy-and-hold equity curve (starts at 1.0)
  "trades": [{"date": "...", "side": "buy"|"sell", "price": 0.0}, ...],
  "trade_log": [{"entry_date": "...", "exit_date": "...", "entry_price": 0.0, "exit_price": 0.0, "return_pct": 0.0, "days": 0}],
  "metrics": {
    "total_return": 0.0, "cagr": 0.0, "sharpe": 0.0, "max_drawdown": 0.0,
    "win_rate": 0.0, "trades": 0, "time_in_market": 0.0,
    "bh_total_return": 0.0, "bh_cagr": 0.0, "bh_sharpe": 0.0, "bh_max_drawdown": 0.0
    # plus whatever extra_metrics the strategy returned
  }
}
```

- `run_on_df(df: pd.DataFrame, strategy: str, ticker: str = "", params: dict | None = None, cost=0.0005) -> dict`
  Same payload as `run_backtest`, but on an already-featured frame. Used by the
  optimizer so one loaded dataframe serves many param combos.
- `signal_today(strategy: str, ticker: str, params: dict) -> dict`
  -> `{"strategy": ..., "ticker": ..., "date": ..., "signal": "LONG" | "FLAT",
  "position": 0.0 | 1.0, "detail": "pred +0.13%" | null}`
- `main()` so `python -m bot.backtest SPY ema_cross` prints strategy vs buy-and-hold.

### bot/optimizer.py

- `MAX_COMBOS_PER_REQUEST = 100`
- `run_optimizer_batch(strategy: str, ticker: str, combos: list[dict], cost=0.0005, years=10) -> dict`
  Runs each explicit param combo through `run_on_df` on one loaded dataframe.
  Every combo is validated against the declared params: unknown name or value
  outside `[min, max]` raises `ValueError`; more than `MAX_COMBOS_PER_REQUEST`
  combos in one call raises `ValueError`. Returns:

```
{
  "strategy": "ema_cross", "ticker": "SPY", "count": 3,
  "results": [{"params": {"threshold": 0.0, ...}, "metrics": {...}}, ...]
}
```

Backtest rules: the strategy's position signal is applied from the NEXT bar
(`positions.shift(1)`), trades pay `cost` per side, long-or-flat only.

### bot/server.py

- `GET /api/tickers` -> `{"tickers": [...]}`
- `GET /api/strategies` -> `{"strategies": [{"name", "description", "params": [...]}, ...]}`
  (params exactly as declared in the registry)
- `GET /api/run?strategy=ema_cross&ticker=SPY&cost=0.0005&years=10&threshold=0.0005&alpha=1.0`
  -> run_backtest payload. Undeclared query params are ignored; declared
  params missing from the query fall back to their defaults. Unknown strategy
  or ticker -> 400/500 JSON error, no hang.
- `GET /api/signal?strategy=ema_cross&ticker=SPY&threshold=...` -> signal_today payload
- `POST /api/optimize` with JSON body
  `{"strategy": "ema_cross", "ticker": "SPY", "cost": 0.0005, "years": 10,
  "combos": [{"threshold": 0.0, "alpha": 1.0, ...}, ...]}`
  -> `run_optimizer_batch` payload. The UI sends the grid in batches of <= 100
  combos (client-side total cap 2000) and renders results as they arrive. Invalid JSON, unknown strategy,
  unknown param, out-of-range value or oversized batch -> 400, no hang.
- `GET /` serves `static/index.html`.

## UI

`static/index.html` is one self-contained file (inline CSS/JS, chart via
lightweight-charts CDN). Pure black background, ambient mouse-reactive canvas,
live signal panel, strategy parameters, synchronized charts, metrics cards,
trade log inspector, strategy template guide, and an Optimize tab.

UI run model: nothing auto-runs. Changing any control (sliders, strategy,
ticker, timeframe, cost) only marks the run as pending (dot on the Run button,
stale chip on the chart, dimmed signal panel); Run or Ctrl+Enter applies the
changes. The Optimize tab lets the user pick per-param from/to/step ranges,
shows the live combo count (capped), runs combos in batches with progress,
and ranks results by a chosen metric; Apply loads a row into the sliders and
marks pending without running.
