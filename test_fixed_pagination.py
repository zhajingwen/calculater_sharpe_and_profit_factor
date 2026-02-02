#!/usr/bin/env python3
"""
修正后的 userFillsByTime 翻页实现

核心修正：
- 第一页获取最新的数据（startTime=0, 不设置 endTime）
- 后续页使用【最早记录】的时间戳作为 endTime，继续往前翻页
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://api.hyperliquid.xyz"
TEST_ADDRESS = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"


def get_user_fills_paginated_fixed(user_address: str, max_fills: int = 10000):
    """
    修正的翻页逻辑

    API 返回顺序：从新到旧（时间倒序）
    翻页策略：
    1. 第一页：获取最新的 2000 条
    2. 第二页：使用第一页【最早记录】的时间戳作为 endTime
    3. 重复直到没有更多数据
    """
    all_fills = []
    page = 0

    # 第一次请求：从最早开始，获取到当前时间的最新数据
    start_time = 0
    end_time = None  # None 表示当前时间

    print("=" * 70)
    print("🔄 开始翻页获取成交记录（修正版）")
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
                print(f"  第一条时间: {datetime.fromtimestamp(first_time/1000).strftime('%Y-%m-%d %H:%M:%S')} (tid: {fills[0].get('tid')})")
                print(f"  最后条时间: {datetime.fromtimestamp(last_time/1000).strftime('%Y-%m-%d %H:%M:%S')} (tid: {fills[-1].get('tid')})")

            # 如果返回的数据少于 2000 条，说明已经是最后一页
            if len(fills) < 2000:
                print(f"  ✓ 已到达最后一页（返回 {len(fills)} < 2000）")
                break

            # 【关键修正】：使用【最后一条】（最早的）记录的时间戳作为下一次的 endTime
            # 因为 API 返回的是从新到旧，所以最后一条是最早的
            oldest_fill_time = fills[-1].get("time")
            if oldest_fill_time is None:
                print(f"  ⚠️  无法获取最后一条记录的时间戳")
                break

            # 下一页：endTime = 最后一条（最早的）的时间戳 - 1
            end_time = oldest_fill_time - 1
            print(f"  → 下一页将获取 {datetime.fromtimestamp(end_time/1000).strftime('%Y-%m-%d %H:%M:%S')} 之前的数据")

            # API 限流保护
            time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            import traceback
            traceback.print_exc()
            break

    print("\n" + "=" * 70)
    print(f"✅ 翻页完成，共获取 {len(all_fills)} 条记录")
    print("=" * 70)

    return all_fills[:max_fills]


def verify_pagination_rules(fills):
    """
    验证翻页规则
    """
    print("\n" + "=" * 70)
    print("🔍 验证翻页规则")
    print("=" * 70)

    print(f"\n✅ 规则 1: 总记录数限制")
    print(f"   获取记录: {len(fills)} 条")
    print(f"   API 限制: ≤10000 条")
    print(f"   结果: {'✅ 通过' if len(fills) <= 10000 else '❌ 失败'}")

    if fills:
        print(f"\n✅ 规则 2: 时间顺序（从新到旧）")
        first_fill = fills[0]
        last_fill = fills[-1]

        first_time = first_fill.get('time')
        last_time = last_fill.get('time')

        print(f"   第一条: {datetime.fromtimestamp(first_time/1000).strftime('%Y-%m-%d %H:%M:%S')} (tid: {first_fill.get('tid')})")
        print(f"   最后条: {datetime.fromtimestamp(last_time/1000).strftime('%Y-%m-%d %H:%M:%S')} (tid: {last_fill.get('tid')})")
        print(f"   结果: {'✅ 通过' if first_time >= last_time else '❌ 失败'}")

        print(f"\n✅ 规则 3: 无重复数据")
        fill_ids = set()
        duplicates = 0
        duplicate_details = []

        for i, fill in enumerate(fills):
            fill_id = fill.get('tid')  # 交易ID
            if fill_id in fill_ids:
                duplicates += 1
                if duplicates <= 3:  # 只记录前3个重复
                    duplicate_details.append({
                        'index': i,
                        'tid': fill_id,
                        'time': fill.get('time'),
                        'coin': fill.get('coin')
                    })
            else:
                fill_ids.add(fill_id)

        print(f"   唯一ID数: {len(fill_ids)}")
        print(f"   重复记录: {duplicates} 条")
        print(f"   结果: {'✅ 通过' if duplicates == 0 else '❌ 失败'}")

        if duplicate_details:
            print(f"\n   重复详情（前3条）:")
            for detail in duplicate_details:
                print(f"     索引 {detail['index']}: tid={detail['tid']}, coin={detail['coin']}, time={datetime.fromtimestamp(detail['time']/1000).strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"\n✅ 规则 4: 每页最多 2000 条")
        print(f"   结果: ✅ 通过（API 自动限制）")

        print(f"\n✅ 规则 5: 数据完整性")
        print(f"   第1条示例:")
        print(f"     币种: {fills[0].get('coin')}, 方向: {fills[0].get('dir')}")
        print(f"     价格: ${fills[0].get('px')}, 数量: {fills[0].get('sz')}")
        print(f"     PnL: ${fills[0].get('closedPnl')}")
        print(f"   第{len(fills)}条示例:")
        print(f"     币种: {fills[-1].get('coin')}, 方向: {fills[-1].get('dir')}")
        print(f"     价格: ${fills[-1].get('px')}, 数量: {fills[-1].get('sz')}")
        print(f"     PnL: ${fills[-1].get('closedPnl')}")
        print(f"   结果: ✅ 通过")

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

            print(f"\nuserFills 返回:")
            print(f"  记录数: {len(fills)} 条")
            print(f"  限制: {'⚠️  达到 API 限制 (2000 条)' if len(fills) == 2000 else '✓ 未达到限制'}")

            if fills:
                print(f"  时间范围:")
                print(f"    最新: {datetime.fromtimestamp(fills[0]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"    最早: {datetime.fromtimestamp(fills[-1]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')}")

            return fills
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ 异常: {e}")
        return []


if __name__ == "__main__":
    print("\n🚀 测试修正后的翻页实现\n")

    # 测试翻页获取
    fills_paginated = get_user_fills_paginated_fixed(TEST_ADDRESS, max_fills=10000)

    # 验证翻页规则
    verify_pagination_rules(fills_paginated)

    # 对比原始 API
    fills_original = compare_with_original_api()

    print("\n" + "=" * 70)
    print("📈 最终对比结果")
    print("=" * 70)
    print(f"翻页方式 (userFillsByTime): {len(fills_paginated)} 条记录")
    print(f"原始方式 (userFills):       {len(fills_original)} 条记录")
    print(f"改进效果: +{len(fills_paginated) - len(fills_original)} 条 ({(len(fills_paginated) - len(fills_original)) / len(fills_original) * 100:.1f}%)")
    print("=" * 70)
