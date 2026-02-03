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
    trade_sharpe: Dict[str, float]
    trade_dd: Dict[str, float]
    win_rate_data: Dict[str, Any]
    hold_time_stats: Dict[str, float]
    data_summary: Dict[str, Any]
    position_analysis: Dict[str, Any]
    profit_factor: float
    account_sharpe: float
    account_dd: float
    raw_results: Dict[str, Any]

# ========== 输出格式化 ==========
def print_section(title: str, char: str = "=") -> None:
    """打印分隔线"""
    line = char * 70
    print(f"\n{line}")
    print(f"{title}")
    print(f"{line}")
    logger.debug(f"Section: {title}")

def print_metric(label: str, value: str, icon: str = "  •") -> None:
    """打印指标"""
    print(f"{icon} {label}: {value}")
    logger.debug(f"Metric - {label}: {value}")

# ========== 数据提取 ==========
def extract_analysis_data(calculator: ApexCalculator, results: Dict[str, Any],
                          user_address: str) -> Optional[AnalysisResults]:
    """从结果中提取分析数据"""
    try:
        logger.info("开始提取分析数据...")

        # 获取嵌套数据
        win_rate_data = results.get('win_rate', {})
        hold_time_stats = results.get('hold_time_stats', {})
        data_summary = results.get('data_summary', {})
        position_analysis = results.get('position_analysis', {})

        logger.debug(f"Win rate data: {win_rate_data}")
        logger.debug(f"Position analysis: {position_analysis}")

        # 获取交易级别数据
        fills = results.get('_raw_fills', [])
        if not fills:
            logger.warning("未找到原始成交数据，重新获取...")
            user_data = calculator.get_user_data(user_address, force_refresh=False)
            fills = user_data.get('fills', [])

        logger.info(f"获取到 {len(fills)} 条成交记录")

        # 计算交易级别指标
        trade_sharpe = calculator.calculate_trade_level_sharpe_ratio(fills)
        trade_dd = calculator.calculate_trade_level_max_drawdown(fills)

        logger.info(f"交易级别 Sharpe: {trade_sharpe['annualized_sharpe']:.2f}")
        logger.info(f"交易级别最大回撤: {trade_dd['max_drawdown_pct']:.2f}%")

        return AnalysisResults(
            trade_sharpe=trade_sharpe,
            trade_dd=trade_dd,
            win_rate_data=win_rate_data,
            hold_time_stats=hold_time_stats,
            data_summary=data_summary,
            position_analysis=position_analysis,
            profit_factor=results.get('profit_factor', 0),
            account_sharpe=results.get('sharpe_ratio', 0),
            account_dd=results.get('max_drawdown', 0),
            raw_results=results
        )
    except Exception as e:
        logger.error(f"提取分析数据失败: {str(e)}", exc_info=True)
        return None

# ========== 输出模块 ==========
def display_header() -> None:
    """显示程序头部信息"""
    print("🚀 Apex Fork - 交易分析系统")
    print("基于Hyperliquid官方API和Apex Liquid Bot算法")
    print("✅ 完全不受出入金影响的准确指标")
    print("=" * 70)
    logger.info("Apex Fork 交易分析系统启动")

def display_core_metrics(analysis: AnalysisResults) -> None:
    """显示核心指标（交易级别）"""
    print_section("📈 核心指标（交易级别 - 完全不受出入金影响）")

    # Sharpe Ratio
    trade_sharpe = analysis.trade_sharpe
    print("\n✅ Sharpe Ratio (交易级别):")
    print_metric("年化 Sharpe", f"{trade_sharpe['annualized_sharpe']:.2f}")
    print_metric("每笔 Sharpe", f"{trade_sharpe['sharpe_ratio']:.4f}")
    print_metric("平均每笔收益率", f"{trade_sharpe['mean_return_per_trade']:.4%}")
    print_metric("收益率标准差", f"{trade_sharpe['std_dev']:.4%}")

    # 解读
    sharpe_val = trade_sharpe['annualized_sharpe']
    if sharpe_val > 1:
        interpretation = "✅ 优秀的风险调整收益"
        logger.info(f"Sharpe Ratio 评级: 优秀 ({sharpe_val:.2f})")
    elif sharpe_val > 0:
        interpretation = "⚠️  正收益但风险较高"
        logger.warning(f"Sharpe Ratio 评级: 风险较高 ({sharpe_val:.2f})")
    else:
        interpretation = "❌ 负的风险调整收益"
        logger.error(f"Sharpe Ratio 评级: 负收益 ({sharpe_val:.2f})")
    print_metric("评级", interpretation, icon="  →")

    # Max Drawdown
    trade_dd = analysis.trade_dd
    print("\n✅ Max Drawdown (交易级别):")
    print_metric("最大回撤", f"{trade_dd['max_drawdown_pct']:.2f}%")
    print_metric("峰值累计收益", f"{trade_dd['peak_return']:.2f}%")
    print_metric("谷底累计收益", f"{trade_dd['trough_return']:.2f}%")

    # 风险评级
    dd_pct = trade_dd['max_drawdown_pct']
    if dd_pct < 20:
        risk_level = "🟢 低风险"
        logger.info(f"风险等级: 低 ({dd_pct:.2f}%)")
    elif dd_pct < 50:
        risk_level = "🟡 中等风险"
        logger.warning(f"风险等级: 中等 ({dd_pct:.2f}%)")
    else:
        risk_level = "🔴 高风险"
        logger.error(f"风险等级: 高 ({dd_pct:.2f}%)")
    print_metric("风险等级", risk_level, icon="  →")

    # 交易统计
    print("\n✅ 交易统计:")
    print_metric("Profit Factor", f"{analysis.profit_factor:.4f}")
    print_metric("Win Rate", f"{analysis.win_rate_data.get('winRate', 0):.2f}%")
    print_metric("Direction Bias", f"{analysis.win_rate_data.get('bias', 0):.2f}%")
    print_metric("Total Trades", f"{analysis.win_rate_data.get('totalTrades', 0)}")
    print_metric("Avg Hold Time", f"{analysis.hold_time_stats.get('allTimeAverage', 0):.2f} 天")

