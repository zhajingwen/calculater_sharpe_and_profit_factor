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
                "startTime": start_time,
                "aggregateByTime": True,
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
        # assetPositions 直接在 userState 下
        return user_state.get("assetPositions", [])
    
    def get_spot_clearinghouse_state(self, user_address: str) -> Dict[str, Any]:
        """
        获取用户 Spot 清算所状态

        Args:
            user_address: 用户地址

        Returns:
            Spot 清算所状态数据
        """
        payload = {
            "type": "spotClearinghouseState",
            "user": user_address
        }

        try:
            response = self._make_request("/info", payload)
            return response
        except Exception as e:
            print(f"获取 Spot 清算所状态失败: {e}")
            return {}

    def get_user_margin_summary(self, user_address: str) -> Dict[str, Any]:
        """
        获取用户保证金摘要（包含正确的总账户价值计算）

        正确的账户价值计算公式:
        总账户价值 = Perp 账户价值 + Spot 账户价值

        Perp 账户价值:
        - 从 user_state API (clearinghouseState) 的 accountValue 获取

        Spot 账户价值:
        - 从 spotClearinghouseState API 获取
        - USDC: 使用实际余额 (1:1 美元)
        - 其他代币: 使用 entryNtl (入账价值/历史成本)
        - 注意: entryNtl 是历史成本, 不是实时市值

        Args:
            user_address: 用户地址

        Returns:
            保证金摘要数据（包含修正后的 accountValue）
        """
        # 获取 Perp 账户状态 (clearinghouseState)
        user_state = self.get_user_state(user_address)
        margin_summary = user_state.get("marginSummary", {})

        # 获取 Perp 账户价值
        perp_account_value = safe_float(margin_summary.get("accountValue", 0))

        # 获取 Spot 账户状态 (spotClearinghouseState)
        spot_state = self.get_spot_clearinghouse_state(user_address)

        # 计算 Spot 账户价值
        spot_account_value = 0.0
        balances = spot_state.get("balances", [])

        for balance in balances:
            coin = balance.get("coin", "")

            # USDC: 使用实际余额 (1:1 美元)
            if coin == "USDC":
                coin_balance = safe_float(balance.get("total", 0))
                spot_account_value += coin_balance
            else:
                # 其他代币: 使用 entryNtl (入账价值/历史成本)
                # 注意: entryNtl 是历史成本, 不是实时市值
                entry_ntl = safe_float(balance.get("entryNtl", 0))
                spot_account_value += entry_ntl

        # 计算正确的总账户价值
        total_account_value = perp_account_value + spot_account_value

        # 更新 margin_summary 中的 accountValue 为正确的总账户价值
        margin_summary_corrected = margin_summary.copy()
        margin_summary_corrected["accountValue"] = total_account_value
        margin_summary_corrected["perpAccountValue"] = perp_account_value
        margin_summary_corrected["spotAccountValue"] = spot_account_value

        return margin_summary_corrected
    
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

    def get_user_ledger(self, user_address: str, start_time: int = 0) -> List[Dict[str, Any]]:
        """
        获取用户账本记录（充值、提现、转账等）

        Args:
            user_address: 用户地址
            start_time: 起始时间戳（毫秒），默认0表示从最早开始

        Returns:
            账本记录列表
        """
        try:
            payload = {
                "type": "userNonFundingLedgerUpdates",
                "user": user_address,
                "startTime": start_time
            }

            response = self._make_request("/info", payload)
            if isinstance(response, list):
                return response
            return response.get("ledgerUpdates", [])
        except Exception as e:
            print(f"获取账本记录失败: {e}")
            return []

    def get_user_portfolio_all_periods(self, user_address: str) -> Dict[str, Dict[str, Any]]:
        """
        获取用户Portfolio所有时间周期的数据

        此API返回用户多个时间周期的账户历史数据，包括：
        - day: 24小时数据
        - week: 7天数据
        - month: 30天数据
        - allTime: 历史总计数据

        Args:
            user_address: 用户地址

        Returns:
            包含所有period数据的字典，格式为：
            {
                "day": {"pnlHistory": [...], "accountValueHistory": [...]},
                "week": {"pnlHistory": [...], "accountValueHistory": [...]},
                "month": {"pnlHistory": [...], "accountValueHistory": [...]},
                "allTime": {"pnlHistory": [...], "accountValueHistory": [...]}
            }

        Raises:
            Exception: 当API请求失败或响应格式不正确时

        注意:
            - 每个period的pnlHistory[-1]是该周期的累计PNL
            - 每个period的accountValueHistory[0]是该周期起始时的账户权益
            - allTime的起始权益可能为0（账户刚创建时）
        """
        try:
            payload = {
                "type": "portfolio",
                "user": user_address
            }

            response = self._make_request("/info", payload)

            if not isinstance(response, list):
                raise Exception(f"Portfolio API响应格式异常: 期望list，实际{type(response)}")

            # 提取所有period的数据
            periods = {}
            target_periods = ["day", "week", "month", "allTime"]

            for item in response:
                if isinstance(item, list) and len(item) >= 2:
                    period = item[0]
                    data = item[1]

                    # 只提取目标period
                    if period in target_periods:
                        # 验证数据格式
                        if not isinstance(data, dict):
                            continue

                        if "pnlHistory" not in data or "accountValueHistory" not in data:
                            continue

                        periods[period] = data

            # 验证是否获取了所有必需的period
            missing = set(target_periods) - set(periods.keys())
            if missing:
                raise Exception(f"Portfolio响应中缺少以下period: {missing}")

            return periods

        except Exception as e:
            raise Exception(f"获取Portfolio所有周期数据失败: {e}")

    def get_user_portfolio_data(self, user_address: str) -> Dict[str, Any]:
        """
        获取用户完整的投资组合数据

        优化说明:
        - 添加请求间延迟避免API限流
        - 使用正确的账户价值计算（Perp + Spot）
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

            # 第二批请求: 获取用户状态（包含持仓信息）
            user_state = self.get_user_state(user_address)

            # 直接从user_state提取数据，避免额外的API请求
            asset_positions = user_state.get("assetPositions", [])

            time.sleep(0.5)  # 延迟500ms

            # 第三批请求: 获取正确计算的保证金摘要（包含 Perp + Spot 账户价值）
            margin_summary = self.get_user_margin_summary(user_address)

            time.sleep(0.5)  # 延迟500ms

            # 第四批请求: 获取未成交订单
            open_orders = self.get_user_open_orders(user_address)

            time.sleep(0.5)  # 延迟500ms

            # 第五批请求: 获取TWAP数据
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
                "marginSummary": margin_summary,  # 现在包含正确计算的总账户价值
                "openOrders": open_orders,
                "twapFills": twap_fills,
            }

            # 输出账户价值详情以便验证
            perp_value = margin_summary.get("perpAccountValue", 0)
            spot_value = margin_summary.get("spotAccountValue", 0)
            total_value = margin_summary.get("accountValue", 0)
            print(f"成功获取数据: {len(fills)} 条成交记录, {len(asset_positions)} 个持仓")
            print(f"账户价值详情: Perp=${perp_value:,.2f}, Spot=${spot_value:,.2f}, 总计=${total_value:,.2f}")
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
