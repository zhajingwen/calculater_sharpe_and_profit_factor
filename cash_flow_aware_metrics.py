#!/usr/bin/env python3
"""
考虑出入金影响的交易指标计算
实现 Time-Weighted Return (TWR) 和修正的 Sharpe Ratio / Max Drawdown
"""

import math
from typing import List, Dict, Tuple
from datetime import datetime


class CashFlowAwareMetrics:
    """考虑出入金影响的指标计算器"""

    def __init__(self, fills: List[Dict], current_account_value: float):
        """
        Args:
            fills: 交易填充记录
            current_account_value: 当前账户价值
        """
        self.fills = sorted(fills, key=lambda x: x.get('time', 0))
        self.current_account_value = current_account_value
        self.cash_flow_events = []  # 检测到的出入金事件

    def detect_cash_flows(self, threshold: float = 100) -> List[Dict]:
        """
        智能检测出入金事件

        方法：
        1. 构建累计 PnL 序列
        2. 寻找账户价值的异常跳变
        3. 当 account_value 出现不能由 PnL 解释的变化时，标记为出入金

        Args:
            threshold: 检测阈值（美元）

        Returns:
            出入金事件列表
        """
        cumulative_pnl = []
        running_pnl = 0

        for fill in self.fills:
            pnl = float(fill.get('closedPnl', 0))
            if pnl != 0:
                running_pnl += pnl
                cumulative_pnl.append({
                    'time': fill.get('time'),
                    'pnl': running_pnl
                })

        if not cumulative_pnl:
            return []

        # 推算初始资金
        final_pnl = cumulative_pnl[-1]['pnl']
        estimated_initial = self.current_account_value - final_pnl

        # 检查账户是否曾为负
        min_pnl = min(item['pnl'] for item in cumulative_pnl)
        min_account_value = estimated_initial + min_pnl

        events = []

        # 检测爆仓后补仓
        if min_account_value < -threshold and self.current_account_value > 0:
            # 找到最低点
            min_idx = next(i for i, item in enumerate(cumulative_pnl)
                          if item['pnl'] == min_pnl)

            # 估算补仓金额
            deposit_amount = -min_account_value + threshold  # 至少要补到不欠债

            events.append({
                'type': 'deposit',
                'time': cumulative_pnl[min_idx]['time'],
                'amount': deposit_amount,
                'reason': f'账户爆仓至 ${min_account_value:,.2f}，推测补仓',
                'confidence': 'high'
            })

        self.cash_flow_events = events
        return events

    def calculate_time_weighted_return(self) -> Dict[str, float]:
        """
        计算 Time-Weighted Return (TWR)

        TWR 不受出入金影响，是评估投资表现的标准方法

        公式：
        TWR = ∏(1 + R_i) - 1
        其中 R_i 是每个时期（两次出入金之间）的收益率

        Returns:
            {
                "twr": float,  # Time-Weighted Return
                "annualized_twr": float,  # 年化收益率
                "periods": int  # 计算周期数
            }
        """
        events = self.detect_cash_flows()

        # 构建累计 PnL 历史
        pnl_history = []
        cumulative_pnl = 0

        for fill in self.fills:
            pnl = float(fill.get('closedPnl', 0))
            if pnl != 0:
                cumulative_pnl += pnl
                pnl_history.append({
                    'time': fill.get('time'),
                    'pnl': cumulative_pnl
                })

        if not pnl_history:
            return {"twr": 0, "annualized_twr": 0, "periods": 0}

        # 推算初始资金
        final_pnl = pnl_history[-1]['pnl']
        initial_capital = self.current_account_value - final_pnl

        # 如果没有检测到出入金，简单计算
        if not events:
            twr = final_pnl / initial_capital if initial_capital > 0 else 0

            # 年化（假设交易时长）
            first_time = pnl_history[0]['time'] / 1000
            last_time = pnl_history[-1]['time'] / 1000
            days = (last_time - first_time) / 86400

            # 避免负值的分数次幂产生复数
            if 1 + twr > 0 and days > 0:
                annualized = (1 + twr) ** (365 / days) - 1
            else:
                annualized = 0

            return {
                "twr": twr,
                "annualized_twr": annualized,
                "periods": 1
            }

        # 有出入金：分段计算
        # 将历史分为多个时期（每次出入金分隔）
        event_times = sorted([e['time'] for e in events])

        period_returns = []

        # 时期1: 开始到第一次出入金
        period_start = 0
        period_initial_capital = initial_capital

        for event_time in event_times:
            # 找到这个时期的 PnL 变化
            period_pnls = [item for item in pnl_history
                          if (period_start == 0 or item['time'] > period_start)
                          and item['time'] <= event_time]

            if period_pnls:
                period_start_pnl = 0 if period_start == 0 else \
                    next((item['pnl'] for item in pnl_history if item['time'] <= period_start), 0)
                period_end_pnl = period_pnls[-1]['pnl']
                period_pnl_change = period_end_pnl - period_start_pnl

                # 计算这个时期的收益率
                period_return = period_pnl_change / period_initial_capital if period_initial_capital > 0 else 0
                period_returns.append(period_return)

                # 下一个时期的初始资金 = 当前价值 + 出入金
                event = next(e for e in events if e['time'] == event_time)
                period_initial_capital = period_initial_capital + period_pnl_change + event['amount']

            period_start = event_time

        # 最后一个时期：最后出入金到现在
        if event_times:
            final_period_pnls = [item for item in pnl_history
                                if item['time'] > event_times[-1]]

            if final_period_pnls:
                period_start_pnl = next((item['pnl'] for item in pnl_history
                                        if item['time'] <= event_times[-1]), 0)
                period_end_pnl = final_period_pnls[-1]['pnl']
                period_pnl_change = period_end_pnl - period_start_pnl

                period_return = period_pnl_change / period_initial_capital if period_initial_capital > 0 else 0
                period_returns.append(period_return)

        # 计算 TWR
        twr = 1.0
        for r in period_returns:
            twr *= (1 + r)
        twr -= 1

        # 年化
        first_time = pnl_history[0]['time'] / 1000
        last_time = pnl_history[-1]['time'] / 1000
        days = (last_time - first_time) / 86400

        # 避免负值的分数次幂产生复数
        if 1 + twr > 0 and days > 0:
            annualized_twr = (1 + twr) ** (365 / days) - 1
        else:
            annualized_twr = 0

        return {
            "twr": twr,
            "annualized_twr": annualized_twr,
            "periods": len(period_returns),
            "cash_flow_events": len(events)
        }

    def calculate_sharpe_ratio_with_cash_flows(self, risk_free_rate: float = 0.03) -> Dict[str, float]:
        """
        考虑出入金的 Sharpe Ratio 计算

        使用 TWR 方法计算收益率序列

        Args:
            risk_free_rate: 无风险利率（年化）

        Returns:
            {
                "sharpe_ratio": float,
                "annualized_sharpe": float,
                "mean_return": float,
                "std_dev": float
            }
        """
        events = self.detect_cash_flows()

        # 构建累计 PnL 历史
        pnl_history = []
        cumulative_pnl = 0

        for fill in self.fills:
            pnl = float(fill.get('closedPnl', 0))
            if pnl != 0:
                cumulative_pnl += pnl
                pnl_history.append({
                    'time': fill.get('time'),
                    'pnl': cumulative_pnl
                })

        if len(pnl_history) < 2:
            return {"sharpe_ratio": 0, "annualized_sharpe": 0,
                   "mean_return": 0, "std_dev": 0}

        # 推算初始资金
        final_pnl = pnl_history[-1]['pnl']
        initial_capital = self.current_account_value - final_pnl

        # 调整初始资金（如果有出入金）
        if events:
            # 从初始资金中减去入金金额
            total_deposits = sum(e['amount'] for e in events if e['type'] == 'deposit')
            initial_capital -= total_deposits

        # 构建账户价值序列
        account_values = [initial_capital + item['pnl'] for item in pnl_history]

        # 如果有出入金，在出入金点调整账户价值
        if events:
            event_dict = {e['time']: e['amount'] for e in events}

            adjusted_values = []
            cumulative_deposits = 0

            for i, item in enumerate(pnl_history):
                if item['time'] in event_dict:
                    cumulative_deposits += event_dict[item['time']]

                adjusted_value = initial_capital + item['pnl'] + cumulative_deposits
                adjusted_values.append(adjusted_value)

            account_values = adjusted_values

        # 计算收益率序列
        returns = []
        for i in range(1, len(account_values)):
            if account_values[i-1] > 0:
                ret = (account_values[i] - account_values[i-1]) / account_values[i-1]
                returns.append(ret)

        if len(returns) < 2:
            return {"sharpe_ratio": 0, "annualized_sharpe": 0,
                   "mean_return": 0, "std_dev": 0}

        # 计算统计量
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return {"sharpe_ratio": 0, "annualized_sharpe": 0,
                   "mean_return": mean_return, "std_dev": 0}

        # 计算 Sharpe Ratio
        # 假设 returns 是每笔交易的收益率，转换为日风险溢价
        daily_rf_rate = (1 + risk_free_rate) ** (1/252) - 1
        sharpe = (mean_return - daily_rf_rate) / std_dev

        # 年化（假设252个交易日）
        annualized_sharpe = sharpe * math.sqrt(252)

        return {
            "sharpe_ratio": sharpe,
            "annualized_sharpe": annualized_sharpe,
            "mean_return": mean_return,
            "std_dev": std_dev,
            "periods_with_cash_flows": len(events)
        }

    def calculate_max_drawdown_with_cash_flows(self) -> Dict[str, float]:
        """
        考虑出入金的 Max Drawdown 计算

        在出入金点重置基准，避免出入金掩盖真实回撤

        Returns:
            {
                "max_drawdown_pct": float,
                "peak_value": float,
                "trough_value": float,
                "peak_time": int,
                "trough_time": int
            }
        """
        events = self.detect_cash_flows()

        # 构建累计 PnL 历史
        pnl_history = []
        cumulative_pnl = 0

        for fill in self.fills:
            pnl = float(fill.get('closedPnl', 0))
            if pnl != 0:
                cumulative_pnl += pnl
                pnl_history.append({
                    'time': fill.get('time'),
                    'pnl': cumulative_pnl
                })

        if not pnl_history:
            return {"max_drawdown_pct": 0, "peak_value": 0,
                   "trough_value": 0, "peak_time": 0, "trough_time": 0}

        # 推算初始资金
        final_pnl = pnl_history[-1]['pnl']
        initial_capital = self.current_account_value - final_pnl

        # 调整初始资金（如果有出入金）
        if events:
            total_deposits = sum(e['amount'] for e in events if e['type'] == 'deposit')
            initial_capital -= total_deposits

        # 构建账户价值序列（考虑出入金）
        account_values = []
        cumulative_deposits = 0

        if events:
            event_dict = {e['time']: e['amount'] for e in events}

            for item in pnl_history:
                if item['time'] in event_dict:
                    cumulative_deposits += event_dict[item['time']]

                value = initial_capital + item['pnl'] + cumulative_deposits
                account_values.append({
                    'time': item['time'],
                    'value': value
                })
        else:
            account_values = [{
                'time': item['time'],
                'value': initial_capital + item['pnl']
            } for item in pnl_history]

        # 计算最大回撤
        peak = account_values[0]['value']
        max_drawdown = 0
        peak_time = account_values[0]['time']
        trough_value = peak
        trough_time = peak_time

        for item in account_values:
            value = item['value']

            if value > peak:
                peak = value
                peak_time = item['time']

            if peak > 0:
                drawdown = (peak - value) / peak * 100

                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    trough_value = value
                    trough_time = item['time']

        return {
            "max_drawdown_pct": max_drawdown,
            "peak_value": peak,
            "trough_value": trough_value,
            "peak_time": peak_time,
            "trough_time": trough_time,
            "cash_flow_adjusted": len(events) > 0
        }


