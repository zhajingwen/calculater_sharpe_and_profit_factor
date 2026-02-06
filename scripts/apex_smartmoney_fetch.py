#!/usr/bin/env python3
"""
Apex Liquid Smart Money 数据获取脚本
获取 backTest30Day 排行榜数据
"""

import requests
import json
import os


def fetch_backtest_30day():
    url = "https://apexliquid.bot/v1/web/backTest30Day"

    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://apexliquid.bot",
        "pragma": "no-cache",
        "referer": "https://apexliquid.bot/trade/topTraders",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    }

    payload = {
        "pagination": {
            "page_number": 1,
            "page_size": 2000
        },
        "sort_options": [
            {
                "field": "backTest30Day",
                "descending": True
            }
        ],
        "time_range": "DAY",
        "telegram_id": ""
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()


def fetch_address_tab_recommend():
    """获取 recommend tab 的地址数据"""
    url = "https://apexliquid.bot/v1/web/address_tab_address"

    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://apexliquid.bot",
        "pragma": "no-cache",
        "referer": "https://apexliquid.bot/trade/topTraders",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    }

    payload = {
        "pagination": {
            "page_number": 1,
            "page_size": 2000
        },
        "sort_options": [
            {
                "field": "backTest30Day",
                "descending": True
            }
        ],
        "time_range": "DAY",
        "telegram_id": "",
        "tab_code": "recommend"
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()


def fetch_position_bias(side=1):
    """获取 position_bias 数据，side=1 做多，side=2 做空"""
    url = "https://apexliquid.bot/v1/web/position_bias"

    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://apexliquid.bot",
        "pragma": "no-cache",
        "referer": "https://apexliquid.bot/trade/topTraders",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    }

    payload = {
        "pagination": {
            "page_number": 1,
            "page_size": 10000
        },
        "sort_options": [
            {
                "field": "monthRoe",
                "descending": True
            }
        ],
        "time_range": "DAY",
        "telegram_id": "",
        "side": side
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()


def fetch_hot_follow():
    """获取 hot_follow 热门跟单数据"""
    url = "https://apexliquid.bot/v1/web/hot_follow"

    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://apexliquid.bot",
        "pragma": "no-cache",
        "referer": "https://apexliquid.bot/trade/topTraders",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    }

    payload = {
        "pagination": {
            "page_number": 1,
            "page_size": 2000
        },
        "sort_options": [
            {
                "field": "backTest30Day",
                "descending": True
            }
        ],
        "time_range": "DAY",
        "telegram_id": ""
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()


def fetch_top_trades():
    """获取 top_trades 顶级交易者数据"""
    url = "https://apexliquid.bot/v1/web/top_trades"

    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "dnt": "1",
        "origin": "https://apexliquid.bot",
        "pragma": "no-cache",
        "referer": "https://apexliquid.bot/trade/topTraders",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    }

    payload = {
        "pagination": {
            "page_number": 1,
            "page_size": 10000
        },
        "sort_options": [
            {
                "field": "monthRoe",
                "descending": True
            }
        ],
        "time_range": "DAY",
        "telegram_id": ""
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 获取 backTest30Day 数据
    data1 = fetch_backtest_30day()
    addresses1 = [trade["address"] for trade in data1["data"]["trades"]]
    output_path1 = os.path.join(script_dir, "addresses.txt")
    with open(output_path1, "w") as f:
        for addr in addresses1:
            f.write(addr + "\n")
    print(f"[backTest30Day] 共获取 {len(addresses1)} 个地址，已保存到 {output_path1}")

    # 获取 recommend tab 数据
    data2 = fetch_address_tab_recommend()
    addresses2 = [trade["address"] for trade in data2["data"]["trades"]]
    output_path2 = os.path.join(script_dir, "addresses_recommend.txt")
    with open(output_path2, "w") as f:
        for addr in addresses2:
            f.write(addr + "\n")
    print(f"[recommend] 共获取 {len(addresses2)} 个地址，已保存到 {output_path2}")

    # 获取 position_bias 数据 (side=1 做多)
    data3 = fetch_position_bias(side=1)
    addresses3 = [trade["address"] for trade in data3["data"]["trades"]]
    output_path3 = os.path.join(script_dir, "addresses_position_bias_long.txt")
    with open(output_path3, "w") as f:
        for addr in addresses3:
            f.write(addr + "\n")
    print(f"[position_bias_long] 共获取 {len(addresses3)} 个地址，已保存到 {output_path3}")

    # 获取 position_bias 数据 (side=2 做空)
    data4 = fetch_position_bias(side=2)
    addresses4 = [trade["address"] for trade in data4["data"]["trades"]]
    output_path4 = os.path.join(script_dir, "addresses_position_bias_short.txt")
    with open(output_path4, "w") as f:
        for addr in addresses4:
            f.write(addr + "\n")
    print(f"[position_bias_short] 共获取 {len(addresses4)} 个地址，已保存到 {output_path4}")

    # 获取 hot_follow 热门跟单数据
    data5 = fetch_hot_follow()
    addresses5 = [trade["address"] for trade in data5["data"]["trades"]]
    output_path5 = os.path.join(script_dir, "addresses_hot_follow.txt")
    with open(output_path5, "w") as f:
        for addr in addresses5:
            f.write(addr + "\n")
    print(f"[hot_follow] 共获取 {len(addresses5)} 个地址，已保存到 {output_path5}")

    # 获取 top_trades 顶级交易者数据
    data6 = fetch_top_trades()
    addresses6 = [trade["address"] for trade in data6["data"]["trades"]]
    output_path6 = os.path.join(script_dir, "addresses_top_trades.txt")
    with open(output_path6, "w") as f:
        for addr in addresses6:
            f.write(addr + "\n")
    print(f"[top_trades] 共获取 {len(addresses6)} 个地址，已保存到 {output_path6}")

    # 合并所有地址并去重
    all_addresses = set(addresses1 + addresses2 + addresses3 + addresses4 + addresses5 + addresses6)
    output_path_all = os.path.join(script_dir, "addresses_all.txt")
    with open(output_path_all, "w") as f:
        for addr in sorted(all_addresses):
            f.write(addr + "\n")
    print(f"\n[合并] 共 {len(all_addresses)} 个唯一地址，已保存到 {output_path_all}")
