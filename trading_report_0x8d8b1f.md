# 交易分析报告

**分析时间**: 2026-02-04T14:00:53.236838
**用户地址**: `0x8d8b1f0a704544f4c8adaf55a1063be1bb656cc9`
**数据来源**: Hyperliquid API

---

## 📊 24小时ROE指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **24h ROE** | **+3.16%** | 📈 盈利 |
| 起始权益 (24h前) | $32,356.31 | 计算基准 |
| 当前权益 | $33,379.01 | 最新账户价值 |
| 24h PNL | +$1,022.69 | 期间盈亏 |
| 更新时间 | 2026-02-04 14:00:53 | 数据时间戳 |


**计算公式**:
```
24h ROE (%) = (24h累计PNL / 起始权益) × 100
           = (1022.69 / 32356.31) × 100
           = +3.16%
```

**指标说明**:
- ✅ ROE反映资金使用效率（24小时内账户权益的收益率）
- ✅ 与绝对盈亏金额不同，ROE考虑了账户规模
- ✅ 适合对比不同账户规模的交易表现

---

## 📈 核心指标（基于单笔交易收益率）

> ✅ 这些指标不依赖本金数据，准确反映交易策略表现

### Sharpe Ratio（风险调整收益）

| 指标 | 数值 | 说明 |
|------|------|------|
| 年化 Sharpe Ratio | **{sharpe_on_trades.get('annualized_sharpe', 0):.2f}** | {'✅ 优秀' if sharpe_on_trades.get('annualized_sharpe', 0) > 1 else '⚠️ 偏低'} |
| 每笔交易 Sharpe | {sharpe_on_trades.get('sharpe_ratio', 0):.4f} | 单笔交易风险调整收益 |
| 平均每笔收益率 | {sharpe_on_trades.get('mean_return', 0):.2%} | 相对持仓价值 |
| 收益率标准差 | {sharpe_on_trades.get('std_return', 0):.2%} | 波动性指标 |

**计算方法**:
```
单笔收益率 = closedPnL / (|sz| × px)
持仓价值 = |sz| × px（该笔交易的名义价值）
```

**优势**:
- ✅ 完全独立：每笔交易自给自足
- ✅ 符合金融标准：基于收益率而非绝对金额
- ✅ 不受出入金影响：与账本记录无关

**评级**: {'✅ 优秀的风险调整收益' if sharpe_on_trades.get('annualized_sharpe', 0) > 1 else '⚠️ 正收益但风险较高' if sharpe_on_trades.get('annualized_sharpe', 0) > 0 else '❌ 负的风险调整收益'}

### 交易统计

| 指标 | 数值 |
|------|------|
| Profit Factor | {pf_display} |
| Win Rate | {win_rate_data.get('winRate', 0):.2f}% |
| Direction Bias | {win_rate_data.get('bias', 0):.2f}% |
| Total Trades | {win_rate_data.get('totalTrades', 0)} |
| Avg Hold Time | {format_hold_time(hold_time_stats.get('allTimeAverage', 0))} |

### 收益率指标

| 指标 | 数值 |
|------|------|
| 平均每笔收益率 | **{sharpe_on_trades.get('mean_return', 0):.2%}** |
| 交易天数 | {return_metrics_on_trades.get('trading_days', 0):.1f} 天 |

---

## 💡 关于指标计算

### 为什么不依赖本金？

传统方法需要准确的本金数据，但实际中：
- ❌ 账本记录可能不完整（无 deposit 记录）
- ❌ 本金可能为负（转出 > 转入）
- ❌ 出入金会干扰收益率计算

### 新方法的优势

✅ **完全独立**: 每笔交易自给自足
✅ **符合金融标准**: 基于收益率而非绝对金额
✅ **不受出入金影响**: 与账本记录无关

### 计算公式

**单笔交易收益率**:
```
收益率 = closedPnL / (|sz| × px)
其中：|sz| × px = 该笔交易的持仓价值（名义价值）
```

**平均每笔收益率**:
```
平均每笔收益率 = Σ(单笔收益率) / 交易笔数
```

### 关于累计收益率

⚠️ **为什么不显示累计收益率？**

基于持仓价值的复利累计收益率**不适用于当前数据**：
- 复利假设每次交易使用全部资金
- 但实际持仓价值差异巨大（最小几十美元，最大数万美元）
- 导致计算结果与实际情况不符

我们提供更有意义的指标：
- **平均每笔收益率**: 反映平均表现
- **Sharpe Ratio**: 反映风险调整收益
- **总盈亏**: 反映绝对收益

---

## 💰 账户信息

| 项目 | 数值 |
|------|------|
| **总账户价值** | **${data_summary.get('account_value', 0):,.2f}** |
| ├─ Perp 账户价值 | ${data_summary.get('perp_account_value', 0):,.2f} |
| └─ Spot 账户价值 | ${data_summary.get('spot_account_value', 0):,.2f} |
| 保证金使用 | ${data_summary.get('total_margin_used', 0):,.2f} |
| 当前持仓 | {position_analysis.get('total_positions', 0)} |
| **累计总盈亏** | **${results.get('total_cumulative_pnl', 0):,.2f}** |
| ├─ 已实现盈亏 | ${results.get('total_realized_pnl', 0):,.2f} |
| └─ 未实现盈亏 | ${position_analysis.get('total_unrealized_pnl', 0):,.2f} |


---

## ⏱️ 持仓时间统计

| 时间段 | 平均持仓时间 |
|--------|--------------|
| 今日 | {format_hold_time(hold_time_stats.get('todayCount', 0))} |
| 近7天 | {format_hold_time(hold_time_stats.get('last7DaysAverage', 0))} |
| 近30天 | {format_hold_time(hold_time_stats.get('last30DaysAverage', 0))} |
| 历史平均 | {format_hold_time(hold_time_stats.get('allTimeAverage', 0))} |

---

## 🎯 策略评估总结

### ✅ 优势

- **优秀的风险调整收益** (Sharpe Ratio = 2.10 > 1.0)
- **正期望策略** (每笔平均收益 = 1.17%)
- **盈利策略** (Profit Factor = 2.66 > 1.0)

### ⚠️ 风险

- 风险可控

### 💡 改进建议

- 持续优化资金管理策略

---

## 📊 数据摘要

| 项目 | 数量 |
|------|------|
| 成交记录 | 1831 条 |
| 当前持仓 | 0 个 |
| 分析时间 | 2026-02-04T14:00:53.236838 |

---

## 📚 说明

### 关于基于交易收益率的指标

**计算方法**:
```
单笔收益率 = closedPnL / (|sz| × px)
Sharpe Ratio = (平均收益率 - 无风险利率) / 收益率标准差
平均每笔收益率 = Σ(单笔收益率) / 交易笔数
```

**优势**:
- ✅ 完全独立：每笔交易自给自足，不需要外部本金数据
- ✅ 符合金融标准：基于收益率而非绝对金额
- ✅ 不受出入金影响：与账本记录无关
- ✅ 可跨账户、跨时期对比

**关于累计收益率**:
- ⚠️ 不显示复利累计收益率，因为复利假设不适用于持仓价值差异巨大的交易
- ✅ 提供平均每笔收益率和Sharpe Ratio等更有意义的指标

### 数据来源

- **API**: Hyperliquid Official API
- **文档**: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
- **算法**: 基于 Apex Liquid Bot 改进版

---

*本报告由 Apex Fork 自动生成 - 2026-02-04 14:00:53*
