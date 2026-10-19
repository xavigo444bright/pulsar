# Grok Bot workers

Grok Bot is a persistent cloud computer. Pulsar treats it as a research factory, not a broker.

## Named bots

Create three Bots. Same computer, so **do not store live keys there**.

### pulsar-researcher

Job: clone this repo, `pip install -e .`, `pulsar research`, summarize the promotion board. Stay inside the RSI family. Write failures into sqlite memory. Never ask for Binance live or IBKR live credentials.

### pulsar-validator

Job: `pytest -q` and `pulsar overview`. If `noise_control` is not rejected, stop and report a product bug.

### pulsar-sentry

Job: poll `GET /v1/overview` if the API is running on this computer, or run `pulsar overview`. If kill switch is tripped, message the owner. Do not reset limits. Do not place orders.

## How to run on the Bot computer

```bash
git clone <this-repo>
cd pulsar
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
# leave PULSAR_LIVE=false, do not paste live keys
pulsar seed
```

If you need HTTP MCP from another Bot, start `pulsar serve` on the same cloud computer and call `POST /mcp/call`. Tools are paper-scoped. `place_live_order` is always 403.

## Skills to save after one demo

See `docs/grokbot/skills/`.