def display_account_comparison(analysis: AnalysisResults) -> None:
    """显示账户级别对比"""
    print_section("⚠️  对比参考（账户级别 - 受出入金影响）", char="-")

    print("\n账户级别 Sharpe Ratio:")
    print_metric("Sharpe Ratio",
                f"{analysis.account_sharpe:.4f} ⚠️  受出入金影响", icon="  ")

    print("\n账户级别 Max Drawdown:")
    print_metric("Max Drawdown",
                f"{analysis.account_dd:.2f}% ⚠️  受出入金影响", icon="  ")

    # 对比说明
    print("\n💡 对比说明:")
    trade_sharpe_val = analysis.trade_sharpe['annualized_sharpe']
    account_sharpe_val = analysis.account_sharpe

    print(f"  • 交易级别 Sharpe ({trade_sharpe_val:.2f}) vs "
          f"账户级别 ({account_sharpe_val:.4f})")

    # 计算差异
    if abs(account_sharpe_val) > 0.001:
        diff_ratio = abs(trade_sharpe_val / account_sharpe_val)
        if diff_ratio > 10:
            msg = f"差异 {diff_ratio:.0f}x 说明账户级别严重失真"
            logger.warning(msg)
            print(f"  • {msg}")
        elif diff_ratio > 2:
            msg = f"差异 {diff_ratio:.1f}x 说明账户级别存在偏差"
            logger.info(msg)
            print(f"  • {msg}")
        else:
            msg = f"差异 {diff_ratio:.2f}x，两种方法较为接近"
            logger.info(msg)
            print(f"  • {msg}")
    else:
        msg = "账户级别 Sharpe 接近 0，无法进行有效对比"
        logger.warning(msg)
        print(f"  • {msg}")

    print(f"  • 推荐使用交易级别指标，因为：")
    print(f"    1. ✅ 完全不依赖账户价值")
    print(f"    2. ✅ 不受出入金影响")
    print(f"    3. ✅ 反映策略真实表现")

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

    print_metric("总账户价值", f"${total_account_value:,.2f}")
    print_metric("  ├─ Perp 账户价值", f"${perp_account_value:,.2f}")
    print_metric("  └─ Spot 账户价值", f"${spot_account_value:,.2f}")
    print_metric("Margin Used", f"${data_summary.get('total_margin_used', 0):,.2f}")
    print_metric("Current Positions", f"{position_analysis.get('total_positions', 0)}")

    # PNL信息
    print("\n盈亏统计:")
    total_cumulative_pnl = raw_results.get('total_cumulative_pnl', 0)
    total_realized_pnl = raw_results.get('total_realized_pnl', 0)
    total_unrealized_pnl = position_analysis.get('total_unrealized_pnl', 0)

    print_metric("累计总盈亏", f"${total_cumulative_pnl:,.2f}")
    print_metric("  ├─ 已实现盈亏", f"${total_realized_pnl:,.2f}")
    print_metric("  └─ 未实现盈亏", f"${total_unrealized_pnl:,.2f}")

    # 本金和收益率信息
    print("\n本金与收益率:")
    capital_info = raw_results.get('capital_info', {})
    return_metrics = raw_results.get('return_metrics', {})

    print_metric("真实本金", f"${capital_info.get('true_capital', 0):,.2f}")
    print_metric("  ├─ 总充值", f"${capital_info.get('total_deposits', 0):,.2f}")
    print_metric("  └─ 总提现", f"${capital_info.get('total_withdrawals', 0):,.2f}")
    print_metric("累计收益率", f"{return_metrics.get('cumulative_return', 0):.2f}%")
    print_metric("年化收益率", f"{return_metrics.get('annualized_return', 0):.2f}%")
    print_metric("  ├─ 净盈利", f"${return_metrics.get('net_profit', 0):,.2f}")
    print_metric("  └─ 交易天数", f"{return_metrics.get('trading_days', 0):.1f} 天")

    logger.debug(f"Total account value: ${total_account_value:,.2f}")
    logger.debug(f"Perp account value: ${perp_account_value:,.2f}")
    logger.debug(f"Spot account value: ${spot_account_value:,.2f}")
    logger.debug(f"Total cumulative PnL: ${total_cumulative_pnl:,.2f}")
    logger.debug(f"Positions: {position_analysis.get('total_positions', 0)}")

