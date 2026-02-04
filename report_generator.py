#!/usr/bin/env python3
"""
报告生成器 - 支持多种格式输出
"""

from typing import Dict
from datetime import datetime


def format_profit_factor(pf: float) -> str:
    """格式化 Profit Factor 显示

    Args:
        pf: profit_factor 数值

    Returns:
        str: 格式化后的字符串，>= 1000 显示为 "1000+"
    """
    if pf >= 1000:
        return "1000+"
    return f"{pf:.4f}"


def format_hold_time(days: float) -> str:
    """智能格式化持仓时间

    Args:
        days: 天数

    Returns:
        格式化的字符串（自动选择天/小时/分钟）
    """
    if days == 0:
        return "0 天"
    elif days >= 1:
        return f"{days:.2f} 天"
    elif days >= 1/24:  # >= 1 小时
        hours = days * 24
        return f"{hours:.2f} 小时"
    else:  # < 1 小时
        minutes = days * 24 * 60
        return f"{minutes:.2f} 分钟"


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

    # 使用基于交易收益率的指标
    sharpe_on_trades = results.get('sharpe_on_trades', {})
    return_metrics_on_trades = results.get('return_metrics_on_trades', {})

    # 获取并格式化 profit_factor
    profit_factor = results.get('profit_factor', 0)
    pf_display = format_profit_factor(profit_factor)

    # 生成 Markdown 内容
    md_content = f"""# 交易分析报告

**分析时间**: {results.get('analysis_timestamp', 'N/A')}
**用户地址**: `{user_address}`
**数据来源**: Hyperliquid API

---

"""

    # 添加多周期ROE部分
    def get_roe_rating(roe_percent: float) -> str:
        """获取ROE评级"""
        if roe_percent >= 10:
            return "🔥 极佳"
        elif roe_percent >= 5:
            return "✅ 优秀"
        elif roe_percent >= 0:
            return "📈 盈利"
        elif roe_percent >= -5:
            return "⚠️ 小幅亏损"
        else:
            return "📉 较大亏损"

    # 获取所有周期的ROE数据
    roe_24h = results.get('roe_24h', {})
    roe_7d = results.get('roe_7d', {})
    roe_30d = results.get('roe_30d', {})
    roe_all = results.get('roe_all', {})

    # 检查是否有任何有效的ROE数据
    has_valid_roe = any([
        roe_24h.get('is_valid', False),
        roe_7d.get('is_valid', False),
        roe_30d.get('is_valid', False),
        roe_all.get('is_valid', False)
    ])

    if has_valid_roe:
        md_content += """## 📊 多周期ROE指标

| 时间周期 | ROE | 起始权益 | 当前权益 | PNL | 评级 |
|---------|-----|----------|----------|-----|------|
"""

        # 添加各个周期的数据
        for roe_data, label in [(roe_24h, '24小时'), (roe_7d, '7天'), (roe_30d, '30天'), (roe_all, '历史总计')]:
            if roe_data.get('is_valid', False):
                roe_percent = roe_data.get('roe_percent', 0)
                start_equity = roe_data.get('start_equity', 0)
                current_equity = roe_data.get('current_equity', 0)
                pnl = roe_data.get('pnl', 0)
                rating = get_roe_rating(roe_percent)

                md_content += f"| **{label}** | **{roe_percent:+.2f}%** | ${start_equity:,.2f} | ${current_equity:,.2f} | {'+' if pnl >= 0 else ''}${pnl:,.2f} | {rating} |\n"
            else:
                error_msg = roe_data.get('error_message', '计算失败')
                md_content += f"| **{label}** | ❌ | - | - | - | {error_msg[:20]} |\n"

        md_content += "\n"

        # 添加警告信息（如果有）
        warnings = []
        for roe_data, label in [(roe_24h, '24小时'), (roe_7d, '7天'), (roe_30d, '30天')]:
            if roe_data.get('is_valid', False) and not roe_data.get('is_sufficient_history', True):
                period_hours = roe_data.get('period_hours', 0)
                warnings.append(f"- {label}: 实际历史仅 {period_hours:.1f} 小时")

        if warnings:
            md_content += "> ⚠️ **注意**: 部分周期历史数据不足，ROE基于实际时长计算\n\n"
            for warning in warnings:
                md_content += f"> {warning}\n"
            md_content += "\n"

        # 获取更新时间（使用24h的时间）
        try:
            end_time = roe_24h.get('end_time', 'N/A')
            end_dt = datetime.fromisoformat(end_time)
            end_time_str = end_dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            end_time_str = 'N/A'

        md_content += f"""
**更新时间**: {end_time_str}

**计算公式**:
```
ROE (%) = (周期累计PNL / 起始权益) × 100
```

**指标说明**:
- **24小时ROE**: 最近一天的资金使用效率
- **7天ROE**: 最近一周的整体表现
- **30天ROE**: 最近一个月的长期表现
- **历史总ROE**: 账户开户以来的总体收益率

**优势**:
- ✅ ROE反映资金使用效率，考虑账户规模
- ✅ 多周期对比帮助识别表现趋势
- ✅ 适合评估不同时间尺度的交易策略

---

"""
    else:
        md_content += """## 📊 多周期ROE指标

> ❌ **ROE计算失败**: 无法获取ROE数据

---

"""

    md_content += """## 📈 核心指标（基于单笔交易收益率）

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

"""

    # 添加优势
    advantages = []
    if sharpe_on_trades.get('annualized_sharpe', 0) > 1:
        advantages.append(f"- **优秀的风险调整收益** (Sharpe Ratio = {sharpe_on_trades['annualized_sharpe']:.2f} > 1.0)")
    if sharpe_on_trades.get('mean_return', 0) > 0:
        advantages.append(f"- **正期望策略** (每笔平均收益 = {sharpe_on_trades['mean_return']:.2%})")

    # Profit Factor 评估
    if profit_factor >= 1000:
        advantages.append(f"- **极优秀盈利策略** (Profit Factor = 1000+，无亏损交易)")
    elif profit_factor > 1:
        advantages.append(f"- **盈利策略** (Profit Factor = {profit_factor:.2f} > 1.0)")

    if advantages:
        md_content += "\n".join(advantages)
    else:
        md_content += "- 暂无明显优势"

    md_content += "\n\n### ⚠️ 风险\n\n"

    # 添加风险
    risks = []
    if win_rate_data.get('winRate', 0) < 50:
        risks.append(f"- **胜率偏低** (Win Rate = {win_rate_data.get('winRate', 0):.2f}%)")

    sharpe_ratio = sharpe_on_trades.get('annualized_sharpe', 0)
    if sharpe_ratio < 1:
        risks.append(f"- **风险调整收益偏低** (Sharpe Ratio = {sharpe_ratio:.2f} < 1.0)")

    if risks:
        md_content += "\n".join(risks)
    else:
        md_content += "- 风险可控"

    md_content += "\n\n### 💡 改进建议\n\n"

    # 添加建议
    suggestions = []
    if win_rate_data.get('winRate', 0) < 45:
        suggestions.append("- 优化入场时机，提高胜率")
    if sharpe_ratio < 1:
        suggestions.append("- 优化风险管理，降低收益波动")
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

    # 使用基于交易收益率的指标
    sharpe_on_trades = results.get('sharpe_on_trades', {})

    # 获取并格式化 profit_factor
    profit_factor = results.get('profit_factor', 0.0)
    pf_display = format_profit_factor(profit_factor)

    # 判断盈利能力
    if profit_factor >= 1000:
        profit_status = '✅ 极优秀（无亏损）'
    elif profit_factor > 1:
        profit_status = '✅ 盈利'
    else:
        profit_status = '❌ 亏损'

    summary = f"""
📊 交易分析摘要
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 核心指标
  • Sharpe Ratio: {sharpe_on_trades.get('annualized_sharpe', 0):.2f}
  • Profit Factor: {pf_display}
  • Win Rate: {results.get('win_rate', {}).get('winRate', 0):.2f}%

🎯 评级
  • 风险调整收益: {'✅ 优秀' if sharpe_on_trades.get('annualized_sharpe', 0) > 1 else '⚠️ 偏低'}
  • 盈利能力: {profit_status}
"""

    return summary
