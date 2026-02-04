#!/usr/bin/env python3
"""
检查Portfolio API返回的完整数据结构
"""

from hyperliquid_api_client import HyperliquidAPIClient
import json

client = HyperliquidAPIClient()
test_address = "0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf"

print("正在获取Portfolio API数据...")
print("=" * 80)

payload = {"type": "portfolio", "user": test_address}
response = client._make_request("/info", payload)

print(f"\n响应类型: {type(response)}")
print(f"响应长度: {len(response) if isinstance(response, list) else 'N/A'}")

if isinstance(response, list):
    for i, item in enumerate(response):
        if isinstance(item, list) and len(item) >= 2:
            period = item[0]
            data = item[1]
            print(f"\n{'='*80}")
            print(f"Period {i}: {period}")
            print(f"{'='*80}")

            if isinstance(data, dict):
                print(f"Keys: {list(data.keys())}")

                # 检查pnlHistory和accountValueHistory的长度
                if "pnlHistory" in data:
                    pnl_hist = data["pnlHistory"]
                    print(f"  pnlHistory: {len(pnl_hist)} 条记录")
                    if len(pnl_hist) > 0:
                        print(f"    第一条: {pnl_hist[0]}")
                        print(f"    最后一条: {pnl_hist[-1]}")

                if "accountValueHistory" in data:
                    acc_hist = data["accountValueHistory"]
                    print(f"  accountValueHistory: {len(acc_hist)} 条记录")
                    if len(acc_hist) > 0:
                        print(f"    第一条: {acc_hist[0]}")
                        print(f"    最后一条: {acc_hist[-1]}")

print("\n" + "=" * 80)
print("检查完成")
