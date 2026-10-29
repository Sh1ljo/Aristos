# PyTrading - Strategy Backtesting Bot

A simple trading bot with a web UI: free daily price data -> features -> registered
strategies -> backtest vs buy-and-hold -> minimal black animated dashboard.

Benchmarks: `buy_hold`, `ema_cross`, `rsi_reversion`. New strategies must beat them.

Read `plan.md` for the full project plan and honest expectations.

## Rules for all agents working in this repo

- Keep it simple. No frameworks beyond what exists, no speculative abstractions.
- Readable code over clever code. Short functions, clear names.
- Comments are ONE-LINERS ONLY, `#` style, and only where the code is not self-explanatory:
  `# act on the next bar, no look-ahead`
  No docstrings, no block comments, no narration of obvious code.
- Never introduce look-ahead bias. See `docs/DOMAIN.md` before touching features or backtest.
- All results must be shown next to buy-and-hold.
- No real trading. Educational project only.

## Layout

```
plan.md            # project plan (source of truth for scope)
requirements.txt   # fastapi, uvicorn, yfinance, pandas, numpy
data/              # cached CSVs, one per ticker, e.g. data/SPY.csv
bot/
  data.py          # download + cache OHLCV
  features.py      # feature columns + next-day target
  registry.py      # strategy registry: register() / get()
  strategies/
    buy_hold.py    # always long, the benchmark
    ema_cross.py   # golden cross: long when fast EMA > slow EMA
    rsi_reversion.py # long on oversold RSI, exit on overbought
  backtest.py      # generic backtest of any registered strategy, run_backtest() entry point
  optimizer.py     # grid search over user-chosen param combos, POST /api/optimize
  server.py        # FastAPI app, serves /api/* and static/
static/
  index.html       # the dashboard (chart, metrics cards, signal panel)
docs/
  ARCHITECTURE.md  # module contracts and API endpoints
  CODING.md        # style and verification rules
  DOMAIN.md        # trading/backtesting concepts and pitfalls
```

## Run

```
pip install -r requirements.txt
uvicorn bot.server:app --reload
open http://localhost:8000
```

Quick check without UI:

```
python -m bot.backtest SPY
```

## Docs for agents

- Start at `docs/ARCHITECTURE.md` for what talks to what.
- `docs/CODING.md` before writing or reviewing code.
- `docs/DOMAIN.md` for the finance concepts and the classic bugs to avoid.
