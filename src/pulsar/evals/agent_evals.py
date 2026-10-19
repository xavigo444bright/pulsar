"""Agent permission evals. These must stay green in CI."""

from __future__ import annotations

from pulsar.agents.operator import Operator
from pulsar.agents.researcher import Researcher
from pulsar.agents.risk_officer import RiskOfficer
from pulsar.agents.validator import Validator
from pulsar.mcp_server import FORBIDDEN, mcp_call
from pulsar.ports.compute import LocalCompute, TaskRequest, assert_execution_is_local


def researcher_has_no_order_tool() -> None:
    assert "place_order" not in Researcher.tools
    assert "place_paper_order" not in Researcher.tools


def validator_cannot_trade() -> None:
    assert "place_paper_order" not in Validator.tools
    assert "place_order" not in Validator.tools


def operator_cannot_promote() -> None:
    assert "run_gauntlet" not in Operator.tools
    assert "set_promotion" not in Operator.tools


def risk_cannot_invent_limits() -> None:
    assert "set_limits" not in getattr(RiskOfficer, "tools", ())
    assert not hasattr(RiskOfficer, "set_limits")


def grokbot_tools_exclude_live() -> None:
    for name in FORBIDDEN:
        assert "live" in name or name == "set_limits"


def compute_rejects_remote_execution() -> None:
    try:
        assert_execution_is_local("grokbot", TaskRequest(kind="execute"))
        raise AssertionError("expected PermissionError")
    except PermissionError:
        pass
    LocalCompute().submit(TaskRequest(kind="research"), lambda: {"ok": True})


def mcp_refuses_live(runtime) -> None:
    try:
        mcp_call(runtime, "place_live_order", {}, token_scope="paper")
        raise AssertionError("mcp must refuse live")
    except PermissionError:
        pass
