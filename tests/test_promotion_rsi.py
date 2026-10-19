from pathlib import Path

from pulsar.config import Settings
from pulsar.research.rsi.family import BASELINE_ID
from pulsar.runtime import build_runtime


def test_research_cycle_promotes_only_rsi_and_never_noise(tmp_path: Path):
    settings = Settings(pulsar_db_path=tmp_path / "p.db", pulsar_data_dir=tmp_path, pulsar_live=False)
    rt = build_runtime(settings, db_path=settings.pulsar_db_path)
    rt.research()
    board = {row["factor_id"]: row for row in rt.overview()["board"]}
    assert "noise_control" in board
    assert board["noise_control"]["state"] == "rejected"
    assert board[BASELINE_ID]["state"] in {"candidate", "paper", "rejected"}
    for row in board.values():
        if row["state"] == "paper":
            assert "rsi" in (row.get("family") or "rsi")
    # Live remains off
    assert rt.settings.live_enabled() is False
    for acct in rt.overview()["accounts"]:
        assert acct["mode"] != "live"


def test_live_requires_confirm_phrase(tmp_path: Path):
    settings = Settings(
        pulsar_db_path=tmp_path / "p.db",
        pulsar_data_dir=tmp_path,
        pulsar_live=True,
        pulsar_live_confirm="nope",
    )
    assert settings.live_enabled() is False
    settings.pulsar_live_confirm = "I_UNDERSTAND_THE_RISK"
    assert settings.live_enabled() is True
