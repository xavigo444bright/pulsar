from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pulsar.ports.market import Account, Bar, Fill, Order, Position


class PaperBook:
    """Local matching: market orders fill at last close. Isolated per market."""

    def __init__(
        self,
        market_id: str,
        starting_cash: float,
        fee_bps: float,
        mode: str = "sim",
        currency: str = "USD",
    ) -> None:
        self.market_id = market_id
        self.cash = starting_cash
        self.starting_cash = starting_cash
        self.fee_bps = fee_bps
        self.mode = mode
        self.currency = currency
        self._positions: dict[str, Position] = {}
        self._last: dict[str, float] = {}
        self.fills: list[Fill] = []
        self.day_realized = 0.0
        self.peak_equity = starting_cash

    def mark(self, symbol: str, price: float) -> None:
        self._last[symbol] = price
        pos = self._positions.get(symbol)
        if pos:
            pos.unrealized_pnl = (price - pos.avg_price) * pos.quantity

    def last_price(self, symbol: str) -> float:
        return self._last.get(symbol, 0.0)

    def equity(self) -> float:
        unreal = sum(p.unrealized_pnl for p in self._positions.values())
        return self.cash + unreal

    def account(self) -> Account:
        eq = self.equity()
        self.peak_equity = max(self.peak_equity, eq)
        return Account(
            market_id=self.market_id,
            cash=self.cash,
            equity=eq,
            mode=self.mode,  # type: ignore[arg-type]
            currency=self.currency,
        )

    def positions(self) -> list[Position]:
        return [p for p in self._positions.values() if abs(p.quantity) > 1e-12]

    def drawdown_pct(self) -> float:
        eq = self.equity()
        if self.peak_equity <= 0:
            return 0.0
        return max(0.0, (self.peak_equity - eq) / self.peak_equity)

    def daily_loss_pct(self) -> float:
        if self.starting_cash <= 0:
            return 0.0
        loss = max(0.0, -self.day_realized)
        return loss / self.starting_cash

    def fill(self, order: Order, price: float, asset_class: str) -> Fill:
        notional = order.quantity * price
        fee = notional * self.fee_bps / 10_000
        signed = order.quantity if order.side == "buy" else -order.quantity
        pos = self._positions.get(order.symbol) or Position(
            symbol=order.symbol,
            quantity=0.0,
            avg_price=price,
            market_id=self.market_id,
            asset_class=asset_class,  # type: ignore[arg-type]
        )
        realized = 0.0
        if pos.quantity == 0 or (pos.quantity > 0 and signed > 0) or (pos.quantity < 0 and signed < 0):
            new_qty = pos.quantity + signed
            if new_qty != 0:
                pos.avg_price = (pos.avg_price * abs(pos.quantity) + price * abs(signed)) / abs(new_qty)
            pos.quantity = new_qty
        else:
            close_qty = min(abs(signed), abs(pos.quantity))
            realized = (price - pos.avg_price) * close_qty * (1 if pos.quantity > 0 else -1)
            pos.quantity += signed
            if abs(pos.quantity) < 1e-12:
                pos.quantity = 0.0
        self.day_realized += realized
        if order.side == "buy":
            self.cash -= notional + fee
        else:
            self.cash += notional - fee
        pos.unrealized_pnl = (price - pos.avg_price) * pos.quantity
        self._positions[order.symbol] = pos
        fill = Fill(
            order_id=str(uuid4()),
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=price,
            fee=fee,
            ts=datetime.now(timezone.utc),
            mode=self.mode,  # type: ignore[arg-type]
            market_id=self.market_id,
        )
        self.fills.append(fill)
        self.mark(order.symbol, price)
        return fill


def last_close(bars: list[Bar]) -> float:
    if not bars:
        raise ValueError("no bars to price an order")
    return bars[-1].close
