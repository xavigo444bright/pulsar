# Safety case

## Defaults

- `PULSAR_LIVE=false`
- 无 `PULSAR_LIVE_CONFIRM=I_UNDERSTAND_THE_RISK` 则 `live_enabled()` 为假
- 无交易所 key 时走合成 K 线 + 本地撮合
- IBKR `supports_live() == False`
- Grok Bot MCP `scope=paper`

## Prompt is not a control

硬限制在：

1. 工具白名单（角色 + MCP FORBIDDEN）
2. `RiskOfficer.allow_order`
3. 分账本限额（spot / equity / futures 不共用一个数字）
4. Kill switch
5. 晋升状态机

DecisionPort 的 noul 只是顾问。突破 `max_drawdown` 时即使模型说「没事」也会停机。

## Grok Bot

所有 Bot 共享一台云电脑的磁盘、cookie、终端凭证。因此：

- 云上只放 paper/testnet 或根本不放密钥
- 主网与 IBKR 实盘密钥只在操作者本机
- ComputePort 拒绝 `execute` 在 `grokbot` 上运行

## Opt-in live (Binance spot only)

需要同时：

```
PULSAR_LIVE=true
PULSAR_LIVE_CONFIRM=I_UNDERSTAND_THE_RISK
```

因子仍须处于 `paper`/`live` 晋升态。v1 Operator 在 API 的 `/v1/paper/order` 永远 `live_enabled=False`。

## Audit

`audit_log`、`decisions`、`orders`、`risk_events` 可回放。
