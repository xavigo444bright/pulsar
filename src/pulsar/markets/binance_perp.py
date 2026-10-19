from __future__ import annotations

from pulsar.ports.market import Account, Bar, Fill, Order, Position


class BinancePerpAdapter:
    """Reserved. BTC perpetual is not a v1 execution venue."""

    market_id = "binance_perp"
    venue = "binance"
    asset_class = "crypto_spot"  # placeholder; not used
    mode = "sim"

    def candles(self, symbol: str, timeframe: str = "1h", limit: int = 500) -> list[Bar]:
        raise NotImplementedError("Binance perpetual adapter is reserved for a later milestone")

    def account(self) -> Account:
        raise NotImplementedError("Binance perpetual adapter is reserved for a later milestone")

    def positions(self) -> list[Position]:
        raise NotImplementedError("Binance perpetual adapter is reserved for a later milestone")

    def place_order(self, order: Order) -> Fill:
        raise NotImplementedError("Binance perpetual adapter is reserved for a later milestone")

    def supports_live(self) -> bool:
        return False
