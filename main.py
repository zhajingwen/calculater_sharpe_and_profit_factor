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

# ========== 颜色支持 ==========
try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    COLORS_ENABLED = True
except ImportError:
    # 如果没有 colorama，使用空字符串
    class Fore:
        GREEN = YELLOW = RED = CYAN = MAGENTA = BLUE = WHITE = LIGHTBLACK_EX = LIGHTGREEN_EX = LIGHTRED_EX = ""
    class Back:
        BLACK = ""
    class Style:
        BRIGHT = RESET_ALL = DIM = ""
    COLORS_ENABLED = False

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
    """打印精美的章节标题"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'━' * width}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}▌{Style.RESET_ALL} {Fore.YELLOW}{Style.BRIGHT}{title}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'━' * width}{Style.RESET_ALL}")

def print_metric(label: str, value: str, icon: str = "  •", indent: int = 0) -> None:
    """打印指标"""
    prefix = " " * indent
    print(f"{prefix}{icon} {label}: {value}")

def print_metric_row(label: str, value: str, unit: str = "", color: str = "") -> None:
    """打印美化的指标行

    Args:
        label: 指标名称
        value: 指标值
        unit: 单位（可选）
        color: 颜色代码（可选）
    """
    # 使用圆点符号和更好的对齐
    if color:
        print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.WHITE}{label:<26}{Style.RESET_ALL} {color}{Style.BRIGHT}{value:>14}{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}{unit}{Style.RESET_ALL}")
    else:
        print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.WHITE}{label:<26}{Style.RESET_ALL} {Fore.WHITE}{value:>14}{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}{unit}{Style.RESET_ALL}")

def print_separator(char: str = "─", width: int = 80) -> None:
    """打印优雅的分隔线

    Args:
        char: 分隔字符
        width: 宽度
    """
    print(f"  {Fore.LIGHTBLACK_EX}{'╌' * width}{Style.RESET_ALL}")

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
    """显示精美的程序头部信息"""
    width = 80
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'━' * width}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}╔{'═' * (width - 2)}╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}  {Fore.YELLOW}{Style.BRIGHT}🚀 Apex Fork - 交易分析系统{Style.RESET_ALL}{'  ' * 16}{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}  {Fore.WHITE}基于Hyperliquid官方API和Apex Liquid Bot算法{Style.RESET_ALL}{'  ' * 6}{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}  {Fore.GREEN}✅ 基于单笔交易收益率的准确指标（不依赖本金）{Style.RESET_ALL}{'  ' * 5}{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}╚{'═' * (width - 2)}╝{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'━' * width}{Style.RESET_ALL}")

def display_core_metrics(analysis: AnalysisResults) -> None:
    """显示核心指标（基于单笔交易收益率）"""
    print_section("📈 核心指标", width=80)

    # Sharpe Ratio - 基于交易收益率
    sharpe_on_trades = analysis.raw_results.get('sharpe_on_trades', {})
    if sharpe_on_trades and sharpe_on_trades.get('total_trades', 0) > 0:
        print(f"\n  {Fore.YELLOW}{Style.BRIGHT}╔═══ Sharpe Ratio (风险调整收益) {'═' * 34}╗{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")

        sharpe_val = sharpe_on_trades['annualized_sharpe']
        if sharpe_val > 1:
            rating = f"{Fore.GREEN}{Style.BRIGHT}✅ 优秀{Style.RESET_ALL}"
            value_color = Fore.GREEN + Style.BRIGHT
        elif sharpe_val > 0:
            rating = f"{Fore.YELLOW}⚠️  偏高风险{Style.RESET_ALL}"
            value_color = Fore.YELLOW + Style.BRIGHT
        else:
            rating = f"{Fore.RED}❌ 负收益{Style.RESET_ALL}"
            value_color = Fore.RED

        print_metric_row('年化 Sharpe Ratio', f"{sharpe_val:.2f}", rating, value_color)
        print_metric_row('每笔 Sharpe', f"{sharpe_on_trades['sharpe_ratio']:.4f}", "")
        print_metric_row('收益率标准差', f"{sharpe_on_trades['std_return']:.2%}", "")

        print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")
        print(f"\n  {Fore.LIGHTBLACK_EX}💡 单笔收益率 = closedPnL / (|sz| × px){Style.RESET_ALL}")

    # Max Drawdown 已移除
    # 原因：基于PNL的回撤计算不够准确，无法反映真实的资金风险

    # 交易统计
    print(f"\n  {Fore.YELLOW}{Style.BRIGHT}╔═══ 交易统计 {'═' * 50}╗{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")

    # Profit Factor 显示：>= 1000 显示为 "1000+"
    if analysis.profit_factor >= 1000:
        pf_value = "1000+"
        pf_status = f'{Fore.GREEN}{Style.BRIGHT}✅ 极优秀（无亏损）{Style.RESET_ALL}'
        pf_color = Fore.GREEN + Style.BRIGHT
    else:
        if analysis.profit_factor > 1:
            pf_value = f"{analysis.profit_factor:.4f}"
            pf_status = f'{Fore.GREEN}✅ 盈利{Style.RESET_ALL}'
            pf_color = Fore.GREEN + Style.BRIGHT
        else:
            pf_value = f"{analysis.profit_factor:.4f}"
            pf_status = f'{Fore.RED}❌ 亏损{Style.RESET_ALL}'
            pf_color = Fore.RED

    print_metric_row('Profit Factor', pf_value, pf_status, pf_color)

    # Win Rate 颜色
    win_rate = analysis.win_rate_data.get('winRate', 0)
    if win_rate >= 60:
        wr_color = Fore.GREEN + Style.BRIGHT
    elif win_rate >= 45:
        wr_color = Fore.YELLOW + Style.BRIGHT
    else:
        wr_color = Fore.RED + Style.BRIGHT

    print_metric_row('Win Rate', f"{win_rate:.2f}%", "", wr_color)
    print_metric_row('Total Trades', f"{analysis.win_rate_data.get('totalTrades', 0)}", "", Fore.CYAN + Style.BRIGHT)

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

    print_metric_row('Avg Hold Time', avg_hold_str, "")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")

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

    print(f"\n  {Fore.YELLOW}{Style.BRIGHT}╔═══ 账户价值 {'═' * 50}╗{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")
    print_metric_row('总账户价值', f"${total_account_value:,.2f}", "", Fore.GREEN + Style.BRIGHT)
    print(f"  {Fore.CYAN}  ├─{Style.RESET_ALL} {Fore.WHITE}Perp 账户{Style.RESET_ALL}          {Fore.CYAN}${perp_account_value:>12,.2f}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}  └─{Style.RESET_ALL} {Fore.WHITE}Spot 账户{Style.RESET_ALL}          {Fore.CYAN}${spot_account_value:>12,.2f}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")
    print_metric_row('保证金使用', f"${data_summary.get('total_margin_used', 0):,.2f}", "", Fore.YELLOW)
    print_metric_row('当前持仓', f"{position_analysis.get('total_positions', 0)}", "个", Fore.CYAN)
    print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")

    # PNL信息
    total_cumulative_pnl = raw_results.get('total_cumulative_pnl', 0)
    total_realized_pnl = raw_results.get('total_realized_pnl', 0)
    total_unrealized_pnl = position_analysis.get('total_unrealized_pnl', 0)

    pnl_icon = "📈" if total_cumulative_pnl >= 0 else "📉"
    pnl_color = Fore.GREEN if total_cumulative_pnl >= 0 else Fore.RED
    real_color = Fore.GREEN if total_realized_pnl >= 0 else Fore.RED
    unreal_color = Fore.GREEN if total_unrealized_pnl >= 0 else Fore.RED

    print(f"\n  {Fore.YELLOW}{Style.BRIGHT}╔═══ 盈亏统计 {pnl_icon} {'═' * 48}╗{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")
    print_metric_row('累计总盈亏', f"${total_cumulative_pnl:,.2f}", "", pnl_color + Style.BRIGHT)
    print(f"  {Fore.CYAN}  ├─{Style.RESET_ALL} {Fore.WHITE}已实现盈亏{Style.RESET_ALL}        {real_color}${total_realized_pnl:>12,.2f}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}  └─{Style.RESET_ALL} {Fore.WHITE}未实现盈亏{Style.RESET_ALL}        {unreal_color}${total_unrealized_pnl:>12,.2f}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")

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

        print(f"\n  {Fore.YELLOW}{Style.BRIGHT}╔═══ 多周期 ROE {roe_icon} {'═' * 46}╗{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")

        # 显示各个周期的ROE
        for roe_data, label in [
            (roe_24h, '24小时'),
            (roe_7d, '7天'),
            (roe_30d, '30天'),
            (roe_all, '历史总计')
        ]:
            if roe_data.get('is_valid', False):
                roe_percent = roe_data.get('roe_percent', 0)

                # 根据ROE值设置颜色
                if roe_percent >= 5:
                    roe_color = Fore.GREEN + Style.BRIGHT
                elif roe_percent >= 0:
                    roe_color = Fore.GREEN
                elif roe_percent >= -5:
                    roe_color = Fore.YELLOW
                else:
                    roe_color = Fore.RED

                roe_sign = '+' if roe_percent >= 0 else ''
                print_metric_row(label, f'{roe_sign}{roe_percent:.2f}%', "", roe_color)
            else:
                error_msg = roe_data.get('error_message', '计算失败')
                print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.WHITE}{label:<26}{Style.RESET_ALL} {Fore.RED}❌ {error_msg[:20]}{Style.RESET_ALL}")

        print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")

        # 显示警告信息（如果有）
        warnings = []
        for roe_data, label in [(roe_24h, '24小时'), (roe_7d, '7天'), (roe_30d, '30天')]:
            if roe_data.get('is_valid', False) and not roe_data.get('is_sufficient_history', True):
                period_hours = roe_data.get('period_hours', 0)
                warnings.append(f"{label}: 实际历史仅 {period_hours:.1f}h")

        if warnings:
            print(f"\n  {Fore.YELLOW}⚠️  注意:{Style.RESET_ALL} " + ", ".join(warnings))
            print(f"  {Fore.LIGHTBLACK_EX}ROE基于实际时长计算{Style.RESET_ALL}")

        # 显示更新时间
        try:
            from datetime import datetime
            end_time = roe_24h.get('end_time', 'N/A')
            end_dt = datetime.fromisoformat(end_time)
            end_time_str = end_dt.strftime('%Y-%m-%d %H:%M')
            print(f"\n  {Fore.LIGHTBLACK_EX}🕐 更新时间: {end_time_str}{Style.RESET_ALL}")
        except:
            pass

    else:
        # 显示错误信息
        print(f"\n  {Fore.YELLOW}{Style.BRIGHT}╔═══ 多周期 ROE {'═' * 48}╗{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")
        print(f"  {Fore.RED}❌ ROE数据不可用{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")

    # 收益率指标（基于交易收益率）
    return_metrics_on_trades = raw_results.get('return_metrics_on_trades', {})
    sharpe_on_trades = raw_results.get('sharpe_on_trades', {})

    print(f"\n  {Fore.YELLOW}{Style.BRIGHT}╔═══ 收益率指标 {'═' * 48}╗{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")

    # 平均每笔收益率
    mean_return = sharpe_on_trades.get('mean_return', 0)
    mean_return_icon = "📈" if mean_return >= 0 else "📉"
    mean_return_color = Fore.GREEN if mean_return >= 0 else Fore.RED
    print_metric_row('平均每笔收益率 ' + mean_return_icon, f"{mean_return:.2%}", "", mean_return_color + Style.BRIGHT)
    print_metric_row('交易天数', f"{return_metrics_on_trades.get('trading_days', 0):.1f}", "天", Fore.CYAN)
    print_metric_row('交易笔数', f"{analysis.win_rate_data.get('totalTrades', 0)}", "笔", Fore.CYAN)

    print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")
    print(f"\n  {Fore.LIGHTBLACK_EX}💡 基于单笔交易持仓价值计算，不依赖外部本金{Style.RESET_ALL}")

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

    print(f"\n  {Fore.YELLOW}{Style.BRIGHT}╔═══ 平均持仓时长 {'═' * 46}╗{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")

    print_metric_row('今日', format_hold_time(stats.get('todayCount', 0)), "")
    print_metric_row('近 7 天', format_hold_time(stats.get('last7DaysAverage', 0)), "")
    print_metric_row('近 30 天', format_hold_time(stats.get('last30DaysAverage', 0)), "")
    print_metric_row('历史平均', format_hold_time(stats.get('allTimeAverage', 0)), "")

    print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")

def display_data_summary(analysis: AnalysisResults) -> None:
    """显示数据摘要"""
    print_section("📊 数据摘要")

    data_summary = analysis.data_summary
    print_metric("成交记录", f"{data_summary.get('total_fills', 0)} 条")
    print_metric("当前持仓", f"{data_summary.get('total_positions', 0)} 个")
    print_metric("分析时间", analysis.raw_results.get('analysis_timestamp', 'N/A'))

def display_strategy_evaluation(analysis: AnalysisResults) -> None:
    """显示策略评估"""
    print_section("🎯 策略评估总结", width=80)

    # 获取 Sharpe Ratio 数据
    sharpe_on_trades = analysis.raw_results.get('sharpe_on_trades', {})

    # 优势
    print(f"\n  {Fore.GREEN}{Style.BRIGHT}╔═══ ✅ 优势 {'═' * 51}╗{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}{Style.BRIGHT}║{Style.RESET_ALL}")
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
            print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.GREEN}{adv}{Style.RESET_ALL}")
    else:
        print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}暂无明显优势{Style.RESET_ALL}")

    print(f"  {Fore.GREEN}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")

    # 风险
    print(f"\n  {Fore.YELLOW}{Style.BRIGHT}╔═══ ⚠️  风险 {'═' * 51}╗{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")
    risks = []

    if analysis.win_rate_data.get('winRate', 0) < 50:
        wr = analysis.win_rate_data.get('winRate', 0)
        risks.append(f"胜率偏低（{wr:.2f}%）")

    sharpe_ratio = analysis.raw_results.get('sharpe_on_trades', {}).get('annualized_sharpe', 0)
    if sharpe_ratio < 1:
        risks.append(f"风险调整收益偏低（Sharpe = {sharpe_ratio:.2f} < 1.0）")

    if risks:
        for risk in risks:
            print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.YELLOW}{risk}{Style.RESET_ALL}")
    else:
        print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.GREEN}风险可控{Style.RESET_ALL}")

    print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")

    # 改进建议
    print(f"\n  {Fore.CYAN}{Style.BRIGHT}╔═══ 💡 改进建议 {'═' * 48}╗{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}")
    suggestions = []

    if analysis.win_rate_data.get('winRate', 0) < 45:
        suggestions.append("优化入场时机，提高胜率")
    if sharpe_ratio < 1:
        suggestions.append("优化风险管理，降低收益波动")
    suggestions.append("持续优化资金管理策略")

    for sug in suggestions:
        print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.WHITE}{sug}{Style.RESET_ALL}")

    print(f"  {Fore.CYAN}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")

def display_usage_guide() -> None:
    """显示使用说明"""
    print_section("📚 使用说明", width=80)

    print(f"\n  {Fore.YELLOW}{Style.BRIGHT}╔═══ 使用步骤 {'═' * 50}╗{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}  1.{Style.RESET_ALL} {Fore.WHITE}将 user_address 替换为真实的 Hyperliquid 用户地址{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}  2.{Style.RESET_ALL} {Fore.WHITE}确保网络连接正常{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}  3.{Style.RESET_ALL} {Fore.WHITE}所有指标基于单笔交易收益率计算（不依赖本金数据）{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}  4.{Style.RESET_ALL} {Fore.WHITE}使用 {Fore.GREEN}--report{Fore.WHITE} 参数生成 Markdown 报告{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}  5.{Style.RESET_ALL} {Fore.WHITE}使用 {Fore.GREEN}--verbose{Fore.WHITE} 显示详细日志{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}  6.{Style.RESET_ALL} {Fore.WHITE}使用 {Fore.GREEN}--debug{Fore.WHITE} 显示调试信息{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")

    print(f"\n  {Fore.YELLOW}{Style.BRIGHT}╔═══ 💡 核心算法 {'═' * 48}╗{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.WHITE}单笔收益率 = closedPnL / (|sz| × px){Style.RESET_ALL}")
    print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.WHITE}完全独立，不受出入金影响{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.WHITE}符合金融标准，使用复利计算{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")

    print(f"\n  {Fore.CYAN}{Style.BRIGHT}╔═══ 🔗 相关链接 {'═' * 48}╗{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.BLUE}API 文档: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.BLUE}项目地址: https://github.com/your-repo/apex-fork{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'━' * 80}{Style.RESET_ALL}")

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
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'━' * 80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}╔{'═' * 78}╗{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}  {Fore.YELLOW}{Style.BRIGHT}📊 分析用户{Style.RESET_ALL}                                                          {Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}  {Fore.MAGENTA}{user_address}{Style.RESET_ALL}  {Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}╚{'═' * 78}╝{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'━' * 80}{Style.RESET_ALL}")

        # 初始化计算器
        calculator = ApexCalculator()

        # 执行分析
        results = calculator.analyze_user(user_address, force_refresh=force_refresh)

        if "error" in results:
            logger.error(f"分析失败: {results['error']}")
            print(f"\n  {Fore.RED}{Style.BRIGHT}╔═══ ❌ 错误 {'═' * 52}╗{Style.RESET_ALL}")
            print(f"  {Fore.RED}{Style.BRIGHT}║{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.RED}分析失败: {results['error']}{Style.RESET_ALL}")
            print(f"  {Fore.RED}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")
            return False

        # 提取分析数据
        analysis = extract_analysis_data(calculator, results, user_address)
        if not analysis:
            logger.error("数据提取失败")
            print(f"\n  {Fore.RED}{Style.BRIGHT}╔═══ ❌ 错误 {'═' * 52}╗{Style.RESET_ALL}")
            print(f"  {Fore.RED}{Style.BRIGHT}║{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.RED}数据提取失败{Style.RESET_ALL}")
            print(f"  {Fore.RED}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")
            return False

        # 显示核心指标
        display_core_metrics(analysis)
        display_account_info(analysis)
        display_hold_time_stats(analysis)

        # 生成报告（可选）
        if generate_report:
            print_section("📄 生成 Markdown 报告", width=80)
            print(f"\n  {Fore.YELLOW}{Style.BRIGHT}╔═══ 报告生成 {'═' * 50}╗{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")
            report_filename = f"trading_report_{user_address[:8]}.md"
            save_result = generate_markdown_report(results, user_address, report_filename)
            print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.GREEN}{save_result}{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}💡 提示: 使用 Markdown 查看器打开报告文件{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}{Style.BRIGHT}{'━' * 80}{Style.RESET_ALL}")

        return True

    except KeyboardInterrupt:
        print(f"\n\n  {Fore.YELLOW}{Style.BRIGHT}╔═══ ⚠️  警告 {'═' * 52}╗{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.YELLOW}操作已取消{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")
        return False

    except Exception as e:
        logger.error(f"分析过程出现错误: {str(e)}", exc_info=True)
        print(f"\n  {Fore.RED}{Style.BRIGHT}╔═══ ❌ 错误 {'═' * 52}╗{Style.RESET_ALL}")
        print(f"  {Fore.RED}{Style.BRIGHT}║{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.RED}分析过程出现错误: {str(e)}{Style.RESET_ALL}")
        print(f"  {Fore.RED}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}")
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
    width = 80
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'━' * width}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}╔{'═' * (width - 2)}╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}  {Fore.YELLOW}{Style.BRIGHT}🚀 Apex Fork - 交易分析系统{Style.RESET_ALL}{'  ' * 16}{Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}╚{'═' * (width - 2)}╝{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'━' * width}{Style.RESET_ALL}\n")

    print(f"  {Fore.CYAN}{Style.BRIGHT}╔═══ 用法 {'═' * 54}╗{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.WHITE}python main.py [用户地址] [选项]{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}\n")

    print(f"  {Fore.YELLOW}{Style.BRIGHT}╔═══ 参数 {'═' * 54}╗{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.GREEN}用户地址{Style.RESET_ALL}          {Fore.WHITE}Hyperliquid 用户地址（0x开头，42字符）{Style.RESET_ALL}")
    print(f"                      {Fore.LIGHTBLACK_EX}如果未提供，将使用默认示例地址{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}\n")

    print(f"  {Fore.YELLOW}{Style.BRIGHT}╔═══ 选项 {'═' * 54}╗{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.GREEN}-h, --help{Style.RESET_ALL}       {Fore.WHITE}显示此帮助信息{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.GREEN}-v, --verbose{Style.RESET_ALL}    {Fore.WHITE}显示详细日志{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.GREEN}-d, --debug{Style.RESET_ALL}      {Fore.WHITE}显示调试信息{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.GREEN}-r, --report{Style.RESET_ALL}     {Fore.WHITE}生成 Markdown 报告{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.GREEN}-f, --force{Style.RESET_ALL}      {Fore.WHITE}强制刷新数据（跳过缓存）{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}\n")

    print(f"  {Fore.CYAN}{Style.BRIGHT}╔═══ 示例 {'═' * 54}╗{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"  {Fore.LIGHTBLACK_EX}# 使用默认地址分析{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}python main.py{Style.RESET_ALL}\n")
    print(f"  {Fore.LIGHTBLACK_EX}# 分析指定地址{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}python main.py 0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf{Style.RESET_ALL}\n")
    print(f"  {Fore.LIGHTBLACK_EX}# 详细模式 + 生成报告{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}python main.py 0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf -v -r{Style.RESET_ALL}\n")
    print(f"  {Fore.LIGHTBLACK_EX}# 调试模式 + 强制刷新{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}python main.py -d -f{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}\n")

    print(f"  {Fore.GREEN}{Style.BRIGHT}╔═══ 功能说明 {'═' * 50}╗{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.GREEN}✅ 交易级别指标（推荐）{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}- 完全不受出入金影响{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}◆{Style.RESET_ALL} {Fore.YELLOW}⚠️  账户级别指标{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}- 受出入金影响，仅供对比参考{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}{Style.BRIGHT}╚{'═' * 74}╝{Style.RESET_ALL}\n")

    print(f"  {Fore.BLUE}📖 文档: https://hyperliquid.gitbook.io/hyperliquid-docs{Style.RESET_ALL}")
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'━' * width}{Style.RESET_ALL}\n")

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