def display_hold_time_stats(analysis: AnalysisResults) -> None:
    """显示持仓时间统计"""
    print_section("⏱️  持仓时间统计")

    stats = analysis.hold_time_stats
    print_metric("今日平均", f"{stats.get('todayCount', 0):.2f} 天")
    print_metric("近7天平均", f"{stats.get('last7DaysAverage', 0):.2f} 天")
    print_metric("近30天平均", f"{stats.get('last30DaysAverage', 0):.2f} 天")
    print_metric("历史平均", f"{stats.get('allTimeAverage', 0):.2f} 天")

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

    # 优势
    print("\n✅ 优势:")
    advantages = []

    if analysis.trade_sharpe['annualized_sharpe'] > 1:
        advantages.append("优秀的风险调整收益（Sharpe > 1）")
    if analysis.trade_sharpe['mean_return_per_trade'] > 0:
        pct = analysis.trade_sharpe['mean_return_per_trade']
        advantages.append(f"正期望策略（每笔平均 {pct:.4%}）")
    if analysis.profit_factor > 1:
        advantages.append(f"盈利策略（Profit Factor = {analysis.profit_factor:.2f}）")

    if advantages:
        for adv in advantages:
            print(f"  • {adv}")
        logger.info(f"策略优势: {len(advantages)} 项")
    else:
        print("  • 暂无明显优势")
        logger.warning("策略未发现明显优势")

    # 风险
    print("\n⚠️  风险:")
    risks = []

    if analysis.trade_dd['max_drawdown_pct'] > 50:
        pct = analysis.trade_dd['max_drawdown_pct']
        risks.append(f"极高回撤风险（{pct:.2f}%）")
    if analysis.win_rate_data.get('winRate', 0) < 50:
        wr = analysis.win_rate_data.get('winRate', 0)
        risks.append(f"胜率偏低（{wr:.2f}%）")

    if risks:
        for risk in risks:
            print(f"  • {risk}")
        logger.warning(f"策略风险: {len(risks)} 项")
    else:
        print("  • 风险可控")
        logger.info("策略风险可控")

    # 改进建议
    print("\n💡 改进建议:")
    suggestions = []

    if analysis.trade_dd['max_drawdown_pct'] > 50:
        suggestions.extend([
            "考虑降低仓位大小",
            "添加更严格的止损机制"
        ])
    if analysis.win_rate_data.get('winRate', 0) < 45:
        suggestions.append("优化入场时机")
    suggestions.append("持续优化资金管理策略")

    for sug in suggestions:
        print(f"  • {sug}")

def display_usage_guide() -> None:
    """显示使用说明"""
    print_section("📚 使用说明")
    print("1. 将 user_address 替换为真实的Hyperliquid用户地址")
    print("2. 确保网络连接正常")
    print("3. 推荐使用交易级别指标（不受出入金影响）")
    print("4. 使用 --report 参数生成 Markdown 报告")
    print("5. 使用 --verbose 显示详细日志")
    print("6. 使用 --debug 显示调试信息")
    print("\n🔗 相关链接:")
    print("  • API文档: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api")
    print("  • 项目地址: https://github.com/your-repo/apex-fork")
    print("=" * 70)

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
        logger.info(f"开始分析用户: {user_address}")
        print(f"\n📊 分析用户: {user_address}")
        print("=" * 70)

        # 初始化计算器
        calculator = ApexCalculator()
        logger.debug("ApexCalculator 初始化完成")

        # 执行分析
        logger.info("执行完整分析...")
        results = calculator.analyze_user(user_address, force_refresh=force_refresh)

        if "error" in results:
            logger.error(f"分析失败: {results['error']}")
            print(f"\n❌ 分析失败: {results['error']}")
            return False

        logger.info("分析完成，开始提取数据...")

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
            logger.info("生成 Markdown 报告...")
            print("\n")
            print_section("📄 生成 Markdown 报告")
            report_filename = f"trading_report_{user_address[:8]}.md"
            save_result = generate_markdown_report(results, user_address, report_filename)
            print(f"\n{save_result}")
            print(f"💡 提示: 使用 Markdown 查看器打开报告文件")
            print("=" * 70)
            logger.info(f"报告已保存: {report_filename}")

        logger.info("分析流程完成")
        return True

    except KeyboardInterrupt:
        logger.warning("用户中断操作")
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

    logger.debug(f"解析参数: {args}")
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
        logger.info(f"使用默认示例地址: {user_address}")

    # 执行分析
    success = analyze_user_trading(
        user_address=user_address,
        force_refresh=args['force_refresh'],
        generate_report=args['report']
    )

    # 显示使用说明
    display_usage_guide()

    # 退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
