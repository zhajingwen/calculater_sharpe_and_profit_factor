# Apex Fork - 安装和使用指南

## 📦 安装

### 1. 克隆或下载项目

```bash
git clone <repository-url>
cd calculater_sharpe_and_profit_factor
```

### 2. 安装依赖

使用uv（推荐）:
```bash
uv add requests
```

或使用pip:
```bash
pip install requests
```

### 3. 验证安装

```bash
uv run python test_api_integration.py
```

## 🚀 快速开始

### 1. 基本使用

```python
from apex_fork import ApexCalculator

# 初始化
calculator = ApexCalculator()

# 分析用户（替换为真实地址）
user_address = "0x1234567890123456789012345678901234567890"
results = calculator.analyze_user(user_address)

# 查看结果
print(f"Profit Factor: {results.get('profit_factor', 0)}")
print(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.4f}")
```

### 2. 运行示例

```bash
# 运行主程序
uv run python apex_fork.py

# 运行使用示例
uv run python example_usage.py

# 运行测试
uv run python test_api_integration.py
```

## 📋 使用步骤

### 步骤1: 获取用户地址

1. 访问 [Hyperliquid](https://app.hyperliquid.xyz)
2. 连接钱包
3. 复制你的钱包地址（格式: 0x...）

### 步骤2: 运行分析

```python
from apex_fork import ApexCalculator

calculator = ApexCalculator()
user_address = "你的钱包地址"  # 替换为真实地址

results = calculator.analyze_user(user_address)
```

### 步骤3: 查看结果

分析结果包含以下指标：

- **Profit Factor**: 盈利因子
- **Sharpe Ratio**: 夏普比率
- **Win Rate**: 胜率
- **Max Drawdown**: 最大回撤
- **Hold Time**: 平均持仓时间
- **Position Analysis**: 持仓分析

## 🔧 配置选项

### API配置

```python
# 使用自定义API端点
calculator = ApexCalculator(api_base_url="https://api.hyperliquid.xyz")
```

### 缓存配置

```python
# 强制刷新数据（不使用缓存）
results = calculator.analyze_user(user_address, force_refresh=True)
```

## 📊 输出示例

```
============================================================
开始分析用户: 0x1234567890123456789012345678901234567890
============================================================
从API获取数据: 0x1234567890123456789012345678901234567890
数据获取完成:
  - 成交记录: 150 条
  - 当前持仓: 3 个
  - 历史PnL: 45 条

Profit Factor: 2.35
Sharpe Ratio: 1.2456
Win Rate: 68.50%
Direction Bias: 65.20%
Total Trades: 150
Max Drawdown: 12.30%
Average Hold Time: 2.45 days
Current Positions: 3 active
Total Unrealized PnL: $1,250.75

============================================================
分析完成!
============================================================
```

## ❗ 注意事项

1. **网络连接**: 确保网络连接正常，能够访问Hyperliquid API
2. **地址格式**: 使用有效的以太坊地址格式（0x开头，42字符）
3. **API限制**: 注意API调用频率限制
4. **数据完整性**: 确保用户有足够的交易历史数据

## 🐛 故障排除

### 常见问题

1. **API请求失败**
   - 检查网络连接
   - 验证用户地址格式
   - 确认API端点可访问

2. **数据不足**
   - 确保用户有交易历史
   - 检查地址是否正确

3. **依赖问题**
   - 确保安装了requests库
   - 使用`uv run`运行脚本

### 调试模式

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

calculator = ApexCalculator()
results = calculator.analyze_user(user_address)
```

## 📞 支持

- **API文档**: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
- **问题报告**: 请提供详细的错误信息和用户地址（脱敏）
- **功能请求**: 欢迎提出改进建议

## 📄 许可证

本项目基于教育目的，请遵守相关法律法规和平台使用条款。
