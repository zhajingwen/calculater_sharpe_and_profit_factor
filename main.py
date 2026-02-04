#!/usr/bin/env python3
"""
Apex Fork - 最终演示（优化版）
基于Hyperliquid官方API和Apex Liquid Bot算法

✅ 完全不受出入金影响的交易级别指标
⚠️ 账户级别指标对比展示
"""

from apex_fork import ApexCalculator
from report_generator import generate_markdown_report
import sys
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# ========== 日志配置 ==========
def setup_logging(verbose: bool = False, debug: bool = False) -> None:
    """配置日志系统"""
    if debug:
        level = logging.DEBUG
        format_str = '%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s'
    elif verbose:
        level = logging.INFO
        format_str = '%(asctime)s | %(levelname)-8s | %(message)s'
    else:
        level = logging.WARNING
        format_str = '%(message)s'

    logging.basicConfig(
        level=level,
        format=format_str,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

logger = logging.getLogger(__name__)

# ========== 数据类 ==========
@dataclass
class AnalysisResults:
    """分析结果数据类"""
    win_rate_data: Dict[str, Any]
    hold_time_stats: Dict[str, float]
    data_summary: Dict[str, Any]
    position_analysis: Dict[str, Any]
    profit_factor: float
    raw_results: Dict[str, Any]

# ========== 输出格式化 ==========
def print_section(title: str, char: str = "=", width: int = 80) -> None:
    """打印分隔线"""
    line = char * width
    print(f"\n{line}")
    print(f"{title}")
    print(f"{line}")

def print_metric(label: str, value: str, icon: str = "  •", indent: int = 0) -> None:
    """打印指标"""
    prefix = " " * indent
    print(f"{prefix}{icon} {label}: {value}")

def print_table_row(items: list, widths: list, align: list = None) -> None:
    """打印表格行

    Args:
        items: 要显示的项目列表
        widths: 每列的宽度列表
        align: 对齐方式列表 ('left', 'right', 'center')，默认左对齐
    """
    if align is None:
        align = ['left'] * len(items)

    row = []
    for item, width, al in zip(items, widths, align):
        if al == 'right':
            row.append(str(item).rjust(width))
        elif al == 'center':
            row.append(str(item).center(width))
        else:
            row.append(str(item).ljust(width))

    print("  " + " │ ".join(row))

def print_table_separator(widths: list, style: str = 'mid') -> None:
    """打印表格分隔线

    Args:
        widths: 每列的宽度列表
        style: 分隔线样式 ('top', 'mid', 'bottom')
    """
    chars = {
        'top': ('┌', '┬', '┐', '─'),
        'mid': ('├', '┼', '┤', '─'),
        'bottom': ('└', '┴', '┘', '─')
    }
    left, mid, right, line = chars.get(style, chars['mid'])

    parts = [line * w for w in widths]
    print("  " + left + mid.join(parts) + right)

# ========== 数据提取 ==========
def extract_analysis_data(calculator: ApexCalculator, results: Dict[str, Any],
                          user_address: str) -> Optional[AnalysisResults]:
    """从结果中提取分析数据"""
    try:
        # 获取嵌套数据
        win_rate_data = results.get('win_rate', {})
        hold_time_stats = results.get('hold_time_stats', {})
        data_summary = results.get('data_summary', {})
        position_analysis = results.get('position_analysis', {})

        # 获取交易级别数据
        fills = results.get('_raw_fills', [])
        if not fills:
            logger.warning("未找到原始成交数据，重新获取...")
            user_data = calculator.get_user_data(user_address, force_refresh=False)
            fills = user_data.get('fills', [])

        return AnalysisResults(
            win_rate_data=win_rate_data,
            hold_time_stats=hold_time_stats,
            data_summary=data_summary,
            position_analysis=position_analysis,
            profit_factor=results.get('profit_factor', 0),
            raw_results=results
        )
    except Exception as e:
        logger.error(f"提取分析数据失败: {str(e)}", exc_info=True)
        return None

# ========== 输出模块 ==========
def display_header() -> None:
    """显示程序头部信息"""
    width = 80
    print("\n" + "=" * width)
    print("🚀 Apex Fork - 交易分析系统".center(width - 2))
    print("基于Hyperliquid官方API和Apex Liquid Bot算法".center(width + 14))  # 调整中文字符
    print("✅ 基于单笔交易收益率的准确指标（不依赖本金）".center(width + 14))
    print("=" * width)

def display_core_metrics(analysis: AnalysisResults) -> None:
    """显示核心指标（基于单笔交易收益率）"""
    print_section("📈 核心指标（基于单笔交易收益率）", width=80)

    # Sharpe Ratio - 基于交易收益率
    sharpe_on_trades = analysis.raw_results.get('sharpe_on_trades', {})
    if sharpe_on_trades and sharpe_on_trades.get('total_trades', 0) > 0:
        print("\n  ┌─ Sharpe Ratio（基于单笔交易收益率）")
        print("  │")

        widths = [28, 18, 28]
        print_table_separator(widths, 'top')
        print_table_row(['指标', '数值', '说明'], widths)
        print_table_separator(widths, 'mid')

        sharpe_val = sharpe_on_trades['annualized_sharpe']
        if sharpe_val > 1:
            rating = "✅ 优秀"
        elif sharpe_val > 0:
            rating = "⚠️  偏高风险"
        else:
            rating = "❌ 负收益"

        print_table_row(
            ['年化 Sharpe Ratio', f"{sharpe_val:.2f}", rating],
            widths, ['left', 'right', 'left']
        )
        print_table_row(
            ['每笔 Sharpe', f"{sharpe_on_trades['sharpe_ratio']:.4f}", '单笔风险调整收益'],
            widths, ['left', 'right', 'left']
        )
        print_table_row(
            ['收益率标准差', f"{sharpe_on_trades['std_return']:.2%}", '波动性指标'],
            widths, ['left', 'right', 'left']
        )
        print_table_separator(widths, 'bottom')

        # 添加说明
        print("\n  ℹ️  计算方法: 单笔收益率 = closedPnL / (|sz| × px)")
        print("  ℹ️  持仓价值 = |sz| × px（该笔交易的名义价值）")

    # Max Drawdown 已移除
    # 原因：基于PNL的回撤计算不够准确，无法反映真实的资金风险

    # 交易统计
    print("\n  ┌─ 交易统计")
    print("  │")

    widths = [28, 18, 28]
    print_table_separator(widths, 'top')
    print_table_row(['指标', '数值', '说明'], widths)
    print_table_separator(widths, 'mid')

    # Profit Factor 显示：>= 1000 显示为 "1000+"
    if analysis.profit_factor >= 1000:
        pf_display = "1000+"
        pf_status = '✅ 极优秀（无亏损）'
    else:
        pf_display = f"{analysis.profit_factor:.4f}"
        pf_status = '✅ 盈利' if analysis.profit_factor > 1 else '❌ 亏损'

    print_table_row(
        ['Profit Factor', pf_display, pf_status],
        widths, ['left', 'right', 'left']
    )
    print_table_row(
        ['Win Rate', f"{analysis.win_rate_data.get('winRate', 0):.2f}%", '胜率'],
        widths, ['left', 'right', 'left']
    )
    print_table_row(
        ['Direction Bias', f"{analysis.win_rate_data.get('bias', 0):.2f}%", '方向偏好（做多/做空）'],
        widths, ['left', 'right', 'left']
    )
    print_table_row(
        ['Total Trades', f"{analysis.win_rate_data.get('totalTrades', 0)}", '总交易次数'],
        widths, ['left', 'right', 'left']
    )

    # 格式化持仓时间
    avg_hold_days = analysis.hold_time_stats.get('allTimeAverage', 0)
    if avg_hold_days == 0:
        avg_hold_str = "0 天"
    elif avg_hold_days >= 1:
        avg_hold_str = f"{avg_hold_days:.2f} 天"
    elif avg_hold_days >= 1/24:  # >= 1 小时
        avg_hold_str = f"{avg_hold_days * 24:.2f} 小时"
    else:  # < 1 小时
        avg_hold_str = f"{avg_hold_days * 24 * 60:.2f} 分钟"

    print_table_row(
        ['Avg Hold Time', avg_hold_str, '平均持仓时长'],
        widths, ['left', 'right', 'left']
    )
    print_table_separator(widths, 'bottom')

def display_account_info(analysis: AnalysisResults) -> None:
    """显示账户信息"""
    print_section("💰 账户信息", width=80)

    data_summary = analysis.data_summary
    position_analysis = analysis.position_analysis
    raw_results = analysis.raw_results

    # 账户价值详情
    total_account_value = data_summary.get('account_value', 0)
    perp_account_value = data_summary.get('perp_account_value', 0)
    spot_account_value = data_summary.get('spot_account_value', 0)

    print("\n  ┌─ 账户价值")
    print("  │")
    print(f"  │  总账户价值          ${total_account_value:>12,.2f}")
    print(f"  │  ├─ Perp 账户        ${perp_account_value:>12,.2f}")
    print(f"  │  └─ Spot 账户        ${spot_account_value:>12,.2f}")
    print("  │")
    print(f"  │  保证金使用          ${data_summary.get('total_margin_used', 0):>12,.2f}")
    print(f"  │  当前持仓            {position_analysis.get('total_positions', 0):>12} 个")

    # PNL信息
    total_cumulative_pnl = raw_results.get('total_cumulative_pnl', 0)
    total_realized_pnl = raw_results.get('total_realized_pnl', 0)
    total_unrealized_pnl = position_analysis.get('total_unrealized_pnl', 0)

    pnl_icon = "📈" if total_cumulative_pnl >= 0 else "📉"
    print(f"\n  ┌─ 盈亏统计 {pnl_icon}")
    print("  │")
    print(f"  │  累计总盈亏          ${total_cumulative_pnl:>12,.2f}")
    print(f"  │  ├─ 已实现盈亏      ${total_realized_pnl:>12,.2f}")
    print(f"  │  └─ 未实现盈亏      ${total_unrealized_pnl:>12,.2f}")

    # 多周期ROE指标
    # 获取所有周期的ROE数据
    roe_24h = raw_results.get('roe_24h', {})
    roe_7d = raw_results.get('roe_7d', {})
    roe_30d = raw_results.get('roe_30d', {})
    roe_all = raw_results.get('roe_all', {})

    # 检查是否有任何有效的ROE数据
    has_valid_roe = any([
        roe_24h.get('is_valid', False),
        roe_7d.get('is_valid', False),
        roe_30d.get('is_valid', False),
        roe_all.get('is_valid', False)
    ])

    if has_valid_roe:
        # 使用24h的ROE确定总体图标
        roe_24h_percent = roe_24h.get('roe_percent', 0)
        roe_icon = "📈" if roe_24h_percent >= 0 else "📉"

        print(f"\n  ┌─ 多周期ROE {roe_icon}")
        print("  │")

        widths = [20, 14]
        print_table_separator(widths, 'top')
        print_table_row(['时间周期', 'ROE'], widths)
        print_table_separator(widths, 'mid')

        # 显示各个周期的ROE
        for roe_data, label in [
            (roe_24h, '24小时'),
            (roe_7d, '7天'),
            (roe_30d, '30天'),
            (roe_all, '历史总计')
        ]:
            if roe_data.get('is_valid', False):
                roe_percent = roe_data.get('roe_percent', 0)

                roe_sign = '+' if roe_percent >= 0 else ''
                print_table_row(
                    [label, f'{roe_sign}{roe_percent:.2f}%'],
                    widths, ['left', 'right']
                )
            else:
                error_msg = roe_data.get('error_message', '计算失败')
                print_table_row(
                    [label, f'❌ {error_msg[:20]}'],
                    widths, ['left', 'left']
                )

        print_table_separator(widths, 'bottom')

        # 显示警告信息（如果有）
        warnings = []
        for roe_data, label in [(roe_24h, '24小时'), (roe_7d, '7天'), (roe_30d, '30天')]:
            if roe_data.get('is_valid', False) and not roe_data.get('is_sufficient_history', True):
                period_hours = roe_data.get('period_hours', 0)
                warnings.append(f"{label}: 实际历史仅 {period_hours:.1f}h")

        if warnings:
            print(f"\n  ⚠️  注意: " + ", ".join(warnings))
            print("  ROE基于实际时长计算")

        # 显示更新时间
        try:
            from datetime import datetime
            end_time = roe_24h.get('end_time', 'N/A')
            end_dt = datetime.fromisoformat(end_time)
            end_time_str = end_dt.strftime('%Y-%m-%d %H:%M')
            print(f"\n  更新时间: {end_time_str}")
        except:
            pass

    else:
        # 显示错误信息
        print(f"\n  ┌─ 多周期ROE")
        print("  │")
        print(f"  ❌ ROE数据不可用")

    # 收益率指标（基于交易收益率）
    return_metrics_on_trades = raw_results.get('return_metrics_on_trades', {})
    sharpe_on_trades = raw_results.get('sharpe_on_trades', {})

    print(f"\n  ┌─ 收益率指标（基于单笔交易）")
    print("  │")

    # 平均每笔收益率
    mean_return = sharpe_on_trades.get('mean_return', 0)
    mean_return_icon = "📈" if mean_return >= 0 else "📉"
    print(f"  │  平均每笔收益率 {mean_return_icon}   {mean_return:>12.2%}")

    print("  │")
    print(f"  │  交易天数            {return_metrics_on_trades.get('trading_days', 0):>12.1f}  天")
    print(f"  │  交易笔数            {analysis.win_rate_data.get('totalTrades', 0):>12}  笔")

    print("\n  ℹ️  说明:")
    print("  • 收益率基于单笔交易的持仓价值计算，不依赖外部本金")
    print("  • 平均每笔收益率：所有交易收益率的简单平均")
    print("  • 不显示累计收益率：复利假设不适用于持仓价值差异巨大的交易")

def display_hold_time_stats(analysis: AnalysisResults) -> None:
    """显示持仓时间统计"""
    print_section("⏱️  持仓时间统计", width=80)

    stats = analysis.hold_time_stats

    def format_hold_time(days: float) -> str:
        """智能格式化持仓时间

        Args:
            days: 天数

        Returns:
            格式化的字符串（自动选择天/小时/分钟）
        """
        if days == 0:
            return "0 天"
        elif days >= 1:
            return f"{days:.2f} 天"
        elif days >= 1/24:  # >= 1 小时
            hours = days * 24
            return f"{hours:.2f} 小时"
        else:  # < 1 小时
            minutes = days * 24 * 60
            return f"{minutes:.2f} 分钟"

    print("\n  ┌─ 平均持仓时长")
    print("  │")

    widths = [28, 20, 28]
    print_table_separator(widths, 'top')
    print_table_row(['时间段', '平均持仓', '说明'], widths)
    print_table_separator(widths, 'mid')

    print_table_row(
        ['今日', format_hold_time(stats.get('todayCount', 0)), '当日交易'],
        widths, ['left', 'right', 'left']
    )
    print_table_row(
        ['近 7 天', format_hold_time(stats.get('last7DaysAverage', 0)), '最近一周'],
        widths, ['left', 'right', 'left']
    )
    print_table_row(
        ['近 30 天', format_hold_time(stats.get('last30DaysAverage', 0)), '最近一月'],
        widths, ['left', 'right', 'left']
    )
    print_table_row(
        ['历史平均', format_hold_time(stats.get('allTimeAverage', 0)), '全部交易历史'],
        widths, ['left', 'right', 'left']
    )
    print_table_separator(widths, 'bottom')

def display_data_summary(analysis: AnalysisResults) -> None:
    """显示数据摘要"""
    print_section("📊 数据摘要")

    data_summary = analysis.data_summary
    print_metric("成交记录", f"{data_summary.get('total_fills', 0)} 条")
    print_metric("当前持仓", f"{data_summary.get('total_positions', 0)} 个")
    print_metric("分析时间", analysis.raw_results.get('analysis_timestamp', 'N/A'))

def display_strategy_evaluation(analysis: AnalysisResults) -> None:
    """显示策略评估"""
    print_section("🎯 策略评估总结")

    # 获取 Sharpe Ratio 数据
    sharpe_on_trades = analysis.raw_results.get('sharpe_on_trades', {})

    # 优势
    print("\n✅ 优势:")
    advantages = []

    if sharpe_on_trades.get('annualized_sharpe', 0) > 1:
        advantages.append("优秀的风险调整收益（Sharpe > 1）")
    if sharpe_on_trades.get('mean_return', 0) > 0:
        pct = sharpe_on_trades['mean_return']
        advantages.append(f"正期望策略（每笔平均 {pct:.2%}）")

    # Profit Factor 评估
    if analysis.profit_factor >= 1000:
        advantages.append(f"极优秀盈利策略（Profit Factor = 1000+，无亏损交易）")
    elif analysis.profit_factor > 1:
        advantages.append(f"盈利策略（Profit Factor = {analysis.profit_factor:.2f}）")

    if advantages:
        for adv in advantages:
            print(f"  • {adv}")
    else:
        print("  • 暂无明显优势")

    # 风险
    print("\n⚠️  风险:")
    risks = []

    if analysis.win_rate_data.get('winRate', 0) < 50:
        wr = analysis.win_rate_data.get('winRate', 0)
        risks.append(f"胜率偏低（{wr:.2f}%）")

    sharpe_ratio = analysis.raw_results.get('sharpe_on_trades', {}).get('annualized_sharpe', 0)
    if sharpe_ratio < 1:
        risks.append(f"风险调整收益偏低（Sharpe = {sharpe_ratio:.2f} < 1.0）")

    if risks:
        for risk in risks:
            print(f"  • {risk}")
    else:
        print("  • 风险可控")

    # 改进建议
    print("\n💡 改进建议:")
    suggestions = []

    if analysis.win_rate_data.get('winRate', 0) < 45:
        suggestions.append("优化入场时机，提高胜率")
    if sharpe_ratio < 1:
        suggestions.append("优化风险管理，降低收益波动")
    suggestions.append("持续优化资金管理策略")

    for sug in suggestions:
        print(f"  • {sug}")

def display_usage_guide() -> None:
    """显示使用说明"""
    print_section("📚 使用说明", width=80)

    print("\n  使用步骤:")
    print("    1. 将 user_address 替换为真实的 Hyperliquid 用户地址")
    print("    2. 确保网络连接正常")
    print("    3. 所有指标基于单笔交易收益率计算（不依赖本金数据）")
    print("    4. 使用 --report 参数生成 Markdown 报告")
    print("    5. 使用 --verbose 显示详细日志")
    print("    6. 使用 --debug 显示调试信息")

    print("\n  💡 核心算法:")
    print("    • 单笔收益率 = closedPnL / (|sz| × px)")
    print("    • 完全独立，不受出入金影响")
    print("    • 符合金融标准，使用复利计算")

    print("\n  🔗 相关链接:")
    print("    • API 文档: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api")
    print("    • 项目地址: https://github.com/your-repo/apex-fork")
    print("\n" + "=" * 80)

# ========== 主程序 ==========
def analyze_user_trading(user_address: str, force_refresh: bool = False,
                         generate_report: bool = False) -> bool:
    """分析用户交易数据

    Args:
        user_address: 用户地址
        force_refresh: 是否强制刷新数据
        generate_report: 是否生成报告

    Returns:
        bool: 分析是否成功
    """
    try:
        print(f"\n{'=' * 80}")
        print(f"📊 分析用户: {user_address}")
        print("=" * 80)

        # 初始化计算器
        calculator = ApexCalculator()

        # 执行分析
        results = calculator.analyze_user(user_address, force_refresh=force_refresh)

        if "error" in results:
            logger.error(f"分析失败: {results['error']}")
            print(f"\n❌ 分析失败: {results['error']}")
            return False

        # 提取分析数据
        analysis = extract_analysis_data(calculator, results, user_address)
        if not analysis:
            logger.error("数据提取失败")
            print("\n❌ 数据提取失败")
            return False

        # 显示核心指标
        display_core_metrics(analysis)
        display_account_info(analysis)
        display_hold_time_stats(analysis)

        # 生成报告（可选）
        if generate_report:
            print_section("📄 生成 Markdown 报告", width=80)
            report_filename = f"trading_report_{user_address[:8]}.md"
            save_result = generate_markdown_report(results, user_address, report_filename)
            print(f"\n  {save_result}")
            print(f"  💡 提示: 使用 Markdown 查看器打开报告文件")
            print("\n" + "=" * 80)

        return True

    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消")
        return False

    except Exception as e:
        logger.error(f"分析过程出现错误: {str(e)}", exc_info=True)
        print(f"\n❌ 分析过程出现错误: {str(e)}")
        return False

def parse_arguments() -> Dict[str, Any]:
    """解析命令行参数

    Returns:
        Dict: 参数字典
    """
    args = {
        'verbose': '--verbose' in sys.argv or '-v' in sys.argv,
        'debug': '--debug' in sys.argv or '-d' in sys.argv,
        'report': '--report' in sys.argv or '-r' in sys.argv,
        'force_refresh': '--force' in sys.argv or '-f' in sys.argv,
        'help': '--help' in sys.argv or '-h' in sys.argv,
        'user_address': None
    }

    # 查找用户地址参数
    for arg in sys.argv[1:]:
        if arg.startswith('0x') and len(arg) == 42:
            args['user_address'] = arg
            break

    return args

def display_help() -> None:
    """显示帮助信息"""
    help_text = """
🚀 Apex Fork - 交易分析系统

用法:
    python final_demo.py [用户地址] [选项]

参数:
    用户地址          Hyperliquid 用户地址（0x开头，42字符）
                      如果未提供，将使用默认示例地址

选项:
    -h, --help       显示此帮助信息
    -v, --verbose    显示详细日志
    -d, --debug      显示调试信息
    -r, --report     生成 Markdown 报告
    -f, --force      强制刷新数据（跳过缓存）

示例:
    # 使用默认地址分析
    python final_demo.py

    # 分析指定地址
    python final_demo.py 0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf

    # 详细模式 + 生成报告
    python final_demo.py 0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf -v -r

    # 调试模式 + 强制刷新
    python final_demo.py -d -f

功能说明:
    ✅ 交易级别指标（推荐）- 完全不受出入金影响
    ⚠️  账户级别指标 - 受出入金影响，仅供对比参考

📖 文档: https://hyperliquid.gitbook.io/hyperliquid-docs
"""
    print(help_text)

def main() -> None:
    """主函数"""
    # 解析参数
    args = parse_arguments()

    # 显示帮助
    if args['help']:
        display_help()
        return

    # 配置日志
    setup_logging(verbose=args['verbose'], debug=args['debug'])

    # 显示头部
    display_header()

    # 确定用户地址
    user_address = args['user_address']
    if not user_address:
        user_address = "0xde786a32f80731923d6297c14ef43ca1c8fd4b44"

    # 执行分析
    success = analyze_user_trading(
        user_address=user_address,
        force_refresh=args['force_refresh'],
        generate_report=args['report']
    )

    # 退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