# 测试代码
if __name__ == '__main__':
    from apex_fork import ApexCalculator

    calculator = ApexCalculator()
    user_address = '0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf'

    user_data = calculator.get_user_data(user_address, force_refresh=False)
    fills = user_data.get('fills', [])
    margin_summary = user_data.get('marginSummary', {})
    account_value = float(margin_summary.get('accountValue', 0))

    metrics = CashFlowAwareMetrics(fills, account_value)

    print('='*60)
    print('考虑出入金的指标计算')
    print('='*60)

    # 1. 检测出入金
    events = metrics.detect_cash_flows()
    print(f'\n检测到 {len(events)} 个出入金事件')
    for event in events:
        time_str = datetime.fromtimestamp(event['time']/1000).strftime('%Y-%m-%d %H:%M')
        print(f'  - {event["type"]}: ${event["amount"]:,.2f} at {time_str}')
        print(f'    原因: {event["reason"]}')

    # 2. Time-Weighted Return
    print('\n1️⃣ Time-Weighted Return:')
    twr_result = metrics.calculate_time_weighted_return()
    print(f'  TWR: {twr_result["twr"]:.2%}')
    print(f'  年化 TWR: {twr_result["annualized_twr"]:.2%}')
    print(f'  计算周期: {twr_result["periods"]}')

    # 3. Sharpe Ratio
    print('\n2️⃣ Sharpe Ratio (考虑出入金):')
    sharpe_result = metrics.calculate_sharpe_ratio_with_cash_flows()
    print(f'  Sharpe Ratio: {sharpe_result["sharpe_ratio"]:.4f}')
    print(f'  年化 Sharpe: {sharpe_result["annualized_sharpe"]:.4f}')
    print(f'  平均收益率: {sharpe_result["mean_return"]:.4%}')
    print(f'  标准差: {sharpe_result["std_dev"]:.4%}')

    # 4. Max Drawdown
    print('\n3️⃣ Max Drawdown (考虑出入金):')
    dd_result = metrics.calculate_max_drawdown_with_cash_flows()
    print(f'  最大回撤: {dd_result["max_drawdown_pct"]:.2f}%')
    print(f'  峰值: ${dd_result["peak_value"]:,.2f}')
    print(f'  谷底: ${dd_result["trough_value"]:,.2f}')
    print(f'  已调整出入金: {dd_result["cash_flow_adjusted"]}')
