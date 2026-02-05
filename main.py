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

        # 提取筛选所需的指标
        total_trades = result.total_trades or 0

        # 从 raw_results 获取详细数据
        raw = result.analysis.raw_results
        hold_time_stats = result.analysis.hold_time_stats

        # 7天平均持仓时间（天）
        hold_time_7d = hold_time_stats.get('last7DaysAverage', 0)

        # 7天最小收益率（原始数据是小数，需要转换为百分比）
        return_metrics = raw.get('return_metrics_on_trades', {})
        min_return_7d = return_metrics.get('min_return_7d', 0) * 100  # 转为百分比

        # ROE 数据
        roe_24h_data = raw.get('roe_24h', {})
        roe_7d_data = raw.get('roe_7d', {})

        roe_24h = roe_24h_data.get('roe_percent', 0) if roe_24h_data.get('is_valid') else 0
        roe_7d = roe_7d_data.get('roe_percent', 0) if roe_7d_data.get('is_valid') else 0

        # 盈利因子
        profit_factor = result.profit_factor

        # 应用筛选条件
        if (total_trades > 10 and
            min_return_7d > -8 and
            hold_time_7d < 1 and
            roe_24h > -10 and
            roe_7d > 10 and
            profit_factor > 1.5):
            filtered.append(result)

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
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_filename = f"trading_report_{timestamp}.html"

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
DEFAULT_BATCH_ADDRESSES = [
    "0x1c91930125d0470c3902520b07b8882c6a2552c2",
    "0x7b7aa3257fcf2013727e0592348110de83067c1c",
    "0xcdd1172d31a68f6e404ad31d51fe45c5ebca90ac",
    "0x35a4b58e75360939f74af724098019aa15cc83bc",
    "0x859662a281839206b1fa46dc695c7fd55c38f33f",
    "0xdd0e7f3a80d5a9c2c299fafc5f5939ca58e2c116",
    "0xcc8e811404efeea2bfa2002db251ebabf43cb94a",
    "0x3866a89f0b7f13b3eea471022fc2182347ff61af",
    "0x67e4d5c95fdd024d136d520b3432ad0f94ed5081",
    "0x9945eb53d066031cb91a5862db7a0ed2d9a8f812",
    "0xa006d6c9e507baedaeebe88fcd3acf646132e321",
    "0xb7c6c05dd58b6b6281295a499d8bdb9be22712ea",
    "0xfbd99a273f18714c3893708a47b796a7ed6cbd4f",
    "0x3bdb59d8f7f62ae9231df716f8461fd97a2ae57b",
    "0x4f6345e02187f1fbefefa14d84938477347f3953",
    "0x138fb48dc319a514e13217acdb7ef97441f1b515",
    "0x0e66ea30180ea13ee91ca1d4d340f993cfb874ec",
    "0x278c6a51c509d213b3772fbe09264c1c18da81f9",
    "0xabcbf61d99a0641a082e20be30118fd9d1e0c151",
    "0x041867c358c1d2c51d16188d1db479424b0ea1db",
    "0x2f4974af193f3b57218f6ba3f2ecff0651b2f33d",
    "0xacec3accdb28be1e1e7fd2fd06e153e382fa6063",
    "0x1f491d285ee4eb19cc0b835723076af8d352f1d5",
    "0xcd87ea212314217b6aa64fdffb9954330db5de4f",
    "0x5843ec7344670a4d13c25fb302ecfc6e488b15c5",
    "0xa38157f31371eec73fd878097c249f16472b066c",
    "0x7a6619c6f52063c4143d3142be56adbeec6a7b70",
    "0xfe2bdf909f81b20a38122b353351c5d8deddd6f0",
    "0x9da99bb7950b89ebb1d882bbb735f91b62f293f0",
    "0xde786a32f80731923d6297c14ef43ca1c8fd4b44",
    "0xa9d7045c13ec29ce7d84124da39f2e633309a164",
    "0x0c9556f7b6897673d280d625e9540dd8022c19cf",
    "0xda8ea8c8da09afec518a955aba00c3f3efa8f168",
    "0xbd7b48a5f74fec74643899795b6964a8fac7e69a",
    "0xf0696b4f8f5ecbb699c7e8cb199db5e55675461c",
    "0x8b7e5e83679e10fcc9aadbb73e2476b7e2c4cc27",
    "0x3ff598667544d1e1feeb805aabb1d04ddb7c8b54",
    "0x60931f62c4a80623df942d0e88feb34c67bcff13",
    "0x58ce97d66ab1bffa2489f962821dc8b0cba5fa23",
    "0x845b62df45ba760938fc3c6d90a9d30ba3f98038",
    "0xdb7cc8d3b4bfb4365f59f0f66cd8a84b74b29a5c",
    "0x05cc4891dd3e207f337e94596cd61dec9ebb7aee",
    "0x40ec53aec62f7710f6a2b0f064cab998d198290c",
    "0xec938c0e8a2f73dfecb5076cd6a3aa72e906fc5b",
    "0x286ae03af6bb029cd7cf7d1e64849af6d2fb99e8",
    "0x806ea832ae8703cf703a8792268c8141d182158c",
    "0x21227ea490a30a756bc4ba3c9427bdf50ed55479",
    "0x77b021523b1dd41d0d98c50d3e1ad5d68bb15993",
    "0xcb67a9132d63ac732a7e21b1ff4c671b3db9139f",
    "0x8973af30506940bbf09ad792d9229dbd1d302ef4",
    "0x53cc2ef0a7c76fd25c4fc5ab6a6d14d1b8fcce16",
    "0x16aa234e82d7b51b8757110cbeeac6a65351785c",
    "0x121c93d3accf50bab046fe499fcefc07fbe6386a",
    "0x27c3e37b40e11802cb9705da44210fcc335ed032",
    "0x8da9e2e97cfea9006512d9f25757e9c0a4982bfd",
    "0x3962db0a8fe242549a489724f2596df05747a5d7",
    "0x9d9cf40cc0a279ec402d0b6a063bb6c6dbd55721",
    "0x07fd993f0fa3a185f7207adccd29f7a87404689d",
    "0xcca57e10217172545f2712562e13a243483bddcc",
    "0x49bc443b8ad4c077dddfb897fd10d3fd44e0c772",
    "0x9909c128feea2b6046026d75c0a29451d3427aa9",
    "0x2bed4b06bbdbcc66a470fbc662aa788d59795c79",
    "0xb8934845c3b00d53744b7e20a08b915d61e767c3",
    "0xb58216005588bc45bd342a2525d52e05c69d13ac",
    "0xbfb93dfdfcb6b0431983e62f31a298422c72ae26",
    "0xa01763dcdf2d7e23c3832b309a67ae51b509e910",
    "0x8bd31f540fb105cfd23120177074131265cc82d2",
    "0xac7cb1a684bac04010357888b55c29d40f1c8e85",
    "0xaba49c1098cc0fa65bf2393822ae8a350019f374",
    "0x27178fd7d728bbc792a776460f44852c8a9d458d",
    "0xcfbe141480a47ca5a1c98719fcf4f826737230b5",
    "0x562ad3b04e55e4a10dd689854ab2260397aabea0",
    "0x8e789a2df8040036cdc498bacd4f0c58f544f70e",
    "0x11f600e4f6afdffa4e5c92d596433e789080cc54",
    "0x826eba90429bff21646c5c56928ee397e424ac05",
    "0xa449037aaedcdbf6398a5d1ce0c172b55d27a51f",
    "0xe4a17737e61b0a265b357b54907a0d3dee2bab5f",
    "0xd8155b44c1487f7533279b27c6758931f5a91743",
    "0x972941561bf9b5200cd0c7ee592fdb401e2ba2d1",
    "0x3d6fcedf93c9d3650e498ceb35607e854ee73eaf",
    "0x9960e1e896038fc00d71040224758da65948817b",
    "0x524e0c66f6bee295650b0bcdb7e5069188f778db",
    "0x6a32a55c7eb57cc6efd218e5590c10c330b0bc1c",
    "0xe4d9d40170e32b062a33081b6d28f2a374604f95",
    "0xd848e901105b5baaca1608023371d41909c1a411",
    "0x25cb49a7bd9baa4b42ac0b5f7445692b58ced661",
    "0xccf595171e2e56655fb4d386b7424da16be69d42",
    "0x1e5cf44f64a66dae56104ed91bf15f6147200ac1",
    "0x20ebb54b4f0285da14e48698287f2baeaa7796b7",
    "0x4466d3a2417fd297611303542545e83fe5429546",
    "0x67766f38b50a29f427b762aea29583cee5f35dc1",
    "0xad59d3bc1907b740c6979c954a00acab7d19a487",
    "0xffef128b266a6d9663392ca7548dc73d9f30b4f4",
    "0x5bab6c73a08ecee96ef617c77ad10a9e1a8ad1fb",
    "0x14f79e252158fb6c042d4d940b0768e57cb35f3c",
    "0xd0a3ed257bbf5c2ad98b6269c05089fd8735ce09",
    "0xbeb49453a11dc0155af4dace1e74e04acaba6ef4",
    "0x0d8bf40b3a87036371a27e280d53174f437c4443",
    "0x3bd61edd15a4b002687d9c6d0f8e0b443ab1f5c4",
    "0xc1a43f6326865d672af92d620dd2885a87039db5",
    "0x836fe463b49da13a7cd305cb44cc63db424e89d7",
    "0x7842cd6f0a05b39eaff9b45c9d8f32696661f587",
    "0x76921b3d2d83fc9842b2f06a0219d2e26705a359",
    "0x999510ad3dd8c94a6659d6401d983137565283e3",
    "0x6b8fb543d3a3a8a47f91d30ca502b2ad126c11c9",
    "0xa938fa65b33add18ca2651e9dc3beb3f32feccdb",
    "0xb88e8b58e10982f997620aba8bcf4343d0b981fe",
    "0x1c6f572138aa26a47d34e570f474b963277b1b21",
    "0xedb1a7c093716f7f20097b4bedd4ae6e0dc1ea68",
    "0x9b15d52dbf7c97124bb7f5fdf0973c776f78d79c",
    "0x40ebad3d5648f1e542376c0e7152bd4018c9ce35",
    "0xee5f7a213fa1b87973e7a42a233cebaad6866dec",
    "0x4af52283ea6de9236c47b28e5dbf156453df8efb",
    "0x736dde3e0f5c588ddc53ad7f0f65667c0cca2801",
    "0x5af5bc81a11a1b28b0960752ea4d86c5ac34f245",
    "0x2689ee9c62e838955110191b672059c700a412dc",
    "0x6c192c6b860736663739a67c462d9a27e706b128",
    "0x513cf4896e8f37eb86841f7d33e81aa4704d95da",
    "0x2dafcc36215b481c331f05437959c428562064b6",
    "0x493364de7f4a39ed24f9c68ece229973f324d369",
    "0x0d41faff04314e43e198df9d8881f3d4ce40291e",
    "0x54e339d97d42abea6aa8a87d9c5845f84b1fd353",
    "0x3f5b197925c5fa1128f1a8cd115534fbe64ae1d3",
    "0x34f78cd823fea1284782641a11a56b9bdff2ce56",
    "0x88f9a3c5eb448900e4ebfdc9b15f09360f79bf47",
    "0x618d69438f6c5785a72d0024a8cb73b81c356e34",
    "0x15265abd25340534a96a6dffca1bb034b1e2a921",
    "0x6fbc81a3d7b430dcbd910d72f29e46b86d66f024",
    "0x2808b04baca6bc5bfd6e41ca83ece5416f87a950",
    "0xa1cb16d2b17202c336138f765559dfc73830b1fb",
    "0xde5a825bb6dfcad6f5ffebcccf7afcc0720c3f31",
    "0x4f923e42793f2d9259e8ac95f2f01c2abf30ed0b",
    "0xb186cf3d090abc44f93e07c7ad82d810a2d31a94",
    "0x3862e797ca5d0c8eafe519a2e8c0f5776f47c23b",
    "0x661fd6bd6baa2ca50b3c8171d59f9d0c54bda303",
    "0x1d1ba58c6ebdf12c4dad7545f81fae2baf2c710c",
    "0xe80c1be7333999be2d3d9a899e6f5aedd66d1904",
    "0xd11a880a60b889f9e88d260a3be04accd60c0efe",
    "0xca5ec0349ab9b76fc49cdf8847f1a638c70e0376",
    "0xb877df08df30c41e41ecd6b21368678aa78b80ba",
    "0xf61a6df7066dc9fb71612c3a4b67a595b7bdd622",
    "0xf19a8f29096ced385abb7c4930548121c97c8c40",
    "0x6feabb8ddc233c4aff8e189fded4736a63744dba",
    "0x9b10262e72747c5f5d517ecfa36e28fbf4ca67b9",
    "0x031fac9c6d5d4554bd976174d572ec4ff5a84e32",
    "0xe608e8278b7e12c0e7f27638630d4b850046f576",
    "0x10a0a14196469a8849af7a6dba3419b371010bc9",
    "0x736029b372703a7efd1c415ec17def15346312c4",
    "0x8d56d30d58d1a2709befccea6642252bab6ed51e",
    "0x27cf4ac68154c279fbb1e6bbf6da1907f9b5c87a",
    "0x260c941039ccd53976c41fe579a888280eeac386",
    "0x568e40b72fd34de4c422395317edfe8bee9fe582",
    "0x18cde66120c9195fb6e50a4b1e13bce4c85d1300",
    "0xda7f23460ba023e10b7d1208a207c37cd8f964bc",
    "0x2054190714542d114b294ea78a460895cd0fd1dc",
    "0x96fd9767ec0c97bd4b33a111a39b4a1d2276b8aa",
    "0xadc721fe657ae09d2a98978ff5c020f3a8088ab5",
    "0xb1de62cdf1440619fb0c62ce8e2d31b4ca4b9de7",
    "0xdfacfc5cd08371d4630daff794865a616e329e4c",
    "0xdb7f7eb6776ea3848e50bb60be6ff17b7e893ed3",
    "0x78006e0be97ce9cbda340f8ae7b11d3e48610ed4",
    "0x01ac7ced5d8f7d33e47894e1be305af927bd89c9",
    "0xea4fc1ae43d644b35e6874c32c49516ccb21df32",
    "0x685feceec46dd4e5c9b5b726f5d7550fd0eda526",
    "0xfd6481ec7daacf224e1f2cefb81ff70b426eaa9a",
    "0x0bd9017e1763bdb790998e4cfc90b6ad5e308f83",
    "0xacf38fc1301382b2d462bf4855abe80552923a7e",
    "0x2cc1a44ee510b23b8f0a0ace748fea2bdd4af6db",
    "0x3e781befd071c59d820725f70ce109298f750706",
    "0xaac1d9fbcb9148bf8d7747b1e1eeb7a9d80c3c78",
    "0xf7f819102ed1ff49377840676c50ada05165d369",
    "0xc09b7082026491173c90579a3b120a844be471e7",
    "0x6e73cb1acc122a1baccaab73937d7118dc185d40",
    "0xa4ac1d48fe393ac94e7f9480af8abd9360abf48a",
    "0xb656a808412666bba2233f6df08842d0e2634a08",
    "0xd8bc3c934b73879cb52ab06f14df0801fac48e6c",
    "0xa581bb0ac1a7ec393e76ccd45de2bfff6146e213",
    "0xf7d86ba83a120c5d8fb1251ac0f17520f9198cff",
    "0x6503fa99cdeadcc0d37e5d0b5966212b2950635c",
    "0x1afc8aa6600333f27378d5ecc846c512a7f1dd44",
    "0x9dea4d13ac1c469b7fe9049d43835df1be143ec0",
    "0x1a68598b176492dd92542e84ff79fa7ec06adda1",
    "0xf6af006e5ff6611b7e4a41bf8138b64877120a82",
    "0x39a2b5b857a702e95d7f1bd1a66d05a3154c05bc",
    "0x8628cc26699ca662a01f4e2f77b6e6dff4936048",
    "0xcf3d27e8d29e3d3a5349a5c284da25f3fd10a694",
    "0xc3921e7d79c020274f19c24894c759fc917a8f3a",
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
        print("⚠ 未提供地址，使用预定义的 20 个地址列表")
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
