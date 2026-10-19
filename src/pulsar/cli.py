from __future__ import annotations

import json
from pathlib import Path

import typer
import uvicorn

from pulsar.config import get_settings
from pulsar.runtime import build_runtime

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Pulsar paper-first wealth agent")


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the API used by the web UI and Grok Bot MCP."""
    uvicorn.run("pulsar.api.app:app", host=host, port=port, reload=False)


@app.command()
def research() -> None:
    """Run one RSI-family research + gauntlet + paper fills."""
    rt = build_runtime()
    result = rt.research()
    typer.echo(json.dumps(result, indent=2, default=str))


@app.command()
def overview() -> None:
    rt = build_runtime()
    typer.echo(json.dumps(rt.overview(), indent=2, default=str))


@app.command()
def seed() -> None:
    """Create the sqlite file and run a demo research cycle."""
    settings = get_settings()
    settings.ensure_dirs()
    rt = build_runtime(settings)
    rt.research()
    typer.echo(f"Seeded {settings.pulsar_db_path}")
    typer.echo(json.dumps({"board": rt.overview()["board"]}, indent=2, default=str))


@app.command()
def mcp_manifest() -> None:
    from pulsar.mcp_server import mcp_manifest as manifest

    typer.echo(json.dumps(manifest(), indent=2))


@app.command()
def live_status() -> None:
    settings = get_settings()
    typer.echo(
        json.dumps(
            {
                "live_enabled": settings.live_enabled(),
                "flag": settings.pulsar_live,
                "confirm_set": bool(settings.pulsar_live_confirm),
            }
        )
    )


def main() -> None:
    Path("data").mkdir(exist_ok=True)
    app()


if __name__ == "__main__":
    main()
