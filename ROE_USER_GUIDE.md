# 24小时ROE指标使用指南

## 什么是ROE？

**ROE (Return on Equity)** 是一个衡量资金使用效率的关键指标。

### 核心概念

```
24h ROE (%) = (24小时累计PNL / 起始权益) × 100
```

**示例计算**:
- 24小时前账户权益: $10,000
- 24小时累计PNL: +$250
- 24h ROE = (250 / 10000) × 100 = **+2.5%**

### 为什么重要？

1. **考虑规模**: 与绝对盈亏不同，ROE考虑了账户规模
2. **可比性**: 适合对比不同规模账户的交易表现
3. **效率指标**: 反映资金使用效率，而非绝对金额

---

## 如何使用

### 命令行使用

```bash
# 查看ROE（在CLI输出中）
python main.py 0x你的地址

# 生成包含ROE的报告
python main.py 0x你的地址 -r
```

### 输出示例

#### CLI输出

```
  ┌─ 24小时ROE 📈
  │
  ┌────────────────────────────┬────────────────┬────────────────────────────┐
  指标                           │ 数值               │ 说明
  ├────────────────────────────┼────────────────┼────────────────────────────┤
  24h ROE                      │          +2.35% │ 📈 盈利
  起始权益 (24h前)                  │       $10,000.00 │ 计算基准
  当前权益                         │       $10,235.00 │ 最新账户价值
  24h PNL                      │         +$235.00 │ 期间盈亏
  更新时间                         │ 2026-02-04 13:45 │ 数据时间戳
  └────────────────────────────┴────────────────┴────────────────────────────┘
```

#### Markdown报告

报告文件会包含完整的ROE部分，包括：
- ROE百分比及评级
- 起始权益和当前权益
- 24小时PNL
- 计算公式说明
- 指标解释

---

## ROE评级系统

| ROE范围 | 评级 | 说明 |
|---------|------|------|
| ≥10% | 🔥 极佳 | 极高收益率，表现优异 |
| ≥5% | ✅ 优秀 | 高收益率，表现良好 |
| ≥0% | 📈 盈利 | 正收益，稳定盈利 |
| ≥-5% | ⚠️ 小幅亏损 | 小幅负收益，需注意 |
| <-5% | 📉 较大亏损 | 显著负收益，需警惕 |

---

## 常见问题

### Q1: 为什么我的ROE是负数？

**A**: 负数ROE表示24小时内账户价值下降。这反映了交易亏损或市场波动导致的未实现损失。

### Q2: ROE和累计总盈亏有什么区别？

**A**:
- **累计总盈亏**: 绝对金额，不考虑账户规模
- **24h ROE**: 百分比，考虑账户规模，更适合对比不同账户

例如：
- 账户A: $100盈利，账户规模$1,000 → ROE = 10%
- 账户B: $100盈利，账户规模$10,000 → ROE = 1%

账户A的资金使用效率更高。

### Q3: 为什么显示"账户历史不足24小时"？

**A**: 这表示你的Hyperliquid账户开户时间不足24小时。系统仍会计算ROE，但基于实际可用的历史时长。

### Q4: ROE数据多久更新一次？

**A**:
- 实时：每次运行分析时从API获取最新数据
- 缓存：5分钟内重复查询使用缓存（减少API请求）
- 强制刷新：使用force_refresh参数

### Q5: 如果ROE显示错误怎么办？

**A**: 可能的原因：
1. **API请求失败**: 检查网络连接
2. **数据格式异常**: Hyperliquid API可能暂时不可用
3. **起始权益为0**: 24小时前账户可能没有资金

错误会显示具体信息，帮助诊断问题。

### Q6: ROE能代替Sharpe Ratio吗？

**A**: 不能。它们衡量不同的方面：
- **ROE**: 资金使用效率（24小时快照）
- **Sharpe Ratio**: 风险调整后收益（考虑波动性）

两者结合使用可以更全面地评估交易表现。

---

## Python API使用

### 基础用法

```python
from apex_fork import ApexCalculator

# 创建计算器
calculator = ApexCalculator()

# 计算ROE
roe_metrics = calculator.calculate_24h_roe(
    user_address="0x你的地址",
    force_refresh=False  # 是否强制刷新缓存
)

# 检查数据有效性
if roe_metrics.is_valid:
    print(f"24h ROE: {roe_metrics.roe_percent:.2f}%")
    print(f"起始权益: ${roe_metrics.start_equity:,.2f}")
    print(f"当前权益: ${roe_metrics.current_equity:,.2f}")
    print(f"24h PNL: ${roe_metrics.pnl_24h:,.2f}")
else:
    print(f"错误: {roe_metrics.error_message}")
```

### 高级用法

```python
# 检查账户历史是否充足
if not roe_metrics.is_sufficient_history:
    print(f"警告: 账户历史仅有 {roe_metrics.account_age_hours:.1f} 小时")

# 获取时间范围
print(f"起始时间: {roe_metrics.start_time}")
print(f"结束时间: {roe_metrics.end_time}")

# 强制刷新缓存
fresh_roe = calculator.calculate_24h_roe(
    user_address="0x你的地址",
    force_refresh=True
)
```

### ROEMetrics数据类

```python
@dataclass
class ROEMetrics:
    roe_percent: float              # ROE百分比
    start_equity: float             # 起始权益
    current_equity: float           # 当前权益
    pnl_24h: float                  # 24小时PNL
    start_time: datetime            # 起始时间
    end_time: datetime              # 结束时间
    is_valid: bool                  # 数据是否有效
    error_message: Optional[str]    # 错误信息
    account_age_hours: Optional[float]  # 账户年龄（小时）
    is_sufficient_history: bool     # 历史是否充足（≥24h）
```

---

## 技术细节

### 数据来源

- **API端点**: Hyperliquid Portfolio API
- **数据类型**: "portfolio" → "day"
- **更新频率**: 实时（带5分钟缓存）

### 计算逻辑

1. 获取Portfolio API的"day"数据
2. 提取pnlHistory和accountValueHistory
3. 使用pnlHistory[-1]作为24h累计PNL
4. 使用accountValueHistory[0]作为起始权益
5. 计算ROE = (PNL / 起始权益) × 100

### 边界处理

- **起始权益≤0**: 返回无效数据
- **历史<24h**: 显示警告，基于实际时长计算
- **API失败**: 自动重试3次，失败后返回错误信息
- **数据缺失**: 验证必需字段，缺失时返回错误

---

## 最佳实践

### 1. 定期监控

建议每天查看ROE，了解账户表现趋势：

```bash
# 每日查看
python main.py 0x你的地址

# 生成周报
python main.py 0x你的地址 -r
```

### 2. 结合其他指标

ROE应与其他指标结合使用：
- **Profit Factor**: 盈亏比率
- **Sharpe Ratio**: 风险调整收益
- **Win Rate**: 胜率
- **持仓时长**: 交易频率

### 3. 理解波动性

ROE是24小时快照，可能波动较大：
- 大额盈亏会显著影响ROE
- 未实现盈亏计入当前权益
- 市场波动会反映在ROE中

### 4. 长期视角

单日ROE不代表长期表现：
- 跟踪多日ROE趋势
- 关注累计指标（Profit Factor、Sharpe Ratio）
- 避免过度关注短期波动

---

## 支持与反馈

如有问题或建议，请通过以下方式反馈：
- GitHub Issues
- 邮件联系
- 社区讨论

---

**最后更新**: 2026-02-04
**版本**: 1.0.0
