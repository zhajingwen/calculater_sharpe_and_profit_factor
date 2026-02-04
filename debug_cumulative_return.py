#!/usr/bin/env python3
"""
调试累计收益率计算问题
"""
from apex_fork import ApexCalculator

def analyze_extreme_returns(user_address):
    """分析极端收益率"""
    calculator = ApexCalculator()

    # 获取数据
    user_data = calculator.get_user_data(user_address, force_refresh=False)
    fills = user_data.get('fills', [])

    print(f"总交易数: {len(fills)}")

    # 统计单笔收益率
    extreme_returns = []
    total_pnl = 0

    for fill in fills:
        closed_pnl = float(fill.get('closedPnl', 0))
        if closed_pnl == 0:
            continue

        total_pnl += closed_pnl

        sz = float(fill.get('sz', 0))
        px = float(fill.get('px', 0))
        notional_value = abs(sz) * px

        if notional_value > 0:
            trade_return = closed_pnl / notional_value

            if trade_return <= -1.0:  # 收益率 <= -100%
                extreme_returns.append({
                    'time': fill.get('time'),
                    'coin': fill.get('coin'),
                    'pnl': closed_pnl,
                    'notional': notional_value,
                    'return_pct': trade_return * 100,
                    'sz': sz,
                    'px': px
                })

    print(f"\n总盈亏 (PNL): ${total_pnl:,.2f}")
    print(f"\n收益率 <= -100% 的交易: {len(extreme_returns)} 笔")

    if extreme_returns:
        print(f"\n前20笔极端亏损交易:")
        print(f"{'时间':<12} {'币种':<8} {'盈亏':<12} {'持仓价值':<12} {'数量':<10} {'价格':<10} {'收益率'}")
        print("-" * 90)

        from datetime import datetime
        for trade in sorted(extreme_returns, key=lambda x: x['return_pct'])[:20]:
            time_str = datetime.fromtimestamp(trade['time']/1000).strftime('%Y-%m-%d')
            print(f"{time_str:<12} {trade['coin']:<8} ${trade['pnl']:>10.2f} "
                  f"${trade['notional']:>10.2f} {trade['sz']:>9.4f} "
                  f"${trade['px']:>9.2f} {trade['return_pct']:>10.2f}%")

    # 计算累计收益率（当前方法 - 未修复）
    print("\n\n=== 未修复算法（复利计算） ===")
    cumulative_old = 1.0
    negative_count_old = 0

    for fill in fills:
        closed_pnl = float(fill.get('closedPnl', 0))
        if closed_pnl == 0:
            continue

        sz = float(fill.get('sz', 0))
        px = float(fill.get('px', 0))
        notional_value = abs(sz) * px

        if notional_value > 0:
            trade_return = closed_pnl / notional_value
            cumulative_old *= (1 + trade_return)

            if cumulative_old < 0:
                negative_count_old += 1

    cumulative_return_old = (cumulative_old - 1) * 100

    print(f"累计乘数 (cumulative): {cumulative_old}")
    print(f"累计收益率: {cumulative_return_old:.2f}%")
    print(f"出现负数的次数: {negative_count_old}")

    # 计算累计收益率（修复后）
    print("\n\n=== 修复后算法（限制收益率下限 -99.9%） ===")
    cumulative_fixed = 1.0
    negative_count_fixed = 0
    capped_count = 0

    for fill in fills:
        closed_pnl = float(fill.get('closedPnl', 0))
        if closed_pnl == 0:
            continue

        sz = float(fill.get('sz', 0))
        px = float(fill.get('px', 0))
        notional_value = abs(sz) * px

        if notional_value > 0:
            trade_return = closed_pnl / notional_value
            if trade_return < -0.999:
                capped_count += 1
            trade_return = max(trade_return, -0.999)  # 🔧 修复
            cumulative_fixed *= (1 + trade_return)

            if cumulative_fixed < 0:
                negative_count_fixed += 1

    cumulative_return_fixed = (cumulative_fixed - 1) * 100

    print(f"累计乘数 (cumulative): {cumulative_fixed}")
    print(f"累计收益率: {cumulative_return_fixed:.2f}%")
    print(f"出现负数的次数: {negative_count_fixed}")
    print(f"被截断的交易数: {capped_count}")

    # 计算简单的平均收益率
    print("\n\n=== 其他统计 ===")
    trade_returns = []
    for fill in fills:
        closed_pnl = float(fill.get('closedPnl', 0))
        if closed_pnl == 0:
            continue

        sz = float(fill.get('sz', 0))
        px = float(fill.get('px', 0))
        notional_value = abs(sz) * px

        if notional_value > 0:
            trade_return = closed_pnl / notional_value
            trade_returns.append(trade_return)

    if trade_returns:
        avg_return = sum(trade_returns) / len(trade_returns)
        print(f"平均每笔收益率: {avg_return * 100:.4f}%")
        print(f"最小收益率: {min(trade_returns) * 100:.2f}%")
        print(f"最大收益率: {max(trade_returns) * 100:.2f}%")

if __name__ == "__main__":
    user_address = "0x8d8b1f0a704544f4c8adaf55a1063be1bb656cc9"
    analyze_extreme_returns(user_address)
