\# Linear Regression Trading Bot: Project Plan



A simple, honest starter project: a Python bot that uses linear regression to predict next-day stock returns, backtests the idea properly, and shows everything in a minimal, black, animated web UI.



\---



\## 1. Goals and honest expectations



\*\*Goal:\*\* a working end-to-end pipeline (data -> features -> model -> signal -> backtest -> UI) that you can later extend with better models, more tickers and live paper trading.



\*\*Honest expectations:\*\*



\- A linear model on daily price data has a \*very\* small edge, if any. Directional accuracy of 50-52% is typical, and trading costs can wipe that out.

\- The main value is the \*\*framework and the learning\*\*. If the strategy doesn't beat buy-and-hold after costs, that is a valid and useful result, not a failure.

\- \*\*No real money\*\* until the strategy beats buy-and-hold out-of-sample, over a long period, in paper trading.



\*\*The classic trap to avoid:\*\* regressing on \*price\*. Price trends upward and is non-stationary, so a regression fits beautifully (R² around 0.99) and predicts nothing. We regress on \*\*returns\*\*.



\---



\## 2. The starter strategy



| Item | Choice |

|---|---|

| Asset | \*\*SPY\*\* (S\&P 500 ETF): liquid, low cost, honest baseline. Later: AAPL, MSFT, etc. |

| Timeframe | Daily bars, about 10 years of history |

| Target (`y`) | Next-day return: `close\[t+1] / close\[t] - 1` |

| Model | `Ridge` regression (linear regression with a little regularization) |

| Position | Long or flat (no shorting, no leverage) |

| Rule | If predicted next-day return > threshold, hold SPY tomorrow; otherwise stay in cash |

| Threshold | Start at `0.0005` (0.05%), tunable in the UI |

| Costs | 0.05% per trade side (slippage + fees) |

| Benchmarks | Buy-and-hold, and optionally a 200-day moving average trend filter |



\### Features (all computed using only data up to day `t`)



1\. Returns over the last 1, 2, 5 and 10 days

2\. 10-day rolling volatility (std of daily returns)

3\. RSI(14), scaled to 0-1

4\. Distance from the 20-day moving average: `close / SMA20 - 1`

5\. Volume change versus the 20-day average volume



Standardize features (`StandardScaler`), fitted \*\*only on the training window\*\*.



\### Training scheme: walk-forward



Never use a random train/test split on time series. Use a rolling window:



1\. Train on the previous \*\*500 trading days\*\* (about 2 years).

2\. Predict the next \*\*20 days\*\*.

3\. Slide the window forward by 20 days, retrain, repeat.



Every prediction in the backtest is therefore made by a model that has never seen that day.



\---



\## 3. Pipeline



```

yfinance -> data.py -> features.py -> model.py (walk-forward) -> backtest.py -> server.py (FastAPI) -> index.html (UI)

```



\### 3.1 Data (`data.py`)

\- Download OHLCV with `yfinance`, cache to `data/SPY.csv` so repeated runs are instant.

\- Drop NaNs, use adjusted close.



\### 3.2 Features (`features.py`)

\- Build the feature columns above.

\- Create the target with `shift(-1)`. The last row has no target and is used only for today's live prediction.

