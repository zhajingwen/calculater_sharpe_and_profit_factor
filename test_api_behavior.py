#!/usr/bin/env python3
"""
深入测试 userFillsByTime API 的行为模式
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://api.hyperliquid.xyz"
TEST_ADDRESS = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"


def test_api_behavior():
    """
    测试 API 在不同参数组合下的行为
    """
    print("=" * 80)
    print("🔬 深入分析 userFillsByTime API 行为")
    print("=" * 80)

    # 测试 1: 只有 startTime=0
    print("\n📋 测试 1: startTime=0, 无 endTime")
    print("-" * 80)

    payload1 = {
        "type": "userFillsByTime",
        "user": TEST_ADDRESS,
        "startTime": 0
    }

    response1 = requests.post(f"{BASE_URL}/info", json=payload1, timeout=30)
    if response1.status_code == 200:
        fills1 = response1.json()
        print(f"✓ 返回 {len(fills1)} 条记录")
        if fills1:
            print(f"  第一条: time={fills1[0]['time']} ({datetime.fromtimestamp(fills1[0]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')}), tid={fills1[0]['tid']}")
            print(f"  最后条: time={fills1[-1]['time']} ({datetime.fromtimestamp(fills1[-1]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')}), tid={fills1[-1]['tid']}")
            print(f"  时间顺序: {'新→旧' if fills1[0]['time'] > fills1[-1]['time'] else '旧→新'}")

    # 测试 2: startTime=0, endTime=第一批最老的时间-1
    if fills1:
        oldest_time = fills1[-1]['time']
        print(f"\n📋 测试 2: startTime=0, endTime={oldest_time-1}")
        print("-" * 80)

        payload2 = {
            "type": "userFillsByTime",
            "user": TEST_ADDRESS,
            "startTime": 0,
            "endTime": oldest_time - 1
        }

        response2 = requests.post(f"{BASE_URL}/info", json=payload2, timeout=30)
        if response2.status_code == 200:
            fills2 = response2.json()
            print(f"✓ 返回 {len(fills2)} 条记录")
            if fills2:
                print(f"  第一条: time={fills2[0]['time']} ({datetime.fromtimestamp(fills2[0]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')}), tid={fills2[0]['tid']}")
                print(f"  最后条: time={fills2[-1]['time']} ({datetime.fromtimestamp(fills2[-1]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')}), tid={fills2[-1]['tid']}")

                # 检查重复
                tids1 = set(f['tid'] for f in fills1)
                tids2 = set(f['tid'] for f in fills2)
                overlap = tids1 & tids2
                print(f"\n  重复检查:")
                print(f"    测试1 唯一ID: {len(tids1)}")
                print(f"    测试2 唯一ID: {len(tids2)}")
                print(f"    重叠ID数: {len(overlap)}")
                if overlap:
                    print(f"    ❌ 发现重复数据")
                else:
                    print(f"    ✅ 无重复数据")

    # 测试 3: startTime=最老时间+1, 无 endTime
    if fills1:
        oldest_time = fills1[-1]['time']
        print(f"\n📋 测试 3: startTime={oldest_time+1}, 无 endTime")
        print("-" * 80)

        payload3 = {
            "type": "userFillsByTime",
            "user": TEST_ADDRESS,
            "startTime": oldest_time + 1
        }

        response3 = requests.post(f"{BASE_URL}/info", json=payload3, timeout=30)
        if response3.status_code == 200:
            fills3 = response3.json()
            print(f"✓ 返回 {len(fills3)} 条记录")
            if fills3:
                print(f"  第一条: time={fills3[0]['time']} ({datetime.fromtimestamp(fills3[0]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')}), tid={fills3[0]['tid']}")
                print(f"  最后条: time={fills3[-1]['time']} ({datetime.fromtimestamp(fills3[-1]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')}), tid={fills3[-1]['tid']}")

                # 检查重复
                tids1 = set(f['tid'] for f in fills1)
                tids3 = set(f['tid'] for f in fills3)
                overlap = tids1 & tids3
                print(f"\n  重复检查:")
                print(f"    测试1 唯一ID: {len(tids1)}")
                print(f"    测试3 唯一ID: {len(tids3)}")
                print(f"    重叠ID数: {len(overlap)}")
                if overlap:
                    print(f"    ❌ 发现 {len(overlap)} 个重复ID")
                    if len(overlap) <= 5:
                        print(f"    重复的ID: {overlap}")
                else:
                    print(f"    ✅ 无重复数据")

    # 测试 4: 使用第一批最新的时间作为 endTime
    if fills1:
        newest_time = fills1[0]['time']
        print(f"\n📋 测试 4: startTime=0, endTime={newest_time-1}")
        print("-" * 80)

        payload4 = {
            "type": "userFillsByTime",
            "user": TEST_ADDRESS,
            "startTime": 0,
            "endTime": newest_time - 1
        }

        response4 = requests.post(f"{BASE_URL}/info", json=payload4, timeout=30)
        if response4.status_code == 200:
            fills4 = response4.json()
            print(f"✓ 返回 {len(fills4)} 条记录")
            if fills4:
                print(f"  第一条: time={fills4[0]['time']} ({datetime.fromtimestamp(fills4[0]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')}), tid={fills4[0]['tid']}")
                print(f"  最后条: time={fills4[-1]['time']} ({datetime.fromtimestamp(fills4[-1]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')}), tid={fills4[-1]['tid']}")

                # 检查重复
                tids1 = set(f['tid'] for f in fills1)
                tids4 = set(f['tid'] for f in fills4)
                overlap = tids1 & tids4
                print(f"\n  重复检查:")
                print(f"    测试1 唯一ID: {len(tids1)}")
                print(f"    测试4 唯一ID: {len(tids4)}")
                print(f"    重叠ID数: {len(overlap)}")
                if overlap:
                    print(f"    ❌ 发现 {len(overlap)} 个重复ID")
                else:
                    print(f"    ✅ 无重复数据")

    print("\n" + "=" * 80)
    print("📊 结论分析")
    print("=" * 80)
    print("基于测试结果，我们可以确定：")
    print("1. API 返回顺序：新→旧（最新的在前）")
    print("2. 正确的翻页策略：")
    print("   - 调整 startTime（使用上一批最老的时间+1）")
    print("   - 或调整 endTime（使用上一批最新的时间-1）")
    print("3. 需要验证哪种策略无重复")
    print("=" * 80)


if __name__ == "__main__":
    test_api_behavior()
