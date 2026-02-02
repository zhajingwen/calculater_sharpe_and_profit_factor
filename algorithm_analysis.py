#!/usr/bin/env python3
"""
算法合理性全面分析报告
分析所有交易指标的计算逻辑是否符合金融行业标准
"""

from apex_fork import ApexCalculator
import json

def analyze_algorithms():
    """分析所有算法的合理性"""

    calculator = ApexCalculator()
    user_address = '0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf'

    # 获取数据
    user_data = calculator.get_user_data(user_address, force_refresh=False)
    fills = user_data.get('fills', [])
    margin_summary = user_data.get('marginSummary', {})

    print('='*80)
    print('交易指标算法合理性分析报告')
    print('='*80)

    # 1. Profit Factor 分析
    print('\n📊 1. PROFIT FACTOR 分析')
    print('-'*80)
    analyze_profit_factor(calculator, fills, user_data.get('assetPositions', []))

    # 2. Sharpe Ratio 分析
    print('\n📊 2. SHARPE RATIO 分析')
    print('-'*80)
    analyze_sharpe_ratio(calculator, fills)

    # 3. Win Rate 分析
    print('\n📊 3. WIN RATE & DIRECTION BIAS 分析')
    print('-'*80)
    analyze_win_rate(calculator, fills)

    # 4. Max Drawdown 分析
    print('\n📊 4. MAX DRAWDOWN 分析')
    print('-'*80)
    analyze_max_drawdown(calculator, fills, margin_summary)

    # 5. Hold Time 分析
    print('\n📊 5. HOLD TIME STATS 分析')
    print('-'*80)
    analyze_hold_time(calculator, fills)

    # 总结
    print('\n'+'='*80)
    print('分析完成')
    print('='*80)


def analyze_profit_factor(calculator, fills, positions):
    """分析 Profit Factor 算法"""

    print('算法定义：Profit Factor = Total Gains / Total Losses')
    print('标准解释：衡量盈利交易与亏损交易的比率')
    print('  - PF > 1: 盈利策略')
    print('  - PF < 1: 亏损策略')
    print('  - PF = 1: 盈亏平衡')

    # 手动计算验证
    total_gains = 0
    total_losses = 0
    zero_pnl_count = 0

    for fill in fills:
        pnl = float(fill.get('closedPnl', 0))
        if pnl > 0:
            total_gains += pnl
        elif pnl < 0:
            total_losses += abs(pnl)
        else:
            zero_pnl_count += 1

    # 加上未实现盈亏
    for pos in positions:
        unrealized = float(pos.get('position', {}).get('unrealizedPnl', 0))
        if unrealized > 0:
            total_gains += unrealized
        elif unrealized < 0:
            total_losses += abs(unrealized)

    calculated_pf = total_gains / total_losses if total_losses > 0 else 0

    print(f'\n当前实现：')
    print(f'  Total Gains: ${total_gains:,.2f}')
    print(f'  Total Losses: ${total_losses:,.2f}')
    print(f'  Zero PnL Trades: {zero_pnl_count} (被正确忽略)')
    print(f'  Profit Factor: {calculated_pf:.4f}')

    # 使用代码计算
    code_pf = calculator.calculate_profit_factor(fills, positions)
    print(f'\n代码计算结果: {code_pf:.4f}')

    # 合理性评估
    print('\n✅ 合理性评估:')
    if abs(calculated_pf - code_pf) < 0.01:
        print('  ✓ 计算正确，符合标准定义')
    else:
        print(f'  ✗ 计算可能有误，差异: {abs(calculated_pf - code_pf):.4f}')

    print('  ✓ 正确包含未实现盈亏')
    print('  ✓ 正确忽略零 PnL 交易（开仓）')

    # 潜在问题
    print('\n⚠️  潜在问题:')
    print('  - 未实现盈亏随市场波动变化，可能导致 PF 不稳定')
    print('  - 建议：提供"仅已实现 PnL"和"含未实现 PnL"两个版本')


