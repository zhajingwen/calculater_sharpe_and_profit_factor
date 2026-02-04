#!/usr/bin/env python3
"""
HTML 报告生成器 - 支持表格排序和深色主题
生成类似 Hyperliquid 交易地址分析报告的 HTML 表格
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class AddressMetrics:
    """地址指标数据类 - 包含所有计算指标"""
    # 基础信息
    address: str
    rank: int = 0

    # 核心交易指标
    total_trades: int = 0
    win_rate: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 0.0

    # 盈亏指标
    total_pnl: float = 0.0
    total_realized_pnl: float = 0.0
    total_unrealized_pnl: float = 0.0

    # 账户信息
    account_value: float = 0.0
    perp_account_value: float = 0.0
    spot_account_value: float = 0.0
    total_margin_used: float = 0.0

    # 收益率指标
    mean_return: float = 0.0
    std_return: float = 0.0
    trades_per_year: float = 0.0
    trading_days: float = 0.0

    # 方向偏好
    bias: float = 50.0
    long_positions: int = 0
    short_positions: int = 0
    total_positions: int = 0
    position_bias: str = "中性"

    # 持仓时间
    avg_hold_time: float = 0.0
    hold_time_today: float = 0.0
    hold_time_7d: float = 0.0
    hold_time_30d: float = 0.0

    # ROE 指标
    roe_24h: float = 0.0
    roe_7d: float = 0.0
    roe_30d: float = 0.0
    roe_all: float = 0.0

    # 状态
    success: bool = True
    error_message: Optional[str] = None


def extract_metrics_from_result(result: Dict[str, Any], address: str) -> AddressMetrics:
    """从分析结果中提取所有指标"""

    # 检查是否成功
    if not result.get('success', True) or 'error' in result:
        return AddressMetrics(
            address=address,
            success=False,
            error_message=result.get('error_message') or result.get('error', '分析失败')
        )

    # 提取各类数据
    win_rate_data = result.get('win_rate', {})
    hold_time_stats = result.get('hold_time_stats', {})
    data_summary = result.get('data_summary', {})
    position_analysis = result.get('position_analysis', {})
    sharpe_on_trades = result.get('sharpe_on_trades', {})
    return_metrics = result.get('return_metrics_on_trades', {})

    # ROE 数据
    roe_24h = result.get('roe_24h', {})
    roe_7d = result.get('roe_7d', {})
    roe_30d = result.get('roe_30d', {})
    roe_all = result.get('roe_all', {})

    return AddressMetrics(
        address=address,

        # 核心交易指标
        total_trades=win_rate_data.get('totalTrades', 0),
        win_rate=win_rate_data.get('winRate', 0),
        sharpe_ratio=sharpe_on_trades.get('annualized_sharpe', 0),
        profit_factor=result.get('profit_factor', 0),

        # 盈亏指标
        total_pnl=result.get('total_cumulative_pnl', 0),
        total_realized_pnl=result.get('total_realized_pnl', 0),
        total_unrealized_pnl=position_analysis.get('total_unrealized_pnl', 0),

        # 账户信息
        account_value=data_summary.get('account_value', 0),
        perp_account_value=data_summary.get('perp_account_value', 0),
        spot_account_value=data_summary.get('spot_account_value', 0),
        total_margin_used=data_summary.get('total_margin_used', 0),

        # 收益率指标
        mean_return=sharpe_on_trades.get('mean_return', 0),
        std_return=sharpe_on_trades.get('std_return', 0),
        trades_per_year=sharpe_on_trades.get('trades_per_year', 0),
        trading_days=return_metrics.get('trading_days', 0),

        # 方向偏好
        bias=win_rate_data.get('bias', 50),
        long_positions=position_analysis.get('long_positions', 0),
        short_positions=position_analysis.get('short_positions', 0),
        total_positions=position_analysis.get('total_positions', 0),
        position_bias=position_analysis.get('position_bias', '中性'),

        # 持仓时间
        avg_hold_time=hold_time_stats.get('allTimeAverage', 0),
        hold_time_today=hold_time_stats.get('todayCount', 0),
        hold_time_7d=hold_time_stats.get('last7DaysAverage', 0),
        hold_time_30d=hold_time_stats.get('last30DaysAverage', 0),

        # ROE 指标
        roe_24h=roe_24h.get('roe_percent', 0) if roe_24h.get('is_valid') else 0,
        roe_7d=roe_7d.get('roe_percent', 0) if roe_7d.get('is_valid') else 0,
        roe_30d=roe_30d.get('roe_percent', 0) if roe_30d.get('is_valid') else 0,
        roe_all=roe_all.get('roe_percent', 0) if roe_all.get('is_valid') else 0,

        success=True
    )


def format_currency(value: float) -> str:
    """格式化货币"""
    if abs(value) >= 1000000:
        return f"${value/1000000:,.2f}M"
    elif abs(value) >= 1000:
        return f"${value:,.0f}"
    else:
        return f"${value:,.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """格式化百分比"""
    return f"{value:.{decimals}f}%"


def format_number(value: float, decimals: int = 2) -> str:
    """格式化数字"""
    if value >= 1000:
        return f"{value:,.{decimals}f}"
    return f"{value:.{decimals}f}"


def format_hold_time(days: float) -> str:
    """智能格式化持仓时间"""
    if days == 0:
        return "0"
    elif days >= 1:
        return f"{days:.1f}天"
    elif days >= 1/24:
        return f"{days * 24:.1f}时"
    else:
        return f"{days * 24 * 60:.0f}分"


def format_profit_factor(pf: float) -> str:
    """格式化盈利因子"""
    if pf >= 1000:
        return "∞"
    return f"{pf:.2f}"


def generate_html_report(
    metrics_list: List[AddressMetrics],
    title: str = "Hyperliquid 交易地址分析报告",
    filename: str = "trading_report.html"
) -> str:
    """
    生成 HTML 格式的分析报告

    Args:
        metrics_list: AddressMetrics 列表
        title: 报告标题
        filename: 输出文件名

    Returns:
        保存结果消息
    """

    # 过滤成功的结果并排序
    successful = [m for m in metrics_list if m.success]
    successful.sort(key=lambda x: x.sharpe_ratio, reverse=True)

    # 分配排名
    for i, m in enumerate(successful, 1):
        m.rank = i

    # 生成表格数据 JSON
    table_data = []
    for m in successful:
        table_data.append({
            'rank': m.rank,
            'address': m.address,
            'total_trades': m.total_trades,
            'win_rate': m.win_rate,
            'sharpe_ratio': m.sharpe_ratio,
            'profit_factor': m.profit_factor,
            'total_pnl': m.total_pnl,
            'account_value': m.account_value,
            'mean_return': m.mean_return * 100,  # 转为百分比
            'std_return': m.std_return * 100,
            'bias': m.bias,
            'avg_hold_time': m.avg_hold_time,
            'roe_24h': m.roe_24h,
            'roe_7d': m.roe_7d,
            'roe_30d': m.roe_30d,
            'roe_all': m.roe_all,
            'total_positions': m.total_positions,
            'trading_days': m.trading_days,
            'total_realized_pnl': m.total_realized_pnl,
            'total_unrealized_pnl': m.total_unrealized_pnl,
        })

    # 统计信息
    total_count = len(metrics_list)
    success_count = len(successful)
    failed_count = total_count - success_count

    avg_sharpe = sum(m.sharpe_ratio for m in successful) / success_count if success_count else 0
    avg_win_rate = sum(m.win_rate for m in successful) / success_count if success_count else 0
    total_pnl_sum = sum(m.total_pnl for m in successful)
    profitable_count = len([m for m in successful if m.total_pnl > 0])

    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --border-color: #30363d;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --text-muted: #6e7681;
            --accent-cyan: #58a6ff;
            --accent-green: #3fb950;
            --accent-red: #f85149;
            --accent-yellow: #d29922;
            --accent-purple: #a371f7;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            padding: 20px;
        }}

        .container {{
            max-width: 1800px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 30px;
        }}

        .header h1 {{
            font-size: 2rem;
            color: var(--accent-cyan);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }}

        .header .subtitle {{
            color: var(--text-secondary);
            margin-top: 8px;
            font-size: 0.9rem;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}

        .stat-card .label {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-bottom: 4px;
        }}

        .stat-card .value {{
            font-size: 1.5rem;
            font-weight: 600;
        }}

        .stat-card .value.positive {{
            color: var(--accent-green);
        }}

        .stat-card .value.negative {{
            color: var(--accent-red);
        }}

        .table-container {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
        }}

        .table-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color);
        }}

        .table-header h2 {{
            font-size: 1.1rem;
            color: var(--text-primary);
        }}

        .table-controls {{
            display: flex;
            gap: 12px;
            align-items: center;
        }}

        .search-input {{
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 8px 12px;
            color: var(--text-primary);
            font-size: 0.9rem;
            width: 250px;
        }}

        .search-input:focus {{
            outline: none;
            border-color: var(--accent-cyan);
        }}

        .table-wrapper {{
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}

        th {{
            background: var(--bg-tertiary);
            color: var(--accent-cyan);
            font-weight: 600;
            text-align: left;
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
            white-space: nowrap;
            cursor: pointer;
            user-select: none;
            position: relative;
        }}

        th:hover {{
            background: var(--bg-primary);
        }}

        th .sort-icon {{
            margin-left: 4px;
            opacity: 0.3;
        }}

        th.sort-asc .sort-icon,
        th.sort-desc .sort-icon {{
            opacity: 1;
        }}

        th.sort-asc .sort-icon::after {{
            content: '▲';
        }}

        th.sort-desc .sort-icon::after {{
            content: '▼';
        }}

        th:not(.sort-asc):not(.sort-desc) .sort-icon::after {{
            content: '⇅';
        }}

        td {{
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
            white-space: nowrap;
        }}

        tr:hover {{
            background: var(--bg-tertiary);
        }}

        .rank {{
            color: var(--text-muted);
            font-weight: 500;
        }}

        .address {{
            font-family: 'SF Mono', Monaco, 'Andale Mono', monospace;
            color: var(--accent-purple);
            font-size: 0.85rem;
        }}

        .positive {{
            color: var(--accent-green);
        }}

        .negative {{
            color: var(--accent-red);
        }}

        .neutral {{
            color: var(--text-secondary);
        }}

        .highlight {{
            font-weight: 600;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 30px;
            border-top: 1px solid var(--border-color);
        }}

        .column-toggle {{
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 8px 16px;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 0.85rem;
        }}

        .column-toggle:hover {{
            background: var(--bg-primary);
        }}

        .column-menu {{
            position: absolute;
            top: 100%;
            right: 0;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px;
            z-index: 100;
            display: none;
            min-width: 200px;
            max-height: 400px;
            overflow-y: auto;
        }}

        .column-menu.show {{
            display: block;
        }}

        .column-menu label {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 0;
            cursor: pointer;
            font-size: 0.85rem;
        }}

        .column-menu label:hover {{
            color: var(--accent-cyan);
        }}

        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .table-controls {{
                flex-direction: column;
                align-items: stretch;
            }}

            .search-input {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 {title}</h1>
            <p class="subtitle">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 数据来源: Hyperliquid API</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">分析地址数</div>
                <div class="value">{success_count} / {total_count}</div>
            </div>
            <div class="stat-card">
                <div class="label">平均夏普比率</div>
                <div class="value {'positive' if avg_sharpe > 0 else 'negative'}">{avg_sharpe:.2f}</div>
            </div>
            <div class="stat-card">
                <div class="label">平均胜率</div>
                <div class="value">{avg_win_rate:.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="label">总累计盈亏</div>
                <div class="value {'positive' if total_pnl_sum > 0 else 'negative'}">{format_currency(total_pnl_sum)}</div>
            </div>
            <div class="stat-card">
                <div class="label">盈利地址数</div>
                <div class="value positive">{profitable_count} / {success_count}</div>
            </div>
        </div>

        <div class="table-container">
            <div class="table-header">
                <h2>📊 详细数据表格</h2>
                <div class="table-controls">
                    <input type="text" class="search-input" id="searchInput" placeholder="搜索地址...">
                    <div style="position: relative;">
                        <button class="column-toggle" id="columnToggle">显示列 ▼</button>
                        <div class="column-menu" id="columnMenu">
                            <!-- 列选择器将由 JS 生成 -->
                        </div>
                    </div>
                </div>
            </div>
            <div class="table-wrapper">
                <table id="dataTable">
                    <thead>
                        <tr id="tableHeader">
                            <!-- 表头将由 JS 生成 -->
                        </tr>
                    </thead>
                    <tbody id="tableBody">
                        <!-- 数据将由 JS 生成 -->
                    </tbody>
                </table>
            </div>
        </div>

        <div class="footer">
            <p>📈 Apex Fork - 交易分析系统 | 基于 Hyperliquid 官方 API</p>
            <p>所有指标基于单笔交易收益率计算，不依赖本金数据</p>
        </div>
    </div>

    <script>
        // 表格数据
        const tableData = {json.dumps(table_data, ensure_ascii=False)};

        // 列定义
        const columns = [
            {{ key: 'rank', label: '#', format: v => v, defaultVisible: true }},
            {{ key: 'address', label: '地址', format: v => v, defaultVisible: true, isAddress: true }},
            {{ key: 'total_trades', label: '交易数', format: v => v.toLocaleString(), defaultVisible: true }},
            {{ key: 'win_rate', label: '胜率', format: v => v.toFixed(1) + '%', defaultVisible: true }},
            {{ key: 'sharpe_ratio', label: '夏普比率', format: v => v.toFixed(2), defaultVisible: true, colorByValue: true }},
            {{ key: 'profit_factor', label: '盈利因子', format: v => v >= 1000 ? '∞' : v.toFixed(2), defaultVisible: true, colorByValue: true, threshold: 1 }},
            {{ key: 'total_pnl', label: '总PNL', format: v => formatCurrency(v), defaultVisible: true, colorByValue: true, isCurrency: true }},
            {{ key: 'account_value', label: '账户价值', format: v => formatCurrency(v), defaultVisible: true, isCurrency: true }},
            {{ key: 'mean_return', label: '平均收益率', format: v => v.toFixed(2) + '%', defaultVisible: true, colorByValue: true }},
            {{ key: 'std_return', label: '收益率标准差', format: v => v.toFixed(2) + '%', defaultVisible: false }},
            {{ key: 'bias', label: '方向偏好', format: v => v.toFixed(1) + '%', defaultVisible: false }},
            {{ key: 'avg_hold_time', label: '平均持仓时间', format: v => formatHoldTime(v), defaultVisible: true }},
            {{ key: 'roe_24h', label: 'ROE(24h)', format: v => (v >= 0 ? '+' : '') + v.toFixed(2) + '%', defaultVisible: true, colorByValue: true }},
            {{ key: 'roe_7d', label: 'ROE(7d)', format: v => (v >= 0 ? '+' : '') + v.toFixed(2) + '%', defaultVisible: false, colorByValue: true }},
            {{ key: 'roe_30d', label: 'ROE(30d)', format: v => (v >= 0 ? '+' : '') + v.toFixed(2) + '%', defaultVisible: false, colorByValue: true }},
            {{ key: 'roe_all', label: 'ROE(历史)', format: v => (v >= 0 ? '+' : '') + v.toFixed(2) + '%', defaultVisible: false, colorByValue: true }},
            {{ key: 'total_positions', label: '当前持仓', format: v => v, defaultVisible: false }},
            {{ key: 'trading_days', label: '交易天数', format: v => v.toFixed(1), defaultVisible: false }},
            {{ key: 'total_realized_pnl', label: '已实现PNL', format: v => formatCurrency(v), defaultVisible: false, colorByValue: true, isCurrency: true }},
            {{ key: 'total_unrealized_pnl', label: '未实现PNL', format: v => formatCurrency(v), defaultVisible: false, colorByValue: true, isCurrency: true }},
        ];

        // 可见列
        let visibleColumns = columns.filter(c => c.defaultVisible).map(c => c.key);

        // 当前排序
        let currentSort = {{ key: 'rank', dir: 'asc' }};

        // 格式化函数
        function formatCurrency(value) {{
            if (Math.abs(value) >= 1000000) {{
                return '$' + (value / 1000000).toFixed(2) + 'M';
            }} else if (Math.abs(value) >= 1000) {{
                return '$' + value.toLocaleString(undefined, {{ maximumFractionDigits: 0 }});
            }} else {{
                return '$' + value.toFixed(2);
            }}
        }}

        function formatHoldTime(days) {{
            if (days === 0) return '0';
            if (days >= 1) return days.toFixed(1) + '天';
            if (days >= 1/24) return (days * 24).toFixed(1) + '时';
            return (days * 24 * 60).toFixed(0) + '分';
        }}

        // 渲染表头
        function renderHeader() {{
            const header = document.getElementById('tableHeader');
            header.innerHTML = '';

            visibleColumns.forEach(key => {{
                const col = columns.find(c => c.key === key);
                const th = document.createElement('th');
                th.dataset.key = key;
                th.innerHTML = `${{col.label}} <span class="sort-icon"></span>`;

                if (currentSort.key === key) {{
                    th.classList.add(currentSort.dir === 'asc' ? 'sort-asc' : 'sort-desc');
                }}

                th.addEventListener('click', () => sortTable(key));
                header.appendChild(th);
            }});
        }}

        // 渲染表格数据
        function renderTable(data) {{
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';

            data.forEach(row => {{
                const tr = document.createElement('tr');

                visibleColumns.forEach(key => {{
                    const col = columns.find(c => c.key === key);
                    const td = document.createElement('td');
                    const value = row[key];

                    // 格式化显示
                    td.textContent = col.format(value);

                    // 特殊样式
                    if (col.isAddress) {{
                        td.classList.add('address');
                    }}

                    if (key === 'rank') {{
                        td.classList.add('rank');
                    }}

                    // 根据值着色
                    if (col.colorByValue) {{
                        const threshold = col.threshold || 0;
                        if (value > threshold) {{
                            td.classList.add('positive', 'highlight');
                        }} else if (value < threshold) {{
                            td.classList.add('negative');
                        }} else {{
                            td.classList.add('neutral');
                        }}
                    }}

                    tr.appendChild(td);
                }});

                tbody.appendChild(tr);
            }});
        }}

        // 排序表格
        function sortTable(key) {{
            if (currentSort.key === key) {{
                currentSort.dir = currentSort.dir === 'asc' ? 'desc' : 'asc';
            }} else {{
                currentSort.key = key;
                currentSort.dir = 'desc';
            }}

            const sortedData = [...tableData].sort((a, b) => {{
                let aVal = a[key];
                let bVal = b[key];

                // 字符串比较
                if (typeof aVal === 'string') {{
                    return currentSort.dir === 'asc'
                        ? aVal.localeCompare(bVal)
                        : bVal.localeCompare(aVal);
                }}

                // 数字比较
                return currentSort.dir === 'asc' ? aVal - bVal : bVal - aVal;
            }});

            renderHeader();
            renderTable(sortedData);
        }}

        // 搜索功能
        function filterTable(searchTerm) {{
            const filtered = tableData.filter(row =>
                row.address.toLowerCase().includes(searchTerm.toLowerCase())
            );
            renderTable(filtered);
        }}

        // 列选择器
        function renderColumnMenu() {{
            const menu = document.getElementById('columnMenu');
            menu.innerHTML = '';

            columns.forEach(col => {{
                const label = document.createElement('label');
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.checked = visibleColumns.includes(col.key);
                checkbox.addEventListener('change', () => {{
                    if (checkbox.checked) {{
                        visibleColumns.push(col.key);
                    }} else {{
                        visibleColumns = visibleColumns.filter(k => k !== col.key);
                    }}
                    // 保持原始顺序
                    visibleColumns = columns.filter(c => visibleColumns.includes(c.key)).map(c => c.key);
                    renderHeader();
                    sortTable(currentSort.key);
                }});

                label.appendChild(checkbox);
                label.appendChild(document.createTextNode(' ' + col.label));
                menu.appendChild(label);
            }});
        }}

        // 初始化
        document.addEventListener('DOMContentLoaded', () => {{
            renderHeader();
            renderTable(tableData);
            renderColumnMenu();

            // 搜索事件
            document.getElementById('searchInput').addEventListener('input', e => {{
                filterTable(e.target.value);
            }});

            // 列选择器切换
            const toggle = document.getElementById('columnToggle');
            const menu = document.getElementById('columnMenu');

            toggle.addEventListener('click', () => {{
                menu.classList.toggle('show');
            }});

            document.addEventListener('click', e => {{
                if (!toggle.contains(e.target) && !menu.contains(e.target)) {{
                    menu.classList.remove('show');
                }}
            }});
        }});
    </script>
</body>
</html>
'''

    # 保存文件
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return f"✅ HTML 报告已保存至: {filename}"
    except Exception as e:
        return f"❌ 保存报告失败: {str(e)}"


def generate_html_report_from_batch_results(
    batch_results: List[Any],
    title: str = "Hyperliquid 交易地址分析报告",
    filename: str = "trading_report.html"
) -> str:
    """
    从批量分析结果生成 HTML 报告

    Args:
        batch_results: BatchAddressResult 列表
        title: 报告标题
        filename: 输出文件名

    Returns:
        保存结果消息
    """
    metrics_list = []

    for result in batch_results:
        if hasattr(result, 'analysis') and result.analysis:
            # 从 AnalysisResults 提取
            metrics = AddressMetrics(
                address=result.address,
                success=result.success,
                total_trades=result.total_trades or 0,
                win_rate=result.win_rate or 0,
                sharpe_ratio=result.sharpe_ratio or 0,
                profit_factor=result.profit_factor or 0,
                total_pnl=result.total_pnl or 0,
                account_value=result.account_value or 0,
                avg_hold_time=result.avg_hold_time or 0,
                error_message=result.error_message
            )

            # 如果有完整分析数据，提取更多指标
            if result.analysis:
                raw = result.analysis.raw_results
                sharpe_data = raw.get('sharpe_on_trades', {})
                pos_data = result.analysis.position_analysis
                hold_data = result.analysis.hold_time_stats
                win_data = result.analysis.win_rate_data

                metrics.mean_return = sharpe_data.get('mean_return', 0)
                metrics.std_return = sharpe_data.get('std_return', 0)
                metrics.trades_per_year = sharpe_data.get('trades_per_year', 0)
                metrics.trading_days = raw.get('return_metrics_on_trades', {}).get('trading_days', 0)

                metrics.bias = win_data.get('bias', 50)
                metrics.total_positions = pos_data.get('total_positions', 0)
                metrics.long_positions = pos_data.get('long_positions', 0)
                metrics.short_positions = pos_data.get('short_positions', 0)
                metrics.position_bias = pos_data.get('position_bias', '中性')

                metrics.hold_time_today = hold_data.get('todayCount', 0)
                metrics.hold_time_7d = hold_data.get('last7DaysAverage', 0)
                metrics.hold_time_30d = hold_data.get('last30DaysAverage', 0)

                metrics.total_realized_pnl = raw.get('total_realized_pnl', 0)
                metrics.total_unrealized_pnl = pos_data.get('total_unrealized_pnl', 0)

                # ROE 数据
                roe_24h = raw.get('roe_24h', {})
                roe_7d = raw.get('roe_7d', {})
                roe_30d = raw.get('roe_30d', {})
                roe_all = raw.get('roe_all', {})

                metrics.roe_24h = roe_24h.get('roe_percent', 0) if roe_24h.get('is_valid') else 0
                metrics.roe_7d = roe_7d.get('roe_percent', 0) if roe_7d.get('is_valid') else 0
                metrics.roe_30d = roe_30d.get('roe_percent', 0) if roe_30d.get('is_valid') else 0
                metrics.roe_all = roe_all.get('roe_percent', 0) if roe_all.get('is_valid') else 0

                # 账户详情
                data_summary = result.analysis.data_summary
                metrics.perp_account_value = data_summary.get('perp_account_value', 0)
                metrics.spot_account_value = data_summary.get('spot_account_value', 0)
                metrics.total_margin_used = data_summary.get('total_margin_used', 0)

            metrics_list.append(metrics)
        else:
            # 简单结果
            metrics_list.append(AddressMetrics(
                address=result.address,
                success=result.success,
                total_trades=result.total_trades or 0,
                win_rate=result.win_rate or 0,
                sharpe_ratio=result.sharpe_ratio or 0,
                profit_factor=result.profit_factor or 0,
                total_pnl=result.total_pnl or 0,
                account_value=result.account_value or 0,
                avg_hold_time=result.avg_hold_time or 0,
                error_message=result.error_message
            ))

    return generate_html_report(metrics_list, title, filename)
