# PM 学习记录 004 — Grok Bot 共享云电脑不是保险箱

**已拍：** 研究/评测/哨兵可以上云；execution 任务禁止远程；MCP 无 live 工具；密钥分级写进安全案。

**为什么：** Grok Bot 账号下所有 Bot 共享磁盘与凭证。一个「帮我看看持仓」的 Bot 也能读到你放上去的 IBKR 密码。

**复盘题：** 以后若把 API 部署到公网给 Bot 调，token 必须默认 paper scope。
