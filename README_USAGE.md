# Apex Fork - 交易分析系统使用指南

## 🎯 项目简介

基于 Hyperliquid 官方 API 和 Apex Liquid Bot 算法的交易分析系统。

**核心特性**：
- ✅ **交易级别指标** - 完全不受出入金影响
- ⚠️ **账户级别对比** - 展示传统方法的局限性
- 📊 **专业报告** - 支持终端输出和 Markdown 报告
- 🔍 **全面分析** - Sharpe Ratio、Max Drawdown、Profit Factor 等

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip3 install --break-system-packages requests
```

### 2. 基本使用

```bash
# 终端输出分析结果
python3 final_demo.py

# 生成 Markdown 报告
python3 final_demo.py --report
```

### 3. 修改用户地址

编辑 `final_demo.py` 第 32 行：

```python
user_address = "YOUR_HYPERLIQUID_ADDRESS"
```

---

## 📊 核心指标说明

### 交易级别指标（推荐）

#### Sharpe Ratio（风险调整收益）

**计算方法**：
```
每笔交易收益率 = closedPnL / position_value
Sharpe Ratio = (平均收益率 - 无风险利率) / 收益率标准差
年化 Sharpe = 每笔 Sharpe × √(年交易次数)
```

**评级标准**：
- **优秀**: > 1.0
- **良好**: 0.5 ~ 1.0
- **一般**: 0 ~ 0.5
- **差**: < 0

#### Max Drawdown（最大回撤）

**计算方法**：
```
累计收益率序列 = ∏(1 + 每笔交易收益率)
最大回撤 = (峰值 - 谷底) / 峰值 × 100%
```

**风险等级**：
- **低风险**: < 20%
- **中等风险**: 20% ~ 50%
- **高风险**: > 50%

#### Profit Factor（盈利因子）

**计算方法**：
```
Profit Factor = 总盈利金额 / 总亏损金额
```

**评级标准**：
- **优秀**: > 2.0
- **良好**: 1.5 ~ 2.0
- **盈利**: 1.0 ~ 1.5
- **亏损**: < 1.0

---

## 🔧 文件说明

### 核心文件

- **`final_demo.py`** - 主程序入口，显示完整分析结果
- **`apex_fork.py`** - 核心计算模块，包含所有指标算法
- **`hyperliquid_api_client.py`** - API 客户端，封装 Hyperliquid API
- **`report_generator.py`** - 报告生成器，支持 Markdown 格式

### 文档文件

- **`ALGORITHM_OPTIMIZATION_SUMMARY.md`** - 算法优化总结
- **`CASH_FLOW_IMPACT_REPORT.md`** - 出入金影响分析
- **`README_USAGE.md`** - 本使用指南

---

## 📈 输出示例

### 终端输出

```
🚀 Apex Fork - 交易分析系统
基于Hyperliquid官方API和Apex Liquid Bot算法
✅ 完全不受出入金影响的准确指标

======================================================================
📈 核心指标（交易级别 - 完全不受出入金影响）
======================================================================

✅ Sharpe Ratio (交易级别):
  • 年化 Sharpe: 1.86
  • 每笔 Sharpe: 0.1170
  • 平均每笔收益率: 0.5351%
  • 收益率标准差: 4.4511%
  → 评级: ✅ 优秀的风险调整收益

✅ Max Drawdown (交易级别):
  • 最大回撤: 91.45%
  • 峰值累计收益: 14475.43%
  • 谷底累计收益: 1145.51%
  → 风险等级: 🔴 高风险

✅ 交易统计:
  • Profit Factor: 1.0940
  • Win Rate: 43.95%
  • Direction Bias: 88.75%
  • Total Trades: 2000
  • Avg Hold Time: 1.78 天
```

### Markdown 报告

生成的 Markdown 报告包含：
- 核心指标表格
- 策略评估总结
- 改进建议
- 对比分析
- 数据摘要

---

## 💡 为什么使用交易级别指标？

### 传统账户级别的问题

```python
# ❌ 账户级别（受出入金影响）
初始资金 = 当前账户价值 - 累计PnL
收益率 = PnL / 初始资金

# 问题：
# 1. 初始资金推算不准确（忽略出入金）
# 2. 账户价值被出入金扰动
# 3. 无法反映策略真实表现
```

### 交易级别的优势

```python
# ✅ 交易级别（完全不受影响）
每笔交易收益率 = closedPnL / position_value
策略表现 = 分析所有交易的收益率分布

# 优势：
# 1. 不需要账户价值
# 2. 不受出入金影响
# 3. 反映策略本质
# 4. 可跨账户对比
```

### 实际案例对比

| 指标 | 账户级别 | 交易级别 | 差异 |
|------|----------|----------|------|
| Sharpe Ratio | 0.04 | 1.86 | 42x |
| Max Drawdown | 105% | 91% | - |

**结论**：账户级别严重失真，推荐使用交易级别！

---

## 🔍 高级用法

### 自定义分析

```python
from apex_fork import ApexCalculator

# 初始化
calculator = ApexCalculator()

# 获取用户数据
user_data = calculator.get_user_data("YOUR_ADDRESS")
fills = user_data.get('fills', [])

# 计算交易级别 Sharpe Ratio
trade_sharpe = calculator.calculate_trade_level_sharpe_ratio(fills)
print(f"年化 Sharpe: {trade_sharpe['annualized_sharpe']:.2f}")

# 计算交易级别 Max Drawdown
trade_dd = calculator.calculate_trade_level_max_drawdown(fills)
print(f"最大回撤: {trade_dd['max_drawdown_pct']:.2f}%")
```

### 生成自定义报告

```python
from report_generator import generate_markdown_report

# 分析用户
results = calculator.analyze_user("YOUR_ADDRESS")

# 生成报告
report_path = generate_markdown_report(
    results,
    "YOUR_ADDRESS",
    "my_custom_report.md"
)
print(report_path)
```

---

## 🐛 故障排除

### 问题：ModuleNotFoundError: No module named 'requests'

**解决方案**：
```bash
pip3 install --break-system-packages requests
```

### 问题：分析失败，无法获取数据

**可能原因**：
1. 网络连接问题
2. 用户地址错误
3. API 限流

**解决方案**：
- 检查网络连接
- 验证用户地址格式
- 等待几分钟后重试

### 问题：Sharpe Ratio 为 0

**可能原因**：
1. 成交记录不足（< 2笔）
2. 所有交易的 closedPnL 都为 0

**解决方案**：
- 确保账户有足够的历史交易
- 检查是否有平仓交易

---

## 📚 参考资料

### API 文档
- [Hyperliquid API 文档](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api)

### 算法说明
- `ALGORITHM_OPTIMIZATION_SUMMARY.md` - 详细的算法优化说明
- `CASH_FLOW_IMPACT_REPORT.md` - 出入金影响分析

### 相关理论
- **Sharpe Ratio**: 诺贝尔经济学奖得主 William Sharpe 提出的风险调整收益指标
- **Max Drawdown**: 投资组合管理中的经典风险度量
- **Profit Factor**: 系统交易中的盈利能力指标

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

*最后更新: 2026-02-02*
