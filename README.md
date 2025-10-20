## calculater_sharpe_and_profit_factor

基于 Hyperliquid API 计算交易账户的 Profit Factor 与 Sharpe Ratio，并提供两种实现示例：

- `from_claude.py`: 面向对象实现，封装拉取数据与指标计算的完整流程。
- `from_grok.py`: 函数式实现，按需调用，适合脚本或服务内快速集成。

### 功能概览
- **Profit Factor**: 盈利总额 / 亏损总额（包含未实现盈亏）。
- **Sharpe Ratio**: 简化模型下的日收益率均值 / 日收益率标准差。
- 自动从 Hyperliquid 的 `info` 接口拉取用户成交、资金、账户等信息。

### 环境要求
- Python >= 3.12
- 依赖：`requests`

### 安装
使用 `uv`（推荐）：

```bash
uv sync
```

或使用 `pip`：

```bash
pip install -r <(python - << 'PY'
import tomllib, sys
data = tomllib.loads(open('pyproject.toml','rb').read())
for d in data['project']['dependencies']:
    print(d)
PY
)
```

### 快速开始

#### 方式一：面向对象流程（`from_claude.py`）

```bash
python from_claude.py
```

或在代码中使用：

```python
from from_claude import HyperliquidAnalyzer

address = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"
analyzer = HyperliquidAnalyzer(address)
results = analyzer.analyze()

print("Profit Factor:", results['profit_factor'])
print("Sharpe Ratio:", results['sharpe_ratio'])
```

`analyze()` 会：
- 拉取用户状态、成交与账户历史（若缺少完整历史则模拟构建）。
- 计算并打印 Profit Factor 与 Sharpe Ratio。
- 打印当前持仓与交易统计。

#### 方式二：函数式调用（`from_grok.py`）

```bash
python from_grok.py
```

或在代码中使用：

```python
from from_grok import calculate_profit_factor, calculate_sharpe_ratio

address = "0x7717a7a245d9f950e586822b8c9b46863ed7bd7e"

pf = calculate_profit_factor(address)
sr = calculate_sharpe_ratio(address, period="perpAllTime")

print("Profit Factor:", pf)
print("Sharpe Ratio (All Time):", sr)
```

`period` 取值取决于 Hyperliquid 返回的组合数据键名，默认 `perpAllTime`。

#### `main.py`

示例入口，目前仅占位打印。你可以在此导入上述方法整合为命令行工具或服务入口。

### 指标定义与计算要点

- **Profit Factor**:
  - 来源：历史已实现盈亏（`closedPnl`）与当前未实现盈亏（持仓 `unrealizedPnl`）。
  - 公式：`总盈利 / 总亏损`。当亏损为 0 时：若总盈利>0，返回 `"1000+"`，否则返回 `0`。
  - `from_claude.py` 使用 `Decimal` 提升数值稳定性。

- **Sharpe Ratio（简化）**：
  - 计算平均账户价值 `avg_value`。
  - 用相邻日 PnL 之差除以 `avg_value` 得到日收益率（百分比）。
  - 计算日收益率的均值与样本标准差，`Sharpe = mean / std`。
  - 若样本不足或标准差为 0，则返回 `0`。

### Hyperliquid API 与数据结构

- 统一入口：`https://api.hyperliquid.xyz/info`，使用 `POST` + JSON payload。
- `from_claude.py` 中使用的类型：
  - `clearinghouseState`（用户状态与仓位）
  - `userFills`（成交历史）
  - `userFunding`（资金费率历史，可按需拓展）
  - `userSnapshot`（快照/历史，若缺失则由成交模拟账户价值序列）
- `from_grok.py` 中还示例了 `portfolio` 返回，并基于其中的 `accountValueHistory`、`pnlHistory` 计算 Sharpe。

注意：Hyperliquid 的返回结构可能变动，示例中对字段路径有注释“Adjust based on actual response structure”，如果接口返回与示例不同，请根据实际 JSON 结构调整字典路径。

### 常见问题

- 无交易或样本过少时 Sharpe/Profit Factor 为 0：属预期处理。
- 亏损为 0 且存在盈利时 Profit Factor 显示为 `"1000+"`：用于表达极高值的简化展示。
- 接口限速或间歇性失败：请增加重试与超时控制（当前示例未内置重试）。
- 小数精度：涉及金额累计的地方已在 `from_claude.py` 使用 `Decimal`；若你在 `from_grok.py` 中需要更高精度，可自行替换。

### 开发建议

- 若要将 `main.py` 做成命令行工具，可解析 `--address`、`--mode`（claude/grok）等参数并调用对应实现。
- 如需更真实的账户价值历史，优先使用官方提供的历史接口，而非由成交推演。
- 在生产中请添加：请求超时、重试、错误分类与日志、类型校验与单元测试。

### 许可证

未显式声明许可证，默认为保留所有权利。如需开源分发，请添加合适的 LICENSE 文件。
