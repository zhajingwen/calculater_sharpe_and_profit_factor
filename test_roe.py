#!/usr/bin/env python3
"""
ROE功能测试脚本
验证边界条件和错误处理
"""

from apex_fork import ApexCalculator, ROEMetrics
from datetime import datetime

def test_roe_calculation():
    """测试ROE计算功能"""

    print("=" * 80)
    print("ROE功能测试")
    print("=" * 80)

    calculator = ApexCalculator()

    # 测试1: 正常ROE计算
    print("\n测试1: 正常用户地址")
    print("-" * 80)
    test_address = "0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf"

    try:
        roe_metrics = calculator.calculate_24h_roe(test_address, force_refresh=True)

        print(f"✓ ROE计算成功")
        print(f"  period: {roe_metrics.period}")
        print(f"  is_valid: {roe_metrics.is_valid}")
        print(f"  roe_percent: {roe_metrics.roe_percent:.2f}%")
        print(f"  start_equity: ${roe_metrics.start_equity:,.2f}")
        print(f"  current_equity: ${roe_metrics.current_equity:,.2f}")
        print(f"  pnl: ${roe_metrics.pnl:,.2f}")
        print(f"  is_sufficient_history: {roe_metrics.is_sufficient_history}")

        if roe_metrics.error_message:
            print(f"  warning: {roe_metrics.error_message}")

        if roe_metrics.period_hours:
            print(f"  period_hours: {roe_metrics.period_hours:.1f}h")

    except Exception as e:
        print(f"✗ 测试失败: {e}")

    # 测试2: 缓存机制
    print("\n测试2: 缓存机制")
    print("-" * 80)

    try:
        # 第一次调用（应该从API获取）
        print("第一次调用（从API获取）...")
        roe1 = calculator.calculate_24h_roe(test_address, force_refresh=False)

        # 第二次调用（应该使用缓存）
        print("第二次调用（使用缓存）...")
        roe2 = calculator.calculate_24h_roe(test_address, force_refresh=False)

        if roe1.roe_percent == roe2.roe_percent:
            print("✓ 缓存机制正常工作")
        else:
            print("⚠️ 两次调用结果不一致")

    except Exception as e:
        print(f"✗ 测试失败: {e}")

    # 测试3: 强制刷新
    print("\n测试3: 强制刷新缓存")
    print("-" * 80)

    try:
        print("force_refresh=True...")
        roe3 = calculator.calculate_24h_roe(test_address, force_refresh=True)
        print("✓ 强制刷新成功")
        print(f"  新的ROE: {roe3.roe_percent:.2f}%")

    except Exception as e:
        print(f"✗ 测试失败: {e}")

    # 测试4: 无效地址（边界测试）
    print("\n测试4: 无效地址")
    print("-" * 80)

    invalid_address = "0x0000000000000000000000000000000000000000"

    try:
        roe_invalid = calculator.calculate_24h_roe(invalid_address, force_refresh=True)

        if not roe_invalid.is_valid:
            print("✓ 正确处理无效地址")
            print(f"  error_message: {roe_invalid.error_message}")
        else:
            print("⚠️ 未检测到无效地址")

    except Exception as e:
        print(f"✓ 正确抛出异常: {str(e)[:100]}")

    # 测试5: 数据类验证
    print("\n测试5: ROEMetrics数据类验证")
    print("-" * 80)

    try:
        test_roe = ROEMetrics(
            period='24h',
            period_label='24小时',
            roe_percent=2.5,
            start_equity=10000.0,
            current_equity=10250.0,
            pnl=250.0,
            start_time=datetime.now(),
            end_time=datetime.now(),
            is_valid=True
        )

        print("✓ ROEMetrics数据类创建成功")
        print(f"  period: {test_roe.period}")
        print(f"  roe_percent: {test_roe.roe_percent}%")
        print(f"  is_valid: {test_roe.is_valid}")

    except Exception as e:
        print(f"✗ 数据类测试失败: {e}")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    test_roe_calculation()
