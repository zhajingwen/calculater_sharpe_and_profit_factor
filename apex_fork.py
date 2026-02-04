"""
Apex Liquid Bot - 盈亏因子和夏普比率计算器
基于Hyperliquid官方API和Apex Liquid Bot算法实现

本模块实现了Apex Liquid Bot用于计算以下指标的精确算法：
1. Profit Factor（盈亏因子）- 总盈利与总亏损的比率
2. Sharpe Ratio（夏普比率）- 风险调整后的收益指标

功能特性：
- 直接从Hyperliquid官方API获取真实交易数据
- 基于Apex Liquid Bot的精确算法计算
- 支持完整的交易分析功能
- 高精度计算（50位精度）
- 智能缓存机制（5分钟TTL）

API文档: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
算法来源:
- https://apexliquid.bot/assets/index-DmUy_5PH.js
- https://apexliquid.bot/assets/AssetPositionsTable-B8MWksSt.js
- https://apexliquid.bot/assets/hyperliquidWs-4Ciu49Um.js
- https://apexliquid.bot/assets/OpenOrdersTableNew-GSqIAf20.js
- https://apexliquid.bot/assets/RecentFillsTable-B8_vbQuR.js
"""

import math
import time
from typing import List, Dict, Any, Optional, Union
from decimal import Decimal, getcontext
from datetime import datetime, timedelta
from hyperliquid_api_client import HyperliquidAPIClient, safe_float, safe_int

# 设置高精度小数计算（50位精度）
getcontext().prec = 50


