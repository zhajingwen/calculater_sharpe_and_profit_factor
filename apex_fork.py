"""
Apex Liquid Bot - Profit Factor and Sharpe Ratio Calculator
基于Hyperliquid官方API和Apex Liquid Bot算法实现

This module implements the exact algorithms used by Apex Liquid Bot for calculating:
1. Profit Factor - Ratio of total gains to total losses
2. Sharpe Ratio - Risk-adjusted return metric

Features:
- 直接从Hyperliquid官方API获取真实数据
- 基于Apex Liquid Bot的精确算法计算
- 支持完整的交易分析功能

API Documentation: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
Algorithms extracted from:
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
from hyperliquid_api_client import HyperliquidAPIClient

# Set precision for decimal calculations
getcontext().prec = 50


class ApexCalculator:
    """
    Main calculator class implementing Apex Liquid Bot algorithms
    集成Hyperliquid官方API和Apex Liquid Bot算法
    """
    
    def __init__(self, api_base_url: str = "https://api.hyperliquid.xyz"):
        self.precision = 50
        self.api_client = HyperliquidAPIClient(api_base_url)
        self.cache = {}  # 数据缓存
        self.cache_ttl = 300  # 缓存5分钟
    
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self.cache:
            return False
        return time.time() - self.cache[key]['timestamp'] < self.cache_ttl
    
    def _get_cached_data(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        if self._is_cache_valid(key):
            return self.cache[key]['data']
        return None
    
    def _set_cache_data(self, key: str, data: Any) -> None:
        """设置缓存数据"""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def get_user_data(self, user_address: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取用户完整数据
        
        Args:
            user_address: 用户地址
            force_refresh: 是否强制刷新缓存
            
        Returns:
            用户完整数据
        """
        cache_key = f"user_data_{user_address}"
        
        if not force_refresh:
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                print(f"使用缓存数据: {user_address}")
                return cached_data
        
        print(f"从API获取数据: {user_address}")
        
        try:
            # 验证地址格式
            if not self.api_client.validate_user_address(user_address):
                raise ValueError(f"无效的用户地址格式: {user_address}")
            
            # 获取完整投资组合数据
            portfolio_data = self.api_client.get_user_portfolio_data(user_address)
            
            if not portfolio_data:
                raise Exception("未能获取用户数据")
            
            # 缓存数据
            self._set_cache_data(cache_key, portfolio_data)
            
            return portfolio_data
            
        except Exception as e:
            print(f"获取用户数据失败: {e}")
            return {}
    
    def get_user_fills(self, user_address: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        获取用户成交记录
        
        Args:
            user_address: 用户地址
            force_refresh: 是否强制刷新缓存
            
        Returns:
            成交记录列表
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
            print(f"获取成交记录失败: {e}")
            return []
    
    def get_user_asset_positions(self, user_address: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        获取用户资产持仓
        
        Args:
            user_address: 用户地址
            force_refresh: 是否强制刷新缓存
            
        Returns:
            资产持仓列表
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
            print(f"获取资产持仓失败: {e}")
            return []
    
    def get_user_margin_summary(self, user_address: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取用户保证金摘要
        
        Args:
            user_address: 用户地址
            force_refresh: 是否强制刷新缓存
            
        Returns:
            保证金摘要数据
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
            print(f"获取保证金摘要失败: {e}")
            return {}
    
    def calculate_profit_factor(self, fills: List[Dict], asset_positions: Optional[List[Dict]] = None) -> Union[float, str]:
        """
        Calculate Profit Factor based on Apex Liquid Bot algorithm
        
        Profit Factor = Total Gains / Total Losses
        
        Args:
            fills: List of trade fills with 'closedPnl' field
            asset_positions: Optional list of current asset positions with 'unrealizedPnl'
            
        Returns:
            Profit factor as float, or "1000+" if only gains, or 0 if no trades
        """
        if not fills and not asset_positions:
            return 0
        
        total_gains = Decimal('0')
        total_losses = Decimal('0')
        
        # Process closed PnL from fills
        for fill in fills:
            closed_pnl = Decimal(str(fill.get('closedPnl', 0)))
            if closed_pnl > 0:
                total_gains += closed_pnl
            elif closed_pnl < 0:
                total_losses += abs(closed_pnl)
        
        # Process unrealized PnL from current positions
        if asset_positions:
            for position in asset_positions:
                unrealized_pnl = Decimal(str(position.get('position', {}).get('unrealizedPnl', 0)))
                if unrealized_pnl > 0:
                    total_gains += unrealized_pnl
                elif unrealized_pnl < 0:
                    total_losses += abs(unrealized_pnl)
        
        # Calculate profit factor
        if total_losses == 0:
            return "1000+" if total_gains > 0 else 0
        
        profit_factor = total_gains / total_losses
        return float(profit_factor)
    
    def calculate_sharpe_ratio(self, portfolio_data: List[Dict], period: str = "perpAllTime", risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe Ratio based on Apex Liquid Bot algorithm
        
        Sharpe Ratio = (Average Daily Return) / (Standard Deviation of Daily Returns)
        
        Args:
            portfolio_data: Portfolio data with accountValueHistory and pnlHistory
            period: Time period filter ("perpDay", "perpWeek", "perpMonth", "perpAllTime")
            risk_free_rate: Risk-free rate (default 0.0)
            
        Returns:
            Sharpe ratio as float
        """
        # Filter data by period
        filtered_data = [item for item in portfolio_data if item[0] == period]
        if not filtered_data:
            return 0
        
        data = filtered_data[0][1]
        account_history = data.get('accountValueHistory', [])
        pnl_history = data.get('pnlHistory', [])
        
        if not account_history or not pnl_history:
            return 0
        
        # Map account value history to daily returns
        daily_returns = []
        for i, (timestamp, account_value) in enumerate(account_history):
            if i == 0:
                continue
            
            # Get PnL for this period
            current_pnl = pnl_history[i][1] if i < len(pnl_history) else 0
            previous_pnl = pnl_history[i-1][1] if i-1 < len(pnl_history) else 0
            period_pnl = current_pnl - previous_pnl
            
            # Calculate daily return as percentage
            if account_value > 0:
                daily_return = (period_pnl / account_value) * 100
                daily_returns.append(float(daily_return))
        
        if len(daily_returns) < 2:
            return 0
        
        # Calculate mean and standard deviation
        mean_return = sum(daily_returns) / len(daily_returns)
        
        # Calculate variance
        variance = sum((x - mean_return) ** 2 for x in daily_returns) / (len(daily_returns) - 1)
        std_deviation = math.sqrt(variance)
        
        if std_deviation == 0:
            return 0
        
        # Calculate Sharpe ratio
        sharpe_ratio = (mean_return - risk_free_rate) / std_deviation
        return sharpe_ratio
    
    def calculate_win_rate(self, fills: List[Dict]) -> Dict[str, float]:
        """
        Calculate win rate and trading statistics
        
        Args:
            fills: List of trade fills
            
        Returns:
            Dictionary with win rate, bias, and total trades
        """
        if not fills:
            return {"winRate": 0, "bias": 50, "totalTrades": 0}
        
        long_trades = 0
        short_trades = 0
        winning_trades = 0
        losing_trades = 0
        
        for fill in fills:
            closed_pnl = Decimal(str(fill.get('closedPnl', 0)))
            direction = fill.get('dir', '')
            
            # Count trade direction
            if direction in ['Open Long', 'Close Long', 'Short > Long']:
                long_trades += 1
            elif direction in ['Open Short', 'Close Short', 'Long > Short']:
                short_trades += 1
            
            # Count wins/losses (excluding zero PnL)
            if closed_pnl != 0:
                if closed_pnl > 0:
                    winning_trades += 1
                else:
                    losing_trades += 1
        
        total_trades = len(fills)
        total_pnl_trades = winning_trades + losing_trades
        
        # Calculate win rate
        win_rate = (winning_trades / total_pnl_trades * 100) if total_pnl_trades > 0 else 0
        
        # Calculate bias (long vs short preference)
        bias = ((long_trades - short_trades) / total_trades * 100 + 100) / 2 if total_trades > 0 else 50
        
        return {
            "winRate": win_rate,
            "bias": bias,
            "totalTrades": total_trades
        }
    
    def calculate_roe(self, portfolio_data: List[Dict], period: str = "perpAllTime") -> float:
        """
        Calculate Return on Equity (ROE) based on Apex Liquid Bot algorithm
        
        Args:
            portfolio_data: Portfolio data with accountValueHistory and pnlHistory
            period: Time period filter
            
        Returns:
            ROE as percentage
        """
        # Filter data by period
        filtered_data = [item for item in portfolio_data if item[0] == period]
        if not filtered_data:
            return 0.0
        
        data = filtered_data[0][1]
        account_history = data.get('accountValueHistory', [])
        pnl_history = data.get('pnlHistory', [])
        
        if not account_history or len(account_history) < 2:
            return 0.0
        
        # Get initial and final balances
        initial_balance = Decimal(str(account_history[0][1]))
        final_balance = Decimal(str(account_history[-1][1]))
        
        # Calculate cash flows (deposits/withdrawals)
        cash_flows = []
        for i in range(1, len(account_history)):
            current_balance = Decimal(str(account_history[i][1]))
            previous_balance = Decimal(str(account_history[i-1][1]))
            current_pnl = Decimal(str(pnl_history[i][1])) if i < len(pnl_history) else Decimal('0')
            previous_pnl = Decimal(str(pnl_history[i-1][1])) if i-1 < len(pnl_history) else Decimal('0')
            
            # Calculate cash flow (deposit/withdrawal)
            expected_balance = previous_balance + (current_pnl - previous_pnl)
            cash_flow = current_balance - expected_balance
            
            if abs(cash_flow) > Decimal('1e-9'):  # Only include significant cash flows
                cash_flows.append({
                    'amount': cash_flow,
                    'date': account_history[i][0]
                })
        
        # Calculate weighted average capital and ROI
        total_cash_flows = sum(cf['amount'] for cf in cash_flows)
        net_income = final_balance - initial_balance - total_cash_flows
        
        # Calculate weighted average capital (simplified)
        weighted_capital = initial_balance
        for cf in cash_flows:
            # Weight by time remaining in period
            weighted_capital += cf['amount'] * 0.5  # Simplified weighting
        
        if weighted_capital == 0:
            return 0.0
        
        roi = (net_income / weighted_capital) * 100
        return float(roi)
    
    def calculate_max_drawdown(self, account_history: List[List]) -> float:
        """
        Calculate maximum drawdown from account value history
        
        Args:
            account_history: List of [timestamp, account_value] pairs
            
        Returns:
            Maximum drawdown as percentage
        """
        if not account_history or len(account_history) < 2:
            return 0.0
        
        peak = Decimal(str(account_history[0][1]))
        max_drawdown = Decimal('0')
        
        for timestamp, value in account_history:
            current_value = Decimal(str(value))
            
            if current_value > peak:
                peak = current_value
            
            drawdown = (peak - current_value) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return float(max_drawdown)
    
    def calculate_hold_time_stats(self, fills: List[Dict]) -> Dict[str, float]:
        """
        Calculate average hold time statistics
        
        Args:
            fills: List of trade fills with openTime and closeTime
            
        Returns:
            Dictionary with hold time statistics
        """
        if not fills:
            return {
                "todayCount": 0,
                "last7DaysAverage": 0,
                "last30DaysAverage": 0,
                "allTimeAverage": 0
            }
        
        from datetime import datetime, timedelta
        
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        week_ago = today_start - timedelta(days=7)
        month_ago = today_start - timedelta(days=30)
        
        today_hold_times = []
        week_hold_times = []
        month_hold_times = []
        all_hold_times = []
        
        for fill in fills:
            if not fill.get('openTime') or not fill.get('closeTime'):
                continue
            
            open_time = datetime.fromtimestamp(fill['openTime'] / 1000)
            close_time = datetime.fromtimestamp(fill['closeTime'] / 1000)
            
            hold_time_days = (close_time - open_time).total_seconds() / 86400
            
            all_hold_times.append(hold_time_days)
            
            if close_time >= today_start:
                today_hold_times.append(hold_time_days)
            
            if close_time >= week_ago:
                week_hold_times.append(hold_time_days)
            
            if close_time >= month_ago:
                month_hold_times.append(hold_time_days)
        
        return {
            "todayCount": sum(today_hold_times) / len(today_hold_times) if today_hold_times else 0,
            "last7DaysAverage": sum(week_hold_times) / len(week_hold_times) if week_hold_times else 0,
            "last30DaysAverage": sum(month_hold_times) / len(month_hold_times) if month_hold_times else 0,
            "allTimeAverage": sum(all_hold_times) / len(all_hold_times) if all_hold_times else 0
        }
    
    def analyze_user(self, user_address: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        分析用户交易表现 - 主要方法
        
        Args:
            user_address: 用户地址
            force_refresh: 是否强制刷新数据
            
        Returns:
            完整的分析结果
        """
        print(f"\n{'='*60}")
        print(f"开始分析用户: {user_address}")
        print(f"{'='*60}")
        
        try:
            # 获取用户数据
            user_data = self.get_user_data(user_address, force_refresh)
            
            if not user_data:
                return {"error": "无法获取用户数据"}
            
            # 提取数据
            fills = user_data.get('fills', [])
            asset_positions = user_data.get('assetPositions', [])
            margin_summary = user_data.get('marginSummary', {})
            historical_pnl = user_data.get('historicalPnl', [])
            
            print(f"数据获取完成:")
            print(f"  - 成交记录: {len(fills)} 条")
            print(f"  - 当前持仓: {len(asset_positions)} 个")
            print(f"  - 历史PnL: {len(historical_pnl)} 条")
            
            # 计算各项指标
            results = {
                "user_address": user_address,
                "analysis_timestamp": datetime.now().isoformat(),
                "data_summary": {
                    "total_fills": len(fills),
                    "total_positions": len(asset_positions),
                    "account_value": margin_summary.get('accountValue', 0),
                    "total_margin_used": margin_summary.get('totalMarginUsed', 0)
                }
            }
            
            # 1. Profit Factor
            if fills:
                profit_factor = self.calculate_profit_factor(fills, asset_positions)
                results["profit_factor"] = profit_factor
                print(f"Profit Factor: {profit_factor}")
            else:
                results["profit_factor"] = 0
                print("Profit Factor: 无成交记录")
            
            # 2. Sharpe Ratio (需要构建账户价值历史)
            if historical_pnl and len(historical_pnl) > 1:
                # 构建简化的Sharpe Ratio计算
                sharpe_ratio = self._calculate_simple_sharpe_ratio(historical_pnl)
                results["sharpe_ratio"] = sharpe_ratio
                print(f"Sharpe Ratio: {sharpe_ratio:.4f}")
            else:
                results["sharpe_ratio"] = 0
                print("Sharpe Ratio: 数据不足")
            
            # 3. Win Rate
            if fills:
                win_stats = self.calculate_win_rate(fills)
                results["win_rate"] = win_stats
                print(f"Win Rate: {win_stats['winRate']:.2f}%")
                print(f"Direction Bias: {win_stats['bias']:.2f}%")
                print(f"Total Trades: {win_stats['totalTrades']}")
            else:
                results["win_rate"] = {"winRate": 0, "bias": 50, "totalTrades": 0}
                print("Win Rate: 无成交记录")
            
            # 4. Max Drawdown
            if historical_pnl:
                max_dd = self._calculate_max_drawdown_from_pnl(historical_pnl)
                results["max_drawdown"] = max_dd
                print(f"Max Drawdown: {max_dd:.2f}%")
            else:
                results["max_drawdown"] = 0
                print("Max Drawdown: 数据不足")
            
            # 5. Hold Time Stats
            if fills:
                hold_stats = self.calculate_hold_time_stats(fills)
                results["hold_time_stats"] = hold_stats
                print(f"Average Hold Time: {hold_stats['allTimeAverage']:.2f} days")
            else:
                results["hold_time_stats"] = {
                    "todayCount": 0, "last7DaysAverage": 0, 
                    "last30DaysAverage": 0, "allTimeAverage": 0
                }
                print("Hold Time Stats: 无成交记录")
            
            # 6. 当前持仓分析
            if asset_positions:
                position_analysis = self._analyze_current_positions(asset_positions)
                results["position_analysis"] = position_analysis
                print(f"Current Positions: {len(asset_positions)} active")
                print(f"Total Unrealized PnL: ${position_analysis.get('total_unrealized_pnl', 0):.2f}")
            else:
                results["position_analysis"] = {"total_positions": 0, "total_unrealized_pnl": 0}
                print("Current Positions: 无持仓")
            
            print(f"\n{'='*60}")
            print("分析完成!")
            print(f"{'='*60}")
            
            return results
            
        except Exception as e:
            error_msg = f"分析过程中发生错误: {e}"
            print(error_msg)
            return {"error": error_msg}
    
    def _calculate_simple_sharpe_ratio(self, historical_pnl: List[Dict]) -> float:
        """
        基于历史PnL计算简化的Sharpe Ratio
        
        Args:
            historical_pnl: 历史PnL数据
            
        Returns:
            Sharpe ratio
        """
        if len(historical_pnl) < 2:
            return 0
        
        # 提取PnL值
        pnl_values = [float(item.get('pnl', 0)) for item in historical_pnl]
        
        # 计算日收益率
        returns = []
        for i in range(1, len(pnl_values)):
            if pnl_values[i-1] != 0:
                daily_return = (pnl_values[i] - pnl_values[i-1]) / abs(pnl_values[i-1])
                returns.append(daily_return)
        
        if len(returns) < 2:
            return 0
        
        # 计算Sharpe Ratio
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = math.sqrt(variance)
        
        if std_dev == 0:
            return 0
        
        return mean_return / std_dev
    
    def _calculate_max_drawdown_from_pnl(self, historical_pnl: List[Dict]) -> float:
        """
        基于历史PnL计算最大回撤
        
        Args:
            historical_pnl: 历史PnL数据
            
        Returns:
            最大回撤百分比
        """
        if not historical_pnl:
            return 0
        
        # 提取PnL值并计算累计PnL
        pnl_values = [float(item.get('pnl', 0)) for item in historical_pnl]
        cumulative_pnl = []
        running_total = 0
        
        for pnl in pnl_values:
            running_total += pnl
            cumulative_pnl.append(running_total)
        
        if not cumulative_pnl:
            return 0
        
        peak = cumulative_pnl[0]
        max_drawdown = 0
        
        for value in cumulative_pnl:
            if value > peak:
                peak = value
            
            if peak != 0:
                drawdown = (peak - value) / abs(peak) * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        return max_drawdown
    
    def _analyze_current_positions(self, asset_positions: List[Dict]) -> Dict[str, Any]:
        """
        分析当前持仓
        
        Args:
            asset_positions: 资产持仓列表
            
        Returns:
            持仓分析结果
        """
        total_unrealized_pnl = 0
        total_position_value = 0
        long_positions = 0
        short_positions = 0
        
        for position in asset_positions:
            pos_data = position.get('position', {})
            unrealized_pnl = float(pos_data.get('unrealizedPnl', 0))
            position_value = float(pos_data.get('positionValue', 0))
            size = float(pos_data.get('szi', 0))
            
            total_unrealized_pnl += unrealized_pnl
            total_position_value += position_value
            
            if size > 0:
                long_positions += 1
            elif size < 0:
                short_positions += 1
        
        return {
            "total_positions": len(asset_positions),
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_position_value": total_position_value,
            "long_positions": long_positions,
            "short_positions": short_positions,
            "position_bias": "Long" if long_positions > short_positions else "Short" if short_positions > long_positions else "Neutral"
        }


def main():
    """
    使用Hyperliquid API的完整分析示例
    """
    print("=== Apex Liquid Bot Calculator with Hyperliquid API ===")
    print("基于Hyperliquid官方API和Apex Liquid Bot算法")
    print()
    
    # 初始化计算器
    calculator = ApexCalculator()
    
    # 示例用户地址 (请替换为真实地址)
    user_address = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"
    
    print("请提供有效的Hyperliquid用户地址进行分析")
    print("示例地址格式: 0x1234567890123456789012345678901234567890")
    print()
    
    # 检查地址格式
    if calculator.api_client.validate_user_address(user_address):
        print(f"地址格式有效: {user_address}")
        print("开始分析...")
        
        try:
            # 执行完整分析
            results = calculator.analyze_user(user_address, force_refresh=True)
            
            if "error" not in results:
                print("\n=== 分析结果摘要 ===")
                print(f"用户地址: {results['user_address']}")
                print(f"分析时间: {results['analysis_timestamp']}")
                print()
                
                data_summary = results.get('data_summary', {})
                print("数据摘要:")
                print(f"  - 成交记录: {data_summary.get('total_fills', 0)} 条")
                print(f"  - 当前持仓: {data_summary.get('total_positions', 0)} 个")
                print(f"  - 账户价值: ${data_summary.get('account_value', 0):,.2f}")
                print(f"  - 已用保证金: ${data_summary.get('total_margin_used', 0):,.2f}")
                print()
                
                print("关键指标:")
                print(f"  - Profit Factor: {results.get('profit_factor', 0)}")
                print(f"  - Sharpe Ratio: {results.get('sharpe_ratio', 0):.4f}")
                print(f"  - Max Drawdown: {results.get('max_drawdown', 0):.2f}%")
                
                win_rate = results.get('win_rate', {})
                print(f"  - Win Rate: {win_rate.get('winRate', 0):.2f}%")
                print(f"  - Direction Bias: {win_rate.get('bias', 50):.2f}%")
                print(f"  - Total Trades: {win_rate.get('totalTrades', 0)}")
                
                hold_stats = results.get('hold_time_stats', {})
                print(f"  - Avg Hold Time: {hold_stats.get('allTimeAverage', 0):.2f} days")
                
                position_analysis = results.get('position_analysis', {})
                print(f"  - Current Positions: {position_analysis.get('total_positions', 0)}")
                print(f"  - Unrealized PnL: ${position_analysis.get('total_unrealized_pnl', 0):.2f}")
                
            else:
                print(f"分析失败: {results['error']}")
                
        except Exception as e:
            print(f"分析过程中发生错误: {e}")
            print("\n请检查:")
            print("1. 网络连接是否正常")
            print("2. 用户地址是否正确")
            print("3. Hyperliquid API是否可访问")
    else:
        print(f"地址格式无效: {user_address}")
        print("请提供有效的以太坊地址格式")
    
    print("\n=== 使用说明 ===")
    print("1. 将 user_address 替换为真实的Hyperliquid用户地址")
    print("2. 确保网络连接正常")
    print("3. 运行脚本获取完整的交易分析")
    print("\nAPI文档: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api")


if __name__ == "__main__":
    main()
