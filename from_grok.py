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

def get_historical_positions(user_address, debug=False):
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

    close_position_count = 0  # 统计平仓操作
    full_close_count = 0      # 统计完全平仓

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

                close_position_count += 1

                # 修复逻辑：检查平仓后的剩余仓位是否接近0
                # 而不是检查平仓大小是否大于等于交易前仓位
                remaining_position = abs(start_position - sz)  # 计算剩余仓位
                is_full_close = remaining_position < 0.01      # 剩余仓位 < 0.01 视为完全平仓

                if debug and close_position_count <= 10:
                    print(f"  平仓 #{close_position_count}: {a['coin']}")
                    print(f"    交易前仓位: {start_position}")
                    print(f"    平仓大小: {sz}")
                    print(f"    剩余仓位: {remaining_position}")
                    print(f"    是否完全平仓: {is_full_close}")
                    print()

                if is_full_close:
                    full_close_count += 1
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

    if debug:
        print(f"\n统计信息:")
        print(f"  总平仓操作数: {close_position_count}")
        print(f"  完全平仓数: {full_close_count}")

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

    # 添加调试信息
    print("获取交易数据...")
    fills = get_user_fills(user_address)
    print(f"总共获取到 {len(fills)} 条交易记录")

    # 过滤后的数据
    fills_filtered = [f for f in fills if not re.match(r'^@\d+$', f['coin'])]
    print(f"过滤后剩余 {len(fills_filtered)} 条交易记录")

    if fills_filtered:
        print(f"\n前3条交易示例:")
        for i, f in enumerate(fills_filtered[:3]):
            print(f"  {i+1}. {f['coin']} | dir: {f['dir']} | sz: {f['sz']} | startPosition: {f['startPosition']}")

    print("\n计算历史仓位...")
    print("\n=== 前10个平仓操作详情 ===")
    historical = get_historical_positions(user_address, debug=True)
    print(f"\n识别到 {len(historical)} 个完整的交易周期")

    if historical:
        print(f"\n前3个交易周期示例:")
        for i, pos in enumerate(historical[:3]):
            print(f"  {i+1}. {pos['coin']} | PnL: {pos['pnl']:.2f} | ROI: {pos['roi']:.2f}%")

    pf, sharpe = calculate_profit_factor_and_sharpe(historical)
    print(f"\n最终结果:")
    print(f"Profit Factor: {pf}")
    print(f"Sharpe Ratio: {sharpe}")