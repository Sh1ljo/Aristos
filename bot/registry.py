STRATEGIES: dict[str, dict] = {}


def register(name: str, description: str, params: list[dict], run, detail=None) -> None:
    if name in STRATEGIES:
        raise ValueError(f"strategy already registered: {name}")
    STRATEGIES[name] = {
        "name": name,
        "description": description,
        "params": params,
        "run": run,
        "detail": detail,
    }


def get(name: str) -> dict:
    if name not in STRATEGIES:
        known = ", ".join(sorted(STRATEGIES))
        raise ValueError(f"unknown strategy '{name}', available: {known}")
    return STRATEGIES[name]


def defaults(name: str) -> dict:
    return {p["name"]: p["default"] for p in get(name)["params"]}
