# PM 学习记录 006 — M1–M4 决策摘要

## M1 市场与纸交易

- 三个适配器同时存在，执行深度可以不同。
- Kill switch 先于 LLM 挖因子存在：没有大脑也能停机。
- DecisionPort 在下单前回答 allow，但限额是代码。

## M2 RSI 混合门控

- 种子库 + 噪声对照。
- 失败进 memory。
- 纸成交只发生在晋升之后，且走 Operator。

## M3 双表面

- 对话是主入口（工具路由也走 DecisionPort）。
- 仪表盘是监控与审计，不是第二个下单台。

## M4 开源可演示

- Docker / CI / README 60 秒。
- live 双 flag。
- IBKR 实盘保持关闭。
