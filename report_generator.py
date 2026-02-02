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

    from apex_fork import ApexCalculator
    calculator = ApexCalculator()
    trade_sharpe = calculator.calculate_trade_level_sharpe_ratio(fills)
    trade_dd = calculator.calculate_trade_level_max_drawdown(fills)
    account_sharpe = results.get('sharpe_ratio', 0)
    account_dd = results.get('max_drawdown', 0)

    # 生成 Markdown 内容
    md_content = f"""# 交易分析报告

**分析时间**: {results.get('analysis_timestamp', 'N/A')}
**用户地址**: `{user_address}`
**数据来源**: Hyperliquid API

---

## 📈 核心指标（交易级别 - 推荐使用）

> ✅ 这些指标完全不受出入金影响，准确反映策略真实表现

### Sharpe Ratio（风险调整收益）

| 指标 | 数值 | 说明 |
|------|------|------|
| 年化 Sharpe Ratio | **{trade_sharpe['annualized_sharpe']:.2f}** | {'✅ 优秀' if trade_sharpe['annualized_sharpe'] > 1 else '⚠️ 偏低'} |
| 每笔交易 Sharpe | {trade_sharpe['sharpe_ratio']:.4f} | 单笔交易风险调整收益 |
| 平均每笔收益率 | {trade_sharpe['mean_return_per_trade']:.4%} | 策略期望值 |
| 收益率标准差 | {trade_sharpe['std_dev']:.4%} | 波动性指标 |
| 分析交易数 | {trade_sharpe['total_trades']} | 样本数量 |

**评级**: {'✅ 优秀的风险调整收益' if trade_sharpe['annualized_sharpe'] > 1 else '⚠️ 正收益但风险较高' if trade_sharpe['annualized_sharpe'] > 0 else '❌ 负的风险调整收益'}

### Max Drawdown（最大回撤）

| 指标 | 数值 | 说明 |
|------|------|------|
| 最大回撤 | **{trade_dd['max_drawdown_pct']:.2f}%** | {'🔴 高风险' if trade_dd['max_drawdown_pct'] > 50 else '🟡 中等风险' if trade_dd['max_drawdown_pct'] > 20 else '🟢 低风险'} |
| 峰值累计收益 | {trade_dd['peak_return']:.2f}% | 历史最高点 |
| 谷底累计收益 | {trade_dd['trough_return']:.2f}% | 回撤最低点 |

**风险等级**: {'🔴 高风险' if trade_dd['max_drawdown_pct'] > 50 else '🟡 中等风险' if trade_dd['max_drawdown_pct'] > 20 else '🟢 低风险'}

### 交易统计

| 指标 | 数值 |
|------|------|
| Profit Factor | {results.get('profit_factor', 0):.4f} |
| Win Rate | {win_rate_data.get('winRate', 0):.2f}% |
| Direction Bias | {win_rate_data.get('bias', 0):.2f}% |
| Total Trades | {win_rate_data.get('totalTrades', 0)} |
| Avg Hold Time | {hold_time_stats.get('allTimeAverage', 0):.2f} 天 |

---

## ⚠️ 对比参考（账户级别 - 受出入金影响）

> ⚠️ 以下指标受出入金影响，仅供参考对比

| 指标 | 账户级别 | 交易级别 | 差异倍数 |
|------|----------|----------|----------|
| Sharpe Ratio | {account_sharpe:.4f} | {trade_sharpe['annualized_sharpe']:.2f} | {abs(trade_sharpe['annualized_sharpe'] / account_sharpe):.0f}x |
| Max Drawdown | {account_dd:.2f}% | {trade_dd['max_drawdown_pct']:.2f}% | - |

**为什么推荐交易级别指标？**

1. ✅ **完全不依赖账户价值** - 只基于交易本身的收益率
2. ✅ **不受出入金影响** - 无需知道存取款记录
3. ✅ **反映策略真实表现** - 纯粹的策略质量评估

---

## 💰 账户信息

| 项目 | 数值 |
|------|------|
| 账户价值 | ${data_summary.get('account_value', 0):,.2f} |
| 保证金使用 | ${data_summary.get('total_margin_used', 0):,.2f} |
| 当前持仓 | {position_analysis.get('total_positions', 0)} |
| 未实现盈亏 | ${position_analysis.get('total_unrealized_pnl', 0):,.2f} |

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
    if trade_sharpe['annualized_sharpe'] > 1:
        advantages.append(f"- **优秀的风险调整收益** (Sharpe Ratio = {trade_sharpe['annualized_sharpe']:.2f} > 1.0)")
    if trade_sharpe['mean_return_per_trade'] > 0:
        advantages.append(f"- **正期望策略** (每笔平均收益 = {trade_sharpe['mean_return_per_trade']:.4%})")
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
每笔交易收益率 = closedPnL / position_value
Sharpe Ratio = (平均收益率 - 无风险利率) / 收益率标准差
Max Drawdown = 基于累计收益率序列计算
```

**优势**:
- 不需要账户初始资金信息
- 不受存取款操作影响
- 可跨账户、跨时期对比
- 反映策略本质表现

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

    from apex_fork import ApexCalculator
    calculator = ApexCalculator()
    trade_sharpe = calculator.calculate_trade_level_sharpe_ratio(fills)
    trade_dd = calculator.calculate_trade_level_max_drawdown(fills)

    summary = f"""
📊 交易分析摘要
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 核心指标（交易级别）
  • Sharpe Ratio: {trade_sharpe['annualized_sharpe']:.2f}
  • Max Drawdown: {trade_dd['max_drawdown_pct']:.2f}%
  • Profit Factor: {results.get('profit_factor', 0):.4f}
  • Win Rate: {results.get('win_rate', {}).get('winRate', 0):.2f}%

🎯 评级
  • 风险调整收益: {'✅ 优秀' if trade_sharpe['annualized_sharpe'] > 1 else '⚠️ 偏低'}
  • 风险等级: {'🔴 高风险' if trade_dd['max_drawdown_pct'] > 50 else '🟡 中等' if trade_dd['max_drawdown_pct'] > 20 else '🟢 低风险'}
  • 盈利能力: {'✅ 盈利' if results.get('profit_factor', 0) > 1 else '❌ 亏损'}
"""

    return summary
