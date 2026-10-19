# Agent Spec v0.1

## Roles

| Agent | May | Must not |
| --- | --- | --- |
| Researcher | 列出 RSI 族、提出假设 | 下单、改限额、改晋升状态 |
| Validator | 跑 gauntlet、写失败原因 | 下单、改限额 |
| Operator | 为 `paper` 状态因子下纸交易单 | 晋升因子、打开 live |
| RiskOfficer | 只读账本、触发 kill switch | 发明新限额、下单 |

Grok Bot 是这四个角色的云端工人，不是第五套大脑。

## Tools

Chat 可调用：`overview`, `list_factors`, `why_not_promoted`, `start_research`, `risk_status`, `kill`, `paper_trade`（说明性）。

MCP 可调用上述只读/研究工具。禁止：`place_live_order`, `enable_live`, `set_limits`, `ibkr_live`。

## Memory

失败假设写入 `memories`。DecisionPort 在新假设上可读取名称/描述，避免重复噪声。

## Irreversible actions

- 主网下单（本机、双 flag、已晋升）。
- Kill switch（可复位，但是审计事件）。
- 改限额：v1 只能改环境变量并重启，不走聊天。

## Human boundary

改 live 开关、改限额、IBKR 真账户：人。  
研究循环、纸成交、停机：Agent。
