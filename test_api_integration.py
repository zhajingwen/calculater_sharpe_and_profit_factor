"""
测试Hyperliquid API集成功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hyperliquid_api_client import HyperliquidAPIClient
from apex_fork import ApexCalculator


def test_api_client():
    """测试API客户端基本功能"""
    print("=== 测试Hyperliquid API客户端 ===")
    
    client = HyperliquidAPIClient()
    
    # 测试地址验证
    test_addresses = [
        "0x1234567890123456789012345678901234567890",  # 有效格式
        "invalid_address",  # 无效格式
        "",  # 空地址
        "0x123"  # 太短
    ]
    
    print("测试地址验证:")
    for addr in test_addresses:
        is_valid = client.validate_user_address(addr)
        print(f"  {addr}: {'✓' if is_valid else '✗'}")
    
    print("\n测试API连接...")
    try:
        # 使用一个已知的测试地址（如果有的话）
        test_user = "0x1234567890123456789012345678901234567890"
        
        # 测试获取用户状态
        print(f"尝试获取用户状态: {test_user}")
        user_state = client.get_user_state(test_user)
        print(f"用户状态获取: {'成功' if user_state else '失败'}")
        
        # 测试获取成交记录
        print(f"尝试获取成交记录: {test_user}")
        fills = client.get_user_fills(test_user)
        print(f"成交记录获取: {'成功' if fills is not None else '失败'}")
        if fills is not None:
            print(f"  成交记录数量: {len(fills)}")
        
    except Exception as e:
        print(f"API测试失败: {e}")
        print("这可能是正常的，因为测试地址可能不存在或API需要特定权限")


def test_calculator_integration():
    """测试计算器集成功能"""
    print("\n=== 测试Apex计算器集成 ===")
    
    calculator = ApexCalculator()
    
    # 测试缓存功能
    print("测试缓存功能:")
    test_key = "test_key"
    test_data = {"test": "data"}
    
    # 设置缓存
    calculator._set_cache_data(test_key, test_data)
    print("  缓存设置: ✓")
    
    # 获取缓存
    cached_data = calculator._get_cached_data(test_key)
    print(f"  缓存获取: {'✓' if cached_data == test_data else '✗'}")
    
    # 检查缓存有效性
    is_valid = calculator._is_cache_valid(test_key)
    print(f"  缓存有效性: {'✓' if is_valid else '✗'}")
    
    print("\n测试地址验证:")
    test_address = "0x1234567890123456789012345678901234567890"
    is_valid = calculator.api_client.validate_user_address(test_address)
    print(f"  地址验证: {'✓' if is_valid else '✗'}")


def test_with_real_address():
    """使用真实地址进行测试（如果提供）"""
    print("\n=== 真实地址测试 ===")
    
    # 这里可以添加一个真实的Hyperliquid用户地址进行测试
    real_address = None  # 请在这里添加真实的用户地址
    
    if real_address:
        print(f"使用真实地址进行测试: {real_address}")
        
        calculator = ApexCalculator()
        
        try:
            # 执行完整分析
            results = calculator.analyze_user(real_address, force_refresh=True)
            
            if "error" not in results:
                print("✓ 分析成功完成")
                print(f"  Profit Factor: {results.get('profit_factor', 0)}")
                print(f"  Sharpe Ratio: {results.get('sharpe_ratio', 0):.4f}")
                print(f"  Win Rate: {results.get('win_rate', {}).get('winRate', 0):.2f}%")
            else:
                print(f"✗ 分析失败: {results['error']}")
                
        except Exception as e:
            print(f"✗ 测试失败: {e}")
    else:
        print("未提供真实地址，跳过真实数据测试")
        print("要测试真实数据，请在 real_address 变量中设置有效的Hyperliquid用户地址")


def main():
    """主测试函数"""
    print("Hyperliquid API集成测试")
    print("=" * 50)
    
    try:
        # 测试API客户端
        test_api_client()
        
        # 测试计算器集成
        test_calculator_integration()
        
        # 测试真实地址（如果提供）
        test_with_real_address()
        
        print("\n" + "=" * 50)
        print("测试完成!")
        print("\n使用说明:")
        print("1. 确保网络连接正常")
        print("2. 在 test_with_real_address() 函数中设置真实的用户地址")
        print("3. 运行 python apex_fork.py 进行完整分析")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")


if __name__ == "__main__":
    main()
