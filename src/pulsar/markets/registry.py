from __future__ import annotations

from pulsar.config import Settings
from pulsar.markets.binance_spot import BinanceSpotAdapter
from pulsar.markets.ibkr_equity import IBKREquityAdapter
from pulsar.markets.ibkr_futures import IBKRFuturesAdapter
from pulsar.markets.paper import PaperBook
from pulsar.ports.market import MarketPort


class MarketRegistry:
    def __init__(self, settings: Settings) -> None:
        cash = settings.starting_cash
        self.spot_book = PaperBook("binance_spot", cash, fee_bps=5.0, mode="sim")
        self.equity_book = PaperBook("ibkr_equity", cash, fee_bps=1.0, mode="paper")
        self.futures_book = PaperBook("ibkr_futures", cash, fee_bps=2.0, mode="paper")
        live = settings.live_enabled()
        self._markets: dict[str, MarketPort] = {
            "binance_spot": BinanceSpotAdapter(
                self.spot_book, testnet=settings.binance_testnet, live_enabled=live
            ),
            "ibkr_equity": IBKREquityAdapter(self.equity_book, connected=settings.ibkr_enabled),
            "ibkr_futures": IBKRFuturesAdapter(self.futures_book, connected=settings.ibkr_enabled),
        }

    def get(self, market_id: str) -> MarketPort:
        return self._markets[market_id]

    def all(self) -> list[MarketPort]:
        return list(self._markets.values())

    def book_for(self, market_id: str) -> PaperBook:
        if market_id == "ibkr_equity":
            return self.equity_book
        if market_id == "ibkr_futures":
            return self.futures_book
        return self.spot_book
