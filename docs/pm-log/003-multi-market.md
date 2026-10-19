# PM 学习记录 003 — 同一 Agent，不同 MarketPort

**已拍：** BTC 现货是实盘主线；IBKR 美股+MES 从 M1 就有纸交易适配。期货与现货限额隔离。

**冲突：** Dogfood 想要 IBKR 深度，OSS 用户可能没有 TWS。  
**决策：** 合成数据让 clone 用户不装 TWS 也能看 SPY/MES 脆弱性检查；文档写明 Binance-only 足够演示。

**复盘题：** 因子只在 BTC 美、在 SPY 崩，算产品缺陷还是市场差异？v1 标 `fragile_cross_market` 并拒绝晋升实盘。
