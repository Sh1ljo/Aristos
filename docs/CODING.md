# Coding rules

## Style

- Comments are ONE-LINERS ONLY, `#` style, only for non-obvious decisions:
  `# scaler fitted on the training window only, avoids look-ahead`
- No docstrings, no block comments, no TODOs, no section banners.
- Plain readable Python. Small functions, no clever one-liners.
- Type hints on public functions.
- No extra dependencies beyond requirements.txt without a stated reason.
- Every agent edits only the files its task names. Do not refactor other files.

## Anti-patterns

- No classes where a function is enough.
- No config files or abstractions for values used once.
- No silent exception swallowing. If something fails, let it fail loudly.
- No dead code, no commented-out code.

## Verification before you claim done

1. `python -m bot.backtest SPY` prints metrics for strategy AND buy-and-hold.
2. The same run works for a second ticker from AVAILABLE_TICKERS.
3. `python -m bot.server` (or uvicorn) starts, `/api/run?ticker=SPY` returns
   valid JSON with non-empty arrays, `/api/signal?ticker=SPY` returns a signal.
4. Shift test: changing the LAST close price must not change any feature for
   earlier days (guards against look-ahead in features).
5. Cached CSV in `data/` is reused on the second run (fast, no re-download).
