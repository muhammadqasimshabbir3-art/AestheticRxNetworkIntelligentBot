"""Business KPI Analyzer.

This module analyzes business KPIs from multiple data sources:
1. Downloaded export data (orders, users, payments)
2. Financial tracking sheet data (if configured)

Generates comprehensive business metrics and trajectory charts.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from libraries.logger import logger


@dataclass
class SalesBreakdown:
    """Sales breakdown by product type."""

    total_sales: float = 0.0
    medical_products: float = 0.0
    beauty_products: float = 0.0
    medical_percentage: float = 0.0
    beauty_percentage: float = 0.0


@dataclass
class ExpenseBreakdown:
    """Expense breakdown by category."""

    total_expenses: float = 0.0
    operating: float = 0.0
    marketing_sales: float = 0.0
    product_costs: float = 0.0
    salaries_wages: float = 0.0
    delivery_logistics: float = 0.0
    regulatory_compliance: float = 0.0
    other: float = 0.0

    @property
    def breakdown_dict(self) -> dict[str, float]:
        """Get expense breakdown as dictionary."""
        return {
            "Operating": self.operating,
            "Marketing/Sales": self.marketing_sales,
            "Product Costs (COGS)": self.product_costs,
            "Salaries/Wages": self.salaries_wages,
            "Delivery/Logistics": self.delivery_logistics,
            "Regulatory/Compliance": self.regulatory_compliance,
            "Other": self.other,
        }

    @property
    def breakdown_percentages(self) -> dict[str, float]:
        """Get expense breakdown as percentages."""
        if self.total_expenses <= 0:
            return dict.fromkeys(self.breakdown_dict.keys(), 0.0)
        return {
            k: (v / self.total_expenses) * 100
            for k, v in self.breakdown_dict.items()
        }


@dataclass
class InvestmentBreakdown:
    """Investment breakdown by source."""

    total_investment: float = 0.0
    founder: float = 0.0
    cofounder: float = 0.0
    investor: float = 0.0
    importer: float = 0.0

    @property
    def breakdown_dict(self) -> dict[str, float]:
        """Get investment breakdown as dictionary."""
        return {
            "Founder": self.founder,
            "Co-Founder": self.cofounder,
            "External Investors": self.investor,
            "Importers": self.importer,
        }

    @property
    def breakdown_percentages(self) -> dict[str, float]:
        """Get investment breakdown as percentages."""
        if self.total_investment <= 0:
            return dict.fromkeys(self.breakdown_dict.keys(), 0.0)
        return {
            k: (v / self.total_investment) * 100
            for k, v in self.breakdown_dict.items()
        }


@dataclass
class DoctorPrizesBreakdown:
    """Doctor prizes breakdown by type."""

    total_prizes: float = 0.0
    gifts: float = 0.0
    research_products: float = 0.0


@dataclass
class GrowthMetrics:
    """Growth metrics month-over-month."""

    sales_growth_percent: float = 0.0
    client_growth_percent: float = 0.0
    profit_growth_percent: float = 0.0
    expense_growth_percent: float = 0.0
    order_growth_percent: float = 0.0


@dataclass
class MonthlyTrend:
    """Single month trend data point."""

    year: int
    month: str
    month_num: int
    total_sales: float
    total_orders: int
    total_clients: int
    avg_order_value: float
    paid_amount: float
    pending_amount: float
    completion_rate: float


@dataclass
class WeeklyTrend:
    """Weekly trend data point."""

    week_start: str
    week_num: int
    total_sales: float
    total_orders: int
    avg_order_value: float


class BusinessKPIAnalyzer:
    """Analyzes business KPIs from downloaded data and financial tracking."""

    def __init__(
        self,
        data_frames: dict[str, pd.DataFrame] | None = None,
        financial_data: Any = None,
    ) -> None:
        """Initialize the analyzer.

        Args:
            data_frames: Dictionary of DataFrames from DataLoader
            financial_data: Optional FinancialTrackingData from Google Sheet
        """
        self.data_frames = data_frames or {}
        self.financial_data = financial_data
        self._analysis_results: dict = {}

    def analyze(self) -> dict:
        """Run full analysis and return results.

        Returns:
            Dictionary containing all KPI analysis results
        """
        logger.info("Analyzing business KPIs from downloaded data...")

        # Check if we have data to analyze
        orders_df = self.data_frames.get("orders")
        if orders_df is None or orders_df.empty:
            logger.warning("No order data available for KPI analysis")
            return self._get_empty_results()

        # Calculate all metrics from downloaded data
        results = {
            # Meta
            "has_data": True,
            "data_source": "downloaded_export",
            "records_count": len(orders_df),
            "analysis_timestamp": datetime.now().isoformat(),

            # Core Metrics from Orders
            **self._analyze_revenue_metrics(orders_df),

            # Client Metrics
            **self._analyze_client_metrics(),

            # Growth & Trajectories
            "growth": self._calculate_growth_metrics(orders_df),
            "monthly_trends": self._calculate_monthly_trends(orders_df),
            "weekly_trends": self._calculate_weekly_trends(orders_df),

            # Product Analysis
            **self._analyze_products(orders_df),

            # Product Trajectories (per-product sales/payment over time)
            **self._calculate_product_trajectories(orders_df),

            # Payment Method Analysis
            **self._analyze_payment_methods(orders_df),

            # Status Distribution for charts
            **self._analyze_status_distribution(orders_df),

            # Projections
            **self._calculate_projections(orders_df),
        }

        # Add financial tracking data if available
        if self.financial_data and hasattr(self.financial_data, "has_data") and self.financial_data.has_data:
            results["financial_tracking"] = self._process_financial_tracking()

        self._analysis_results = results
        logger.info(f"✓ Business KPIs analyzed: Revenue={results.get('total_revenue', 0):,.0f}")

        return results

    def _get_empty_results(self) -> dict:
        """Get empty results structure when no data available."""
        return {
            "has_data": False,
            "data_source": None,
            "records_count": 0,
            "analysis_timestamp": datetime.now().isoformat(),
            "total_revenue": 0.0,
            "total_paid": 0.0,
            "total_pending": 0.0,
            "net_profit": 0.0,
            "profit_margin_percent": 0.0,
            "collection_efficiency_percent": 0.0,
            "total_orders": 0,
            "total_clients": 0,
            "avg_order_value": 0.0,
            "growth": GrowthMetrics(),
            "monthly_trends": [],
            "weekly_trends": [],
            "top_products": [],
            "product_categories": {},
            "product_trajectories": [],
            "trajectory_labels": [],
        }

    def _analyze_revenue_metrics(self, orders_df: pd.DataFrame) -> dict:
        """Analyze revenue metrics from orders."""
        # Get numeric columns safely
        if "order_total" in orders_df.columns:
            order_total = pd.to_numeric(orders_df["order_total"], errors="coerce").fillna(0)
        else:
            order_total = pd.Series([0])

        if "payment_amount" in orders_df.columns:
            payment_amount = pd.to_numeric(orders_df["payment_amount"], errors="coerce").fillna(0)
        else:
            payment_amount = pd.Series([0])

        if "remaining_amount" in orders_df.columns:
            remaining_amount = pd.to_numeric(orders_df["remaining_amount"], errors="coerce").fillna(0)
        else:
            remaining_amount = pd.Series([0])

        total_revenue = order_total.sum()
        total_paid = payment_amount.sum()
        total_pending = remaining_amount.sum()

        # Estimate profit (assume 30% margin for now - can be configured)
        estimated_cogs = total_revenue * 0.50  # 50% cost of goods
        estimated_expenses = total_revenue * 0.20  # 20% operating expenses
        net_profit = total_paid - estimated_cogs - estimated_expenses

        collection_efficiency = (total_paid / total_revenue * 100) if total_revenue > 0 else 0
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

        avg_order_value = total_revenue / len(orders_df) if len(orders_df) > 0 else 0

        return {
            "total_revenue": total_revenue,
            "total_paid": total_paid,
            "total_pending": total_pending,
            "estimated_cogs": estimated_cogs,
            "estimated_expenses": estimated_expenses,
            "net_profit": net_profit,
            "profit_margin_percent": profit_margin,
            "collection_efficiency_percent": collection_efficiency,
            "roi_percent": collection_efficiency,  # Using collection as ROI proxy
            "total_orders": len(orders_df),
            "avg_order_value": avg_order_value,
        }

    def _analyze_client_metrics(self) -> dict:
        """Analyze client/doctor metrics."""
        doctors_df = self.data_frames.get("doctors")
        users_df = self.data_frames.get("users")

        total_doctors = len(doctors_df) if doctors_df is not None else 0
        total_users = len(users_df) if users_df is not None else 0

        # Calculate CAC (Client Acquisition Cost) estimate
        # Assume marketing spend is 15% of revenue
        orders_df = self.data_frames.get("orders")
        if orders_df is not None and not orders_df.empty and "order_total" in orders_df.columns:
            total_revenue = pd.to_numeric(orders_df["order_total"], errors="coerce").fillna(0).sum()
            estimated_marketing = total_revenue * 0.15
            cac = estimated_marketing / total_doctors if total_doctors > 0 else 0
        else:
            cac = 0

        return {
            "total_clients": total_doctors,
            "total_users": total_users,
            "client_acquisition_cost": cac,
        }

    def _calculate_growth_metrics(self, orders_df: pd.DataFrame) -> GrowthMetrics:
        """Calculate growth metrics from orders."""
        # Try to get date column
        date_col = None
        for col in ["created_at", "order_date", "payment_date"]:
            if col in orders_df.columns:
                date_col = col
                break

        if date_col is None:
            return GrowthMetrics()

        # Convert to datetime
        orders_df = orders_df.copy()
        orders_df["_date"] = pd.to_datetime(orders_df[date_col], errors="coerce")
        orders_df = orders_df.dropna(subset=["_date"])

        if orders_df.empty:
            return GrowthMetrics()

        # Add order total column safely
        if "order_total" in orders_df.columns:
            orders_df["_order_total"] = pd.to_numeric(orders_df["order_total"], errors="coerce").fillna(0)
        else:
            orders_df["_order_total"] = 0

        # Group by month
        orders_df["_month"] = orders_df["_date"].dt.to_period("M")
        monthly = orders_df.groupby("_month").agg({
            "_order_total": "sum",
            "id": "count",
        }).reset_index()

        if len(monthly) < 2:
            return GrowthMetrics()

        # Calculate growth between last two months
        current = monthly.iloc[-1]
        previous = monthly.iloc[-2]

        sales_growth = ((current["_order_total"] - previous["_order_total"]) / previous["_order_total"] * 100) if previous["_order_total"] > 0 else 0
        order_growth = ((current["id"] - previous["id"]) / previous["id"] * 100) if previous["id"] > 0 else 0

        return GrowthMetrics(
            sales_growth_percent=sales_growth,
            order_growth_percent=order_growth,
            client_growth_percent=0,  # Would need historical client data
            profit_growth_percent=sales_growth * 0.8,  # Estimate
            expense_growth_percent=0,
        )

    def _calculate_monthly_trends(self, orders_df: pd.DataFrame) -> list[dict]:
        """Calculate monthly trends for trajectory charts."""
        date_col = None
        for col in ["created_at", "order_date", "payment_date"]:
            if col in orders_df.columns:
                date_col = col
                break

        if date_col is None:
            return []

        orders_df = orders_df.copy()
        orders_df["_date"] = pd.to_datetime(orders_df[date_col], errors="coerce")
        orders_df = orders_df.dropna(subset=["_date"])

        if orders_df.empty:
            return []

        # Add numeric columns safely
        if "order_total" in orders_df.columns:
            orders_df["_order_total"] = pd.to_numeric(orders_df["order_total"], errors="coerce").fillna(0)
        else:
            orders_df["_order_total"] = 0.0

        if "payment_amount" in orders_df.columns:
            orders_df["_payment_amount"] = pd.to_numeric(orders_df["payment_amount"], errors="coerce").fillna(0)
        else:
            orders_df["_payment_amount"] = 0.0

        if "remaining_amount" in orders_df.columns:
            orders_df["_remaining"] = pd.to_numeric(orders_df["remaining_amount"], errors="coerce").fillna(0)
        else:
            orders_df["_remaining"] = 0.0

        # Group by month
        orders_df["_year"] = orders_df["_date"].dt.year
        orders_df["_month"] = orders_df["_date"].dt.month
        orders_df["_month_name"] = orders_df["_date"].dt.strftime("%b")

        monthly = orders_df.groupby(["_year", "_month", "_month_name"]).agg({
            "_order_total": "sum",
            "_payment_amount": "sum",
            "_remaining": "sum",
            "id": "count",
            "doctor_id": "nunique",
        }).reset_index()

        trends = []
        for _, row in monthly.iterrows():
            total_sales = row["_order_total"]
            paid = row["_payment_amount"]
            completion = (paid / total_sales * 100) if total_sales > 0 else 0
            avg_order = total_sales / row["id"] if row["id"] > 0 else 0

            trends.append({
                "year": int(row["_year"]),
                "month": row["_month_name"],
                "month_num": int(row["_month"]),
                "total_sales": float(total_sales),
                "total_orders": int(row["id"]),
                "total_clients": int(row["doctor_id"]),
                "avg_order_value": float(avg_order),
                "paid_amount": float(paid),
                "pending_amount": float(row["_remaining"]),
                "completion_rate": float(completion),
            })

        # Sort by year and month
        trends.sort(key=lambda x: (x["year"], x["month_num"]))
        return trends

    def _calculate_weekly_trends(self, orders_df: pd.DataFrame) -> list[dict]:
        """Calculate weekly trends for trajectory charts."""
        date_col = None
        for col in ["created_at", "order_date", "payment_date"]:
            if col in orders_df.columns:
                date_col = col
                break

        if date_col is None:
            return []

        orders_df = orders_df.copy()
        orders_df["_date"] = pd.to_datetime(orders_df[date_col], errors="coerce")
        orders_df = orders_df.dropna(subset=["_date"])

        if orders_df.empty:
            return []

        if "order_total" in orders_df.columns:
            orders_df["_order_total"] = pd.to_numeric(orders_df["order_total"], errors="coerce").fillna(0)
        else:
            orders_df["_order_total"] = 0.0
        orders_df["_week"] = orders_df["_date"].dt.isocalendar().week
        orders_df["_year"] = orders_df["_date"].dt.year
        orders_df["_week_start"] = orders_df["_date"].dt.to_period("W").dt.start_time

        weekly = orders_df.groupby(["_year", "_week", "_week_start"]).agg({
            "_order_total": "sum",
            "id": "count",
        }).reset_index()

        trends = []
        for _, row in weekly.iterrows():
            avg_order = row["_order_total"] / row["id"] if row["id"] > 0 else 0
            trends.append({
                "week_start": row["_week_start"].strftime("%Y-%m-%d"),
                "week_num": int(row["_week"]),
                "year": int(row["_year"]),
                "total_sales": float(row["_order_total"]),
                "total_orders": int(row["id"]),
                "avg_order_value": float(avg_order),
            })

        trends.sort(key=lambda x: (x["year"], x["week_num"]))
        return trends[-12:]  # Last 12 weeks

    def _extract_product_name(self, value: Any) -> str:
        """Extract product name from JSON or dict value."""
        if pd.isna(value) or value is None:
            return "Unknown"
        if isinstance(value, dict):
            return value.get("name", "Unknown")
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed.get("name", "Unknown") if isinstance(parsed, dict) else "Unknown"
            except (json.JSONDecodeError, TypeError):
                return "Unknown"
        return "Unknown"

    def _analyze_products(self, orders_df: pd.DataFrame) -> dict:
        """Analyze product performance."""
        orders_df = orders_df.copy()

        # Extract product_name from various sources
        if "product_name" not in orders_df.columns:
            # Try to extract from JSON 'product' column
            if "product" in orders_df.columns:
                orders_df["product_name"] = orders_df["product"].apply(self._extract_product_name)
            # Or join with products table using product_id
            elif "product_id" in orders_df.columns:
                products_df = self.data_frames.get("products")
                if products_df is not None and not products_df.empty and "name" in products_df.columns:
                    product_map = dict(zip(products_df["id"], products_df["name"], strict=False))
                    orders_df["product_name"] = orders_df["product_id"].map(product_map).fillna("Unknown")
                else:
                    orders_df["product_name"] = "Unknown"
            else:
                return {
                    "top_products": [],
                    "product_categories": {},
                }

        # Filter out unknown products for cleaner stats
        orders_with_products = orders_df[orders_df["product_name"] != "Unknown"]
        if orders_with_products.empty:
            return {
                "top_products": [],
                "product_categories": {},
            }

        if "order_total" in orders_with_products.columns:
            orders_with_products["_order_total"] = pd.to_numeric(
                orders_with_products["order_total"], errors="coerce"
            ).fillna(0)
        else:
            orders_with_products["_order_total"] = 0.0

        if "qty" in orders_with_products.columns:
            orders_with_products["_qty"] = pd.to_numeric(
                orders_with_products["qty"], errors="coerce"
            ).fillna(1)
        else:
            orders_with_products["_qty"] = 1

        product_stats = orders_with_products.groupby("product_name").agg({
            "_order_total": "sum",
            "_qty": "sum",
            "id": "count",
        }).reset_index()

        product_stats.columns = ["product_name", "revenue", "qty", "order_count"]
        product_stats = product_stats.sort_values("revenue", ascending=False)

        top_products = []
        for _, row in product_stats.head(10).iterrows():
            top_products.append({
                "name": row["product_name"],
                "revenue": float(row["revenue"]),
                "qty": int(row["qty"]),
                "orders": int(row["order_count"]),
            })

        # Categorize products (simple heuristic)
        categories = {}
        for _, row in product_stats.iterrows():
            name = str(row["product_name"]).lower()
            if any(x in name for x in ["cream", "serum", "skin", "face", "beauty"]):
                cat = "Beauty Products"
            elif any(x in name for x in ["medical", "pharma", "health", "medicine"]):
                cat = "Medical Products"
            else:
                cat = "Other Products"
            categories[cat] = categories.get(cat, 0) + row["revenue"]

        return {
            "top_products": top_products,
            "product_categories": categories,
        }

    def _calculate_product_trajectories(self, orders_df: pd.DataFrame, top_n: int = 5) -> dict:
        """Calculate per-product trajectories showing sales and payments over time.

        Args:
            orders_df: Orders DataFrame
            top_n: Number of top products to track

        Returns:
            Dictionary with product trajectory data for charts
        """
        orders_df = orders_df.copy()

        # Extract product names if not present
        if "product_name" not in orders_df.columns:
            if "product" in orders_df.columns:
                orders_df["product_name"] = orders_df["product"].apply(self._extract_product_name)
            elif "product_id" in orders_df.columns:
                products_df = self.data_frames.get("products")
                if products_df is not None and not products_df.empty and "name" in products_df.columns:
                    product_map = dict(zip(products_df["id"], products_df["name"], strict=False))
                    orders_df["product_name"] = orders_df["product_id"].map(product_map).fillna("Unknown")
                else:
                    return {"product_trajectories": [], "trajectory_labels": []}
            else:
                return {"product_trajectories": [], "trajectory_labels": []}

        # Find date column
        date_col = None
        for col in ["created_at", "order_date", "payment_date"]:
            if col in orders_df.columns:
                date_col = col
                break

        if date_col is None:
            return {"product_trajectories": [], "trajectory_labels": []}

        # Parse dates
        orders_df["_date"] = pd.to_datetime(orders_df[date_col], errors="coerce")
        orders_df = orders_df.dropna(subset=["_date"])
        orders_df = orders_df[orders_df["product_name"] != "Unknown"]

        if orders_df.empty:
            return {"product_trajectories": [], "trajectory_labels": []}

        # Add numeric columns
        if "order_total" in orders_df.columns:
            orders_df["_order_total"] = pd.to_numeric(orders_df["order_total"], errors="coerce").fillna(0)
        else:
            orders_df["_order_total"] = 0.0

        if "payment_amount" in orders_df.columns:
            orders_df["_payment_amount"] = pd.to_numeric(orders_df["payment_amount"], errors="coerce").fillna(0)
        else:
            orders_df["_payment_amount"] = 0.0

        # Get top products by total revenue
        product_totals = orders_df.groupby("product_name")["_order_total"].sum().nlargest(top_n)
        top_product_names = product_totals.index.tolist()

        if not top_product_names:
            return {"product_trajectories": [], "trajectory_labels": []}

        # Filter to top products only
        orders_df = orders_df[orders_df["product_name"].isin(top_product_names)]

        # Group by month
        orders_df["_year_month"] = orders_df["_date"].dt.to_period("M")

        # Get all unique months sorted
        all_months = sorted(orders_df["_year_month"].unique())
        month_labels = [str(m) for m in all_months]

        # Calculate trajectories for each product
        trajectories = []
        for product_name in top_product_names:
            product_orders = orders_df[orders_df["product_name"] == product_name]

            monthly_data = product_orders.groupby("_year_month").agg({
                "_order_total": "sum",
                "_payment_amount": "sum",
                "id": "count",
            }).reindex(all_months, fill_value=0)

            trajectories.append({
                "product_name": product_name,
                "sales": [float(v) for v in monthly_data["_order_total"].values],
                "payments": [float(v) for v in monthly_data["_payment_amount"].values],
                "orders": [int(v) for v in monthly_data["id"].values],
                "total_revenue": float(product_totals.get(product_name, 0)),
            })

        return {
            "product_trajectories": trajectories,
            "trajectory_labels": month_labels,
        }

    def _analyze_payment_methods(self, orders_df: pd.DataFrame) -> dict:
        """Analyze payment methods."""
        if "payment_method" not in orders_df.columns:
            return {"payment_methods": {}}

        orders_df = orders_df.copy()
        if "payment_amount" in orders_df.columns:
            orders_df["_payment_amount"] = pd.to_numeric(orders_df["payment_amount"], errors="coerce").fillna(0)
        else:
            orders_df["_payment_amount"] = 0.0

        method_stats = orders_df.groupby("payment_method").agg({
            "_payment_amount": "sum",
            "id": "count",
        }).reset_index()

        methods = {}
        for _, row in method_stats.iterrows():
            method = str(row["payment_method"]) if pd.notna(row["payment_method"]) else "Unknown"
            methods[method] = {
                "revenue": float(row["_payment_amount"]),
                "count": int(row["id"]),
            }

        return {"payment_methods": methods}

    def _analyze_status_distribution(self, orders_df: pd.DataFrame) -> dict:
        """Analyze order and payment status distribution."""
        result = {
            "order_status_distribution": {},
            "payment_status_distribution": {},
        }

        if "status" in orders_df.columns:
            status_counts = orders_df["status"].value_counts().to_dict()
            result["order_status_distribution"] = {str(k): int(v) for k, v in status_counts.items()}

        if "payment_status" in orders_df.columns:
            payment_counts = orders_df["payment_status"].value_counts().to_dict()
            result["payment_status_distribution"] = {str(k): int(v) for k, v in payment_counts.items()}

        return result

    def _calculate_projections(self, orders_df: pd.DataFrame) -> dict:
        """Calculate future projections based on trends."""
        trends = self._calculate_monthly_trends(orders_df)

        if len(trends) < 3:
            return {
                "projected_monthly_revenue": 0,
                "projected_quarterly_revenue": 0,
                "projected_annual_revenue": 0,
                "growth_trajectory": "insufficient_data",
            }

        # Calculate average growth rate
        growth_rates = []
        for i in range(1, len(trends)):
            prev = trends[i - 1]["total_sales"]
            curr = trends[i]["total_sales"]
            if prev > 0:
                growth_rates.append((curr - prev) / prev)

        if not growth_rates:
            avg_growth = 0
        else:
            avg_growth = sum(growth_rates) / len(growth_rates)

        # Project based on last month
        last_month_revenue = trends[-1]["total_sales"]
        projected_monthly = last_month_revenue * (1 + avg_growth)
        projected_quarterly = projected_monthly * 3 * (1 + avg_growth)
        projected_annual = projected_monthly * 12 * (1 + avg_growth * 2)

        # Determine trajectory
        if avg_growth > 0.1:
            trajectory = "strong_growth"
        elif avg_growth > 0.02:
            trajectory = "moderate_growth"
        elif avg_growth > -0.02:
            trajectory = "stable"
        elif avg_growth > -0.1:
            trajectory = "slight_decline"
        else:
            trajectory = "significant_decline"

        return {
            "projected_monthly_revenue": projected_monthly,
            "projected_quarterly_revenue": projected_quarterly,
            "projected_annual_revenue": projected_annual,
            "growth_trajectory": trajectory,
            "avg_monthly_growth_rate": avg_growth * 100,
        }

    def _process_financial_tracking(self) -> dict:
        """Process financial tracking sheet data if available.

        Returns comprehensive financial KPIs from the manual tracking sheet.
        """
        if not self.financial_data:
            return {}

        # Get month-end records (final monthly data)
        month_ends = self.financial_data.get_month_end_records()
        if not month_ends:
            return {}

        # Get records with actual data
        records_with_data = [
            r for r in month_ends
            if r.medical_products_sales_actual > 0 or r.beauty_products_sales_actual > 0 or r.tp_actual != 0
        ]

        if not records_with_data:
            # Return structure with empty data
            return self._get_empty_financial_tracking()

        latest = records_with_data[-1] if records_with_data else month_ends[-1]

        # === SALES BREAKDOWN ===
        sales_breakdown = {
            "medical_products": {
                "target": latest.medical_products_sales_target,
                "actual": latest.medical_products_sales_actual,
                "variance": latest.medical_products_sales_actual - latest.medical_products_sales_target,
                "achievement_percent": (latest.medical_products_sales_actual / latest.medical_products_sales_target * 100)
                    if latest.medical_products_sales_target > 0 else 0,
            },
            "beauty_products": {
                "target": latest.beauty_products_sales_target,
                "actual": latest.beauty_products_sales_actual,
                "variance": latest.beauty_products_sales_actual - latest.beauty_products_sales_target,
                "achievement_percent": (latest.beauty_products_sales_actual / latest.beauty_products_sales_target * 100)
                    if latest.beauty_products_sales_target > 0 else 0,
            },
            "total": {
                "target": latest.ts_target,
                "actual": latest.ts_calculated,
                "variance": latest.ts_calculated - latest.ts_target,
            },
        }

        # === INVESTMENT BREAKDOWN ===
        investment_breakdown = {
            "founder": {
                "target": latest.founder_investment_target,
                "actual": latest.founder_investment_actual,
            },
            "cofounder": {
                "target": latest.cofounder_investment_target,
                "actual": latest.cofounder_investment_actual,
            },
            "investor": {
                "target": latest.investor_investment_target,
                "actual": latest.investor_investment_actual,
            },
            "importer": {
                "target": latest.importer_investment_target,
                "actual": latest.importer_investment_actual,
            },
            "total": {
                "target": latest.ti_target,
                "actual": latest.ti_calculated,
            },
        }

        # === EXPENSE BREAKDOWN ===
        expense_breakdown = {
            "operating": {
                "target": latest.operating_expenses_target,
                "actual": latest.operating_expenses_actual,
            },
            "marketing_sales": {
                "target": latest.marketing_sales_expenses_target,
                "actual": latest.marketing_sales_expenses_actual,
            },
            "product_costs": {
                "target": latest.product_costs_target,
                "actual": latest.product_costs_actual,
            },
            "salaries_wages": {
                "target": latest.salaries_wages_target,
                "actual": latest.salaries_wages_actual,
            },
            "delivery_logistics": {
                "target": latest.delivery_logistics_target,
                "actual": latest.delivery_logistics_actual,
            },
            "regulatory_compliance": {
                "target": latest.regulatory_compliance_target,
                "actual": latest.regulatory_compliance_actual,
            },
            "other": {
                "target": latest.other_expenses_target,
                "actual": latest.other_expenses_actual,
            },
            "total": {
                "target": latest.te_target,
                "actual": latest.te_calculated,
            },
        }

        # === DOCTOR PRIZES BREAKDOWN ===
        doctor_prizes = {
            "gifts": {
                "target": latest.doctor_prizes_gifts_target,
                "actual": latest.doctor_prizes_gifts_actual,
            },
            "research_products": {
                "target": latest.doctor_prizes_research_products_target,
                "actual": latest.doctor_prizes_research_products_actual,
            },
            "total": {
                "target": latest.pupmpd_target,
                "actual": latest.pupmpd_calculated,
            },
        }

        # === CAPITAL METRICS ===
        capital_metrics = {
            "total_capital_target": latest.tcmc_target,
            "total_capital_actual": latest.tcmc_calculated,
            "capital_to_convert_target": latest.tcmcci_target,
            "capital_to_convert_actual": latest.tcmcci_actual,
            "borrowed_product_cost": latest.tbpc_actual,
            "borrowed_product_paid": latest.tbpp_actual,
            "remaining_borrowed": latest.rbpp_calculated,
        }

        # === CALCULATED KPIs ===
        calculated_kpis = {
            "roi_percent": latest.roi_percent_calculated,
            "profit_margin_percent": latest.profit_margin_percent_calculated,
            "cac": latest.cac_calculated,
            "debt_ratio_percent": latest.debt_ratio_percent_calculated,
            "collection_efficiency_percent": latest.collection_efficiency_percent_calculated,
            "sales_growth_percent": latest.sales_growth_percent_calculated,
            "client_growth_percent": latest.client_growth_percent_calculated,
        }

        # === CLIENTS ===
        client_metrics = {
            "target": latest.tnc_target,
            "actual": latest.tnc_actual,
            "previous_month_target": latest.ncpmt,
            "previous_month_actual": latest.ncpmd,
        }

        # === PROFIT ===
        profit_metrics = {
            "target": latest.tp_target,
            "actual": latest.tp_actual,
            "net_profit_pm": latest.tnppm_calculated,
        }

        # === MONTHLY TRENDS FROM FINANCIAL SHEET ===
        financial_trends = []
        for record in records_with_data[-12:]:  # Last 12 months
            financial_trends.append({
                "period": f"{record.month[:3]} {record.year}",
                "year": record.year,
                "month": record.month,
                "sales": record.ts_calculated,
                "medical_sales": record.medical_products_sales_actual,
                "beauty_sales": record.beauty_products_sales_actual,
                "expenses": record.te_calculated,
                "profit": record.tp_actual,
                "clients": record.tnc_actual,
                "investment": record.ti_calculated,
                "roi_percent": record.roi_percent_calculated,
            })

        # === INVESTMENT TREND ===
        investment_trend = []
        for record in records_with_data[-12:]:
            investment_trend.append({
                "period": f"{record.month[:3]} {record.year}",
                "founder": record.founder_investment_actual,
                "cofounder": record.cofounder_investment_actual,
                "investor": record.investor_investment_actual,
                "importer": record.importer_investment_actual,
                "total": record.ti_calculated,
            })

        # === EXPENSE TREND ===
        expense_trend = []
        for record in records_with_data[-12:]:
            expense_trend.append({
                "period": f"{record.month[:3]} {record.year}",
                "operating": record.operating_expenses_actual,
                "marketing": record.marketing_sales_expenses_actual,
                "product_costs": record.product_costs_actual,
                "salaries": record.salaries_wages_actual,
                "delivery": record.delivery_logistics_actual,
                "regulatory": record.regulatory_compliance_actual,
                "other": record.other_expenses_actual,
                "total": record.te_calculated,
            })

        # === FINANCIAL TRAJECTORY DATA (for charts) ===
        financial_trajectory = self._build_financial_trajectory(records_with_data)

        # === CAPITAL TRAJECTORY (Investment vs Retrieved vs Company Capital) ===
        capital_trajectory = self._build_capital_trajectory(records_with_data)

        # === GOAL PROGRESS DATA ===
        goal_progress = self._build_goal_progress(latest, records_with_data)

        return {
            "has_financial_data": True,
            "period": f"{latest.month} {latest.year}",
            "records_count": len(records_with_data),

            # Core Metrics
            "total_sales": latest.ts_calculated,
            "total_investment": latest.ti_calculated,
            "total_expenses": latest.te_calculated,
            "net_profit": latest.tp_actual,
            "total_clients": latest.tnc_actual,

            # Breakdowns
            "sales_breakdown": sales_breakdown,
            "investment_breakdown": investment_breakdown,
            "expense_breakdown": expense_breakdown,
            "doctor_prizes": doctor_prizes,

            # Metrics
            "capital_metrics": capital_metrics,
            "calculated_kpis": calculated_kpis,
            "client_metrics": client_metrics,
            "profit_metrics": profit_metrics,

            # Trends
            "financial_trends": financial_trends,
            "investment_trend": investment_trend,
            "expense_trend": expense_trend,

            # Target vs Actual Summary
            "target_vs_actual": {
                "sales_achievement": (latest.ts_calculated / latest.ts_target * 100) if latest.ts_target > 0 else 0,
                "expense_variance": latest.te_calculated - latest.te_target,
                "profit_achievement": (latest.tp_actual / latest.tp_target * 100) if latest.tp_target > 0 else 0,
                "client_achievement": (latest.tnc_actual / latest.tnc_target * 100) if latest.tnc_target > 0 else 0,
            },

            # NEW: Trajectory Chart Data
            "financial_trajectory": financial_trajectory,
            "capital_trajectory": capital_trajectory,
            "goal_progress": goal_progress,
        }

    def _build_financial_trajectory(self, records: list) -> dict:
        """Build financial trajectory data for charts.

        Returns data showing actual vs target vs cumulative trends.
        """
        if not records:
            return {"has_data": False}

        labels = []
        sales_actual = []
        sales_target = []
        profit_actual = []
        profit_target = []
        investment_actual = []
        investment_target = []
        expenses_actual = []
        expenses_target = []

        cumulative_investment = 0
        cumulative_profit = 0
        cumulative_sales = 0

        cumulative_investment_list = []
        cumulative_profit_list = []
        cumulative_sales_list = []

        for record in records[-12:]:  # Last 12 months
            labels.append(f"{record.month[:3]} {record.year}")

            # Actual values
            sales_actual.append(round(record.ts_calculated, 2))
            profit_actual.append(round(record.tp_actual, 2))
            investment_actual.append(round(record.ti_calculated, 2))
            expenses_actual.append(round(record.te_calculated, 2))

            # Target values
            sales_target.append(round(record.ts_target, 2))
            profit_target.append(round(record.tp_target, 2))
            investment_target.append(round(record.ti_target, 2))
            expenses_target.append(round(record.te_target, 2))

            # Cumulative values
            cumulative_investment += record.ti_calculated
            cumulative_profit += record.tp_actual
            cumulative_sales += record.ts_calculated

            cumulative_investment_list.append(round(cumulative_investment, 2))
            cumulative_profit_list.append(round(cumulative_profit, 2))
            cumulative_sales_list.append(round(cumulative_sales, 2))

        return {
            "has_data": True,
            "labels": labels,
            "sales": {
                "actual": sales_actual,
                "target": sales_target,
                "cumulative": cumulative_sales_list,
            },
            "profit": {
                "actual": profit_actual,
                "target": profit_target,
                "cumulative": cumulative_profit_list,
            },
            "investment": {
                "actual": investment_actual,
                "target": investment_target,
                "cumulative": cumulative_investment_list,
            },
            "expenses": {
                "actual": expenses_actual,
                "target": expenses_target,
            },
        }

    def _build_capital_trajectory(self, records: list) -> dict:
        """Build capital trajectory showing investment, retrieved, and company capital.

        This shows:
        - Total Investment Done (cumulative investment from all sources)
        - Amount Retrieved (money received back / sales collected)
        - Company Capital (what belongs to company after all payments)
        """
        if not records:
            return {"has_data": False}

        labels = []
        total_invested = []
        money_retrieved = []
        company_capital = []
        outstanding = []
        borrowed_remaining = []

        cumulative_invested = 0
        cumulative_retrieved = 0

        for record in records[-12:]:
            labels.append(f"{record.month[:3]} {record.year}")

            # Cumulative investment
            cumulative_invested += record.ti_calculated
            total_invested.append(round(cumulative_invested, 2))

            # Money retrieved (from TPMRP - money received from payments)
            cumulative_retrieved += record.tpmrp
            money_retrieved.append(round(cumulative_retrieved, 2))

            # Company capital (TCMC - Total Capital Managed by Company)
            company_capital.append(round(record.tcmc_calculated, 2))

            # Outstanding payments (TRPMRP)
            outstanding.append(round(record.trpmrp, 2))

            # Remaining borrowed product value
            borrowed_remaining.append(round(record.rbpp_calculated, 2))

        return {
            "has_data": True,
            "labels": labels,
            "total_invested": total_invested,
            "money_retrieved": money_retrieved,
            "company_capital": company_capital,
            "outstanding": outstanding,
            "borrowed_remaining": borrowed_remaining,
            "summary": {
                "latest_invested": total_invested[-1] if total_invested else 0,
                "latest_retrieved": money_retrieved[-1] if money_retrieved else 0,
                "latest_capital": company_capital[-1] if company_capital else 0,
                "latest_outstanding": outstanding[-1] if outstanding else 0,
            },
        }

    def _build_goal_progress(self, latest, records: list) -> dict:
        """Build goal progress data for multiple financial goals.

        Args:
            latest: Latest financial record
            records: All records with data
        """
        goals = []

        # Sales Goal
        if latest.ts_target > 0:
            goals.append({
                "name": "Monthly Sales Target",
                "target": latest.ts_target,
                "current": latest.ts_calculated,
                "progress_percent": min((latest.ts_calculated / latest.ts_target) * 100, 150),
                "on_track": latest.ts_calculated >= latest.ts_target * 0.8,
                "status": "achieved" if latest.ts_calculated >= latest.ts_target else (
                    "on_track" if latest.ts_calculated >= latest.ts_target * 0.8 else "behind"
                ),
            })

        # Profit Goal
        if latest.tp_target != 0:
            goals.append({
                "name": "Monthly Profit Target",
                "target": latest.tp_target,
                "current": latest.tp_actual,
                "progress_percent": min((latest.tp_actual / latest.tp_target) * 100, 150) if latest.tp_target > 0 else 0,
                "on_track": latest.tp_actual >= latest.tp_target * 0.8,
                "status": "achieved" if latest.tp_actual >= latest.tp_target else (
                    "on_track" if latest.tp_actual >= latest.tp_target * 0.8 else "behind"
                ),
            })

        # Client Acquisition Goal
        if latest.tnc_target > 0:
            goals.append({
                "name": "New Clients Target",
                "target": latest.tnc_target,
                "current": latest.tnc_actual,
                "progress_percent": min((latest.tnc_actual / latest.tnc_target) * 100, 150),
                "on_track": latest.tnc_actual >= latest.tnc_target * 0.8,
                "status": "achieved" if latest.tnc_actual >= latest.tnc_target else (
                    "on_track" if latest.tnc_actual >= latest.tnc_target * 0.8 else "behind"
                ),
            })

        # Investment Goal (monthly)
        if latest.ti_target > 0:
            goals.append({
                "name": "Investment Target",
                "target": latest.ti_target,
                "current": latest.ti_calculated,
                "progress_percent": min((latest.ti_calculated / latest.ti_target) * 100, 150),
                "on_track": latest.ti_calculated >= latest.ti_target * 0.8,
                "status": "achieved" if latest.ti_calculated >= latest.ti_target else "behind",
            })

        # Collection Efficiency Goal (85% target)
        collection_target = 85.0
        collection_actual = latest.collection_efficiency_percent_calculated
        goals.append({
            "name": "Payment Collection Rate",
            "target": collection_target,
            "current": collection_actual,
            "progress_percent": min((collection_actual / collection_target) * 100, 150),
            "on_track": collection_actual >= collection_target * 0.9,
            "status": "achieved" if collection_actual >= collection_target else (
                "on_track" if collection_actual >= collection_target * 0.9 else "behind"
            ),
            "unit": "%",
        })

        # Capital Growth Goal (Total Capital > Total Investment)
        if latest.ti_calculated > 0:
            capital_ratio = (latest.tcmc_calculated / latest.ti_calculated) * 100 if latest.ti_calculated > 0 else 0
            goals.append({
                "name": "Capital Growth (Capital/Investment)",
                "target": 100,  # Capital should at least equal investment
                "current": capital_ratio,
                "progress_percent": min(capital_ratio, 150),
                "on_track": capital_ratio >= 100,
                "status": "achieved" if capital_ratio >= 100 else "behind",
                "unit": "%",
            })

        # Calculate overall stats
        achieved_count = sum(1 for g in goals if g["status"] == "achieved")
        on_track_count = sum(1 for g in goals if g["status"] == "on_track")
        behind_count = sum(1 for g in goals if g["status"] == "behind")

        return {
            "goals": goals,
            "summary": {
                "total_goals": len(goals),
                "achieved": achieved_count,
                "on_track": on_track_count,
                "behind": behind_count,
                "overall_health": "excellent" if achieved_count >= len(goals) * 0.8 else (
                    "good" if (achieved_count + on_track_count) >= len(goals) * 0.7 else "needs_attention"
                ),
            },
        }

    def _get_empty_financial_tracking(self) -> dict:
        """Return empty financial tracking structure."""
        return {
            "has_financial_data": False,
            "period": "N/A",
            "records_count": 0,
            "total_sales": 0.0,
            "total_investment": 0.0,
            "total_expenses": 0.0,
            "net_profit": 0.0,
            "total_clients": 0,
            "sales_breakdown": {},
            "investment_breakdown": {},
            "expense_breakdown": {},
            "doctor_prizes": {},
            "capital_metrics": {},
            "calculated_kpis": {},
            "client_metrics": {},
            "profit_metrics": {},
            "financial_trends": [],
            "investment_trend": [],
            "expense_trend": [],
            "target_vs_actual": {},
            "financial_trajectory": {"has_data": False},
            "capital_trajectory": {"has_data": False},
            "goal_progress": {"goals": [], "summary": {}},
        }

    @property
    def results(self) -> dict:
        """Get analysis results."""
        return self._analysis_results
