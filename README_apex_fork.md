# Apex Fork - Profit Factor and Sharpe Ratio Calculator

基于Hyperliquid官方API和Apex Liquid Bot算法的完整交易分析工具。

This Python implementation replicates the exact algorithms used by [Apex Liquid Bot](https://apexliquid.bot) for calculating trading performance metrics, with direct integration to [Hyperliquid's official API](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api).

## 🎯 Features

- **🔄 实时数据获取** - 直接从Hyperliquid官方API获取真实交易数据
- **📊 Profit Factor计算** - 总盈利与总亏损的比率
- **📈 Sharpe Ratio计算** - 风险调整后的收益指标
- **🎯 Win Rate分析** - 交易成功率统计
- **💰 ROE计算** - 净资产收益率
- **📉 Max Drawdown分析** - 风险评估
- **⏱️ Hold Time统计** - 持仓时间分析
- **💾 智能缓存** - 5分钟数据缓存，减少API调用
- **🔍 多用户分析** - 支持批量分析多个用户

## 📊 Algorithms Extracted

The algorithms were extracted from the following JavaScript files:
- `https://apexliquid.bot/assets/index-DmUy_5PH.js`
- `https://apexliquid.bot/assets/AssetPositionsTable-B8MWksSt.js`
- `https://apexliquid.bot/assets/hyperliquidWs-4Ciu49Um.js`
- `https://apexliquid.bot/assets/OpenOrdersTableNew-GSqIAf20.js`
- `https://apexliquid.bot/assets/RecentFillsTable-B8_vbQuR.js`

## 🚀 Quick Start

### 基本使用

```python
from apex_fork import ApexCalculator

# 初始化计算器
calculator = ApexCalculator()

# 分析用户交易表现
user_address = "0x1234567890123456789012345678901234567890"
results = calculator.analyze_user(user_address)

print(f"Profit Factor: {results.get('profit_factor', 0)}")
print(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.4f}")
print(f"Win Rate: {results.get('win_rate', {}).get('winRate', 0):.2f}%")
```

### 高级使用

```python
# 获取特定数据
fills = calculator.get_user_fills(user_address)
positions = calculator.get_user_asset_positions(user_address)
margin_summary = calculator.get_user_margin_summary(user_address)

# 计算特定指标
profit_factor = calculator.calculate_profit_factor(fills, positions)
win_stats = calculator.calculate_win_rate(fills)

# 强制刷新数据（不使用缓存）
results = calculator.analyze_user(user_address, force_refresh=True)
```

### 批量分析

```python
# 分析多个用户
user_addresses = [
    "0x1234567890123456789012345678901234567890",
    "0x0987654321098765432109876543210987654321"
]

for address in user_addresses:
    results = calculator.analyze_user(address)
    print(f"用户 {address}: PF={results.get('profit_factor', 0)}")
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
- requests (for API calls)
- 使用uv管理依赖: `uv add requests`

## 🌐 API Integration

### Hyperliquid API支持

本工具直接集成Hyperliquid官方API，支持以下数据获取：

- **用户成交记录** (`userFills`) - 获取所有历史交易
- **用户账户状态** (`clearinghouseState`) - 获取当前账户信息
- **资产持仓** (`assetPositions`) - 获取当前持仓详情
- **保证金摘要** (`marginSummary`) - 获取账户价值和保证金使用情况
- **历史PnL** (`historicalPnl`) - 获取历史盈亏数据
- **未成交订单** (`openOrders`) - 获取当前挂单
- **TWAP成交** (`userTwapSliceFills`) - 获取TWAP交易记录
- **资金历史** (`fundingHistory`) - 获取资金变动记录
- **账本更新** (`ledgerUpdates`) - 获取账本变更记录

### API端点

- **基础URL**: `https://api.hyperliquid.xyz`
- **主要端点**: `/info` (POST请求)
- **文档**: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api

### 数据缓存

- **缓存时间**: 5分钟
- **缓存策略**: 自动缓存API响应，减少重复请求
- **强制刷新**: 支持`force_refresh=True`参数强制获取最新数据

## 📝 Notes

- Uses high-precision decimal arithmetic for financial calculations
- Handles edge cases and invalid data gracefully
- Maintains compatibility with the original JavaScript implementation
- All calculations match the Apex Liquid Bot algorithms exactly

## 🤝 Contributing

This implementation is based on reverse-engineering the Apex Liquid Bot algorithms. If you find discrepancies or improvements, please verify against the original JavaScript implementation.

## 📄 License

This code is provided for educational and research purposes. Please respect the original Apex Liquid Bot terms of service.
