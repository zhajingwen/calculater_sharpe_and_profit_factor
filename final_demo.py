#!/usr/bin/env python3
"""
Apex Fork - 最终演示
基于Hyperliquid官方API和Apex Liquid Bot算法

这个演示展示了如何使用ApexCalculator分析真实的Hyperliquid用户数据
"""

from apex_fork import ApexCalculator

def main():
    print("🚀 Apex Fork - 最终演示")
    print("基于Hyperliquid官方API和Apex Liquid Bot算法")
    print("=" * 60)
    
    # 初始化计算器
    calculator = ApexCalculator()
    
    # 真实用户地址示例
    user_address = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"
    
    print(f"📊 分析用户: {user_address}")
    print("=" * 60)
    
    # 执行完整分析
    results = calculator.analyze_user(user_address, force_refresh=True)
    
    if "error" not in results:
        print("\n✅ 分析成功完成!")
        print("=" * 60)
        
        # 显示关键指标
        print("📈 关键交易指标:")
        print(f"  • Profit Factor: {results.get('profit_factor', 0):.4f}")
        print(f"  • Sharpe Ratio: {results.get('sharpe_ratio', 0):.4f}")
        
        win_rate = results.get('win_rate', {})
        if isinstance(win_rate, dict):
            win_rate_pct = win_rate.get('win_rate', 0)
        else:
            win_rate_pct = win_rate
        print(f"  • Win Rate: {win_rate_pct:.2f}%")
        
        direction_bias = results.get('direction_bias', {})
        if isinstance(direction_bias, dict):
            direction_bias_pct = direction_bias.get('direction_bias', 0)
        else:
            direction_bias_pct = direction_bias
        print(f"  • Direction Bias: {direction_bias_pct:.2f}%")
        
        print(f"  • Total Trades: {results.get('total_trades', 0)}")
        print(f"  • Max Drawdown: {results.get('max_drawdown', 0):.2f}%")
        print(f"  • Avg Hold Time: {results.get('avg_hold_time', 0):.2f} days")
        
        # 显示账户信息
        print("\n💰 账户信息:")
        print(f"  • Account Value: ${results.get('account_value', 0):,.2f}")
        print(f"  • Margin Used: ${results.get('margin_used', 0):,.2f}")
        print(f"  • Current Positions: {results.get('current_positions', 0)}")
        print(f"  • Unrealized PnL: ${results.get('unrealized_pnl', 0):,.2f}")
        
        # 显示数据摘要
        print("\n📊 数据摘要:")
        print(f"  • 成交记录: {results.get('total_fills', 0)} 条")
        print(f"  • 当前持仓: {results.get('current_positions', 0)} 个")
        print(f"  • 未成交订单: {results.get('open_orders', 0)} 个")
        
    else:
        print(f"\n❌ 分析失败: {results['error']}")
    
    print("\n" + "=" * 60)
    print("🎯 使用说明:")
    print("1. 将 user_address 替换为真实的Hyperliquid用户地址")
    print("2. 确保网络连接正常")
    print("3. 运行脚本获取完整的交易分析")
    print("\n📚 API文档: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api")
    print("🔗 项目地址: https://github.com/your-repo/apex-fork")

if __name__ == "__main__":
    main()
