from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from fastapi import Body, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

STATIC_DIR = Path(__file__).resolve().parent / "static"

from pulsar import __version__
from pulsar.config import LIVE_CONFIRM_PHRASE
from pulsar.mcp_server import mcp_call, mcp_manifest
from pulsar.ports.market import Order
from pulsar.runtime import Runtime, build_runtime

_runtime: Runtime | None = None


class ChatIn(BaseModel):
    message: str


class KillIn(BaseModel):
    reason: str = "api"


class OrderIn(BaseModel):
    market_id: str
    symbol: str
    side: str
    quantity: float
    factor_id: str | None = None


class McpIn(BaseModel):
    tool: str
    arguments: dict[str, Any] = {}


def get_runtime() -> Runtime:
    global _runtime
    if _runtime is None:
        _runtime = build_runtime()
    return _runtime


def create_app(runtime: Runtime | None = None) -> FastAPI:
    global _runtime
    if runtime is not None:
        _runtime = runtime
    app = FastAPI(title="Pulsar", version=__version__, description="Paper-first wealth agent")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def health() -> dict[str, Any]:
        rt = get_runtime()
        return {
            "ok": True,
            "version": __version__,
            "live_enabled": rt.settings.live_enabled(),
            "decision_backend": rt.decision.backend,
        }

    @app.get("/v1/overview")
    def overview() -> dict[str, Any]:
        return get_runtime().overview()

    @app.post("/v1/research")
    def research() -> dict[str, Any]:
        return {"results": get_runtime().research()}

    @app.post("/v1/chat")
    def chat(payload: Annotated[ChatIn, Body()]) -> dict[str, Any]:
        return get_runtime().handle_chat(payload.message)

    @app.get("/v1/factors")
    def factors() -> dict[str, Any]:
        return {"board": get_runtime().overview()["board"]}

    @app.get("/v1/factors/{factor_id}/why")
    def why(factor_id: str) -> dict[str, Any]:
        return {"items": get_runtime().why(factor_id)}

    @app.post("/v1/kill")
    def kill(payload: Annotated[KillIn, Body()]) -> dict[str, Any]:
        return get_runtime().trip(payload.reason)

    @app.post("/v1/kill/reset")
    def kill_reset() -> dict[str, Any]:
        return get_runtime().reset_kill()

    @app.post("/v1/paper/order")
    def paper_order(payload: Annotated[OrderIn, Body()]) -> dict[str, Any]:
        rt = get_runtime()
        return rt.operator.place(
            payload.market_id,
            Order(symbol=payload.symbol, side=payload.side, quantity=payload.quantity, factor_id=payload.factor_id),  # type: ignore[arg-type]
            live_enabled=False,
        )

    @app.get("/v1/safety")
    def safety() -> dict[str, Any]:
        rt = get_runtime()
        return {
            "live_enabled": rt.settings.live_enabled(),
            "live_requires": ["PULSAR_LIVE=true", f"PULSAR_LIVE_CONFIRM={LIVE_CONFIRM_PHRASE}"],
            "grokbot_scope": rt.settings.pulsar_grokbot_scope,
            "ibkr_live": False,
            "default_mode": "paper/sim",
        }

    @app.get("/mcp/manifest")
    def manifest() -> dict[str, Any]:
        return mcp_manifest()

    @app.post("/mcp/call")
    def call(payload: Annotated[McpIn, Body()], x_pulsar_token: str | None = Header(default=None)) -> dict[str, Any]:
        rt = get_runtime()
        expected = rt.settings.pulsar_mcp_token
        if expected and x_pulsar_token != expected:
            raise HTTPException(status_code=401, detail="bad mcp token")
        try:
            return mcp_call(rt, payload.tool, payload.arguments, token_scope=rt.settings.pulsar_grokbot_scope)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return app


app = create_app()
