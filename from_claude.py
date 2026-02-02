import requests
import json
from datetime import datetime, timedelta
from decimal import Decimal
import math

class HyperliquidAnalyzer:
    def __init__(self, address):
        self.address = address
        self.base_url = "https://api.hyperliquid.xyz/info"
        
    def post_request(self, data):
        """发送 POST 请求到 Hyperliquid API"""
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.base_url, json=data, headers=headers)
        if data['type'] == 'userSnapshot':
            print(response.text)
        print(data)
        print(response.status_code)
        return response.json()
    
    def get_user_state(self):
        """获取用户当前状态（包括持仓和账户信息）"""
        data = {
            "type": "clearinghouseState",
            "user": self.address
        }
        return self.post_request(data)
    
    def get_user_fills(self):
        """获取用户历史成交记录"""
        data = {
            "type": "userFills",
            "user": self.address
        }
        return self.post_request(data)
    
    def get_user_funding_history(self):
        """获取用户资金费率历史"""
        data = {
            "type": "userFunding",
            "user": self.address
        }
        return self.post_request(data)
    
    def get_snapshot_and_history(self):
        """获取账户快照和历史数据"""
        data = {
            "type": "userSnapshot",
            "user": self.address
        }
        return self.post_request(data)

    def calculate_profit_factor(self, fills_data, user_state):
        """
        计算 Profit Factor
        Profit Factor = 总盈利 / 总亏损
        """
        total_profit = Decimal('0')
        total_loss = Decimal('0')
        
        # 1. 统计已实现盈亏（从历史成交中计算）
        for fill in fills_data:
            if 'closedPnl' in fill and fill['closedPnl'] != '0':
                closed_pnl = Decimal(str(fill['closedPnl']))
                if closed_pnl > 0:
                    total_profit += closed_pnl
                else:
                    total_loss += abs(closed_pnl)
        
        # 2. 统计未实现盈亏（从当前持仓中获取）
        if user_state and 'assetPositions' in user_state:
            for position in user_state['assetPositions']:
                if 'position' in position and 'unrealizedPnl' in position['position']:
                    unrealized_pnl = Decimal(str(position['position']['unrealizedPnl']))
                    if unrealized_pnl > 0:
                        total_profit += unrealized_pnl
                    else:
                        total_loss += abs(unrealized_pnl)
        
        # 3. 计算 Profit Factor
        if total_loss != 0:
            profit_factor = float(total_profit / total_loss)
            return round(profit_factor, 2)
        else:
            return "1000+" if total_profit > 0 else 0
    
    def calculate_sharpe_ratio(self, account_history, period='all'):
        """
        计算 Sharpe 比率
        Sharpe = 平均日收益率 / 日收益率标准差
        """
        if not account_history or len(account_history) < 2:
            return 0
        
        # 1. 计算平均账户价值
        total_value = sum(Decimal(str(item['accountValue'])) 
                         for item in account_history)
        avg_value = total_value / len(account_history)
        
        if avg_value == 0:
            return 0
        
        # 2. 计算每日收益率（百分比）
        daily_returns = []
        for i in range(1, len(account_history)):
            prev_pnl = Decimal(str(account_history[i-1].get('pnl', 0)))
            curr_pnl = Decimal(str(account_history[i].get('pnl', 0)))
            daily_pnl = curr_pnl - prev_pnl
            
            # 日收益率 = (日PNL / 平均账户价值) * 100
            daily_return = float((daily_pnl / avg_value) * 100)
            daily_returns.append(daily_return)
        
        if len(daily_returns) < 2:
            return 0
        
        # 3. 计算平均日收益率
        mean_return = sum(daily_returns) / len(daily_returns)
        
        # 4. 计算标准差
        variance = sum((r - mean_return) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        std_dev = math.sqrt(variance)
        
        # 5. 计算 Sharpe 比率
        if std_dev == 0:
            return 0
        
        sharpe = mean_return / std_dev
        return round(sharpe, 4)
    
    def get_account_value_history(self):
        """
        获取账户价值历史
        注意：Hyperliquid 可能需要通过多个 API 调用来构建完整的历史数据
        """
        # 尝试获取快照数据
        # snapshot_data = self.get_snapshot_and_history()
        
        # 如果 API 不直接提供历史数据，我们需要从成交记录重建
        fills = self.get_user_fills()
        
        # 构建账户历史
        account_history = []
        
        # 按时间排序成交记录
        if fills:
            sorted_fills = sorted(fills, key=lambda x: x.get('time', 0))
            
            # 模拟账户价值变化
            running_pnl = Decimal('0')
            daily_data = {}
            
            for fill in sorted_fills:
                # print(fill)
                timestamp = fill.get('time', 0)
                date = datetime.fromtimestamp(timestamp / 1000).date()
                
                closed_pnl = Decimal(str(fill.get('closedPnl', 0)))
                running_pnl += closed_pnl
                
                if date not in daily_data:
                    daily_data[date] = {
                        'accountValue': 0,
                        'pnl': float(running_pnl),
                        'time': timestamp
                    }
                else:
                    daily_data[date]['pnl'] = float(running_pnl)
                # print(daily_data)
            
            # 获取当前账户价值
            user_state = self.get_user_state()
            print(f'user_state:{user_state}')
            if user_state and 'marginSummary' in user_state:
                current_value = Decimal(str(user_state['marginSummary'].get('accountValue', 0)))
                
                # 填充账户价值
                for date in sorted(daily_data.keys()):
                    daily_data[date]['accountValue'] = float(current_value)
                    account_history.append(daily_data[date])
        
        return account_history

    def analyze(self):
        """执行完整分析"""
        print(f"分析地址: {self.address}\n")
        print("=" * 60)
        
        # 1. 获取数据
        print("正在获取数据...")
        user_state = self.get_user_state()
        fills = self.get_user_fills()
        account_history = self.get_account_value_history()
        
        # 2. 显示基本信息
        if user_state and 'marginSummary' in user_state:
            margin_summary = user_state['marginSummary']
            print(f"\n账户基本信息:")
            print(f"  账户价值: ${float(margin_summary.get('accountValue', 0)):,.2f}")
            print(f"  已用保证金: ${float(margin_summary.get('totalMarginUsed', 0)):,.2f}")
            print(f"  未实现盈亏: ${float(margin_summary.get('totalNtlPos', 0)):,.2f}")
        
        # 3. 计算 Profit Factor
        print(f"\n计算 Profit Factor...")
        profit_factor = self.calculate_profit_factor(fills, user_state)
        print(f"  Profit Factor: {profit_factor}")
        
        # 4. 计算 Sharpe 比率
        print(f"\n计算 Sharpe 比率...")
        sharpe_ratio = self.calculate_sharpe_ratio(account_history)
        print(f"  Sharpe 比率: {sharpe_ratio}")
        
        # 5. 显示持仓信息
        if user_state and 'assetPositions' in user_state:
            positions = user_state['assetPositions']
            if positions:
                print(f"\n当前持仓 ({len(positions)} 个):")
                for pos in positions:
                    coin = pos['position']['coin']
                    szi = float(pos['position']['szi'])
                    unrealized_pnl = float(pos['position']['unrealizedPnl'])
                    print(f"  {coin}: 数量={szi:.4f}, 未实现盈亏=${unrealized_pnl:.2f}")
        
        # 6. 显示交易统计
        if fills:
            print(f"\n交易统计:")
            print(f"  总成交数: {len(fills)}")
            
            profitable_trades = sum(1 for f in fills if float(f.get('closedPnl', 0)) > 0)
            total_trades = len([f for f in fills if 'closedPnl' in f and f['closedPnl'] != '0'])
            
            if total_trades > 0:
                win_rate = (profitable_trades / total_trades) * 100
                print(f"  盈利交易: {profitable_trades}/{total_trades}")
                print(f"  胜率: {win_rate:.2f}%")
        
        print("\n" + "=" * 60)
        
        return {
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'user_state': user_state,
            'fills': fills
        }


# 使用示例
if __name__ == "__main__":
    address = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"
    
    analyzer = HyperliquidAnalyzer(address)
    results = analyzer.analyze()
    
    # 可以进一步处理结果
    print(f"\n最终结果:")
    print(f"Profit Factor: {results['profit_factor']}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']}")