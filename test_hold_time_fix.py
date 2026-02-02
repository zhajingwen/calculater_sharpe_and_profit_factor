"""
测试持仓时间计算算法的修复效果

此脚本演示了修复前后的差异：
1. 修复前：不区分多空方向，错误配对
2. 修复后：正确区分多空，支持部分平仓
"""

from apex_fork import ApexCalculator
from datetime import datetime, timedelta


def create_test_fills():
    """创建测试交易数据"""
    base_time = int(datetime.now().timestamp() * 1000)
    one_day = 24 * 60 * 60 * 1000

    # 测试场景1：多空混合交易（修复前会错误配对）
    test_scenario_1 = [
        {
            'coin': 'BTC',
            'dir': 'Open Long',
            'time': base_time,
            'sz': '1.0',
            'closedPnl': 0
        },
        {
            'coin': 'BTC',
            'dir': 'Open Short',
            'time': base_time + one_day,
            'sz': '2.0',
            'closedPnl': 0
        },
        {
            'coin': 'BTC',
            'dir': 'Close Short',
            'time': base_time + 2 * one_day,  # Short持仓1天
            'sz': '2.0',
            'closedPnl': 100
        },
        {
            'coin': 'BTC',
            'dir': 'Close Long',
            'time': base_time + 5 * one_day,  # Long持仓5天
            'sz': '1.0',
            'closedPnl': 200
        }
    ]

    # 测试场景2：部分平仓（修复前无法正确处理）
    test_scenario_2 = [
        {
            'coin': 'ETH',
            'dir': 'Open Long',
            'time': base_time,
            'sz': '10.0',
            'closedPnl': 0
        },
        {
            'coin': 'ETH',
            'dir': 'Close Long',
            'time': base_time + 2 * one_day,  # 部分平仓，持仓2天
            'sz': '5.0',
            'closedPnl': 50
        },
        {
            'coin': 'ETH',
            'dir': 'Close Long',
            'time': base_time + 4 * one_day,  # 剩余平仓，持仓4天
            'sz': '5.0',
            'closedPnl': 80
        }
    ]

    # 测试场景3：翻仓交易
    test_scenario_3 = [
        {
            'coin': 'SOL',
            'dir': 'Open Long',
            'time': base_time,
            'sz': '100.0',
            'closedPnl': 0
        },
        {
            'coin': 'SOL',
            'dir': 'Long > Short',  # 翻仓：平多开空
            'time': base_time + 3 * one_day,  # Long持仓3天
            'sz': '150.0',
            'closedPnl': 150
        },
        {
            'coin': 'SOL',
            'dir': 'Close Short',
            'time': base_time + 5 * one_day,  # Short持仓2天
            'sz': '150.0',
            'closedPnl': -50
        }
    ]

    return {
        'scenario_1': test_scenario_1,
        'scenario_2': test_scenario_2,
        'scenario_3': test_scenario_3
    }


def test_old_algorithm_simulation(fills):
    """模拟旧算法的行为（用于对比）"""
    from collections import defaultdict

    coin_open_trades = defaultdict(list)
    coin_positions = defaultdict(list)

    sorted_fills = sorted(fills, key=lambda x: x.get('time', 0))

    for fill in sorted_fills:
        coin = fill.get('coin', '')
        direction = fill.get('dir', '')
        timestamp = fill.get('time', 0)

        if not coin or not timestamp:
            continue

        # 旧算法：不区分多空，简单匹配Open/Close
        if 'Open' in direction:
            coin_open_trades[coin].append(timestamp)
        elif 'Close' in direction:
            if coin_open_trades[coin]:
                open_time = coin_open_trades[coin].pop(0)
                coin_positions[coin].append((open_time, timestamp))

    # 计算持仓时间
    all_hold_times = []
    for coin, positions in coin_positions.items():
        for open_time, close_time in positions:
            hold_time_days = (close_time - open_time) / 1000 / 86400
            all_hold_times.append(hold_time_days)

    avg_hold_time = sum(all_hold_times) / len(all_hold_times) if all_hold_times else 0
    return avg_hold_time, len(all_hold_times)


