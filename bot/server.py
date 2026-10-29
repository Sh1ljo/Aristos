from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse

app = FastAPI(title="PyTrading")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/tickers")
def get_tickers() -> dict:
    try:
        from bot.data import AVAILABLE_TICKERS
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=f"backend not ready: {exc}")
    return {"tickers": list(AVAILABLE_TICKERS)}


@app.get("/api/strategies")
def get_strategies() -> dict:
    try:
        import bot.strategies  # noqa: F401 - import triggers registration
        from bot.registry import STRATEGIES
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=f"backend not ready: {exc}")
    return {
        "strategies": [
            {"name": s["name"], "description": s["description"], "params": s["params"]}
            for s in STRATEGIES.values()
        ]
    }


def _strategy_params(strategy: str, request: Request) -> dict:
    import bot.strategies  # noqa: F401 - import triggers registration
    from bot.registry import defaults, get

    try:
        params = defaults(strategy)
        for p in get(strategy)["params"]:
            if p["name"] in request.query_params:
                params[p["name"]] = float(request.query_params[p["name"]])
        return params
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/run")
def get_run(request: Request, strategy: str = "ema_cross", ticker: str = "SPY", cost: float = 0.0005, years: int = 10) -> dict:
    params = _strategy_params(strategy, request)
    try:
        from bot.backtest import run_backtest
        return run_backtest(strategy, ticker, params, cost=cost, years=years)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/signal")
def get_signal(request: Request, strategy: str = "ema_cross", ticker: str = "SPY") -> dict:
    params = _strategy_params(strategy, request)
    try:
        from bot.backtest import signal_today
        return signal_today(strategy, ticker, params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/optimize")
async def post_optimize(request: Request) -> dict:
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid JSON body")
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="body must be a JSON object")
    try:
        from bot.optimizer import run_optimizer_batch
        return run_optimizer_batch(
            strategy=body.get("strategy", "ema_cross"),
            ticker=body.get("ticker", "SPY"),
            combos=body.get("combos", []),
            cost=float(body.get("cost", 0.0005)),
            years=int(body.get("years", 10)),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
