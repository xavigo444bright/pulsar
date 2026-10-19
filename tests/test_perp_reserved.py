import pytest

from pulsar.markets.binance_perp import BinancePerpAdapter


def test_perp_is_stub():
    with pytest.raises(NotImplementedError):
        BinancePerpAdapter().candles("BTCUSDT")
