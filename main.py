#!/usr/bin/env python3
"""
Apex Fork - Hyperliquid 交易分析系统
批量分析地址并生成 HTML 报告
"""

from apex_fork import ApexCalculator
from html_report_generator import generate_html_report_from_batch_results
import sys
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


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


# ========== 筛选功能 ==========
def filter_results_by_criteria(results: List[BatchAddressResult]) -> List[BatchAddressResult]:
    """
    根据预设筛选条件过滤分析结果

    筛选规则：
    - 交易数 > 10
    - 7天最小收益率 > -8%
    - 7天平均持仓时间 < 1天
    - ROE(24h) > -10%
    - ROE(7d) > 10%

    Args:
        results: BatchAddressResult 列表

    Returns:
        符合条件的 BatchAddressResult 列表
    """
    filtered = []

    for result in results:
        # 跳过失败的结果
        if not result.success or not result.analysis:
            continue

        addr_short = f"{result.address[:6]}...{result.address[-4:]}"

        # 提取筛选所需的指标
        total_trades = result.total_trades or 0

        # 从 raw_results 获取详细数据
        raw = result.analysis.raw_results
        hold_time_stats = result.analysis.hold_time_stats

        # 持仓时间
        hold_time_today = hold_time_stats.get('todayCount', 0)
        hold_time_7d = hold_time_stats.get('last7DaysAverage', 0)
        under_5min_ratio = hold_time_stats.get('under5minRatio', 0)

        # 7天最小收益率（原始数据是小数，需要转换为百分比）
        return_metrics = raw.get('return_metrics_on_trades', {})
        min_return_7d = return_metrics.get('min_return_7d', 0) * 100  # 转为百分比
        # 平均每笔交易的收益率
        mean_return = return_metrics.get('mean_return', 0) * 100

        # ROE 数据
        roe_24h_data = raw.get('roe_24h', {})
        roe_7d_data = raw.get('roe_7d', {})

        roe_24h = roe_24h_data.get('roe_percent', 0) if roe_24h_data.get('is_valid') else 0
        roe_7d = roe_7d_data.get('roe_percent', 0) if roe_7d_data.get('is_valid') else 0

        # 盈利因子
        profit_factor = result.profit_factor

        # 逐条检查筛选条件，记录未通过的条件
        failed_conditions = []
        if not (total_trades > 10):
            failed_conditions.append(f"总交易数={total_trades} (需要>10)")
        if not (min_return_7d > -8):
            failed_conditions.append(f"7天最小收益率={min_return_7d:.2f}% (需要>-8%)")
        if not (hold_time_7d < 1):
            failed_conditions.append(f"7天平均持仓时间={hold_time_7d:.4f}天 (需要<1天)")
        if not (hold_time_today < 0.083):
            failed_conditions.append(f"今日平均持仓时间={hold_time_today:.4f}天/{hold_time_today*24:.2f}h (需要<0.083天/2h)")
        if not (hold_time_7d < 0.083):
            failed_conditions.append(f"7天平均持仓时间={hold_time_7d:.4f}天/{hold_time_7d*24:.2f}h (需要<0.083天/2h)")
        if not (roe_24h > -10):
            failed_conditions.append(f"24h ROE={roe_24h:.2f}% (需要>-10%)")
        if not (roe_7d > 10):
            failed_conditions.append(f"7d ROE={roe_7d:.2f}% (需要>10%)")
        if not (mean_return > 2):
            failed_conditions.append(f"平均每笔收益率={mean_return:.2f}% (需要>2%)")
        if not (profit_factor > 2.5):
            failed_conditions.append(f"盈利因子={profit_factor:.2f} (需要>1.5)")
        if not (under_5min_ratio <= 40):
            failed_conditions.append(f"持仓<5分钟占比={under_5min_ratio:.1f}% (需要<=40%)")

        if not failed_conditions:
            filtered.append(result)
        else:
            print(f"   ⛔ {addr_short} 未通过筛选 ({len(failed_conditions)}项不达标):")
            for cond in failed_conditions:
                print(f"      ✗ {cond}")

    return filtered


# ========== 分析功能 ==========
def analyze_single_address(address: str, calculator: ApexCalculator,
                           force_refresh: bool = False) -> BatchAddressResult:
    """分析单个地址"""
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


