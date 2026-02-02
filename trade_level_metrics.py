#!/usr/bin/env python3
"""
交易级别指标计算 - 完全规避出入金影响

核心思想：
1. 不依赖账户价值，只分析每笔交易的表现
2. 每笔交易的收益率 = PnL / Position Value
3. 基于交易级别计算 Sharpe Ratio 和 Drawdown
4. 完全不受出入金影响！
"""

import math
from typing import List, Dict
from datetime import datetime
from decimal import Decimal


class TradeLevelMetrics:
    """
    交易级别指标计算器
    完全不依赖账户价值，只分析交易本身
    """

    def __init__(self, fills: List[Dict]):
        self.fills = sorted(fills, key=lambda x: x.get('time', 0))

    def calculate_trade_level_sharpe_ratio(self, risk_free_rate: float = 0.03) -> Dict:
        """
        计算交易级别的 Sharpe Ratio

        方法：
        1. 对每笔有PnL的交易，计算其收益率 = PnL / Position_Value
        2. 收益率序列的均值和标准差
        3. Sharpe = (mean_return - rf) / std_dev

        优势：
        - 完全不需要账户价值
        - 不受出入金影响
        - 评估交易策略本身的表现

        Returns:
            {
                "sharpe_ratio": float,
                "annualized_sharpe": float,
                "mean_return_per_trade": float,
                "std_dev": float,
                "total_trades": int
            }
        """
        trade_returns = []

        for fill in self.fills:
            closed_pnl = float(fill.get('closedPnl', 0))

            # 只分析平仓交易（有PnL的交易）
            if closed_pnl == 0:
                continue

            # 计算仓位价值
            # Position Value = Price * Size
            px = float(fill.get('px', 0))
            sz = abs(float(fill.get('sz', 0)))
            position_value = px * sz

            if position_value > 0:
                # 交易收益率 = PnL / Position_Value
                trade_return = closed_pnl / position_value
                trade_returns.append(trade_return)

        if len(trade_returns) < 2:
            return {
                "sharpe_ratio": 0,
                "annualized_sharpe": 0,
                "mean_return_per_trade": 0,
                "std_dev": 0,
                "total_trades": 0
            }

        # 计算统计量
        mean_return = sum(trade_returns) / len(trade_returns)
        variance = sum((r - mean_return) ** 2 for r in trade_returns) / (len(trade_returns) - 1)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return {
                "sharpe_ratio": 0,
                "annualized_sharpe": 0,
                "mean_return_per_trade": mean_return,
                "std_dev": 0,
                "total_trades": len(trade_returns)
            }

        # 每笔交易的无风险收益率（假设持仓1.78天）
        avg_hold_days = 1.78  # 从之前计算得出
        trade_rf_rate = (1 + risk_free_rate) ** (avg_hold_days / 365) - 1

        # Sharpe Ratio（每笔交易）
        sharpe_per_trade = (mean_return - trade_rf_rate) / std_dev

        # 年化：假设每年交易N次
        # 从数据推算：835笔有PnL交易，时间跨度约X天
        first_trade_time = next((f['time'] for f in self.fills
                                if float(f.get('closedPnl', 0)) != 0), 0)
        last_trade_time = next((f['time'] for f in reversed(self.fills)
                               if float(f.get('closedPnl', 0)) != 0), 0)

        if first_trade_time and last_trade_time:
            days = (last_trade_time - first_trade_time) / 1000 / 86400
            trades_per_year = len(trade_returns) / days * 365 if days > 0 else 252
        else:
            trades_per_year = 252  # 默认假设每年252个交易日

        # 年化 Sharpe = 每笔交易 Sharpe * sqrt(年交易次数)
        annualized_sharpe = sharpe_per_trade * math.sqrt(trades_per_year)

        return {
            "sharpe_ratio": sharpe_per_trade,
            "annualized_sharpe": annualized_sharpe,
            "mean_return_per_trade": mean_return,
            "std_dev": std_dev,
            "total_trades": len(trade_returns),
            "trades_per_year": trades_per_year
        }

    def calculate_trade_level_max_drawdown(self) -> Dict:
        """
        计算交易级别的最大回撤

        方法：
        1. 构建累计收益率序列（不是累计PnL）
        2. 每笔交易后，累计收益率 *= (1 + 当前交易收益率)
        3. 基于累计收益率计算回撤

        优势：
        - 不需要初始资金
        - 不受出入金影响
        - 反映策略本身的回撤风险

        Returns:
            {
                "max_drawdown_pct": float,
                "peak_return": float,
                "trough_return": float,
                "peak_trade_index": int,
                "trough_trade_index": int
            }
        """
        trade_returns = []
        trade_indices = []  # 记录交易序号

        trade_count = 0
        for fill in self.fills:
            closed_pnl = float(fill.get('closedPnl', 0))

            if closed_pnl == 0:
                continue

            px = float(fill.get('px', 0))
            sz = abs(float(fill.get('sz', 0)))
            position_value = px * sz

            if position_value > 0:
                trade_return = closed_pnl / position_value
                trade_returns.append(trade_return)
                trade_indices.append(trade_count)
                trade_count += 1

        if len(trade_returns) < 2:
            return {
                "max_drawdown_pct": 0,
                "peak_return": 0,
                "trough_return": 0,
                "peak_trade_index": 0,
                "trough_trade_index": 0
            }

        # 构建累计收益率序列
        cumulative_returns = []
        cumulative = 1.0  # 从1.0开始（代表100%本金）

        for ret in trade_returns:
            cumulative *= (1 + ret)
            cumulative_returns.append(cumulative)

        # 计算最大回撤
        peak = cumulative_returns[0]
        max_drawdown = 0
        peak_idx = 0
        trough_value = peak
        trough_idx = 0

        for i, value in enumerate(cumulative_returns):
            if value > peak:
                peak = value
                peak_idx = i

            drawdown = (peak - value) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                trough_value = value
                trough_idx = i

        return {
            "max_drawdown_pct": max_drawdown,
            "peak_return": (peak - 1) * 100,  # 转换为百分比
            "trough_return": (trough_value - 1) * 100,
            "peak_trade_index": peak_idx,
            "trough_trade_index": trough_idx,
            "total_trades": len(trade_returns)
        }

    def calculate_trade_statistics(self) -> Dict:
        """
        计算详细的交易统计

        Returns:
            丰富的交易级别统计信息
        """
        trade_pnls = []
        trade_returns = []
        winning_returns = []
        losing_returns = []
        position_sizes = []

        for fill in self.fills:
            closed_pnl = float(fill.get('closedPnl', 0))

            if closed_pnl == 0:
                continue

            px = float(fill.get('px', 0))
            sz = abs(float(fill.get('sz', 0)))
            position_value = px * sz

            if position_value > 0:
                trade_return = closed_pnl / position_value
                trade_pnls.append(closed_pnl)
                trade_returns.append(trade_return)
                position_sizes.append(position_value)

                if closed_pnl > 0:
                    winning_returns.append(trade_return)
                else:
                    losing_returns.append(trade_return)

        if not trade_returns:
            return {}

        # 基础统计
        stats = {
            "total_trades": len(trade_returns),
            "winning_trades": len(winning_returns),
            "losing_trades": len(losing_returns),
            "win_rate": len(winning_returns) / len(trade_returns) * 100,

            # 平均收益率
            "avg_return_per_trade": sum(trade_returns) / len(trade_returns) * 100,
            "avg_winning_return": sum(winning_returns) / len(winning_returns) * 100 if winning_returns else 0,
            "avg_losing_return": sum(losing_returns) / len(losing_returns) * 100 if losing_returns else 0,

            # 最大/最小单笔收益率
            "max_return": max(trade_returns) * 100,
            "min_return": min(trade_returns) * 100,

            # 收益率标准差
            "return_std_dev": (sum((r - sum(trade_returns)/len(trade_returns)) ** 2
                                  for r in trade_returns) / (len(trade_returns) - 1)) ** 0.5 * 100,

            # 平均仓位大小
            "avg_position_size": sum(position_sizes) / len(position_sizes),

            # Profit Factor（基于PnL）
            "profit_factor": sum(abs(p) for p in trade_pnls if p > 0) /
                            sum(abs(p) for p in trade_pnls if p < 0) if any(p < 0 for p in trade_pnls) else 0,

            # Expectancy（每笔交易的期望收益率）
            "expectancy": sum(trade_returns) / len(trade_returns) * 100
        }

        return stats

    def generate_report(self) -> str:
        """生成完整的交易级别分析报告"""

        sharpe = self.calculate_trade_level_sharpe_ratio()
        drawdown = self.calculate_trade_level_max_drawdown()
        stats = self.calculate_trade_statistics()

        report = []
        report.append("=" * 70)
        report.append("交易级别指标分析报告")
        report.append("✅ 不受出入金影响的准确指标")
        report.append("=" * 70)

        # 1. Sharpe Ratio
        report.append("\n📊 1. SHARPE RATIO (交易级别)")
        report.append("-" * 70)
        report.append(f"  每笔交易 Sharpe: {sharpe['sharpe_ratio']:.4f}")
        report.append(f"  年化 Sharpe: {sharpe['annualized_sharpe']:.4f}")
        report.append(f"  平均每笔收益率: {sharpe['mean_return_per_trade']:.4%}")
        report.append(f"  收益率标准差: {sharpe['std_dev']:.4%}")
        report.append(f"  分析交易数: {sharpe['total_trades']}")
        report.append(f"  推算年交易次数: {sharpe.get('trades_per_year', 0):.0f}")

        # 解读
        if sharpe['annualized_sharpe'] > 1:
            interpretation = "✅ 优秀的风险调整收益"
        elif sharpe['annualized_sharpe'] > 0:
            interpretation = "⚠️  正收益但风险较高"
        else:
            interpretation = "❌ 负的风险调整收益"
        report.append(f"  解读: {interpretation}")

        # 2. Max Drawdown
        report.append("\n📉 2. MAX DRAWDOWN (交易级别)")
        report.append("-" * 70)
        report.append(f"  最大回撤: {drawdown['max_drawdown_pct']:.2f}%")
        report.append(f"  峰值累计收益: {drawdown['peak_return']:.2f}%")
        report.append(f"  谷底累计收益: {drawdown['trough_return']:.2f}%")
        report.append(f"  峰值位置: 第 {drawdown['peak_trade_index']} 笔交易")
        report.append(f"  谷底位置: 第 {drawdown['trough_trade_index']} 笔交易")

        # 3. 交易统计
        report.append("\n📈 3. 交易统计 (交易级别)")
        report.append("-" * 70)
        report.append(f"  总交易数: {stats['total_trades']}")
        report.append(f"  胜率: {stats['win_rate']:.2f}%")
        report.append(f"  平均每笔收益率: {stats['avg_return_per_trade']:.4f}%")
        report.append(f"  平均盈利交易收益率: {stats['avg_winning_return']:.4f}%")
        report.append(f"  平均亏损交易收益率: {stats['avg_losing_return']:.4f}%")
        report.append(f"  收益率标准差: {stats['return_std_dev']:.4f}%")
        report.append(f"  最大单笔收益率: {stats['max_return']:.4f}%")
        report.append(f"  最小单笔收益率: {stats['min_return']:.4f}%")
        report.append(f"  期望值: {stats['expectancy']:.4f}%")
        report.append(f"  Profit Factor: {stats['profit_factor']:.4f}")

        # 4. 对比说明
        report.append("\n" + "=" * 70)
        report.append("✅ 优势说明")
        report.append("=" * 70)
        report.append("1. ✅ 完全不依赖账户价值")
        report.append("2. ✅ 不受出入金影响")
        report.append("3. ✅ 评估交易策略本身的表现")
        report.append("4. ✅ 适用于所有杠杆交易场景")
        report.append("5. ✅ 可横向对比不同策略")

        report.append("\n💡 解读建议")
        report.append("=" * 70)
        report.append("- 年化 Sharpe > 1: 优秀策略")
        report.append("- 年化 Sharpe > 0.5: 可接受")
        report.append("- 年化 Sharpe < 0: 策略需要改进")
        report.append("- Max Drawdown < 20%: 风险可控")
        report.append("- Max Drawdown > 50%: 风险较高")
        report.append("- 期望值 > 0: 策略具有正期望")

        return "\n".join(report)


