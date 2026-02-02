#!/usr/bin/env python3
"""
测试正确的 userFillsByTime 翻页实现
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://api.hyperliquid.xyz"
TEST_ADDRESS = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"


def get_user_fills_paginated(user_address: str, max_fills: int = 10000):
    """
    使用 userFillsByTime 翻页获取全量数据

    根据 API 文档：
    - startTime 是必需参数
    - 每次最多返回 2000 条记录
    - 只能获取最近 10000 条记录
    """
    all_fills = []
    page = 0

    # 第一次请求：从很早的时间开始（0 表示最早）
    start_time = 0
    end_time = None  # None 表示当前时间

    print("=" * 70)
    print("🔄 开始翻页获取成交记录")
    print("=" * 70)

    while len(all_fills) < max_fills:
        page += 1

        payload = {
            "type": "userFillsByTime",
            "user": user_address,
            "startTime": start_time
        }

        if end_time is not None:
            payload["endTime"] = end_time

        print(f"\n📄 第 {page} 页:")
        print(f"  startTime: {start_time} ({datetime.fromtimestamp(start_time/1000).strftime('%Y-%m-%d %H:%M:%S') if start_time > 0 else '最早'})")
        if end_time:
            print(f"  endTime: {end_time} ({datetime.fromtimestamp(end_time/1000).strftime('%Y-%m-%d %H:%M:%S')})")

        try:
            response = requests.post(
                f"{BASE_URL}/info",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            if response.status_code != 200:
                print(f"  ❌ 请求失败: {response.status_code}")
                print(f"  响应: {response.text}")
                break

            data = response.json()

            if isinstance(data, list):
                fills = data
            else:
                fills = data.get("fills", [])

            if not fills:
                print(f"  ✓ 没有更多数据")
                break

            all_fills.extend(fills)
            print(f"  ✓ 获取 {len(fills)} 条记录，累计 {len(all_fills)} 条")

            if fills:
                first_time = fills[0].get('time')
                last_time = fills[-1].get('time')
                print(f"  时间范围: {datetime.fromtimestamp(last_time/1000).strftime('%Y-%m-%d %H:%M:%S')} ~ {datetime.fromtimestamp(first_time/1000).strftime('%Y-%m-%d %H:%M:%S')}")

            # 如果返回的数据少于 2000 条，说明已经是最后一页
            if len(fills) < 2000:
                print(f"  ✓ 已到达最后一页（返回 {len(fills)} < 2000）")
                break

            # 使用最后一条记录的时间戳作为下一次的 endTime
            last_fill_time = fills[-1].get("time")
            if last_fill_time is None:
                print(f"  ⚠️  无法获取最后一条记录的时间戳")
                break

            # 下一页：endTime = 最后一条的时间戳 - 1，startTime 保持为 0
            end_time = last_fill_time - 1

            # API 限流保护
            time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            break

    print("\n" + "=" * 70)
    print(f"✅ 翻页完成")
    print("=" * 70)

    return all_fills[:max_fills]


def verify_pagination_rules(fills):
    """
    验证翻页规则
    """
    print("\n" + "=" * 70)
    print("🔍 验证翻页规则")
    print("=" * 70)

    print(f"\n1️⃣  总记录数验证:")
    print(f"   获取记录: {len(fills)} 条")
    if len(fills) <= 10000:
        print(f"   ✅ 符合 API 限制（≤10000 条）")
    else:
        print(f"   ⚠️  超过 API 限制（>10000 条）")

    if fills:
        print(f"\n2️⃣  时间戳验证:")
        first_fill = fills[0]
        last_fill = fills[-1]

        first_time = first_fill.get('time')
        last_time = last_fill.get('time')

        print(f"   最新记录: {datetime.fromtimestamp(first_time/1000).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   最早记录: {datetime.fromtimestamp(last_time/1000).strftime('%Y-%m-%d %H:%M:%S')}")

        if first_time >= last_time:
            print(f"   ✅ 时间顺序正确（从新到旧）")
        else:
            print(f"   ❌ 时间顺序错误")

        print(f"\n3️⃣  重复数据检查:")
        fill_ids = set()
        duplicates = 0

        for fill in fills:
            fill_id = fill.get('tid')  # 交易ID
            if fill_id in fill_ids:
                duplicates += 1
            else:
                fill_ids.add(fill_id)

        if duplicates == 0:
            print(f"   ✅ 无重复数据")
        else:
            print(f"   ⚠️  发现 {duplicates} 条重复记录")

        print(f"\n4️⃣  数据样本:")
        print(f"   第1条:")
        print(f"     币种: {fills[0].get('coin')}")
        print(f"     方向: {fills[0].get('dir')}")
        print(f"     价格: ${fills[0].get('px')}")
        print(f"     数量: {fills[0].get('sz')}")
        print(f"     PnL: ${fills[0].get('closedPnl')}")

        print(f"\n   第{len(fills)}条:")
        print(f"     币种: {fills[-1].get('coin')}")
        print(f"     方向: {fills[-1].get('dir')}")
        print(f"     价格: ${fills[-1].get('px')}")
        print(f"     数量: {fills[-1].get('sz')}")
        print(f"     PnL: ${fills[-1].get('closedPnl')}")

    print("\n" + "=" * 70)


def compare_with_original_api():
    """
    对比原始 userFills API
    """
    print("\n" + "=" * 70)
    print("📊 对比原始 userFills API")
    print("=" * 70)

    payload = {
        "type": "userFills",
        "user": TEST_ADDRESS
    }

    try:
        response = requests.post(
            f"{BASE_URL}/info",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()

            if isinstance(data, list):
                fills = data
            else:
                fills = data.get("fills", [])

            print(f"\nuserFills 返回记录数: {len(fills)}")

            if len(fills) == 2000:
                print(f"⚠️  返回 2000 条（可能是 API 限制）")
            else:
                print(f"✓ 返回 {len(fills)} 条")

            return fills
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ 异常: {e}")
        return []


if __name__ == "__main__":
    print("\n🚀 测试正确的翻页实现\n")

    # 测试翻页获取
    fills_paginated = get_user_fills_paginated(TEST_ADDRESS, max_fills=10000)

    # 验证翻页规则
    verify_pagination_rules(fills_paginated)

    # 对比原始 API
    fills_original = compare_with_original_api()

    print("\n" + "=" * 70)
    print("📈 最终对比")
    print("=" * 70)
    print(f"翻页方式 (userFillsByTime): {len(fills_paginated)} 条记录")
    print(f"原始方式 (userFills): {len(fills_original)} 条记录")
    print("=" * 70)
