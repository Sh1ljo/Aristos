import sys

import numpy as np
import pandas as pd

from .data import load_ohlcv
from .features import build_features
from .registry import defaults, get
from . import strategies  # noqa: F401 - import registers all strategies

DEFAULT_COST = 0.0005


def _metrics(daily: pd.Series) -> dict:
    equity = (1 + daily).cumprod()
    n = len(daily)
    total_return = float(equity.iloc[-1] - 1)
    cagr = float(equity.iloc[-1] ** (252 / n) - 1)
    std = float(daily.std())
    sharpe = float(daily.mean() / std * np.sqrt(252)) if std > 0 else 0.0
    max_drawdown = float((equity / equity.cummax() - 1).min())
    return {"total_return": total_return, "cagr": cagr, "sharpe": sharpe, "max_drawdown": max_drawdown}


def run_backtest(strategy: str, ticker: str, params: dict | None = None, cost: float = DEFAULT_COST, years: int = 10) -> dict:
    ticker = ticker.upper()
    strat = get(strategy)
    params = {**defaults(strategy), **(params or {})}
    df = build_features(load_ohlcv(ticker, years=years))

    result = strat["run"](df, params)
    signal = result["positions"].reindex(df.index)

    bt = pd.DataFrame({"signal": signal, "close": df["close"], "ret": df["ret"]}).dropna(subset=["ret"])
    bt["signal"] = bt["signal"].fillna(0.0)

    position = bt["signal"].shift(1)
    position.iloc[0] = 0.0
    trades = position.diff().abs()
    trades.iloc[0] = 0.0
    strat_ret = position * bt["ret"] - trades * cost

    equity = (1 + strat_ret).cumprod()
    buy_hold = (1 + bt["ret"]).cumprod()

    in_market = bt["ret"][position > 0]
    win_rate = float((in_market > 0).mean()) if len(in_market) else 0.0

    metrics = _metrics(strat_ret)
    bh = _metrics(bt["ret"])
    metrics.update(
        {
            "win_rate": win_rate,
            "trades": int(trades.sum()),
            "time_in_market": float((position > 0).mean()),
            "bh_total_return": bh["total_return"],
            "bh_cagr": bh["cagr"],
            "bh_sharpe": bh["sharpe"],
            "bh_max_drawdown": bh["max_drawdown"],
        }
    )
    metrics.update(result.get("extra_metrics", {}))

    markers = []
    for date in trades.index[trades > 0]:
        side = "buy" if position.loc[date] > 0 else "sell"
        markers.append(
            {"date": date.strftime("%Y-%m-%d"), "side": side, "price": float(bt.loc[date, "close"])}
        )

    # anchor both curves at 1.0 on the day before the first backtest day
    anchor = df.index[df.index.get_loc(bt.index[0]) - 1]
    dates = [anchor.strftime("%Y-%m-%d")] + [d.strftime("%Y-%m-%d") for d in bt.index]
    price = [float(df.loc[anchor, "close"])] + [float(v) for v in bt["close"]]
    equity_vals = [1.0] + [float(v) for v in equity]
    buy_hold_vals = [1.0] + [float(v) for v in buy_hold]

    return {
        "strategy": strategy,
        "ticker": ticker,
        "dates": dates,
        "price": price,
        "equity": equity_vals,
        "buy_hold": buy_hold_vals,
        "trades": markers,
        "metrics": metrics,
    }


def signal_today(strategy: str, ticker: str, params: dict | None = None) -> dict:
    ticker = ticker.upper()
    strat = get(strategy)
    params = {**defaults(strategy), **(params or {})}
    df = build_features(load_ohlcv(ticker))
    signal = strat["run"](df, params)["positions"].reindex(df.index)
    position = float(signal.iloc[-1]) if signal.notna().iloc[-1] else 0.0
    detail = strat["detail"](df, params) if strat["detail"] else None
    return {
        "strategy": strategy,
        "ticker": ticker,
        "date": df.index[-1].strftime("%Y-%m-%d"),
        "signal": "LONG" if position > 0 else "FLAT",
        "position": position,
        "detail": detail,
    }


def main() -> None:
    ticker = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    strategy = sys.argv[2] if len(sys.argv) > 2 else "linreg"
    result = run_backtest(strategy, ticker)
    m = result["metrics"]

    def pct(x: float) -> str:
        return f"{x * 100:.1f}%"

    print(f"{result['ticker']}  {result['strategy']}  {result['dates'][0]} -> {result['dates'][-1]}  ({len(result['dates'])} days)")
    print(f"{'':20}{'STRATEGY':>12}{'BUY&HOLD':>12}")
    print(f"{'total return':20}{pct(m['total_return']):>12}{pct(m['bh_total_return']):>12}")
    print(f"{'cagr':20}{pct(m['cagr']):>12}{pct(m['bh_cagr']):>12}")
    print(f"{'sharpe':20}{m['sharpe']:>12.2f}{m['bh_sharpe']:>12.2f}")
    print(f"{'max drawdown':20}{pct(m['max_drawdown']):>12}{pct(m['bh_max_drawdown']):>12}")
    print(f"{'win rate':20}{pct(m['win_rate']):>12}")
    print(f"{'trades':20}{m['trades']:>12}")
    if "directional_accuracy" in m:
        print(f"{'directional acc':20}{pct(m['directional_accuracy']):>12}")
    print(f"{'time in market':20}{pct(m['time_in_market']):>12}")


if __name__ == "__main__":
    main()
