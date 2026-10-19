from __future__ import annotations

from dataclasses import dataclass

from pulsar.config import Settings


@dataclass
class BookLimits:
    name: str
    max_notional_pct: float
    max_daily_loss_pct: float
    max_drawdown_pct: float


def limits_from_settings(settings: Settings) -> dict[str, BookLimits]:
    return {
        "spot": BookLimits(
            "spot",
            settings.pulsar_spot_max_notional_pct,
            settings.pulsar_spot_max_daily_loss_pct,
            settings.pulsar_spot_max_drawdown_pct,
        ),
        "futures": BookLimits(
            "futures",
            settings.pulsar_futures_max_notional_pct,
            settings.pulsar_futures_max_daily_loss_pct,
            settings.pulsar_futures_max_drawdown_pct,
        ),
        "equity": BookLimits(
            "equity",
            settings.pulsar_spot_max_notional_pct,
            settings.pulsar_spot_max_daily_loss_pct,
            settings.pulsar_spot_max_drawdown_pct,
        ),
    }


def book_for_market(market_id: str) -> str:
    if market_id == "ibkr_futures":
        return "futures"
    if market_id == "ibkr_equity":
        return "equity"
    return "spot"
