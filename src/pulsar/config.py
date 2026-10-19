from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


LIVE_CONFIRM_PHRASE = "I_UNDERSTAND_THE_RISK"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    pulsar_live: bool = False
    pulsar_live_confirm: str = ""
    pulsar_data_dir: Path = Path("./data")
    pulsar_db_path: Path = Path("./data/pulsar.db")
    pulsar_log_level: str = "INFO"
    pulsar_host: str = "127.0.0.1"
    pulsar_port: int = 8000

    pulsar_decision_backend: str = "rules"
    typesafe_api_key: str = ""
    typesafe_base_url: str = "https://api.typesafe.ai/v1"

    pulsar_llm_api_key: str = ""
    pulsar_llm_base_url: str = "https://api.x.ai/v1"
    pulsar_llm_model: str = "grok-4"

    pulsar_compute: str = "local"
    pulsar_mcp_token: str = ""
    pulsar_grokbot_scope: str = "paper"

    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_testnet: bool = True

    ibkr_enabled: bool = False
    ibkr_host: str = "127.0.0.1"
    ibkr_port: int = 7497
    ibkr_client_id: int = 1
    ibkr_paper: bool = True

    pulsar_spot_max_notional_pct: float = 0.05
    pulsar_spot_max_daily_loss_pct: float = 0.02
    pulsar_spot_max_drawdown_pct: float = 0.08
    pulsar_futures_max_notional_pct: float = 0.02
    pulsar_futures_max_daily_loss_pct: float = 0.01
    pulsar_futures_max_drawdown_pct: float = 0.05

    starting_cash: float = Field(default=100_000.0)

    def live_enabled(self) -> bool:
        return (
            self.pulsar_live
            and self.pulsar_live_confirm.strip() == LIVE_CONFIRM_PHRASE
        )

    def grokbot_may_live(self) -> bool:
        return False

    def ensure_dirs(self) -> None:
        self.pulsar_data_dir.mkdir(parents=True, exist_ok=True)
        self.pulsar_db_path.parent.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    return Settings()
