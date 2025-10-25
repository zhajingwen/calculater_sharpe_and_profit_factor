"""
Hyperliquid API Client
基于官方API文档实现的数据获取客户端
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
"""

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time


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
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送POST请求到Hyperliquid API
        
        Args:
            endpoint: API端点
            payload: 请求载荷
            
        Returns:
            API响应数据
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON解析失败: {e}")
    
    def get_user_fills(self, user_address: str) -> List[Dict[str, Any]]:
        """
        获取用户成交记录
        
        Args:
            user_address: 用户地址
            
        Returns:
            成交记录列表
        """
        payload = {
            "type": "userFills",
            "user": user_address
        }
        
        response = self._make_request("/info", payload)
        if isinstance(response, list):
            return response
        return response.get("fills", [])
    
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
        return user_state.get("clearinghouseState", {}).get("assetPositions", [])
    
    def get_user_margin_summary(self, user_address: str) -> Dict[str, Any]:
        """
        获取用户保证金摘要
        
        Args:
            user_address: 用户地址
            
        Returns:
            保证金摘要数据
        """
        user_state = self.get_user_state(user_address)
        return user_state.get("clearinghouseState", {}).get("marginSummary", {})
    
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
        
        Args:
            user_address: 用户地址
            
        Returns:
            完整的投资组合数据
        """
        print(f"正在获取用户 {user_address} 的投资组合数据...")
        
        try:
            # 获取所有相关数据
            fills = self.get_user_fills(user_address)
            user_state = self.get_user_state(user_address)
            asset_positions = self.get_user_asset_positions(user_address)
            margin_summary = self.get_user_margin_summary(user_address)
            open_orders = self.get_user_open_orders(user_address)
            twap_fills = self.get_user_twap_slice_fills(user_address)
            
            # 数据验证完成
            
            # 确保所有数据都是列表或字典
            if not isinstance(fills, list):
                fills = []
            if not isinstance(asset_positions, list):
                asset_positions = []
            if not isinstance(open_orders, list):
                open_orders = []
            if not isinstance(twap_fills, list):
                twap_fills = []
            
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
            
            # 确保user_state是字典
            if not isinstance(user_state, dict):
                user_state = {}
            if not isinstance(margin_summary, dict):
                margin_summary = {}
            
            # 更新portfolio_data中的user_state和margin_summary
            portfolio_data["userState"] = user_state
            portfolio_data["marginSummary"] = margin_summary
            
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
    测试API客户端
    """
    client = HyperliquidAPIClient()
    
    # 测试地址（请替换为真实地址）
    test_address = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"
    
    if client.validate_user_address(test_address):
        print(f"测试地址格式有效: {test_address}")
        
        try:
            # 获取投资组合数据
            portfolio_data = client.get_user_portfolio_data(test_address)
            
            if portfolio_data:
                print("\n=== 投资组合数据摘要 ===")
                print(f"成交记录数量: {len(portfolio_data.get('fills', []))}")
                print(f"持仓数量: {len(portfolio_data.get('assetPositions', []))}")
                print(f"未成交订单: {len(portfolio_data.get('openOrders', []))}")
                
                margin_summary = portfolio_data.get('marginSummary', {})
                if margin_summary:
                    print(f"账户价值: ${margin_summary.get('accountValue', 0):,.2f}")
                    print(f"已用保证金: ${margin_summary.get('totalMarginUsed', 0):,.2f}")
            else:
                print("未能获取投资组合数据")
            # print(portfolio_data)
        except Exception as e:
            print(f"测试失败: {e}")
    else:
        print(f"测试地址格式无效: {test_address}")


if __name__ == "__main__":
    main()
