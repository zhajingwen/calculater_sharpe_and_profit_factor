"""
Hyperliquid API Client
基于官方API文档实现的数据获取客户端
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
"""

import requests
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import time
from portfolio_analyzer import PortfolioAnalyzer


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    安全地将值转换为float

    Args:
        value: 要转换的值（可能是字符串、数字或None）
        default: 转换失败时的默认值

    Returns:
        转换后的float值
    """
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    安全地将值转换为int

    Args:
        value: 要转换的值
        default: 转换失败时的默认值

    Returns:
        转换后的int值
    """
    if value is None:
        return default
    try:
        return int(float(value))  # 先转float再转int，处理"123.45"这种情况
    except (ValueError, TypeError):
        return default


class HyperliquidAPIClient:
    """
    Hyperliquid官方API客户端
    基于官方文档实现的数据获取功能
    """
    
    def __init__(self, base_url: str = "https://api.hyperliquid.xyz"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'HyperliquidAnalyzer/1.0'
        })
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any],
                      max_retries: int = 3) -> Dict[str, Any]:
        """
        发送POST请求到Hyperliquid API（带重试机制）

        Args:
            endpoint: API端点
            payload: 请求载荷
            max_retries: 最大重试次数

        Returns:
            API响应数据
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(max_retries):
            try:
                response = self.session.post(url, json=payload, timeout=30)

                # 处理429限流错误
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 2))
                    if attempt < max_retries - 1:
                        print(f"⚠️  API限流，等待{retry_after}秒后重试...")
                        time.sleep(retry_after)
                        continue
                    else:
                        raise Exception(f"API请求失败: 429 Too Many Requests")

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避: 1s, 2s, 4s
                    print(f"⚠️  请求超时，{wait_time}秒后重试 ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                raise Exception(f"API请求超时")

            except requests.exceptions.RequestException as e:
                # 5xx服务器错误才重试
                if attempt < max_retries - 1 and hasattr(e, 'response') and e.response and e.response.status_code >= 500:
                    wait_time = 2 ** attempt
                    print(f"⚠️  服务器错误，{wait_time}秒后重试 ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                raise Exception(f"API请求失败: {e}")

            except json.JSONDecodeError as e:
                raise Exception(f"JSON解析失败: {e}")

        # 如果所有重试都失败
        raise Exception(f"API请求失败: 超过最大重试次数")
    
    def get_user_fills(self, user_address: str, max_fills: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取用户成交记录（支持翻页获取全量数据）

        根据 Hyperliquid API 规则：
        - 使用 userFillsByTime 端点支持时间范围查询
        - 每次请求最多返回 2000 条记录
        - API 返回顺序：从旧到新（按时间升序）
        - 通过 startTime 参数进行翻页（向更新的时间前进）

        Args:
            user_address: 用户地址
            max_fills: 最大获取记录数（默认10000，受API限制）

        Returns:
            成交记录列表（按时间升序排列，从最早到最新）
        """
        all_fills = []
        start_time = 0  # 从最早的时间开始
        page = 0

        print(f"→ 开始获取用户成交记录...")

        while True:

            if max_fills is not None and len(all_fills) >= max_fills:
                break
            
            payload = {
                "type": "userFillsByTime",
                "user": user_address,
                "startTime": start_time
            }

            try:
                response = self._make_request("/info", payload)
            except Exception as e:
                print(f"✗ 获取第 {page + 1} 页数据失败: {e}")
                break

            # 解析响应数据
            if isinstance(response, list):
                fills = response
            else:
                fills = response.get("fills", [])

            # 没有更多数据，退出循环
            if not fills:
                print(f"✓ 已获取所有数据，共 {len(all_fills)} 条记录")
                break

            all_fills.extend(fills)
            page += 1
            print(f"  第 {page} 页: {len(fills)} 条记录，累计 {len(all_fills)} 条")

            # 如果返回的数据少于2000条，说明已经是最后一页
            if len(fills) < 2000:
                print(f"✓ 已到达最后一页，共获取 {len(all_fills)} 条记录")
                break

            # 使用最后一条记录（最新的）的时间戳+1作为下一次的 startTime
            last_fill_time = fills[-1].get("time")
            if last_fill_time is None:
                print(f"⚠️  无法获取最后一条记录的时间戳，停止翻页")
                break

            # 加1毫秒作为下一页的起始时间，避免重复获取同一条记录
            start_time = last_fill_time + 1

            # 避免API限流，每页之间延迟500ms
            time.sleep(0.5)

        return all_fills
    
    def get_user_state(self, user_address: str) -> Dict[str, Any]:
        """
        获取用户账户状态
        
        Args:
            user_address: 用户地址
            
        Returns:
            用户账户状态数据
        """
        payload = {
            "type": "clearinghouseState",
            "user": user_address
        }
        
        response = self._make_request("/info", payload)
        return response
    
    def get_user_asset_positions(self, user_address: str) -> List[Dict[str, Any]]:
        """
        获取用户资产持仓

        Args:
            user_address: 用户地址

        Returns:
            资产持仓数据
        """
        user_state = self.get_user_state(user_address)
        # 修复：assetPositions 直接在 userState 下，不在 clearinghouseState 里
        return user_state.get("assetPositions", [])
    
    def get_user_margin_summary(self, user_address: str) -> Dict[str, Any]:
        """
        获取用户保证金摘要

        Args:
            user_address: 用户地址

        Returns:
            保证金摘要数据
        """
        user_state = self.get_user_state(user_address)
        # 修复：marginSummary 直接在 userState 下，不在 clearinghouseState 里
        return user_state.get("marginSummary", {})
    
    def get_user_open_orders(self, user_address: str) -> List[Dict[str, Any]]:
        """
        获取用户未成交订单
        
        Args:
            user_address: 用户地址
            
        Returns:
            未成交订单列表
        """
        payload = {
            "type": "openOrders",
            "user": user_address
        }
        
        response = self._make_request("/info", payload)
        if isinstance(response, list):
            return response
        return response.get("orders", [])
    
    def get_user_twap_slice_fills(self, user_address: str) -> List[Dict[str, Any]]:
        """
        获取用户TWAP切片成交记录
        
        Args:
            user_address: 用户地址
            
        Returns:
            TWAP切片成交记录
        """
        try:
            payload = {
                "type": "userTwapSliceFills",
                "user": user_address
            }
            
            response = self._make_request("/info", payload)
            if isinstance(response, list):
                return response
            return response.get("fills", [])
        except Exception as e:
            print(f"获取TWAP切片成交记录失败: {e}")
            return []
    
    def get_user_portfolio_data(self, user_address: str) -> Dict[str, Any]:
        """
        获取用户完整的投资组合数据

        优化说明:
        - 添加请求间延迟避免API限流
        - 从user_state直接提取数据减少API调用
        - 避免重复请求

        Args:
            user_address: 用户地址

        Returns:
            完整的投资组合数据
        """
        print(f"正在获取用户 {user_address} 的投资组合数据...")

        try:
            # 第一批请求: 获取成交记录
            fills = self.get_user_fills(user_address)
            time.sleep(0.5)  # 延迟500ms避免限流

            # 第二批请求: 获取用户状态（包含持仓和保证金信息）
            user_state = self.get_user_state(user_address)

            # 直接从user_state提取数据，避免额外的API请求
            asset_positions = user_state.get("assetPositions", [])
            margin_summary = user_state.get("marginSummary", {})

            time.sleep(0.5)  # 延迟500ms

            # 第三批请求: 获取未成交订单
            open_orders = self.get_user_open_orders(user_address)

            time.sleep(0.5)  # 延迟500ms

            # 第四批请求: 获取TWAP数据
            twap_fills = self.get_user_twap_slice_fills(user_address)

            # 确保所有数据都是列表或字典
            if not isinstance(fills, list):
                fills = []
            if not isinstance(asset_positions, list):
                asset_positions = []
            if not isinstance(open_orders, list):
                open_orders = []
            if not isinstance(twap_fills, list):
                twap_fills = []
            if not isinstance(user_state, dict):
                user_state = {}
            if not isinstance(margin_summary, dict):
                margin_summary = {}

            # 构建完整的投资组合数据
            portfolio_data = {
                "user": user_address,
                "timestamp": int(time.time() * 1000),
                "fills": fills,
                "userState": user_state,
                "assetPositions": asset_positions,
                "marginSummary": margin_summary,
                "openOrders": open_orders,
                "twapFills": twap_fills,
            }

            print(f"成功获取数据: {len(fills)} 条成交记录, {len(asset_positions)} 个持仓")
            return portfolio_data
            
        except Exception as e:
            print(f"获取投资组合数据失败: {e}")
            return {}
    
    def validate_user_address(self, user_address: str) -> bool:
        """
        验证用户地址格式
        
        Args:
            user_address: 用户地址
            
        Returns:
            是否为有效地址
        """
        if not user_address:
            return False
        
        # 基本的地址格式验证
        if len(user_address) < 20 or not user_address.startswith('0x'):
            return False
        
        return True


def main():
    """
    测试API客户端并展示详细的投资组合分析
    """
    client = HyperliquidAPIClient()
    analyzer = PortfolioAnalyzer()

    # 测试地址（请替换为真实地址）
    test_address = "0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf"

    if not client.validate_user_address(test_address):
        print(f"❌ 测试地址格式无效: {test_address}")
        return

    print(f"✅ 测试地址格式有效: {test_address}\n")

    try:
        # 获取用户状态数据
        print("📡 正在获取用户数据...")
        user_state = client.get_user_state(user_address=test_address)

        if not user_state:
            print("❌ 未能获取用户数据")
            return

        # 解析数据
        print("📊 正在解析数据...\n")
        parsed_data = analyzer.parse_user_state(user_state)

        # 计算统计数据
        stats = analyzer.calculate_statistics(parsed_data)

        # 格式化输出
        output = analyzer.format_output(parsed_data, stats)
        print(output)

        # 额外显示原始数据摘要
        print("\n" + "=" * 80)
        print("📋 原始数据摘要")
        print("-" * 80)
        print(f"成交记录数量: {len(client.get_user_fills(test_address))}")
        print(f"未成交订单: {len(client.get_user_open_orders(test_address))}")
        print("=" * 80)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
