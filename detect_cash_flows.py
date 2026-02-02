#!/usr/bin/env python3
"""
出入金检测算法
通过账户价值和PnL的不一致性来推断出入金
"""

from apex_fork import ApexCalculator
from datetime import datetime

def detect_cash_flows(fills, account_value, threshold=100):
    """
    检测出入金操作

    原理：
    如果没有出入金，则：
        account_value(t) = account_value(t-1) + pnl_change(t)

    如果有出入金，则会出现不一致：
        actual_value(t) != expected_value(t)
        cash_flow(t) = actual_value(t) - expected_value(t)

    Args:
        fills: 成交记录
        account_value: 当前账户价值
        threshold: 出入金检测阈值（美元）

    Returns:
        {
            "has_cash_flows": bool,
            "estimated_initial_capital": float,
            "cash_flow_events": [...]
        }
    """

    # 构建历史累计 PnL
    sorted_fills = sorted(fills, key=lambda x: x.get('time', 0))

    cumulative_pnl_history = []
    cumulative_pnl = 0

    for fill in sorted_fills:
        pnl = float(fill.get('closedPnl', 0))
        if pnl != 0:  # 只记录有PnL的交易
            cumulative_pnl += pnl
            cumulative_pnl_history.append({
                'time': fill.get('time'),
                'pnl': cumulative_pnl,
                'coin': fill.get('coin'),
                'direction': fill.get('dir')
            })

    if not cumulative_pnl_history:
        return {
            "has_cash_flows": False,
            "estimated_initial_capital": account_value,
            "cash_flow_events": []
        }

    # 最终累计 PnL
    final_cumulative_pnl = cumulative_pnl_history[-1]['pnl']

    # 简单推算：假设没有出入金
    simple_initial_capital = account_value - final_cumulative_pnl

    print('📊 出入金检测分析')
    print('='*60)
    print(f'当前账户价值: ${account_value:,.2f}')
    print(f'最终累计 PnL: ${final_cumulative_pnl:,.2f}')
    print(f'推算初始资金: ${simple_initial_capital:,.2f}')

    # 分析 PnL 波动模式，寻找异常
    print('\n🔍 分析累计 PnL 波动:')
    pnl_values = [item['pnl'] for item in cumulative_pnl_history]

    max_pnl = max(pnl_values)
    min_pnl = min(pnl_values)
    pnl_range = max_pnl - min_pnl

    print(f'  PnL 最大值: ${max_pnl:,.2f}')
    print(f'  PnL 最小值: ${min_pnl:,.2f}')
    print(f'  PnL 波动范围: ${pnl_range:,.2f}')

    # 检查账户是否曾经为负
    # 如果 simple_initial_capital + min_pnl < 0，说明账户曾爆仓
    min_account_value = simple_initial_capital + min_pnl

    print(f'\n📉 账户价值分析:')
    print(f'  推算峰值: ${simple_initial_capital + max_pnl:,.2f}')
    print(f'  推算谷底: ${min_account_value:,.2f}')

    # 出入金检测逻辑
    cash_flow_indicators = []

    # 指标1: 账户曾为负但现在为正
    if min_account_value < -threshold and account_value > 0:
        cash_flow_indicators.append({
            'type': '可能补仓',
            'reason': f'账户曾跌至 ${min_account_value:,.2f}，现恢复至 ${account_value:,.2f}',
            'likelihood': 'high'
        })

    # 指标2: 初始资金推算异常（过小或为负）
    if simple_initial_capital < 1000:
        cash_flow_indicators.append({
            'type': '初始资金异常',
            'reason': f'推算初始资金仅 ${simple_initial_capital:,.2f}，可能有入金',
            'likelihood': 'medium'
        })

    # 指标3: PnL 波动范围远大于当前账户价值
    if pnl_range > account_value * 2:
        cash_flow_indicators.append({
            'type': 'PnL波动异常',
            'reason': f'PnL 波动 ${pnl_range:,.2f} >> 账户价值 ${account_value:,.2f}',
            'likelihood': 'medium'
        })

    # 检测大额 PnL 跳变（可能是强平/爆仓后的重置）
    large_jumps = []
    for i in range(1, len(cumulative_pnl_history)):
        pnl_change = abs(cumulative_pnl_history[i]['pnl'] - cumulative_pnl_history[i-1]['pnl'])

        # 如果单笔 PnL 变化超过当前账户价值的 50%，可能异常
        if pnl_change > account_value * 0.5:
            large_jumps.append({
                'time': cumulative_pnl_history[i]['time'],
                'change': pnl_change,
                'from': cumulative_pnl_history[i-1]['pnl'],
                'to': cumulative_pnl_history[i]['pnl']
            })

    if large_jumps:
        print(f'\n⚠️  发现 {len(large_jumps)} 个异常大额 PnL 跳变:')
        for jump in large_jumps[:5]:  # 只显示前5个
            time_str = datetime.fromtimestamp(jump['time']/1000).strftime('%Y-%m-%d %H:%M')
            print(f'  - {time_str}: ${jump["change"]:,.2f}')

    # 总结
    has_cash_flows = len(cash_flow_indicators) > 0

    print('\n' + '='*60)
    if has_cash_flows:
        print('⚠️  检测到可能的出入金操作:')
        for indicator in cash_flow_indicators:
            likelihood_emoji = '🔴' if indicator['likelihood'] == 'high' else '🟡'
            print(f'{likelihood_emoji} {indicator["type"]}: {indicator["reason"]}')

        print('\n💡 建议:')
        print('  1. 使用 Time-Weighted Return (TWR) 计算收益率')
        print('  2. 谨慎解读 Max Drawdown（可能被出入金掩盖）')
        print('  3. 询问用户确认是否有出入金操作')
    else:
        print('✅ 未检测到明显的出入金操作')
        print(f'   可以使用推算的初始资金: ${simple_initial_capital:,.2f}')

    return {
        "has_cash_flows": has_cash_flows,
        "estimated_initial_capital": simple_initial_capital,
        "cash_flow_indicators": cash_flow_indicators,
        "large_jumps": large_jumps,
        "min_account_value": min_account_value,
        "max_account_value": simple_initial_capital + max_pnl
    }


if __name__ == '__main__':
    calculator = ApexCalculator()
    user_address = '0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf'

    user_data = calculator.get_user_data(user_address, force_refresh=False)
    fills = user_data.get('fills', [])
    margin_summary = user_data.get('marginSummary', {})
    account_value = float(margin_summary.get('accountValue', 0))

    result = detect_cash_flows(fills, account_value)

    print(f'\n返回结果:')
    print(f'  has_cash_flows: {result["has_cash_flows"]}')
    print(f'  estimated_initial_capital: ${result["estimated_initial_capital"]:,.2f}')