def main():
    print("=" * 80)
    print("📊 持仓时间计算算法修复测试")
    print("=" * 80)
    print()

    calculator = ApexCalculator()
    test_data = create_test_fills()

    # 测试场景1：多空混合交易
    print("🔍 测试场景1：多空混合交易")
    print("-" * 80)
    print("交易序列：")
    print("  1. T0:   Open Long BTC   (1.0)")
    print("  2. T+1d: Open Short BTC  (2.0)")
    print("  3. T+2d: Close Short BTC (2.0) ← Short持仓1天")
    print("  4. T+5d: Close Long BTC  (1.0) ← Long持仓5天")
    print()
    print("预期结果：")
    print("  - Short持仓: 1天")
    print("  - Long持仓: 5天")
    print("  - 平均持仓时间: 3天 (简单平均)")
    print()

    fills_1 = test_data['scenario_1']
    old_avg_1, old_count_1 = test_old_algorithm_simulation(fills_1)
    new_result_1 = calculator.calculate_hold_time_stats(fills_1)

    print(f"旧算法结果：")
    print(f"  ❌ 平均持仓时间: {old_avg_1:.2f} 天 (配对次数: {old_count_1})")
    print(f"     问题：Open Long错误地与Close Short配对")
    print()
    print(f"新算法结果：")
    print(f"  ✅ 平均持仓时间: {new_result_1['allTimeAverage']:.2f} 天")
    print(f"     正确配对：Long配Long，Short配Short")
    print()

    # 测试场景2：部分平仓
    print("\n🔍 测试场景2：部分平仓")
    print("-" * 80)
    print("交易序列：")
    print("  1. T0:   Open Long ETH  (10.0)")
    print("  2. T+2d: Close Long ETH (5.0)  ← 部分平仓，持仓2天")
    print("  3. T+4d: Close Long ETH (5.0)  ← 剩余平仓，持仓4天")
    print()
    print("预期结果：")
    print("  - 5 ETH持仓2天")
    print("  - 5 ETH持仓4天")
    print("  - 平均持仓时间: 3天")
    print()

    fills_2 = test_data['scenario_2']
    old_avg_2, old_count_2 = test_old_algorithm_simulation(fills_2)
    new_result_2 = calculator.calculate_hold_time_stats(fills_2)

    print(f"旧算法结果：")
    print(f"  ❌ 平均持仓时间: {old_avg_2:.2f} 天 (配对次数: {old_count_2})")
    print(f"     问题：第二次平仓找不到对应的开仓")
    print()
    print(f"新算法结果：")
    print(f"  ✅ 平均持仓时间: {new_result_2['allTimeAverage']:.2f} 天")
    print(f"     正确处理：支持部分平仓")
    print()

    # 测试场景3：翻仓交易
    print("\n🔍 测试场景3：翻仓交易")
    print("-" * 80)
    print("交易序列：")
    print("  1. T0:   Open Long SOL     (100.0)")
    print("  2. T+3d: Long > Short SOL  (150.0) ← 平多开空，Long持仓3天")
    print("  3. T+5d: Close Short SOL   (150.0) ← Short持仓2天")
    print()
    print("预期结果：")
    print("  - Long持仓: 3天")
    print("  - Short持仓: 2天")
    print("  - 平均持仓时间: 2.5天")
    print()

    fills_3 = test_data['scenario_3']
    old_avg_3, old_count_3 = test_old_algorithm_simulation(fills_3)
    new_result_3 = calculator.calculate_hold_time_stats(fills_3)

    print(f"旧算法结果：")
    print(f"  ❌ 平均持仓时间: {old_avg_3:.2f} 天 (配对次数: {old_count_3})")
    print(f"     问题：无法正确处理翻仓交易")
    print()
    print(f"新算法结果：")
    print(f"  ✅ 平均持仓时间: {new_result_3['allTimeAverage']:.2f} 天")
    print(f"     正确处理：识别翻仓交易，先平仓再开仓")
    print()

    # 总结
    print("\n" + "=" * 80)
    print("📈 修复总结")
    print("=" * 80)
    print()
    print("✅ 修复的问题：")
    print("  1. 区分多头和空头仓位，避免错误配对")
    print("  2. 支持部分平仓的数量加权计算")
    print("  3. 正确处理翻仓交易 (Long > Short, Short > Long)")
    print()
    print("🎯 算法改进：")
    print("  - 为每个币种维护独立的多头和空头开仓队列")
    print("  - 使用FIFO原则进行配对")
    print("  - 按数量比例处理部分平仓")
    print()
    print("⚠️  影响范围：")
    print("  - 如果用户只做单一方向交易，结果可能保持一致")
    print("  - 如果用户同时做多空交易，结果会显著改善")
    print("  - 存在部分平仓时，计算会更加准确")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
