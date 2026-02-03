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
    
    def calculate_profit_factor(self, fills: List[Dict], asset_positions: Optional[List[Dict]] = None) -> Union[float, str]:
        """
        计算盈亏因子（基于Apex Liquid Bot算法）

        盈亏因子 = 总盈利 / 总亏损
        该指标反映了交易策略的盈利能力，大于1表示盈利，小于1表示亏损

        参数：
            fills: 成交记录列表，包含'closedPnl'字段（已实现盈亏）
            asset_positions: 可选的当前持仓列表，包含'unrealizedPnl'字段（未实现盈亏）

        返回：
            - float: 盈亏因子数值
            - "1000+": 只有盈利没有亏损时
            - 0: 无交易记录时

        算法说明：
            1. 累计所有已实现盈亏（来自fills）
            2. 累计所有未实现盈亏（来自当前持仓）
            3. 计算总盈利和总亏损的比值
        """
        if not fills and not asset_positions:
            return 0

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
            return "1000+" if total_gains > 0 else 0

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
    
    def calculate_roe(self, portfolio_data: List[Dict], period: str = "perpAllTime") -> float:
        """
        计算股本回报率ROE（基于Apex Liquid Bot算法）

        ROE = (净收益 / 加权平均资本) × 100%
        该指标衡量资金使用效率，考虑了出入金的影响

        参数：
            portfolio_data: 投资组合数据，包含accountValueHistory和pnlHistory
            period: 时间周期过滤器（默认"perpAllTime"）

        返回：
            float: ROE百分比

        算法说明：
            1. 识别所有出入金流水
            2. 计算净收益（排除出入金影响）
            3. 计算加权平均资本
            4. 应用ROE公式
        """
        # 根据时间周期过滤数据
        filtered_data = [item for item in portfolio_data if item[0] == period]
        if not filtered_data:
            return 0.0

        data = filtered_data[0][1]
        account_history = data.get('accountValueHistory', [])
        pnl_history = data.get('pnlHistory', [])

        if not account_history or len(account_history) < 2:
            return 0.0

        # 获取初始和最终余额
        initial_balance = Decimal(str(account_history[0][1]))
        final_balance = Decimal(str(account_history[-1][1]))

        # 计算现金流（出入金）
        cash_flows = []
        for i in range(1, len(account_history)):
            current_balance = Decimal(str(account_history[i][1]))
            previous_balance = Decimal(str(account_history[i-1][1]))
            current_pnl = Decimal(str(pnl_history[i][1])) if i < len(pnl_history) else Decimal('0')
            previous_pnl = Decimal(str(pnl_history[i-1][1])) if i-1 < len(pnl_history) else Decimal('0')

            # 计算出入金流量
            expected_balance = previous_balance + (current_pnl - previous_pnl)
            cash_flow = current_balance - expected_balance

            # 只记录显著的现金流（>1e-9）
            if abs(cash_flow) > Decimal('1e-9'):
                cash_flows.append({
                    'amount': cash_flow,
                    'date': account_history[i][0]
                })

        # 计算加权平均资本和ROI
        total_cash_flows = sum(cf['amount'] for cf in cash_flows)
        net_income = final_balance - initial_balance - total_cash_flows

        # 计算加权平均资本（简化方法）
        weighted_capital = initial_balance
        for cf in cash_flows:
            # 按周期内剩余时间加权
            weighted_capital += cf['amount'] * Decimal('0.5')  # 简化权重

        if weighted_capital == 0:
            return 0.0

        roi = (net_income / weighted_capital) * 100
        return float(roi)
    
    
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

        from datetime import datetime, timedelta
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
            - 夏普比率 (Sharpe Ratio)
            - 胜率统计 (Win Rate)
            - 最大回撤 (Max Drawdown)
            - 持仓时间统计 (Hold Time Stats)
            - 当前持仓分析 (Position Analysis)
            - 原始数据摘要 (Data Summary)

        异常：
            捕获所有异常并返回错误信息
        """
        print(f"\n{'='*60}")
        print(f"🔍 开始分析用户: {user_address}")
        print(f"{'='*60}")

        try:
            # 步骤1: 获取用户数据
            user_data = self.get_user_data(user_address, force_refresh)

            if not user_data:
                return {"error": "无法获取用户数据，请检查地址是否正确或网络连接"}

            # 步骤2: 提取核心数据
            fills = user_data.get('fills', [])
            asset_positions = user_data.get('assetPositions', [])
            margin_summary = user_data.get('marginSummary', {})

            print(f"\n📊 数据获取完成:")
            print(f"  ✓ 成交记录: {len(fills)} 条")
            print(f"  ✓ 当前持仓: {len(asset_positions)} 个")

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

            print(f"\n📈 计算交易指标:")

            # 指标1: 盈亏因子 (Profit Factor)
            if fills:
                profit_factor = self.calculate_profit_factor(fills, asset_positions)
                results["profit_factor"] = profit_factor
                print(f"  ✓ Profit Factor: {profit_factor}")
            else:
                results["profit_factor"] = 0
                print(f"  ⚠ Profit Factor: 无成交记录")


            # 指标3: 胜率统计 (Win Rate)
            if fills:
                win_stats = self.calculate_win_rate(fills)
                results["win_rate"] = win_stats
                print(f"  ✓ Win Rate: {win_stats['winRate']:.2f}%")
                print(f"    - 方向偏好: {win_stats['bias']:.2f}% ({'多头' if win_stats['bias'] > 50 else '空头' if win_stats['bias'] < 50 else '中性'})")
                print(f"    - 总交易次数: {win_stats['totalTrades']}")
            else:
                results["win_rate"] = {"winRate": 0, "bias": 50, "totalTrades": 0}
                print(f"  ⚠ Win Rate: 无成交记录")

            # 指标4: 持仓时间统计 (Hold Time Stats)
            if fills:
                hold_stats = self.calculate_hold_time_stats(fills)
                results["hold_time_stats"] = hold_stats
                print(f"  ✓ 平均持仓时间: {hold_stats['allTimeAverage']:.2f} 天")
            else:
                results["hold_time_stats"] = {
                    "todayCount": 0, "last7DaysAverage": 0,
                    "last30DaysAverage": 0, "allTimeAverage": 0
                }
                print(f"  ⚠ 持仓时间统计: 无成交记录")

            # 指标6: 当前持仓分析 (Current Positions)
            if asset_positions:
                position_analysis = self._analyze_current_positions(asset_positions)
                results["position_analysis"] = position_analysis
                print(f"  ✓ 当前持仓: {len(asset_positions)} 个活跃仓位")
                print(f"    - 总未实现盈亏: ${position_analysis.get('total_unrealized_pnl', 0):.2f}")
                print(f"    - 仓位偏好: {position_analysis.get('position_bias', 'Unknown')}")
            else:
                results["position_analysis"] = {"total_positions": 0, "total_unrealized_pnl": 0}
                print(f"  ⚠ 当前持仓: 无持仓")

            # 指标7: 累计总PNL (Total Cumulative PnL)
            total_realized_pnl = sum(safe_float(fill.get('closedPnl', 0)) for fill in fills)
            total_unrealized_pnl = results["position_analysis"].get('total_unrealized_pnl', 0)
            total_cumulative_pnl = total_realized_pnl + total_unrealized_pnl
            results["total_realized_pnl"] = total_realized_pnl
            results["total_cumulative_pnl"] = total_cumulative_pnl
            print(f"  ✓ 累计总盈亏: ${total_cumulative_pnl:,.2f}")
            print(f"    - 已实现盈亏: ${total_realized_pnl:,.2f}")
            print(f"    - 未实现盈亏: ${total_unrealized_pnl:,.2f}")

            # 指标8: 真实本金计算 (True Capital)
            print(f"\n📊 计算本金和收益率指标:")
            print(f"  → 获取账本记录...")
            ledger_records = self.api_client.get_user_ledger(user_address, start_time=0)

            capital_info = self.calculate_true_capital(user_address, ledger_records)
            results["capital_info"] = capital_info
            print(f"  ✓ 真实本金: ${capital_info['true_capital']:,.2f}")
            print(f"    - 总充值: ${capital_info['total_deposits']:,.2f}")
            print(f"    - 总提现: ${capital_info['total_withdrawals']:,.2f}")
            print(f"    - 外部转入 Spot: ${capital_info['external_to_spot']:,.2f}")
            print(f"    - 外部转出: ${capital_info['external_out']:,.2f}")

            # 指标9: 累计收益率和年化收益率 (Return Metrics)
            current_account_value = results["data_summary"].get("account_value", 0)

            # 获取第一笔和最后一笔交易时间
            if fills:
                first_trade_time = min(fill.get('time', 0) for fill in fills if fill.get('time', 0) > 0)
                last_trade_time = max(fill.get('time', 0) for fill in fills if fill.get('time', 0) > 0)
            else:
                first_trade_time = 0
                last_trade_time = 0

            return_metrics = self.calculate_return_metrics(
                current_value=current_account_value,
                true_capital=capital_info['true_capital'],
                first_trade_time=first_trade_time,
                last_trade_time=last_trade_time
            )
            results["return_metrics"] = return_metrics
            print(f"  ✓ 累计收益率: {return_metrics['cumulative_return']:.2f}%")
            print(f"  ✓ 年化收益率: {return_metrics['annualized_return']:.2f}%")
            print(f"    - 净盈利: ${return_metrics['net_profit']:,.2f}")
            print(f"    - 交易天数: {return_metrics['trading_days']:.1f} 天")

            # 指标10: 基于真实本金的 Sharpe Ratio（推荐方法）
            if fills and len(fills) > 1:
                print(f"\n📈 计算 Sharpe Ratio（基于真实本金）:")
                sharpe_on_capital = self.calculate_sharpe_ratio_on_capital(
                    fills=fills,
                    true_capital=capital_info['true_capital']
                )
                results["sharpe_on_capital"] = sharpe_on_capital
                print(f"  ✓ Sharpe Ratio (每笔交易): {sharpe_on_capital['sharpe_ratio']:.4f}")
                print(f"  ✓ Sharpe Ratio (年化): {sharpe_on_capital['annualized_sharpe']:.2f}")
                print(f"    - 平均每笔收益率: {sharpe_on_capital['mean_return_per_trade']*100:.4f}%")
                print(f"    - 收益率标准差: {sharpe_on_capital['std_dev']*100:.4f}%")
                print(f"    - 分析交易数: {sharpe_on_capital['total_trades']}")
            else:
                results["sharpe_on_capital"] = {
                    "sharpe_ratio": 0,
                    "annualized_sharpe": 0,
                    "mean_return_per_trade": 0,
                    "std_dev": 0,
                    "total_trades": 0
                }
                print(f"  ⚠ Sharpe Ratio (基于真实本金): 数据不足")

            # 指标11: 基于真实本金的 Max Drawdown（推荐方法）
            if fills and len(fills) > 1:
                print(f"\n📉 计算 Max Drawdown（基于真实本金）:")
                max_dd_on_capital = self.calculate_max_drawdown_on_capital(
                    fills=fills,
                    true_capital=capital_info['true_capital']
                )
                results["max_drawdown_on_capital"] = max_dd_on_capital
                print(f"  ✓ 最大回撤: {max_dd_on_capital['max_drawdown_pct']:.2f}%")
                print(f"    - 峰值累计收益率: {max_dd_on_capital['peak_return']:.2f}%")
                print(f"    - 谷底累计收益率: {max_dd_on_capital['trough_return']:.2f}%")
                print(f"    - 分析交易数: {max_dd_on_capital['total_trades']}")
            else:
                results["max_drawdown_on_capital"] = {
                    "max_drawdown_pct": 0,
                    "peak_return": 0,
                    "trough_return": 0,
                    "total_trades": 0
                }
                print(f"  ⚠ Max Drawdown (基于真实本金): 数据不足")

            print(f"\n{'='*60}")
            print("✅ 分析完成!")
            print(f"{'='*60}")

            return results

        except Exception as e:
            error_msg = f"分析过程中发生错误: {str(e)}"
            print(f"\n✗ {error_msg}")
            import traceback
            print(f"详细错误信息:\n{traceback.format_exc()}")
            return {"error": error_msg}

    def calculate_true_capital(self, user_address: str, ledger_records: List[Dict]) -> Dict[str, float]:
        """
        计算真实本金（算法 2: 完整版本）

        计算公式:
        true_capital = deposits - withdrawals + external_to_spot - external_out

        考虑因素:
        1. ✅ 充值和提现（deposit/withdraw）
        2. ✅ 外部转入到 Spot（别人通过 send 转给我的）
        3. ✅ 外部转出（我通过 send 转给别人的）
        4. ❌ 排除内部 Perp ↔ Spot 转账（不影响总资金）

        参数：
            user_address: 用户地址
            ledger_records: 账本记录列表

        返回：
            字典，包含：
            - total_deposits: 总充值
            - total_withdrawals: 总提现
            - external_to_spot: 外部转入 Spot
            - external_out: 外部转出
            - true_capital: 真实本金
        """
        total_deposits = 0.0
        total_withdrawals = 0.0
        external_to_spot = 0.0
        external_out = 0.0

        addr_lower = user_address.lower()

        for record in ledger_records:
            delta = record.get('delta', {})
            delta_type = delta.get('type', '')

            if delta_type == 'deposit':
                # 充值
                amount = safe_float(delta.get('usdc', 0))
                total_deposits += amount

            elif delta_type == 'withdraw':
                # 提现
                amount = safe_float(delta.get('usdc', 0))
                total_withdrawals += abs(amount)  # 提现可能是负数

            elif delta_type == 'send':
                # 转账操作
                amount = safe_float(delta.get('amount', 0))
                user = delta.get('user', '').lower()
                dest = delta.get('destination', '').lower()
                source_dex = delta.get('sourceDex', '')
                dest_dex = delta.get('destinationDex', '')

                # 判断是否为内部转账（Perp ↔ Spot）
                is_internal_transfer = (user == addr_lower and dest == addr_lower)

                if is_internal_transfer:
                    # 内部转账，不影响总资金，跳过
                    continue

                # 外部转入到 Spot
                if user != addr_lower and dest == addr_lower and dest_dex == 'spot':
                    external_to_spot += amount

                # 外部转出
                elif user == addr_lower and dest != addr_lower:
                    external_out += amount

        # 计算真实本金
        true_capital = (
            total_deposits - total_withdrawals +
            external_to_spot - external_out
        )

        return {
            "total_deposits": total_deposits,
            "total_withdrawals": total_withdrawals,
            "external_to_spot": external_to_spot,
            "external_out": external_out,
            "true_capital": true_capital
        }

    def calculate_return_metrics(self, current_value: float, true_capital: float,
                                 first_trade_time: int, last_trade_time: int) -> Dict[str, float]:
        """
        计算累计收益率和年化收益率

        参数：
            current_value: 当前总账户价值
            true_capital: 真实本金（充值 - 提现）
            first_trade_time: 第一笔交易时间戳（毫秒）
            last_trade_time: 最后一笔交易时间戳（毫秒）

        返回：
            字典，包含：
            - cumulative_return: 累计收益率（百分比）
            - annualized_return: 年化收益率（百分比）
            - net_profit: 净盈利（美元）
            - trading_days: 交易天数
        """
        # 计算净盈利
        net_profit = current_value - true_capital

        # 计算累计收益率
        if true_capital > 0:
            cumulative_return = (net_profit / true_capital) * 100
        else:
            cumulative_return = 0.0

        # 计算交易天数
        if first_trade_time > 0 and last_trade_time > first_trade_time:
            trading_days = (last_trade_time - first_trade_time) / 1000 / 86400
        else:
            trading_days = 0.0

        # 计算年化收益率
        if trading_days > 0 and true_capital > 0:
            # 年化收益率 = ((1 + 累计收益率) ^ (365 / 交易天数) - 1) × 100%
            annual_factor = 365.0 / trading_days
            annualized_return = (math.pow(1 + cumulative_return / 100, annual_factor) - 1) * 100
        else:
            annualized_return = 0.0

        return {
            "cumulative_return": cumulative_return,
            "annualized_return": annualized_return,
            "net_profit": net_profit,
            "trading_days": trading_days
        }

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

    def calculate_sharpe_ratio_on_capital(self, fills: List[Dict], true_capital: float,
                                          risk_free_rate: float = 0.03) -> Dict[str, float]:
        """
        计算基于真实本金的夏普比率（方案 1: 推荐方法）

        该方法基于真实本金计算夏普比率,不受杠杆影响

        参数：
            fills: 成交记录列表
            true_capital: 真实本金（充值 - 提现 + 外部转入 - 外部转出）
            risk_free_rate: 无风险利率（年化，默认3%）

        返回：
            字典，包含：
            - sharpe_ratio: 每笔交易的夏普比率
            - annualized_sharpe: 年化夏普比率
            - mean_return_per_trade: 平均每笔收益率（相对本金）
            - std_dev: 收益率标准差
            - total_trades: 分析的交易数量

        算法说明：
            1. 对每笔有PnL的交易，计算收益率 = PnL / True_Capital
            2. 基于收益率序列计算均值和标准差
            3. Sharpe = (mean_return - rf) / std_dev
            4. 年化Sharpe = 每笔交易Sharpe × sqrt(年交易次数)

        优势：
            - ✅ 不受杠杆影响，真实反映风险收益比
            - ✅ 与累计收益率计算逻辑一致
            - ✅ 不受出入金影响（使用校正后的本金）
            - ✅ 反映真实的资金使用效率
        """
        if true_capital <= 0:
            return {
                "sharpe_ratio": 0,
                "annualized_sharpe": 0,
                "mean_return_per_trade": 0,
                "std_dev": 0,
                "total_trades": 0
            }

        trade_returns = []

        # 遍历所有成交记录，提取平仓交易的收益率
        for fill in fills:
            closed_pnl = float(fill.get('closedPnl', 0))

            # 只分析平仓交易（有PnL的交易）
            if closed_pnl == 0:
                continue

            # 计算交易收益率 = PnL / 真实本金
            trade_return = closed_pnl / true_capital
            trade_returns.append(trade_return)

        # 数据不足时返回零值
        if len(trade_returns) < 2:
            return {
                "sharpe_ratio": 0,
                "annualized_sharpe": 0,
                "mean_return_per_trade": 0,
                "std_dev": 0,
                "total_trades": 0
            }

        # 计算统计量：均值、方差、标准差
        mean_return = sum(trade_returns) / len(trade_returns)
        variance = sum((r - mean_return) ** 2 for r in trade_returns) / (len(trade_returns) - 1)
        std_dev = math.sqrt(variance)

        # 标准差为零时无法计算夏普比率
        if std_dev == 0:
            return {
                "sharpe_ratio": 0,
                "annualized_sharpe": 0,
                "mean_return_per_trade": mean_return,
                "std_dev": 0,
                "total_trades": len(trade_returns)
            }

        # 从实际数据计算平均持仓时间
        hold_stats = self.calculate_hold_time_stats(fills)
        avg_hold_days = hold_stats['allTimeAverage']

        # 如果没有持仓数据或持仓时间为0，使用默认值1天（保守估计）
        if avg_hold_days <= 0:
            avg_hold_days = 1.0

        # 计算每笔交易的无风险收益率（基于实际平均持仓时间）
        trade_rf_rate = (1 + risk_free_rate) ** (avg_hold_days / 365) - 1

        # 计算每笔交易的夏普比率
        sharpe_per_trade = (mean_return - trade_rf_rate) / std_dev

        # 推算年交易次数（用于年化）
        first_trade_time = next((f['time'] for f in fills if float(f.get('closedPnl', 0)) != 0), 0)
        last_trade_time = next((f['time'] for f in reversed(fills) if float(f.get('closedPnl', 0)) != 0), 0)

        if first_trade_time and last_trade_time:
            days = (last_trade_time - first_trade_time) / 1000 / 86400
            trades_per_year = len(trade_returns) / days * 365 if days > 0 else 365
        else:
            trades_per_year = 365  # 加密货币市场7×24小时交易，使用365天

        # 年化夏普比率 = 每笔交易夏普 × sqrt(年交易次数)
        annualized_sharpe = sharpe_per_trade * math.sqrt(trades_per_year)

        return {
            "sharpe_ratio": sharpe_per_trade,
            "annualized_sharpe": annualized_sharpe,
            "mean_return_per_trade": mean_return,
            "std_dev": std_dev,
            "total_trades": len(trade_returns)
        }

    def calculate_max_drawdown_on_capital(self, fills: List[Dict], true_capital: float) -> Dict[str, float]:
        """
        基于真实本金计算最大回撤（推荐方法）

        关键改进：使用真实本金而非持仓价值计算收益率，完全不受杠杆影响

        参数：
            fills: 成交记录列表
            true_capital: 真实本金（充值 - 提现 + 外部转入 - 外部转出）

        返回：
            字典，包含：
            - max_drawdown_pct: 最大回撤百分比
            - peak_return: 峰值累计收益率（百分比）
            - trough_return: 谷底累计收益率（百分比）
            - total_trades: 分析的交易数量

        算法说明：
            1. 每笔交易收益率 = closedPnL / true_capital（不是 position_value）
            2. 构建累计收益率序列（复利计算）
            3. 追踪峰值，计算每个点相对峰值的回撤
            4. 记录最大回撤及对应的峰值和谷底

        优势：
            - ✅ 不受杠杆影响，真实反映风险
            - ✅ 与 Sharpe Ratio 计算逻辑一致
            - ✅ 不受出入金影响
            - ✅ 反映真实的资金使用效率

        为什么使用真实本金？
            - 10倍杠杆：投入 $100，持仓价值 $1000
            - 亏损 $50：
              * 旧算法：-50/1000 = -5%（❌ 严重低估）
              * 新算法：-50/100 = -50%（✅ 真实风险）
        """
        if true_capital <= 0:
            return {
                "max_drawdown_pct": 0,
                "peak_return": 0,
                "trough_return": 0,
                "total_trades": 0
            }

        trade_returns = []

        # 提取每笔平仓交易的收益率
        for fill in fills:
            closed_pnl = float(fill.get('closedPnl', 0))

            # 只分析平仓交易
            if closed_pnl == 0:
                continue

            # ✅ 关键改进：使用真实本金计算收益率
            trade_return = closed_pnl / true_capital

            # 限制单笔收益率范围：[-0.99, 10.0]（防止极端值）
            # -0.99 = -99%（最多亏完）
            # 10.0 = 1000%（合理的最大盈利上限）
            trade_return = max(-0.99, min(trade_return, 10.0))
            trade_returns.append(trade_return)

        # 数据不足时返回零值
        if len(trade_returns) < 2:
            return {
                "max_drawdown_pct": 0,
                "peak_return": 0,
                "trough_return": 0,
                "total_trades": 0
            }

        # 构建累计收益率序列（复利计算，带上限保护）
        cumulative_returns = []
        cumulative = 1.0  # 从1.0开始（代表100%本金）
        MAX_CUMULATIVE = 10000.0  # 最大累计收益倍数（10000倍 = 1000000%）

        for ret in trade_returns:
            cumulative *= (1 + ret)  # 复利累积
            # 防止数值溢出：限制累计收益上限
            cumulative = min(cumulative, MAX_CUMULATIVE)
            cumulative_returns.append(cumulative)

        # 计算最大回撤
        peak = cumulative_returns[0]  # 初始峰值
        peak_index = 0  # 峰值位置
        max_drawdown = 0  # 最大回撤
        trough_value = peak  # 谷底值
        trough_index = 0  # 谷底位置

        for i, value in enumerate(cumulative_returns):
            # 更新峰值
            if value > peak:
                peak = value
                peak_index = i

            # 计算当前回撤 = (峰值 - 当前值) / 峰值
            drawdown = (peak - value) / peak * 100 if peak > 0 else 0

            # 更新最大回撤和谷底
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                trough_value = value
                trough_index = i

        # 限制最大回撤不超过100%
        max_drawdown = min(max_drawdown, 100.0)

        return {
            "max_drawdown_pct": max_drawdown,
            "peak_return": (peak - 1) * 100,  # 转换为百分比
            "trough_return": (trough_value - 1) * 100,
            "total_trades": len(trade_returns)
        }


def main():
    """
    主程序入口 - Hyperliquid交易分析示例

    演示如何使用ApexCalculator类分析用户交易表现
    """
    print("=" * 70)
    print("📊 Apex Liquid Bot 交易分析计算器")
    print("=" * 70)
    print("基于: Hyperliquid官方API + Apex Liquid Bot算法")
    print()

    # 初始化计算器
    calculator = ApexCalculator()

    # 示例用户地址（请替换为真实地址）
    user_address = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"

    print("💡 使用说明:")
    print("   请提供有效的Hyperliquid用户钱包地址进行分析")
    print("   地址格式示例: 0x1234567890123456789012345678901234567890")
    print()

    # 验证地址格式
    if calculator.api_client.validate_user_address(user_address):
        print(f"✓ 地址格式验证通过: {user_address}")
        print(f"→ 开始分析...\n")

        try:
            # 执行完整交易分析
            results = calculator.analyze_user(user_address, force_refresh=True)

            # 检查是否有错误
            if "error" not in results:
                print("\n" + "=" * 70)
                print("📈 分析结果摘要")
                print("=" * 70)
                print(f"用户地址: {results['user_address']}")
                print(f"分析时间: {results['analysis_timestamp']}")
                print()

                # 数据摘要
                data_summary = results.get('data_summary', {})
                print("📦 数据摘要:")
                print(f"  • 成交记录: {data_summary.get('total_fills', 0)} 条")
                print(f"  • 当前持仓: {data_summary.get('total_positions', 0)} 个")
                print(f"  • 账户价值: ${data_summary.get('account_value', 0):,.2f}")
                print(f"  • 已用保证金: ${data_summary.get('total_margin_used', 0):,.2f}")
                print()

                # 关键指标
                print("🎯 关键指标:")
                print(f"  • Profit Factor（盈亏因子）: {results.get('profit_factor', 0)}")
                print(f"  • Sharpe Ratio（夏普比率）: {results.get('sharpe_ratio', 0):.4f}")
                max_dd_on_capital = results.get('max_drawdown_on_capital', {})
                print(f"  • Max Drawdown（最大回撤）: {max_dd_on_capital.get('max_drawdown_pct', 0):.2f}%")

                win_rate = results.get('win_rate', {})
                print(f"  • Win Rate（胜率）: {win_rate.get('winRate', 0):.2f}%")
                print(f"  • Direction Bias（方向偏好）: {win_rate.get('bias', 50):.2f}%")
                print(f"  • Total Trades（总交易次数）: {win_rate.get('totalTrades', 0)}")

                hold_stats = results.get('hold_time_stats', {})
                print(f"  • Avg Hold Time（平均持仓时间）: {hold_stats.get('allTimeAverage', 0):.2f} 天")

                position_analysis = results.get('position_analysis', {})
                print(f"  • Current Positions（当前持仓）: {position_analysis.get('total_positions', 0)}")
                print(f"  • Unrealized PnL（未实现盈亏）: ${position_analysis.get('total_unrealized_pnl', 0):.2f}")

                print("\n" + "=" * 70)
                print("✅ 分析完成!")
                print("=" * 70)

            else:
                print(f"\n✗ 分析失败: {results['error']}")

        except Exception as e:
            print(f"\n✗ 分析过程中发生错误: {e}")
            print("\n🔍 故障排查:")
            print("  1. 检查网络连接是否正常")
            print("  2. 确认用户地址是否正确")
            print("  3. 验证Hyperliquid API是否可访问")
            print("  4. 查看是否存在防火墙或代理限制")

    else:
        print(f"✗ 地址格式无效: {user_address}")
        print("⚠ 请提供有效的以太坊地址格式（0x开头，42位十六进制字符）")

    print("\n" + "=" * 70)
    print("📖 使用说明")
    print("=" * 70)
    print("1. 将代码中的 user_address 替换为真实的Hyperliquid用户地址")
    print("2. 确保网络连接正常，可以访问Hyperliquid API")
    print("3. 运行脚本即可获取完整的交易分析报告")
    print("\n📚 参考文档:")
    print("   Hyperliquid API: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api")
    print("   Apex Liquid Bot: https://apexliquid.bot/")
    print("=" * 70)


if __name__ == "__main__":
    main()
