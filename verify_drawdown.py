#!/usr/bin/env python3
"""验证 Max Drawdown 计算"""
from apex_fork import ApexCalculator

def verify_drawdown(user_address):
    calculator = ApexCalculator()
    user_data = calculator.get_user_data(user_address, force_refresh=False)
    fills = user_data.get('fills', [])

    # 提取PNL
    trade_pnls = []
    trade_times = []

    for fill in fills:
        closed_pnl = float(fill.get('closedPnl', 0))
        if closed_pnl == 0:
            continue
        trade_pnls.append(closed_pnl)
        trade_times.append(fill.get('time', 0))

    # 构建累计PNL序列
    cumulative_pnls = []
    cumulative = 0.0

    for pnl in trade_pnls:
        cumulative += pnl
        cumulative_pnls.append(cumulative)

    print(f"总交易数: {len(trade_pnls)}")
    print(f"累计PNL序列长度: {len(cumulative_pnls)}")
    print(f"最终累计PNL: ${cumulative_pnls[-1]:,.2f}")
    print(f"最小累计PNL: ${min(cumulative_pnls):,.2f}")
    print(f"最大累计PNL: ${max(cumulative_pnls):,.2f}")

    # 手动计算最大回撤
    peak = cumulative_pnls[0]
    peak_index = 0
    max_drawdown = 0
    trough_value = peak
    trough_index = 0

    for i, value in enumerate(cumulative_pnls):
        if value > peak:
            peak = value
            peak_index = i

        drawdown = peak - value

        if drawdown > max_drawdown:
            max_drawdown = drawdown
            trough_value = value
            trough_index = i

    from datetime import datetime
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

    print(f"\n最大回撤计算:")
    print(f"  最大回撤: ${max_drawdown:,.2f}")
    print(f"  峰值PNL: ${peak:,.2f} (索引: {peak_index}, 日期: {peak_date})")
    print(f"  谷底PNL: ${trough_value:,.2f} (索引: {trough_index}, 日期: {trough_date})")
    print(f"  差值: ${peak - trough_value:,.2f}")

    # 打印前后几个点
    print(f"\n峰值附近:")
    for i in range(max(0, peak_index-2), min(len(cumulative_pnls), peak_index+3)):
        print(f"  索引 {i}: ${cumulative_pnls[i]:,.2f} ({format_date(trade_times[i])})")

    print(f"\n谷底附近:")
    for i in range(max(0, trough_index-2), min(len(cumulative_pnls), trough_index+3)):
        print(f"  索引 {i}: ${cumulative_pnls[i]:,.2f} ({format_date(trade_times[i])})")

if __name__ == "__main__":
    user_address = "0x8d8b1f0a704544f4c8adaf55a1063be1bb656cc9"
    verify_drawdown(user_address)