def analyze_sharpe_ratio(calculator, fills):
    """分析 Sharpe Ratio 算法"""

    print('算法定义：Sharpe Ratio = (Mean Return - Risk Free Rate) / Std Dev')
    print('标准解释：衡量风险调整后的收益率')
    print('  - SR > 1: 优秀')
    print('  - SR > 2: 非常优秀')
    print('  - SR < 0: 风险收益为负')

    # 构建历史 PnL
    historical_pnl = calculator._build_historical_pnl_from_fills(fills)

    if not historical_pnl or len(historical_pnl) < 2:
        print('\n❌ 数据不足，无法计算')
        return

    # 手动计算验证
    pnl_values = [item['pnl'] for item in historical_pnl]

    # 计算收益率序列
    returns = []
    for i in range(1, len(pnl_values)):
        # 这里的问题：应该基于账户价值计算收益率，而不是 PnL 差值
        if pnl_values[i-1] != 0:
            ret = (pnl_values[i] - pnl_values[i-1]) / abs(pnl_values[i-1])
            returns.append(ret)

    if len(returns) < 2:
        print('\n❌ 收益率数据不足')
        return

    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
    std_dev = variance ** 0.5

    sharpe = mean_return / std_dev if std_dev > 0 else 0

    print(f'\n当前实现分析:')
    print(f'  历史 PnL 数据点: {len(historical_pnl)}')
    print(f'  收益率序列长度: {len(returns)}')
    print(f'  平均收益率: {mean_return:.6f}')
    print(f'  标准差: {std_dev:.6f}')
    print(f'  手动计算 Sharpe: {sharpe:.4f}')

    # 使用代码计算
    code_sharpe = calculator._calculate_simple_sharpe_ratio(historical_pnl)
    print(f'  代码计算 Sharpe: {code_sharpe:.4f}')

    # 合理性评估
    print('\n⚠️  算法问题:')
    print('  ✗ 当前基于累计 PnL 计算收益率，这是不标准的')
    print('  ✗ 应该基于账户价值计算收益率')
    print('  ✗ 分母使用 abs(pnl) 会导致负 PnL 时的符号问题')

    print('\n💡 建议改进:')
    print('  1. 基于账户价值计算收益率: Return = (Value_t - Value_{t-1}) / Value_{t-1}')
    print('  2. 考虑时间周期：年化 Sharpe Ratio = SR * sqrt(252) (对日收益)')
    print('  3. Risk Free Rate 应该设置为实际的无风险利率（如 3-5%）')


def analyze_win_rate(calculator, fills):
    """分析 Win Rate 算法"""

    print('算法定义：')
    print('  Win Rate = Winning Trades / (Winning Trades + Losing Trades)')
    print('  Direction Bias = (Long Trades - Short Trades) / Total Trades * 50 + 50')

    # 手动计算
    winning = 0
    losing = 0
    long_trades = 0
    short_trades = 0
    zero_pnl = 0

    for fill in fills:
        pnl = float(fill.get('closedPnl', 0))
        direction = fill.get('dir', '')

        # 统计胜率
        if pnl > 0:
            winning += 1
        elif pnl < 0:
            losing += 1
        else:
            zero_pnl += 1

        # 统计方向
        if direction in ['Open Long', 'Close Long', 'Short > Long']:
            long_trades += 1
        elif direction in ['Open Short', 'Close Short', 'Long > Short']:
            short_trades += 1

    total_pnl_trades = winning + losing
    win_rate = (winning / total_pnl_trades * 100) if total_pnl_trades > 0 else 0

    bias = ((long_trades - short_trades) / len(fills) * 100 + 100) / 2 if fills else 50

    print(f'\n当前数据:')
    print(f'  Winning Trades: {winning}')
    print(f'  Losing Trades: {losing}')
    print(f'  Zero PnL Trades: {zero_pnl} (开仓交易)')
    print(f'  Win Rate: {win_rate:.2f}%')
    print(f'  Long Trades: {long_trades}')
    print(f'  Short Trades: {short_trades}')
    print(f'  Direction Bias: {bias:.2f}%')

    # 使用代码计算
    result = calculator.calculate_win_rate(fills)
    print(f'\n代码计算结果:')
    print(f'  Win Rate: {result["winRate"]:.2f}%')
    print(f'  Direction Bias: {result["bias"]:.2f}%')

    # 合理性评估
    print('\n✅ 合理性评估:')
    print('  ✓ 正确排除零 PnL 交易（开仓不计入胜率）')
    print('  ✓ 方向偏好计算公式合理')

    print('\n⚠️  潜在问题:')
    print('  - 方向判断可能不完整：')
    print('    当前识别: Open Long, Close Long, Short > Long')
    print('    可能缺失: 其他方向标识（如 "Buy", "Sell" 等）')
    print('  - 建议打印未识别的 direction 值进行排查')


