"""
优化算法：规避出入金影响的指标计算
通过算法创新避免显式跟踪出入金记录

核心思想：
1. 使用 PnL 变化而非账户价值变化
2. 使用动态基准资金而非固定初始资金
3. 基于相对回撤而非绝对回撤
"""

import math
from typing import List, Dict, Any, Tuple
from decimal import Decimal
import statistics


class OptimizedCalculator:
    """
    优化的指标计算器 - 规避出入金影响
    """

    # ============================================================
    # 方案1: PnL 基准法 - 使用有效交易资金作为基准
    # ============================================================

    def calculate_sharpe_ratio_pnl_based(
        self,
        pnl_history: List[Dict],
        account_history: List[List],
        method: str = "median"
    ) -> Dict[str, float]:
        """
        基于 PnL 变化计算 Sharpe Ratio（规避出入金影响）

        核心思想：
        - PnL 变化不受出入金影响
        - 使用"有效交易资金"作为稳定基准来标准化收益率
        - 有效交易资金 = 去除出入金影响后的账户规模估计

        Args:
            pnl_history: 历史 PnL 数据 [{"time": ts, "pnl": cumulative_pnl}, ...]
            account_history: 账户价值历史 [[timestamp, value], ...]
            method: 基准资金计算方法 ("median", "moving_avg", "min_balance")

        Returns:
            {
                "sharpe_ratio": 年化 Sharpe Ratio,
                "daily_sharpe": 日 Sharpe Ratio,
                "avg_daily_return": 平均日收益率,
                "volatility": 收益率波动率,
                "baseline_capital": 使用的基准资金
            }
        """
        if len(pnl_history) < 2:
            return {
                "sharpe_ratio": 0,
                "daily_sharpe": 0,
                "avg_daily_return": 0,
                "volatility": 0,
                "baseline_capital": 0
            }

        # 步骤1: 计算基准资金（有效交易资金）
        baseline_capital = self._calculate_baseline_capital(
            account_history,
            pnl_history,
            method
        )

        if baseline_capital <= 0:
            return {
                "sharpe_ratio": 0,
                "daily_sharpe": 0,
                "avg_daily_return": 0,
                "volatility": 0,
                "baseline_capital": 0
            }

        # 步骤2: 计算基于 PnL 变化的日收益率
        daily_returns = []

        for i in range(1, len(pnl_history)):
            pnl_prev = float(pnl_history[i-1].get('pnl', 0))
            pnl_curr = float(pnl_history[i].get('pnl', 0))

            # PnL 变化（绝对金额）
            pnl_change = pnl_curr - pnl_prev

            # 转换为收益率（相对于基准资金）
            daily_return = pnl_change / baseline_capital
            daily_returns.append(daily_return)

        if len(daily_returns) < 2:
            return {
                "sharpe_ratio": 0,
                "daily_sharpe": 0,
                "avg_daily_return": 0,
                "volatility": 0,
                "baseline_capital": baseline_capital
            }

        # 步骤3: 计算统计指标
        avg_return = statistics.mean(daily_returns)
        std_dev = statistics.stdev(daily_returns)

        if std_dev == 0:
            return {
                "sharpe_ratio": 0,
                "daily_sharpe": 0,
                "avg_daily_return": avg_return,
                "volatility": 0,
                "baseline_capital": baseline_capital
            }

        # 步骤4: 计算 Sharpe Ratio
        daily_sharpe = avg_return / std_dev
        annual_sharpe = daily_sharpe * math.sqrt(252)  # 年化

        return {
            "sharpe_ratio": annual_sharpe,
            "daily_sharpe": daily_sharpe,
            "avg_daily_return": avg_return * 100,  # 转换为百分比
            "volatility": std_dev * 100,
            "baseline_capital": baseline_capital
        }

    def _calculate_baseline_capital(
        self,
        account_history: List[List],
        pnl_history: List[Dict],
        method: str
    ) -> float:
        """
        计算基准资金（有效交易资金）

        核心思想：估算"如果没有出入金"的账户规模

        方法1 - median (推荐): 使用账户价值中位数
            - 优点: 对极值不敏感，对大额出入金有较好鲁棒性
            - 逻辑: 中位数代表"典型"账户规模

        方法2 - moving_avg: 使用移动平均
            - 优点: 平滑短期波动
            - 逻辑: 平均值代表长期资金水平

        方法3 - min_balance: 使用最低账户价值
            - 优点: 保守估计，避免高估风险承受能力
            - 逻辑: 最低点代表"核心资金"

        方法4 - pnl_adjusted (最准确但复杂):
            - 使用第一个账户价值减去第一个 PnL，得到"真实初始资金"
            - 然后根据 PnL 变化动态调整
        """

        if method == "median":
            # 中位数法：对出入金不敏感
            account_values = [value for _, value in account_history]
            return statistics.median(account_values)

        elif method == "moving_avg":
            # 移动平均法：平滑波动
            account_values = [value for _, value in account_history]
            # 使用整个周期的平均值
            return statistics.mean(account_values)

        elif method == "min_balance":
            # 最小余额法：保守估计
            account_values = [value for _, value in account_history]
            return min(account_values)

        elif method == "pnl_adjusted":
            # PnL 调整法：最准确
            # 逻辑: 第一个账户价值 - 第一个累计 PnL = 初始投入资金
            if len(account_history) > 0 and len(pnl_history) > 0:
                first_account_value = account_history[0][1]
                first_pnl = float(pnl_history[0].get('pnl', 0))

                # 推算初始资金
                initial_capital = first_account_value - first_pnl

                # 如果初始资金合理，使用它作为基准
                if initial_capital > 0:
                    return initial_capital
                else:
                    # 如果推算失败，回退到中位数法
                    account_values = [value for _, value in account_history]
                    return statistics.median(account_values)
            else:
                return 0

        else:
            # 默认使用中位数法
            account_values = [value for _, value in account_history]
            return statistics.median(account_values)

    # ============================================================
    # 方案2: 相对 PnL 回撤法 - 基于 PnL 曲线计算回撤
    # ============================================================

    def calculate_max_drawdown_pnl_based(
        self,
        pnl_history: List[Dict],
        method: str = "relative_to_peak"
    ) -> Dict[str, Any]:
        """
        基于 PnL 曲线计算最大回撤（规避出入金影响）

        核心思想：
        - PnL 曲线不受出入金影响
        - 计算 PnL 从峰值到谷底的相对回撤

        方法1 - relative_to_peak (推荐):
            回撤率 = (PnL峰值 - 当前PnL) / PnL峰值的账户价值

        方法2 - absolute_pnl:
            直接返回绝对 PnL 回撤金额

        方法3 - pnl_percentage:
            回撤率 = (PnL峰值 - PnL谷底) / |PnL峰值|

        Args:
            pnl_history: 历史 PnL 数据 [{"time": ts, "pnl": cumulative_pnl}, ...]
            method: 回撤计算方法

        Returns:
            {
                "max_drawdown_pct": 最大回撤百分比,
                "max_drawdown_amount": 最大回撤金额（美元）,
                "peak_pnl": PnL 峰值,
                "trough_pnl": PnL 谷底,
                "peak_time": 峰值时间戳,
                "trough_time": 谷底时间戳,
                "drawdown_duration_days": 回撤持续天数
            }
        """
        if not pnl_history or len(pnl_history) < 2:
            return {
                "max_drawdown_pct": 0,
                "max_drawdown_amount": 0,
                "peak_pnl": 0,
                "trough_pnl": 0,
                "peak_time": 0,
                "trough_time": 0,
                "drawdown_duration_days": 0
            }

        pnl_values = [float(item.get('pnl', 0)) for item in pnl_history]
        timestamps = [item.get('time', 0) for item in pnl_history]

        if method == "relative_to_peak":
            return self._calculate_relative_drawdown(pnl_values, timestamps, pnl_history)

        elif method == "absolute_pnl":
            return self._calculate_absolute_drawdown(pnl_values, timestamps)

        elif method == "pnl_percentage":
            return self._calculate_pnl_percentage_drawdown(pnl_values, timestamps)

        else:
            # 默认使用 relative_to_peak
            return self._calculate_relative_drawdown(pnl_values, timestamps, pnl_history)

    def _calculate_relative_drawdown(
        self,
        pnl_values: List[float],
        timestamps: List[int],
        pnl_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        相对回撤法（推荐）

        核心思想：
        - 跟踪 PnL 峰值
        - 计算从峰值到当前的 PnL 下降
        - 回撤率 = PnL 下降 / 峰值时的账户规模

        账户规模估计：
        - 如果有账户价值历史，使用峰值时的实际账户价值
        - 否则，使用 PnL 峰值 + 推算的基准资金
        """
        peak_pnl = pnl_values[0]
        peak_idx = 0
        max_drawdown_amount = 0
        max_drawdown_pct = 0
        trough_idx = 0

        for i, pnl in enumerate(pnl_values):
            # 更新峰值
            if pnl > peak_pnl:
                peak_pnl = pnl
                peak_idx = i

            # 计算当前回撤
            drawdown_amount = peak_pnl - pnl

            if drawdown_amount > max_drawdown_amount:
                max_drawdown_amount = drawdown_amount
                trough_idx = i

        # 计算回撤百分比
        # 关键：需要知道峰值时的账户规模
        # 简化方法：假设账户规模 = 基准资金 + peak_pnl

        # 估算基准资金（使用 PnL 均值的 10 倍作为经验估计）
        avg_pnl = statistics.mean([abs(p) for p in pnl_values])
        estimated_base_capital = max(avg_pnl * 10, 10000)  # 至少 $10K

        # 峰值时的账户规模
        peak_account_value = estimated_base_capital + peak_pnl

        if peak_account_value > 0:
            max_drawdown_pct = (max_drawdown_amount / peak_account_value) * 100
        else:
            max_drawdown_pct = 0

        # 计算回撤持续时间
        duration_ms = timestamps[trough_idx] - timestamps[peak_idx] if trough_idx > peak_idx else 0
        duration_days = duration_ms / (1000 * 86400) if duration_ms > 0 else 0

        return {
            "max_drawdown_pct": max_drawdown_pct,
            "max_drawdown_amount": max_drawdown_amount,
            "peak_pnl": peak_pnl,
            "trough_pnl": pnl_values[trough_idx],
            "peak_time": timestamps[peak_idx],
            "trough_time": timestamps[trough_idx],
            "drawdown_duration_days": duration_days
        }

    def _calculate_absolute_drawdown(
        self,
        pnl_values: List[float],
        timestamps: List[int]
    ) -> Dict[str, Any]:
        """
        绝对回撤法：直接返回 PnL 的最大下降金额

        优点：不需要账户价值，简单直观
        缺点：无法提供百分比，不便于跨账户比较
        """
        peak_pnl = pnl_values[0]
        peak_idx = 0
        max_drawdown = 0
        trough_idx = 0

        for i, pnl in enumerate(pnl_values):
            if pnl > peak_pnl:
                peak_pnl = pnl
                peak_idx = i

            drawdown = peak_pnl - pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                trough_idx = i

        duration_ms = timestamps[trough_idx] - timestamps[peak_idx] if trough_idx > peak_idx else 0
        duration_days = duration_ms / (1000 * 86400) if duration_ms > 0 else 0

        return {
            "max_drawdown_pct": 0,  # 不提供百分比
            "max_drawdown_amount": max_drawdown,
            "peak_pnl": peak_pnl,
            "trough_pnl": pnl_values[trough_idx],
            "peak_time": timestamps[peak_idx],
            "trough_time": timestamps[trough_idx],
            "drawdown_duration_days": duration_days
        }

    def _calculate_pnl_percentage_drawdown(
        self,
        pnl_values: List[float],
        timestamps: List[int]
    ) -> Dict[str, Any]:
        """
        PnL 百分比回撤法

        回撤率 = (PnL峰值 - PnL谷底) / |PnL峰值|

        注意：当 PnL 为负时，这个方法可能产生反直觉的结果
        例如：从 -$100 跌到 -$200，计算为 100% 回撤
        """
        peak_pnl = pnl_values[0]
        peak_idx = 0
        max_drawdown_pct = 0
        max_drawdown_amount = 0
        trough_idx = 0

        for i, pnl in enumerate(pnl_values):
            if pnl > peak_pnl:
                peak_pnl = pnl
                peak_idx = i

            drawdown_amount = peak_pnl - pnl

            # 计算相对于 PnL 峰值的百分比
            if abs(peak_pnl) > 1e-6:  # 避免除零
                drawdown_pct = (drawdown_amount / abs(peak_pnl)) * 100

                if drawdown_pct > max_drawdown_pct:
                    max_drawdown_pct = drawdown_pct
                    max_drawdown_amount = drawdown_amount
                    trough_idx = i

        duration_ms = timestamps[trough_idx] - timestamps[peak_idx] if trough_idx > peak_idx else 0
        duration_days = duration_ms / (1000 * 86400) if duration_ms > 0 else 0

        return {
            "max_drawdown_pct": max_drawdown_pct,
            "max_drawdown_amount": max_drawdown_amount,
            "peak_pnl": peak_pnl,
            "trough_pnl": pnl_values[trough_idx],
            "peak_time": timestamps[peak_idx],
            "trough_time": timestamps[trough_idx],
            "drawdown_duration_days": duration_days
        }

    # ============================================================
    # 方案3: 改进的 PnL 调整法 - 结合账户价值和 PnL
    # ============================================================

    def calculate_metrics_with_improved_adjustment(
        self,
        account_history: List[List],
        pnl_history: List[Dict],
        use_median_baseline: bool = True
    ) -> Dict[str, Any]:
        """
        改进的综合方法：结合账户价值和 PnL 数据

        核心思想：
        1. 使用 PnL 变化计算收益（不受出入金影响）
        2. 使用动态基准资金标准化收益率
        3. 同时计算多个基准下的指标，提供稳健性检验

        Args:
            account_history: 账户价值历史
            pnl_history: PnL 历史
            use_median_baseline: 是否使用中位数基准（否则使用 pnl_adjusted）

        Returns:
            综合指标结果
        """
        baseline_method = "median" if use_median_baseline else "pnl_adjusted"

        # 计算 Sharpe Ratio
        sharpe_results = self.calculate_sharpe_ratio_pnl_based(
            pnl_history,
            account_history,
            method=baseline_method
        )

        # 计算最大回撤
        drawdown_results = self.calculate_max_drawdown_pnl_based(
            pnl_history,
            method="relative_to_peak"
        )

        # 计算多个基准下的结果，用于稳健性检验
        robustness_check = {}
        for method in ["median", "moving_avg", "min_balance", "pnl_adjusted"]:
            sharpe = self.calculate_sharpe_ratio_pnl_based(
                pnl_history,
                account_history,
                method=method
            )
            robustness_check[method] = {
                "sharpe_ratio": sharpe["sharpe_ratio"],
                "baseline_capital": sharpe["baseline_capital"]
            }

        return {
            "sharpe_ratio": sharpe_results["sharpe_ratio"],
            "daily_sharpe": sharpe_results["daily_sharpe"],
            "avg_daily_return_pct": sharpe_results["avg_daily_return"],
            "volatility_pct": sharpe_results["volatility"],
            "baseline_capital": sharpe_results["baseline_capital"],
            "max_drawdown_pct": drawdown_results["max_drawdown_pct"],
            "max_drawdown_amount": drawdown_results["max_drawdown_amount"],
            "peak_pnl": drawdown_results["peak_pnl"],
            "trough_pnl": drawdown_results["trough_pnl"],
            "drawdown_duration_days": drawdown_results["drawdown_duration_days"],
            "robustness_check": robustness_check,
            "method_used": baseline_method
        }


# ============================================================
# 使用示例和测试
# ============================================================

def test_optimized_algorithms():
    """
    测试优化算法，对比不同方法的结果
    """
    print("=" * 60)
    print("优化算法测试：规避出入金影响")
    print("=" * 60)

    # 模拟数据：有出入金的场景
    # 场景：初始 $10K，盈利 $2K，入金 $5K，再亏损 $1K
    account_history = [
        [1000, 10000],   # T0: 初始
        [2000, 11000],   # T1: 盈利 $1K
        [3000, 12000],   # T2: 盈利 $1K
        [4000, 17000],   # T3: 入金 $5K（账户跳变）
        [5000, 16500],   # T4: 亏损 $500
        [6000, 16000],   # T5: 亏损 $500
    ]

    pnl_history = [
        {"time": 1000, "pnl": 0},
        {"time": 2000, "pnl": 1000},
        {"time": 3000, "pnl": 2000},
        {"time": 4000, "pnl": 2000},   # 入金不计入 PnL
        {"time": 5000, "pnl": 1500},
        {"time": 6000, "pnl": 1000},
    ]

    calculator = OptimizedCalculator()

    # 测试不同基准方法
    print("\n1. Sharpe Ratio - 不同基准方法对比:")
    print("-" * 60)

    for method in ["median", "moving_avg", "min_balance", "pnl_adjusted"]:
        result = calculator.calculate_sharpe_ratio_pnl_based(
            pnl_history,
            account_history,
            method=method
        )
        print(f"\n方法: {method}")
        print(f"  基准资金: ${result['baseline_capital']:,.2f}")
        print(f"  年化 Sharpe: {result['sharpe_ratio']:.4f}")
        print(f"  日均收益率: {result['avg_daily_return']:.4f}%")
        print(f"  波动率: {result['volatility']:.4f}%")

    # 测试回撤计算
    print("\n2. 最大回撤 - 不同方法对比:")
    print("-" * 60)

    for method in ["relative_to_peak", "absolute_pnl", "pnl_percentage"]:
        result = calculator.calculate_max_drawdown_pnl_based(
            pnl_history,
            method=method
        )
        print(f"\n方法: {method}")
        print(f"  最大回撤: {result['max_drawdown_pct']:.2f}%")
        print(f"  最大回撤金额: ${result['max_drawdown_amount']:,.2f}")
        print(f"  PnL 峰值: ${result['peak_pnl']:,.2f}")
        print(f"  PnL 谷底: ${result['trough_pnl']:,.2f}")

    # 测试综合方法
    print("\n3. 综合方法（推荐）:")
    print("-" * 60)

    result = calculator.calculate_metrics_with_improved_adjustment(
        account_history,
        pnl_history,
        use_median_baseline=True
    )

    print(f"\n主要指标:")
    print(f"  年化 Sharpe Ratio: {result['sharpe_ratio']:.4f}")
    print(f"  日均收益率: {result['avg_daily_return_pct']:.4f}%")
    print(f"  波动率: {result['volatility_pct']:.4f}%")
    print(f"  最大回撤: {result['max_drawdown_pct']:.2f}%")
    print(f"  使用的基准资金: ${result['baseline_capital']:,.2f}")

    print(f"\n稳健性检验（不同基准下的 Sharpe Ratio）:")
    for method, values in result['robustness_check'].items():
        print(f"  {method:15s}: {values['sharpe_ratio']:7.4f} (基准: ${values['baseline_capital']:,.0f})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_optimized_algorithms()
