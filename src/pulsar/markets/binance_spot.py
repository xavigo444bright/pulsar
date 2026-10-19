from __future__ import annotations

from pulsar.markets.paper import PaperBook, last_close
from pulsar.markets.synthetic import generate_bars
from pulsar.ports.market import Account, Bar, Fill, Order, Position


class BinanceSpotAdapter:
    market_id = "binance_spot"
    venue = "binance"
    asset_class = "crypto_spot"  # type: ignore[assignment]

    def __init__(self, book: PaperBook, testnet: bool = True, live_enabled: bool = False) -> None:
        self.book = book
        self.testnet = testnet
        self._live_enabled = live_enabled
        self.mode = "live" if live_enabled and not testnet else ("testnet" if testnet else "sim")
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
        acct = self.book.account()
        acct.mode = self.mode  # type: ignore[assignment]
        return acct

    def positions(self) -> list[Position]:
        return self.book.positions()

    def place_order(self, order: Order) -> Fill:
        bars = self.candles(order.symbol)
        price = last_close(bars)
        if order.type == "limit" and order.limit_price:
            price = order.limit_price
        fill = self.book.fill(order, price, self.asset_class)
        fill.mode = self.mode  # type: ignore[assignment]
        return fill

    def supports_live(self) -> bool:
        return True
