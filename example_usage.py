"""
Apex Fork - 使用示例
基于Hyperliquid官方API和Apex Liquid Bot算法的完整使用示例
"""

from apex_fork import ApexCalculator


def analyze_single_user():
    """分析单个用户的交易表现"""
    print("=== 单用户分析示例 ===")
    
    # 初始化计算器
    calculator = ApexCalculator()
    
    # 替换为真实的Hyperliquid用户地址
    user_address = "0x1234567890123456789012345678901234567890"
    
    print(f"分析用户: {user_address}")
    
    try:
        # 执行完整分析
        results = calculator.analyze_user(user_address, force_refresh=True)
        
        if "error" not in results:
            print("\n✓ 分析成功!")
            print(f"Profit Factor: {results.get('profit_factor', 0)}")
            print(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.4f}")
            print(f"Win Rate: {results.get('win_rate', {}).get('winRate', 0):.2f}%")
            print(f"Max Drawdown: {results.get('max_drawdown', 0):.2f}%")
        else:
            print(f"✗ 分析失败: {results['error']}")
            
    except Exception as e:
        print(f"✗ 发生错误: {e}")


def analyze_multiple_users():
    """分析多个用户的交易表现"""
    print("\n=== 多用户分析示例 ===")
    
    calculator = ApexCalculator()
    
    # 用户地址列表
    user_addresses = [
        "0x1234567890123456789012345678901234567890",
        "0x0987654321098765432109876543210987654321",
        # 添加更多地址...
    ]
    
    results_summary = []
    
    for user_address in user_addresses:
        print(f"\n分析用户: {user_address}")
        
        try:
            results = calculator.analyze_user(user_address, force_refresh=False)  # 使用缓存
            
            if "error" not in results:
                summary = {
                    "address": user_address,
                    "profit_factor": results.get('profit_factor', 0),
                    "sharpe_ratio": results.get('sharpe_ratio', 0),
                    "win_rate": results.get('win_rate', {}).get('winRate', 0),
                    "max_drawdown": results.get('max_drawdown', 0),
                    "total_trades": results.get('win_rate', {}).get('totalTrades', 0)
                }
                results_summary.append(summary)
                print(f"  ✓ 完成分析")
            else:
                print(f"  ✗ 分析失败: {results['error']}")
                
        except Exception as e:
            print(f"  ✗ 发生错误: {e}")
    
    # 显示汇总结果
    if results_summary:
        print(f"\n=== 分析汇总 ===")
        print(f"{'地址':<45} {'PF':<8} {'Sharpe':<8} {'Win%':<8} {'DD%':<8} {'Trades':<8}")
        print("-" * 90)
        
        for summary in results_summary:
            print(f"{summary['address']:<45} "
                  f"{summary['profit_factor']:<8} "
                  f"{summary['sharpe_ratio']:<8.3f} "
                  f"{summary['win_rate']:<8.1f} "
                  f"{summary['max_drawdown']:<8.1f} "
                  f"{summary['total_trades']:<8}")


def get_specific_metrics():
    """获取特定指标"""
    print("\n=== 获取特定指标示例 ===")
    
    calculator = ApexCalculator()
    user_address = "0x1234567890123456789012345678901234567890"
    
    try:
        # 只获取成交记录
        fills = calculator.get_user_fills(user_address)
        print(f"成交记录数量: {len(fills)}")
        
        # 只获取持仓信息
        positions = calculator.get_user_asset_positions(user_address)
        print(f"当前持仓数量: {len(positions)}")
        
        # 只获取保证金摘要
        margin_summary = calculator.get_user_margin_summary(user_address)
        account_value = margin_summary.get('accountValue', 0)
        print(f"账户价值: ${account_value:,.2f}")
        
        # 计算Profit Factor
        if fills:
            profit_factor = calculator.calculate_profit_factor(fills, positions)
            print(f"Profit Factor: {profit_factor}")
        
    except Exception as e:
        print(f"获取数据失败: {e}")


def main():
    """主函数"""
    print("Apex Fork - 使用示例")
    print("基于Hyperliquid官方API和Apex Liquid Bot算法")
    print("=" * 60)
    
    # 示例1: 单用户分析
    analyze_single_user()
    
    # 示例2: 多用户分析
    analyze_multiple_users()
    
    # 示例3: 获取特定指标
    get_specific_metrics()
    
    print("\n" + "=" * 60)
    print("使用说明:")
    print("1. 将示例中的地址替换为真实的Hyperliquid用户地址")
    print("2. 确保网络连接正常")
    print("3. 根据需要调整分析参数")
    print("\nAPI文档: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api")


if __name__ == "__main__":
    main()
