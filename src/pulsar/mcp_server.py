"""HTTP MCP-shaped tools for Grok Bot. Live execution is never exposed."""

from __future__ import annotations

from typing import Any

from pulsar.runtime import Runtime

TOOLS = [
    {
        "name": "overview",
        "description": "Accounts, promotion board, kill switch. Paper-safe.",
        "arguments": {},
    },
    {
        "name": "start_research",
        "description": "Run RSI-family mining plus gauntlet on BTC and SPY synthetic/paper data.",
        "arguments": {},
    },
    {
        "name": "list_factors",
        "description": "Promotion board.",
        "arguments": {},
    },
    {
        "name": "why_not_promoted",
        "description": "Explain a rejected factor.",
        "arguments": {"factor_id": "optional factor id"},
    },
    {
        "name": "risk_status",
        "description": "Kill switch and risk events.",
        "arguments": {},
    },
    {
        "name": "get_evals",
        "description": "Recent gate metrics.",
        "arguments": {},
    },
]


FORBIDDEN = {"place_live_order", "enable_live", "set_limits", "ibkr_live"}


def mcp_manifest() -> dict[str, Any]:
    return {
        "name": "pulsar",
        "version": "0.1.0",
        "scope": "paper",
        "tools": TOOLS,
        "forbidden": sorted(FORBIDDEN),
        "note": "Grok Bot must run this process in paper mode on its own computer. Live keys stay on the operator laptop.",
    }


def mcp_call(runtime: Runtime, tool: str, arguments: dict[str, Any], token_scope: str = "paper") -> dict[str, Any]:
    if tool in FORBIDDEN:
        raise PermissionError(f"{tool} is not available to Grok Bot")
    if token_scope not in {"paper", "research", "local"}:
        raise PermissionError("mcp scope cannot include live")
    if tool == "overview":
        return runtime.overview()
    if tool == "start_research":
        return {"results": runtime.research()}
    if tool == "list_factors":
        return {"board": runtime.overview()["board"]}
    if tool == "why_not_promoted":
        return {"items": runtime.why(arguments.get("factor_id"))}
    if tool == "risk_status":
        ov = runtime.overview()
        return {"kill": ov["kill"], "risk_events": ov["risk_events"], "limits": ov["limits"]}
    if tool == "get_evals":
        return {"evaluations": runtime.overview()["evaluations"]}
    raise KeyError(tool)