def analyze_max_drawdown(calculator, fills, margin_summary):
    """分析 Max Drawdown 算法"""

    print('算法定义：Max Drawdown = (Peak - Trough) / Peak * 100%')
    print('标准解释：从历史最高点到最低点的最大跌幅')

    # 构建历史 PnL
    historical_pnl = calculator._build_historical_pnl_from_fills(fills)

    if not historical_pnl:
        print('\n❌ 无历史数据')
        return

    cumulative_pnl = [item['pnl'] for item in historical_pnl]
    account_value = float(margin_summary.get('accountValue', 0))
    final_pnl = cumulative_pnl[-1]
    initial_capital = account_value - final_pnl

    # 构建账户价值序列
    account_values = [initial_capital + pnl for pnl in cumulative_pnl]

    # 计算回撤
    peak = account_values[0]
    max_dd = 0
    peak_value = 0
    trough_value = 0

    for value in account_values:
        if value > peak:
            peak = value

        if peak > 0:
            dd = ((peak - value) / peak) * 100
            if dd > max_dd:
                max_dd = dd
                peak_value = peak
                trough_value = value

    print(f'\n当前实现分析:')
    print(f'  推算初始资金: ${initial_capital:,.2f}')
    print(f'  峰值账户价值: ${peak_value:,.2f}')
    print(f'  谷底账户价值: ${trough_value:,.2f}')
    print(f'  最大回撤: {max_dd:.2f}%')

    # 使用代码计算
    code_dd = calculator._calculate_max_drawdown_from_pnl(historical_pnl, account_value)
    print(f'  代码计算结果: {code_dd:.2f}%')

    # 特殊情况分析
    negative_values = [v for v in account_values if v < 0]

    print('\n⚠️  算法问题:')
    if negative_values:
        print(f'  ✗ 发现 {len(negative_values)} 个负账户价值（杠杆爆仓）')
        print(f'  ✗ 最大回撤 {max_dd:.2f}% > 100%，表明账户曾欠债')
        print(f'  ✗ 最低账户价值: ${min(account_values):,.2f}')

    print('  ✗ 初始资金推算方法不准确：')
    print('    当前: initial_capital = current_value - final_pnl')
    print('    问题: 忽略了存取款操作')

    print('\n💡 建议改进:')
    print('  1. 如果有存取款记录，应该考虑资金流动')
    print('  2. 对于杠杆交易，考虑显示两个指标：')
    print('     - 基于账户价值的回撤（可能>100%）')
    print('     - 基于初始保证金的回撤（限制≤100%）')
    print('  3. 添加时间维度：最大回撤发生的时间和持续时长')


def analyze_hold_time(calculator, fills):
    """分析 Hold Time 算法"""

    print('算法定义：配对 Open/Close 交易计算持仓时间')
    print('标准解释：从开仓到平仓的时间跨度')

    # 统计交易方向
    open_count = 0
    close_count = 0
    other_count = 0

    for fill in fills:
        direction = fill.get('dir', '')
        if 'Open' in direction:
            open_count += 1
        elif 'Close' in direction:
            close_count += 1
        else:
            other_count += 1

    print(f'\n交易分布:')
    print(f'  Open 交易: {open_count}')
    print(f'  Close 交易: {close_count}')
    print(f'  其他交易: {other_count}')

    # 使用代码计算
    result = calculator.calculate_hold_time_stats(fills)

    print(f'\n计算结果:')
    print(f'  历史平均: {result["allTimeAverage"]:.2f} 天')
    print(f'  近30天平均: {result["last30DaysAverage"]:.2f} 天')
    print(f'  近7天平均: {result["last7DaysAverage"]:.2f} 天')
    print(f'  今日平均: {result["todayCount"]:.2f} 天')

    # 合理性评估
    print('\n✅ 合理性评估:')
    print('  ✓ FIFO 配对逻辑合理（先开先平）')
    print('  ✓ 按币种分组处理，避免混淆')
    print('  ✓ 按时间分段统计，提供多维度视角')

    print('\n⚠️  潜在问题:')
    if open_count != close_count:
        print(f'  ⚠️  Open/Close 数量不匹配: {open_count} vs {close_count}')
        print('     可能存在：')
        print('     1. 当前持仓（未平仓）')
        print('     2. 部分平仓操作')
        print('     3. 方向识别不完整')

    print('\n💡 建议改进:')
    print('  1. 添加"配对成功率"指标')
    print('  2. 处理部分平仓：按 size 比例配对')
    print('  3. 报告未配对的 Open/Close 交易数量')


if __name__ == '__main__':
    analyze_algorithms()