def analyze_batch_addresses(addresses: List[str], force_refresh: bool = False) -> List[BatchAddressResult]:
    """批量分析多个地址并生成 HTML 报告"""

    print(f"\n🔍 Hyperliquid 交易地址分析")
    print(f"   地址数量: {len(addresses)}")
    print(f"   预计耗时: ~{len(addresses) * 8 / 60:.1f} 分钟\n")

    results: List[BatchAddressResult] = []
    calculator = ApexCalculator()

    for i, addr in enumerate(addresses, 1):
        addr_short = f"{addr[:6]}...{addr[-4:]}"

        try:
            result = analyze_single_address(addr, calculator, force_refresh)
            results.append(result)

            if result.success:
                sharpe_str = f"Sharpe: {result.sharpe_ratio:.2f}" if result.sharpe_ratio else "N/A"
                print(f"   ✓ [{i:3}/{len(addresses)}] {addr_short}  {sharpe_str}")
            else:
                error_short = (result.error_message or "未知错误")[:30]
                print(f"   ✗ [{i:3}/{len(addresses)}] {addr_short}  {error_short}")

        except Exception as e:
            results.append(BatchAddressResult(
                address=addr,
                success=False,
                error_message=str(e)
            ))
            print(f"   ✗ [{i:3}/{len(addresses)}] {addr_short}  异常: {str(e)[:30]}")

        # 地址之间的间隔
        if i < len(addresses):
            time.sleep(1.0)

    # 应用筛选条件
    filtered_results = filter_results_by_criteria(results)

    # 生成 HTML 报告
    print()
    html_filename = "trading_report.html"

    html_result = generate_html_report_from_batch_results(
        filtered_results,
        title="Hyperliquid 交易地址分析报告",
        filename=html_filename
    )

    # 统计
    success_count = len([r for r in results if r.success])
    failed_count = len(results) - success_count
    filtered_count = len(filtered_results)

    print(f"📊 分析完成: {success_count} 成功, {failed_count} 失败")
    print(f"🔍 筛选后: {filtered_count} 个地址符合条件")
    print(f"📄 {html_result}")

    return results


def load_addresses_from_file(filepath: str) -> List[str]:
    """从文件加载地址列表"""
    addresses = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    addr = line.split(',')[0].strip().strip('"').strip("'")
                    if addr.startswith('0x') and len(addr) == 42:
                        if addr in addresses:
                            continue
                        addresses.append(addr)
    except FileNotFoundError:
        print(f"✗ 文件不存在: {filepath}")
    except Exception as e:
        print(f"✗ 读取文件失败: {str(e)}")

    return addresses


def load_blacklist(filepath: str = "blacklist.txt") -> set:
    """加载黑名单地址"""
    blacklist = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    addr = line.split(',')[0].strip().strip('"').strip("'").lower()
                    if addr.startswith('0x') and len(addr) == 42:
                        blacklist.add(addr)
    except FileNotFoundError:
        pass  # 黑名单文件不存在时静默跳过
    except Exception as e:
        print(f"⚠ 读取黑名单失败: {str(e)}")
    return blacklist


# 预定义的批量地址列表
DEFAULT_BATCH_ADDRESSES = []


def display_help() -> None:
    """显示帮助信息"""
    print("""
🔍 Hyperliquid 交易地址分析系统

用法:
    python main.py [地址1] [地址2] ...     分析指定地址
    python main.py --file=addresses.txt    从文件读取地址
    python main.py                         使用预定义地址列表

选项:
    -h, --help       显示帮助
    -f, --force      强制刷新数据（跳过缓存）
    --file=PATH      从文件读取地址列表（每行一个）

黑名单:
    blacklist.txt    存放需要跳过的地址（每行一个，自动过滤）

示例:
    python main.py 0xfbd99a273f18714c3893708a47b796a7ed6cbd4f
    python main.py --file=addresses.txt
    python main.py --file=addresses.txt -f

输出:
    生成 HTML 报告文件 (trading_report_YYYYMMDD_HHMMSS.html)
    - 深色主题界面
    - 点击表头可排序
    - 支持搜索和列选择
    - 20+ 交易指标
""")


def main() -> None:
    """主函数"""
    # 解析参数
    args = sys.argv[1:]

    # 帮助
    if '-h' in args or '--help' in args:
        display_help()
        return

    # 强制刷新
    force_refresh = '-f' in args or '--force' in args

    # 收集地址
    addresses = []

    # 从文件加载
    for arg in args:
        if arg.startswith('--file='):
            filepath = arg.split('=', 1)[1]
            addresses = load_addresses_from_file(filepath)
            break

    # 从命令行参数
    for arg in args:
        if arg.startswith('0x') and len(arg) == 42:
            addresses.append(arg)

    # 去重
    addresses = list(dict.fromkeys(addresses))

    # 如果没有地址，使用默认列表
    if not addresses:
        print("⚠ 未提供地址，使用预定义的地址列表")
        addresses = DEFAULT_BATCH_ADDRESSES

    # 过滤黑名单地址
    blacklist = load_blacklist()
    if blacklist:
        original_count = len(addresses)
        addresses = [addr for addr in addresses if addr.lower() not in blacklist]
        filtered_count = original_count - len(addresses)
        if filtered_count > 0:
            print(f"⛔ 已过滤 {filtered_count} 个黑名单地址")

    # 执行分析
    results = analyze_batch_addresses(addresses, force_refresh=force_refresh)

    # 退出码
    success_count = len([r for r in results if r.success])
    sys.exit(0 if success_count > 0 else 1)


if __name__ == "__main__":
    main()
