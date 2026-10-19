# PM 学习记录 000 — Jev / System One（M0 开工课）

**此刻要拍的板：** 高频判断走 DecisionPort，即使还没有 TypeSafe Key。  
**工件：** `src/pulsar/ports/decision.py`、本文件。  
**复盘问题：** 有没有判断仍在用「让模型写一段话」？

## System One vs System Two

- System Two（生成式）：写因子描述、写复盘、提出新假设。开放文本。
- System One（Jev 形）：封闭选项、要概率、要便宜且稳定。`choice` / `score` / `noul`。

门控阈值和下单是 **code-only**。Jev 可以建议停机，代码在突破限额时必须停机。

## 作业：10 个决策点

| # | 决策 | 归类 | 实现 |
| --- | --- | --- | --- |
| 1 | 假设是否仍属 RSI 族 | jev (`noul`) | DecisionPort |
| 2 | 相对种子库的新颖性 | jev (`score`) | DecisionPort |
| 3 | 送去 gauntlet / 进记忆 / 丢掉 | jev (`choice`) | DecisionPort |
| 4 | 回测是否过拟合到该拒绝 | jev (`noul`) 顾问 + code | gates.py 为硬门 |
| 5 | 是否晋升纸交易 | jev 顾问 + code | PromotionMachine |
| 6 | 跨市场是否脆弱 | code-only | `fragility()` |
| 7 | 是否该触发 kill switch | jev 顾问 + code | RiskOfficer |
| 8 | 聊天下一步调哪个工具 | jev (`choice`) | ChatRouter |
| 9 | 写哪一个 RSI 变体 | llm | Researcher 文本；v1 实际从种子库选 |
| 10 | 以什么价格下多少张单 | code-only | Operator + limits |

拍板记录：先 rules 后端，接口与 Jev 同构；`PULSAR_DECISION_BACKEND=jev|llm|rules`。
