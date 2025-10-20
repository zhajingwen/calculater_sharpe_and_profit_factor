import requests
import json
import statistics
import math

# Hyperliquid API endpoint
API_URL = "https://api.hyperliquid.xyz/info"

def fetch_hyperliquid_data(payload):
    """
    Helper function to fetch data from Hyperliquid API.
    """
    headers = {"Content-Type": "application/json"}
    response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API request failed: {response.text}")

def calculate_profit_factor(address):
    """
    Calculate Profit Factor based on user fills and current state.
    """
    # Fetch user fills (closed trades)
    fills_payload = {"type": "userFills", "user": address}
    fills_data = fetch_hyperliquid_data(fills_payload)
    fills = fills_data.get("fills", [])  # Adjust based on actual response structure

    # Fetch current user state (open positions)
    state_payload = {"type": "userState", "user": address}
    state_data = fetch_hyperliquid_data(state_payload)
    asset_positions = state_data.get("clearinghouseState", {}).get("assetPositions", [])  # Adjust path

    gains = 0.0
    losses = 0.0

    # Process closed fills
    for fill_group in fills:
        for fill in fill_group.get("fills", []):
            closed_pnl = float(fill.get("closedPnl", 0))
            if closed_pnl > 0:
                gains += closed_pnl
            else:
                losses += abs(closed_pnl)

    # Process open positions (unrealized PNL)
    for pos in asset_positions:
        unrealized_pnl = float(pos.get("position", {}).get("unrealizedPnl", 0))
        if unrealized_pnl > 0:
            gains += unrealized_pnl
        else:
            losses += abs(unrealized_pnl)

    if losses == 0:
        return "1000+" if gains > 0 else 0
    else:
        return round(gains / losses, 2)

def calculate_sharpe_ratio(address, period="perpAllTime"):
    """
    Calculate simplified Sharpe Ratio for the given period.
    """
    # Fetch portfolio data
    portfolio_payload = {"type": "portfolio", "user": address}
    portfolio_data = fetch_hyperliquid_data(portfolio_payload)

    # Find the entry for the period
    entry = next((e[1] for e in portfolio_data if e[0] == period), None)
    if not entry:
        return 0

    account_values = [float(val[1]) for val in entry.get("accountValueHistory", [])]
    pnls = [float(val[1]) for val in entry.get("pnlHistory", [])]

    if len(account_values) == 0 or len(pnls) < 2:
        return 0

    # Average account value
    avg_value = sum(account_values) / len(account_values)
    if avg_value == 0:
        return 0

    # Daily returns
    daily_returns = []
    for i in range(1, len(pnls)):
        daily_pnl = pnls[i] - pnls[i-1]
        daily_return = (daily_pnl / avg_value) * 100
        daily_returns.append(daily_return)

    if len(daily_returns) < 2:
        return 0

    # Mean and standard deviation
    mean = statistics.mean(daily_returns)
    variance = sum((r - mean) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
    std_dev = math.sqrt(variance)

    if std_dev == 0:
        return 0
    else:
        return round(mean / std_dev, 2)

# Example usage
if __name__ == "__main__":
    address = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"
    profit_factor = calculate_profit_factor(address)
    sharpe_ratio = calculate_sharpe_ratio(address)
    print(f"Profit Factor: {profit_factor}")
    print(f"Sharpe Ratio (All Time): {sharpe_ratio}")