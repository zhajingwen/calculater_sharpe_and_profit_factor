#!/usr/bin/env python3
"""
分析收益率分布，找出累计收益率为负的原因
"""
from apex_fork import ApexCalculator
import statistics

def analyze_return_distribution(user_address):
    """分析收益率分布"""
    calculator = ApexCalculator()

    # 获取数据
    user_data = calculator.get_user_data(user_address, force_refresh=False)
    fills = user_data.get('fills', [])

    # 收集数据
    trade_returns = []
    trade_pnls = []
    trade_notional = []

    for fill in fills:
        closed_pnl = float(fill.get('closedPnl', 0))
        if closed_pnl == 0:
            continue

        sz = float(fill.get('sz', 0))
        px = float(fill.get('px', 0))
        notional_value = abs(sz) * px

        if notional_value > 0:
            trade_return = closed_pnl / notional_value
            trade_return = max(trade_return, -0.999)  # 应用修复

            trade_returns.append(trade_return)
            trade_pnls.append(closed_pnl)
            trade_notional.append(notional_value)

    print("=" * 80)
    print("收益率分布分析")
    print("=" * 80)

    print(f"\n总交易数: {len(trade_returns)}")
    print(f"总盈亏: ${sum(trade_pnls):,.2f}")

    # 统计收益率分布
    mean_return = statistics.mean(trade_returns)
    median_return = statistics.median(trade_returns)
    std_return = statistics.stdev(trade_returns) if len(trade_returns) > 1 else 0
    min_return = min(trade_returns)
    max_return = max(trade_returns)

    print(f"\n收益率统计:")
    print(f"  平均值: {mean_return * 100:.4f}%")
    print(f"  中位数: {median_return * 100:.4f}%")
    print(f"  标准差: {std_return * 100:.4f}%")
    print(f"  最小值: {min_return * 100:.2f}%")
    print(f"  最大值: {max_return * 100:.2f}%")

    # 分布区间
    print(f"\n收益率分布区间:")
    bins = [
        ("-99.9% ~ -50%", -0.999, -0.5),
        ("-50% ~ -20%", -0.5, -0.2),
        ("-20% ~ -10%", -0.2, -0.1),
        ("-10% ~ -5%", -0.1, -0.05),
        ("-5% ~ 0%", -0.05, 0),
        ("0% ~ 5%", 0, 0.05),
        ("5% ~ 10%", 0.05, 0.1),
        ("10% ~ 20%", 0.1, 0.2),
        ("20% ~ 50%", 0.2, 0.5),
        ("50% ~ 100%", 0.5, 1.0)
    ]

    for label, low, high in bins:
        count = sum(1 for r in trade_returns if low <= r < high)
        pnl = sum(p for r, p in zip(trade_returns, trade_pnls) if low <= r < high)
        if count > 0:
            print(f"  {label:<20}: {count:>5} 笔  (总盈亏: ${pnl:>12,.2f})")

    # 盈亏分布
    print(f"\n盈亏交易统计:")
    winning_trades = [p for p in trade_pnls if p > 0]
    losing_trades = [p for p in trade_pnls if p < 0]

    print(f"  盈利交易: {len(winning_trades)} 笔, 总计 ${sum(winning_trades):,.2f}")
    print(f"  亏损交易: {len(losing_trades)} 笔, 总计 ${sum(losing_trades):,.2f}")

    # 加权收益率 vs 简单平均收益率
    print(f"\n收益率对比:")
    print(f"  简单平均收益率: {mean_return * 100:.4f}%")

    # 按持仓价值加权的平均收益率
    weighted_return = (sum(trade_pnls) / sum(trade_notional)) * 100
    print(f"  加权平均收益率: {weighted_return:.4f}%  (= 总盈亏 / 总持仓价值)")

    # 复利累计
    cumulative = 1.0
    for ret in trade_returns:
        cumulative *= (1 + ret)
    cumulative_return = (cumulative - 1) * 100
    print(f"  复利累计收益率: {cumulative_return:.2f}%")

    print(f"\n持仓价值统计:")
    print(f"  总持仓价值: ${sum(trade_notional):,.2f}")
    print(f"  平均持仓价值: ${statistics.mean(trade_notional):,.2f}")
    print(f"  中位持仓价值: ${statistics.median(trade_notional):,.2f}")

    # 找出大额亏损交易
    print(f"\n前10笔大额亏损交易（按持仓价值）:")
    large_losses = []
    for i, (ret, pnl, notional) in enumerate(zip(trade_returns, trade_pnls, trade_notional)):
        if pnl < 0 and notional > 1000:  # 持仓价值超过$1000的亏损
            large_losses.append({
                'idx': i,
                'return': ret * 100,
                'pnl': pnl,
                'notional': notional
            })

    large_losses.sort(key=lambda x: x['pnl'])
    print(f"{'序号':<8} {'收益率':<12} {'盈亏':<15} {'持仓价值'}")
    print("-" * 60)
    for loss in large_losses[:10]:
        print(f"{loss['idx']:<8} {loss['return']:>10.2f}% ${loss['pnl']:>12,.2f} ${loss['notional']:>12,.2f}")

    # 解释为什么累计收益率为负
    print(f"\n" + "=" * 80)
    print("为什么累计收益率为负？")
    print("=" * 80)

    print(f"""
累计收益率计算的问题：

1. **复利计算假设**：
   - 假设每次交易都用全部资金
   - 前一笔的收益会影响下一笔的"本金"

2. **实际情况**：
   - 每笔交易只用一部分资金（持仓价值 ≠ 总资金）
   - 大额亏损交易的持仓价值大，对复利影响大
   - 小额盈利交易的持仓价值小，贡献小

3. **数据分析**：
   - 总盈亏: ${sum(trade_pnls):,.2f} (正的) ✅
   - 简单平均收益率: {mean_return * 100:.4f}% (正的) ✅
   - 复利累计收益率: {cumulative_return:.2f}% (负的) ❌

4. **结论**：
   基于持仓价值的复利累计收益率 **不适合** 衡量总体表现！

   原因：
   - 不同交易的持仓价值差异很大
   - 复利假设与实际资金使用不符
   - 无法反映真实的资金增长情况

建议：
   - 使用 "简单平均收益率" 或 "加权平均收益率"
   - 或者使用 "总盈亏 / 初始本金" 作为累计收益率
""")

if __name__ == "__main__":
    user_address = "0x8d8b1f0a704544f4c8adaf55a1063be1bb656cc9"
    analyze_return_distribution(user_address)
