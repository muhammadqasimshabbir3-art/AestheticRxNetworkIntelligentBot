"""Report Builder - HTML dashboard generator for business reports.

This module generates interactive HTML dashboards with:
- KPI cards
- Chart.js charts (pie, bar, line)
- Data tables
- Dark theme styling
"""

import json
from datetime import datetime
from typing import Any

from config import CONFIG
from libraries.logger import logger


class ReportBuilder:
    """Generates HTML business report dashboards."""

    def __init__(
        self,
        executive_summary: dict[str, Any],
        user_analytics: dict[str, Any],
        order_analytics: dict[str, Any],
        payment_analytics: dict[str, Any],
        research_analytics: dict[str, Any],
        ad_analytics: dict[str, Any],
        financial_analytics: dict[str, Any],
        business_kpi_analytics: dict[str, Any] | None = None,
        # Historical analytics
        trend_analytics: dict[str, Any] | None = None,
        forecast_analytics: dict[str, Any] | None = None,
        anomaly_analytics: dict[str, Any] | None = None,
        comparison_analytics: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the report builder.

        Args:
            executive_summary: Executive summary metrics.
            user_analytics: User analytics data.
            order_analytics: Order analytics data.
            payment_analytics: Payment analytics data.
            research_analytics: Research analytics data.
            ad_analytics: Advertisement analytics data.
            financial_analytics: Financial analytics data.
            business_kpi_analytics: Business KPI tracking data (from manual sheet).
            trend_analytics: Historical trend analysis data.
            forecast_analytics: Forecast predictions data.
            anomaly_analytics: Anomaly detection data.
            comparison_analytics: Period comparison data.
        """
        self.executive_summary = executive_summary
        self.user_analytics = user_analytics
        self.order_analytics = order_analytics
        self.payment_analytics = payment_analytics
        self.research_analytics = research_analytics
        self.ad_analytics = ad_analytics
        self.financial_analytics = financial_analytics
        self.business_kpi_analytics = business_kpi_analytics or {}
        # Historical analytics
        self.trend_analytics = trend_analytics or {}
        self.forecast_analytics = forecast_analytics or {}
        self.anomaly_analytics = anomaly_analytics or {}
        self.comparison_analytics = comparison_analytics or {}

    def generate(self) -> str:
        """Generate the HTML report.

        Returns:
            Path to the generated report file.
        """
        logger.info("Generating HTML business report...")

        # Ensure output directory exists
        CONFIG.ensure_directories()

        # Generate filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"business_report_{timestamp}.html"
        filepath = CONFIG.OUTPUT_DIR / filename

        # Generate HTML content
        html_content = self._generate_html()

        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"✓ Business report generated: {filepath}")
        return str(filepath)

    def _generate_html(self) -> str:
        """Generate the full HTML content."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business Intelligence Report - {datetime.now().strftime("%Y-%m-%d")}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    {self._get_styles()}
</head>
<body>
    <div class="container">
        {self._generate_header()}
        {self._generate_executive_summary()}
        {self._generate_nav_tabs()}
        <div id="tab-users" class="tab-content active">
            {self._generate_users_section()}
        </div>
        <div id="tab-orders" class="tab-content">
            {self._generate_orders_section()}
        </div>
        <div id="tab-payments" class="tab-content">
            {self._generate_payments_section()}
        </div>
        <div id="tab-research" class="tab-content">
            {self._generate_research_section()}
        </div>
        <div id="tab-ads" class="tab-content">
            {self._generate_ads_section()}
        </div>
        <div id="tab-financial" class="tab-content">
            {self._generate_financial_section()}
        </div>
        <div id="tab-business-kpi" class="tab-content">
            {self._generate_business_kpi_section()}
        </div>
        <div id="tab-fin-tracking" class="tab-content">
            {self._generate_financial_tracking_section()}
        </div>
        <div id="tab-trends" class="tab-content">
            {self._generate_historical_trends_section()}
        </div>
        <div id="tab-forecast" class="tab-content">
            {self._generate_forecast_section()}
        </div>
        {self._generate_alerts_banner()}
        {self._generate_footer()}
    </div>
    {self._get_scripts()}
</body>
</html>"""

    def _get_styles(self) -> str:
        """Get CSS styles."""
        return """
    <style>
        :root {
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #6366f1;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #06b6d4;
            --border: #334155;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        .header {
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: linear-gradient(135deg, var(--primary) 0%, #8b5cf6 100%);
            border-radius: 16px;
        }

        .header h1 { font-size: 2rem; margin-bottom: 0.5rem; }
        .header .subtitle { color: rgba(255,255,255,0.8); }

        .executive-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .kpi-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }

        .kpi-card .icon { font-size: 2rem; margin-bottom: 0.5rem; }
        .kpi-card .value { font-size: 2rem; font-weight: 700; }
        .kpi-card .label { color: var(--text-muted); font-size: 0.875rem; }

        .kpi-card.primary .value { color: var(--primary); }
        .kpi-card.success .value { color: var(--success); }
        .kpi-card.warning .value { color: var(--warning); }
        .kpi-card.danger .value { color: var(--danger); }
        .kpi-card.info .value { color: var(--info); }

        .nav-tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 2rem;
            border-bottom: 2px solid var(--border);
            padding-bottom: 0.5rem;
            overflow-x: auto;
        }

        .nav-tab {
            padding: 0.75rem 1.5rem;
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            border-radius: 8px 8px 0 0;
            transition: all 0.2s;
            white-space: nowrap;
        }

        .nav-tab:hover { background: var(--bg-card); color: var(--text); }
        .nav-tab.active {
            background: var(--primary);
            color: white;
        }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .section {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .section-title {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; }
        .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }

        .chart-container {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.5rem;
            height: 350px;
        }

        .chart-title {
            font-size: 1rem;
            margin-bottom: 1rem;
            color: var(--text-muted);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }

        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }

        th {
            background: var(--bg-dark);
            font-weight: 600;
            color: var(--text-muted);
        }

        tr:hover td { background: var(--bg-card-hover); }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .badge-success { background: rgba(16, 185, 129, 0.2); color: var(--success); }
        .badge-warning { background: rgba(245, 158, 11, 0.2); color: var(--warning); }
        .badge-danger { background: rgba(239, 68, 68, 0.2); color: var(--danger); }
        .badge-info { background: rgba(6, 182, 212, 0.2); color: var(--info); }

        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--border);
        }

        .stat-row:last-child { border-bottom: none; }
        .stat-label { color: var(--text-muted); }
        .stat-value { font-weight: 600; }

        .footer {
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.875rem;
        }

        @media (max-width: 768px) {
            .container { padding: 1rem; }
            .grid-2, .grid-3 { grid-template-columns: 1fr; }
            .executive-summary { grid-template-columns: repeat(2, 1fr); }
        }

        /* Trend indicators */
        .trend-indicators {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            margin-top: 0.5rem;
            font-size: 0.75rem;
        }
        .trend-up { color: var(--success); }
        .trend-down { color: var(--danger); }
        .trend-flat { color: var(--warning); }

        /* Alerts banner */
        .alerts-banner {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            padding: 0.5rem 1rem;
        }
        .alert-item {
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        .alert-item.critical {
            background: rgba(239, 68, 68, 0.9);
            color: white;
        }
        .alert-item.warning {
            background: rgba(245, 158, 11, 0.9);
            color: white;
        }

        /* Risk indicators */
        .risk-indicators { margin-top: 1rem; }
        .risk-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        .risk-item.success { background: rgba(16, 185, 129, 0.1); border-left: 4px solid var(--success); }
        .risk-item.warning { background: rgba(245, 158, 11, 0.1); border-left: 4px solid var(--warning); }
        .risk-item.danger { background: rgba(239, 68, 68, 0.1); border-left: 4px solid var(--danger); }
        .risk-icon { font-size: 1.25rem; }

        /* Goal tracking */
        .goal-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }
        .goal-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.5rem;
        }
        .goal-card h4 { margin-bottom: 1rem; }
        .progress-bar {
            background: var(--border);
            border-radius: 8px;
            height: 20px;
            overflow: hidden;
            margin: 0.5rem 0;
        }
        .progress-fill {
            height: 100%;
            border-radius: 8px;
            transition: width 0.5s;
        }
        .progress-fill.badge-success { background: var(--success); }
        .progress-fill.badge-warning { background: var(--warning); }

        /* Comparison cards */
        .comparison-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }
        .comparison-summary { display: inline-block; margin-top: 0.5rem; }

        /* Rankings */
        .rankings-section { margin-top: 1rem; }

        /* Seasonal patterns */
        .seasonal-section {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.25rem;
            margin-top: 1rem;
        }

        /* Info card */
        .info-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
        }
        .info-card p { margin: 0.5rem 0; color: var(--text-muted); }
    </style>"""

    def _generate_header(self) -> str:
        """Generate header section."""
        return f"""
        <div class="header">
            <h1>📊 Business Intelligence Report</h1>
            <p class="subtitle">AestheticRxNetwork - Comprehensive Analytics Dashboard</p>
            <p class="subtitle">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>"""

    def _generate_executive_summary(self) -> str:
        """Generate executive summary KPI cards."""
        es = self.executive_summary
        completion_rate = es.get("payment_completion_rate", 0)
        return f"""
        <div class="executive-summary">
            <div class="kpi-card primary">
                <div class="icon">👥</div>
                <div class="value">{es.get('total_users', 0):,}</div>
                <div class="label">Total Users</div>
            </div>
            <div class="kpi-card success">
                <div class="icon">📦</div>
                <div class="value">{es.get('total_orders', 0):,}</div>
                <div class="label">Total Orders</div>
            </div>
            <div class="kpi-card warning">
                <div class="icon">💰</div>
                <div class="value">₨{es.get('total_paid_amount', 0):,.0f}</div>
                <div class="label">Revenue Collected</div>
            </div>
            <div class="kpi-card danger">
                <div class="icon">⏳</div>
                <div class="value">₨{es.get('total_pending_amount', 0):,.0f}</div>
                <div class="label">Pending Revenue</div>
            </div>
            <div class="kpi-card info">
                <div class="icon">✅</div>
                <div class="value">{completion_rate:.1f}%</div>
                <div class="label">Payment Rate</div>
            </div>
            <div class="kpi-card primary">
                <div class="icon">📊</div>
                <div class="value">₨{es.get('avg_order_value', 0):,.0f}</div>
                <div class="label">Avg Order Value</div>
            </div>
            <div class="kpi-card success">
                <div class="icon">📄</div>
                <div class="value">{es.get('total_papers', 0):,}</div>
                <div class="label">Research Papers</div>
            </div>
            <div class="kpi-card info">
                <div class="icon">📺</div>
                <div class="value">{es.get('active_ads', 0):,}</div>
                <div class="label">Active Ads</div>
            </div>
        </div>"""

    def _generate_nav_tabs(self) -> str:
        """Generate navigation tabs."""
        return """
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="openTab(event, 'tab-users')">👥 Users</button>
            <button class="nav-tab" onclick="openTab(event, 'tab-orders')">📦 Orders</button>
            <button class="nav-tab" onclick="openTab(event, 'tab-payments')">💳 Payments</button>
            <button class="nav-tab" onclick="openTab(event, 'tab-research')">📄 Research</button>
            <button class="nav-tab" onclick="openTab(event, 'tab-ads')">📺 Ads</button>
            <button class="nav-tab" onclick="openTab(event, 'tab-financial')">💵 System</button>
            <button class="nav-tab" onclick="openTab(event, 'tab-business-kpi')">📊 KPIs</button>
            <button class="nav-tab" onclick="openTab(event, 'tab-fin-tracking')">💹 Tracking</button>
            <button class="nav-tab" onclick="openTab(event, 'tab-trends')">📈 Trends</button>
            <button class="nav-tab" onclick="openTab(event, 'tab-forecast')">🔮 Forecast</button>
        </div>"""

    def _generate_users_section(self) -> str:
        """Generate users and doctors section."""
        ua = self.user_analytics
        tier_dist = ua.get("tier_distribution", {})
        top_doctors = ua.get("top_doctors_by_sales", [])

        # Tier chart data
        tier_labels = json.dumps(list(tier_dist.keys()) if tier_dist else ["No Data"])
        tier_data = json.dumps(list(tier_dist.values()) if tier_dist else [1])

        # Top doctors table
        doctors_rows = ""
        for doc in top_doctors[:10]:
            doctor_display = str(doc.get("doctor_name", doc.get("doctor_id", "N/A")))[:20]
            doctors_rows += f"""
                <tr>
                    <td>{doc.get('rank', 'N/A')}</td>
                    <td>{doctor_display}</td>
                    <td><span class="badge badge-info">{doc.get('tier', 'N/A')}</span></td>
                    <td>₨{doc.get('current_sales', 0):,.0f}</td>
                </tr>"""

        return f"""
        <div class="section">
            <h2 class="section-title">👥 Users & Doctors Overview</h2>
            <div class="grid-3">
                <div class="stat-row"><span class="stat-label">Total Users</span><span class="stat-value">{ua.get('total_users', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Total Doctors</span><span class="stat-value">{ua.get('total_doctors', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Active Users</span><span class="stat-value">{ua.get('active_users', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Approved</span><span class="stat-value">{ua.get('approved_users', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Pending Approval</span><span class="stat-value">{ua.get('pending_approval', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Approval Rate</span><span class="stat-value">{ua.get('approval_rate', 0):.1f}%</span></div>
                <div class="stat-row"><span class="stat-label">Admins</span><span class="stat-value">{ua.get('admin_count', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Signup IDs Used</span><span class="stat-value">{ua.get('used_signup_ids', 0):,}/{ua.get('total_signup_ids', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Signup Usage Rate</span><span class="stat-value">{ua.get('signup_usage_rate', 0):.1f}%</span></div>
            </div>
        </div>

        <div class="grid-2">
            <div class="chart-container">
                <h3 class="chart-title">Tier Distribution</h3>
                <canvas id="tierChart"></canvas>
            </div>
            <div class="section">
                <h3 class="section-title">🏆 Top Doctors by Sales</h3>
                <table>
                    <thead><tr><th>Rank</th><th>Doctor</th><th>Tier</th><th>Sales</th></tr></thead>
                    <tbody>{doctors_rows if doctors_rows else '<tr><td colspan="4">No data available</td></tr>'}</tbody>
                </table>
            </div>
        </div>

        <script>
            new Chart(document.getElementById('tierChart'), {{
                type: 'doughnut',
                data: {{
                    labels: {tier_labels},
                    datasets: [{{
                        data: {tier_data},
                        backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#8b5cf6']
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'right', labels: {{ color: '#f8fafc' }} }} }} }}
            }});
        </script>"""

    def _generate_orders_section(self) -> str:
        """Generate orders and revenue section."""
        oa = self.order_analytics
        status_dist = oa.get("order_status_distribution", {})
        payment_dist = oa.get("payment_status_distribution", {})
        top_products = oa.get("top_products", [])

        # Chart data
        status_labels = json.dumps(list(status_dist.keys()) if status_dist else ["No Data"])
        status_data = json.dumps(list(status_dist.values()) if status_dist else [1])
        payment_labels = json.dumps(list(payment_dist.keys()) if payment_dist else ["No Data"])
        payment_data = json.dumps(list(payment_dist.values()) if payment_dist else [1])

        # Products table
        products_rows = ""
        for prod in top_products[:10]:
            products_rows += f"""
                <tr>
                    <td>{str(prod.get('product_name', 'Unknown'))[:30]}</td>
                    <td>{prod.get('order_count', 0):,}</td>
                    <td>{prod.get('total_qty', 0):,}</td>
                    <td>₨{prod.get('total_revenue', 0):,.0f}</td>
                </tr>"""

        return f"""
        <div class="section">
            <h2 class="section-title">📦 Orders & Revenue Overview</h2>
            <div class="grid-3">
                <div class="stat-row"><span class="stat-label">Total Orders</span><span class="stat-value">{oa.get('total_orders', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Completed Orders</span><span class="stat-value">{oa.get('completed_orders', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Pending Orders</span><span class="stat-value">{oa.get('pending_orders', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Cancelled Orders</span><span class="stat-value">{oa.get('cancelled_orders', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Total Revenue</span><span class="stat-value">₨{oa.get('total_revenue', 0):,.0f}</span></div>
                <div class="stat-row"><span class="stat-label">Paid Revenue</span><span class="stat-value">₨{oa.get('paid_revenue', 0):,.0f}</span></div>
                <div class="stat-row"><span class="stat-label">Pending Revenue</span><span class="stat-value">₨{oa.get('pending_revenue', 0):,.0f}</span></div>
                <div class="stat-row"><span class="stat-label">Avg Order Value</span><span class="stat-value">₨{oa.get('average_order_value', 0):,.0f}</span></div>
                <div class="stat-row"><span class="stat-label">Total Products</span><span class="stat-value">{oa.get('total_products', 0):,}</span></div>
            </div>
        </div>

        <div class="grid-2">
            <div class="chart-container">
                <h3 class="chart-title">Order Status Distribution</h3>
                <canvas id="orderStatusChart"></canvas>
            </div>
            <div class="chart-container">
                <h3 class="chart-title">Payment Status Distribution</h3>
                <canvas id="paymentStatusChart"></canvas>
            </div>
        </div>

        <div class="section">
            <h3 class="section-title">🏆 Top Products by Revenue</h3>
            <table>
                <thead><tr><th>Product</th><th>Orders</th><th>Qty</th><th>Revenue</th></tr></thead>
                <tbody>{products_rows if products_rows else '<tr><td colspan="4">No data available</td></tr>'}</tbody>
            </table>
        </div>

        <script>
            new Chart(document.getElementById('orderStatusChart'), {{
                type: 'pie',
                data: {{
                    labels: {status_labels},
                    datasets: [{{ data: {status_data}, backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#6366f1'] }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'right', labels: {{ color: '#f8fafc' }} }} }} }}
            }});

            new Chart(document.getElementById('paymentStatusChart'), {{
                type: 'pie',
                data: {{
                    labels: {payment_labels},
                    datasets: [{{ data: {payment_data}, backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#06b6d4'] }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'right', labels: {{ color: '#f8fafc' }} }} }} }}
            }});
        </script>"""

    def _generate_payments_section(self) -> str:
        """Generate payments and revenue section."""
        pa = self.payment_analytics
        payment_status = pa.get("payment_status_breakdown", {})
        payment_methods = pa.get("payment_method_breakdown", {})
        revenue_by_method = pa.get("revenue_by_method", {})
        top_doctors = pa.get("top_paying_doctors", [])
        recent_payments = pa.get("recent_payments", [])
        daily_revenue = pa.get("daily_revenue", [])
        trends = pa.get("payment_trends", {})

        # Chart data
        status_labels = json.dumps(list(payment_status.keys()) if payment_status else ["No Data"])
        status_data = json.dumps(list(payment_status.values()) if payment_status else [1])
        method_labels = json.dumps(list(payment_methods.keys()) if payment_methods else ["No Data"])
        method_data = json.dumps(list(payment_methods.values()) if payment_methods else [1])
        revenue_labels = json.dumps(list(revenue_by_method.keys()) if revenue_by_method else ["No Data"])
        revenue_data = json.dumps(list(revenue_by_method.values()) if revenue_by_method else [1])

        # Daily revenue chart data
        daily_labels = json.dumps([d.get("date", "") for d in daily_revenue[:14]])
        daily_data = json.dumps([d.get("revenue", 0) for d in daily_revenue[:14]])

        # Trend indicator
        trend_dir = trends.get("trend_direction", "stable")
        trend_pct = trends.get("trend_percentage", 0)
        trend_class = "badge-success" if trend_dir == "up" else "badge-danger" if trend_dir == "down" else "badge-info"
        trend_icon = "📈" if trend_dir == "up" else "📉" if trend_dir == "down" else "➡️"

        # Top doctors table
        doctors_rows = ""
        for doc in top_doctors[:10]:
            doctor_display = str(doc.get("doctor_name", doc.get("doctor_id", "N/A")))[:20]
            clinic_display = str(doc.get("clinic_name", "N/A"))[:20]
            doctors_rows += f"""
                <tr>
                    <td>{doctor_display}</td>
                    <td>{clinic_display}</td>
                    <td><span class="badge badge-info">{doc.get('tier', 'N/A')}</span></td>
                    <td>{doc.get('order_count', 0):,}</td>
                    <td>₨{doc.get('total_paid', 0):,.0f}</td>
                </tr>"""

        # Recent payments table
        payments_rows = ""
        for pay in recent_payments[:10]:
            payments_rows += f"""
                <tr>
                    <td>{pay.get('order_number', 'N/A')}</td>
                    <td>₨{pay.get('amount', 0):,.0f}</td>
                    <td><span class="badge badge-success">{pay.get('method', 'N/A')}</span></td>
                    <td>{pay.get('completed_at', 'N/A')}</td>
                </tr>"""

        return f"""
        <div class="section">
            <h2 class="section-title">💳 Payment & Revenue Analytics</h2>
            <div class="grid-3">
                <div class="stat-row">
                    <span class="stat-label">Total Revenue (All Orders)</span>
                    <span class="stat-value">₨{pa.get('total_revenue', 0):,.0f}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Total Paid Amount</span>
                    <span class="stat-value" style="color: var(--success);">₨{pa.get('total_paid_amount', 0):,.0f}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Pending Revenue</span>
                    <span class="stat-value" style="color: var(--warning);">₨{pa.get('total_pending_amount', 0):,.0f}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Payment Completion Rate</span>
                    <span class="stat-value">{pa.get('payment_completion_rate', 0):.1f}%</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Average Order Value</span>
                    <span class="stat-value">₨{pa.get('avg_order_value', 0):,.0f}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">7-Day Revenue</span>
                    <span class="stat-value">₨{trends.get('last_7_days_revenue', 0):,.0f}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Previous 7-Day Revenue</span>
                    <span class="stat-value">₨{trends.get('prev_7_days_revenue', 0):,.0f}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Revenue Trend</span>
                    <span class="stat-value">
                        <span class="badge {trend_class}">{trend_icon} {trend_pct:+.1f}%</span>
                    </span>
                </div>
            </div>
        </div>

        <div class="grid-2">
            <div class="chart-container">
                <h3 class="chart-title">Payment Status Distribution</h3>
                <canvas id="paymentStatusPieChart"></canvas>
            </div>
            <div class="chart-container">
                <h3 class="chart-title">Payment Methods Used</h3>
                <canvas id="paymentMethodChart"></canvas>
            </div>
        </div>

        <div class="grid-2">
            <div class="chart-container" style="height: 400px;">
                <h3 class="chart-title">Revenue by Payment Method</h3>
                <canvas id="revenueByMethodChart"></canvas>
            </div>
            <div class="chart-container" style="height: 400px;">
                <h3 class="chart-title">Daily Revenue (Last 14 Days)</h3>
                <canvas id="dailyRevenueChart"></canvas>
            </div>
        </div>

        <div class="grid-2">
            <div class="section">
                <h3 class="section-title">🏆 Top Paying Doctors</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Doctor</th>
                            <th>Clinic</th>
                            <th>Tier</th>
                            <th>Orders</th>
                            <th>Total Paid</th>
                        </tr>
                    </thead>
                    <tbody>
                        {doctors_rows if doctors_rows else '<tr><td colspan="5">No data available</td></tr>'}
                    </tbody>
                </table>
            </div>
            <div class="section">
                <h3 class="section-title">⏱ Recent Payments</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Order #</th>
                            <th>Amount</th>
                            <th>Method</th>
                            <th>Completed</th>
                        </tr>
                    </thead>
                    <tbody>
                        {payments_rows if payments_rows else '<tr><td colspan="4">No data available</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>

        <script>
            // Payment Status Pie Chart
            new Chart(document.getElementById('paymentStatusPieChart'), {{
                type: 'doughnut',
                data: {{
                    labels: {status_labels},
                    datasets: [{{
                        data: {status_data},
                        backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#6366f1', '#06b6d4']
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ position: 'right', labels: {{ color: '#f8fafc' }} }} }}
                }}
            }});

            // Payment Methods Chart
            new Chart(document.getElementById('paymentMethodChart'), {{
                type: 'doughnut',
                data: {{
                    labels: {method_labels},
                    datasets: [{{
                        data: {method_data},
                        backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ position: 'right', labels: {{ color: '#f8fafc' }} }} }}
                }}
            }});

            // Revenue by Method Bar Chart
            new Chart(document.getElementById('revenueByMethodChart'), {{
                type: 'bar',
                data: {{
                    labels: {revenue_labels},
                    datasets: [{{
                        label: 'Revenue (₨)',
                        data: {revenue_data},
                        backgroundColor: '#6366f1',
                        borderRadius: 8
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        y: {{
                            ticks: {{ color: '#94a3b8', callback: function(value) {{ return '₨' + value.toLocaleString(); }} }},
                            grid: {{ color: '#334155' }}
                        }},
                        x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }}
                    }}
                }}
            }});

            // Daily Revenue Line Chart
            new Chart(document.getElementById('dailyRevenueChart'), {{
                type: 'line',
                data: {{
                    labels: {daily_labels},
                    datasets: [{{
                        label: 'Daily Revenue (₨)',
                        data: {daily_data},
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#10b981',
                        pointRadius: 4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        y: {{
                            ticks: {{ color: '#94a3b8', callback: function(value) {{ return '₨' + value.toLocaleString(); }} }},
                            grid: {{ color: '#334155' }}
                        }},
                        x: {{ ticks: {{ color: '#94a3b8', maxRotation: 45 }}, grid: {{ display: false }} }}
                    }}
                }}
            }});
        </script>"""

    def _generate_research_section(self) -> str:
        """Generate research section."""
        ra = self.research_analytics
        top_papers = ra.get("top_papers_by_views", [])
        top_performers = ra.get("top_performers", [])

        # Papers table
        papers_rows = ""
        for paper in top_papers[:10]:
            papers_rows += f"""
                <tr>
                    <td>{paper.get('title', 'Untitled')}</td>
                    <td>{paper.get('view_count', 0):,}</td>
                    <td>{paper.get('upvote_count', 0):,}</td>
                </tr>"""

        # Performers table
        performers_rows = ""
        for perf in top_performers[:10]:
            performers_rows += f"""
                <tr>
                    <td>{perf.get('rank', 'N/A')}</td>
                    <td>{str(perf.get('doctor_id', 'N/A'))[:20]}</td>
                    <td><span class="badge badge-success">{perf.get('tier', 'N/A')}</span></td>
                    <td>₨{perf.get('current_sales', 0):,.0f}</td>
                </tr>"""

        return f"""
        <div class="section">
            <h2 class="section-title">📄 Research & Engagement Overview</h2>
            <div class="grid-3">
                <div class="stat-row"><span class="stat-label">Total Papers</span><span class="stat-value">{ra.get('total_papers', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Approved Papers</span><span class="stat-value">{ra.get('approved_papers', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Pending Papers</span><span class="stat-value">{ra.get('pending_papers', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Total Views</span><span class="stat-value">{ra.get('total_views', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Total Upvotes</span><span class="stat-value">{ra.get('total_upvotes', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Unique Viewers</span><span class="stat-value">{ra.get('unique_viewers', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Avg Views/Paper</span><span class="stat-value">{ra.get('average_views_per_paper', 0):.1f}</span></div>
                <div class="stat-row"><span class="stat-label">Engagement Rate</span><span class="stat-value">{ra.get('engagement_rate', 0):.1f}%</span></div>
                <div class="stat-row"><span class="stat-label">Certificates</span><span class="stat-value">{ra.get('total_certificates', 0):,}</span></div>
            </div>
        </div>

        <div class="grid-2">
            <div class="section">
                <h3 class="section-title">📄 Top Papers by Views</h3>
                <table>
                    <thead><tr><th>Title</th><th>Views</th><th>Upvotes</th></tr></thead>
                    <tbody>{papers_rows if papers_rows else '<tr><td colspan="3">No data available</td></tr>'}</tbody>
                </table>
            </div>
            <div class="section">
                <h3 class="section-title">🏆 Leaderboard Top Performers</h3>
                <table>
                    <thead><tr><th>Rank</th><th>Doctor</th><th>Tier</th><th>Sales</th></tr></thead>
                    <tbody>{performers_rows if performers_rows else '<tr><td colspan="4">No data available</td></tr>'}</tbody>
                </table>
            </div>
        </div>"""

    def _generate_ads_section(self) -> str:
        """Generate advertisements section."""
        aa = self.ad_analytics
        status_dist = aa.get("status_distribution", {})
        type_dist = aa.get("type_distribution", {})
        top_ads = aa.get("top_ads_by_views", [])

        # Chart data
        status_labels = json.dumps(list(status_dist.keys()) if status_dist else ["No Data"])
        status_data = json.dumps(list(status_dist.values()) if status_dist else [1])
        type_labels = json.dumps(list(type_dist.keys()) if type_dist else ["No Data"])
        type_data = json.dumps(list(type_dist.values()) if type_dist else [1])

        # Ads table
        ads_rows = ""
        for ad in top_ads[:10]:
            status_class = "badge-success" if ad.get("status") == "active" else "badge-warning"
            ads_rows += f"""
                <tr>
                    <td>{ad.get('title', 'Untitled')}</td>
                    <td>{ad.get('type', 'N/A')}</td>
                    <td><span class="badge {status_class}">{ad.get('status', 'N/A')}</span></td>
                    <td>{ad.get('views', 0):,}</td>
                    <td>{ad.get('clicks', 0):,}</td>
                </tr>"""

        return f"""
        <div class="section">
            <h2 class="section-title">📺 Advertisement Overview</h2>
            <div class="grid-3">
                <div class="stat-row"><span class="stat-label">Total Ads</span><span class="stat-value">{aa.get('total_ads', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Active Ads</span><span class="stat-value">{aa.get('active_ads', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Pending Ads</span><span class="stat-value">{aa.get('pending_ads', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Completed Ads</span><span class="stat-value">{aa.get('completed_ads', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Video Ads</span><span class="stat-value">{aa.get('video_ads', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Banner Ads</span><span class="stat-value">{aa.get('banner_ads', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Total Revenue</span><span class="stat-value">₨{aa.get('total_ad_revenue', 0):,.0f}</span></div>
                <div class="stat-row"><span class="stat-label">Paid Revenue</span><span class="stat-value">₨{aa.get('paid_ad_revenue', 0):,.0f}</span></div>
                <div class="stat-row"><span class="stat-label">Total Impressions</span><span class="stat-value">{aa.get('total_impressions', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Total Clicks</span><span class="stat-value">{aa.get('total_clicks', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Total Views</span><span class="stat-value">{aa.get('total_views', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">CTR</span><span class="stat-value">{aa.get('click_through_rate', 0):.2f}%</span></div>
            </div>
        </div>

        <div class="grid-2">
            <div class="chart-container">
                <h3 class="chart-title">Ad Status Distribution</h3>
                <canvas id="adStatusChart"></canvas>
            </div>
            <div class="chart-container">
                <h3 class="chart-title">Ad Type Distribution</h3>
                <canvas id="adTypeChart"></canvas>
            </div>
        </div>

        <div class="section">
            <h3 class="section-title">🏆 Top Ads by Views</h3>
            <table>
                <thead><tr><th>Title</th><th>Type</th><th>Status</th><th>Views</th><th>Clicks</th></tr></thead>
                <tbody>{ads_rows if ads_rows else '<tr><td colspan="5">No data available</td></tr>'}</tbody>
            </table>
        </div>

        <script>
            new Chart(document.getElementById('adStatusChart'), {{
                type: 'doughnut',
                data: {{
                    labels: {status_labels},
                    datasets: [{{ data: {status_data}, backgroundColor: ['#10b981', '#f59e0b', '#6366f1', '#ef4444'] }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'right', labels: {{ color: '#f8fafc' }} }} }} }}
            }});

            new Chart(document.getElementById('adTypeChart'), {{
                type: 'doughnut',
                data: {{
                    labels: {type_labels},
                    datasets: [{{ data: {type_data}, backgroundColor: ['#6366f1', '#10b981', '#f59e0b'] }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'right', labels: {{ color: '#f8fafc' }} }} }} }}
            }});
        </script>"""

    def _generate_financial_section(self) -> str:
        """Generate financial section."""
        fa = self.financial_analytics
        return f"""
        <div class="section">
            <h2 class="section-title">💰 Financial & System Overview</h2>
            <div class="grid-3">
                <div class="stat-row"><span class="stat-label">Total Wallets</span><span class="stat-value">{fa.get('total_wallets', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Total Wallet Balance</span><span class="stat-value">₨{fa.get('total_wallet_balance', 0):,.0f}</span></div>
                <div class="stat-row"><span class="stat-label">Avg Wallet Balance</span><span class="stat-value">₨{fa.get('average_wallet_balance', 0):,.0f}</span></div>
                <div class="stat-row"><span class="stat-label">Debt Records</span><span class="stat-value">{fa.get('total_debt_records', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Total Debt</span><span class="stat-value">₨{fa.get('total_debt_amount', 0):,.0f}</span></div>
                <div class="stat-row"><span class="stat-label">Notifications</span><span class="stat-value">{fa.get('total_notifications', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Emails Sent</span><span class="stat-value">{fa.get('total_emails_sent', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">OTP Codes</span><span class="stat-value">{fa.get('total_otp_codes', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Teams</span><span class="stat-value">{fa.get('total_teams', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Team Members</span><span class="stat-value">{fa.get('total_team_members', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">Badges</span><span class="stat-value">{fa.get('total_badges', 0):,}</span></div>
                <div class="stat-row"><span class="stat-label">AI Models</span><span class="stat-value">{fa.get('ai_models_count', 0):,}</span></div>
            </div>
        </div>"""

    def _generate_business_kpi_section(self) -> str:
        """Generate Business KPI section with comprehensive metrics and trajectory charts."""
        bk = self.business_kpi_analytics

        # Check if we have data
        if not bk or not bk.get("has_data", False):
            return """
        <div class="section">
            <h2 class="section-title">📊 Business KPIs & Trajectories</h2>
            <div style="text-align: center; padding: 3rem; color: var(--text-muted);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📋</div>
                <h3>No Data Available</h3>
                <p>Run the Data Analysis Process first to download order data.</p>
            </div>
        </div>"""

        # Get data from the updated analyzer
        growth = bk.get("growth", {})
        monthly_trends = bk.get("monthly_trends", [])
        weekly_trends = bk.get("weekly_trends", [])
        top_products = bk.get("top_products", [])
        product_categories = bk.get("product_categories", {})
        payment_methods = bk.get("payment_methods", {})
        bk.get("order_status_distribution", {})
        bk.get("payment_status_distribution", {})

        # Growth metrics from new structure
        sales_growth = (
            growth.sales_growth_percent
            if hasattr(growth, "sales_growth_percent")
            else growth.get("sales_growth_percent", 0)
        )
        order_growth = (
            growth.order_growth_percent
            if hasattr(growth, "order_growth_percent")
            else growth.get("order_growth_percent", 0)
        )
        growth.profit_growth_percent if hasattr(growth, "profit_growth_percent") else growth.get(
            "profit_growth_percent", 0
        )

        # Growth indicators
        sales_growth_class = (
            "badge-success" if sales_growth > 0 else "badge-danger" if sales_growth < 0 else "badge-info"
        )
        sales_growth_icon = "📈" if sales_growth > 0 else "📉" if sales_growth < 0 else "➡️"

        # Monthly trend chart data
        monthly_labels = json.dumps([f"{t.get('month', '')} {t.get('year', '')}" for t in monthly_trends[-12:]])
        monthly_sales = json.dumps([t.get("total_sales", 0) for t in monthly_trends[-12:]])
        monthly_orders = json.dumps([t.get("total_orders", 0) for t in monthly_trends[-12:]])
        monthly_paid = json.dumps([t.get("paid_amount", 0) for t in monthly_trends[-12:]])
        json.dumps([t.get("avg_order_value", 0) for t in monthly_trends[-12:]])

        # Weekly trend chart data
        weekly_labels = json.dumps([t.get("week_start", "") for t in weekly_trends[-12:]])
        weekly_sales = json.dumps([t.get("total_sales", 0) for t in weekly_trends[-12:]])
        json.dumps([t.get("total_orders", 0) for t in weekly_trends[-12:]])

        # Product categories chart
        cat_labels = json.dumps(list(product_categories.keys()) if product_categories else ["No Data"])
        cat_data = json.dumps(list(product_categories.values()) if product_categories else [1])

        # Payment methods chart
        method_labels = json.dumps(list(payment_methods.keys()) if payment_methods else ["No Data"])
        method_revenue = json.dumps(
            [v.get("revenue", 0) if isinstance(v, dict) else v for v in payment_methods.values()]
            if payment_methods
            else [1]
        )

        # Product trajectories (per-product sales over time)
        product_trajectories = bk.get("product_trajectories", [])
        trajectory_labels = bk.get("trajectory_labels", [])

        # Prepare product trajectory chart data
        product_traj_labels = json.dumps(trajectory_labels if trajectory_labels else ["No Data"])
        product_traj_datasets = []
        colors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
        for i, traj in enumerate(product_trajectories[:5]):
            color = colors[i % len(colors)]
            product_traj_datasets.append(
                {
                    "label": str(traj.get("product_name", f"Product {i+1}"))[:25],
                    "data": traj.get("sales", []),
                    "borderColor": color,
                    "backgroundColor": f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)",
                    "fill": False,
                    "tension": 0.4,
                    "borderWidth": 2,
                }
            )
        product_traj_datasets_json = json.dumps(
            product_traj_datasets if product_traj_datasets else [{"label": "No Data", "data": [0]}]
        )

        # Top products table
        products_rows = ""
        for prod in top_products[:10]:
            products_rows += f"""
                <tr>
                    <td>{str(prod.get('name', 'Unknown'))[:30]}</td>
                    <td>₨{prod.get('revenue', 0):,.0f}</td>
                    <td>{prod.get('qty', 0):,}</td>
                    <td>{prod.get('orders', 0):,}</td>
                </tr>"""

        # Trajectory indicator
        trajectory = bk.get("growth_trajectory", "stable")
        traj_class = (
            "badge-success" if "growth" in trajectory else "badge-danger" if "decline" in trajectory else "badge-info"
        )
        traj_icon = (
            "🚀"
            if trajectory == "strong_growth"
            else "📈"
            if "growth" in trajectory
            else "📉"
            if "decline" in trajectory
            else "➡️"
        )

        # Calculate pending percentage
        total_rev = bk.get("total_revenue", 0)
        total_pending = bk.get("total_pending", 0)
        pending_percent = (total_pending / total_rev * 100) if total_rev > 0 else 0

        return f"""
        <style>
            .kpi-tooltip {{
                position: relative;
                cursor: help;
            }}
            .kpi-tooltip .tooltip-text {{
                visibility: hidden;
                width: 250px;
                background-color: #1e293b;
                color: #f1f5f9;
                text-align: left;
                border-radius: 8px;
                padding: 12px;
                position: absolute;
                z-index: 100;
                bottom: 125%;
                left: 50%;
                margin-left: -125px;
                opacity: 0;
                transition: opacity 0.3s;
                font-size: 0.85rem;
                line-height: 1.4;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4);
                border: 1px solid #334155;
            }}
            .kpi-tooltip .tooltip-text::after {{
                content: "";
                position: absolute;
                top: 100%;
                left: 50%;
                margin-left: -8px;
                border-width: 8px;
                border-style: solid;
                border-color: #1e293b transparent transparent transparent;
            }}
            .kpi-tooltip:hover .tooltip-text {{
                visibility: visible;
                opacity: 1;
            }}
            .kpi-description {{
                font-size: 0.75rem;
                color: var(--text-muted);
                margin-top: 4px;
                line-height: 1.3;
            }}
            .pending-alert {{
                background: linear-gradient(135deg, #f59e0b22 0%, #ef444422 100%);
                border: 1px solid #f59e0b;
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1.5rem 0;
            }}
            .pending-alert h4 {{
                color: #f59e0b;
                margin: 0 0 0.5rem 0;
                font-size: 1.1rem;
            }}
            .pending-bar {{
                background: #334155;
                border-radius: 8px;
                height: 24px;
                overflow: hidden;
                margin: 0.75rem 0;
            }}
            .pending-bar-fill {{
                height: 100%;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 0.8rem;
                transition: width 0.5s ease;
            }}
            .pending-bar-collected {{
                background: linear-gradient(90deg, #10b981 0%, #059669 100%);
            }}
            .pending-bar-pending {{
                background: linear-gradient(90deg, #f59e0b 0%, #ef4444 100%);
            }}
        </style>

        <div class="section">
            <h2 class="section-title">📊 Business KPIs & Trajectories</h2>
            <p style="color: var(--text-muted); margin-bottom: 0.5rem;">
                <strong>What is this?</strong> Key Performance Indicators (KPIs) show how well your business is performing.
                These numbers help you understand sales, payments, and growth at a glance.
            </p>
            <p style="color: var(--text-muted); margin-bottom: 1rem; font-size: 0.9rem;">
                📊 Data Source: {bk.get('data_source', 'Downloaded Export')} |
                📦 Orders Analyzed: {bk.get('records_count', 0):,} |
                🎯 Trajectory: <span class="badge {traj_class}">{traj_icon} {trajectory.replace('_', ' ').title()}</span>
            </p>

            <!-- Payment Status Alert -->
            <div class="pending-alert">
                <h4>💰 Payment Collection Status</h4>
                <p style="margin: 0; color: #94a3b8;">
                    Shows how much money has been collected vs. still pending from customers.
                </p>
                <div class="pending-bar">
                    <div class="pending-bar-fill pending-bar-collected" style="width: {bk.get('collection_efficiency_percent', 0):.1f}%;">
                        ✓ Collected: ₨{bk.get('total_paid', 0):,.0f}
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.9rem; color: #94a3b8;">
                    <span>💵 <strong style="color: #10b981;">Collected:</strong> ₨{bk.get('total_paid', 0):,.0f} ({bk.get('collection_efficiency_percent', 0):.1f}%)</span>
                    <span>⏳ <strong style="color: #f59e0b;">Pending:</strong> ₨{total_pending:,.0f} ({pending_percent:.1f}%)</span>
                    <span>💰 <strong>Total:</strong> ₨{total_rev:,.0f}</span>
                </div>
            </div>

            <!-- Executive KPI Cards with Tooltips -->
            <div class="executive-summary" style="margin-bottom: 2rem;">
                <div class="kpi-card success kpi-tooltip">
                    <span class="tooltip-text">
                        <strong>Total Revenue</strong><br>
                        The total value of all orders placed. This is the gross income before any deductions or expenses.
                    </span>
                    <div class="icon">💰</div>
                    <div class="value">₨{bk.get('total_revenue', 0):,.0f}</div>
                    <div class="label">Total Revenue</div>
                    <div class="kpi-description">All orders value</div>
                </div>
                <div class="kpi-card primary kpi-tooltip">
                    <span class="tooltip-text">
                        <strong>Total Collected</strong><br>
                        Money actually received from customers. This is the cash in hand that has been paid.
                    </span>
                    <div class="icon">💵</div>
                    <div class="value">₨{bk.get('total_paid', 0):,.0f}</div>
                    <div class="label">Total Collected</div>
                    <div class="kpi-description">Payments received</div>
                </div>
                <div class="kpi-card warning kpi-tooltip">
                    <span class="tooltip-text">
                        <strong>Pending Amount</strong><br>
                        Money customers still owe. This needs to be collected. Lower is better!
                    </span>
                    <div class="icon">⏳</div>
                    <div class="value">₨{total_pending:,.0f}</div>
                    <div class="label">Pending Amount</div>
                    <div class="kpi-description">{pending_percent:.1f}% of total</div>
                </div>
                <div class="kpi-card info kpi-tooltip">
                    <span class="tooltip-text">
                        <strong>Collection Rate</strong><br>
                        Percentage of revenue actually collected. 100% means all payments received. Higher is better!
                    </span>
                    <div class="icon">📈</div>
                    <div class="value">{bk.get('collection_efficiency_percent', 0):.1f}%</div>
                    <div class="label">Collection Rate</div>
                    <div class="kpi-description">% payments received</div>
                </div>
                <div class="kpi-card success kpi-tooltip">
                    <span class="tooltip-text">
                        <strong>Profit Margin</strong><br>
                        Estimated percentage of revenue that becomes profit after costs. Higher means more profitable!
                    </span>
                    <div class="icon">📊</div>
                    <div class="value">{bk.get('profit_margin_percent', 0):.1f}%</div>
                    <div class="label">Est. Profit Margin</div>
                    <div class="kpi-description">Profit per sale</div>
                </div>
                <div class="kpi-card primary kpi-tooltip">
                    <span class="tooltip-text">
                        <strong>Average Order Value</strong><br>
                        Average amount spent per order. Higher value means customers buy more per purchase.
                    </span>
                    <div class="icon">🛒</div>
                    <div class="value">₨{bk.get('avg_order_value', 0):,.0f}</div>
                    <div class="label">Avg Order Value</div>
                    <div class="kpi-description">Per order average</div>
                </div>
            </div>
        </div>

        <!-- Growth & Projections -->
        <div class="section">
            <h3 class="section-title">🚀 Growth Metrics & Projections</h3>
            <p style="color: var(--text-muted); margin-bottom: 1rem; font-size: 0.9rem;">
                <strong>What is this?</strong> These metrics show how your business is growing compared to last month,
                and predict future revenue based on current trends.
            </p>
            <div class="grid-3">
                <div class="stat-row kpi-tooltip" style="position: relative;">
                    <span class="tooltip-text" style="bottom: 100%; left: 0; margin-left: 0;">
                        <strong>Sales Growth (MoM)</strong><br>
                        How much sales increased/decreased compared to last month. Positive = growth, Negative = decline.
                    </span>
                    <span class="stat-label">📈 Sales Growth (MoM)</span>
                    <span class="stat-value"><span class="badge {sales_growth_class}">{sales_growth_icon} {sales_growth:+.1f}%</span></span>
                </div>
                <div class="stat-row kpi-tooltip" style="position: relative;">
                    <span class="tooltip-text" style="bottom: 100%; left: 0; margin-left: 0;">
                        <strong>Order Growth (MoM)</strong><br>
                        Change in number of orders from last month. More orders = more customers buying.
                    </span>
                    <span class="stat-label">📦 Order Growth (MoM)</span>
                    <span class="stat-value">{order_growth:+.1f}%</span>
                </div>
                <div class="stat-row kpi-tooltip" style="position: relative;">
                    <span class="tooltip-text" style="bottom: 100%; left: 0; margin-left: 0;">
                        <strong>Avg Monthly Growth Rate</strong><br>
                        Average growth rate over all months. Shows overall business trajectory.
                    </span>
                    <span class="stat-label">📊 Avg Monthly Growth</span>
                    <span class="stat-value">{bk.get('avg_monthly_growth_rate', 0):.1f}%</span>
                </div>
                <div class="stat-row kpi-tooltip" style="position: relative;">
                    <span class="tooltip-text" style="bottom: 100%; left: 0; margin-left: 0;">
                        <strong>Projected Monthly Revenue</strong><br>
                        Estimated revenue for next month based on current growth trends.
                    </span>
                    <span class="stat-label">🎯 Projected Monthly</span>
                    <span class="stat-value" style="color: var(--primary);">₨{bk.get('projected_monthly_revenue', 0):,.0f}</span>
                </div>
                <div class="stat-row kpi-tooltip" style="position: relative;">
                    <span class="tooltip-text" style="bottom: 100%; left: 0; margin-left: 0;">
                        <strong>Projected Quarterly Revenue</strong><br>
                        Estimated revenue for next 3 months combined.
                    </span>
                    <span class="stat-label">📅 Projected Quarterly</span>
                    <span class="stat-value" style="color: var(--primary);">₨{bk.get('projected_quarterly_revenue', 0):,.0f}</span>
                </div>
                <div class="stat-row kpi-tooltip" style="position: relative;">
                    <span class="tooltip-text" style="bottom: 100%; left: 0; margin-left: 0;">
                        <strong>Projected Annual Revenue</strong><br>
                        Estimated total revenue for the full year at current growth rate.
                    </span>
                    <span class="stat-label">📆 Projected Annual</span>
                    <span class="stat-value" style="color: var(--success);">₨{bk.get('projected_annual_revenue', 0):,.0f}</span>
                </div>
            </div>
        </div>

        <!-- Monthly Revenue Trajectory Chart -->
        <div class="chart-container" style="height: 400px; margin-bottom: 1.5rem;">
            <h3 class="chart-title">📈 Monthly Revenue Trajectory</h3>
            <p style="color: var(--text-muted); font-size: 0.85rem; margin: -0.5rem 0 1rem 0;">
                Shows monthly sales (blue) vs actual payments collected (green). The gap between lines indicates pending payments.
            </p>
            <canvas id="monthlyRevenueTrajectory"></canvas>
        </div>

        <div class="grid-2">
            <!-- Monthly Orders Trend -->
            <div class="chart-container" style="height: 350px;">
                <h3 class="chart-title">📦 Monthly Orders Trend</h3>
                <p style="color: var(--text-muted); font-size: 0.8rem; margin: -0.5rem 0 0.5rem 0;">
                    Number of orders placed each month. Higher bars = more customer orders.
                </p>
                <canvas id="monthlyOrdersTrend"></canvas>
            </div>
            <!-- Weekly Revenue Trend -->
            <div class="chart-container" style="height: 350px;">
                <h3 class="chart-title">📊 Weekly Revenue (Last 12 Weeks)</h3>
                <p style="color: var(--text-muted); font-size: 0.8rem; margin: -0.5rem 0 0.5rem 0;">
                    Recent weekly performance. Helps identify short-term trends and patterns.
                </p>
                <canvas id="weeklyRevenueTrend"></canvas>
            </div>
        </div>

        <div class="grid-2">
            <!-- Product Categories -->
            <div class="chart-container" style="height: 350px;">
                <h3 class="chart-title">🏷️ Revenue by Product Category</h3>
                <p style="color: var(--text-muted); font-size: 0.8rem; margin: -0.5rem 0 0.5rem 0;">
                    Which product types generate the most revenue.
                </p>
                <canvas id="productCategoriesChart"></canvas>
            </div>
            <!-- Payment Methods -->
            <div class="chart-container" style="height: 350px;">
                <h3 class="chart-title">💳 Revenue by Payment Method</h3>
                <p style="color: var(--text-muted); font-size: 0.8rem; margin: -0.5rem 0 0.5rem 0;">
                    How customers prefer to pay for their orders.
                </p>
                <canvas id="paymentMethodsChart"></canvas>
            </div>
        </div>

        <!-- Product Trajectory Chart -->
        <div class="chart-container" style="height: 400px; margin-top: 1.5rem; margin-bottom: 1.5rem;">
            <h3 class="chart-title">📊 Top Products - Sales Trajectory Over Time</h3>
            <p style="color: var(--text-muted); font-size: 0.85rem; margin: -0.5rem 0 1rem 0;">
                Track how your top 5 products perform month-by-month. Rising lines indicate growing product demand.
            </p>
            <canvas id="productTrajectoryChart"></canvas>
        </div>

        <!-- Top Products Table -->
        <div class="section" style="margin-top: 1.5rem;">
            <h3 class="section-title">🏆 Top Products by Revenue</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1rem;">
                Your best-selling products ranked by total revenue generated. Focus on these products for maximum impact.
            </p>
            <table>
                <thead>
                    <tr><th>Product</th><th>Revenue</th><th>Qty Sold</th><th>Orders</th></tr>
                </thead>
                <tbody>
                    {products_rows if products_rows else '<tr><td colspan="4">No product data</td></tr>'}
                </tbody>
            </table>
        </div>

        <!-- Cost & Efficiency Estimates -->
        <div class="section" style="margin-top: 1.5rem;">
            <h3 class="section-title">💼 Estimated Costs & Efficiency</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1rem;">
                <strong>Note:</strong> These are estimated values based on industry standard percentages.
                Actual costs may vary. COGS = Cost of Goods Sold (product cost).
            </p>
            <div class="grid-3">
                <div class="stat-row kpi-tooltip" style="position: relative;">
                    <span class="tooltip-text" style="bottom: 100%; left: 0; margin-left: 0;">
                        <strong>Cost of Goods Sold (COGS)</strong><br>
                        The direct cost of products sold. Estimated at 50% of revenue. This is what you pay for the products.
                    </span>
                    <span class="stat-label">📦 Est. Cost of Goods (50%)</span>
                    <span class="stat-value" style="color: var(--danger);">₨{bk.get('estimated_cogs', 0):,.0f}</span>
                </div>
                <div class="stat-row kpi-tooltip" style="position: relative;">
                    <span class="tooltip-text" style="bottom: 100%; left: 0; margin-left: 0;">
                        <strong>Operating Expenses</strong><br>
                        Day-to-day business costs like rent, salaries, utilities. Estimated at 20% of revenue.
                    </span>
                    <span class="stat-label">🏢 Est. Operating Expenses (20%)</span>
                    <span class="stat-value" style="color: var(--warning);">₨{bk.get('estimated_expenses', 0):,.0f}</span>
                </div>
                <div class="stat-row kpi-tooltip" style="position: relative;">
                    <span class="tooltip-text" style="bottom: 100%; left: 0; margin-left: 0;">
                        <strong>Net Profit</strong><br>
                        Money left after all costs. This is what the business actually earns. Higher = better!
                    </span>
                    <span class="stat-label">💵 Est. Net Profit (30%)</span>
                    <span class="stat-value" style="color: var(--success);">₨{bk.get('net_profit', 0):,.0f}</span>
                </div>
                <div class="stat-row kpi-tooltip" style="position: relative;">
                    <span class="tooltip-text" style="bottom: 100%; left: 0; margin-left: 0;">
                        <strong>Total Doctors/Clients</strong><br>
                        Number of unique customers (doctors) who have placed orders.
                    </span>
                    <span class="stat-label">👨‍⚕️ Total Doctors/Clients</span>
                    <span class="stat-value">{bk.get('total_clients', 0):,}</span>
                </div>
                <div class="stat-row kpi-tooltip" style="position: relative;">
                    <span class="tooltip-text" style="bottom: 100%; left: 0; margin-left: 0;">
                        <strong>Client Acquisition Cost (CAC)</strong><br>
                        Average cost to acquire one customer. Calculated as marketing spend ÷ number of clients. Lower = more efficient!
                    </span>
                    <span class="stat-label">💰 Client Acquisition Cost</span>
                    <span class="stat-value">₨{bk.get('client_acquisition_cost', 0):,.0f}</span>
                </div>
                <div class="stat-row kpi-tooltip" style="position: relative;">
                    <span class="tooltip-text" style="bottom: 100%; left: 0; margin-left: 0;">
                        <strong>Total Orders</strong><br>
                        Total number of orders placed by all customers.
                    </span>
                    <span class="stat-label">📦 Total Orders</span>
                    <span class="stat-value">{bk.get('total_orders', 0):,}</span>
                </div>
            </div>
        </div>

        <!-- KPI Glossary -->
        <div class="section" style="margin-top: 1.5rem; background: #1e293b; border-radius: 12px; padding: 1.5rem;">
            <h3 class="section-title" style="margin-top: 0;">📖 KPI Glossary - Quick Reference</h3>
            <div class="grid-2" style="gap: 1rem;">
                <div style="font-size: 0.9rem; line-height: 1.8;">
                    <p><strong style="color: #10b981;">💰 Revenue</strong> = Total value of all orders (before collecting)</p>
                    <p><strong style="color: #10b981;">💵 Collected</strong> = Actual money received from customers</p>
                    <p><strong style="color: #f59e0b;">⏳ Pending</strong> = Money customers still owe you</p>
                    <p><strong style="color: #6366f1;">📈 Collection Rate</strong> = % of revenue actually collected</p>
                </div>
                <div style="font-size: 0.9rem; line-height: 1.8;">
                    <p><strong style="color: #10b981;">📊 Profit Margin</strong> = % of revenue that becomes profit</p>
                    <p><strong style="color: #6366f1;">🛒 Avg Order Value</strong> = Average amount per order</p>
                    <p><strong style="color: #f59e0b;">💰 CAC</strong> = Cost to acquire one new customer</p>
                    <p><strong style="color: #10b981;">📈 Growth (MoM)</strong> = Month-over-Month change %</p>
                </div>
            </div>
            <p style="margin-top: 1rem; color: #94a3b8; font-size: 0.85rem;">
                💡 <strong>Tip:</strong> Hover over any KPI card or metric for a detailed explanation!
            </p>
        </div>

        <script>
            // Monthly Revenue Trajectory Chart
            new Chart(document.getElementById('monthlyRevenueTrajectory'), {{
                type: 'line',
                data: {{
                    labels: {monthly_labels},
                    datasets: [
                        {{
                            label: 'Total Sales (₨)',
                            data: {monthly_sales},
                            borderColor: '#6366f1',
                            backgroundColor: 'rgba(99, 102, 241, 0.15)',
                            fill: true,
                            tension: 0.4,
                            pointRadius: 5,
                            pointBackgroundColor: '#6366f1',
                            borderWidth: 3
                        }},
                        {{
                            label: 'Amount Collected (₨)',
                            data: {monthly_paid},
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4,
                            borderWidth: 2
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ position: 'top', labels: {{ color: '#f8fafc' }} }}
                    }},
                    scales: {{
                        y: {{
                            ticks: {{ color: '#94a3b8', callback: function(value) {{ return '₨' + (value/1000000).toFixed(1) + 'M'; }} }},
                            grid: {{ color: '#334155' }}
                        }},
                        x: {{ ticks: {{ color: '#94a3b8', maxRotation: 45 }}, grid: {{ display: false }} }}
                    }}
                }}
            }});

            // Monthly Orders Trend
            new Chart(document.getElementById('monthlyOrdersTrend'), {{
                type: 'bar',
                data: {{
                    labels: {monthly_labels},
                    datasets: [{{
                        label: 'Orders',
                        data: {monthly_orders},
                        backgroundColor: '#8b5cf6',
                        borderRadius: 6
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }} }},
                        x: {{ ticks: {{ color: '#94a3b8', maxRotation: 45 }}, grid: {{ display: false }} }}
                    }}
                }}
            }});

            // Weekly Revenue Trend
            new Chart(document.getElementById('weeklyRevenueTrend'), {{
                type: 'line',
                data: {{
                    labels: {weekly_labels},
                    datasets: [{{
                        label: 'Weekly Revenue (₨)',
                        data: {weekly_sales},
                        borderColor: '#06b6d4',
                        backgroundColor: 'rgba(6, 182, 212, 0.1)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        y: {{
                            ticks: {{ color: '#94a3b8', callback: function(value) {{ return '₨' + (value/1000000).toFixed(1) + 'M'; }} }},
                            grid: {{ color: '#334155' }}
                        }},
                        x: {{ ticks: {{ color: '#94a3b8', maxRotation: 45 }}, grid: {{ display: false }} }}
                    }}
                }}
            }});

            // Product Categories Chart
            new Chart(document.getElementById('productCategoriesChart'), {{
                type: 'doughnut',
                data: {{
                    labels: {cat_labels},
                    datasets: [{{
                        data: {cat_data},
                        backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ position: 'right', labels: {{ color: '#f8fafc' }} }} }}
                }}
            }});

            // Payment Methods Chart
            new Chart(document.getElementById('paymentMethodsChart'), {{
                type: 'bar',
                data: {{
                    labels: {method_labels},
                    datasets: [{{
                        label: 'Revenue (₨)',
                        data: {method_revenue},
                        backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'],
                        borderRadius: 6
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        y: {{
                            ticks: {{ color: '#94a3b8', callback: function(value) {{ return '₨' + (value/1000000).toFixed(1) + 'M'; }} }},
                            grid: {{ color: '#334155' }}
                        }},
                        x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }}
                    }}
                }}
            }});

            // Product Trajectory Chart (Top 5 products over time)
            new Chart(document.getElementById('productTrajectoryChart'), {{
                type: 'line',
                data: {{
                    labels: {product_traj_labels},
                    datasets: {product_traj_datasets_json}
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'top',
                            labels: {{ color: '#f8fafc', boxWidth: 12, padding: 15 }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            ticks: {{
                                color: '#94a3b8',
                                callback: function(value) {{
                                    if (value >= 1000000) return '₨' + (value/1000000).toFixed(1) + 'M';
                                    if (value >= 1000) return '₨' + (value/1000).toFixed(0) + 'K';
                                    return '₨' + value;
                                }}
                            }},
                            grid: {{ color: '#334155' }}
                        }},
                        x: {{ ticks: {{ color: '#94a3b8', maxRotation: 45 }}, grid: {{ display: false }} }}
                    }},
                    interaction: {{
                        intersect: false,
                        mode: 'index'
                    }}
                }}
            }});
        </script>"""

    def _generate_financial_tracking_section(self) -> str:
        """Generate Financial Tracking section with investment/expense breakdowns."""
        bk = self.business_kpi_analytics
        ft = bk.get("financial_tracking", {})

        # Check if we have financial tracking data
        if not ft or not ft.get("has_financial_data"):
            return """
        <div class="section">
            <h2 class="section-title">💹 Financial Tracking (Manual Entry)</h2>
            <div style="text-align: center; padding: 3rem; color: var(--text-muted);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📋</div>
                <h3>Financial Tracking Not Configured</h3>
                <p>This section displays data from the manual Financial Tracking Google Sheet.</p>
                <p style="margin-top: 1rem;">To set up:</p>
                <ol style="text-align: left; max-width: 500px; margin: 1rem auto;">
                    <li>Create a Google Sheet from the template</li>
                    <li>Import <code>output/Q_Financial_Tracking_MockData.csv</code></li>
                    <li>Share with the service account</li>
                    <li>Update <code>FINANCIAL_TRACKING_SPREADSHEET_ID</code> in config</li>
                </ol>
            </div>
        </div>"""

        # Get data
        period = ft.get("period", "N/A")
        records_count = ft.get("records_count", 0)

        # Sales breakdown
        sales = ft.get("sales_breakdown", {})
        med_sales = sales.get("medical_products", {})
        beauty_sales = sales.get("beauty_products", {})

        # Investment breakdown
        inv = ft.get("investment_breakdown", {})
        inv_founder = inv.get("founder", {}).get("actual", 0)
        inv_cofounder = inv.get("cofounder", {}).get("actual", 0)
        inv_investor = inv.get("investor", {}).get("actual", 0)
        inv_importer = inv.get("importer", {}).get("actual", 0)
        inv_total = inv.get("total", {}).get("actual", 0)

        # Expense breakdown
        exp = ft.get("expense_breakdown", {})
        exp_operating = exp.get("operating", {}).get("actual", 0)
        exp_marketing = exp.get("marketing_sales", {}).get("actual", 0)
        exp_product = exp.get("product_costs", {}).get("actual", 0)
        exp_salaries = exp.get("salaries_wages", {}).get("actual", 0)
        exp_delivery = exp.get("delivery_logistics", {}).get("actual", 0)
        exp_regulatory = exp.get("regulatory_compliance", {}).get("actual", 0)
        exp_other = exp.get("other", {}).get("actual", 0)
        exp_total = exp.get("total", {}).get("actual", 0)

        # Doctor prizes
        prizes = ft.get("doctor_prizes", {})
        prize_gifts = prizes.get("gifts", {}).get("actual", 0)
        prize_research = prizes.get("research_products", {}).get("actual", 0)
        prize_total = prizes.get("total", {}).get("actual", 0)

        # Calculated KPIs
        kpis = ft.get("calculated_kpis", {})
        roi = kpis.get("roi_percent", 0)
        profit_margin = kpis.get("profit_margin_percent", 0)
        cac = kpis.get("cac", 0)
        debt_ratio = kpis.get("debt_ratio_percent", 0)
        collection_eff = kpis.get("collection_efficiency_percent", 0)

        # Target vs Actual
        tva = ft.get("target_vs_actual", {})

        # Trends data for charts
        fin_trends = ft.get("financial_trends", [])
        ft.get("investment_trend", [])
        ft.get("expense_trend", [])

        # Prepare chart data
        trend_labels = json.dumps([t.get("period", "") for t in fin_trends])
        trend_sales = json.dumps([t.get("sales", 0) for t in fin_trends])
        trend_expenses = json.dumps([t.get("expenses", 0) for t in fin_trends])
        trend_profit = json.dumps([t.get("profit", 0) for t in fin_trends])

        # Investment chart data
        inv_labels = json.dumps(["Founder", "Co-Founder", "Investor", "Importer"])
        inv_data = json.dumps([inv_founder, inv_cofounder, inv_investor, inv_importer])

        # Expense chart data
        exp_labels = json.dumps(["Operating", "Marketing", "Products", "Salaries", "Delivery", "Regulatory", "Other"])
        exp_data = json.dumps(
            [exp_operating, exp_marketing, exp_product, exp_salaries, exp_delivery, exp_regulatory, exp_other]
        )

        return f"""
        <div class="section">
            <h2 class="section-title">💹 Financial Tracking (Manual Entry)</h2>
            <p style="color: var(--text-muted); margin-bottom: 1rem;">
                📊 Data from Financial Tracking Sheet | Period: <strong>{period}</strong> | Records: {records_count}
            </p>

            <!-- KPI Cards -->
            <div class="executive-summary" style="margin-bottom: 2rem;">
                <div class="kpi-card success">
                    <div class="icon">💰</div>
                    <div class="value">₨{ft.get('total_sales', 0):,.0f}</div>
                    <div class="label">Total Sales</div>
                </div>
                <div class="kpi-card primary">
                    <div class="icon">💵</div>
                    <div class="value">₨{inv_total:,.0f}</div>
                    <div class="label">Total Investment</div>
                </div>
                <div class="kpi-card warning">
                    <div class="icon">📉</div>
                    <div class="value">₨{exp_total:,.0f}</div>
                    <div class="label">Total Expenses</div>
                </div>
                <div class="kpi-card {'success' if ft.get('net_profit', 0) > 0 else 'danger'}">
                    <div class="icon">{'📈' if ft.get('net_profit', 0) > 0 else '📉'}</div>
                    <div class="value">₨{ft.get('net_profit', 0):,.0f}</div>
                    <div class="label">Net Profit</div>
                </div>
                <div class="kpi-card info">
                    <div class="icon">📊</div>
                    <div class="value">{roi:.1f}%</div>
                    <div class="label">ROI</div>
                </div>
                <div class="kpi-card primary">
                    <div class="icon">🏆</div>
                    <div class="value">₨{prize_total:,.0f}</div>
                    <div class="label">Doctor Prizes</div>
                </div>
            </div>

            <!-- Sales Breakdown -->
            <div class="section" style="margin-bottom: 1.5rem; background: #1e293b; border-radius: 12px; padding: 1.5rem;">
                <h3 class="section-title" style="margin-top: 0;">🏥 Sales by Product Type</h3>
                <div class="grid-2">
                    <div class="stat-card">
                        <div class="stat-row">
                            <span class="stat-label">💊 Medical Products</span>
                            <span class="stat-value">₨{med_sales.get('actual', 0):,.0f}</span>
                        </div>
                        <div class="stat-row" style="font-size: 0.9rem; color: var(--text-muted);">
                            <span>Target: ₨{med_sales.get('target', 0):,.0f}</span>
                            <span class="badge {'badge-success' if med_sales.get('achievement_percent', 0) >= 100 else 'badge-warning'}">{med_sales.get('achievement_percent', 0):.1f}%</span>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-row">
                            <span class="stat-label">✨ Beauty Products</span>
                            <span class="stat-value">₨{beauty_sales.get('actual', 0):,.0f}</span>
                        </div>
                        <div class="stat-row" style="font-size: 0.9rem; color: var(--text-muted);">
                            <span>Target: ₨{beauty_sales.get('target', 0):,.0f}</span>
                            <span class="badge {'badge-success' if beauty_sales.get('achievement_percent', 0) >= 100 else 'badge-warning'}">{beauty_sales.get('achievement_percent', 0):.1f}%</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Charts Row -->
            <div class="grid-2" style="margin-bottom: 1.5rem;">
                <!-- Investment Breakdown -->
                <div class="chart-container" style="height: 300px;">
                    <h3 class="chart-title">💵 Investment by Source</h3>
                    <canvas id="investmentBreakdownChart"></canvas>
                </div>
                <!-- Expense Breakdown -->
                <div class="chart-container" style="height: 300px;">
                    <h3 class="chart-title">📊 Expense Breakdown</h3>
                    <canvas id="expenseBreakdownChart"></canvas>
                </div>
            </div>

            <!-- Trend Chart -->
            <div class="chart-container" style="height: 350px; margin-bottom: 1.5rem;">
                <h3 class="chart-title">📈 Financial Trends Over Time</h3>
                <canvas id="financialTrendChart"></canvas>
            </div>

            <!-- KPI Details -->
            <div class="section" style="background: #1e293b; border-radius: 12px; padding: 1.5rem;">
                <h3 class="section-title" style="margin-top: 0;">📋 Calculated KPIs</h3>
                <div class="grid-3">
                    <div class="stat-row">
                        <span class="stat-label">📊 ROI %</span>
                        <span class="stat-value" style="color: {'var(--success)' if roi > 0 else 'var(--danger)'};">{roi:.1f}%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">💰 Profit Margin %</span>
                        <span class="stat-value">{profit_margin:.1f}%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">👥 Client Acquisition Cost</span>
                        <span class="stat-value">₨{cac:,.0f}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">📉 Debt Ratio %</span>
                        <span class="stat-value">{debt_ratio:.1f}%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">💵 Collection Efficiency %</span>
                        <span class="stat-value">{collection_eff:.1f}%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">📈 Sales Growth %</span>
                        <span class="stat-value">{kpis.get('sales_growth_percent', 0):.1f}%</span>
                    </div>
                </div>
            </div>

            <!-- Target vs Actual -->
            <div class="section" style="margin-top: 1.5rem; background: #1e293b; border-radius: 12px; padding: 1.5rem;">
                <h3 class="section-title" style="margin-top: 0;">🎯 Target vs Actual Achievement</h3>
                <div class="grid-4">
                    <div class="stat-row">
                        <span class="stat-label">Sales</span>
                        <span class="stat-value badge {'badge-success' if tva.get('sales_achievement', 0) >= 100 else 'badge-warning'}">{tva.get('sales_achievement', 0):.1f}%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Profit</span>
                        <span class="stat-value badge {'badge-success' if tva.get('profit_achievement', 0) >= 100 else 'badge-warning'}">{tva.get('profit_achievement', 0):.1f}%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Clients</span>
                        <span class="stat-value badge {'badge-success' if tva.get('client_achievement', 0) >= 100 else 'badge-warning'}">{tva.get('client_achievement', 0):.1f}%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Expense Var.</span>
                        <span class="stat-value" style="color: {'var(--danger)' if tva.get('expense_variance', 0) > 0 else 'var(--success)'};">₨{tva.get('expense_variance', 0):,.0f}</span>
                    </div>
                </div>
            </div>

            <!-- Doctor Prizes -->
            <div class="section" style="margin-top: 1.5rem; background: #1e293b; border-radius: 12px; padding: 1.5rem;">
                <h3 class="section-title" style="margin-top: 0;">🏆 Doctor Prizes Distribution</h3>
                <div class="grid-3">
                    <div class="stat-row">
                        <span class="stat-label">🎁 Gifts</span>
                        <span class="stat-value">₨{prize_gifts:,.0f}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">🔬 Research Products</span>
                        <span class="stat-value">₨{prize_research:,.0f}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">📊 Total Prizes</span>
                        <span class="stat-value">₨{prize_total:,.0f}</span>
                    </div>
                </div>
            </div>

            {self._generate_capital_trajectory_chart(ft)}

            {self._generate_goal_progress_section(ft)}

            {self._generate_financial_trajectory_chart(ft)}
        </div>

        <script>
            // Investment Breakdown Chart
            new Chart(document.getElementById('investmentBreakdownChart'), {{
                type: 'doughnut',
                data: {{
                    labels: {inv_labels},
                    datasets: [{{
                        data: {inv_data},
                        backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#ef4444']
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ position: 'right', labels: {{ color: '#f8fafc' }} }} }}
                }}
            }});

            // Expense Breakdown Chart
            new Chart(document.getElementById('expenseBreakdownChart'), {{
                type: 'pie',
                data: {{
                    labels: {exp_labels},
                    datasets: [{{
                        data: {exp_data},
                        backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#94a3b8']
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ position: 'right', labels: {{ color: '#f8fafc' }} }} }}
                }}
            }});

            // Financial Trend Chart
            new Chart(document.getElementById('financialTrendChart'), {{
                type: 'line',
                data: {{
                    labels: {trend_labels},
                    datasets: [
                        {{
                            label: 'Sales',
                            data: {trend_sales},
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            fill: true,
                            tension: 0.4
                        }},
                        {{
                            label: 'Expenses',
                            data: {trend_expenses},
                            borderColor: '#ef4444',
                            fill: false,
                            tension: 0.4
                        }},
                        {{
                            label: 'Profit',
                            data: {trend_profit},
                            borderColor: '#6366f1',
                            fill: false,
                            tension: 0.4
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ position: 'top', labels: {{ color: '#f8fafc' }} }} }},
                    scales: {{
                        y: {{
                            ticks: {{ color: '#94a3b8', callback: function(value) {{ return '₨' + (value/1000000).toFixed(1) + 'M'; }} }},
                            grid: {{ color: '#334155' }}
                        }},
                        x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }}
                    }}
                }}
            }});
        </script>"""

    def _generate_capital_trajectory_chart(self, ft: dict) -> str:
        """Generate capital trajectory chart showing investment flow.

        Shows: Total Invested vs Money Retrieved vs Company Capital vs Outstanding
        """
        capital_traj = ft.get("capital_trajectory", {})
        if not capital_traj.get("has_data"):
            return ""

        labels = json.dumps(capital_traj.get("labels", []))
        total_invested = json.dumps(capital_traj.get("total_invested", []))
        money_retrieved = json.dumps(capital_traj.get("money_retrieved", []))
        company_capital = json.dumps(capital_traj.get("company_capital", []))
        outstanding = json.dumps(capital_traj.get("outstanding", []))

        summary = capital_traj.get("summary", {})
        latest_invested = summary.get("latest_invested", 0)
        latest_retrieved = summary.get("latest_retrieved", 0)
        latest_capital = summary.get("latest_capital", 0)
        latest_outstanding = summary.get("latest_outstanding", 0)

        # Calculate percentages
        retrieval_rate = (latest_retrieved / latest_invested * 100) if latest_invested > 0 else 0
        capital_growth = (latest_capital / latest_invested * 100) if latest_invested > 0 else 0

        return f"""
            <!-- Capital Trajectory Section -->
            <div class="section" style="margin-top: 2rem; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 12px; padding: 1.5rem;">
                <h3 class="section-title" style="margin-top: 0;">💰 Capital Flow Trajectory</h3>
                <p class="description" style="color: var(--text-muted); margin-bottom: 1rem;">
                    Track how investment flows: money invested → sales collected → company capital growth
                </p>

                <!-- Summary Cards -->
                <div class="executive-summary" style="margin-bottom: 1.5rem;">
                    <div class="kpi-card primary">
                        <div class="icon">💵</div>
                        <div class="value">₨{latest_invested:,.0f}</div>
                        <div class="label">Total Invested (Cumulative)</div>
                        <div class="kpi-subtext">Money put into business</div>
                    </div>
                    <div class="kpi-card success">
                        <div class="icon">📥</div>
                        <div class="value">₨{latest_retrieved:,.0f}</div>
                        <div class="label">Money Retrieved</div>
                        <div class="kpi-subtext">{retrieval_rate:.1f}% of invested</div>
                    </div>
                    <div class="kpi-card info">
                        <div class="icon">🏢</div>
                        <div class="value">₨{latest_capital:,.0f}</div>
                        <div class="label">Company Capital</div>
                        <div class="kpi-subtext">{capital_growth:.1f}% of investment</div>
                    </div>
                    <div class="kpi-card warning">
                        <div class="icon">⏳</div>
                        <div class="value">₨{latest_outstanding:,.0f}</div>
                        <div class="label">Outstanding Payments</div>
                        <div class="kpi-subtext">Pending collection</div>
                    </div>
                </div>

                <!-- Capital Trajectory Chart -->
                <div class="chart-container" style="height: 350px;">
                    <canvas id="capitalTrajectoryChart"></canvas>
                </div>

                <!-- Legend explanation -->
                <div class="trajectory-legend" style="margin-top: 1rem; display: flex; gap: 1.5rem; justify-content: center; flex-wrap: wrap; font-size: 0.85rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="width: 20px; height: 3px; background: #6366f1;"></span>
                        <span>Total Invested</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="width: 20px; height: 3px; background: #10b981;"></span>
                        <span>Money Retrieved</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="width: 20px; height: 3px; background: #f59e0b;"></span>
                        <span>Company Capital</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="width: 20px; height: 3px; background: #ef4444; border-style: dashed;"></span>
                        <span>Outstanding</span>
                    </div>
                </div>
            </div>

            <script>
            new Chart(document.getElementById('capitalTrajectoryChart'), {{
                type: 'line',
                data: {{
                    labels: {labels},
                    datasets: [
                        {{
                            label: 'Total Invested',
                            data: {total_invested},
                            borderColor: '#6366f1',
                            backgroundColor: 'rgba(99, 102, 241, 0.1)',
                            fill: true,
                            tension: 0.3,
                            pointRadius: 4
                        }},
                        {{
                            label: 'Money Retrieved',
                            data: {money_retrieved},
                            borderColor: '#10b981',
                            fill: false,
                            tension: 0.3,
                            pointRadius: 4
                        }},
                        {{
                            label: 'Company Capital',
                            data: {company_capital},
                            borderColor: '#f59e0b',
                            fill: false,
                            tension: 0.3,
                            pointRadius: 4
                        }},
                        {{
                            label: 'Outstanding',
                            data: {outstanding},
                            borderColor: '#ef4444',
                            borderDash: [5, 5],
                            fill: false,
                            tension: 0.3,
                            pointRadius: 4
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{
                        legend: {{ position: 'top', labels: {{ color: '#f8fafc' }} }},
                        title: {{ display: true, text: 'Capital Flow Over Time', color: '#f8fafc', font: {{ size: 14 }} }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return context.dataset.label + ': ₨' + context.parsed.y.toLocaleString();
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            ticks: {{ color: '#94a3b8', callback: function(v) {{ return '₨' + (v/1000000).toFixed(1) + 'M'; }} }},
                            grid: {{ color: '#334155' }}
                        }},
                        x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }}
                    }}
                }}
            }});
            </script>"""

    def _generate_goal_progress_section(self, ft: dict) -> str:
        """Generate goal progress section with progress bars."""
        goal_data = ft.get("goal_progress", {})
        goals = goal_data.get("goals", [])
        summary = goal_data.get("summary", {})

        if not goals:
            return ""

        # Build goal cards
        goal_cards = ""
        for goal in goals:
            name = goal.get("name", "")
            target = goal.get("target", 0)
            current = goal.get("current", 0)
            progress = goal.get("progress_percent", 0)
            status = goal.get("status", "behind")
            unit = goal.get("unit", "")

            # Determine colors
            if status == "achieved":
                status_color = "var(--success)"
                status_icon = "✅"
                bar_class = "badge-success"
            elif status == "on_track":
                status_color = "var(--warning)"
                status_icon = "🔄"
                bar_class = "badge-warning"
            else:
                status_color = "var(--danger)"
                status_icon = "⚠️"
                bar_class = "badge-danger"

            # Format values
            if unit == "%":
                target_str = f"{target:.1f}%"
                current_str = f"{current:.1f}%"
            else:
                target_str = f"₨{target:,.0f}"
                current_str = f"₨{current:,.0f}"

            goal_cards += f"""
                <div class="goal-card" style="background: #0f172a; border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-weight: 600;">{status_icon} {name}</span>
                        <span class="badge {bar_class}" style="font-size: 0.8rem;">{status.replace('_', ' ').title()}</span>
                    </div>
                    <div class="progress-bar" style="background: #334155; border-radius: 4px; height: 8px; overflow: hidden;">
                        <div style="width: {min(progress, 100)}%; height: 100%; background: {status_color}; transition: width 0.3s;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.85rem; color: var(--text-muted);">
                        <span>Current: {current_str}</span>
                        <span>{progress:.1f}%</span>
                        <span>Target: {target_str}</span>
                    </div>
                </div>"""

        # Overall health badge
        overall = summary.get("overall_health", "needs_attention")
        if overall == "excellent":
            health_badge = '<span class="badge badge-success">🌟 Excellent</span>'
        elif overall == "good":
            health_badge = '<span class="badge badge-warning">👍 Good</span>'
        else:
            health_badge = '<span class="badge badge-danger">⚠️ Needs Attention</span>'

        return f"""
            <!-- Goal Progress Section -->
            <div class="section" style="margin-top: 2rem; background: #1e293b; border-radius: 12px; padding: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 class="section-title" style="margin: 0;">🎯 Goal Progress Tracker</h3>
                    {health_badge}
                </div>
                <p class="description" style="color: var(--text-muted); margin-bottom: 1rem;">
                    Track progress toward monthly targets. Green = Achieved, Yellow = On Track (80%+), Red = Behind.
                </p>

                <!-- Summary Stats -->
                <div class="grid-3" style="margin-bottom: 1.5rem; text-align: center;">
                    <div style="padding: 0.5rem;">
                        <div style="font-size: 2rem; color: var(--success);">{summary.get('achieved', 0)}</div>
                        <div style="color: var(--text-muted); font-size: 0.85rem;">Achieved</div>
                    </div>
                    <div style="padding: 0.5rem;">
                        <div style="font-size: 2rem; color: var(--warning);">{summary.get('on_track', 0)}</div>
                        <div style="color: var(--text-muted); font-size: 0.85rem;">On Track</div>
                    </div>
                    <div style="padding: 0.5rem;">
                        <div style="font-size: 2rem; color: var(--danger);">{summary.get('behind', 0)}</div>
                        <div style="color: var(--text-muted); font-size: 0.85rem;">Behind</div>
                    </div>
                </div>

                <!-- Individual Goals -->
                <div class="goals-list">
                    {goal_cards}
                </div>
            </div>"""

    def _generate_financial_trajectory_chart(self, ft: dict) -> str:
        """Generate financial trajectory chart with actual vs target."""
        fin_traj = ft.get("financial_trajectory", {})
        if not fin_traj.get("has_data"):
            return ""

        labels = json.dumps(fin_traj.get("labels", []))
        sales_actual = json.dumps(fin_traj.get("sales", {}).get("actual", []))
        sales_target = json.dumps(fin_traj.get("sales", {}).get("target", []))
        profit_actual = json.dumps(fin_traj.get("profit", {}).get("actual", []))
        profit_target = json.dumps(fin_traj.get("profit", {}).get("target", []))
        investment_cumulative = json.dumps(fin_traj.get("investment", {}).get("cumulative", []))

        return f"""
            <!-- Financial Trajectory: Actual vs Target -->
            <div class="section" style="margin-top: 2rem; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 12px; padding: 1.5rem;">
                <h3 class="section-title" style="margin-top: 0;">📈 Financial Trajectory: Actual vs Target</h3>
                <p class="description" style="color: var(--text-muted); margin-bottom: 1rem;">
                    Compare actual performance against targets. Solid lines = Actual, Dashed lines = Target.
                </p>

                <div class="chart-container" style="height: 400px;">
                    <canvas id="financialActualVsTargetChart"></canvas>
                </div>
            </div>

            <script>
            new Chart(document.getElementById('financialActualVsTargetChart'), {{
                type: 'line',
                data: {{
                    labels: {labels},
                    datasets: [
                        {{
                            label: 'Sales (Actual)',
                            data: {sales_actual},
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            fill: true,
                            tension: 0.3,
                            pointRadius: 4
                        }},
                        {{
                            label: 'Sales (Target)',
                            data: {sales_target},
                            borderColor: '#10b981',
                            borderDash: [5, 5],
                            fill: false,
                            tension: 0.3,
                            pointRadius: 2
                        }},
                        {{
                            label: 'Profit (Actual)',
                            data: {profit_actual},
                            borderColor: '#6366f1',
                            fill: false,
                            tension: 0.3,
                            pointRadius: 4
                        }},
                        {{
                            label: 'Profit (Target)',
                            data: {profit_target},
                            borderColor: '#6366f1',
                            borderDash: [5, 5],
                            fill: false,
                            tension: 0.3,
                            pointRadius: 2
                        }},
                        {{
                            label: 'Investment (Cumulative)',
                            data: {investment_cumulative},
                            borderColor: '#f59e0b',
                            fill: false,
                            tension: 0.3,
                            pointRadius: 4
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{
                        legend: {{
                            position: 'top',
                            labels: {{
                                color: '#f8fafc',
                                usePointStyle: true
                            }}
                        }},
                        title: {{
                            display: true,
                            text: 'Monthly Performance: Actual vs Target',
                            color: '#f8fafc',
                            font: {{ size: 14 }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            ticks: {{
                                color: '#94a3b8',
                                callback: function(v) {{ return '₨' + (v/1000000).toFixed(1) + 'M'; }}
                            }},
                            grid: {{ color: '#334155' }}
                        }},
                        x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }}
                    }}
                }}
            }});
            </script>"""

    def _generate_historical_trends_section(self) -> str:
        """Generate historical trends section with charts and comparisons."""
        if not self.trend_analytics.get("has_data"):
            return """
            <div class="section">
                <h2>📈 Historical Trends</h2>
                <div class="info-card">
                    <p>📊 Historical data not yet available.</p>
                    <p>Run the report daily to build up historical data for trend analysis.</p>
                    <p>Trend analysis requires at least 7 days of data.</p>
                </div>
            </div>"""

        growth = self.trend_analytics.get("growth_rates", {})
        trends = self.trend_analytics.get("trends", {})
        seasonal = self.trend_analytics.get("seasonal_patterns", {})
        comparisons = self.comparison_analytics

        # Build growth cards
        growth_cards = ""
        for metric, data in growth.items():
            metric_label = metric.replace("_", " ").title()
            dod = data.get("dod", 0)
            wow = data.get("wow", 0)
            mom = data.get("mom", 0)
            current = data.get("current", 0)

            dod_class = "trend-up" if dod > 0 else ("trend-down" if dod < 0 else "trend-flat")
            wow_class = "trend-up" if wow > 0 else ("trend-down" if wow < 0 else "trend-flat")
            mom_class = "trend-up" if mom > 0 else ("trend-down" if mom < 0 else "trend-flat")

            dod_arrow = "📈" if dod > 0 else ("📉" if dod < 0 else "➡️")
            wow_arrow = "📈" if wow > 0 else ("📉" if wow < 0 else "➡️")
            mom_arrow = "📈" if mom > 0 else ("📉" if mom < 0 else "➡️")

            growth_cards += f"""
            <div class="kpi-card">
                <div class="kpi-label">{metric_label}</div>
                <div class="kpi-value">{current:,.0f}</div>
                <div class="trend-indicators">
                    <span class="{dod_class}">{dod_arrow} DoD: {dod:+.1f}%</span>
                    <span class="{wow_class}">{wow_arrow} WoW: {wow:+.1f}%</span>
                    <span class="{mom_class}">{mom_arrow} MoM: {mom:+.1f}%</span>
                </div>
            </div>"""

        # Build trend direction summary
        trend_summary = ""
        for metric, data in trends.items():
            metric_label = metric.replace("_", " ").title()
            direction = data.get("direction", "sideways")
            strength = data.get("strength", 0)

            icon = "📈" if direction == "upward" else ("📉" if direction == "downward" else "➡️")
            color_class = "success" if direction == "upward" else ("danger" if direction == "downward" else "warning")

            trend_summary += f"""
            <tr>
                <td>{metric_label}</td>
                <td><span class="badge badge-{color_class}">{icon} {direction.title()}</span></td>
                <td>{strength:.0%}</td>
                <td>{data.get('days_analyzed', 0)} days</td>
            </tr>"""

        # Build comparison cards
        comparison_html = ""
        today_vs_yesterday = comparisons.get("today_vs_yesterday", {})
        if today_vs_yesterday.get("metrics"):
            summary = today_vs_yesterday.get("summary", {})
            sentiment_class = (
                "success"
                if summary.get("overall_sentiment") == "positive"
                else ("danger" if summary.get("overall_sentiment") == "negative" else "warning")
            )
            comparison_html += f"""
            <div class="comparison-card">
                <h4>Today vs Yesterday</h4>
                <div class="comparison-summary badge badge-{sentiment_class}">
                    {summary.get('improved', 0)} improved, {summary.get('declined', 0)} declined
                </div>
            </div>"""

        # Rankings section
        rankings_html = ""
        rankings = comparisons.get("rankings", {})
        if rankings.get("revenue_total"):
            top_days = rankings["revenue_total"].get("top_days", [])[:5]
            rankings_html = """
            <div class="rankings-section">
                <h4>🏆 Top 5 Revenue Days</h4>
                <table class="data-table">
                    <thead><tr><th>Rank</th><th>Date</th><th>Revenue</th></tr></thead>
                    <tbody>"""
            for day in top_days:
                rankings_html += f"""
                    <tr>
                        <td>#{day['rank']}</td>
                        <td>{day['date']}</td>
                        <td>₨{day['value']:,.0f}</td>
                    </tr>"""
            rankings_html += "</tbody></table></div>"

        # Seasonal patterns
        seasonal_html = ""
        rev_seasonal = seasonal.get("revenue_total", {})
        if rev_seasonal.get("day_averages"):
            seasonal_html = f"""
            <div class="seasonal-section">
                <h4>📅 Weekly Patterns (Revenue)</h4>
                <p><strong>Peak Day:</strong> {rev_seasonal.get('peak_day', 'N/A')}</p>
                <p><strong>Lowest Day:</strong> {rev_seasonal.get('low_day', 'N/A')}</p>
            </div>"""

        return f"""
        <div class="section">
            <h2>📈 Historical Trends</h2>

            <div class="subsection">
                <h3>Growth Rates</h3>
                <p class="description">How metrics are changing over time: Day-over-Day (DoD), Week-over-Week (WoW), and Month-over-Month (MoM).</p>
                <div class="kpi-grid">
                    {growth_cards}
                </div>
            </div>

            <div class="subsection">
                <h3>Trend Direction</h3>
                <p class="description">Statistical trend analysis using linear regression over the past 7 days.</p>
                <table class="data-table">
                    <thead>
                        <tr><th>Metric</th><th>Direction</th><th>Strength</th><th>Period</th></tr>
                    </thead>
                    <tbody>
                        {trend_summary}
                    </tbody>
                </table>
            </div>

            <div class="grid-2">
                <div class="subsection">
                    <h3>Period Comparisons</h3>
                    {comparison_html if comparison_html else "<p>Run report for multiple days to see comparisons.</p>"}
                </div>
                <div class="subsection">
                    {rankings_html if rankings_html else ""}
                </div>
            </div>

            {seasonal_html}
        </div>"""

    def _generate_forecast_section(self) -> str:
        """Generate forecast and predictions section."""
        if not self.forecast_analytics.get("has_data"):
            return """
            <div class="section">
                <h2>🔮 Forecast & Predictions</h2>
                <div class="info-card">
                    <p>🔮 Forecasting requires at least 14 days of historical data.</p>
                    <p>Continue running the report daily to enable predictions.</p>
                </div>
            </div>"""

        self.forecast_analytics.get("forecasts_by_metric", {})
        daily = self.forecast_analytics.get("daily_forecasts", [])
        projections = self.forecast_analytics.get("projections", {})
        goals = self.forecast_analytics.get("goal_tracking", {})
        trajectory_data = self.forecast_analytics.get("trajectory_chart_data", {})

        # Generate trajectory chart for revenue
        trajectory_chart_html = self._generate_trajectory_chart(trajectory_data)

        # 7-day forecast table
        forecast_table = ""
        if daily:
            forecast_table = """
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Day</th>
                        <th>Revenue (Predicted)</th>
                        <th>Confidence Range</th>
                    </tr>
                </thead>
                <tbody>"""
            for day in daily:
                rev = day.get("revenue_total", {})
                if rev:
                    forecast_table += f"""
                    <tr>
                        <td>{day['date']}</td>
                        <td>{day['day_name']}</td>
                        <td>₨{rev.get('value', 0):,.0f}</td>
                        <td>₨{rev.get('lower', 0):,.0f} - ₨{rev.get('upper', 0):,.0f}</td>
                    </tr>"""
            forecast_table += "</tbody></table>"

        # Monthly projections
        proj_html = ""
        proj_metrics = projections.get("metrics", {})
        if proj_metrics:
            proj_html = """
            <div class="kpi-grid">"""
            for metric, data in proj_metrics.items():
                metric_label = metric.replace("_", " ").title()
                proj_html += f"""
                <div class="kpi-card">
                    <div class="kpi-label">{metric_label} (Projected Month)</div>
                    <div class="kpi-value">₨{data.get('projected_month', 0):,.0f}</div>
                    <div class="kpi-subtext">MTD: ₨{data.get('mtd_value', 0):,.0f}</div>
                    <div class="kpi-subtext">Daily Avg: ₨{data.get('daily_avg', 0):,.0f}</div>
                </div>"""
            proj_html += "</div>"

        # Goal tracking
        goal_html = ""
        if goals:
            goal_html = """
            <h3>🎯 Goal Tracking</h3>
            <div class="goal-grid">"""
            for metric, data in goals.items():
                metric_label = metric.replace("_", " ").title()
                progress = data.get("progress_percent", 0)
                on_track = data.get("on_track", False)
                status_class = "success" if on_track else "warning"

                goal_html += f"""
                <div class="goal-card">
                    <h4>{metric_label}</h4>
                    <div class="progress-bar">
                        <div class="progress-fill badge-{status_class}" style="width: {min(progress, 100)}%"></div>
                    </div>
                    <p>{progress:.1f}% of target</p>
                    <p class="kpi-subtext">Target: ₨{data.get('target', 0):,.0f}</p>
                    <p class="kpi-subtext">Current: ₨{data.get('current', 0):,.0f}</p>
                    <p class="kpi-subtext">Required Daily: ₨{data.get('required_daily_avg', 0):,.0f}</p>
                </div>"""
            goal_html += "</div>"

        # Model info
        model_info = self.forecast_analytics.get("model_info", {})
        model_note = ""
        if model_info.get("statsmodels_available"):
            model_note = (
                "<p class='description'>Using Holt-Winters exponential smoothing with 85% confidence intervals.</p>"
            )
        else:
            model_note = "<p class='description'>Using simple moving average forecasting. Install statsmodels for advanced predictions.</p>"

        return f"""
        <div class="section">
            <h2>🔮 Forecast & Predictions</h2>
            {model_note}

            <div class="subsection">
                <h3>📊 Revenue Trajectory: Actual vs Forecast vs Target</h3>
                <p class="description">Historical performance (solid blue), predicted values (dashed green), and baseline target (dotted orange).</p>
                {trajectory_chart_html}
            </div>

            <div class="subsection">
                <h3>7-Day Revenue Forecast</h3>
                <p class="description">Predicted daily revenue with confidence intervals.</p>
                {forecast_table if forecast_table else "<p>No forecast data available.</p>"}
            </div>

            <div class="subsection">
                <h3>Monthly Projections</h3>
                <p class="description">Based on current month-to-date performance, projected month totals.</p>
                {proj_html if proj_html else "<p>No projection data available.</p>"}
            </div>

            <div class="subsection">
                {goal_html if goal_html else ""}
            </div>

            <div class="subsection risk-indicators">
                <h3>⚠️ Risk Indicators</h3>
                {self._generate_risk_indicators()}
            </div>
        </div>"""

    def _generate_risk_indicators(self) -> str:
        """Generate risk indicators based on forecast and anomaly data."""
        risks = []

        # Check anomalies
        anomaly_summary = self.anomaly_analytics.get("anomaly_summary", {})
        if anomaly_summary.get("critical_alerts", 0) > 0:
            risks.append(("Critical", f"{anomaly_summary['critical_alerts']} critical anomalies detected", "danger"))
        if anomaly_summary.get("warning_alerts", 0) > 0:
            risks.append(("Warning", f"{anomaly_summary['warning_alerts']} warnings detected", "warning"))

        # Check goal tracking
        goals = self.forecast_analytics.get("goal_tracking", {})
        for metric, data in goals.items():
            if not data.get("on_track", True):
                metric_label = metric.replace("_", " ").title()
                risks.append(("Warning", f"{metric_label} is behind target", "warning"))

        if not risks:
            return """
            <div class="risk-item success">
                <span class="risk-icon">✅</span>
                <span>All systems normal - no significant risks detected</span>
            </div>"""

        risk_html = ""
        for severity, message, color in risks:
            icon = "🚨" if severity == "Critical" else "⚠️"
            risk_html += f"""
            <div class="risk-item {color}">
                <span class="risk-icon">{icon}</span>
                <span>{message}</span>
            </div>"""

        return risk_html

    def _generate_trajectory_chart(self, trajectory_data: dict) -> str:
        """Generate trajectory chart showing actual vs forecast vs target.

        Args:
            trajectory_data: Dictionary with chart data for each metric

        Returns:
            HTML string with Chart.js trajectory charts
        """
        if not trajectory_data:
            return "<p class='description'>No trajectory data available.</p>"

        # Generate chart for revenue (primary metric)
        revenue_data = trajectory_data.get("revenue_total", {})
        if not revenue_data:
            # Try first available metric
            for _metric, data in trajectory_data.items():
                if data.get("labels"):
                    revenue_data = data
                    break

        if not revenue_data or not revenue_data.get("labels"):
            return "<p class='description'>No trajectory data available.</p>"

        labels = json.dumps(revenue_data.get("labels", []))
        actual = json.dumps(revenue_data.get("actual", []))
        forecast = json.dumps(revenue_data.get("forecast", []))
        forecast_lower = json.dumps(revenue_data.get("forecast_lower", []))
        forecast_upper = json.dumps(revenue_data.get("forecast_upper", []))
        target = json.dumps(revenue_data.get("target", []))
        metric_label = revenue_data.get("metric_label", "Revenue")

        # Build additional metric charts (orders, users)
        additional_charts = ""
        orders_data = trajectory_data.get("orders_total", {})
        trajectory_data.get("users_total", {})

        if orders_data.get("labels"):
            orders_labels = json.dumps(orders_data.get("labels", []))
            orders_actual = json.dumps(orders_data.get("actual", []))
            orders_forecast = json.dumps(orders_data.get("forecast", []))
            orders_target = json.dumps(orders_data.get("target", []))
            additional_charts += f"""
            <div class="chart-container" style="height: 250px; margin-top: 1.5rem;">
                <canvas id="ordersTrajectoryChart"></canvas>
            </div>
            <script>
                new Chart(document.getElementById('ordersTrajectoryChart'), {{
                    type: 'line',
                    data: {{
                        labels: {orders_labels},
                        datasets: [
                            {{
                                label: 'Actual Orders',
                                data: {orders_actual},
                                borderColor: '#3b82f6',
                                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                                fill: true,
                                tension: 0.3,
                                pointRadius: 4,
                                spanGaps: false
                            }},
                            {{
                                label: 'Forecast',
                                data: {orders_forecast},
                                borderColor: '#10b981',
                                borderDash: [5, 5],
                                fill: false,
                                tension: 0.3,
                                pointRadius: 4,
                                spanGaps: false
                            }},
                            {{
                                label: 'Target (Avg)',
                                data: {orders_target},
                                borderColor: '#f59e0b',
                                borderDash: [2, 2],
                                fill: false,
                                tension: 0,
                                pointRadius: 0,
                                borderWidth: 2
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ position: 'top', labels: {{ color: '#f8fafc' }} }},
                            title: {{ display: true, text: 'Orders Trajectory', color: '#f8fafc' }}
                        }},
                        scales: {{
                            y: {{
                                ticks: {{ color: '#94a3b8' }},
                                grid: {{ color: '#334155' }}
                            }},
                            x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }}
                        }}
                    }}
                }});
            </script>"""

        return f"""
        <div class="trajectory-charts">
            <div class="chart-container" style="height: 350px;">
                <canvas id="revenueTrajectoryChart"></canvas>
            </div>

            <div class="trajectory-legend" style="margin-top: 1rem; display: flex; gap: 2rem; justify-content: center; flex-wrap: wrap;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="width: 30px; height: 3px; background: #3b82f6; display: inline-block;"></span>
                    <span>Actual (Historical)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="width: 30px; height: 3px; background: #10b981; border-style: dashed; display: inline-block;"></span>
                    <span>Forecast (Predicted)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="width: 30px; height: 3px; background: #f59e0b; border-style: dotted; display: inline-block;"></span>
                    <span>Target (Baseline Avg)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="width: 30px; height: 10px; background: rgba(16, 185, 129, 0.2); display: inline-block;"></span>
                    <span>Confidence Band (85%)</span>
                </div>
            </div>

            {additional_charts}
        </div>

        <script>
            // Revenue Trajectory Chart
            new Chart(document.getElementById('revenueTrajectoryChart'), {{
                type: 'line',
                data: {{
                    labels: {labels},
                    datasets: [
                        {{
                            label: 'Actual {metric_label}',
                            data: {actual},
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            fill: true,
                            tension: 0.3,
                            pointRadius: 5,
                            pointBackgroundColor: '#3b82f6',
                            spanGaps: false
                        }},
                        {{
                            label: 'Forecast',
                            data: {forecast},
                            borderColor: '#10b981',
                            borderDash: [5, 5],
                            fill: false,
                            tension: 0.3,
                            pointRadius: 5,
                            pointBackgroundColor: '#10b981',
                            spanGaps: false
                        }},
                        {{
                            label: 'Confidence Upper',
                            data: {forecast_upper},
                            borderColor: 'rgba(16, 185, 129, 0.3)',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            fill: '+1',
                            tension: 0.3,
                            pointRadius: 0,
                            spanGaps: false
                        }},
                        {{
                            label: 'Confidence Lower',
                            data: {forecast_lower},
                            borderColor: 'rgba(16, 185, 129, 0.3)',
                            fill: false,
                            tension: 0.3,
                            pointRadius: 0,
                            spanGaps: false
                        }},
                        {{
                            label: 'Target (Avg)',
                            data: {target},
                            borderColor: '#f59e0b',
                            borderDash: [2, 2],
                            fill: false,
                            tension: 0,
                            pointRadius: 0,
                            borderWidth: 2
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    plugins: {{
                        legend: {{
                            position: 'top',
                            labels: {{
                                color: '#f8fafc',
                                filter: function(item) {{
                                    // Hide confidence bands from legend
                                    return !item.text.includes('Confidence');
                                }}
                            }}
                        }},
                        title: {{
                            display: true,
                            text: '{metric_label} Trajectory: Past 14 Days + 7-Day Forecast',
                            color: '#f8fafc',
                            font: {{ size: 16 }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    if (context.dataset.label.includes('Confidence')) return null;
                                    let value = context.parsed.y;
                                    if (value === null) return null;
                                    return context.dataset.label + ': ₨' + value.toLocaleString();
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            ticks: {{
                                color: '#94a3b8',
                                callback: function(value) {{
                                    return '₨' + (value/1000000).toFixed(1) + 'M';
                                }}
                            }},
                            grid: {{ color: '#334155' }}
                        }},
                        x: {{
                            ticks: {{ color: '#94a3b8' }},
                            grid: {{ display: false }}
                        }}
                    }}
                }}
            }});
        </script>"""

    def _generate_alerts_banner(self) -> str:
        """Generate alerts banner if there are critical anomalies."""
        alerts = self.anomaly_analytics.get("alerts", [])
        critical = [a for a in alerts if a.get("severity") == "critical"]
        warnings = [a for a in alerts if a.get("severity") == "warning"]

        if not critical and not warnings:
            return ""

        banner_html = '<div class="alerts-banner">'
        if critical:
            banner_html += f"""
            <div class="alert-item critical">
                🚨 <strong>{len(critical)} Critical Alert(s):</strong>
                {'; '.join(a.get('message', '') for a in critical[:3])}
            </div>"""
        if warnings:
            banner_html += f"""
            <div class="alert-item warning">
                ⚠️ <strong>{len(warnings)} Warning(s):</strong>
                {'; '.join(a.get('message', '') for a in warnings[:3])}
            </div>"""
        banner_html += "</div>"

        return banner_html

    def _generate_footer(self) -> str:
        """Generate footer."""
        return f"""
        <div class="footer">
            <p>Business Intelligence Report - Generated by AestheticRxNetworkIntelligentBot</p>
            <p>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>"""

    def _get_scripts(self) -> str:
        """Get JavaScript for tab functionality."""
        return """
    <script>
        function openTab(evt, tabId) {
            var tabContents = document.getElementsByClassName('tab-content');
            for (var i = 0; i < tabContents.length; i++) {
                tabContents[i].classList.remove('active');
            }
            var navTabs = document.getElementsByClassName('nav-tab');
            for (var i = 0; i < navTabs.length; i++) {
                navTabs[i].classList.remove('active');
            }
            document.getElementById(tabId).classList.add('active');
            evt.currentTarget.classList.add('active');
        }
    </script>"""
