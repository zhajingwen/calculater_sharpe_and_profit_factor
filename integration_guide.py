"""
集成指南：如何在 apex_fork.py 中应用优化算法

展示如何替换原有的指标计算方法
"""

from apex_fork import ApexCalculator
from optimized_algorithms import OptimizedCalculator
from typing import Dict, Any


class EnhancedApexCalculator(ApexCalculator):
    """
    增强版 Apex Calculator - 集成优化算法

    新增功能：
    1. 使用优化的 Sharpe Ratio 计算（规避出入金影响）
    2. 使用优化的 Max Drawdown 计算（基于 PnL 曲线）
    3. 提供多种方法的对比结果
    4. 稳健性检验
    """

    def __init__(self, api_base_url: str = "https://api.hyperliquid.xyz"):
        super().__init__(api_base_url)
        self.optimized_calc = OptimizedCalculator()

    def analyze_user_enhanced(self, user_address: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        增强版用户分析 - 使用优化算法

        Args:
            user_address: 用户地址
            force_refresh: 是否强制刷新数据

        Returns:
            完整的分析结果（包含原始和优化两种算法的结果）
        """
        print(f"\n{'='*60}")
        print(f"开始增强分析: {user_address}")
        print(f"{'='*60}")

        # 获取用户数据
        user_data = self.get_user_data(user_address, force_refresh)

        if not user_data:
            return {"error": "无法获取用户数据"}

        # 提取数据
        fills = user_data.get('fills', [])
        asset_positions = user_data.get('assetPositions', [])
        margin_summary = user_data.get('marginSummary', {})

        # 构建历史 PnL
        historical_pnl = self._build_historical_pnl_from_fills(fills)

        # 构建账户价值历史（简化版，实际应从 API 获取）
        account_history = self._build_account_history(historical_pnl, margin_summary)

        print(f"\n数据获取完成:")
        print(f"  - 成交记录: {len(fills)} 条")
        print(f"  - 当前持仓: {len(asset_positions)} 个")
        print(f"  - 历史PnL: {len(historical_pnl)} 条")

        results = {
            "user_address": user_address,
            "data_summary": {
                "total_fills": len(fills),
                "total_positions": len(asset_positions),
                "account_value": float(margin_summary.get('accountValue', 0)),
                "total_margin_used": float(margin_summary.get('totalMarginUsed', 0))
            }
        }

        # ============================================================
        # 对比：原始算法 vs 优化算法
        # ============================================================

        print(f"\n{'='*60}")
        print("指标计算对比：原始算法 vs 优化算法")
        print(f"{'='*60}")

        # 1. Profit Factor（不受出入金影响，保持原算法）
        if fills:
            profit_factor = self.calculate_profit_factor(fills, asset_positions)
            results["profit_factor"] = profit_factor
            print(f"\n✅ Profit Factor: {profit_factor}")
            print(f"   (不受出入金影响，无需优化)")

        # 2. Sharpe Ratio - 对比
        if historical_pnl and len(historical_pnl) > 1 and account_history:
            print(f"\n{'='*60}")
            print("Sharpe Ratio 对比")
            print(f"{'='*60}")

            # 原始算法（可能受出入金影响）
            original_sharpe = self._calculate_simple_sharpe_ratio(historical_pnl)
            print(f"\n❌ 原始算法 Sharpe Ratio: {original_sharpe:.4f}")
            print(f"   问题：可能受出入金影响")

            # 优化算法（规避出入金影响）
            optimized_results = self.optimized_calc.calculate_sharpe_ratio_pnl_based(
                historical_pnl,
                account_history,
                method="median"
            )

            print(f"\n✅ 优化算法（中位数基准）:")
            print(f"   年化 Sharpe Ratio: {optimized_results['sharpe_ratio']:.4f}")
            print(f"   日 Sharpe Ratio: {optimized_results['daily_sharpe']:.4f}")
            print(f"   日均收益率: {optimized_results['avg_daily_return']:.4f}%")
            print(f"   波动率: {optimized_results['volatility']:.4f}%")
            print(f"   基准资金: ${optimized_results['baseline_capital']:,.2f}")

            # 稳健性检验
            print(f"\n📊 稳健性检验（不同基准方法）:")
            for method in ["median", "moving_avg", "min_balance", "pnl_adjusted"]:
                test_result = self.optimized_calc.calculate_sharpe_ratio_pnl_based(
                    historical_pnl,
                    account_history,
                    method=method
                )
                print(f"   {method:15s}: {test_result['sharpe_ratio']:7.4f} "
                      f"(基准: ${test_result['baseline_capital']:,.0f})")

            # 保存结果
            results["sharpe_ratio"] = {
                "original": original_sharpe,
                "optimized": optimized_results['sharpe_ratio'],
                "daily_sharpe": optimized_results['daily_sharpe'],
                "avg_daily_return": optimized_results['avg_daily_return'],
                "volatility": optimized_results['volatility'],
                "baseline_capital": optimized_results['baseline_capital']
            }

        # 3. Max Drawdown - 对比
        if historical_pnl:
            print(f"\n{'='*60}")
            print("Max Drawdown 对比")
            print(f"{'='*60}")

            # 原始算法（初始资金推算可能不准确）
            account_value = float(margin_summary.get('accountValue', 0))
            original_dd = self._calculate_max_drawdown_from_pnl(historical_pnl, account_value)
            print(f"\n❌ 原始算法 Max Drawdown: {original_dd:.2f}%")
            print(f"   问题：初始资金推算可能受出入金影响")

            # 优化算法（基于 PnL 曲线）
            optimized_dd = self.optimized_calc.calculate_max_drawdown_pnl_based(
                historical_pnl,
                method="relative_to_peak"
            )

            print(f"\n✅ 优化算法（相对峰值法）:")
            print(f"   最大回撤: {optimized_dd['max_drawdown_pct']:.2f}%")
            print(f"   最大回撤金额: ${optimized_dd['max_drawdown_amount']:,.2f}")
            print(f"   PnL 峰值: ${optimized_dd['peak_pnl']:,.2f}")
            print(f"   PnL 谷底: ${optimized_dd['trough_pnl']:,.2f}")
            print(f"   回撤持续时间: {optimized_dd['drawdown_duration_days']:.1f} 天")

            # 其他方法对比
            print(f"\n📊 不同回撤计算方法:")
            for method in ["relative_to_peak", "absolute_pnl", "pnl_percentage"]:
                test_dd = self.optimized_calc.calculate_max_drawdown_pnl_based(
                    historical_pnl,
                    method=method
                )
                if test_dd['max_drawdown_pct'] > 0:
                    print(f"   {method:20s}: {test_dd['max_drawdown_pct']:6.2f}% "
                          f"(${test_dd['max_drawdown_amount']:,.0f})")
                else:
                    print(f"   {method:20s}: ${test_dd['max_drawdown_amount']:,.0f} (绝对金额)")

            # 保存结果
            results["max_drawdown"] = {
                "original": original_dd,
                "optimized": optimized_dd['max_drawdown_pct'],
                "amount": optimized_dd['max_drawdown_amount'],
                "peak_pnl": optimized_dd['peak_pnl'],
                "trough_pnl": optimized_dd['trough_pnl'],
                "duration_days": optimized_dd['drawdown_duration_days']
            }

        # 4. Win Rate（不受出入金影响，保持原算法）
        if fills:
            win_stats = self.calculate_win_rate(fills)
            results["win_rate"] = win_stats
            print(f"\n✅ Win Rate: {win_stats['winRate']:.2f}%")
            print(f"   (不受出入金影响，无需优化)")

        # 5. Hold Time Stats（不受出入金影响，保持原算法）
        if fills:
            hold_stats = self.calculate_hold_time_stats(fills)
            results["hold_time_stats"] = hold_stats
            print(f"\n✅ Average Hold Time: {hold_stats['allTimeAverage']:.2f} days")
            print(f"   (不受出入金影响，无需优化)")

        # 6. 当前持仓分析
        if asset_positions:
            position_analysis = self._analyze_current_positions(asset_positions)
            results["position_analysis"] = position_analysis
            print(f"\n✅ Current Positions: {len(asset_positions)} active")
            print(f"   Total Unrealized PnL: ${position_analysis.get('total_unrealized_pnl', 0):.2f}")

        print(f"\n{'='*60}")
        print("增强分析完成!")
        print(f"{'='*60}")

        return results

    def _build_account_history(self, historical_pnl, margin_summary):
        """
        构建账户价值历史（简化版）

        实际应用中应从 API 获取完整的账户价值历史
        这里使用简化逻辑：account_value = initial_capital + cumulative_pnl
        """
        if not historical_pnl:
            return []

        # 获取当前账户价值
        current_value = float(margin_summary.get('accountValue', 0))
        final_pnl = float(historical_pnl[-1].get('pnl', 0))

        # 推算初始资金（简化方法）
        # 注意：这里仍然使用简化方法，实际应从 API 获取
        if current_value > 0:
            initial_capital = current_value - final_pnl
        else:
            initial_capital = 10000  # 默认值

        # 构建账户价值历史
        account_history = []
        for item in historical_pnl:
            timestamp = item.get('time', 0)
            pnl = float(item.get('pnl', 0))
            account_value = initial_capital + pnl
            account_history.append([timestamp, account_value])

        return account_history


def demo_comparison():
    """
    演示：原始算法 vs 优化算法
    """
    print("="*80)
    print("集成演示：增强版 Apex Calculator")
    print("="*80)

    # 初始化增强版计算器
    calculator = EnhancedApexCalculator()

    # 示例用户地址
    user_address = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"

    print(f"\n使用增强版计算器分析用户: {user_address}")
    print("新功能：")
    print("  1. ✅ 规避出入金影响的 Sharpe Ratio 计算")
    print("  2. ✅ 基于 PnL 曲线的 Max Drawdown 计算")
    print("  3. ✅ 多种方法对比和稳健性检验")
    print("  4. ✅ 保留原有功能（Profit Factor, Win Rate 等）")

    print(f"\n{'='*80}")
    print("实际使用请取消注释以下代码：")
    print(f"{'='*80}")
    print("""
    # 执行增强分析
    results = calculator.analyze_user_enhanced(user_address, force_refresh=True)

    # 查看结果
    if "error" not in results:
        print("\\n分析结果：")
        print(f"  Profit Factor: {results['profit_factor']}")

        sharpe = results['sharpe_ratio']
        print(f"  年化 Sharpe Ratio (优化): {sharpe['optimized']:.4f}")
        print(f"  原始 Sharpe Ratio: {sharpe['original']:.4f}")

        dd = results['max_drawdown']
        print(f"  Max Drawdown (优化): {dd['optimized']:.2f}%")
        print(f"  原始 Max Drawdown: {dd['original']:.2f}%")

        win_rate = results['win_rate']
        print(f"  Win Rate: {win_rate['winRate']:.2f}%")
    """)

    print(f"\n{'='*80}")
    print("集成完成!")
    print(f"{'='*80}")


if __name__ == "__main__":
    demo_comparison()
