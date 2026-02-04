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
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# ========== 显示配置 ==========
DISPLAY_WIDTH = 80  # 统一显示宽度

# 边框字符
BORDER_DOUBLE = "═"
BORDER_SINGLE = "─"
BORDER_CORNER_TL = "┌"
BORDER_CORNER_TR = "┐"
BORDER_CORNER_BL = "└"
BORDER_CORNER_BR = "┘"

# 配色方案
COLOR_SUCCESS = Fore.GREEN + Style.BRIGHT      # 成功/正向
COLOR_WARNING = Fore.YELLOW + Style.BRIGHT     # 警告/中性
COLOR_ERROR = Fore.RED + Style.BRIGHT          # 错误/负向
COLOR_INFO = Fore.CYAN                         # 信息/次要
COLOR_DIM = Fore.LIGHTBLACK_EX                 # 提示/灰色
COLOR_TITLE = Fore.YELLOW + Style.BRIGHT       # 强调/标题

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


@dataclass
class BatchAddressResult:
    """批量地址分析结果"""
    address: str
    success: bool
    sharpe_ratio: Optional[float] = None
    profit_factor: Optional[float] = None
    win_rate: Optional[float] = None
    total_trades: Optional[int] = None
    total_pnl: Optional[float] = None
    account_value: Optional[float] = None
    avg_hold_time: Optional[float] = None
    error_message: Optional[str] = None
    analysis: Optional[AnalysisResults] = None

