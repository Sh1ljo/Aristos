from pathlib import Path

import pandas as pd
import yfinance as yf

AVAILABLE_TICKERS = ["SPY", "AAPL", "MSFT", "QQQ", "GLD"]

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_ohlcv(ticker: str, years: int = 10) -> pd.DataFrame:
    ticker = ticker.upper()
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / f"{ticker}.csv"
    if path.exists():
        df = pd.read_csv(path, index_col=0, parse_dates=True)
    else:
        end = pd.Timestamp.today().normalize()
        start = end - pd.DateOffset(years=years)
        raw = yf.download(ticker, start=start, end=end, interval="1d", auto_adjust=True, progress=False)
        if raw.empty:
            raise ValueError(f"yfinance returned no data for {ticker}")
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.columns = ["open", "high", "low", "close", "volume"]
        df.to_csv(path)
    df.index = pd.to_datetime(df.index)
    df.index.name = "date"
    df = df.dropna()
    return df[["open", "high", "low", "close", "volume"]]
