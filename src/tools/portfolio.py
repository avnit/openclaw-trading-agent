import json
from typing import Any

from claude_agent_sdk import tool
from src.openclaw import OpenClawClient


def _make_portfolio_tools(client: OpenClawClient) -> list[Any]:

    @tool(
        "get_accounts",
        "List all brokerage accounts with buying power, cash balance, and total portfolio value",
        {},
    )
    async def get_accounts(args: dict[str, Any]) -> dict[str, Any]:
        accounts = await client.get_accounts()
        rows = []
        for a in accounts:
            rows.append({
                "account_id": a.account_id,
                "account_number": a.account_number,
                "account_type": a.account_type,
                "buying_power": a.buying_power,
                "cash": a.cash,
                "portfolio_value": a.portfolio_value,
            })
        return {"content": [{"type": "text", "text": json.dumps(rows, indent=2)}]}

    @tool(
        "get_portfolio",
        "Get current portfolio positions including quantity, average cost, current price, market value, and unrealized P&L",
        {"account_id": str},
    )
    async def get_portfolio(args: dict[str, Any]) -> dict[str, Any]:
        positions = await client.get_portfolio(args.get("account_id"))
        rows = []
        for p in positions:
            rows.append({
                "symbol": p.symbol,
                "quantity": p.quantity,
                "average_cost": p.average_cost,
                "current_price": p.current_price,
                "market_value": round(p.market_value, 2),
                "unrealized_pnl": round(p.unrealized_pnl, 2),
                "unrealized_pnl_pct": round(p.unrealized_pnl_pct, 4),
            })
        total_pnl = sum(p.unrealized_pnl for p in positions)
        total_mv = sum(p.market_value for p in positions)
        summary = {
            "positions": rows,
            "summary": {
                "total_positions": len(rows),
                "total_market_value": round(total_mv, 2),
                "total_unrealized_pnl": round(total_pnl, 2),
            },
        }
        return {"content": [{"type": "text", "text": json.dumps(summary, indent=2)}]}

    @tool(
        "get_account_history",
        "Get recent transaction history (trades, dividends, deposits) for an account",
        {"account_id": str, "limit": int},
    )
    async def get_account_history(args: dict[str, Any]) -> dict[str, Any]:
        history = await client.get_history(
            account_id=args.get("account_id"),
            limit=args.get("limit", 50),
        )
        return {"content": [{"type": "text", "text": json.dumps(history, indent=2)}]}

    return [get_accounts, get_portfolio, get_account_history]


def portfolio_tools(client: OpenClawClient) -> list[Any]:
    return _make_portfolio_tools(client)
