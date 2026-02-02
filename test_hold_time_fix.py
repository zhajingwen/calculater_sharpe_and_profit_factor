#!/usr/bin/env python3
"""
测试最大回撤计算中的数值溢出问题
"""

from apex_fork import ApexCalculator

def test_max_drawdown_with_extreme_values():
    """测试极端值情况下的最大回撤计算"""

    calculator = ApexCalculator()

    # 模拟一些包含极端值的交易数据
    test_fills = [
        # 正常交易
        {'closedPnl': 100, 'px': 1000, 'sz': 1},
        {'closedPnl': -50, 'px': 1000, 'sz': 1},
        {'closedPnl': 200, 'px': 1000, 'sz': 1},
        # 极端亏损
        {'closedPnl': -9000, 'px': 1000, 'sz': 1},
        {'closedPnl': 50, 'px': 1000, 'sz': 1},
    ]

    result = calculator.calculate_trade_level_max_drawdown(test_fills)

    print("=" * 60)
    print("测试结果：")
    print("=" * 60)
    print(f"最大回撤: {result['max_drawdown_pct']:.2f}%")
    print(f"峰值累计收益: {result['peak_return']:.2f}%")
    print(f"谷底累计收益: {result['trough_return']:.2f}%")
    print(f"分析交易数: {result['total_trades']}")
    print("=" * 60)

    # 检查是否有异常值
    if abs(result['peak_return']) > 1000000:
        print("⚠️  检测到峰值累计收益异常值！")
        return False

    if abs(result['trough_return']) > 1000000:
        print("⚠️  检测到谷底累计收益异常值！")
        return False

    if result['max_drawdown_pct'] > 100:
        print("⚠️  最大回撤超过100%，可能存在问题！")
        return False

    print("✅ 测试通过：所有数值在合理范围内")
    return True


def test_with_real_address():
    """使用真实地址测试"""
    calculator = ApexCalculator()
    user_address = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"

    print("\n" + "=" * 60)
    print(f"测试真实地址: {user_address}")
    print("=" * 60)

    try:
        # 获取真实数据
        user_data = calculator.get_user_data(user_address)
        fills = user_data.get('fills', [])

        if not fills:
            print("⚠️  没有交易数据")
            return

        print(f"获取到 {len(fills)} 条交易记录")

        # 计算最大回撤
        result = calculator.calculate_trade_level_max_drawdown(fills)

        print("\n计算结果：")
        print(f"  • 最大回撤: {result['max_drawdown_pct']:.2f}%")
        print(f"  • 峰值累计收益: {result['peak_return']:.2f}%")
        print(f"  • 谷底累计收益: {result['trough_return']:.2f}%")
        print(f"  • 分析交易数: {result['total_trades']}")

        # 检查异常值
        if abs(result['peak_return']) > 1e6 or abs(result['trough_return']) > 1e6:
            print("\n" + "!" * 60)
            print("⚠️  检测到数值溢出问题！")
            print("!" * 60)

            # 详细分析问题
            print("\n🔍 问题诊断：")
            print(f"  峰值收益是否溢出: {abs(result['peak_return']) > 1e6}")
            print(f"  谷底收益是否溢出: {abs(result['trough_return']) > 1e6}")

            # 分析交易收益率
            trade_returns = []
            for fill in fills:
                closed_pnl = float(fill.get('closedPnl', 0))
                if closed_pnl == 0:
                    continue

                px = float(fill.get('px', 0))
                sz = abs(float(fill.get('sz', 0)))
                position_value = px * sz

                if position_value > 0:
                    trade_return = closed_pnl / position_value
                    trade_returns.append(trade_return)

            if trade_returns:
                max_return = max(trade_returns)
                min_return = min(trade_returns)
                print(f"\n  单笔最大收益率: {max_return:.2%}")
                print(f"  单笔最大亏损率: {min_return:.2%}")

                # 检查是否有极端值
                if abs(max_return) > 10 or abs(min_return) > 10:
                    print(f"\n  ⚠️  存在极端收益率（>1000%），可能导致溢出！")
                    print(f"  建议：添加收益率范围限制")
        else:
            print("\n✅ 数值正常，无溢出问题")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("开始测试最大回撤计算...\n")

    # 测试1：极端值测试
    test_max_drawdown_with_extreme_values()

    # 测试2：真实地址测试
    test_with_real_address()