class ApexCalculator:
    """
    Apex Liquid Bot算法计算器主类

    功能：
    - 集成Hyperliquid官方API获取交易数据
    - 实现Apex Liquid Bot的核心算法
    - 提供完整的交易分析功能
    - 智能缓存机制提升性能

    属性：
        precision: 计算精度（位数）
        api_client: Hyperliquid API客户端
        cache: 数据缓存字典
        cache_ttl: 缓存过期时间（秒）
    """

    def __init__(self, api_base_url: str = "https://api.hyperliquid.xyz"):
        """
        初始化计算器

        参数：
            api_base_url: Hyperliquid API基础URL
        """
        self.precision = 50
        self.api_client = HyperliquidAPIClient(api_base_url)
        self.cache = {}  # 数据缓存字典
        self.cache_ttl = 300  # 缓存有效期：5分钟
    
    def _is_cache_valid(self, key: str) -> bool:
        """
        检查缓存是否有效

        参数：
            key: 缓存键

        返回：
            bool: 缓存是否有效且未过期
        """
        if key not in self.cache:
            return False
        return time.time() - self.cache[key]['timestamp'] < self.cache_ttl

    def _get_cached_data(self, key: str) -> Optional[Any]:
        """
        获取缓存数据

        参数：
            key: 缓存键

        返回：
            缓存的数据，如果缓存无效则返回None
        """
        if self._is_cache_valid(key):
            return self.cache[key]['data']
        return None

    def _set_cache_data(self, key: str, data: Any) -> None:
        """
        设置缓存数据

        参数：
            key: 缓存键
            data: 要缓存的数据
        """
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def get_user_data(self, user_address: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取用户完整交易数据

        参数：
            user_address: 用户钱包地址
            force_refresh: 是否强制刷新缓存（跳过缓存）

        返回：
            用户完整数据字典，包含成交记录、持仓、保证金等信息

        异常：
            ValueError: 地址格式无效
            Exception: API请求失败
        """
        cache_key = f"user_data_{user_address}"

        # 尝试使用缓存
        if not force_refresh:
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                print(f"✓ 使用缓存数据: {user_address}")
                return cached_data

        print(f"→ 从API获取数据: {user_address}")

        try:
            # 验证地址格式
            if not self.api_client.validate_user_address(user_address):
                raise ValueError(f"无效的用户地址格式: {user_address}")

            # 获取完整投资组合数据
            portfolio_data = self.api_client.get_user_portfolio_data(user_address)

            if not portfolio_data:
                raise Exception("未能获取用户数据，可能地址无交易记录或API不可用")

            # 缓存数据
            self._set_cache_data(cache_key, portfolio_data)
            print(f"✓ 数据获取成功并已缓存")

            return portfolio_data

        except ValueError as e:
            print(f"✗ 地址验证失败: {e}")
            raise
        except Exception as e:
            print(f"✗ 获取用户数据失败: {e}")
            return {}
    
    def get_user_fills(self, user_address: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        获取用户成交记录

        参数：
            user_address: 用户钱包地址
            force_refresh: 是否强制刷新缓存

        返回：
            成交记录列表，包含交易时间、价格、数量、PnL等信息
        """
        cache_key = f"fills_{user_address}"

        if not force_refresh:
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

        try:
            fills = self.api_client.get_user_fills(user_address)
            self._set_cache_data(cache_key, fills)
            return fills
        except Exception as e:
            print(f"✗ 获取成交记录失败: {e}")
            return []

    def get_user_asset_positions(self, user_address: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        获取用户当前资产持仓

        参数：
            user_address: 用户钱包地址
            force_refresh: 是否强制刷新缓存

        返回：
            资产持仓列表，包含持仓数量、未实现盈亏等信息
        """
        cache_key = f"positions_{user_address}"

        if not force_refresh:
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

        try:
            positions = self.api_client.get_user_asset_positions(user_address)
            self._set_cache_data(cache_key, positions)
            return positions
        except Exception as e:
            print(f"✗ 获取资产持仓失败: {e}")
            return []

    def get_user_margin_summary(self, user_address: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取用户保证金摘要

        参数：
            user_address: 用户钱包地址
            force_refresh: 是否强制刷新缓存

        返回：
            保证金摘要数据，包含账户价值、已用保证金等信息
        """
        cache_key = f"margin_{user_address}"

        if not force_refresh:
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

        try:
            margin_summary = self.api_client.get_user_margin_summary(user_address)
            self._set_cache_data(cache_key, margin_summary)
            return margin_summary
        except Exception as e:
            print(f"✗ 获取保证金摘要失败: {e}")
            return {}
    
    def calculate_profit_factor(self, fills: List[Dict], asset_positions: Optional[List[Dict]] = None) -> float:
        """
        计算盈亏因子（基于Apex Liquid Bot算法）

        盈亏因子 = 总盈利 / 总亏损
        该指标反映了交易策略的盈利能力，大于1表示盈利，小于1表示亏损

        参数：
            fills: 成交记录列表，包含'closedPnl'字段（已实现盈亏）
            asset_positions: 可选的当前持仓列表，包含'unrealizedPnl'字段（未实现盈亏）

        返回：
            - float: 盈亏因子数值
            - 1000.0: 只有盈利没有亏损时（表示无穷大）
            - 0.0: 无交易记录时

        算法说明：
            1. 累计所有已实现盈亏（来自fills）
            2. 累计所有未实现盈亏（来自当前持仓）
            3. 计算总盈利和总亏损的比值
            4. 当无亏损时返回 1000.0（代表无穷大）
        """
        if not fills and not asset_positions:
            return 0.0

        total_gains = Decimal('0')
        total_losses = Decimal('0')

        # 处理已实现盈亏（来自成交记录）
        for fill in fills:
            closed_pnl = Decimal(str(fill.get('closedPnl', 0)))
            if closed_pnl > 0:
                total_gains += closed_pnl
            elif closed_pnl < 0:
                total_losses += abs(closed_pnl)

        # 处理未实现盈亏（来自当前持仓）
        if asset_positions:
            for position in asset_positions:
                unrealized_pnl = Decimal(str(position.get('position', {}).get('unrealizedPnl', 0)))
                if unrealized_pnl > 0:
                    total_gains += unrealized_pnl
                elif unrealized_pnl < 0:
                    total_losses += abs(unrealized_pnl)

        # 计算盈亏因子
        if total_losses == 0:
            # 无亏损时返回 1000.0 表示无穷大（而非字符串）
            return 1000.0 if total_gains > 0 else 0.0

        profit_factor = total_gains / total_losses
        return float(profit_factor)

    def calculate_win_rate(self, fills: List[Dict]) -> Dict[str, float]:
        """
        计算胜率和交易统计信息

        参数：
            fills: 成交记录列表

        返回：
            字典，包含：
            - winRate: 胜率（百分比）
            - bias: 方向偏好（0-100，50为中性，>50偏多，<50偏空）
            - totalTrades: 总交易次数

        算法说明：
            1. 统计盈利和亏损交易次数
            2. 统计多头和空头交易次数
            3. 计算胜率 = 盈利次数 / 总次数
            4. 计算方向偏好 = (多头-空头) / 总数
        """
        if not fills:
            return {"winRate": 0, "bias": 50, "totalTrades": 0}

        long_trades = 0
        short_trades = 0
        winning_trades = 0
        losing_trades = 0

        for fill in fills:
            # 安全获取已实现盈亏
            closed_pnl_value = fill.get('closedPnl')
            if closed_pnl_value is None:
                continue

            closed_pnl = Decimal(str(closed_pnl_value))
            direction = fill.get('dir', '').strip()

            # 标准化方向判断（不区分大小写）
            direction_lower = direction.lower()

            # 统计交易方向（多头/空头）
            if any(term in direction_lower for term in ['open long', 'close long']):
                if 'short' not in direction_lower or direction_lower.endswith('long'):
                    long_trades += 1
            elif 'short > long' in direction_lower or 'short>long' in direction_lower:
                long_trades += 1
            elif any(term in direction_lower for term in ['open short', 'close short']):
                if 'long' not in direction_lower or direction_lower.endswith('short'):
                    short_trades += 1
            elif 'long > short' in direction_lower or 'long>short' in direction_lower:
                short_trades += 1

            # 统计盈亏次数（排除零盈亏）
            if closed_pnl != 0:
                if closed_pnl > 0:
                    winning_trades += 1
                else:
                    losing_trades += 1

        total_trades = len(fills)
        total_pnl_trades = winning_trades + losing_trades

        # 计算胜率
        win_rate = (winning_trades / total_pnl_trades * 100) if total_pnl_trades > 0 else 0

        # 计算方向偏好（多空倾向）
        bias = ((long_trades - short_trades) / total_trades * 100 + 100) / 2 if total_trades > 0 else 50

        return {
            "winRate": win_rate,
            "bias": bias,
            "totalTrades": total_trades
        }

    def calculate_hold_time_stats(self, fills: List[Dict]) -> Dict[str, float]:
        """
        计算平均持仓时间统计（改进版：区分多空方向，支持部分平仓）

        参数：
            fills: 成交记录列表，包含'time'、'dir'、'coin'和'sz'字段

        返回：
            字典，包含不同时间段的平均持仓时间（天数）：
            - todayCount: 今日平均持仓时间
            - last7DaysAverage: 最近7天平均持仓时间
            - last30DaysAverage: 最近30天平均持仓时间
            - allTimeAverage: 全部时间平均持仓时间

        算法改进：
            1. 区分多头(Long)和空头(Short)仓位，分别配对
            2. 支持部分平仓的加权计算
            3. 使用FIFO原则进行配对
            4. 正确处理翻仓交易(Long > Short, Short > Long)

        算法说明：
            1. 为每个币种维护独立的多头和空头开仓队列
            2. 平仓时从对应方向的队列中按FIFO原则匹配
            3. 支持部分平仓：按数量比例匹配开仓记录
            4. 计算每对交易的持仓时长并按时间段统计
        """
        if not fills:
            return {
                "todayCount": 0,
                "last7DaysAverage": 0,
                "last30DaysAverage": 0,
                "allTimeAverage": 0
            }

        from collections import defaultdict

        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        week_ago = today_start - timedelta(days=7)
        month_ago = today_start - timedelta(days=30)

        # 为每个币种维护多头和空头的开仓队列
        # 队列中存储 [开仓时间, 剩余数量]
        long_open_positions = defaultdict(list)
        short_open_positions = defaultdict(list)

        # 存储所有已配对的持仓记录 (开仓时间, 平仓时间, 持仓数量)
        completed_positions = []

        # 按时间排序
        sorted_fills = sorted(fills, key=lambda x: x.get('time', 0))

        for fill in sorted_fills:
            coin = fill.get('coin', '')
            direction = fill.get('dir', '').strip()
            timestamp = fill.get('time', 0)
            size = abs(float(fill.get('sz', 0)))

            if not coin or not timestamp or size == 0:
                continue

            # 标准化方向字符串（不区分大小写）
            dir_lower = direction.lower()

            # 处理开多仓交易
            if 'open long' in dir_lower and 'short' not in dir_lower:
                long_open_positions[coin].append([timestamp, size])

            # 处理开空仓交易
            elif 'open short' in dir_lower and 'long' not in dir_lower:
                short_open_positions[coin].append([timestamp, size])

            # 处理平多仓交易（支持部分平仓）
            elif 'close long' in dir_lower and 'short' not in dir_lower:
                remaining_size = size

                while remaining_size > 1e-9 and long_open_positions[coin]:
                    open_time, open_size = long_open_positions[coin][0]

                    if open_size <= remaining_size:
                        # 完全平掉这笔开仓
                        completed_positions.append((open_time, timestamp, open_size))
                        remaining_size -= open_size
                        long_open_positions[coin].pop(0)
                    else:
                        # 部分平仓
                        completed_positions.append((open_time, timestamp, remaining_size))
                        long_open_positions[coin][0][1] -= remaining_size
                        remaining_size = 0

            # 处理平空仓交易（支持部分平仓）
            elif 'close short' in dir_lower and 'long' not in dir_lower:
                remaining_size = size

                while remaining_size > 1e-9 and short_open_positions[coin]:
                    open_time, open_size = short_open_positions[coin][0]

                    if open_size <= remaining_size:
                        # 完全平掉这笔开仓
                        completed_positions.append((open_time, timestamp, open_size))
                        remaining_size -= open_size
                        short_open_positions[coin].pop(0)
                    else:
                        # 部分平仓
                        completed_positions.append((open_time, timestamp, remaining_size))
                        short_open_positions[coin][0][1] -= remaining_size
                        remaining_size = 0

            # 处理翻仓交易：从空翻多 (Short > Long)
            elif 'short > long' in dir_lower or 'short>long' in dir_lower:
                # 先平掉所有空头仓位
                while short_open_positions[coin]:
                    open_time, open_size = short_open_positions[coin].pop(0)
                    completed_positions.append((open_time, timestamp, open_size))
                # 然后作为开多仓处理
                long_open_positions[coin].append([timestamp, size])

            # 处理翻仓交易：从多翻空 (Long > Short)
            elif 'long > short' in dir_lower or 'long>short' in dir_lower:
                # 先平掉所有多头仓位
                while long_open_positions[coin]:
                    open_time, open_size = long_open_positions[coin].pop(0)
                    completed_positions.append((open_time, timestamp, open_size))
                # 然后作为开空仓处理
                short_open_positions[coin].append([timestamp, size])

        # 计算所有配对交易的持仓时间
        today_hold_times = []
        week_hold_times = []
        month_hold_times = []
        all_hold_times = []

        for open_time, close_time, position_size in completed_positions:
            open_dt = datetime.fromtimestamp(open_time / 1000)
            close_dt = datetime.fromtimestamp(close_time / 1000)

            hold_time_days = (close_dt - open_dt).total_seconds() / 86400
            all_hold_times.append(hold_time_days)

            # 按时间段分类
            if close_dt >= today_start:
                today_hold_times.append(hold_time_days)

            if close_dt >= week_ago:
                week_hold_times.append(hold_time_days)

            if close_dt >= month_ago:
                month_hold_times.append(hold_time_days)

        return {
            "todayCount": sum(today_hold_times) / len(today_hold_times) if today_hold_times else 0,
            "last7DaysAverage": sum(week_hold_times) / len(week_hold_times) if week_hold_times else 0,
            "last30DaysAverage": sum(month_hold_times) / len(month_hold_times) if month_hold_times else 0,
            "allTimeAverage": sum(all_hold_times) / len(all_hold_times) if all_hold_times else 0
        }
    
    def analyze_user(self, user_address: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        分析用户交易表现（主要方法）

        该方法执行完整的交易分析，计算所有关键指标

        参数：
            user_address: 用户钱包地址
            force_refresh: 是否强制刷新缓存数据

        返回：
            完整的分析结果字典，包含：
            - 盈亏因子 (Profit Factor)
            - 胜率统计 (Win Rate)
            - 持仓时间统计 (Hold Time Stats)
            - 当前持仓分析 (Position Analysis)
            - 夏普比率 - 基于交易收益率 (Sharpe Ratio on Trades)
            - 最大回撤 - 基于交易收益率 (Max Drawdown on Trades)
            - 收益率指标 - 基于交易收益率 (Return Metrics on Trades)
            - 原始数据摘要 (Data Summary)

        异常：
            捕获所有异常并返回错误信息
        """
        try:
            # 步骤1: 获取用户数据
            user_data = self.get_user_data(user_address, force_refresh)

            if not user_data:
                return {"error": "无法获取用户数据，请检查地址是否正确或网络连接"}

            # 步骤2: 提取核心数据
            fills = user_data.get('fills', [])
            asset_positions = user_data.get('assetPositions', [])
            margin_summary = user_data.get('marginSummary', {})

            # 步骤4: 初始化结果字典
            results = {
                "user_address": user_address,
                "analysis_timestamp": datetime.now().isoformat(),
                "_raw_fills": fills,  # 保存原始数据供报告生成使用
                "data_summary": {
                    "total_fills": len(fills),
                    "total_positions": len(asset_positions),
                    "account_value": safe_float(margin_summary.get('accountValue')),
                    "perp_account_value": safe_float(margin_summary.get('perpAccountValue')),
                    "spot_account_value": safe_float(margin_summary.get('spotAccountValue')),
                    "total_margin_used": safe_float(margin_summary.get('totalMarginUsed'))
                }
            }

            # 指标1: 盈亏因子 (Profit Factor)
            if fills:
                profit_factor = self.calculate_profit_factor(fills, asset_positions)
                results["profit_factor"] = profit_factor
            else:
                results["profit_factor"] = 0

            # 指标3: 胜率统计 (Win Rate)
            if fills:
                win_stats = self.calculate_win_rate(fills)
                results["win_rate"] = win_stats
            else:
                results["win_rate"] = {"winRate": 0, "bias": 50, "totalTrades": 0}

            # 指标4: 持仓时间统计 (Hold Time Stats)
            if fills:
                hold_stats = self.calculate_hold_time_stats(fills)
                results["hold_time_stats"] = hold_stats
            else:
                results["hold_time_stats"] = {
                    "todayCount": 0, "last7DaysAverage": 0,
                    "last30DaysAverage": 0, "allTimeAverage": 0
                }

            # 指标6: 当前持仓分析 (Current Positions)
            if asset_positions:
                position_analysis = self._analyze_current_positions(asset_positions)
                results["position_analysis"] = position_analysis
            else:
                results["position_analysis"] = {"total_positions": 0, "total_unrealized_pnl": 0}

            # 指标7: 累计总PNL (Total Cumulative PnL)
            total_realized_pnl = sum(safe_float(fill.get('closedPnl', 0)) for fill in fills)
            total_unrealized_pnl = results["position_analysis"].get('total_unrealized_pnl', 0)
            total_cumulative_pnl = total_realized_pnl + total_unrealized_pnl
            results["total_realized_pnl"] = total_realized_pnl
            results["total_cumulative_pnl"] = total_cumulative_pnl

            # 指标8: 基于单笔交易收益率的 Sharpe Ratio（不依赖本金）
            if fills and len(fills) > 1:
                sharpe_on_trades = self.calculate_sharpe_ratio_on_trades(fills)
                results["sharpe_on_trades"] = sharpe_on_trades
            else:
                results["sharpe_on_trades"] = {
                    "sharpe_ratio": 0,
                    "annualized_sharpe": 0,
                    "mean_return": 0,
                    "std_return": 0,
                    "total_trades": 0,
                    "trades_per_year": 0
                }

            # 指标9: 基于单笔交易收益率的 Max Drawdown（不依赖本金）
            if fills and len(fills) > 1:
                max_dd_on_trades = self.calculate_max_drawdown_on_trades(fills)
                results["max_drawdown_on_trades"] = max_dd_on_trades
            else:
                results["max_drawdown_on_trades"] = {
                    "max_drawdown_pct": 0,
                    "peak_return": 0,
                    "trough_return": 0,
                    "total_trades": 0,
                    "cumulative_return": 0
                }

            # 指标10: 基于单笔交易收益率的收益率指标（不依赖本金）
            if fills and len(fills) > 1:
                return_metrics_on_trades = self.calculate_return_metrics_on_trades(fills)
                results["return_metrics_on_trades"] = return_metrics_on_trades
            else:
                results["return_metrics_on_trades"] = {
                    "cumulative_return": 0,
                    "annualized_return": 0,
                    "trading_days": 0,
                    "annualized_return_valid": False,
                    "annualized_return_warnings": ["NO_TRADES"]
                }

            return results

        except Exception as e:
            error_msg = f"分析过程中发生错误: {str(e)}"
            print(f"\n✗ {error_msg}")
            import traceback
            print(f"详细错误信息:\n{traceback.format_exc()}")
            return {"error": error_msg}


    def _analyze_current_positions(self, asset_positions: List[Dict]) -> Dict[str, Any]:
        """
        分析当前持仓状态

        参数：
            asset_positions: 资产持仓列表

        返回：
            持仓分析结果字典，包含：
            - total_positions: 总持仓数
            - total_unrealized_pnl: 总未实现盈亏
            - total_position_value: 总持仓价值
            - long_positions: 多头仓位数
            - short_positions: 空头仓位数
            - position_bias: 仓位偏好（多头/空头/中性）

        算法说明：
            1. 遍历所有持仓，累计未实现盈亏和仓位价值
            2. 根据持仓数量正负判断多空方向
            3. 统计多空仓位数量和偏好
        """
        total_unrealized_pnl = 0
        total_position_value = 0
        long_positions = 0
        short_positions = 0

        for position in asset_positions:
            pos_data = position.get('position', {})
            # 安全转换数值类型
            unrealized_pnl = safe_float(pos_data.get('unrealizedPnl'))
            position_value = safe_float(pos_data.get('positionValue'))
            size = safe_float(pos_data.get('szi'))

            total_unrealized_pnl += unrealized_pnl
            total_position_value += position_value

            # 根据持仓数量判断方向
            if size > 0:
                long_positions += 1
            elif size < 0:
                short_positions += 1

        # 判断仓位偏好
        if long_positions > short_positions:
            bias = "多头"
        elif short_positions > long_positions:
            bias = "空头"
        else:
            bias = "中性"

        return {
            "total_positions": len(asset_positions),
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_position_value": total_position_value,
            "long_positions": long_positions,
            "short_positions": short_positions,
            "position_bias": bias
        }


    def calculate_sharpe_ratio_on_trades(self, fills: List[Dict],
                                         risk_free_rate: float = 0.03) -> Dict[str, float]:
        """
        基于单笔交易收益率计算 Sharpe Ratio（不依赖本金）

        参数：
            fills: 成交记录列表
            risk_free_rate: 无风险利率（年化，默认3%）

        返回：
            - sharpe_ratio: 每笔交易的夏普比率
            - annualized_sharpe: 年化夏普比率
            - mean_return: 平均每笔收益率
            - std_return: 收益率标准差
            - total_trades: 交易数量
            - trades_per_year: 年交易频率
        """
        trade_returns = []
        trade_times = []

        for fill in fills:
            closed_pnl = float(fill.get('closedPnl', 0))
            if closed_pnl == 0:
                continue

            sz = float(fill.get('sz', 0))
            px = float(fill.get('px', 0))
            notional_value = abs(sz) * px

            if notional_value > 0:
                trade_return = closed_pnl / notional_value
                trade_returns.append(trade_return)
                trade_times.append(fill.get('time', 0))

        if len(trade_returns) < 2:
            return {
                "sharpe_ratio": 0,
                "annualized_sharpe": 0,
                "mean_return": 0,
                "std_return": 0,
                "total_trades": 0,
                "trades_per_year": 0
            }

        # 计算均值和标准差
        mean_return = sum(trade_returns) / len(trade_returns)
        variance = sum((r - mean_return) ** 2 for r in trade_returns) / (len(trade_returns) - 1)
        std_return = math.sqrt(variance)

        if std_return == 0:
            return {
                "sharpe_ratio": 0,
                "annualized_sharpe": 0,
                "mean_return": mean_return,
                "std_return": 0,
                "total_trades": len(trade_returns),
                "trades_per_year": 0
            }

        # 计算每笔交易的 Sharpe
        hold_stats = self.calculate_hold_time_stats(fills)
        avg_hold_days = hold_stats['allTimeAverage'] if hold_stats['allTimeAverage'] > 0 else 1.0
        trade_rf_rate = (1 + risk_free_rate) ** (avg_hold_days / 365) - 1

        sharpe_per_trade = (mean_return - trade_rf_rate) / std_return

        # 计算年交易次数
        if len(trade_times) >= 2:
            first_time = min(trade_times)
            last_time = max(trade_times)
            days = (last_time - first_time) / 1000 / 86400
            trades_per_year = len(trade_returns) / days * 365 if days > 0 else 365
        else:
            trades_per_year = 365

        # 年化 Sharpe
        annualized_sharpe = sharpe_per_trade * math.sqrt(trades_per_year)

        return {
            "sharpe_ratio": sharpe_per_trade,
            "annualized_sharpe": annualized_sharpe,
            "mean_return": mean_return,
            "std_return": std_return,
            "total_trades": len(trade_returns),
            "trades_per_year": trades_per_year
        }

    def calculate_max_drawdown_on_trades(self, fills: List[Dict]) -> Dict[str, float]:
        """
        基于单笔交易收益率计算最大回撤（不依赖本金）

        使用复利计算累计收益率曲线，追踪峰谷

        参数：
            fills: 成交记录列表

        返回：
            - max_drawdown_pct: 最大回撤百分比
            - peak_return: 峰值累计收益率
            - trough_return: 谷底累计收益率
            - peak_date: 峰值日期
            - trough_date: 谷底日期
            - total_trades: 交易数量
            - cumulative_return: 总累计收益率
        """
        trade_returns = []
        trade_times = []

        for fill in fills:
            closed_pnl = float(fill.get('closedPnl', 0))
            if closed_pnl == 0:
                continue

            sz = float(fill.get('sz', 0))
            px = float(fill.get('px', 0))
            notional_value = abs(sz) * px

            if notional_value > 0:
                trade_return = closed_pnl / notional_value
                trade_returns.append(trade_return)
                trade_times.append(fill.get('time', 0))

        if len(trade_returns) < 2:
            return {
                "max_drawdown_pct": 0,
                "peak_return": 0,
                "trough_return": 0,
                "peak_date": "N/A",
                "trough_date": "N/A",
                "total_trades": 0,
                "cumulative_return": 0
            }

        # 构建累计收益率序列（复利）
        cumulative_returns = []
        cumulative = 1.0

        for ret in trade_returns:
            cumulative *= (1 + ret)
            cumulative_returns.append(cumulative)

        # 计算最大回撤
        peak = cumulative_returns[0]
        peak_index = 0
        max_drawdown = 0
        trough_value = peak
        trough_index = 0

        for i, value in enumerate(cumulative_returns):
            if value > peak:
                peak = value
                peak_index = i

            drawdown = (peak - value) / peak

            if drawdown > max_drawdown:
                max_drawdown = drawdown
                trough_value = value
                trough_index = i

        # 格式化日期
        def format_date(timestamp_ms):
            if timestamp_ms > 0:
                try:
                    dt = datetime.fromtimestamp(timestamp_ms / 1000)
                    return dt.strftime('%Y-%m-%d')
                except:
                    return "N/A"
            return "N/A"

        peak_date = format_date(trade_times[peak_index])
        trough_date = format_date(trade_times[trough_index])

        return {
            "max_drawdown_pct": max_drawdown * 100,
            "peak_return": (peak - 1) * 100,
            "trough_return": (trough_value - 1) * 100,
            "peak_date": peak_date,
            "trough_date": trough_date,
            "total_trades": len(trade_returns),
            "cumulative_return": (cumulative - 1) * 100
        }

    def calculate_return_metrics_on_trades(self, fills: List[Dict]) -> Dict[str, float]:
        """
        基于单笔交易收益率计算累计和年化收益率（不依赖本金）

        参数：
            fills: 成交记录列表

        返回：
            - cumulative_return: 累计收益率（复利）
            - annualized_return: 年化收益率
            - trading_days: 交易天数
            - annualized_return_valid: 年化收益率是否可靠
            - annualized_return_warnings: 警告列表
        """
        trade_returns = []
        trade_times = []

        for fill in fills:
            closed_pnl = float(fill.get('closedPnl', 0))
            if closed_pnl == 0:
                continue

            sz = float(fill.get('sz', 0))
            px = float(fill.get('px', 0))
            notional_value = abs(sz) * px

            if notional_value > 0:
                trade_return = closed_pnl / notional_value
                trade_returns.append(trade_return)
                trade_times.append(fill.get('time', 0))

        if len(trade_returns) < 1:
            return {
                "cumulative_return": 0,
                "annualized_return": 0,
                "trading_days": 0,
                "annualized_return_valid": False,
                "annualized_return_warnings": ["NO_TRADES"]
            }

        # 计算累计收益率（复利）
        cumulative = 1.0
        for ret in trade_returns:
            cumulative *= (1 + ret)
        cumulative_return = (cumulative - 1) * 100

        # 计算交易天数
        if len(trade_times) >= 2:
            first_time = min(trade_times)
            last_time = max(trade_times)
            trading_days = (last_time - first_time) / 1000 / 86400
        else:
            trading_days = 0

        # 计算年化收益率（带溢出保护）
        annualized_return = 0
        annualized_return_valid = True
        annualized_return_warnings = []

        if trading_days > 0:
            try:
                annual_factor = 365.0 / trading_days

                # 分级警告而非硬性拒绝
                if trading_days < 1:
                    annualized_return_valid = False
                    annualized_return_warnings.append("LESS_THAN_1_DAY")
                elif trading_days < 7:
                    annualized_return_valid = False
                    annualized_return_warnings.append("LESS_THAN_7_DAYS")
                elif trading_days < 30:
                    annualized_return_valid = False
                    annualized_return_warnings.append("LESS_THAN_30_DAYS")

                # 计算年化收益率
                if annual_factor <= 100:  # 交易天数 >= 3.65 天
                    annualized_return = (math.pow(cumulative, annual_factor) - 1) * 100

                    # 检查极端值
                    if abs(annualized_return) > 5000:
                        annualized_return_valid = False
                        annualized_return_warnings.append("EXTREME_RETURN_VALUE")
                    elif abs(annualized_return) > 1000:
                        annualized_return_valid = False
                        annualized_return_warnings.append("VERY_HIGH_RETURN_VALUE")
                else:
                    # 交易天数太短，标记但仍计算
                    annualized_return = (math.pow(cumulative, annual_factor) - 1) * 100
                    annualized_return_valid = False
                    annualized_return_warnings.append("VERY_SHORT_PERIOD")

            except (OverflowError, ValueError):
                annualized_return = 0
                annualized_return_valid = False
                annualized_return_warnings.append("CALCULATION_ERROR")
        else:
            annualized_return_valid = False
            annualized_return_warnings.append("NO_TIME_SPAN")

        return {
            "cumulative_return": cumulative_return,
            "annualized_return": annualized_return,
            "trading_days": trading_days,
            "annualized_return_valid": annualized_return_valid,
            "annualized_return_warnings": annualized_return_warnings
        }


def main():
    """主程序入口 - Hyperliquid交易分析示例"""
    calculator = ApexCalculator()
    user_address = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"  # 示例地址

    if calculator.api_client.validate_user_address(user_address):
        try:
            results = calculator.analyze_user(user_address, force_refresh=True)
            if "error" not in results:
                print(f"✅ 分析成功: {user_address}")
                return results
            else:
                print(f"❌ 分析失败: {results['error']}")
        except Exception as e:
            print(f"❌ 错误: {e}")
    else:
        print(f"❌ 地址格式无效: {user_address}")


if __name__ == "__main__":
    main()
