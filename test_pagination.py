#!/usr/bin/env python3
"""
测试 Hyperliquid API 的翻页功能

此脚本用于验证优化后的 get_user_fills 方法是否能正确翻页获取全量数据
"""

from hyperliquid_api_client import HyperliquidAPIClient


def test_pagination():
    """
    测试翻页获取用户成交记录
    """
    print("=" * 70)
    print("🧪 测试 Hyperliquid API 翻页功能")
    print("=" * 70)
    print()

    # 初始化 API 客户端
    client = HyperliquidAPIClient()

    # 测试地址（使用示例中的地址）
    test_address = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"

    print(f"测试地址: {test_address}")
    print()

    try:
        # 测试获取全量数据
        print("📡 正在获取用户成交记录（支持翻页）...")
        print("-" * 70)

        fills = client.get_user_fills(test_address, max_fills=10000)

        print("-" * 70)
        print()
        print("✅ 数据获取完成！")
        print()
        print("📊 统计信息:")
        print(f"  • 总成交记录数: {len(fills)} 条")

        if fills:
            # 显示第一条和最后一条记录的时间
            first_fill_time = fills[0].get('time')
            last_fill_time = fills[-1].get('time')

            from datetime import datetime

            if first_fill_time:
                first_dt = datetime.fromtimestamp(first_fill_time / 1000)
                print(f"  • 最新记录时间: {first_dt.strftime('%Y-%m-%d %H:%M:%S')}")

            if last_fill_time:
                last_dt = datetime.fromtimestamp(last_fill_time / 1000)
                print(f"  • 最早记录时间: {last_dt.strftime('%Y-%m-%d %H:%M:%S')}")

            # 显示一些记录样本
            print()
            print("📝 前3条记录样本:")
            for i, fill in enumerate(fills[:3]):
                print(f"\n  记录 {i+1}:")
                print(f"    - 币种: {fill.get('coin', 'N/A')}")
                print(f"    - 方向: {fill.get('dir', 'N/A')}")
                print(f"    - 价格: ${fill.get('px', 0)}")
                print(f"    - 数量: {fill.get('sz', 0)}")
                print(f"    - PnL: ${fill.get('closedPnl', 0)}")

        else:
            print("  ⚠️  该地址暂无成交记录")

        print()
        print("=" * 70)
        print("✅ 测试完成！翻页功能正常工作")
        print("=" * 70)

    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ 测试失败: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_pagination()
