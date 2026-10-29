# Domain notes

Reference for the trading concepts used here. Read before touching
`bot/features.py` or `bot/backtest.py`.

## Prices vs returns

- Price trends upward and is non-stationary. Regressing on price gives R^2
  near 0.99 and predicts nothing. The model always works on RETURNS.
- `ret[t] = close[t] / close[t-1] - 1` is the daily return.
- Target: `target[t] = close[t+1] / close[t] - 1` (next-day return).

## Look-ahead bias

The number one backtest bug. Rules:

- Every feature for day t uses only data up to day t.
- The signal decided on day t is applied to day t+1's return
  (`position = signal.shift(1)`).
- The scaler and the model are fitted only on the training window.
- Shift test: modify tomorrow's price; nothing about today's features or
  today's signal may change.

## Walk-forward training

Never randomly split time series. Train on the previous 500 trading days,
predict the next 20, slide forward by 20, retrain. Every backtest prediction
comes from a model that never saw that day.

## Strategy

- Ridge regression (regularized linear) on standardized features.
- Signal: predicted next-day return > threshold -> LONG tomorrow, else FLAT.
- Long-or-flat only: no shorting, no leverage.
- Cost: 0.05% per trade side, both entering and exiting.

## Metrics

- Total return: final equity - 1.
- CAGR: `equity[-1] ** (252 / n_days) - 1`.
- Sharpe: `mean(daily ret) / std(daily ret) * sqrt(252)` (annualized).
- Max drawdown: worst peak-to-trough decline of the equity curve.
- Win rate: share of in-market days with positive return.
- Directional accuracy: share of days where sign(prediction) == sign(target).
- Time in market: share of days with a position.
- Every strategy number is shown next to the same buy-and-hold number.

## Honest expectations

A linear model on daily bars has a very small edge, if any. Matching
buy-and-hold with lower drawdown is a good result. Underperforming is a valid
finding. The framework is the value. No real money without beating
buy-and-hold out-of-sample in paper trading over months.
