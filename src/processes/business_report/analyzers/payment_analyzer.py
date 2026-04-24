"""Payment Analyzer for Business Report.

Analyzes payment data including:
- Payment status breakdown
- Payment methods distribution
- Revenue by payment method
- Payment completion rates
- Top paying doctors
"""

from typing import Any

import pandas as pd

from libraries.logger import logger


class PaymentAnalyzer:
    """Analyzes payment and revenue data from orders."""

    def __init__(self, data_frames: dict[str, pd.DataFrame]) -> None:
        """Initialize with loaded data frames."""
        self.data_frames = data_frames
        self.results: dict[str, Any] = {}

    def analyze(self) -> dict[str, Any]:
        """Run payment analysis and return results."""
        logger.info("Running payment analytics...")

        self.results = {
            "payment_status_breakdown": {},
            "payment_method_breakdown": {},
            "revenue_by_method": {},
            "total_revenue": 0.0,
            "total_paid_amount": 0.0,
            "total_pending_amount": 0.0,
            "payment_completion_rate": 0.0,
            "avg_order_value": 0.0,
            "top_paying_doctors": [],
            "recent_payments": [],
            "daily_revenue": [],
            "payment_trends": {},
        }

        self._analyze_payment_status()
        self._analyze_payment_methods()
        self._analyze_revenue()
        self._analyze_top_doctors()
        self._analyze_recent_payments()
        self._analyze_daily_revenue()

        return self.results

    def _analyze_payment_status(self) -> None:
        """Analyze payment status distribution."""
        orders_df = self.data_frames.get("orders")
        if orders_df is None or orders_df.empty:
            return

        # Payment status breakdown
        if "payment_status" in orders_df.columns:
            status_counts = orders_df["payment_status"].value_counts().to_dict()
            self.results["payment_status_breakdown"] = status_counts

            # Calculate completion rate
            total = len(orders_df)
            paid = status_counts.get("paid", 0) + status_counts.get("success", 0)
            if total > 0:
                self.results["payment_completion_rate"] = round((paid / total) * 100, 2)

    def _analyze_payment_methods(self) -> None:
        """Analyze payment method distribution."""
        orders_df = self.data_frames.get("orders")
        if orders_df is None or orders_df.empty:
            return

        if "payment_method" in orders_df.columns:
            # Clean payment methods
            orders_df["payment_method_clean"] = orders_df["payment_method"].fillna("unknown").str.lower()
            method_counts = orders_df["payment_method_clean"].value_counts().to_dict()
            self.results["payment_method_breakdown"] = method_counts

            # Revenue by payment method
            if "payment_amount" in orders_df.columns:
                orders_df["payment_amount_num"] = pd.to_numeric(orders_df["payment_amount"], errors="coerce").fillna(0)
                revenue_by_method = orders_df.groupby("payment_method_clean")["payment_amount_num"].sum().to_dict()
                self.results["revenue_by_method"] = {k: round(v, 2) for k, v in revenue_by_method.items()}

    def _analyze_revenue(self) -> None:
        """Analyze total revenue and order values."""
        orders_df = self.data_frames.get("orders")
        if orders_df is None or orders_df.empty:
            return

        # Convert amounts to numeric
        if "payment_amount" in orders_df.columns:
            orders_df["payment_amount_num"] = pd.to_numeric(orders_df["payment_amount"], errors="coerce").fillna(0)

        if "order_total" in orders_df.columns:
            orders_df["order_total_num"] = pd.to_numeric(orders_df["order_total"], errors="coerce").fillna(0)

        # Total revenue from paid orders
        if "payment_status" in orders_df.columns and "payment_amount_num" in orders_df.columns:
            paid_orders = orders_df[orders_df["payment_status"].isin(["paid", "success"])]
            self.results["total_paid_amount"] = round(paid_orders["payment_amount_num"].sum(), 2)

            pending_orders = orders_df[orders_df["payment_status"].isin(["pending", "unpaid"])]
            self.results["total_pending_amount"] = round(
                pending_orders["order_total_num"].sum() if "order_total_num" in orders_df.columns else 0, 2
            )

        # Total revenue from all orders
        if "order_total_num" in orders_df.columns:
            self.results["total_revenue"] = round(orders_df["order_total_num"].sum(), 2)
            if len(orders_df) > 0:
                self.results["avg_order_value"] = round(orders_df["order_total_num"].mean(), 2)

    def _analyze_top_doctors(self) -> None:
        """Analyze top paying doctors."""
        orders_df = self.data_frames.get("orders")
        if orders_df is None or orders_df.empty:
            return

        if "doctor_id" not in orders_df.columns:
            return

        # Convert amounts
        if "payment_amount" in orders_df.columns:
            orders_df["payment_amount_num"] = pd.to_numeric(orders_df["payment_amount"], errors="coerce").fillna(0)

        # Get paid orders grouped by doctor
        if "payment_status" in orders_df.columns:
            paid_orders = orders_df[orders_df["payment_status"].isin(["paid", "success"])]

            if not paid_orders.empty and "payment_amount_num" in paid_orders.columns:
                doctor_revenue = (
                    paid_orders.groupby("doctor_id")
                    .agg({"payment_amount_num": "sum", "id": "count"})
                    .rename(columns={"id": "order_count", "payment_amount_num": "total_paid"})
                )

                doctor_revenue = doctor_revenue.sort_values("total_paid", ascending=False).head(10)

                # Try to get doctor names from the doctor column (JSON)
                top_doctors = []
                for doctor_id, row in doctor_revenue.iterrows():
                    doctor_info = {
                        "doctor_id": doctor_id,
                        "total_paid": round(row["total_paid"], 2),
                        "order_count": int(row["order_count"]),
                    }

                    # Try to extract doctor name from the orders data
                    doctor_orders = paid_orders[paid_orders["doctor_id"] == doctor_id]
                    if "doctor" in doctor_orders.columns and not doctor_orders.empty:
                        try:
                            import json

                            doctor_data = doctor_orders.iloc[0]["doctor"]
                            if isinstance(doctor_data, str):
                                doctor_json = json.loads(doctor_data)
                                doctor_info["doctor_name"] = doctor_json.get("doctor_name", "Unknown")
                                doctor_info["clinic_name"] = doctor_json.get("clinic_name", "Unknown")
                                doctor_info["tier"] = doctor_json.get("tier", "Unknown")
                        except (json.JSONDecodeError, TypeError, KeyError):
                            doctor_info["doctor_name"] = "Unknown"

                    top_doctors.append(doctor_info)

                self.results["top_paying_doctors"] = top_doctors

    def _analyze_recent_payments(self) -> None:
        """Analyze recent completed payments."""
        orders_df = self.data_frames.get("orders")
        if orders_df is None or orders_df.empty:
            return

        if "payment_completed_at" not in orders_df.columns:
            return

        # Filter paid orders with completion date
        paid_orders = orders_df[orders_df["payment_status"].isin(["paid", "success"])].copy()
        if paid_orders.empty:
            return

        # Parse dates
        paid_orders["payment_completed_at_dt"] = pd.to_datetime(
            paid_orders["payment_completed_at"], errors="coerce", utc=True
        )

        # Sort by date and get recent
        recent = (
            paid_orders.dropna(subset=["payment_completed_at_dt"])
            .sort_values("payment_completed_at_dt", ascending=False)
            .head(10)
        )

        recent_payments = []
        for _, row in recent.iterrows():
            payment_info = {
                "order_number": row.get("order_number", "N/A"),
                "amount": float(row.get("payment_amount", 0) or 0),
                "method": row.get("payment_method", "unknown"),
                "completed_at": str(row.get("payment_completed_at_dt", ""))[:10]
                if pd.notna(row.get("payment_completed_at_dt"))
                else "N/A",
            }
            recent_payments.append(payment_info)

        self.results["recent_payments"] = recent_payments

    def _analyze_daily_revenue(self) -> None:
        """Analyze daily revenue trends."""
        orders_df = self.data_frames.get("orders")
        if orders_df is None or orders_df.empty:
            return

        if "created_at" not in orders_df.columns:
            return

        # Filter paid orders
        paid_orders = orders_df[orders_df["payment_status"].isin(["paid", "success"])].copy()
        if paid_orders.empty:
            return

        # Parse dates
        paid_orders["created_date"] = pd.to_datetime(paid_orders["created_at"], errors="coerce", utc=True)
        paid_orders["date_only"] = paid_orders["created_date"].dt.date

        # Convert amounts
        paid_orders["payment_amount_num"] = pd.to_numeric(paid_orders["payment_amount"], errors="coerce").fillna(0)

        # Group by date
        daily = (
            paid_orders.groupby("date_only")
            .agg({"payment_amount_num": "sum", "id": "count"})
            .rename(columns={"id": "order_count", "payment_amount_num": "revenue"})
        )

        daily = daily.sort_index(ascending=False).head(30)

        daily_revenue = []
        for date, row in daily.iterrows():
            daily_revenue.append(
                {"date": str(date), "revenue": round(row["revenue"], 2), "order_count": int(row["order_count"])}
            )

        self.results["daily_revenue"] = daily_revenue

        # Calculate trends
        if len(daily_revenue) >= 7:
            last_7_days = sum(r["revenue"] for r in daily_revenue[:7])
            prev_7_days = sum(r["revenue"] for r in daily_revenue[7:14]) if len(daily_revenue) >= 14 else 0

            if prev_7_days > 0:
                trend_pct = round(((last_7_days - prev_7_days) / prev_7_days) * 100, 2)
            else:
                trend_pct = 100.0 if last_7_days > 0 else 0.0

            self.results["payment_trends"] = {
                "last_7_days_revenue": round(last_7_days, 2),
                "prev_7_days_revenue": round(prev_7_days, 2),
                "trend_percentage": trend_pct,
                "trend_direction": "up" if trend_pct > 0 else "down" if trend_pct < 0 else "stable",
            }
