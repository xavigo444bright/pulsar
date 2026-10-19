from __future__ import annotations

from pulsar.markets.paper import PaperBook, last_close
from pulsar.markets.synthetic import generate_bars
from pulsar.ports.market import Account, Bar, Fill, Order, Position


class IBKRFuturesAdapter:
    market_id = "ibkr_futures"
    venue = "ibkr"
    asset_class = "us_future"  # type: ignore[assignment]
    mode = "paper"

    def __init__(self, book: PaperBook, connected: bool = False) -> None:
        self.book = book
        self.connected = connected
        self._cache: dict[str, list[Bar]] = {}

    def candles(self, symbol: str, timeframe: str = "1h", limit: int = 500) -> list[Bar]:
        key = f"{symbol}:{timeframe}:{limit}"
        if key not in self._cache:
            self._cache[key] = generate_bars(symbol, n=max(limit, 200), timeframe=timeframe)
        bars = self._cache[key][-limit:]
        if bars:
            self.book.mark(symbol, bars[-1].close)
        return bars

    def account(self) -> Account:
        return self.book.account()

    def positions(self) -> list[Position]:
        return self.book.positions()

    def place_order(self, order: Order) -> Fill:
        bars = self.candles(order.symbol)
        return self.book.fill(order, last_close(bars), self.asset_class)

    def supports_live(self) -> bool:
        return False
