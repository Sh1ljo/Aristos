# PyTrading - Linear Regression Trading Bot

A simple trading bot with a web UI: free daily price data -> features -> Ridge regression
(walk-forward) -> backtest vs buy-and-hold -> minimal black animated dashboard.

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
requirements.txt   # fastapi, uvicorn, yfinance, pandas, numpy, scikit-learn
data/              # cached CSVs, one per ticker, e.g. data/SPY.csv
bot/
  data.py          # download + cache OHLCV
  features.py      # feature columns + next-day target
  model.py         # Ridge walk-forward predictions
  registry.py      # strategy registry: register() / get()
  strategies/
    linreg.py      # Ridge walk-forward strategy (the original bot)
    sma_trend.py   # simple SMA trend strategy, minimal template
  backtest.py      # generic backtest of any registered strategy, run_backtest() entry point
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
