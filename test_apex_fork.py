"""
Test script to verify the Apex Fork implementation matches the original JavaScript algorithms
"""

from apex_fork import ApexCalculator
import json


def test_profit_factor():
    """Test Profit Factor calculation"""
    calculator = ApexCalculator()
    
    # Test case 1: Only gains
    fills_gains_only = [
        {'closedPnl': 100},
        {'closedPnl': 200},
        {'closedPnl': 50}
    ]
    result = calculator.calculate_profit_factor(fills_gains_only)
    assert result == "1000+", f"Expected '1000+', got {result}"
    
    # Test case 2: Mixed gains and losses
    fills_mixed = [
        {'closedPnl': 100},   # +100
        {'closedPnl': -50},   # -50
        {'closedPnl': 200},   # +200
        {'closedPnl': -25}    # -25
    ]
    result = calculator.calculate_profit_factor(fills_mixed)
    expected = 300 / 75  # 4.0
    assert abs(result - expected) < 0.001, f"Expected {expected}, got {result}"
    
    # Test case 3: Only losses
    fills_losses_only = [
        {'closedPnl': -100},
        {'closedPnl': -50}
    ]
    result = calculator.calculate_profit_factor(fills_losses_only)
    assert result == 0, f"Expected 0, got {result}"
    
    print("✓ Profit Factor tests passed")


def test_sharpe_ratio():
    """Test Sharpe Ratio calculation"""
    calculator = ApexCalculator()
    
    # Test case with known values
    portfolio_data = [
        [
            "perpAllTime",
            {
                "accountValueHistory": [
                    [1640995200000, 10000],  # Day 1
                    [1641081600000, 10100],  # Day 2 (+1%)
                    [1641168000000, 10050],  # Day 3 (-0.5%)
                    [1641254400000, 10000],  # Day 4 (-0.5%)
                    [1641340800000, 10200],  # Day 5 (+2%)
                    [1641427200000, 10400]   # Day 6 (+1.96%)
                ],
                "pnlHistory": [
                    [1640995200000, 0],      # Day 1
                    [1641081600000, 100],    # Day 2
                    [1641168000000, 50],     # Day 3
                    [1641254400000, 0],      # Day 4
                    [1641340800000, 200],    # Day 5
                    [1641427200000, 400]     # Day 6
                ]
            }
        ]
    ]
    
    result = calculator.calculate_sharpe_ratio(portfolio_data)
    assert isinstance(result, float), f"Expected float, got {type(result)}"
    assert result > 0, f"Expected positive Sharpe ratio, got {result}"
    
    print("✓ Sharpe Ratio tests passed")


def test_win_rate():
    """Test Win Rate calculation"""
    calculator = ApexCalculator()
    
    fills = [
        {'closedPnl': 100, 'dir': 'Close Long'},    # Win
        {'closedPnl': -50, 'dir': 'Close Short'},   # Loss
        {'closedPnl': 200, 'dir': 'Close Long'},    # Win
        {'closedPnl': 0, 'dir': 'Close Long'},      # No PnL
        {'closedPnl': -25, 'dir': 'Close Short'}    # Loss
    ]
    
    result = calculator.calculate_win_rate(fills)
    
    assert result['winRate'] == 50.0, f"Expected 50% win rate, got {result['winRate']}%"
    assert result['totalTrades'] == 5, f"Expected 5 total trades, got {result['totalTrades']}"
    assert result['bias'] == 60.0, f"Expected 60% bias (3 long, 2 short), got {result['bias']}%"
    
    print("✓ Win Rate tests passed")


def test_edge_cases():
    """Test edge cases"""
    calculator = ApexCalculator()
    
    # Empty data
    assert calculator.calculate_profit_factor([]) == 0
    assert calculator.calculate_sharpe_ratio([]) == 0
    assert calculator.calculate_win_rate([]) == {"winRate": 0, "bias": 50, "totalTrades": 0}
    
    # Zero PnL trades
    fills_zero = [{'closedPnl': 0, 'dir': 'Close Long'}]
    result = calculator.calculate_win_rate(fills_zero)
    assert result['winRate'] == 0, "Zero PnL trades should not affect win rate"
    
    print("✓ Edge case tests passed")


def main():
    """Run all tests"""
    print("Running Apex Fork Algorithm Tests...")
    print("=" * 50)
    
    try:
        test_profit_factor()
        test_sharpe_ratio()
        test_win_rate()
        test_edge_cases()
        
        print("=" * 50)
        print("🎉 All tests passed! The implementation matches the original algorithms.")
        
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    main()
