# 24小时ROE - 快速参考卡片

## 🎯 核心公式

```
24h ROE (%) = (24小时累计PNL / 起始权益) × 100
```

---

## 📊 评级系统

| ROE | 评级 | 图标 |
|-----|------|------|
| ≥10% | 极佳 | 🔥 |
| ≥5% | 优秀 | ✅ |
| ≥0% | 盈利 | 📈 |
| ≥-5% | 小幅亏损 | ⚠️ |
| <-5% | 较大亏损 | 📉 |

---

## 💻 使用命令

```bash
# 查看ROE
python main.py 0x你的地址

# 生成报告
python main.py 0x你的地址 -r
```

---

## 🔧 Python API

```python
from apex_fork import ApexCalculator

calculator = ApexCalculator()
roe = calculator.calculate_24h_roe("0x地址")

if roe.is_valid:
    print(f"ROE: {roe.roe_percent:.2f}%")
```

---

## ✅ 数据有效性

| 字段 | 说明 |
|------|------|
| `is_valid` | True=数据可用，False=计算失败 |
| `is_sufficient_history` | True=历史≥24h，False=<24h |
| `error_message` | 错误/警告信息 |

---

## 🚀 关键特性

- ✅ **实时计算**: 基于最新API数据
- ✅ **智能缓存**: 5分钟TTL，减少API请求
- ✅ **边界处理**: 完善的错误处理和警告
- ✅ **美观输出**: CLI表格和Markdown报告

---

## 📝 输出位置

| 输出类型 | 位置 |
|---------|------|
| **CLI** | "盈亏统计"部分之后 |
| **Markdown** | "核心指标"部分之前 |
| **数据** | `results["roe_24h"]` |

---

## ⚠️ 常见问题

**Q: ROE为负？**
A: 24小时内账户价值下降

**Q: 历史不足24h？**
A: 新账户，基于实际时长计算

**Q: 计算失败？**
A: 检查网络或API状态

---

## 📚 更多文档

- 完整实施总结: `ROE_IMPLEMENTATION_SUMMARY.md`
- 用户指南: `ROE_USER_GUIDE.md`
- 测试脚本: `test_roe.py`

---

**版本**: 1.0.0 | **更新**: 2026-02-04
