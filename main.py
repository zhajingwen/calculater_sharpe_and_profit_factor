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

    # 生成 HTML 报告
    print()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_filename = f"trading_report_{timestamp}.html"

    html_result = generate_html_report_from_batch_results(
        results,
        title="Hyperliquid 交易地址分析报告",
        filename=html_filename
    )

    # 统计
    success_count = len([r for r in results if r.success])
    failed_count = len(results) - success_count

    print(f"📊 分析完成: {success_count} 成功, {failed_count} 失败")
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
                        addresses.append(addr)
    except FileNotFoundError:
        print(f"✗ 文件不存在: {filepath}")
    except Exception as e:
        print(f"✗ 读取文件失败: {str(e)}")

    return addresses


# 预定义的批量地址列表
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
        print("⚠ 未提供地址，使用预定义的 20 个地址列表")
        addresses = DEFAULT_BATCH_ADDRESSES

    # 执行分析
    results = analyze_batch_addresses(addresses, force_refresh=force_refresh)

    # 退出码
    success_count = len([r for r in results if r.success])
    sys.exit(0 if success_count > 0 else 1)


if __name__ == "__main__":
    main()
