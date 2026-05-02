import json
from typing import Any

from claude_agent_sdk import tool
from src.openclaw import OpenClawClient
from src.openclaw.types import OrderRequest, OrderSide, OrderType, TimeInForce


def _make_order_tools(client: OpenClawClient) -> list[Any]:

    @tool(
        "preflight_order",
        "Validate an order before placing it — checks buying power, symbol validity, and estimated cost. Always call this before place_order.",
        {
            "symbol": str,
            "side": str,
            "quantity": float,
            "order_type": str,
            "limit_price": float,
            "time_in_force": str,
            "account_id": str,
        },
    )
    async def preflight_order(args: dict[str, Any]) -> dict[str, Any]:
        req = _build_order_request(args)
        result = await client.preflight_order(req, account_id=args.get("account_id"))
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    @tool(
        "place_order",
        "Place a buy or sell order. IMPORTANT: always call preflight_order first to validate. order_type: market|limit|stop|stop_limit. side: buy|sell. time_in_force: day|gtc|ioc|fok.",
        {
            "symbol": str,
            "side": str,
            "quantity": float,
            "order_type": str,
            "limit_price": float,
            "stop_price": float,
            "time_in_force": str,
            "account_id": str,
        },
    )
    async def place_order(args: dict[str, Any]) -> dict[str, Any]:
        req = _build_order_request(args)
        order = await client.place_order(req, account_id=args.get("account_id"))
        return {"content": [{"type": "text", "text": json.dumps(_order_dict(order), indent=2)}]}

    @tool(
        "get_order",
        "Get the current status and details of an order by its order ID",
        {"order_id": str},
    )
    async def get_order(args: dict[str, Any]) -> dict[str, Any]:
        order = await client.get_order(args["order_id"])
        return {"content": [{"type": "text", "text": json.dumps(_order_dict(order), indent=2)}]}

    @tool(
        "replace_order",
        "Modify an existing open order (e.g. change limit price or quantity)",
        {"order_id": str, "limit_price": float, "quantity": float},
    )
    async def replace_order(args: dict[str, Any]) -> dict[str, Any]:
        order_id = args.pop("order_id")
        updates = {k: v for k, v in args.items() if v is not None}
        order = await client.replace_order(order_id, updates)
        return {"content": [{"type": "text", "text": json.dumps(_order_dict(order), indent=2)}]}

    @tool(
        "cancel_order",
        "Cancel an open order by its order ID",
        {"order_id": str},
    )
    async def cancel_order(args: dict[str, Any]) -> dict[str, Any]:
        result = await client.cancel_order(args["order_id"])
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}

    return [preflight_order, place_order, get_order, replace_order, cancel_order]


def _build_order_request(args: dict[str, Any]) -> OrderRequest:
    side = OrderSide(args["side"].lower())
    order_type = OrderType(args.get("order_type", "market").lower())
    tif = TimeInForce(args.get("time_in_force", "day").lower())
    return OrderRequest(
        symbol=args["symbol"].upper(),
        side=side,
        quantity=float(args["quantity"]),
        order_type=order_type,
        limit_price=float(args["limit_price"]) if args.get("limit_price") else None,
        stop_price=float(args["stop_price"]) if args.get("stop_price") else None,
        time_in_force=tif,
    )


def _order_dict(order: Any) -> dict[str, Any]:
    return {
        "order_id": order.order_id,
        "symbol": order.symbol,
        "side": order.side,
        "quantity": order.quantity,
        "filled_quantity": order.filled_quantity,
        "order_type": order.order_type,
        "status": order.status,
        "limit_price": order.limit_price,
        "stop_price": order.stop_price,
        "average_fill_price": order.average_fill_price,
        "created_at": order.created_at,
    }


def order_tools(client: OpenClawClient) -> list[Any]:
    return _make_order_tools(client)
