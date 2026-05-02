"""
openclaw-trading-agent — interactive AI trading assistant powered by Claude Agent SDK.

Usage:
    python main.py                        # interactive REPL
    python main.py "Show my portfolio"    # single one-shot query
"""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, ResultMessage, TextBlock
from claude_agent_sdk import create_sdk_mcp_server

from src.openclaw import OpenClawClient
from src.tools import market_data_tools, portfolio_tools, order_tools

SYSTEM_PROMPT = """You are an expert AI trading assistant connected to a live brokerage account via the OpenClaw API.

You have access to the following tools:

MARKET DATA:
- get_quotes: Get live bid/ask/last price for one or more symbols
- get_option_expirations: Get option expiration dates for a symbol
- get_option_chain: Get full options chain for a symbol and expiration
- get_option_greeks: Get delta, gamma, theta, vega for options
- search_instruments: Search for tradeable instruments
- get_instrument: Get detailed info on a specific instrument

PORTFOLIO:
- get_accounts: List accounts with balances and buying power
- get_portfolio: View current positions with P&L
- get_account_history: View recent transaction history

ORDERS:
- preflight_order: Validate an order BEFORE placing it (always do this first)
- place_order: Execute a trade (buy or sell)
- get_order: Check order status
- replace_order: Modify an open order
- cancel_order: Cancel an open order

TRADING RULES YOU MUST FOLLOW:
1. ALWAYS call preflight_order before place_order — never skip validation.
2. ALWAYS confirm the user's intent before placing or cancelling any order.
3. Summarize the key details (symbol, side, qty, price, estimated cost) before execution.
4. If buying power is insufficient, say so clearly and suggest alternatives.
5. Never place orders for more than the user explicitly requested.
6. When showing prices, always include bid/ask spread context.
7. Flag unusual market conditions (wide spreads, low volume, high volatility).

Be concise, accurate, and cautious. Trading involves real money — prioritize clarity and safety.
"""


def _print_response(message: object) -> None:
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print(f"\n[Agent] {block.text}")
    elif isinstance(message, ResultMessage):
        cost = getattr(message, "total_cost_usd", None)
        if cost is not None:
            print(f"\n[Cost: ${cost:.4f}]")


async def run_query(client: ClaudeSDKClient, prompt: str) -> None:
    await client.query(prompt)
    async for message in client.receive_response():
        _print_response(message)


async def interactive_loop(client: ClaudeSDKClient) -> None:
    print("\n=== OpenClaw Trading Agent ===")
    print("Type your trading request, or 'exit' to quit.\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            print("Goodbye.")
            break
        await run_query(client, user_input)


async def main() -> None:
    api_key = os.getenv("OPENCLAW_API_KEY")
    if not api_key:
        print("ERROR: OPENCLAW_API_KEY is not set. Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)

    async with OpenClawClient() as openclaw:
        all_tools = (
            market_data_tools(openclaw)
            + portfolio_tools(openclaw)
            + order_tools(openclaw)
        )

        mcp_server = create_sdk_mcp_server(
            name="openclaw",
            version="1.0.0",
            tools=all_tools,
        )

        allowed = [f"mcp__openclaw__{t.__name__}" for t in all_tools]

        options = ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            mcp_servers={"openclaw": mcp_server},
            allowed_tools=allowed,
            model="claude-sonnet-4-6",
            permission_mode="acceptEdits",
        )

        async with ClaudeSDKClient(options=options) as sdk_client:
            if len(sys.argv) > 1:
                prompt = " ".join(sys.argv[1:])
                print(f"\nRunning: {prompt!r}\n")
                await run_query(sdk_client, prompt)
            else:
                await interactive_loop(sdk_client)


if __name__ == "__main__":
    asyncio.run(main())