# ========== 工具函数 ==========
def format_currency(value: float) -> str:
    """统一的货币格式化"""
    return f"${value:,.2f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """统一的百分比格式化"""
    return f"{value:.{decimals}f}%"

def format_number(value: float, decimals: int = 2) -> str:
    """统一的数字格式化"""
    if abs(value) >= 1000:
        return f"{value:,.{decimals}f}"
    return f"{value:.{decimals}f}"

def get_color_for_value(value: float, positive_color: str = COLOR_SUCCESS,
                        negative_color: str = COLOR_ERROR) -> str:
    """根据值自动选择颜色"""
    return positive_color if value >= 0 else negative_color

# ========== 输出格式化 ==========
def print_section(title: str, char: str = BORDER_SINGLE, width: int = DISPLAY_WIDTH) -> None:
    """打印精美的章节标题"""
    print(f"\n{COLOR_INFO}{Style.BRIGHT}{char * width}{Style.RESET_ALL}")
    print(f"{COLOR_INFO}{Style.BRIGHT}│{Style.RESET_ALL} {COLOR_TITLE}{title}{Style.RESET_ALL}")
    print(f"{COLOR_INFO}{Style.BRIGHT}{char * width}{Style.RESET_ALL}")

def print_box_header(title: str, width: int = DISPLAY_WIDTH) -> None:
    """打印盒子头部"""
    inner_width = width - 6
    print(f"  {COLOR_TITLE}{BORDER_CORNER_TL}{BORDER_SINGLE} {title} {BORDER_SINGLE * (inner_width - len(title) - 1)}{BORDER_CORNER_TR}{Style.RESET_ALL}")

def print_box_footer(width: int = DISPLAY_WIDTH) -> None:
    """打印盒子底部"""
    inner_width = width - 4
    print(f"  {COLOR_TITLE}{BORDER_CORNER_BL}{BORDER_SINGLE * inner_width}{BORDER_CORNER_BR}{Style.RESET_ALL}")

def print_metric_row(label: str, value: str, unit: str = "", color: str = "") -> None:
    """打印美化的指标行

    Args:
        label: 指标名称
        value: 指标值
        unit: 单位（可选）
        color: 颜色代码（可选）
    """
    label_width = 28
    value_width = 18

    if color:
        value_display = f"{color}{value:>{value_width}}{Style.RESET_ALL}"
    else:
        value_display = f"{Fore.WHITE}{value:>{value_width}}{Style.RESET_ALL}"

    unit_display = f" {COLOR_DIM}{unit}{Style.RESET_ALL}" if unit else ""

    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {Fore.WHITE}{label:<{label_width}}{Style.RESET_ALL} {value_display}{unit_display}")

def print_separator(char: str = BORDER_SINGLE, width: int = DISPLAY_WIDTH) -> None:
    """打印优雅的分隔线

    Args:
        char: 分隔字符
        width: 宽度
    """
    print(f"  {COLOR_DIM}{char * (width - 2)}{Style.RESET_ALL}")

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
    title = "🚀 Apex Fork - 交易分析系统"
    subtitle = "基于 Hyperliquid 官方 API 和 Apex Liquid Bot 算法"
    feature = "✓ 基于单笔交易收益率的准确指标（不依赖本金）"

    # 计算居中空格
    title_padding = (DISPLAY_WIDTH - len(title) - 4) // 2
    subtitle_padding = (DISPLAY_WIDTH - len(subtitle) - 4) // 2
    feature_padding = (DISPLAY_WIDTH - len(feature) - 4) // 2

    print(f"\n{COLOR_INFO}{Style.BRIGHT}{BORDER_DOUBLE * DISPLAY_WIDTH}{Style.RESET_ALL}")
    print(f"{COLOR_INFO}{Style.BRIGHT}║{Style.RESET_ALL}{' ' * title_padding}{COLOR_TITLE}{title}{Style.RESET_ALL}{' ' * title_padding}{COLOR_INFO}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"{COLOR_INFO}{Style.BRIGHT}║{Style.RESET_ALL}{' ' * subtitle_padding}{COLOR_DIM}{subtitle}{Style.RESET_ALL}{' ' * subtitle_padding}{COLOR_INFO}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"{COLOR_INFO}{Style.BRIGHT}║{Style.RESET_ALL}{' ' * feature_padding}{COLOR_SUCCESS}{feature}{Style.RESET_ALL}{' ' * feature_padding}{COLOR_INFO}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"{COLOR_INFO}{Style.BRIGHT}{BORDER_DOUBLE * DISPLAY_WIDTH}{Style.RESET_ALL}")

def display_core_metrics(analysis: AnalysisResults) -> None:
    """显示核心指标（基于单笔交易收益率）"""
    print_section("📈 核心指标")

    # Sharpe Ratio - 基于交易收益率
    sharpe_on_trades = analysis.raw_results.get('sharpe_on_trades', {})
    if sharpe_on_trades and sharpe_on_trades.get('total_trades', 0) > 0:
        print()
        print_box_header("Sharpe Ratio (风险调整收益)")

        sharpe_val = sharpe_on_trades['annualized_sharpe']
        if sharpe_val > 1:
            rating = f"{COLOR_SUCCESS}✓ 优秀{Style.RESET_ALL}"
            value_color = COLOR_SUCCESS
        elif sharpe_val > 0:
            rating = f"{COLOR_WARNING}⚠ 偏高风险{Style.RESET_ALL}"
            value_color = COLOR_WARNING
        else:
            rating = f"{COLOR_ERROR}✗ 负收益{Style.RESET_ALL}"
            value_color = COLOR_ERROR

        print_metric_row('年化 Sharpe Ratio', format_number(sharpe_val), rating, value_color)
        print_metric_row('每笔 Sharpe', format_number(sharpe_on_trades['sharpe_ratio'], 4), "")
        print_metric_row('收益率标准差', format_percentage(sharpe_on_trades['std_return'] * 100), "")

        print_box_footer()
        print(f"  {COLOR_DIM}  💡 单笔收益率 = closedPnL / (|sz| × px){Style.RESET_ALL}")

    # 交易统计
    print()
    print_box_header("交易统计")

    # Profit Factor 显示：>= 1000 显示为 "1000+"
    if analysis.profit_factor >= 1000:
        pf_value = "1000+"
        pf_status = f'{COLOR_SUCCESS}✓ 极优秀（无亏损）{Style.RESET_ALL}'
        pf_color = COLOR_SUCCESS
    else:
        if analysis.profit_factor > 1:
            pf_value = format_number(analysis.profit_factor, 4)
            pf_status = f'{COLOR_SUCCESS}✓ 盈利{Style.RESET_ALL}'
            pf_color = COLOR_SUCCESS
        else:
            pf_value = format_number(analysis.profit_factor, 4)
            pf_status = f'{COLOR_ERROR}✗ 亏损{Style.RESET_ALL}'
            pf_color = COLOR_ERROR

    print_metric_row('Profit Factor', pf_value, pf_status, pf_color)

    # Win Rate 颜色
    win_rate = analysis.win_rate_data.get('winRate', 0)
    if win_rate >= 60:
        wr_color = COLOR_SUCCESS
    elif win_rate >= 45:
        wr_color = COLOR_WARNING
    else:
        wr_color = COLOR_ERROR

    print_metric_row('Win Rate', format_percentage(win_rate), "", wr_color)

    total_trades = analysis.win_rate_data.get('totalTrades', 0)
    print_metric_row('Total Trades', format_number(total_trades, 0), "", COLOR_INFO + Style.BRIGHT)

    # 格式化持仓时间
    avg_hold_days = analysis.hold_time_stats.get('allTimeAverage', 0)
    if avg_hold_days == 0:
        avg_hold_str = "0 天"
    elif avg_hold_days >= 1:
        avg_hold_str = f"{avg_hold_days:.2f} 天"
    elif avg_hold_days >= 1/24:
        avg_hold_str = f"{avg_hold_days * 24:.2f} 小时"
    else:
        avg_hold_str = f"{avg_hold_days * 24 * 60:.2f} 分钟"

    print_metric_row('Avg Hold Time', avg_hold_str, "")
    print_box_footer()

def display_account_info(analysis: AnalysisResults) -> None:
    """显示账户信息"""
    print_section("💰 账户信息")

    data_summary = analysis.data_summary
    position_analysis = analysis.position_analysis
    raw_results = analysis.raw_results

    # 账户价值详情
    total_account_value = data_summary.get('account_value', 0)
    perp_account_value = data_summary.get('perp_account_value', 0)
    spot_account_value = data_summary.get('spot_account_value', 0)

    print()
    print_box_header("账户价值")
    print_metric_row('总账户价值', format_currency(total_account_value), "", COLOR_SUCCESS)
    print(f"  {COLOR_INFO}  ├─{Style.RESET_ALL} {COLOR_DIM}Perp 账户{Style.RESET_ALL}          {COLOR_INFO}{format_currency(perp_account_value):>18}{Style.RESET_ALL}")
    print(f"  {COLOR_INFO}  └─{Style.RESET_ALL} {COLOR_DIM}Spot 账户{Style.RESET_ALL}          {COLOR_INFO}{format_currency(spot_account_value):>18}{Style.RESET_ALL}")
    print_separator()
    print_metric_row('保证金使用', format_currency(data_summary.get('total_margin_used', 0)), "", COLOR_WARNING)
    print_metric_row('当前持仓', str(position_analysis.get('total_positions', 0)), "个", COLOR_INFO)
    print_box_footer()

    # PNL信息
    total_cumulative_pnl = raw_results.get('total_cumulative_pnl', 0)
    total_realized_pnl = raw_results.get('total_realized_pnl', 0)
    total_unrealized_pnl = position_analysis.get('total_unrealized_pnl', 0)

    pnl_icon = "📈" if total_cumulative_pnl >= 0 else "📉"
    pnl_color = get_color_for_value(total_cumulative_pnl)
    real_color = get_color_for_value(total_realized_pnl)
    unreal_color = get_color_for_value(total_unrealized_pnl)

    print()
    print_box_header(f"盈亏统计 {pnl_icon}")
    print_metric_row('累计总盈亏', format_currency(total_cumulative_pnl), "", pnl_color)
    print(f"  {COLOR_INFO}  ├─{Style.RESET_ALL} {COLOR_DIM}已实现盈亏{Style.RESET_ALL}        {real_color}{format_currency(total_realized_pnl):>18}{Style.RESET_ALL}")
    print(f"  {COLOR_INFO}  └─{Style.RESET_ALL} {COLOR_DIM}未实现盈亏{Style.RESET_ALL}        {unreal_color}{format_currency(total_unrealized_pnl):>18}{Style.RESET_ALL}")
    print_box_footer()

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

        print()
        print_box_header(f"多周期 ROE {roe_icon}")

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
                    roe_color = COLOR_SUCCESS
                elif roe_percent >= 0:
                    roe_color = Fore.GREEN
                elif roe_percent >= -5:
                    roe_color = COLOR_WARNING
                else:
                    roe_color = COLOR_ERROR

                roe_sign = '+' if roe_percent >= 0 else ''
                print_metric_row(label, f'{roe_sign}{format_percentage(roe_percent)}', "", roe_color)
            else:
                error_msg = roe_data.get('error_message', '计算失败')
                print(f"  {COLOR_INFO}•{Style.RESET_ALL} {Fore.WHITE}{label:<28}{Style.RESET_ALL} {COLOR_ERROR}✗ {error_msg[:20]}{Style.RESET_ALL}")

        print_box_footer()

        # 显示警告信息（如果有）
        warnings = []
        for roe_data, label in [(roe_24h, '24小时'), (roe_7d, '7天'), (roe_30d, '30天')]:
            if roe_data.get('is_valid', False) and not roe_data.get('is_sufficient_history', True):
                period_hours = roe_data.get('period_hours', 0)
                warnings.append(f"{label}: 实际历史仅 {period_hours:.1f}h")

        if warnings:
            print(f"  {COLOR_WARNING}  ⚠ 注意:{Style.RESET_ALL} " + ", ".join(warnings))
            print(f"  {COLOR_DIM}  ROE 基于实际时长计算{Style.RESET_ALL}")

        # 显示更新时间
        try:
            from datetime import datetime
            end_time = roe_24h.get('end_time', 'N/A')
            end_dt = datetime.fromisoformat(end_time)
            end_time_str = end_dt.strftime('%Y-%m-%d %H:%M')
            print(f"  {COLOR_DIM}  🕐 更新时间: {end_time_str}{Style.RESET_ALL}")
        except:
            pass

    else:
        # 显示错误信息
        print()
        print_box_header("多周期 ROE")
        print(f"  {COLOR_ERROR}  ✗ ROE数据不可用{Style.RESET_ALL}")
        print_box_footer()

    # 收益率指标（基于交易收益率）
    return_metrics_on_trades = raw_results.get('return_metrics_on_trades', {})
    sharpe_on_trades = raw_results.get('sharpe_on_trades', {})

    print()
    print_box_header("收益率指标")

    # 平均每笔收益率
    mean_return = sharpe_on_trades.get('mean_return', 0)
    mean_return_icon = "📈" if mean_return >= 0 else "📉"
    mean_return_color = get_color_for_value(mean_return)
    print_metric_row('平均每笔收益率 ' + mean_return_icon, format_percentage(mean_return * 100), "", mean_return_color)
    print_metric_row('交易天数', format_number(return_metrics_on_trades.get('trading_days', 0), 1), "天", COLOR_INFO)
    print_metric_row('交易笔数', str(analysis.win_rate_data.get('totalTrades', 0)), "笔", COLOR_INFO)

    print_box_footer()
    print(f"  {COLOR_DIM}  💡 基于单笔交易持仓价值计算，不依赖外部本金{Style.RESET_ALL}")

def display_hold_time_stats(analysis: AnalysisResults) -> None:
    """显示持仓时间统计"""
    print_section("⏱️  持仓时间统计")

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
        elif days >= 1/24:
            hours = days * 24
            return f"{hours:.2f} 小时"
        else:
            minutes = days * 24 * 60
            return f"{minutes:.2f} 分钟"

    print()
    print_box_header("平均持仓时长")

    print_metric_row('今日', format_hold_time(stats.get('todayCount', 0)), "")
    print_metric_row('近 7 天', format_hold_time(stats.get('last7DaysAverage', 0)), "")
    print_metric_row('近 30 天', format_hold_time(stats.get('last30DaysAverage', 0)), "")
    print_metric_row('历史平均', format_hold_time(stats.get('allTimeAverage', 0)), "")

    print_box_footer()


# ========== 批量分析功能 ==========
def analyze_single_address_for_batch(address: str, calculator: ApexCalculator,
                                     force_refresh: bool = False) -> BatchAddressResult:
    """分析单个地址（用于批量处理）

    Args:
        address: 用户地址
        calculator: ApexCalculator 实例
        force_refresh: 是否强制刷新

    Returns:
        BatchAddressResult: 分析结果
    """
    try:
        results = calculator.analyze_user(address, force_refresh=force_refresh)

        if "error" in results:
            return BatchAddressResult(
                address=address,
                success=False,
                error_message=results['error']
            )

        # 提取关键指标
        win_rate_data = results.get('win_rate', {})
        hold_time_stats = results.get('hold_time_stats', {})
        data_summary = results.get('data_summary', {})
        position_analysis = results.get('position_analysis', {})
        sharpe_on_trades = results.get('sharpe_on_trades', {})

        # 创建 AnalysisResults 对象
        analysis = AnalysisResults(
            win_rate_data=win_rate_data,
            hold_time_stats=hold_time_stats,
            data_summary=data_summary,
            position_analysis=position_analysis,
            profit_factor=results.get('profit_factor', 0),
            raw_results=results
        )

        return BatchAddressResult(
            address=address,
            success=True,
            sharpe_ratio=sharpe_on_trades.get('annualized_sharpe'),
            profit_factor=results.get('profit_factor', 0),
            win_rate=win_rate_data.get('winRate', 0),
            total_trades=win_rate_data.get('totalTrades', 0),
            total_pnl=results.get('total_cumulative_pnl', 0),
            account_value=data_summary.get('account_value', 0),
            avg_hold_time=hold_time_stats.get('allTimeAverage', 0),
            analysis=analysis
        )

    except Exception as e:
        return BatchAddressResult(
            address=address,
            success=False,
            error_message=str(e)
        )


def display_batch_summary(results: List[BatchAddressResult]) -> None:
    """显示批量分析汇总

    Args:
        results: 批量分析结果列表
    """
    print_section("📊 批量分析汇总")

    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    print()
    print_box_header("分析统计")
    print_metric_row('总地址数', str(len(results)), "", COLOR_INFO)
    print_metric_row('成功', str(len(successful)), "", COLOR_SUCCESS)
    print_metric_row('失败', str(len(failed)), "", COLOR_ERROR if failed else COLOR_INFO)
    print_box_footer()

    if not successful:
        print(f"\n  {COLOR_ERROR}✗ 没有成功分析的地址{Style.RESET_ALL}")
        return

    # 排序选项
    print()
    print_box_header("排行榜 - 按 Sharpe Ratio")

    # 按 Sharpe Ratio 排序
    sorted_by_sharpe = sorted(
        [r for r in successful if r.sharpe_ratio is not None],
        key=lambda x: x.sharpe_ratio or 0,
        reverse=True
    )

    for i, r in enumerate(sorted_by_sharpe[:10], 1):
        sharpe_val = r.sharpe_ratio or 0
        if sharpe_val > 1:
            sharpe_color = COLOR_SUCCESS
        elif sharpe_val > 0:
            sharpe_color = COLOR_WARNING
        else:
            sharpe_color = COLOR_ERROR

        addr_short = f"{r.address[:6]}...{r.address[-4:]}"
        print(f"  {COLOR_INFO}{i:2}.{Style.RESET_ALL} {Fore.MAGENTA}{addr_short}{Style.RESET_ALL}  "
              f"Sharpe: {sharpe_color}{sharpe_val:>8.2f}{Style.RESET_ALL}  "
              f"WR: {Fore.WHITE}{r.win_rate:>6.1f}%{Style.RESET_ALL}  "
              f"PF: {Fore.WHITE}{format_number(r.profit_factor or 0, 2):>8}{Style.RESET_ALL}")

    print_box_footer()

    # 按 Profit Factor 排序
    print()
    print_box_header("排行榜 - 按 Profit Factor")

    sorted_by_pf = sorted(
        [r for r in successful if r.profit_factor is not None],
        key=lambda x: min(x.profit_factor or 0, 1000),  # 限制极端值
        reverse=True
    )

    for i, r in enumerate(sorted_by_pf[:10], 1):
        pf_val = r.profit_factor or 0
        if pf_val >= 1000:
            pf_str = "1000+"
            pf_color = COLOR_SUCCESS
        elif pf_val > 1:
            pf_str = format_number(pf_val, 2)
            pf_color = COLOR_SUCCESS
        else:
            pf_str = format_number(pf_val, 2)
            pf_color = COLOR_ERROR

        addr_short = f"{r.address[:6]}...{r.address[-4:]}"
        print(f"  {COLOR_INFO}{i:2}.{Style.RESET_ALL} {Fore.MAGENTA}{addr_short}{Style.RESET_ALL}  "
              f"PF: {pf_color}{pf_str:>8}{Style.RESET_ALL}  "
              f"WR: {Fore.WHITE}{r.win_rate:>6.1f}%{Style.RESET_ALL}  "
              f"Trades: {Fore.WHITE}{r.total_trades:>6}{Style.RESET_ALL}")

    print_box_footer()

    # 按胜率排序
    print()
    print_box_header("排行榜 - 按 Win Rate")

    sorted_by_wr = sorted(
        successful,
        key=lambda x: x.win_rate or 0,
        reverse=True
    )

    for i, r in enumerate(sorted_by_wr[:10], 1):
        wr_val = r.win_rate or 0
        if wr_val >= 60:
            wr_color = COLOR_SUCCESS
        elif wr_val >= 45:
            wr_color = COLOR_WARNING
        else:
            wr_color = COLOR_ERROR

        addr_short = f"{r.address[:6]}...{r.address[-4:]}"
        print(f"  {COLOR_INFO}{i:2}.{Style.RESET_ALL} {Fore.MAGENTA}{addr_short}{Style.RESET_ALL}  "
              f"WR: {wr_color}{wr_val:>6.1f}%{Style.RESET_ALL}  "
              f"Sharpe: {Fore.WHITE}{(r.sharpe_ratio or 0):>8.2f}{Style.RESET_ALL}  "
              f"PnL: {get_color_for_value(r.total_pnl or 0)}{format_currency(r.total_pnl or 0):>12}{Style.RESET_ALL}")

    print_box_footer()

    # 按 PnL 排序
    print()
    print_box_header("排行榜 - 按累计盈亏")

    sorted_by_pnl = sorted(
        successful,
        key=lambda x: x.total_pnl or 0,
        reverse=True
    )

    for i, r in enumerate(sorted_by_pnl[:10], 1):
        pnl_val = r.total_pnl or 0
        pnl_color = get_color_for_value(pnl_val)

        addr_short = f"{r.address[:6]}...{r.address[-4:]}"
        print(f"  {COLOR_INFO}{i:2}.{Style.RESET_ALL} {Fore.MAGENTA}{addr_short}{Style.RESET_ALL}  "
              f"PnL: {pnl_color}{format_currency(pnl_val):>12}{Style.RESET_ALL}  "
              f"WR: {Fore.WHITE}{r.win_rate:>6.1f}%{Style.RESET_ALL}  "
              f"Value: {Fore.WHITE}{format_currency(r.account_value or 0):>12}{Style.RESET_ALL}")

    print_box_footer()

    # 统计摘要
    print()
    print_box_header("统计摘要")

    sharpe_values = [r.sharpe_ratio for r in successful if r.sharpe_ratio is not None]
    pf_values = [r.profit_factor for r in successful if r.profit_factor is not None and r.profit_factor < 1000]
    wr_values = [r.win_rate for r in successful if r.win_rate is not None]
    pnl_values = [r.total_pnl for r in successful if r.total_pnl is not None]

    if sharpe_values:
        avg_sharpe = sum(sharpe_values) / len(sharpe_values)
        print_metric_row('平均 Sharpe Ratio', format_number(avg_sharpe, 2), "", get_color_for_value(avg_sharpe))

    if pf_values:
        avg_pf = sum(pf_values) / len(pf_values)
        print_metric_row('平均 Profit Factor', format_number(avg_pf, 2), "", get_color_for_value(avg_pf - 1))

    if wr_values:
        avg_wr = sum(wr_values) / len(wr_values)
        print_metric_row('平均 Win Rate', format_percentage(avg_wr), "", COLOR_INFO)

    if pnl_values:
        total_pnl_sum = sum(pnl_values)
        avg_pnl = total_pnl_sum / len(pnl_values)
        print_metric_row('平均累计盈亏', format_currency(avg_pnl), "", get_color_for_value(avg_pnl))
        print_metric_row('总累计盈亏', format_currency(total_pnl_sum), "", get_color_for_value(total_pnl_sum))

    profitable = len([r for r in successful if (r.total_pnl or 0) > 0])
    print_metric_row('盈利地址数', str(profitable), f"/ {len(successful)}", COLOR_SUCCESS)

    print_box_footer()

    # 显示失败的地址
    if failed:
        print()
        print_box_header("失败的地址")
        for r in failed:
            addr_short = f"{r.address[:6]}...{r.address[-4:]}"
            error_msg = (r.error_message or "未知错误")[:40]
            print(f"  {COLOR_ERROR}✗{Style.RESET_ALL} {Fore.MAGENTA}{addr_short}{Style.RESET_ALL}  "
                  f"{COLOR_DIM}{error_msg}{Style.RESET_ALL}")
        print_box_footer()


def display_batch_detail_table(results: List[BatchAddressResult]) -> None:
    """显示批量分析详细表格

    Args:
        results: 批量分析结果列表
    """
    successful = [r for r in results if r.success]
    if not successful:
        return

    print_section("📋 详细数据表格")

    # 表头
    print()
    header = (f"  {COLOR_TITLE}{'地址':<14} {'Sharpe':>8} {'PF':>8} {'WR':>7} "
              f"{'交易数':>7} {'累计PnL':>12} {'账户价值':>12}{Style.RESET_ALL}")
    print(header)
    print(f"  {COLOR_DIM}{'-' * 78}{Style.RESET_ALL}")

    # 按 Sharpe 排序显示所有地址
    sorted_results = sorted(
        successful,
        key=lambda x: x.sharpe_ratio or 0,
        reverse=True
    )

    for r in sorted_results:
        addr_short = f"{r.address[:6]}...{r.address[-4:]}"

        sharpe_val = r.sharpe_ratio or 0
        if sharpe_val > 1:
            sharpe_color = COLOR_SUCCESS
        elif sharpe_val > 0:
            sharpe_color = COLOR_WARNING
        else:
            sharpe_color = COLOR_ERROR

        pf_val = r.profit_factor or 0
        if pf_val >= 1000:
            pf_str = "1000+"
        else:
            pf_str = f"{pf_val:.2f}"

        pnl_color = get_color_for_value(r.total_pnl or 0)

        print(f"  {Fore.MAGENTA}{addr_short:<14}{Style.RESET_ALL} "
              f"{sharpe_color}{sharpe_val:>8.2f}{Style.RESET_ALL} "
              f"{Fore.WHITE}{pf_str:>8}{Style.RESET_ALL} "
              f"{Fore.WHITE}{r.win_rate:>6.1f}%{Style.RESET_ALL} "
              f"{Fore.WHITE}{r.total_trades:>7}{Style.RESET_ALL} "
              f"{pnl_color}{format_currency(r.total_pnl or 0):>12}{Style.RESET_ALL} "
              f"{Fore.WHITE}{format_currency(r.account_value or 0):>12}{Style.RESET_ALL}")

    print(f"  {COLOR_DIM}{'-' * 78}{Style.RESET_ALL}")


def export_batch_results(results: List[BatchAddressResult], filename: str) -> str:
    """导出批量分析结果到 JSON 文件

    Args:
        results: 批量分析结果列表
        filename: 输出文件名

    Returns:
        str: 保存结果信息
    """
    export_data = {
        'export_time': datetime.now().isoformat(),
        'total_addresses': len(results),
        'successful': len([r for r in results if r.success]),
        'failed': len([r for r in results if not r.success]),
        'results': []
    }

    for r in results:
        result_dict = {
            'address': r.address,
            'success': r.success,
            'sharpe_ratio': r.sharpe_ratio,
            'profit_factor': r.profit_factor if r.profit_factor and r.profit_factor < 1000 else (1000 if r.profit_factor and r.profit_factor >= 1000 else None),
            'win_rate': r.win_rate,
            'total_trades': r.total_trades,
            'total_pnl': r.total_pnl,
            'account_value': r.account_value,
            'avg_hold_time_days': r.avg_hold_time,
            'error_message': r.error_message
        }
        export_data['results'].append(result_dict)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    return f"结果已保存至 {filename}"


def analyze_batch_addresses(addresses: List[str], force_refresh: bool = False,
                            show_detail: bool = True, export_json: bool = False,
                            max_workers: int = 1) -> List[BatchAddressResult]:
    """批量分析多个地址

    Args:
        addresses: 地址列表
        force_refresh: 是否强制刷新
        show_detail: 是否显示每个地址的详细分析
        export_json: 是否导出 JSON
        max_workers: 最大并发数（默认 1，避免 API 限流）

    Returns:
        List[BatchAddressResult]: 分析结果列表
    """
    print_section(f"🔄 批量分析 - {len(addresses)} 个地址")

    # 根据地址数量自动调整并发数（保守策略避免 429）
    # 由于 API 限流严格，建议保持低并发
    effective_workers = min(max_workers, 2)  # 最多 2 并发
    estimated_time = len(addresses) * 8 / effective_workers  # 预估每个地址约 8 秒

    print()
    print_box_header("分析配置")
    print_metric_row('地址数量', str(len(addresses)), "", COLOR_INFO)
    print_metric_row('强制刷新', '是' if force_refresh else '否', "", COLOR_WARNING if force_refresh else COLOR_INFO)
    print_metric_row('并发数', str(effective_workers), f"(请求速率限制: 1.5/秒)", COLOR_INFO)
    print_metric_row('预计耗时', f"~{estimated_time/60:.1f} 分钟", "", COLOR_DIM)
    print_box_footer()

    results: List[BatchAddressResult] = []
    calculator = ApexCalculator()

    print()
    print(f"  {COLOR_INFO}开始分析（已启用全局速率限制避免 429）...{Style.RESET_ALL}\n")

    # 串行处理 - 最安全的方式避免 429
    if effective_workers == 1:
        for i, addr in enumerate(addresses, 1):
            addr_short = f"{addr[:6]}...{addr[-4:]}"
            progress = f"[{i}/{len(addresses)}]"

            try:
                result = analyze_single_address_for_batch(addr, calculator, force_refresh)
                results.append(result)

                if result.success:
                    sharpe_str = f"Sharpe: {result.sharpe_ratio:.2f}" if result.sharpe_ratio else "N/A"
                    print(f"  {COLOR_SUCCESS}✓{Style.RESET_ALL} {progress:>10} {Fore.MAGENTA}{addr_short}{Style.RESET_ALL} "
                          f"{COLOR_DIM}{sharpe_str}{Style.RESET_ALL}")
                else:
                    error_short = (result.error_message or "未知错误")[:30]
                    print(f"  {COLOR_ERROR}✗{Style.RESET_ALL} {progress:>10} {Fore.MAGENTA}{addr_short}{Style.RESET_ALL} "
                          f"{COLOR_ERROR}{error_short}{Style.RESET_ALL}")

            except Exception as e:
                results.append(BatchAddressResult(
                    address=addr,
                    success=False,
                    error_message=str(e)
                ))
                print(f"  {COLOR_ERROR}✗{Style.RESET_ALL} {progress:>10} {Fore.MAGENTA}{addr_short}{Style.RESET_ALL} "
                      f"{COLOR_ERROR}异常: {str(e)[:30]}{Style.RESET_ALL}")

            # 地址之间的间隔（让速率限制器有时间恢复）
            if i < len(addresses):
                time.sleep(1.0)

    else:
        # 使用线程池并发处理（低并发）
        with ThreadPoolExecutor(max_workers=effective_workers) as executor:
            future_to_addr = {
                executor.submit(analyze_single_address_for_batch, addr, calculator, force_refresh): addr
                for addr in addresses
            }

            completed = 0
            for future in as_completed(future_to_addr):
                addr = future_to_addr[future]
                completed += 1

                try:
                    result = future.result()
                    results.append(result)

                    # 进度显示
                    addr_short = f"{addr[:6]}...{addr[-4:]}"
                    progress = f"[{completed}/{len(addresses)}]"

                    if result.success:
                        sharpe_str = f"Sharpe: {result.sharpe_ratio:.2f}" if result.sharpe_ratio else "N/A"
                        print(f"  {COLOR_SUCCESS}✓{Style.RESET_ALL} {progress:>10} {Fore.MAGENTA}{addr_short}{Style.RESET_ALL} "
                              f"{COLOR_DIM}{sharpe_str}{Style.RESET_ALL}")
                    else:
                        error_short = (result.error_message or "未知错误")[:30]
                        print(f"  {COLOR_ERROR}✗{Style.RESET_ALL} {progress:>10} {Fore.MAGENTA}{addr_short}{Style.RESET_ALL} "
                              f"{COLOR_ERROR}{error_short}{Style.RESET_ALL}")

                except Exception as e:
                    results.append(BatchAddressResult(
                        address=addr,
                        success=False,
                        error_message=str(e)
                    ))
                    addr_short = f"{addr[:6]}...{addr[-4:]}"
                    progress = f"[{completed}/{len(addresses)}]"
                    print(f"  {COLOR_ERROR}✗{Style.RESET_ALL} {progress:>10} {Fore.MAGENTA}{addr_short}{Style.RESET_ALL} "
                          f"{COLOR_ERROR}异常: {str(e)[:30]}{Style.RESET_ALL}")

    print()

    # 显示汇总
    display_batch_summary(results)

    # 显示详细表格
    if show_detail:
        display_batch_detail_table(results)

    # 导出 JSON
    if export_json:
        print()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_filename = f"batch_analysis_{timestamp}.json"
        export_result = export_batch_results(results, json_filename)
        print_box_header("导出结果")
        print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}{export_result}{Style.RESET_ALL}")
        print_box_footer()

    return results


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
        print(f"\n{COLOR_INFO}{Style.BRIGHT}{BORDER_SINGLE * DISPLAY_WIDTH}{Style.RESET_ALL}")
        print(f"{COLOR_INFO}{Style.BRIGHT}│{Style.RESET_ALL}  {COLOR_TITLE}📊 分析用户{Style.RESET_ALL}")
        print(f"{COLOR_INFO}{Style.BRIGHT}│{Style.RESET_ALL}  {Fore.MAGENTA}{user_address}{Style.RESET_ALL}")
        print(f"{COLOR_INFO}{Style.BRIGHT}{BORDER_SINGLE * DISPLAY_WIDTH}{Style.RESET_ALL}")

        # 初始化计算器
        calculator = ApexCalculator()

        # 执行分析
        results = calculator.analyze_user(user_address, force_refresh=force_refresh)

        if "error" in results:
            logger.error(f"分析失败: {results['error']}")
            print()
            print_box_header("✗ 错误")
            print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_ERROR}分析失败: {results['error']}{Style.RESET_ALL}")
            print_box_footer()
            return False

        # 提取分析数据
        analysis = extract_analysis_data(calculator, results, user_address)
        if not analysis:
            logger.error("数据提取失败")
            print()
            print_box_header("✗ 错误")
            print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_ERROR}数据提取失败{Style.RESET_ALL}")
            print_box_footer()
            return False

        # 显示核心指标
        display_core_metrics(analysis)
        display_account_info(analysis)
        display_hold_time_stats(analysis)

        # 生成报告（可选）
        if generate_report:
            print_section("📄 生成 Markdown 报告")
            print()
            print_box_header("报告生成")
            report_filename = f"trading_report_{user_address[:8]}.md"
            save_result = generate_markdown_report(results, user_address, report_filename)
            print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}{save_result}{Style.RESET_ALL}")
            print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_DIM}💡 提示: 使用 Markdown 查看器打开报告文件{Style.RESET_ALL}")
            print_box_footer()
            print(f"\n{COLOR_INFO}{Style.BRIGHT}{BORDER_SINGLE * DISPLAY_WIDTH}{Style.RESET_ALL}")

        return True

    except KeyboardInterrupt:
        print()
        print()
        print_box_header("⚠ 警告")
        print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_WARNING}操作已取消{Style.RESET_ALL}")
        print_box_footer()
        return False

    except Exception as e:
        logger.error(f"分析过程出现错误: {str(e)}", exc_info=True)
        print()
        print_box_header("✗ 错误")
        print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_ERROR}分析过程出现错误: {str(e)}{Style.RESET_ALL}")
        print_box_footer()
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
        'batch': '--batch' in sys.argv or '-b' in sys.argv,
        'export_json': '--export' in sys.argv or '-e' in sys.argv,
        'no_detail': '--no-detail' in sys.argv,
        'addresses_file': None,
        'max_workers': 1,
        'user_address': None,
        'addresses': []
    }

    # 解析 --workers 参数
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg.startswith('--workers='):
            try:
                args['max_workers'] = int(arg.split('=')[1])
            except ValueError:
                pass
        elif arg == '--workers' and i + 1 < len(sys.argv):
            try:
                args['max_workers'] = int(sys.argv[i + 1])
            except ValueError:
                pass
        elif arg.startswith('--file='):
            args['addresses_file'] = arg.split('=')[1]
        elif arg == '--file' and i + 1 < len(sys.argv):
            args['addresses_file'] = sys.argv[i + 1]

    # 查找用户地址参数（支持多个地址）
    for arg in sys.argv[1:]:
        if arg.startswith('0x') and len(arg) == 42:
            if args['batch']:
                args['addresses'].append(arg)
            else:
                if args['user_address'] is None:
                    args['user_address'] = arg
                else:
                    # 如果有多个地址，自动切换到批量模式
                    args['batch'] = True
                    args['addresses'] = [args['user_address'], arg]
                    args['user_address'] = None

    return args

def display_help() -> None:
    """显示帮助信息"""
    title = "🚀 Apex Fork - 交易分析系统"
    title_padding = (DISPLAY_WIDTH - len(title) - 4) // 2

    print(f"\n{COLOR_INFO}{Style.BRIGHT}{BORDER_DOUBLE * DISPLAY_WIDTH}{Style.RESET_ALL}")
    print(f"{COLOR_INFO}{Style.BRIGHT}║{Style.RESET_ALL}{' ' * title_padding}{COLOR_TITLE}{title}{Style.RESET_ALL}{' ' * title_padding}{COLOR_INFO}{Style.BRIGHT}║{Style.RESET_ALL}")
    print(f"{COLOR_INFO}{Style.BRIGHT}{BORDER_DOUBLE * DISPLAY_WIDTH}{Style.RESET_ALL}\n")

    print_box_header("用法")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {Fore.WHITE}python main.py [用户地址] [选项]{Style.RESET_ALL}")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {Fore.WHITE}python main.py -b [地址1] [地址2] ...{Style.RESET_ALL} {COLOR_DIM}(批量模式){Style.RESET_ALL}")
    print_box_footer()
    print()

    print_box_header("参数")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}用户地址{Style.RESET_ALL}          {Fore.WHITE}Hyperliquid 用户地址（0x开头，42字符）{Style.RESET_ALL}")
    print(f"                      {COLOR_DIM}如果未提供，将使用默认示例地址{Style.RESET_ALL}")
    print_box_footer()
    print()

    print_box_header("基本选项")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}-h, --help{Style.RESET_ALL}       {Fore.WHITE}显示此帮助信息{Style.RESET_ALL}")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}-v, --verbose{Style.RESET_ALL}    {Fore.WHITE}显示详细日志{Style.RESET_ALL}")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}-d, --debug{Style.RESET_ALL}      {Fore.WHITE}显示调试信息{Style.RESET_ALL}")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}-r, --report{Style.RESET_ALL}     {Fore.WHITE}生成 Markdown 报告{Style.RESET_ALL}")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}-f, --force{Style.RESET_ALL}      {Fore.WHITE}强制刷新数据（跳过缓存）{Style.RESET_ALL}")
    print_box_footer()
    print()

    print_box_header("批量模式选项")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}-b, --batch{Style.RESET_ALL}      {Fore.WHITE}启用批量分析模式{Style.RESET_ALL}")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}-e, --export{Style.RESET_ALL}     {Fore.WHITE}导出结果到 JSON 文件{Style.RESET_ALL}")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}--no-detail{Style.RESET_ALL}      {Fore.WHITE}不显示详细表格{Style.RESET_ALL}")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}--workers=N{Style.RESET_ALL}      {Fore.WHITE}设置并发数（默认: 1，最大: 2）{Style.RESET_ALL}")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}--file=PATH{Style.RESET_ALL}      {Fore.WHITE}从文件读取地址列表（每行一个地址）{Style.RESET_ALL}")
    print_box_footer()
    print()

    print_box_header("单地址示例")
    print(f"  {COLOR_DIM}# 使用默认地址分析{Style.RESET_ALL}")
    print(f"  {COLOR_WARNING}python main.py{Style.RESET_ALL}\n")
    print(f"  {COLOR_DIM}# 分析指定地址{Style.RESET_ALL}")
    print(f"  {COLOR_WARNING}python main.py 0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf{Style.RESET_ALL}\n")
    print(f"  {COLOR_DIM}# 详细模式 + 生成报告{Style.RESET_ALL}")
    print(f"  {COLOR_WARNING}python main.py 0x3ca32dd3666ed1b69e86b86b420b058caa8c1aaf -v -r{Style.RESET_ALL}")
    print_box_footer()
    print()

    print_box_header("批量分析示例")
    print(f"  {COLOR_DIM}# 分析多个地址（命令行）{Style.RESET_ALL}")
    print(f"  {COLOR_WARNING}python main.py -b 0x...addr1 0x...addr2 0x...addr3{Style.RESET_ALL}\n")
    print(f"  {COLOR_DIM}# 从文件读取地址列表{Style.RESET_ALL}")
    print(f"  {COLOR_WARNING}python main.py -b --file=addresses.txt{Style.RESET_ALL}\n")
    print(f"  {COLOR_DIM}# 批量分析 + 导出 JSON + 2并发{Style.RESET_ALL}")
    print(f"  {COLOR_WARNING}python main.py -b --file=addresses.txt -e --workers=2{Style.RESET_ALL}")
    print_box_footer()
    print()

    print_box_header("功能说明")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}✓ 交易级别指标（推荐）{Style.RESET_ALL} {COLOR_DIM}- 完全不受出入金影响{Style.RESET_ALL}")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_WARNING}⚠ 账户级别指标{Style.RESET_ALL} {COLOR_DIM}- 受出入金影响，仅供对比参考{Style.RESET_ALL}")
    print(f"  {COLOR_INFO}•{Style.RESET_ALL} {COLOR_SUCCESS}✓ 批量模式{Style.RESET_ALL} {COLOR_DIM}- 支持排行榜、统计摘要、JSON导出{Style.RESET_ALL}")
    print_box_footer()
    print()

    print(f"  {Fore.BLUE}📖 文档: https://hyperliquid.gitbook.io/hyperliquid-docs{Style.RESET_ALL}")
    print(f"\n{COLOR_INFO}{Style.BRIGHT}{BORDER_SINGLE * DISPLAY_WIDTH}{Style.RESET_ALL}\n")

def load_addresses_from_file(filepath: str) -> List[str]:
    """从文件加载地址列表

    Args:
        filepath: 文件路径

    Returns:
        List[str]: 地址列表
    """
    addresses = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if line and not line.startswith('#'):
                    # 提取地址（支持 "address" 或 "address,comment" 格式）
                    addr = line.split(',')[0].strip().strip('"').strip("'")
                    if addr.startswith('0x') and len(addr) == 42:
                        addresses.append(addr)
    except FileNotFoundError:
        print(f"{COLOR_ERROR}✗ 文件不存在: {filepath}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{COLOR_ERROR}✗ 读取文件失败: {str(e)}{Style.RESET_ALL}")

    return addresses


# 预定义的批量地址列表（用于快速测试）
DEFAULT_BATCH_ADDRESSES = [
    "0xfbd99a273f18714c3893708a47b796a7ed6cbd4f",
    "0xb7c6c05dd58b6b6281295a499d8bdb9be22712ea",
    "0x9945eb53d066031cb91a5862db7a0ed2d9a8f812",
    "0x67e4d5c95fdd024d136d520b3432ad0f94ed5081",
    "0xcdd1172d31a68f6e404ad31d51fe45c5ebca90ac",
    "0x859662a281839206b1fa46dc695c7fd55c38f33f",
    "0xa006d6c9e507baedaeebe88fcd3acf646132e321",
    "0x7b7aa3257fcf2013727e0592348110de83067c1c",
    "0xdd0e7f3a80d5a9c2c299fafc5f5939ca58e2c116",
    "0x4f6345e02187f1fbefefa14d84938477347f3953",
    "0x278c6a51c509d213b3772fbe09264c1c18da81f9",
    "0x2f4974af193f3b57218f6ba3f2ecff0651b2f33d",
    "0x1f491d285ee4eb19cc0b835723076af8d352f1d5",
    "0xcd87ea212314217b6aa64fdffb9954330db5de4f",
    "0x5843ec7344670a4d13c25fb302ecfc6e488b15c5",
    "0xa38157f31371eec73fd878097c249f16472b066c",
    "0x7a6619c6f52063c4143d3142be56adbeec6a7b70",
    "0xfe2bdf909f81b20a38122b353351c5d8deddd6f0",
    "0x9da99bb7950b89ebb1d882bbb735f91b62f293f0",
    "0xde786a32f80731923d6297c14ef43ca1c8fd4b44",
]


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

    # 批量模式
    if args['batch']:
        # 收集地址
        addresses = []

        # 从文件加载
        if args['addresses_file']:
            addresses = load_addresses_from_file(args['addresses_file'])

        # 从命令行参数
        if args['addresses']:
            addresses.extend(args['addresses'])

        # 如果没有提供地址，使用预定义列表
        if not addresses:
            print(f"  {COLOR_WARNING}⚠ 未提供地址，使用预定义的20个地址列表{Style.RESET_ALL}")
            addresses = DEFAULT_BATCH_ADDRESSES

        # 去重
        addresses = list(dict.fromkeys(addresses))

        if not addresses:
            print(f"\n  {COLOR_ERROR}✗ 没有有效的地址可分析{Style.RESET_ALL}")
            sys.exit(1)

        # 执行批量分析
        results = analyze_batch_addresses(
            addresses=addresses,
            force_refresh=args['force_refresh'],
            show_detail=not args['no_detail'],
            export_json=args['export_json'],
            max_workers=args['max_workers']
        )

        # 统计成功率
        success_count = len([r for r in results if r.success])
        sys.exit(0 if success_count > 0 else 1)

    else:
        # 单地址模式
        user_address = args['user_address']
        if not user_address:
            user_address = "0x10a0a14196469a8849af7a6dba3419b371010bc9"

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
