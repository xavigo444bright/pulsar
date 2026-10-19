from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pulsar.agents.chat import ChatRouter, format_overview
from pulsar.agents.operator import Operator
from pulsar.agents.researcher import Researcher
from pulsar.agents.risk_officer import RiskOfficer
from pulsar.agents.validator import Validator
from pulsar.config import Settings, get_settings
from pulsar.db import Database
from pulsar.decision.factory import get_decision_port
from pulsar.markets.registry import MarketRegistry
from pulsar.ports.compute import LocalCompute, TaskRequest
from pulsar.ports.market import Order
from pulsar.promotion.machine import PromotionMachine
from pulsar.risk.killswitch import KillSwitch
from pulsar.risk.limits import limits_from_settings


@dataclass
class Runtime:
    settings: Settings
    db: Database
    markets: MarketRegistry
    decision: Any
    compute: LocalCompute
    kill: KillSwitch
    researcher: Researcher
    validator: Validator
    operator: Operator
    risk: RiskOfficer
    chat: ChatRouter

    def overview(self) -> dict[str, Any]:
        accounts = [m.account().model_dump() for m in self.markets.all()]
        positions = []
        for m in self.markets.all():
            positions.extend([p.model_dump() for p in m.positions()])
        board = self.db.fetchall(
            """SELECT p.factor_id, p.state, p.reason, f.name, f.family, p.updated
               FROM promotions p LEFT JOIN factors f ON f.id = p.factor_id
               ORDER BY p.updated DESC"""
        )
        evals = self.db.fetchall(
            "SELECT factor_id, market_id, symbol, metrics, passed, created FROM evaluations ORDER BY id DESC LIMIT 40"
        )
        memories = self.db.fetchall("SELECT title, reason, created FROM memories ORDER BY id DESC LIMIT 20")
        audit = self.db.fetchall(
            "SELECT ts, actor, action, payload FROM audit_log ORDER BY id DESC LIMIT 30"
        )
        risk_events = self.db.fetchall(
            "SELECT ts, book, kind, detail FROM risk_events ORDER BY id DESC LIMIT 20"
        )
        return {
            "live_enabled": self.settings.live_enabled(),
            "decision_backend": self.decision.backend,
            "compute": self.compute.name,
            "kill": {
                "tripped": self.kill.tripped,
                "reason": self.kill.reason,
                "book": self.kill.book,
            },
            "accounts": accounts,
            "positions": positions,
            "board": board,
            "evaluations": evals,
            "memories": memories,
            "audit": audit,
            "risk_events": risk_events,
            "limits": {k: v.__dict__ for k, v in limits_from_settings(self.settings).items()},
        }

    def research(self) -> list[dict[str, Any]]:
        def _run() -> dict[str, Any]:
            records = self.validator.run_gauntlet(
                primary=self.markets.get("binance_spot"),
                secondary=self.markets.get("ibkr_equity"),
                primary_symbol="BTCUSDT",
                secondary_symbol="SPY",
                fee_bps_primary=5.0,
                fee_bps_secondary=1.0,
                live_enabled=self.settings.live_enabled(),
            )
            # Paper-trade a token size for each promoted factor on BTC to prove the loop.
            for rec in records:
                if rec.state != "paper":
                    continue
                last = self.markets.get("binance_spot").candles("BTCUSDT", limit=2)[-1].close
                qty = max(0.001, (self.markets.spot_book.equity() * 0.01) / last)
                self.operator.place(
                    "binance_spot",
                    Order(symbol="BTCUSDT", side="buy", quantity=qty, factor_id=rec.factor.id),
                    live_enabled=False,
                    grokbot_scope="local",
                )
            return {
                "count": len(records),
                "paper": [r.factor.id for r in records if r.state == "paper"],
                "rejected": [r.factor.id for r in records if r.state == "rejected"],
            }

        result = self.compute.submit(TaskRequest(kind="research", payload={}), _run)
        self.db.audit("researcher", "cycle", result.detail)
        return [result.model_dump()]

    def why(self, factor_id: str | None = None) -> list[dict[str, Any]]:
        if factor_id:
            row = self.db.fetchone("SELECT * FROM promotions WHERE factor_id = ?", (factor_id,))
            ev = self.db.fetchall("SELECT * FROM evaluations WHERE factor_id = ?", (factor_id,))
            return [{"promotion": row, "evaluations": ev}]
        return self.db.fetchall("SELECT * FROM promotions WHERE state = 'rejected'")

    def trip(self, reason: str = "user_requested") -> dict[str, Any]:
        self.kill.trip(reason, "all")
        self.db.add_risk_event("all", "kill", {"reason": reason})
        self.db.audit("user", "kill_switch", {"reason": reason})
        return {"tripped": True, "reason": reason}

    def reset_kill(self) -> dict[str, Any]:
        self.kill.reset()
        self.db.audit("user", "kill_reset", {})
        return {"tripped": False}

    def handle_chat(self, text: str) -> dict[str, Any]:
        tool = self.chat.route(text)
        if tool == "start_research":
            payload = self.research()
            reply = f"Research cycle finished. {payload[0]['detail']}"
        elif tool == "why_not_promoted":
            payload = self.why()
            reply = "Rejected factors:\n" + "\n".join(
                f"- {r.get('factor_id')}: {r.get('reason')}" for r in payload[:8]
            )
        elif tool == "risk_status":
            payload = self.overview()["kill"]
            reply = f"Kill switch tripped={payload['tripped']} reason={payload['reason']}"
        elif tool == "kill":
            payload = self.trip("chat_kill")
            reply = "Kill switch tripped. No further orders will pass."
        elif tool == "paper_trade":
            payload = {"ok": False, "reason": "use_start_research_to_paper_fill_promoted"}
            reply = "Paper fills happen automatically for factors that pass the gauntlet. Ask me to start research."
        elif tool == "list_factors":
            payload = self.overview()["board"]
            reply = "\n".join(f"- {r.get('factor_id')} [{r.get('state')}] {r.get('reason')}" for r in payload) or "No board yet. Start research."
        else:
            payload = self.overview()
            reply = format_overview(payload)
        self.db.audit("chat", tool, {"text": text})
        return {"tool": tool, "reply": reply, "data": payload}


def build_runtime(settings: Settings | None = None, db_path=None) -> Runtime:
    settings = settings or get_settings()
    settings.ensure_dirs()
    db = Database(db_path or settings.pulsar_db_path)
    markets = MarketRegistry(settings)
    decision = get_decision_port(settings)
    kill = KillSwitch()
    risk = RiskOfficer(db, decision, kill, limits_from_settings(settings))
    machine = PromotionMachine(db, decision)
    return Runtime(
        settings=settings,
        db=db,
        markets=markets,
        decision=decision,
        compute=LocalCompute(),
        kill=kill,
        researcher=Researcher(),
        validator=Validator(machine),
        operator=Operator(db, markets, risk),
        risk=risk,
        chat=ChatRouter(decision),
    )
