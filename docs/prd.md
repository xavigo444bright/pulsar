# Pulsar PRD v0.1

## Problem

个人交易者无法把「研究 → 验证 → 纸交易 → 限额实盘」做成一条可审计的闭环。现成机器人要么让 LLM 直接喊单，要么只有执行没有研究治理。Pulsar 把晋升做成产品。

## User

- 超级用户：仓库作者，先跑通自己。
- 开源用户：clone 后无 key 也能演示；有 Binance testnet 可走类实盘；有 IBKR paper 可看美股/期货适配。

## Jobs to be done

1. 在 RSI 族里提出可检验因子。
2. 看清为什么一个因子没晋升。
3. 纸交易自动跑，限额外停机。
4. 用对话驱动研究，用仪表盘审计。

## Non-goals (v1)

A 股、国内期货、承诺收益、prompt 当风控、LLM 直接实盘、IBKR 实盘、把真密钥放到 Grok Bot。

## Success metrics (anti-game)

- **Clone 成功率**：无交易所 key，`pulsar seed` 能产出晋升榜和失败记忆。
- **门控诚实度**：`noise_control` 100% 不得晋升。
- **权限**：CI 里 Researcher/MCP 碰不到 live 工具。
- **安全默认**：新进程 `live_enabled=false`。
- **不**把回测 Sharpe 当北极星。对外只承诺治理闭环。

## Surfaces

- Chat：研究、解释、风控、停机。不能在对话里打开主网。
- Dashboard：多市场权益、持仓、RSI 因子榜、审计、kill switch。

## Risks

过拟合、RSI 拥挤、合成数据与真实行情差异、IBKR 接入成本、Grok Bot 共享磁盘。
