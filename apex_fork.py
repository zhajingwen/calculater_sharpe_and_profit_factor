"""
Apex Liquid Bot - Profit Factor and Sharpe Ratio Calculator
Based on algorithms extracted from apexliquid.bot JavaScript files

This module implements the exact algorithms used by Apex Liquid Bot for calculating:
1. Profit Factor - Ratio of total gains to total losses
2. Sharpe Ratio - Risk-adjusted return metric

Algorithms extracted from:
- https://apexliquid.bot/assets/index-DmUy_5PH.js
- https://apexliquid.bot/assets/AssetPositionsTable-B8MWksSt.js
- https://apexliquid.bot/assets/hyperliquidWs-4Ciu49Um.js
- https://apexliquid.bot/assets/OpenOrdersTableNew-GSqIAf20.js
- https://apexliquid.bot/assets/RecentFillsTable-B8_vbQuR.js
"""

import math
from typing import List, Dict, Any, Optional, Union
from decimal import Decimal, getcontext

# Set precision for decimal calculations
getcontext().prec = 50


class ApexCalculator:
    """
    Main calculator class implementing Apex Liquid Bot algorithms
    """
    
    def __init__(self):
        self.precision = 50
    
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


def main():
    """
    Example usage of the Apex Calculator
    """
    calculator = ApexCalculator()
    
    # Example trade fills data
    sample_fills = [
        {
            'closedPnl': 100.50,
            'dir': 'Close Long',
            'openTime': 1640995200000,  # 2022-01-01
            'closeTime': 1641081600000   # 2022-01-02
        },
        {
            'closedPnl': -50.25,
            'dir': 'Close Short',
            'openTime': 1641168000000,  # 2022-01-03
            'closeTime': 1641254400000   # 2022-01-04
        },
        {
            'closedPnl': 200.75,
            'dir': 'Close Long',
            'openTime': 1641340800000,  # 2022-01-05
            'closeTime': 1641427200000   # 2022-01-06
        }
    ]
    
    # Example asset positions
    sample_positions = [
        {
            'position': {
                'unrealizedPnl': 75.30
            }
        },
        {
            'position': {
                'unrealizedPnl': -25.10
            }
        }
    ]
    
    # Example portfolio data
    sample_portfolio = [
        [
            "perpAllTime",
            {
                "accountValueHistory": [
                    [1640995200000, 10000],  # Day 1
                    [1641081600000, 10100],  # Day 2
                    [1641168000000, 10050],  # Day 3
                    [1641254400000, 10000],  # Day 4
                    [1641340800000, 10200],  # Day 5
                    [1641427200000, 10400]   # Day 6
                ],
                "pnlHistory": [
                    [1640995200000, 0],      # Day 1
                    [1641081600000, 100],    # Day 2
                    [1641168000000, 50],     # Day 3
                    [1641254400000, 0],      # Day 4
                    [1641340800000, 200],    # Day 5
                    [1641427200000, 400]     # Day 6
                ]
            }
        ]
    ]
    
    # Calculate metrics
    print("=== Apex Liquid Bot Calculator ===")
    print()
    
    # Profit Factor
    profit_factor = calculator.calculate_profit_factor(sample_fills, sample_positions)
    print(f"Profit Factor: {profit_factor}")
    
    # Sharpe Ratio
    sharpe_ratio = calculator.calculate_sharpe_ratio(sample_portfolio)
    print(f"Sharpe Ratio: {sharpe_ratio:.4f}")
    
    # Win Rate
    win_stats = calculator.calculate_win_rate(sample_fills)
    print(f"Win Rate: {win_stats['winRate']:.2f}%")
    print(f"Direction Bias: {win_stats['bias']:.2f}%")
    print(f"Total Trades: {win_stats['totalTrades']}")
    
    # ROE
    roe = calculator.calculate_roe(sample_portfolio)
    print(f"ROE: {roe:.2f}%")
    
    # Max Drawdown
    account_history = sample_portfolio[0][1]['accountValueHistory']
    max_dd = calculator.calculate_max_drawdown(account_history)
    print(f"Max Drawdown: {max_dd:.2f}%")
    
    # Hold Time Stats
    hold_stats = calculator.calculate_hold_time_stats(sample_fills)
    print(f"Average Hold Time (All Time): {hold_stats['allTimeAverage']:.2f} days")


if __name__ == "__main__":
    main()
