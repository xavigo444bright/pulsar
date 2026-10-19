# Pulsar

Paper-first personal wealth agent. Large models propose **RSI-family** factors. A Jev-shaped **DecisionPort** makes typed judgments. Statistical gates and paper trading decide promotion. Code — not the model — places orders, and only inside isolated risk books.

**Not financial advice. Default is simulated/paper trading. Live Binance spot is a double-flag opt-in. IBKR live is not enabled in v1.**

中文：这是开源财富 Agent 的可演示雏形。对话 + 仪表盘。挖因子只在 RSI 族内。BTC 现货是第一条实盘闭环；美股/美股期货走 IBKR 纸交易适配。Grok Bot 只能跑研究与纸交易。

## 60-second demo

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pulsar seed
pulsar serve
```

Dual surface (chat + dashboard): `http://127.0.0.1:8000`  
Health: `http://127.0.0.1:8000/health`

Optional Next.js workspace lives in `apps/web` if you want a separate frontend process.

Or one process:

```bash
docker compose up --build
```

Without exchange keys, Pulsar uses deterministic synthetic OHLCV for `BTCUSDT`, `SPY`, `QQQ`, `MES`.

## What is gated

```
hypothesis → DecisionPort (RSI family?) → walk-forward / holdout vs RSI(14)
         → paper on BTC and fragility check on SPY → live only if you opt in
```

The LLM never receives a live order tool. Grok Bot MCP never exposes `place_live_order`.

## Markets

| Adapter | Asset | v1 depth |
| --- | --- | --- |
| `binance_spot` | BTC/USDT | sim / testnet / live opt-in |
| `ibkr_equity` | SPY / QQQ | paper (synthetic if TWS is off) |
| `ibkr_futures` | MES / ES | paper, **separate risk book** |
| `binance_perp` | — | reserved stub |

Binance-only clone still works. IBKR is optional.

## Architecture ports

- **DecisionPort** — `choice` / `score` / `noul`. Backends: `rules` (default), `llm`, `jev` (TypeSafe, optional).
- **MarketPort** — candles, account, orders. Factors never import `ccxt` or `ib_insync`.
- **ComputePort** — research may run on a Grok Bot computer; **execution stays local**.

## Agent roles

Researcher, Validator, Operator, RiskOfficer. See [docs/agent-spec.md](docs/agent-spec.md).

## Grok Bot

Named workers: `pulsar-researcher`, `pulsar-validator`, `pulsar-sentry`.  
They clone this repo **on the cloud computer**, run `pulsar research` in paper mode, and must never receive live keys.  
HTTP MCP: `GET /mcp/manifest`, `POST /mcp/call`. Guide: [docs/grokbot/README.md](docs/grokbot/README.md).

## Live opt-in

```
PULSAR_LIVE=true
PULSAR_LIVE_CONFIRM=I_UNDERSTAND_THE_RISK
```

Both required. IBKR live stays false in v1 regardless.

## Docs

- [DISCLAIMER.md](DISCLAIMER.md)
- [docs/NAMING.md](docs/NAMING.md) — RSI = Relative Strength Index only; Recursive Self-Improvement is always spelled out
- [docs/prd.md](docs/prd.md)
- [docs/agent-spec.md](docs/agent-spec.md)
- [docs/safety.md](docs/safety.md)
- [docs/eval-plan.md](docs/eval-plan.md)
- [docs/pm-log/DIARY.md](docs/pm-log/DIARY.md) — product decision diary for interview review

## Tests

```bash
pytest
```

CI runs the same suite, including agent permission evals.