def compare_with_account_level(fills, account_value):
    """对比交易级别和账户级别的指标差异"""

    trade_metrics = TradeLevelMetrics(fills)

    print("=" * 70)
    print("交易级别 vs 账户级别指标对比")
    print("=" * 70)

    # 交易级别
    trade_sharpe = trade_metrics.calculate_trade_level_sharpe_ratio()
    trade_dd = trade_metrics.calculate_trade_level_max_drawdown()

    # 账户级别（简化计算）
    from apex_fork import ApexCalculator
    calculator = ApexCalculator()

    historical_pnl = calculator._build_historical_pnl_from_fills(fills)
    account_sharpe = calculator._calculate_simple_sharpe_ratio(historical_pnl)
    account_dd = calculator._calculate_max_drawdown_from_pnl(historical_pnl, account_value)

    print("\n📊 Sharpe Ratio 对比:")
    print(f"  交易级别 (年化): {trade_sharpe['annualized_sharpe']:.4f} ✅ 不受出入金影响")
    print(f"  账户级别 (原算法): {account_sharpe:.4f} ⚠️  受出入金影响")

    print("\n📉 Max Drawdown 对比:")
    print(f"  交易级别: {trade_dd['max_drawdown_pct']:.2f}% ✅ 不受出入金影响")
    print(f"  账户级别: {account_dd:.2f}% ⚠️  受出入金影响")

    print("\n💡 建议:")
    print("  推荐使用【交易级别】指标，因为：")
    print("  1. 完全不受出入金影响")
    print("  2. 反映策略本质表现")
    print("  3. 可跨账户、跨时期对比")


if __name__ == '__main__':
    from apex_fork import ApexCalculator

    calculator = ApexCalculator()
    user_address = '0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf'

    user_data = calculator.get_user_data(user_address, force_refresh=False)
    fills = user_data.get('fills', [])
    margin_summary = user_data.get('marginSummary', {})
    account_value = float(margin_summary.get('accountValue', 0))

    # 生成交易级别报告
    metrics = TradeLevelMetrics(fills)
    report = metrics.generate_report()
    print(report)

    # 对比分析
    print("\n\n")
    compare_with_account_level(fills, account_value)
