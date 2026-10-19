from __future__ import annotations

from pulsar.db import Database
from pulsar.markets.paper import PaperBook
from pulsar.ports.decision import DecisionPort, DecisionRequest, Question
from pulsar.ports.market import Order
from pulsar.risk.killswitch import KillSwitch
from pulsar.risk.limits import BookLimits, book_for_market


class RiskOfficer:
    """May trip the kill switch. May not invent new limits or place orders."""

    name = "risk_officer"

    def __init__(
        self,
        db: Database,
        decision: DecisionPort,
        kill: KillSwitch,
        books: dict[str, BookLimits],
    ) -> None:
        self.db = db
        self.decision = decision
        self.kill = kill
        self.books = books

    def review_book(self, market_id: str, book: PaperBook) -> KillSwitch:
        key = book_for_market(market_id)
        limits = self.books[key]
        dd = book.drawdown_pct()
        daily = book.daily_loss_pct()
        state = {
            "kill_already": self.kill.tripped,
            "drawdown_pct": dd,
            "daily_loss_pct": daily,
            "max_drawdown_pct": limits.max_drawdown_pct,
            "max_daily_loss_pct": limits.max_daily_loss_pct,
        }
        noul = self.decision.decide(
            DecisionRequest(
                state=state,
                questions={
                    "should_trip_kill": Question(
                        type="noul",
                        instructions="Hard risk limits are already breached.",
                    )
                },
            )
        )
        advisory = float(noul.answers["should_trip_kill"].noul)  # type: ignore[union-attr]
        self.db.log_decision(noul.backend, {"market": market_id}, noul.answers["should_trip_kill"].model_dump())
        if dd >= limits.max_drawdown_pct:
            self._trip(key, f"drawdown {dd:.2%} >= {limits.max_drawdown_pct:.2%}", market_id)
        elif daily >= limits.max_daily_loss_pct:
            self._trip(key, f"daily loss {daily:.2%} >= {limits.max_daily_loss_pct:.2%}", market_id)
        elif advisory >= 0.95 and (dd >= limits.max_drawdown_pct * 0.98):
            self._trip(key, "decisionport_kill_advisory", market_id)
        return self.kill

    def allow_order(
        self,
        market_id: str,
        order: Order,
        book: PaperBook,
        price: float,
        live_enabled: bool,
        promoted: bool,
        grokbot_scope: str,
    ) -> tuple[bool, str]:
        if self.kill.tripped:
            return False, f"kill_switch:{self.kill.reason}"
        key = book_for_market(market_id)
        limits = self.books[key]
        notional = order.quantity * price
        equity = max(book.equity(), 1.0)
        if notional / equity > limits.max_notional_pct:
            return False, "notional_limit"
        if grokbot_scope != "local" and live_enabled:
            return False, "grokbot_cannot_live"
        if live_enabled and not promoted:
            return False, "not_promoted"
        self.review_book(market_id, book)
        if self.kill.tripped:
            return False, f"kill_switch:{self.kill.reason}"
        return True, "ok"

    def _trip(self, book: str, reason: str, market_id: str) -> None:
        self.kill.trip(reason, book)
        self.db.add_risk_event(book, "kill", {"reason": reason, "market_id": market_id})
        self.db.audit(self.name, "kill_switch", {"reason": reason, "market": market_id})