\- \*\*Rule: no feature may use information from day `t+1` or later\*\* (look-ahead bias is the #1 backtest bug).



\### 3.3 Model (`model.py`)

```python

from sklearn.linear\_model import Ridge

from sklearn.preprocessing import StandardScaler



def walk\_forward(df, feature\_cols, train\_days=500, step=20, alpha=1.0):

&#x20;   preds = pd.Series(index=df.index, dtype=float)

&#x20;   for start in range(train\_days, len(df) - 1, step):

&#x20;       train = df.iloc\[start - train\_days:start].dropna()

&#x20;       test = df.iloc\[start:start + step]

&#x20;       scaler = StandardScaler().fit(train\[feature\_cols])

&#x20;       model = Ridge(alpha=alpha).fit(scaler.transform(train\[feature\_cols]), train\["target"])

&#x20;       preds.iloc\[start:start + step] = model.predict(scaler.transform(test\[feature\_cols]))

&#x20;   return preds

```



\### 3.4 Backtest (`backtest.py`)

```python

signal   = (preds > threshold).astype(int)        # 1 = long, 0 = flat

position = signal.shift(1).fillna(0)              # act on the NEXT bar, no look-ahead

trades   = position.diff().abs().fillna(0)

strat\_ret = position \* df\["ret"] - trades \* cost

equity    = (1 + strat\_ret).cumprod()

bh\_equity = (1 + df\["ret"]).cumprod()

```



Metrics (always shown next to buy-and-hold):



\- Total return and CAGR

\- Sharpe ratio (annualized, `sqrt(252)`)

\- Max drawdown

\- Win rate and number of trades

\- \*\*Directional accuracy\*\* of the raw predictions

\- Time in market (%)



\### 3.5 API (`server.py`, FastAPI)

| Endpoint | Returns |

|---|---|

| `GET /api/run?ticker=SPY\&threshold=0.0005\&cost=0.0005` | Dates, price, equity curve, buy-and-hold curve, trade markers, metrics |

| `GET /api/signal?ticker=SPY` | Today's prediction and `LONG` / `FLAT` |

| `GET /` | Serves `static/index.html` |



\---



\## 4. UI design



\*\*Feel:\*\* minimal, black, sleek, fast. Think trading terminal meets Apple keynote.



\### Visual language

\- Background pure `#000`, panels `#0a0a0a` with 1px borders at about 8% white

\- Text near-white `#ededed`, secondary text `#777`

\- One accent color for gains (for example `#00e5a0`) and one for losses (`#ff4d4d`)

\- Font: Inter for text and JetBrains Mono for numbers

\- Small uppercase labels with letter spacing, large light-weight numbers



\### Layout

```

+--------------------------------------------------------------+

|  BOT.                         \[ SPY ]  threshold ---o--  RUN |

+--------------------------------------------+-----------------+

|                                            |  TODAY'S SIGNAL |

|   Chart: price / strategy / buy\&hold       |   ● LONG        |

|   with buy/sell markers                    |   pred +0.12%   |

|                                            |                 |

+--------------------------------------------+-----------------+

|  RETURN   SHARPE   MAX DD   WIN RATE   TRADES   vs BUY\&HOLD |

+--------------------------------------------------------------+

```



\### Animations

\- Staggered fade and slide-up of panels on page load

\- Metric numbers count up from 0 to their value

\- The equity line draws itself left to right after each run

\- Signal dot pulses softly (green glow for LONG, dim for FLAT)

\- Run button: subtle hover glow, then a shimmer or progress bar while the backtest runs

\- Smooth transitions when switching tickers



\### Libraries

\- `lightweight-charts` (TradingView, free) for the chart

\- Plain CSS animations plus a small JS count-up helper. No framework needed.



\---



\## 5. Project structure



```

trading-bot/

├── requirements.txt        # fastapi, uvicorn, yfinance, pandas, numpy, scikit-learn

├── data/                   # cached CSVs

├── bot/

│   ├── data.py

│   ├── features.py

│   ├── model.py

│   ├── backtest.py

│   └── server.py

└── static/

&#x20;   └── index.html

```



Run with: `uvicorn bot.server:app --reload`, then open `http://localhost:8000`.



\---



\## 6. Build phases



| Phase | What | Done when |

|---|---|---|

| 1 | Data download and cache | `SPY.csv` loads, no gaps |

| 2 | Features and target | No NaNs except warm-up rows, look-ahead check passes |

| 3 | Walk-forward model | Predictions exist for every test day |

| 4 | Backtest and metrics | Terminal prints strategy vs buy-and-hold |

| 5 | FastAPI endpoints | `/api/run` returns valid JSON |

| 6 | UI | Chart, cards and animations working |

| 7 | Paper trading (optional) | Daily job sends orders to the Alpaca \*paper\* API |



\---



\## 7. Validation checklist (don't skip)



\- \[ ] Features use only past data (shift test: change tomorrow's price, features for today must not change)

\- \[ ] Signal is shifted by one bar before applying to returns

\- \[ ] Costs are included

\- \[ ] Walk-forward only, with no shuffled splits

\- \[ ] Compared against buy-and-hold \*\*and\*\* a naive baseline (always long)

\- \[ ] Results checked on other tickers and other time periods (one lucky ticker proves nothing)

\- \[ ] Tuned parameters (threshold, window size) are not picked from the same data used to judge the result

\- \[ ] Number of trades is large enough to mean something (dozens, not 5)



\---



\## 8. Likely outcomes and what to do next



\*\*Most likely:\*\* the strategy roughly matches or underperforms buy-and-hold, with lower drawdown because it's often in cash. That is normal.



\*\*Ideas to improve, in order of value:\*\*

1\. Add a regime filter (only trade when price > 200-day MA)

2\. Predict direction (logistic regression) instead of return

3\. Add more tickers and a portfolio layer

4\. Try other models (Random Forest, gradient boosting) under the same walk-forward framework

5\. Add proper position sizing (volatility targeting)

6\. Run on paper trading for 3+ months before considering real money



\---



\## 9. Disclaimer



This is an educational project, not financial advice. Backtests overstate real performance. Never risk money you can't afford to lose.

