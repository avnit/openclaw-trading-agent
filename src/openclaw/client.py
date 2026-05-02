import os
import httpx
from typing import Any

from .types import (
    Account,
    Order,
    OrderRequest,
    Position,
    Quote,
)


class OpenClawClient:
    """Thin async HTTP client wrapping the OpenClaw / Public.com broker API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        account_id: str | None = None,
    ) -> None:
        self._api_key = api_key or os.environ["OPENCLAW_API_KEY"]
        self._base_url = (base_url or os.getenv("OPENCLAW_BASE_URL", "https://api.public.com")).rstrip("/")
        self._account_id = account_id or os.getenv("OPENCLAW_ACCOUNT_ID")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "OpenClawClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    async def _get(self, path: str, **params: Any) -> Any:
        r = await self._client.get(path, params={k: v for k, v in params.items() if v is not None})
        r.raise_for_status()
        return r.json()

    async def _post(self, path: str, body: dict[str, Any]) -> Any:
        r = await self._client.post(path, json=body)
        r.raise_for_status()
        return r.json()

    async def _put(self, path: str, body: dict[str, Any]) -> Any:
        r = await self._client.put(path, json=body)
        r.raise_for_status()
        return r.json()

    async def _delete(self, path: str) -> Any:
        r = await self._client.delete(path)
        r.raise_for_status()
        return r.json()

    def _account_id_required(self) -> str:
        if not self._account_id:
            raise ValueError(
                "account_id is required. Set OPENCLAW_ACCOUNT_ID or pass account_id= to the client."
            )
        return self._account_id

    # ------------------------------------------------------------------ #
    # Account
    # ------------------------------------------------------------------ #

    async def get_accounts(self) -> list[Account]:
        data = await self._get("/v2/accounts")
        accounts = []
        for raw in data.get("accounts", [data]):
            accounts.append(
                Account(
                    account_id=raw.get("account_id", raw.get("id", "")),
                    account_number=raw.get("account_number", ""),
                    account_type=raw.get("account_type", ""),
                    buying_power=float(raw.get("buying_power", 0)),
                    cash=float(raw.get("cash", 0)),
                    portfolio_value=float(raw.get("portfolio_value", raw.get("equity", 0))),
                    raw=raw,
                )
            )
        return accounts

    async def get_portfolio(self, account_id: str | None = None) -> list[Position]:
        aid = account_id or self._account_id_required()
        data = await self._get(f"/v2/accounts/{aid}/portfolio")
        positions = []
        for raw in data.get("positions", []):
            qty = float(raw.get("qty", raw.get("quantity", 0)))
            avg_cost = float(raw.get("avg_entry_price", raw.get("average_cost", 0)))
            current = float(raw.get("current_price", 0))
            mv = qty * current
            pnl = mv - (qty * avg_cost)
            pnl_pct = (pnl / (qty * avg_cost) * 100) if qty * avg_cost != 0 else 0.0
            positions.append(
                Position(
                    symbol=raw.get("symbol", ""),
                    quantity=qty,
                    average_cost=avg_cost,
                    current_price=current,
                    market_value=mv,
                    unrealized_pnl=pnl,
                    unrealized_pnl_pct=pnl_pct,
                    raw=raw,
                )
            )
        return positions

    async def get_history(self, account_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        aid = account_id or self._account_id_required()
        data = await self._get(f"/v2/accounts/{aid}/history", limit=limit)
        return data.get("history", data.get("transactions", []))

    # ------------------------------------------------------------------ #
    # Market data
    # ------------------------------------------------------------------ #

    async def get_quotes(self, symbols: list[str]) -> list[Quote]:
        data = await self._post("/v2/quotes", {"symbols": symbols})
        quotes = []
        for raw in data.get("quotes", []):
            quotes.append(
                Quote(
                    symbol=raw.get("symbol", ""),
                    bid=float(raw.get("bid", 0)),
                    ask=float(raw.get("ask", 0)),
                    last=float(raw.get("last", raw.get("last_trade_price", 0))),
                    volume=int(raw.get("volume", 0)),
                    change=float(raw.get("change", 0)),
                    change_pct=float(raw.get("change_pct", raw.get("percent_change", 0))),
                    raw=raw,
                )
            )
        return quotes

    async def get_option_expirations(self, symbol: str) -> list[str]:
        data = await self._post("/v2/options/expirations", {"symbol": symbol})
        return data.get("expirations", [])

    async def get_option_chain(self, symbol: str, expiration: str) -> dict[str, Any]:
        data = await self._post("/v2/options/chain", {"symbol": symbol, "expiration": expiration})
        return data

    async def get_option_greeks(self, symbol: str) -> dict[str, Any]:
        data = await self._get(f"/v2/instruments/{symbol}/greeks")
        return data

    # ------------------------------------------------------------------ #
    # Instruments
    # ------------------------------------------------------------------ #

    async def get_instruments(self, query: str = "") -> list[dict[str, Any]]:
        data = await self._get("/v2/instruments", query=query or None)
        return data.get("instruments", [])

    async def get_instrument(self, symbol: str) -> dict[str, Any]:
        data = await self._get(f"/v2/instruments/{symbol}")
        return data

    # ------------------------------------------------------------------ #
    # Orders
    # ------------------------------------------------------------------ #

    async def preflight_order(self, req: OrderRequest, account_id: str | None = None) -> dict[str, Any]:
        aid = account_id or self._account_id_required()
        body = self._order_body(req, aid)
        return await self._post("/v2/orders/preflight", body)

    async def place_order(self, req: OrderRequest, account_id: str | None = None) -> Order:
        aid = account_id or self._account_id_required()
        body = self._order_body(req, aid)
        raw = await self._post("/v2/orders", body)
        return self._parse_order(raw)

    async def get_order(self, order_id: str) -> Order:
        raw = await self._get(f"/v2/orders/{order_id}")
        return self._parse_order(raw)

    async def replace_order(self, order_id: str, updates: dict[str, Any]) -> Order:
        raw = await self._put(f"/v2/orders/{order_id}", updates)
        return self._parse_order(raw)

    async def cancel_order(self, order_id: str) -> dict[str, Any]:
        return await self._delete(f"/v2/orders/{order_id}")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _order_body(req: OrderRequest, account_id: str) -> dict[str, Any]:
        body: dict[str, Any] = {
            "account_id": account_id,
            "symbol": req.symbol,
            "side": req.side.value,
            "quantity": req.quantity,
            "type": req.order_type.value,
            "time_in_force": req.time_in_force.value,
        }
        if req.limit_price is not None:
            body["limit_price"] = req.limit_price
        if req.stop_price is not None:
            body["stop_price"] = req.stop_price
        return body

    @staticmethod
    def _parse_order(raw: dict[str, Any]) -> Order:
        order = raw.get("order", raw)
        return Order(
            order_id=order.get("id", order.get("order_id", "")),
            symbol=order.get("symbol", ""),
            side=order.get("side", ""),
            quantity=float(order.get("qty", order.get("quantity", 0))),
            filled_quantity=float(order.get("filled_qty", order.get("filled_quantity", 0))),
            order_type=order.get("type", order.get("order_type", "")),
            status=order.get("status", ""),
            limit_price=float(order["limit_price"]) if order.get("limit_price") else None,
            stop_price=float(order["stop_price"]) if order.get("stop_price") else None,
            average_fill_price=float(order["avg_fill_price"]) if order.get("avg_fill_price") else None,
            created_at=order.get("created_at", ""),
            raw=order,
        )
