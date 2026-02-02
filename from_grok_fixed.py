import requests
import math
import statistics

def get_user_fills(user_address):
    """获取用户所有成交记录"""
    base_url = "https://api.hyperliquid.xyz/info"
    fills = []
    start_time = 0
    while True:
        body = {
            "type": "userFillsByTime",
            "user": user_address,
            "startTime": start_time,
            "aggregateByTime": True
        }
        response = requests.post(base_url, json=body)
        response.raise_for_status()
        data = response.json()
        if not data:
            break
        fills.extend(data)
        if len(data) < 2000:
            break
        max_time = max(d['time'] for d in data)
        start_time = max_time + 1
    return fills

def calculate_profit_factor(fills):
    """
    计算 Profit Factor（盈亏因子）

    盈亏因子 = 总盈利 / 总亏损

    参数：
        fills: 成交记录列表

    返回：
        float: 盈亏因子，如果无亏损返回 "1000+"
    """
    total_gains = 0.0
    total_losses = 0.0

    for fill in fills:
        closed_pnl = float(fill.get('closedPnl', 0))
        if closed_pnl > 0:
            total_gains += closed_pnl
        elif closed_pnl < 0:
            total_losses += abs(closed_pnl)

    if total_losses == 0:
        return "1000+" if total_gains > 0 else 0

    return total_gains / total_losses

def calculate_sharpe_ratio(fills, risk_free_rate=0.03):
    """
    计算 Sharpe Ratio（夏普比率）

    基于每笔交易的收益率计算，不受账户出入金影响

    参数：
        fills: 成交记录列表
        risk_free_rate: 无风险利率（年化，默认3%）

    返回：
        dict: 包含夏普比率、年化夏普比率等指标
    """
    trade_returns = []

    # 计算每笔交易的收益率
    for fill in fills:
        closed_pnl = float(fill.get('closedPnl', 0))

        # 只分析有 PnL 的交易
        if closed_pnl == 0:
            continue

        # 计算仓位价值 = 价格 × 数量
        px = float(fill.get('px', 0))
        sz = abs(float(fill.get('sz', 0)))
        position_value = px * sz

        if position_value > 0:
            # 交易收益率 = PnL / 仓位价值
            trade_return = closed_pnl / position_value
            trade_returns.append(trade_return)

    # 数据不足时返回零值
    if len(trade_returns) < 2:
        return {
            "sharpe_ratio": 0,
            "annualized_sharpe": 0,
            "mean_return": 0,
            "std_dev": 0,
            "total_trades": len(trade_returns)
        }

    # 计算统计量
    mean_return = statistics.mean(trade_returns)
    std_dev = statistics.stdev(trade_returns)

    # 标准差为零时无法计算
    if std_dev == 0:
        return {
            "sharpe_ratio": 0,
            "annualized_sharpe": 0,
            "mean_return": mean_return,
            "std_dev": 0,
            "total_trades": len(trade_returns)
        }

    # 假设平均持仓1天（保守估计）
    avg_hold_days = 1.0
    trade_rf_rate = (1 + risk_free_rate) ** (avg_hold_days / 365) - 1

    # 计算每笔交易的夏普比率
    sharpe_per_trade = (mean_return - trade_rf_rate) / std_dev

    # 推算年交易次数
    first_trade_time = next((f['time'] for f in fills if float(f.get('closedPnl', 0)) != 0), 0)
    last_trade_time = next((f['time'] for f in reversed(fills) if float(f.get('closedPnl', 0)) != 0), 0)

    if first_trade_time and last_trade_time:
        days = (last_trade_time - first_trade_time) / 1000 / 86400
        trades_per_year = len(trade_returns) / days * 365 if days > 0 else 365
    else:
        trades_per_year = 365

    # 年化夏普比率
    annualized_sharpe = sharpe_per_trade * math.sqrt(trades_per_year)

    return {
        "sharpe_ratio": sharpe_per_trade,
        "annualized_sharpe": annualized_sharpe,
        "mean_return": mean_return,
        "std_dev": std_dev,
        "total_trades": len(trade_returns)
    }

if __name__ == "__main__":
    user_address = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"

    print("获取交易数据...")
    fills = get_user_fills(user_address)
    print(f"总共获取到 {len(fills)} 条交易记录")

    # 统计有 PnL 的交易
    pnl_trades = [f for f in fills if float(f.get('closedPnl', 0)) != 0]
    print(f"有 PnL 的交易数: {len(pnl_trades)}")

    # 计算 Profit Factor
    print("\n计算 Profit Factor...")
    pf = calculate_profit_factor(fills)
    print(f"Profit Factor: {pf}")

    # 计算 Sharpe Ratio
    print("\n计算 Sharpe Ratio...")
    sharpe_result = calculate_sharpe_ratio(fills)
    print(f"Sharpe Ratio (per trade): {sharpe_result['sharpe_ratio']:.4f}")
    print(f"Annualized Sharpe Ratio: {sharpe_result['annualized_sharpe']:.4f}")
    print(f"Mean Return per Trade: {sharpe_result['mean_return']:.4f}")
    print(f"Std Dev: {sharpe_result['std_dev']:.4f}")
    print(f"Total Trades Analyzed: {sharpe_result['total_trades']}")
