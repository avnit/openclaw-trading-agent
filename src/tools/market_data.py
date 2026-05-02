import json
from typing import Any

from claude_agent_sdk import tool
from src.openclaw import OpenClawClient


def _make_market_data_tools(client: OpenClawClient) -> list[Any]:

    @tool(
        "get_quotes",
        "Get live bid/ask/last price and volume for one or more stock symbols",
        {"symbols": list[str]},
    )
    async def get_quotes(args: dict[str, Any]) -> dict[str, Any]:
        symbols: list[str] = args["symbols"]
        quotes = await client.get_quotes(symbols)
        rows = []
        for q in quotes:
            rows.append({
                "symbol": q.symbol,
                "bid": q.bid,
                "ask": q.ask,
                "last": q.last,
                "volume": q.volume,
                "change": q.change,
                "change_pct": round(q.change_pct, 4),
            })
        return {"content": [{"type": "text", "text": json.dumps(rows, indent=2)}]}

    @tool(
        "get_option_expirations",
        "Get available option expiration dates for a symbol",
        {"symbol": str},
    )
    async def get_option_expirations(args: dict[str, Any]) -> dict[str, Any]:
        expirations = await client.get_option_expirations(args["symbol"])
        return {"content": [{"type": "text", "text": json.dumps(expirations, indent=2)}]}

    @tool(
        "get_option_chain",
        "Get the full option chain (calls and puts) for a symbol at a specific expiration date",
        {"symbol": str, "expiration": str},
    )
    async def get_option_chain(args: dict[str, Any]) -> dict[str, Any]:
        chain = await client.get_option_chain(args["symbol"], args["expiration"])
        return {"content": [{"type": "text", "text": json.dumps(chain, indent=2)}]}

    @tool(
        "get_option_greeks",
        "Get option Greeks (delta, gamma, theta, vega, rho) for a symbol",
        {"symbol": str},
    )
    async def get_option_greeks(args: dict[str, Any]) -> dict[str, Any]:
        greeks = await client.get_option_greeks(args["symbol"])
        return {"content": [{"type": "text", "text": json.dumps(greeks, indent=2)}]}

    @tool(
        "search_instruments",
        "Search for tradeable instruments (stocks, ETFs) by name or ticker",
        {"query": str},
    )
    async def search_instruments(args: dict[str, Any]) -> dict[str, Any]:
        instruments = await client.get_instruments(args["query"])
        return {"content": [{"type": "text", "text": json.dumps(instruments[:20], indent=2)}]}

    @tool(
        "get_instrument",
        "Get detailed information about a specific instrument by symbol",
        {"symbol": str},
    )
    async def get_instrument(args: dict[str, Any]) -> dict[str, Any]:
        info = await client.get_instrument(args["symbol"])
        return {"content": [{"type": "text", "text": json.dumps(info, indent=2)}]}

    return [get_quotes, get_option_expirations, get_option_chain, get_option_greeks, search_instruments, get_instrument]


def market_data_tools(client: OpenClawClient) -> list[Any]:
    return _make_market_data_tools(client)
