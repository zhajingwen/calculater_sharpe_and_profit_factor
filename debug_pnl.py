#!/usr/bin/env python3
"""调试 Historical PnL 数据"""

from apex_fork import ApexCalculator

calculator = ApexCalculator()
user_address = '0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf'

# 获取数据
user_data = calculator.get_user_data(user_address, force_refresh=False)
fills = user_data.get('fills', [])

# 构建历史 PnL
historical_pnl = calculator._build_historical_pnl_from_fills(fills)

print('📊 Historical PnL 数据分析:')
print('='*60)
print(f'总记录数: {len(historical_pnl)}')

if historical_pnl:
    pnl_values = [item['pnl'] for item in historical_pnl]
    print(f'\n累计 PnL 范围:')
    print(f'  最小值: ${min(pnl_values):,.2f}')
    print(f'  最大值: ${max(pnl_values):,.2f}')
    print(f'  起始值: ${pnl_values[0]:,.2f}')
    print(f'  结束值: ${pnl_values[-1]:,.2f}')

    print(f'\n前10条记录:')
    for i, item in enumerate(historical_pnl[:10]):
        print(f'  {i+1}. PnL: ${item["pnl"]:,.2f}')

    print(f'\n最后10条记录:')
    for i, item in enumerate(historical_pnl[-10:]):
        print(f'  {len(historical_pnl)-10+i+1}. PnL: ${item["pnl"]:,.2f}')

    # 计算回撤
    peak = pnl_values[0]
    max_dd = 0
    for value in pnl_values:
        if value > peak:
            peak = value
        dd = peak - value
        if dd > max_dd:
            max_dd = dd

    print(f'\n回撤计算:')
    print(f'  峰值: ${peak:,.2f}')
    print(f'  最大回撤金额: ${max_dd:,.2f}')
    if peak > 0:
        print(f'  最大回撤百分比: {(max_dd / peak * 100):.2f}%')
