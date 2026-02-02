import requests
import re
import statistics

def is_open(dir_):
    return dir_ in ["Open Long", "Open Short"]

def is_close(dir_):
    return dir_ in ["Close Long", "Close Short", "Short > Long", "Long > Short"]

def get_side(dir_):
    return "Long" if dir_ in ["Open Long", "Close Long", "Short > Long"] else "Short"

def get_user_fills(user_address):
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
        # Assuming data is sorted ascending by time
        max_time = max(d['time'] for d in data)
        start_time = max_time + 1
    return fills

def get_historical_positions(user_address):
    fills = get_user_fills(user_address)
    # Filter out coins matching @\d+
    fills = [f for f in fills if not re.match(r'^@\d+$', f['coin'])]
    # Sort by time ascending
    fills.sort(key=lambda f: f['time'])
    # Group by coin
    groups = {}
    for f in fills:
        coin = f['coin']
        groups.setdefault(coin, []).append(f)
    historical = []
    for group in groups.values():
        t = []
        s = None
        for a in group:
            try:
                sz = float(a['sz'])
                px = float(a['px'])
                fee = float(a.get('fee', 0.0))
                start_position = float(a['startPosition'])
                closed_pnl = float(a['closedPnl'])
            except (KeyError, ValueError):
                continue  # Skip invalid fills
            i = abs(start_position)
            n = px * i if sz > i else px * sz
            dir_ = a['dir']
            side = get_side(dir_)
            if is_open(dir_):
                if s:
                    s['buyValue'] += px * sz
                    s['buySize'] += sz
                    s['totalFees'] += fee
                else:
                    s = {
                        'coin': a['coin'],
                        'side': side,
                        'dir': side,
                        'openTime': a['time'],
                        'buyValue': px * sz,
                        'buySize': sz,
                        'totalFees': fee,
                        'closedPnl': closed_pnl,
                        'sellValue': 0.0,
                        'sellSize': 0.0,
                        'positionValue': n
                    }
            elif s and is_close(dir_) and side == s['side']:
                s['sellValue'] += px * sz
                s['sellSize'] += sz
                s['totalFees'] += fee
                s['closedPnl'] += closed_pnl
                s['positionValue'] += n
                if sz >= i:
                    s['closeTime'] = a['time']
                    pnl = s['closedPnl'] - s['totalFees']
                    roi = (pnl * 100) / s['positionValue'] if s['positionValue'] != 0 else 0.0
                    entry_price = s['buyValue'] / s['buySize'] if s['buySize'] != 0 else 0.0
                    exit_price = s['sellValue'] / s['sellSize'] if s['sellSize'] != 0 else 0.0
                    pos = s.copy()
                    pos['pnl'] = pnl
                    pos['roi'] = roi
                    pos['entryPrice'] = entry_price
                    pos['exitPrice'] = exit_price
                    t.append(pos)
                    s = None
        historical.extend(t)
    return historical

def calculate_profit_factor_and_sharpe(historical_positions):
    """
    计算 Profit Factor 和 Sharpe Ratio 基于历史位置数据。

    :param historical_positions: 列表，每个元素是一个字典，包含 'pnl' (利润/损失) 和 'roi' (回报率，百分比形式)。
    :return: 元组 (profit_factor, sharpe_ratio)
    """
    if not historical_positions:
        return 0.0, 0.0

    # 计算 Profit Factor
    total_profit = sum(pos['pnl'] for pos in historical_positions if pos['pnl'] > 0)
    total_loss = sum(pos['pnl'] for pos in historical_positions if pos['pnl'] < 0)
    profit_factor = total_profit / abs(total_loss) if total_loss != 0 else 0.0  # 避免除以零

    # 计算 Sharpe Ratio
    returns = [pos['roi'] / 100 for pos in historical_positions]  # 将 ROI 转换为小数形式
    if len(returns) < 2:
        sharpe_ratio = 0.0
    else:
        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        sharpe_ratio = mean_return / std_return if std_return != 0 else 0.0
        # 注意: 这里未进行年化处理，因为 JS 代码中未明确指定时间-based 的年化因子。
        # 如果需要年化，可以添加如 sharpe_ratio *= math.sqrt(252) 假设交易日。

    return profit_factor, sharpe_ratio

if __name__ == "__main__":
    user_address = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"
    historical = get_historical_positions(user_address)
    pf, sharpe = calculate_profit_factor_and_sharpe(historical)
    print(f"Profit Factor: {pf}")
    print(f"Sharpe Ratio: {sharpe}")