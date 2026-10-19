from pathlib import Path

from fastapi.testclient import TestClient

from pulsar.api.app import create_app
from pulsar.config import Settings
from pulsar.evals import (
    compute_rejects_remote_execution,
    grokbot_tools_exclude_live,
    operator_cannot_promote,
    researcher_has_no_order_tool,
    risk_cannot_invent_limits,
    validator_cannot_trade,
)
from pulsar.evals.agent_evals import mcp_refuses_live
from pulsar.runtime import build_runtime


def test_permission_evals():
    researcher_has_no_order_tool()
    validator_cannot_trade()
    operator_cannot_promote()
    risk_cannot_invent_limits()
    grokbot_tools_exclude_live()
    compute_rejects_remote_execution()


def test_mcp_and_api(tmp_path: Path):
    settings = Settings(pulsar_db_path=tmp_path / "p.db", pulsar_data_dir=tmp_path, pulsar_mcp_token="")
    rt = build_runtime(settings, db_path=settings.pulsar_db_path)
    mcp_refuses_live(rt)
    app = create_app(rt)
    client = TestClient(app)
    home = client.get("/")
    assert home.status_code == 200
    assert "PULSAR" in home.text
    assert client.get("/health").json()["live_enabled"] is False
    started = client.post("/v1/research").json()
    assert started["results"]
    chat_res = client.post("/v1/chat", json={"message": "现在风控怎样"})
    chat = chat_res.json()
    assert chat_res.status_code == 200, chat
    assert chat["tool"] in {"risk_status", "overview", "list_factors", "start_research"}
    man = client.get("/mcp/manifest").json()
    assert "place_live_order" in man["forbidden"]
    called = client.post("/mcp/call", json={"tool": "risk_status"}).json()
    assert "kill" in called
    denied = client.post("/mcp/call", json={"tool": "place_live_order"})
    assert denied.status_code == 403
