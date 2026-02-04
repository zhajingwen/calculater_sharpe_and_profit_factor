# 累计收益率计算问题修复方案

## 问题描述

当前累计收益率计算使用复利公式：
```python
cumulative = 1.0
for ret in trade_returns:
    cumulative *= (1 + ret)
cumulative_return = (cumulative - 1) * 100
```

**问题**：当单笔收益率 ≤ -100% 时，`(1 + ret) ≤ 0`，导致 cumulative 变成负数或零，最终导致累计收益率出现巨大的负值。

**实际案例**：
- 用户地址：0x8d8b1f0a704544f4c8adaf55a1063be1bb656cc9
- 总盈亏：$20,744（正的）
- 累计收益率：-5008.87%（错误）
- 问题交易：GRIFFAIN，收益率 -128.47%

## 方案对比

### 方案1：限制单笔收益率下限（推荐）⭐

**原理**：将单笔收益率限制在 -99.9% 以上

**优点**：
- ✅ 简单易懂，修改量最小
- ✅ 保持复利计算逻辑不变
- ✅ 符合金融常识（最多亏损本金）
- ✅ 不影响其他指标计算

**缺点**：
- ⚠️ 对极端亏损交易进行了"截断"处理

**实现**：
```python
# 方案1：限制单笔收益率下限
trade_return = closed_pnl / notional_value
trade_return = max(trade_return, -0.999)  # 限制最小为 -99.9%
```

### 方案2：使用对数收益率

**原理**：使用 `log(1 + return)` 累加，然后 `exp(sum) - 1`

**优点**：
- ✅ 理论上更加优雅
- ✅ 避免负数问题

**缺点**：
- ❌ 当 `1 + return ≤ 0` 时，log 无定义
- ❌ 仍需要限制收益率下限
- ❌ 计算复杂度增加

### 方案3：基于本金的累计收益率

**原理**：累计收益率 = 总盈亏 / 初始本金

**优点**：
- ✅ 与总盈亏直接对应
- ✅ 不受单笔收益率影响

**缺点**：
- ❌ 需要准确的本金数据（目前缺失）
- ❌ 受出入金影响
- ❌ 不符合"基于交易收益率"的设计原则

### 方案4：修正持仓价值计算

**原理**：使用实际保证金而非名义价值

**优点**：
- ✅ 理论上最准确

**缺点**：
- ❌ 需要额外的保证金数据（API 可能不提供）
- ❌ 实现复杂度高

## 推荐方案：方案1

### 修改位置

**文件**：`apex_fork.py`

**函数**：`_calculate_return_metrics_on_trades(self, fills)`

**修改代码**：

```python
# 第 967 行附近
if notional_value > 0:
    trade_return = closed_pnl / notional_value
    # 🔧 修复：限制单笔收益率下限为 -99.9%
    trade_return = max(trade_return, -0.999)
    trade_returns.append(trade_return)
    trade_times.append(fill.get('time', 0))
```

### 预期效果

**修复前**：
- 累计收益率：-5008.87%
- cumulative：-49.09

**修复后** (估算)：
- 极端交易从 -128.47% 截断为 -99.9%
- cumulative 保持正数
- 累计收益率将会是一个合理的正值（预计 +50% 到 +300%）

### 其他需要修改的地方

1. **最大回撤计算** (`_calculate_max_drawdown_on_trades`)
   - 第 896 行附近，同样需要限制收益率下限

2. **Sharpe Ratio 计算** (`_calculate_sharpe_on_trades`)
   - 第 819 行附近，同样需要限制收益率下限

### 完整修改代码

```python
# apex_fork.py

# 1. _calculate_sharpe_on_trades (第 819 行附近)
def _calculate_sharpe_on_trades(self, fills: List[Dict]) -> Dict[str, Any]:
    trade_returns = []
    for fill in fills:
        closed_pnl = float(fill.get('closedPnl', 0))
        if closed_pnl == 0:
            continue

        sz = float(fill.get('sz', 0))
        px = float(fill.get('px', 0))
        notional_value = abs(sz) * px

        if notional_value > 0:
            trade_return = closed_pnl / notional_value
            trade_return = max(trade_return, -0.999)  # 🔧 修复
            trade_returns.append(trade_return)
    # ... 其余代码不变

# 2. _calculate_max_drawdown_on_trades (第 896 行附近)
def _calculate_max_drawdown_on_trades(self, fills: List[Dict]) -> Dict[str, Any]:
    trade_returns = []
    trade_times = []

    for fill in fills:
        closed_pnl = float(fill.get('closedPnl', 0))
        if closed_pnl == 0:
            continue

        sz = float(fill.get('sz', 0))
        px = float(fill.get('px', 0))
        notional_value = abs(sz) * px

        if notional_value > 0:
            trade_return = closed_pnl / notional_value
            trade_return = max(trade_return, -0.999)  # 🔧 修复
            trade_returns.append(trade_return)
            trade_times.append(fill.get('time', 0))
    # ... 其余代码不变

# 3. _calculate_return_metrics_on_trades (第 967 行附近)
def _calculate_return_metrics_on_trades(self, fills: List[Dict]) -> Dict[str, Any]:
    trade_returns = []
    trade_times = []

    for fill in fills:
        closed_pnl = float(fill.get('closedPnl', 0))
        if closed_pnl == 0:
            continue

        sz = float(fill.get('sz', 0))
        px = float(fill.get('px', 0))
        notional_value = abs(sz) * px

        if notional_value > 0:
            trade_return = closed_pnl / notional_value
            trade_return = max(trade_return, -0.999)  # 🔧 修复
            trade_returns.append(trade_return)
            trade_times.append(fill.get('time', 0))
    # ... 其余代码不变
```

## 验证方法

修改后运行：
```bash
python main.py --verbose
```

检查：
1. ✅ 累计收益率是否为正值
2. ✅ 累计收益率是否与总盈亏方向一致
3. ✅ cumulative 是否保持正数
4. ✅ 其他指标（Sharpe、Max Drawdown）是否合理

## 注意事项

1. **截断处理的合理性**：
   - 在杠杆交易中，确实可能出现亏损超过保证金的情况
   - 但从收益率角度，最多亏损 100%（全部本金）是合理的假设
   - 超额亏损应该被视为"爆仓"或"追加保证金"

2. **是否需要记录被截断的交易**：
   - 可以在日志中记录哪些交易被截断了
   - 供用户了解数据处理情况

3. **文档更新**：
   - 需要在算法文档中说明这个限制
   - 解释为什么这样处理

## 总结

**推荐使用方案1**：限制单笔收益率下限为 -99.9%

- ✅ 简单有效
- ✅ 符合金融常识
- ✅ 修改量小
- ✅ 不影响其他逻辑
