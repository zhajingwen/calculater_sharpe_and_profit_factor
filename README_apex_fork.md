# Apex Fork - Profit Factor and Sharpe Ratio Calculator

This Python implementation replicates the exact algorithms used by [Apex Liquid Bot](https://apexliquid.bot) for calculating trading performance metrics.

## 🎯 Features

- **Profit Factor Calculation** - Ratio of total gains to total losses
- **Sharpe Ratio Calculation** - Risk-adjusted return metric
- **Win Rate Analysis** - Trading success statistics
- **ROE Calculation** - Return on Equity
- **Max Drawdown Analysis** - Risk assessment
- **Hold Time Statistics** - Position duration analysis

## 📊 Algorithms Extracted

The algorithms were extracted from the following JavaScript files:
- `https://apexliquid.bot/assets/index-DmUy_5PH.js`
- `https://apexliquid.bot/assets/AssetPositionsTable-B8MWksSt.js`
- `https://apexliquid.bot/assets/hyperliquidWs-4Ciu49Um.js`
- `https://apexliquid.bot/assets/OpenOrdersTableNew-GSqIAf20.js`
- `https://apexliquid.bot/assets/RecentFillsTable-B8_vbQuR.js`

## 🚀 Quick Start

```python
from apex_fork import ApexCalculator

# Initialize calculator
calculator = ApexCalculator()

# Sample trade data
fills = [
    {'closedPnl': 100.50, 'dir': 'Close Long'},
    {'closedPnl': -50.25, 'dir': 'Close Short'},
    {'closedPnl': 200.75, 'dir': 'Close Long'}
]

# Calculate Profit Factor
profit_factor = calculator.calculate_profit_factor(fills)
print(f"Profit Factor: {profit_factor}")

# Calculate Sharpe Ratio
portfolio_data = [
    [
        "perpAllTime",
        {
            "accountValueHistory": [
                [1640995200000, 10000],
                [1641081600000, 10100],
                [1641168000000, 10050]
            ],
            "pnlHistory": [
                [1640995200000, 0],
                [1641081600000, 100],
                [1641168000000, 50]
            ]
        }
    ]
]

sharpe_ratio = calculator.calculate_sharpe_ratio(portfolio_data)
print(f"Sharpe Ratio: {sharpe_ratio:.4f}")
```

## 📈 Profit Factor Algorithm

The Profit Factor is calculated as:

```
Profit Factor = Total Gains / Total Losses
```

**Special Cases:**
- If only gains: Returns `"1000+"`
- If only losses: Returns `0`
- If no trades: Returns `0`

**Implementation Details:**
- Includes both closed PnL from fills and unrealized PnL from current positions
- Uses high-precision decimal arithmetic for accuracy
- Handles edge cases gracefully

## 📊 Sharpe Ratio Algorithm

The Sharpe Ratio is calculated as:

```
Sharpe Ratio = (Average Daily Return) / (Standard Deviation of Daily Returns)
```

**Implementation Details:**
- Filters portfolio data by time period (1D, 7D, 30D, All Time)
- Calculates daily returns as percentage of account value
- Uses sample standard deviation (n-1 denominator)
- Returns 0 for insufficient data or zero volatility

## 🎯 Win Rate Algorithm

Calculates comprehensive trading statistics:

```python
{
    "winRate": 66.67,      # Percentage of winning trades
    "bias": 60.0,          # Long vs Short preference (50% = neutral)
    "totalTrades": 5       # Total number of trades
}
```

**Implementation Details:**
- Excludes zero PnL trades from win rate calculation
- Bias calculation: `((long_trades - short_trades) / total_trades * 100 + 100) / 2`
- Handles various trade direction formats

## 📋 Data Format Requirements

### Trade Fills
```python
fills = [
    {
        'closedPnl': 100.50,           # Realized P&L
        'dir': 'Close Long',           # Trade direction
        'openTime': 1640995200000,     # Opening timestamp (ms)
        'closeTime': 1641081600000     # Closing timestamp (ms)
    }
]
```

### Asset Positions
```python
positions = [
    {
        'position': {
            'unrealizedPnl': 75.30     # Unrealized P&L
        }
    }
]
```

### Portfolio Data
```python
portfolio_data = [
    [
        "perpAllTime",                 # Time period
        {
            "accountValueHistory": [   # Account value over time
                [timestamp, value],
                [timestamp, value]
            ],
            "pnlHistory": [            # P&L history
                [timestamp, pnl],
                [timestamp, pnl]
            ]
        }
    ]
]
```

## 🧪 Testing

Run the test suite to verify algorithm accuracy:

```bash
python test_apex_fork.py
```

The tests verify:
- Profit Factor calculations with various scenarios
- Sharpe Ratio calculations with known data
- Win Rate and bias calculations
- Edge case handling

## 📚 API Reference

### ApexCalculator Class

#### `calculate_profit_factor(fills, asset_positions=None)`
Calculate Profit Factor from trade data.

**Parameters:**
- `fills`: List of trade fills with 'closedPnl' field
- `asset_positions`: Optional list of current positions with 'unrealizedPnl'

**Returns:** Profit factor as float or "1000+" string

#### `calculate_sharpe_ratio(portfolio_data, period="perpAllTime", risk_free_rate=0.0)`
Calculate Sharpe Ratio from portfolio data.

**Parameters:**
- `portfolio_data`: Portfolio data with account value and P&L history
- `period`: Time period filter ("perpDay", "perpWeek", "perpMonth", "perpAllTime")
- `risk_free_rate`: Risk-free rate for Sharpe calculation

**Returns:** Sharpe ratio as float

#### `calculate_win_rate(fills)`
Calculate win rate and trading statistics.

**Parameters:**
- `fills`: List of trade fills

**Returns:** Dictionary with winRate, bias, and totalTrades

#### `calculate_roe(portfolio_data, period="perpAllTime")`
Calculate Return on Equity.

**Parameters:**
- `portfolio_data`: Portfolio data
- `period`: Time period filter

**Returns:** ROE as percentage

#### `calculate_max_drawdown(account_history)`
Calculate maximum drawdown from account value history.

**Parameters:**
- `account_history`: List of [timestamp, account_value] pairs

**Returns:** Maximum drawdown as percentage

#### `calculate_hold_time_stats(fills)`
Calculate average hold time statistics.

**Parameters:**
- `fills`: List of trade fills with openTime and closeTime

**Returns:** Dictionary with hold time statistics for different periods

## 🔧 Dependencies

- Python 3.7+
- No external dependencies (uses only standard library)

## 📝 Notes

- Uses high-precision decimal arithmetic for financial calculations
- Handles edge cases and invalid data gracefully
- Maintains compatibility with the original JavaScript implementation
- All calculations match the Apex Liquid Bot algorithms exactly

## 🤝 Contributing

This implementation is based on reverse-engineering the Apex Liquid Bot algorithms. If you find discrepancies or improvements, please verify against the original JavaScript implementation.

## 📄 License

This code is provided for educational and research purposes. Please respect the original Apex Liquid Bot terms of service.
