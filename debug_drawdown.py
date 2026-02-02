#!/usr/bin/env python3
"""调试 Max Drawdown 计算"""

from apex_fork import ApexCalculator

calculator = ApexCalculator()
user_address = '0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf'

# 获取数据
user_data = calculator.get_user_data(user_address, force_refresh=False)
fills = user_data.get('fills', [])
margin_summary = user_data.get('marginSummary', {})

# 构建历史 PnL
historical_pnl = calculator._build_historical_pnl_from_fills(fills)
cumulative_pnl = [item['pnl'] for item in historical_pnl]

# 当前账户价值
account_value = float(margin_summary.get('accountValue', 0))
final_pnl = cumulative_pnl[-1]

print('🔍 Max Drawdown 计算调试:')
print('='*60)
print(f'当前账户价值: ${account_value:,.2f}')
print(f'最终累计 PnL: ${final_pnl:,.2f}')
print(f'推算初始资金: ${account_value - final_pnl:,.2f}')
print(f'\n累计 PnL 统计:')
print(f'  最大: ${max(cumulative_pnl):,.2f}')
print(f'  最小: ${min(cumulative_pnl):,.2f}')
print(f'  范围: ${max(cumulative_pnl) - min(cumulative_pnl):,.2f}')

# 模拟计算
initial_capital = account_value - final_pnl
account_values = [initial_capital + pnl for pnl in cumulative_pnl]

print(f'\n账户价值序列:')
print(f'  初始: ${account_values[0]:,.2f}')
print(f'  峰值: ${max(account_values):,.2f}')
print(f'  最低: ${min(account_values):,.2f}')
print(f'  当前: ${account_values[-1]:,.2f}')

# 计算回撤
peak = account_values[0]
max_dd = 0
peak_idx = 0
trough_idx = 0

for i, value in enumerate(account_values):
    if value > peak:
        peak = value
        peak_idx = i

    if peak > 0:
        dd = ((peak - value) / peak) * 100
        if dd > max_dd:
            max_dd = dd
            trough_idx = i

print(f'\n回撤计算:')
print(f'  峰值: ${peak:,.2f} (第 {peak_idx+1} 笔交易)')
print(f'  谷底: ${account_values[trough_idx]:,.2f} (第 {trough_idx+1} 笔交易)')
print(f'  最大回撤: {max_dd:.2f}%')

# 检查是否有负值
negative_values = [v for v in account_values if v < 0]
if negative_values:
    print(f'\n⚠️  警告: 发现 {len(negative_values)} 个负账户价值!')
    print(f'  这可能是杠杆交易导致的')
