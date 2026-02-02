#!/usr/bin/env python3
"""
调试 Hyperliquid API 请求格式
"""

import requests
import json
import time

BASE_URL = "https://api.hyperliquid.xyz"
TEST_ADDRESS = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"


def test_user_fills():
    """测试原始的 userFills 端点"""
    print("=" * 70)
    print("🧪 测试 1: userFills 端点（原始方式）")
    print("=" * 70)

    payload = {
        "type": "userFills",
        "user": TEST_ADDRESS
    }

    print(f"请求 URL: {BASE_URL}/info")
    print(f"请求 Payload: {json.dumps(payload, indent=2)}")
    print()

    try:
        response = requests.post(
            f"{BASE_URL}/info",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        print(f"响应状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if isinstance(data, list):
                fills = data
            else:
                fills = data.get("fills", [])

            print(f"✅ 成功获取 {len(fills)} 条记录")

            if fills:
                print(f"\n第一条记录:")
                print(json.dumps(fills[0], indent=2))
                print(f"\n最后一条记录:")
                print(json.dumps(fills[-1], indent=2))

            return fills
        else:
            print(f"❌ 请求失败")
            print(f"响应内容: {response.text}")
            return []

    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_user_fills_by_time():
    """测试 userFillsByTime 端点"""
    print("\n" + "=" * 70)
    print("🧪 测试 2: userFillsByTime 端点（翻页方式）")
    print("=" * 70)

    payload = {
        "type": "userFillsByTime",
        "user": TEST_ADDRESS
    }

    print(f"请求 URL: {BASE_URL}/info")
    print(f"请求 Payload: {json.dumps(payload, indent=2)}")
    print()

    try:
        response = requests.post(
            f"{BASE_URL}/info",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        print(f"响应状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if isinstance(data, list):
                fills = data
            else:
                fills = data.get("fills", [])

            print(f"✅ 成功获取 {len(fills)} 条记录")

            if fills:
                print(f"\n第一条记录:")
                print(json.dumps(fills[0], indent=2))
                print(f"\n最后一条记录:")
                print(json.dumps(fills[-1], indent=2))

                # 测试翻页
                print("\n" + "-" * 70)
                print("🔄 测试翻页功能...")
                print("-" * 70)

                last_time = fills[-1].get('time')
                if last_time:
                    print(f"使用最后一条记录的时间戳: {last_time}")
                    print(f"下一页的 endTime: {last_time - 1}")

                    # 请求下一页
                    time.sleep(0.5)

                    next_payload = {
                        "type": "userFillsByTime",
                        "user": TEST_ADDRESS,
                        "endTime": last_time - 1
                    }

                    print(f"\n请求下一页...")
                    print(f"请求 Payload: {json.dumps(next_payload, indent=2)}")

                    next_response = requests.post(
                        f"{BASE_URL}/info",
                        json=next_payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=30
                    )

                    print(f"响应状态码: {next_response.status_code}")

                    if next_response.status_code == 200:
                        next_data = next_response.json()

                        if isinstance(next_data, list):
                            next_fills = next_data
                        else:
                            next_fills = next_data.get("fills", [])

                        print(f"✅ 第2页成功获取 {len(next_fills)} 条记录")

                        if next_fills:
                            print(f"\n第2页第一条记录:")
                            print(json.dumps(next_fills[0], indent=2))
                    else:
                        print(f"❌ 第2页请求失败")
                        print(f"响应内容: {next_response.text}")

            return fills
        else:
            print(f"❌ 请求失败")
            print(f"响应内容: {response.text}")
            return []

    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_user_fills_by_time_with_aggregation():
    """测试 userFillsByTime 端点（带聚合参数）"""
    print("\n" + "=" * 70)
    print("🧪 测试 3: userFillsByTime 端点（带聚合参数）")
    print("=" * 70)

    payload = {
        "type": "userFillsByTime",
        "user": TEST_ADDRESS,
        "aggregateByTime": True
    }

    print(f"请求 URL: {BASE_URL}/info")
    print(f"请求 Payload: {json.dumps(payload, indent=2)}")
    print()

    try:
        response = requests.post(
            f"{BASE_URL}/info",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        print(f"响应状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功")
            print(f"响应数据类型: {type(data)}")

            if isinstance(data, list):
                print(f"获取 {len(data)} 条记录")
            elif isinstance(data, dict):
                print(f"响应字段: {list(data.keys())}")

            print(f"\n完整响应:")
            print(json.dumps(data, indent=2)[:1000])  # 只显示前1000字符

            return data
        else:
            print(f"❌ 请求失败")
            print(f"响应内容: {response.text}")
            return None

    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n🚀 开始 API 调试测试\n")

    # 测试 1: 原始端点
    fills_1 = test_user_fills()

    # 测试 2: 带时间的端点
    fills_2 = test_user_fills_by_time()

    # 测试 3: 带聚合参数的端点
    fills_3 = test_user_fills_by_time_with_aggregation()

    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    print(f"userFills: {len(fills_1) if fills_1 else 0} 条记录")
    print(f"userFillsByTime: {len(fills_2) if fills_2 else 0} 条记录")
    print("=" * 70)
