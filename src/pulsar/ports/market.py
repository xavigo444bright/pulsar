from __future__ import annotations

from datetime import datetime
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field

Side = Literal["buy", "sell"]
AssetClass = Literal["crypto_spot", "us_equity", "us_future"]
ExecMode = Literal["sim", "paper", "testnet", "live"]


class Bar(BaseModel):
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class Order(BaseModel):
    symbol: str
    side: Side
    quantity: float = Field(gt=0)
    type: Literal["market", "limit"] = "market"
    limit_price: float | None = None
    client_id: str | None = None
    factor_id: str | None = None
    reduce_only: bool = False


class Fill(BaseModel):
    order_id: str
    symbol: str
    side: Side
    quantity: float
    price: float
    fee: float = 0.0
    ts: datetime
    mode: ExecMode
    market_id: str


class Position(BaseModel):
    symbol: str
    quantity: float
    avg_price: float
    market_id: str
    asset_class: AssetClass
    unrealized_pnl: float = 0.0


class Account(BaseModel):
    market_id: str
    cash: float
    equity: float
    mode: ExecMode
    currency: str = "USD"


@runtime_checkable
class MarketPort(Protocol):
    market_id: str
    venue: str
    asset_class: AssetClass
    mode: ExecMode

    def candles(self, symbol: str, timeframe: str = "1h", limit: int = 500) -> list[Bar]: ...

    def account(self) -> Account: ...

    def positions(self) -> list[Position]: ...

    def place_order(self, order: Order) -> Fill: ...

    def supports_live(self) -> bool: ...
