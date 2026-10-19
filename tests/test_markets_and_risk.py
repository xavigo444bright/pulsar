from pathlib import Path

from pulsar.config import Settings
from pulsar.db import Database
from pulsar.decision.rules import RuleDecisionPort
from pulsar.markets.registry import MarketRegistry
from pulsar.ports.market import Order
from pulsar.agents.risk_officer import RiskOfficer
from pulsar.risk.killswitch import KillSwitch
from pulsar.risk.limits import BookLimits


def test_binance_and_ibkr_paper_isolated(tmp_path: Path):
    settings = Settings(pulsar_db_path=tmp_path / "t.db", pulsar_data_dir=tmp_path)
    markets = MarketRegistry(settings)
    btc = markets.get("binance_spot").candles("BTCUSDT", limit=10)
    spy = markets.get("ibkr_equity").candles("SPY", limit=10)
    mes = markets.get("ibkr_futures").candles("MES", limit=10)
    assert btc and spy and mes
    assert btc[-1].close != spy[-1].close
    fill = markets.get("binance_spot").place_order(Order(symbol="BTCUSDT", side="buy", quantity=0.01))
    assert fill.market_id == "binance_spot"
    assert markets.spot_book.equity() != markets.equity_book.equity() or markets.spot_book.cash != settings.starting_cash
    assert not markets.get("ibkr_equity").positions()
    assert not markets.get("ibkr_futures").supports_live()
    assert markets.get("ibkr_equity").supports_live() is False


def test_kill_switch_blocks_orders(tmp_path: Path):
    db = Database(tmp_path / "t.db")
    settings = Settings(pulsar_db_path=tmp_path / "t.db", pulsar_data_dir=tmp_path)
    markets = MarketRegistry(settings)
    kill = KillSwitch()
    risk = RiskOfficer(
        db,
        RuleDecisionPort(),
        kill,
        {
            "spot": BookLimits("spot", 0.05, 0.02, 0.08),
            "equity": BookLimits("equity", 0.05, 0.02, 0.08),
            "futures": BookLimits("futures", 0.02, 0.01, 0.05),
        },
    )
    book = markets.spot_book
    book.peak_equity = 100_000
    book.cash = 90_000
    # 10% drawdown vs 8% cap
    risk.review_book("binance_spot", book)
    assert kill.tripped
    ok, reason = risk.allow_order(
        "binance_spot",
        Order(symbol="BTCUSDT", side="buy", quantity=0.001),
        book,
        price=40_000,
        live_enabled=False,
        promoted=True,
        grokbot_scope="local",
    )
    assert not ok and "kill" in reason
