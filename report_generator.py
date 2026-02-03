#!/usr/bin/env python3
"""
报告生成器 - 支持多种格式输出
"""

from typing import Dict
from datetime import datetime


def generate_markdown_report(results: Dict, user_address: str, filename: str = "trading_report.md") -> str:
    """
    生成 Markdown 格式的交易分析报告

    Args:
        results: 分析结果字典
        user_address: 用户地址
        filename: 输出文件名

    Returns:
        str: 保存结果消息
    """
    if "error" in results:
        return f"# 分析报告\n\n❌ 分析失败: {results['error']}"

    # 提取数据
    win_rate_data = results.get('win_rate', {})
    hold_time_stats = results.get('hold_time_stats', {})
    data_summary = results.get('data_summary', {})
    position_analysis = results.get('position_analysis', {})

    # 获取交易级别指标
    fills = results.get('_raw_fills', [])
    if not fills:
        return "# 分析报告\n\n❌ 无法获取交易数据"

    # 使用基于真实本金的指标
    sharpe_on_capital = results.get('sharpe_on_capital', {})
    trade_dd = results.get('max_drawdown_on_capital', {
        "max_drawdown_pct": 0,
        "peak_return": 0,
        "trough_return": 0,
        "total_trades": 0
    })

    # 生成 Markdown 内容
    md_content = f"""# 交易分析报告

**分析时间**: {results.get('analysis_timestamp', 'N/A')}
**用户地址**: `{user_address}`
**数据来源**: Hyperliquid API

---

## 📈 核心指标（交易级别 - 推荐使用）

> ✅ 这些指标完全不受出入金影响，准确反映策略真实表现

### Sharpe Ratio（风险调整收益）- 基于真实本金

| 指标 | 数值 | 说明 |
|------|------|------|
| 年化 Sharpe Ratio | **{sharpe_on_capital.get('annualized_sharpe', 0):.2f}** | {'✅ 优秀' if sharpe_on_capital.get('annualized_sharpe', 0) > 1 else '⚠️ 偏低'} |
| 每笔交易 Sharpe | {sharpe_on_capital.get('sharpe_ratio', 0):.4f} | 单笔交易风险调整收益 |
| 平均每笔收益率 | {sharpe_on_capital.get('mean_return_per_trade', 0):.4%} | 相对真实本金 |
| 收益率标准差 | {sharpe_on_capital.get('std_dev', 0):.4%} | 波动性指标 |
| 分析交易数 | {sharpe_on_capital.get('total_trades', 0)} | 样本数量 |

**计算方法**: 每笔收益率 = closedPnL / 真实本金

**优势**:
- ✅ 不受杠杆影响，真实反映风险收益比
- ✅ 与累计收益率计算逻辑一致
- ✅ 反映真实的资金使用效率

**评级**: {'✅ 优秀的风险调整收益' if sharpe_on_capital.get('annualized_sharpe', 0) > 1 else '⚠️ 正收益但风险较高' if sharpe_on_capital.get('annualized_sharpe', 0) > 0 else '❌ 负的风险调整收益'}

### Max Drawdown（最大回撤）

| 指标 | 数值 | 说明 |
|------|------|------|
| 最大回撤 | **{trade_dd['max_drawdown_pct']:.2f}%** | {'🔴 高风险' if trade_dd['max_drawdown_pct'] > 50 else '🟡 中等风险' if trade_dd['max_drawdown_pct'] > 20 else '🟢 低风险'} |
| 峰值累计收益 | {trade_dd['peak_return']:.2f}% | 历史最高点 |
| 峰值日期 | **{trade_dd.get('peak_date', 'N/A')}** | 峰值发生时间 |
| 谷底累计收益 | {trade_dd['trough_return']:.2f}% | 回撤最低点 |
| 谷底日期 | **{trade_dd.get('trough_date', 'N/A')}** | 谷底发生时间 |

**风险等级**: {'🔴 高风险' if trade_dd['max_drawdown_pct'] > 50 else '🟡 中等风险' if trade_dd['max_drawdown_pct'] > 20 else '🟢 低风险'}

> 📅 **回撤时间跨度**: 从 {trade_dd.get('peak_date', 'N/A')} 到 {trade_dd.get('trough_date', 'N/A')}

### 交易统计

| 指标 | 数值 |
|------|------|
| Profit Factor | {results.get('profit_factor', 0):.4f} |
| Win Rate | {win_rate_data.get('winRate', 0):.2f}% |
| Direction Bias | {win_rate_data.get('bias', 0):.2f}% |
| Total Trades | {win_rate_data.get('totalTrades', 0)} |
| Avg Hold Time | {hold_time_stats.get('allTimeAverage', 0):.2f} 天 |

---

---

## 💡 关于指标计算

### Sharpe Ratio 计算方法

**我们使用的方法**:
```
每笔交易收益率 = closedPnL / 真实本金
Sharpe Ratio = (平均收益率 - 无风险利率) / 收益率标准差
年化 Sharpe = 每笔 Sharpe × sqrt(年交易次数)
```

**为什么这样计算？**

1. ✅ **不受杠杆影响** - 真实反映风险收益比
2. ✅ **不受出入金影响** - 使用校正后的真实本金
3. ✅ **逻辑一致** - 与累计收益率计算方法一致
4. ✅ **反映资金效率** - 准确评估策略表现

**真实本金的计算**:
```
真实本金 = 充值 - 提现 + 外部转入 Spot - 外部转出
```

这个方法确保了收益率指标的准确性和可比性。

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

## 💵 本金与收益率

### 真实本金计算（算法 2: 完整版本）

| 项目 | 数值 | 说明 |
|------|------|------|
| **真实本金** | **${results.get('capital_info', {}).get('true_capital', 0):,.2f}** | 充值 - 提现 + 外部转入 - 外部转出 |
| ├─ 总充值 | ${results.get('capital_info', {}).get('total_deposits', 0):,.2f} | Deposit 操作 |
| ├─ 总提现 | -${results.get('capital_info', {}).get('total_withdrawals', 0):,.2f} | Withdraw 操作 |
| ├─ 外部转入 Spot | +${results.get('capital_info', {}).get('external_to_spot', 0):,.2f} | 别人通过 Send 转入 |
| └─ 外部转出 | -${results.get('capital_info', {}).get('external_out', 0):,.2f} | 通过 Send 转给别人 |

> ⚠️ **注意**: 已排除 Perp ↔ Spot 内部转账（不影响总资金）

### 收益率指标

| 项目 | 数值 |
|------|------|
| **累计收益率** | **{results.get('return_metrics', {}).get('cumulative_return', 0):.2f}%** |
| **年化收益率** | **{results.get('return_metrics', {}).get('annualized_return', 0):.2f}%**{' ⚠️ (交易天数<30天,仅供参考)' if results.get('return_metrics', {}).get('trading_days', 0) < 30 else ''} |
| 交易净盈利 | ${results.get('return_metrics', {}).get('net_profit_trading', 0):,.2f} (基于累计总盈亏) |
| 账户净增长 | ${results.get('return_metrics', {}).get('net_profit_account', 0):,.2f} (当前价值-本金) |
| 交易天数 | {results.get('return_metrics', {}).get('trading_days', 0):.1f} 天 |

> ℹ️ **盈亏口径说明**：
> - **交易净盈利**：基于所有成交记录的 closedPnL + 未实现盈亏，准确反映交易策略表现
> - **账户净增长**：当前账户总价值 - 真实本金，包含所有资金变动
> - **差异原因**：可能包含 funding fee（资金费率）、空投、外部转账等非交易盈亏

---

## ⏱️ 持仓时间统计

| 时间段 | 平均持仓时间 |
|--------|--------------|
| 今日 | {hold_time_stats.get('todayCount', 0):.2f} 天 |
| 近7天 | {hold_time_stats.get('last7DaysAverage', 0):.2f} 天 |
| 近30天 | {hold_time_stats.get('last30DaysAverage', 0):.2f} 天 |
| 历史平均 | {hold_time_stats.get('allTimeAverage', 0):.2f} 天 |

---

## 🎯 策略评估总结

### ✅ 优势

"""

    # 添加优势
    advantages = []
    if sharpe_on_capital.get('annualized_sharpe', 0) > 1:
        advantages.append(f"- **优秀的风险调整收益** (Sharpe Ratio = {sharpe_on_capital['annualized_sharpe']:.2f} > 1.0)")
    if sharpe_on_capital.get('mean_return_per_trade', 0) > 0:
        advantages.append(f"- **正期望策略** (每笔平均收益 = {sharpe_on_capital['mean_return_per_trade']:.4%})")
    if results.get('profit_factor', 0) > 1:
        advantages.append(f"- **盈利策略** (Profit Factor = {results.get('profit_factor', 0):.2f} > 1.0)")

    if advantages:
        md_content += "\n".join(advantages)
    else:
        md_content += "- 暂无明显优势"

    md_content += "\n\n### ⚠️ 风险\n\n"

    # 添加风险
    risks = []
    if trade_dd['max_drawdown_pct'] > 50:
        risks.append(f"- **极高回撤风险** (最大回撤 = {trade_dd['max_drawdown_pct']:.2f}%)")
    if win_rate_data.get('winRate', 0) < 50:
        risks.append(f"- **胜率偏低** (Win Rate = {win_rate_data.get('winRate', 0):.2f}%)")

    if risks:
        md_content += "\n".join(risks)
    else:
        md_content += "- 风险可控"

    md_content += "\n\n### 💡 改进建议\n\n"

    # 添加建议
    suggestions = []
    if trade_dd['max_drawdown_pct'] > 50:
        suggestions.extend([
            "- 考虑降低仓位大小",
            "- 添加更严格的止损机制"
        ])
    if win_rate_data.get('winRate', 0) < 45:
        suggestions.append("- 优化入场时机，提高胜率")
    suggestions.append("- 持续优化资金管理策略")

    md_content += "\n".join(suggestions)

    md_content += f"""

---

## 📊 数据摘要

| 项目 | 数量 |
|------|------|
| 成交记录 | {data_summary.get('total_fills', 0)} 条 |
| 当前持仓 | {data_summary.get('total_positions', 0)} 个 |
| 分析时间 | {results.get('analysis_timestamp', 'N/A')} |

---

## 📚 说明

### 关于交易级别指标

**计算方法**:
```
每笔交易收益率 = closedPnL / true_capital (真实本金)
Sharpe Ratio = (平均收益率 - 无风险利率) / 收益率标准差
Max Drawdown = 基于累计收益率序列计算
```

**优势**:
- ✅ 不受杠杆影响，真实反映风险收益比
- ✅ 不受存取款操作影响
- ✅ 与累计收益率计算逻辑一致
- ✅ 反映真实的资金使用效率
- 可跨账户、跨时期对比

### 数据来源

- **API**: Hyperliquid Official API
- **文档**: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
- **算法**: 基于 Apex Liquid Bot 改进版

---

*本报告由 Apex Fork 自动生成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

    # 保存到文件
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
        return f"✅ Markdown 报告已保存至: {filename}"
    except Exception as e:
        return f"❌ 保存报告失败: {str(e)}"


def generate_summary_text(results: Dict) -> str:
    """
    生成简洁的文本摘要

    Args:
        results: 分析结果字典

    Returns:
        str: 摘要文本
    """
    if "error" in results:
        return f"分析失败: {results['error']}"

    fills = results.get('_raw_fills', [])
    if not fills:
        return "无法获取交易数据"

    # 使用基于真实本金的指标
    sharpe_on_capital = results.get('sharpe_on_capital', {})
    trade_dd = results.get('max_drawdown_on_capital', {
        "max_drawdown_pct": 0,
        "peak_return": 0,
        "trough_return": 0,
        "total_trades": 0
    })

    summary = f"""
📊 交易分析摘要
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 核心指标（交易级别）
  • Sharpe Ratio: {sharpe_on_capital.get('annualized_sharpe', 0):.2f}
  • Max Drawdown: {trade_dd['max_drawdown_pct']:.2f}%
  • Profit Factor: {results.get('profit_factor', 0):.4f}
  • Win Rate: {results.get('win_rate', {}).get('winRate', 0):.2f}%

🎯 评级
  • 风险调整收益: {'✅ 优秀' if sharpe_on_capital.get('annualized_sharpe', 0) > 1 else '⚠️ 偏低'}
  • 风险等级: {'🔴 高风险' if trade_dd['max_drawdown_pct'] > 50 else '🟡 中等' if trade_dd['max_drawdown_pct'] > 20 else '🟢 低风险'}
  • 盈利能力: {'✅ 盈利' if results.get('profit_factor', 0) > 1 else '❌ 亏损'}
"""

    return summary
