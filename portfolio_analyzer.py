"""
Hyperliquid投资组合分析器
提供详细的数据解析、统计计算和格式化输出功能
"""

from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict


class PortfolioAnalyzer:
    """投资组合分析器 - 解析和分析Hyperliquid用户数据"""

    def __init__(self):
        self.reset_stats()

    def reset_stats(self):
        """重置统计数据"""
        self.stats = {
            'total_positions': 0,
            'long_positions': 0,
            'short_positions': 0,
            'isolated_positions': 0,
            'cross_positions': 0,
            'total_unrealized_pnl': 0.0,
            'total_position_value': 0.0,
            'total_margin_used': 0.0,
            'total_funding_all_time': 0.0,
            'winning_positions': 0,
            'losing_positions': 0,
            'top_winners': [],
            'top_losers': [],
            'leverage_distribution': defaultdict(int),
            'coin_categories': defaultdict(list)
        }

    def parse_user_state(self, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析用户状态数据

        Args:
            user_state: 原始用户状态数据

        Returns:
            解析后的结构化数据
        """
        if not user_state:
            return {}

        # 提取核心数据
        margin_summary = user_state.get('marginSummary', {})
        cross_margin_summary = user_state.get('crossMarginSummary', {})
        asset_positions = user_state.get('assetPositions', [])

        parsed_data = {
            # 账户总览
            'account_value': float(margin_summary.get('accountValue', 0)),
            'total_position_value': float(margin_summary.get('totalNtlPos', 0)),
            'total_raw_usd': float(margin_summary.get('totalRawUsd', 0)),
            'total_margin_used': float(margin_summary.get('totalMarginUsed', 0)),

            # 全仓信息
            'cross_account_value': float(cross_margin_summary.get('accountValue', 0)),
            'cross_position_value': float(cross_margin_summary.get('totalNtlPos', 0)),
            'cross_margin_used': float(cross_margin_summary.get('totalMarginUsed', 0)),

            # 维持保证金和可提取金额
            'maintenance_margin': float(user_state.get('crossMaintenanceMarginUsed', 0)),
            'withdrawable': float(user_state.get('withdrawable', 0)),

            # 时间戳
            'timestamp': user_state.get('time', 0),

            # 持仓列表
            'positions': self._parse_positions(asset_positions)
        }

        # 计算衍生指标
        if parsed_data['account_value'] > 0:
            parsed_data['margin_usage_rate'] = (parsed_data['total_margin_used'] /
                                                parsed_data['account_value'] * 100)
            parsed_data['maintenance_margin_rate'] = (parsed_data['maintenance_margin'] /
                                                     parsed_data['total_margin_used'] * 100
                                                     if parsed_data['total_margin_used'] > 0 else 0)
            parsed_data['withdrawable_rate'] = (parsed_data['withdrawable'] /
                                                parsed_data['account_value'] * 100)

        return parsed_data

    def _parse_positions(self, asset_positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        解析持仓列表

        Args:
            asset_positions: 原始持仓数据列表

        Returns:
            解析后的持仓列表
        """
        parsed_positions = []

        for asset in asset_positions:
            pos_type = asset.get('type', '')
            position = asset.get('position', {})

            if not position:
                continue

            # 解析杠杆信息
            leverage_info = position.get('leverage', {})
            leverage_type = leverage_info.get('type', 'cross')
            leverage_value = float(leverage_info.get('value', 1))

            # 解析持仓方向
            szi = float(position.get('szi', 0))
            is_long = szi > 0
            position_size = abs(szi)

            # 解析资金费率
            cum_funding = position.get('cumFunding', {})
            funding_all_time = float(cum_funding.get('allTime', 0))
            funding_since_open = float(cum_funding.get('sinceOpen', 0))

            # 解析价格和盈亏
            entry_px = float(position.get('entryPx', 0))
            position_value = float(position.get('positionValue', 0))
            unrealized_pnl = float(position.get('unrealizedPnl', 0))
            roe = float(position.get('returnOnEquity', 0))
            margin_used = float(position.get('marginUsed', 0))

            # 强平价格（可能为None）
            liq_px = position.get('liquidationPx')
            liquidation_price = float(liq_px) if liq_px is not None else None

            parsed_pos = {
                'coin': position.get('coin', 'UNKNOWN'),
                'type': pos_type,
                'direction': 'LONG' if is_long else 'SHORT',
                'is_long': is_long,
                'size': position_size,
                'raw_size': szi,

                # 杠杆信息
                'leverage_type': leverage_type,
                'leverage': leverage_value,
                'max_leverage': float(position.get('maxLeverage', 0)),
                'is_isolated': leverage_type == 'isolated',

                # 价格和价值
                'entry_price': entry_px,
                'position_value': position_value,
                'margin_used': margin_used,
                'liquidation_price': liquidation_price,

                # 盈亏数据
                'unrealized_pnl': unrealized_pnl,
                'roe': roe,
                'roe_percent': roe * 100,

                # 资金费率
                'funding_all_time': funding_all_time,
                'funding_since_open': funding_since_open,

                # 盈亏状态
                'is_winning': unrealized_pnl > 0,
                'pnl_status': 'WIN' if unrealized_pnl > 0 else 'LOSS' if unrealized_pnl < 0 else 'BREAK_EVEN'
            }

            parsed_positions.append(parsed_pos)

        return parsed_positions

    def calculate_statistics(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算详细的统计数据

        Args:
            parsed_data: 解析后的数据

        Returns:
            统计结果
        """
        self.reset_stats()
        positions = parsed_data.get('positions', [])

        if not positions:
            return self.stats

        # 分类统计
        long_positions = []
        short_positions = []
        winning_positions = []
        losing_positions = []

        for pos in positions:
            # 基础计数
            self.stats['total_positions'] += 1

            # 方向统计
            if pos['is_long']:
                self.stats['long_positions'] += 1
                long_positions.append(pos)
            else:
                self.stats['short_positions'] += 1
                short_positions.append(pos)

            # 杠杆类型统计
            if pos['is_isolated']:
                self.stats['isolated_positions'] += 1
            else:
                self.stats['cross_positions'] += 1

            # 累计数据
            self.stats['total_unrealized_pnl'] += pos['unrealized_pnl']
            self.stats['total_position_value'] += pos['position_value']
            self.stats['total_margin_used'] += pos['margin_used']
            self.stats['total_funding_all_time'] += pos['funding_all_time']

            # 盈亏统计
            if pos['is_winning']:
                self.stats['winning_positions'] += 1
                winning_positions.append(pos)
            elif pos['unrealized_pnl'] < 0:
                self.stats['losing_positions'] += 1
                losing_positions.append(pos)

            # 杠杆分布
            leverage_key = f"{int(pos['leverage'])}x"
            self.stats['leverage_distribution'][leverage_key] += 1

        # 计算胜率
        if self.stats['total_positions'] > 0:
            self.stats['win_rate'] = (self.stats['winning_positions'] /
                                     self.stats['total_positions'] * 100)
            self.stats['loss_rate'] = (self.stats['losing_positions'] /
                                      self.stats['total_positions'] * 100)

        # 计算方向偏好
        if self.stats['total_positions'] > 0:
            self.stats['long_rate'] = (self.stats['long_positions'] /
                                      self.stats['total_positions'] * 100)
            self.stats['short_rate'] = (self.stats['short_positions'] /
                                       self.stats['total_positions'] * 100)

        # Top盈利和亏损持仓
        self.stats['top_winners'] = sorted(winning_positions,
                                          key=lambda x: x['unrealized_pnl'],
                                          reverse=True)[:10]
        self.stats['top_losers'] = sorted(losing_positions,
                                         key=lambda x: x['unrealized_pnl'])[:10]

        # 按持仓价值排序的Top持仓
        self.stats['top_positions_by_value'] = sorted(positions,
                                                     key=lambda x: x['position_value'],
                                                     reverse=True)[:10]

        # 高风险持仓（ROE < -50%或杠杆>10x且亏损）
        self.stats['high_risk_positions'] = [
            pos for pos in positions
            if (pos['roe'] < -0.5) or
               (pos['leverage'] > 10 and pos['unrealized_pnl'] < 0)
        ]

        return self.stats

    def format_output(self, parsed_data: Dict[str, Any], stats: Dict[str, Any]) -> str:
        """
        格式化输出数据

        Args:
            parsed_data: 解析后的数据
            stats: 统计数据

        Returns:
            格式化的字符串
        """
        lines = []

        # 标题
        lines.append("=" * 80)
        lines.append("💼 Hyperliquid 投资组合分析报告".center(80))
        lines.append("=" * 80)

        # 账户总览
        lines.append("\n📊 账户总览")
        lines.append("-" * 80)
        lines.append(f"账户总价值:      ${parsed_data.get('account_value', 0):>20,.2f}")
        lines.append(f"持仓总价值:      ${parsed_data.get('total_position_value', 0):>20,.2f}")
        lines.append(f"已用保证金:      ${parsed_data.get('total_margin_used', 0):>20,.2f}")
        lines.append(f"维持保证金:      ${parsed_data.get('maintenance_margin', 0):>20,.2f}")
        lines.append(f"可提取金额:      ${parsed_data.get('withdrawable', 0):>20,.2f}")

        # 风险指标
        lines.append(f"\n保证金使用率:    {parsed_data.get('margin_usage_rate', 0):>19.2f}%")
        lines.append(f"维持保证金率:    {parsed_data.get('maintenance_margin_rate', 0):>19.2f}%")
        lines.append(f"可提取资金率:    {parsed_data.get('withdrawable_rate', 0):>19.2f}%")

        # 持仓统计
        lines.append("\n📈 持仓统计")
        lines.append("-" * 80)
        lines.append(f"总持仓数量:      {stats.get('total_positions', 0):>20}")
        lines.append(f"  └─ 多头持仓:   {stats.get('long_positions', 0):>20} "
                    f"({stats.get('long_rate', 0):>5.1f}%)")
        lines.append(f"  └─ 空头持仓:   {stats.get('short_positions', 0):>20} "
                    f"({stats.get('short_rate', 0):>5.1f}%)")
        lines.append(f"\n全仓持仓:        {stats.get('cross_positions', 0):>20}")
        lines.append(f"逐仓持仓:        {stats.get('isolated_positions', 0):>20}")

        # 盈亏统计
        lines.append("\n💰 盈亏统计")
        lines.append("-" * 80)
        total_pnl = stats.get('total_unrealized_pnl', 0)
        pnl_symbol = "📈" if total_pnl > 0 else "📉" if total_pnl < 0 else "➖"
        lines.append(f"{pnl_symbol} 未实现总盈亏:  ${total_pnl:>20,.2f}")
        lines.append(f"盈利持仓:        {stats.get('winning_positions', 0):>20} "
                    f"({stats.get('win_rate', 0):>5.1f}%)")
        lines.append(f"亏损持仓:        {stats.get('losing_positions', 0):>20} "
                    f"({stats.get('loss_rate', 0):>5.1f}%)")
        lines.append(f"\n累计资金费率:    ${stats.get('total_funding_all_time', 0):>20,.2f}")

        # 杠杆分布
        if stats.get('leverage_distribution'):
            lines.append("\n⚡ 杠杆分布")
            lines.append("-" * 80)
            for leverage, count in sorted(stats['leverage_distribution'].items(),
                                         key=lambda x: int(x[0].replace('x', ''))):
                percentage = (count / stats['total_positions'] * 100)
                lines.append(f"{leverage:>6} : {count:>4} 个持仓 ({percentage:>5.1f}%)")

        # Top盈利持仓
        if stats.get('top_winners'):
            lines.append("\n🏆 Top 10 盈利持仓")
            lines.append("-" * 80)
            lines.append(f"{'币种':<8} {'方向':<6} {'杠杆':<6} {'未实现盈亏':<18} {'ROE':<12}")
            lines.append("-" * 80)
            for pos in stats['top_winners'][:10]:
                lines.append(
                    f"{pos['coin']:<8} "
                    f"{pos['direction']:<6} "
                    f"{pos['leverage']:>3.0f}x  "
                    f"${pos['unrealized_pnl']:>15,.2f}  "
                    f"{pos['roe_percent']:>8.2f}%"
                )

        # Top亏损持仓
        if stats.get('top_losers'):
            lines.append("\n⚠️  Top 10 亏损持仓")
            lines.append("-" * 80)
            lines.append(f"{'币种':<8} {'方向':<6} {'杠杆':<6} {'未实现盈亏':<18} {'ROE':<12}")
            lines.append("-" * 80)
            for pos in stats['top_losers'][:10]:
                lines.append(
                    f"{pos['coin']:<8} "
                    f"{pos['direction']:<6} "
                    f"{pos['leverage']:>3.0f}x  "
                    f"${pos['unrealized_pnl']:>15,.2f}  "
                    f"{pos['roe_percent']:>8.2f}%"
                )

        # 高风险持仓
        if stats.get('high_risk_positions'):
            lines.append("\n🚨 高风险持仓警告")
            lines.append("-" * 80)
            lines.append(f"{'币种':<8} {'方向':<6} {'杠杆':<6} {'未实现盈亏':<18} "
                        f"{'ROE':<12} {'强平价':<15}")
            lines.append("-" * 80)
            for pos in stats['high_risk_positions'][:10]:
                liq_price = f"${pos['liquidation_price']:,.2f}" if pos['liquidation_price'] else "N/A"
                lines.append(
                    f"{pos['coin']:<8} "
                    f"{pos['direction']:<6} "
                    f"{pos['leverage']:>3.0f}x  "
                    f"${pos['unrealized_pnl']:>15,.2f}  "
                    f"{pos['roe_percent']:>8.2f}%  "
                    f"{liq_price:<15}"
                )

        # 报告时间
        timestamp = parsed_data.get('timestamp', 0)
        if timestamp:
            dt = datetime.fromtimestamp(timestamp / 1000)
            lines.append("\n" + "-" * 80)
            lines.append(f"报告生成时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

        lines.append("=" * 80)

        return "\n".join(lines)


def main():
    """测试分析器"""
    # 示例数据（使用你提供的真实数据结构）
    sample_data = {
        'marginSummary': {
            'accountValue': '6701199.8799740002',
            'totalNtlPos': '13111958.1704760008',
            'totalRawUsd': '2700392.6017300002',
            'totalMarginUsed': '2077445.510696'
        },
        'crossMarginSummary': {
            'accountValue': '6655258.0014760001',
            'totalNtlPos': '13058334.0724800006',
            'totalRawUsd': '2608165.6252359999',
            'totalMarginUsed': '2031503.6321980001'
        },
        'crossMaintenanceMarginUsed': '999789.477911',
        'withdrawable': '4431527.9827819997',
        'time': 1770011370408,
        'assetPositions': [
            {
                'type': 'oneWay',
                'position': {
                    'coin': 'BTC',
                    'szi': '13.0161',
                    'leverage': {'type': 'cross', 'value': 20},
                    'entryPx': '75925.8',
                    'positionValue': '979018.9776',
                    'unrealizedPnl': '-9238.937047',
                    'returnOnEquity': '-0.186974208',
                    'liquidationPx': None,
                    'marginUsed': '48950.94888',
                    'maxLeverage': 40,
                    'cumFunding': {
                        'allTime': '-128161.965033',
                        'sinceOpen': '-25.721198',
                        'sinceChange': '0.0'
                    }
                }
            }
        ]
    }

    analyzer = PortfolioAnalyzer()
    parsed_data = analyzer.parse_user_state(sample_data)
    stats = analyzer.calculate_statistics(parsed_data)
    output = analyzer.format_output(parsed_data, stats)

    print(output)


if __name__ == "__main__":
    main()
