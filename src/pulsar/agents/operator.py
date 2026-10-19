from __future__ import annotations

from pulsar.db import Database
from pulsar.markets.paper import last_close
from pulsar.markets.registry import MarketRegistry
from pulsar.agents.risk_officer import RiskOfficer
from pulsar.ports.market import Order


class Operator:
    """Places paper/testnet orders for promoted factors. Cannot promote."""

    name = "operator"
    tools = ("place_paper_order",)

    def __init__(self, db: Database, markets: MarketRegistry, risk: RiskOfficer) -> None:
        self.db = db
        self.markets = markets
        self.risk = risk

    def place(
        self,
        market_id: str,
        order: Order,
        live_enabled: bool,
        grokbot_scope: str = "local",
    ) -> dict:
        market = self.markets.get(market_id)
        book = self.markets.book_for(market_id)
        bars = market.candles(order.symbol, limit=50)
        price = last_close(bars)
        promoted = False
        if order.factor_id:
            row = self.db.fetchone(
                "SELECT state FROM promotions WHERE factor_id = ?", (order.factor_id,)
            )
            promoted = bool(row and row["state"] in {"paper", "live"})
        if live_enabled and market_id != "binance_spot":
            return {"ok": False, "reason": "ibkr_live_not_enabled"}
        allowed, reason = self.risk.allow_order(
            market_id, order, book, price, live_enabled, promoted, grokbot_scope
        )
        if not allowed:
            self.db.audit(self.name, "order_denied", {"reason": reason, "order": order.model_dump()})
            return {"ok": False, "reason": reason}
        fill = market.place_order(order)
        self.db.add_order(
            {
                "id": fill.order_id,
                "market_id": fill.market_id,
                "symbol": fill.symbol,
                "side": fill.side,
                "quantity": fill.quantity,
                "price": fill.price,
                "fee": fill.fee,
                "mode": fill.mode,
                "factor_id": order.factor_id,
                "ts": fill.ts.isoformat(),
            }
        )
        self.db.audit(self.name, "order_filled", fill.model_dump())
        self.risk.review_book(market_id, book)
        return {"ok": True, "fill": fill.model_dump()}
