# Eval plan

## Strategy gates (code)

相对 **同一成本模型下的 RSI(14) 均值回归基线**：

- 全样本超额 Sharpe > 0
- Holdout 超额 Sharpe > 0
- Walk-forward 多数折胜出
- 换手 < 0.6 / bar
- 回撤 < 45%
- 复杂度 ≤ 6
- 必须是 RSI 族（噪声对照必须失败）
- 第二市场（默认 SPY）Sharpe 不得低于 -0.5，否则标 fragile

基线本身只做参考，不自动实盘。

## Agent evals (CI)

见 `src/pulsar/evals/agent_evals.py` 与 `tests/test_agents_and_mcp.py`：

- Researcher 无下单工具
- Validator 无下单工具
- Operator 无晋升工具
- RiskOfficer 无 set_limits
- MCP 拒绝 live 工具
- ComputePort 拒绝远程 execution

## Product evals

- 新进程 live=false
- `/mcp/manifest` 声明 forbidden
- `noise_control` 被拒绝
