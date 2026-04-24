"""Order Analyzer - Analytics for orders, payments, and delivery.

This module analyzes order data including:
- Order volume by status
- Revenue breakdown
- Payment status distribution
- Delivery performance
- Top selling products
"""

from typing import TYPE_CHECKING, Any

from libraries.logger import logger

if TYPE_CHECKING:
    from processes.business_report.data_loader import DataLoader


class OrderAnalyzer:
    """Analyzes order and revenue data."""

    def __init__(self, data_loader: "DataLoader") -> None:
        """Initialize the analyzer.

        Args:
            data_loader: DataLoader instance with loaded CSV data.
        """
        self._loader = data_loader

    def analyze(self) -> dict[str, Any]:
        """Run all order analytics.

        Returns:
            Dictionary containing all order analytics.
        """
        logger.info("Running order analytics...")

        results = {
            # Basic counts
            "total_orders": self._count_orders(),
            "completed_orders": self._count_completed_orders(),
            "pending_orders": self._count_pending_orders(),
            "cancelled_orders": self._count_cancelled_orders(),
            # Revenue metrics
            "total_revenue": self._calculate_total_revenue(),
            "paid_revenue": self._calculate_paid_revenue(),
            "pending_revenue": self._calculate_pending_revenue(),
            "average_order_value": self._calculate_average_order_value(),
            # Status distributions
            "order_status_distribution": self._get_order_status_distribution(),
            "payment_status_distribution": self._get_payment_status_distribution(),
            "payment_method_distribution": self._get_payment_method_distribution(),
            # Delivery metrics
            "delivery_status_distribution": self._get_delivery_status_distribution(),
            "deliveries_completed": self._count_deliveries_completed(),
            "deliveries_pending": self._count_deliveries_pending(),
            # Products
            "top_products": self._get_top_products(),
            "total_products": self._count_products(),
            # Trends
            "orders_by_date": self._get_orders_by_date(),
            "revenue_by_date": self._get_revenue_by_date(),
        }

        logger.info(f"  ✓ Orders: {results['total_orders']}, Revenue: {results['total_revenue']:,.2f}")
        return results

    def _count_orders(self) -> int:
        """Count total orders."""
        return len(self._loader.orders)

    def _count_completed_orders(self) -> int:
        """Count completed orders."""
        orders = self._loader.orders
        if orders.empty or "status" not in orders.columns:
            return 0
        return len(orders[orders["status"] == "completed"])

    def _count_pending_orders(self) -> int:
        """Count pending orders."""
        orders = self._loader.orders
        if orders.empty or "status" not in orders.columns:
            return 0
        return len(orders[orders["status"] == "pending"])

    def _count_cancelled_orders(self) -> int:
        """Count cancelled orders."""
        orders = self._loader.orders
        if orders.empty or "status" not in orders.columns:
            return 0
        return len(orders[orders["status"] == "cancelled"])

    def _calculate_total_revenue(self) -> float:
        """Calculate total revenue from all orders."""
        orders = self._loader.orders
        if orders.empty or "order_total" not in orders.columns:
            return 0.0
        return float(orders["order_total"].sum())

    def _calculate_paid_revenue(self) -> float:
        """Calculate revenue from paid orders."""
        orders = self._loader.orders
        if orders.empty:
            return 0.0

        if "payment_status" in orders.columns and "payment_amount" in orders.columns:
            paid = orders[orders["payment_status"].isin(["paid", "completed", "success"])]
            return float(paid["payment_amount"].sum())

        if "payment_amount" in orders.columns:
            return float(orders["payment_amount"].sum())

        return 0.0

    def _calculate_pending_revenue(self) -> float:
        """Calculate revenue from pending orders."""
        orders = self._loader.orders
        if orders.empty:
            return 0.0

        if "payment_status" in orders.columns and "order_total" in orders.columns:
            pending = orders[orders["payment_status"].isin(["pending", "unpaid"])]
            return float(pending["order_total"].sum())

        return 0.0

    def _calculate_average_order_value(self) -> float:
        """Calculate average order value."""
        orders = self._loader.orders
        if orders.empty or "order_total" not in orders.columns:
            return 0.0
        total = orders["order_total"].sum()
        count = len(orders)
        if count == 0:
            return 0.0
        return round(float(total / count), 2)

    def _get_order_status_distribution(self) -> dict[str, int]:
        """Get distribution of orders by status."""
        orders = self._loader.orders
        if orders.empty or "status" not in orders.columns:
            return {}

        distribution = orders["status"].value_counts().to_dict()
        return {str(k): int(v) for k, v in distribution.items() if k and str(k) != "nan"}

    def _get_payment_status_distribution(self) -> dict[str, int]:
        """Get distribution of orders by payment status."""
        orders = self._loader.orders
        if orders.empty or "payment_status" not in orders.columns:
            return {}

        distribution = orders["payment_status"].value_counts().to_dict()
        return {str(k): int(v) for k, v in distribution.items() if k and str(k) != "nan"}

    def _get_payment_method_distribution(self) -> dict[str, int]:
        """Get distribution of orders by payment method."""
        orders = self._loader.orders
        if orders.empty or "payment_method" not in orders.columns:
            return {}

        distribution = orders["payment_method"].value_counts().to_dict()
        return {str(k): int(v) for k, v in distribution.items() if k and str(k) != "nan"}

    def _get_delivery_status_distribution(self) -> dict[str, int]:
        """Get distribution of delivery statuses."""
        delivery = self._loader.get("delivery_tracking")
        if delivery.empty:
            # Fall back to orders delivery_status
            orders = self._loader.orders
            if orders.empty or "delivery_status" not in orders.columns:
                return {}
            distribution = orders["delivery_status"].value_counts().to_dict()
        else:
            if "status" in delivery.columns:
                distribution = delivery["status"].value_counts().to_dict()
            else:
                return {}

        return {str(k): int(v) for k, v in distribution.items() if k and str(k) != "nan"}

    def _count_deliveries_completed(self) -> int:
        """Count completed deliveries."""
        orders = self._loader.orders
        if orders.empty or "delivery_status" not in orders.columns:
            return 0
        return len(orders[orders["delivery_status"] == "completed"])

    def _count_deliveries_pending(self) -> int:
        """Count pending deliveries."""
        orders = self._loader.orders
        if orders.empty or "delivery_status" not in orders.columns:
            return 0
        return len(orders[orders["delivery_status"] == "pending"])

    def _get_top_products(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top selling products."""
        import pandas as pd

        orders = self._loader.orders
        if orders.empty or "product_id" not in orders.columns:
            return []

        orders = orders.copy()

        # Ensure order_total is numeric
        if "order_total" in orders.columns:
            orders["order_total"] = pd.to_numeric(orders["order_total"], errors="coerce").fillna(0)
        else:
            orders["order_total"] = 0.0

        # Handle qty column - may not exist in regex-extracted data
        if "qty" in orders.columns:
            orders["qty"] = pd.to_numeric(orders["qty"], errors="coerce").fillna(1)
        else:
            orders["qty"] = 1

        # Group by product_id and count
        product_counts = (
            orders.groupby("product_id")
            .agg(
                order_count=("id", "count"),
                total_qty=("qty", "sum"),
                total_revenue=("order_total", "sum"),
            )
            .reset_index()
        )

        top_products = product_counts.nlargest(limit, "total_revenue")

        # Try to get product names from products table
        products = self._loader.products
        product_names = {}
        if not products.empty and "id" in products.columns and "name" in products.columns:
            product_names = dict(zip(products["id"], products["name"], strict=False))

        # Also check if orders have product_name column (from regex extraction)
        if "product_name" in orders.columns:
            order_product_names = dict(zip(orders["product_id"], orders["product_name"], strict=False))
            product_names.update(order_product_names)

        return [
            {
                "product_id": row["product_id"],
                "product_name": product_names.get(row["product_id"], "Unknown"),
                "order_count": int(row["order_count"]),
                "total_qty": int(row["total_qty"]),
                "total_revenue": float(row["total_revenue"]),
            }
            for _, row in top_products.iterrows()
        ]

    def _count_products(self) -> int:
        """Count total products."""
        return len(self._loader.products)

    def _get_orders_by_date(self) -> dict[str, int]:
        """Get orders grouped by date."""
        import pandas as pd

        orders = self._loader.orders
        if orders.empty or "created_at" not in orders.columns:
            return {}

        orders_with_date = orders[orders["created_at"].notna()].copy()
        if orders_with_date.empty:
            return {}

        # Ensure created_at is datetime
        if not pd.api.types.is_datetime64_any_dtype(orders_with_date["created_at"]):
            orders_with_date["created_at"] = pd.to_datetime(orders_with_date["created_at"], errors="coerce", utc=True)
            orders_with_date = orders_with_date[orders_with_date["created_at"].notna()]
            if orders_with_date.empty:
                return {}

        orders_with_date["date"] = orders_with_date["created_at"].dt.date
        by_date = orders_with_date.groupby("date").size()

        return {str(k): int(v) for k, v in by_date.items()}

    def _get_revenue_by_date(self) -> dict[str, float]:
        """Get revenue grouped by date."""
        import pandas as pd

        orders = self._loader.orders
        if orders.empty or "created_at" not in orders.columns or "order_total" not in orders.columns:
            return {}

        orders_with_date = orders[orders["created_at"].notna()].copy()
        if orders_with_date.empty:
            return {}

        # Ensure created_at is datetime
        if not pd.api.types.is_datetime64_any_dtype(orders_with_date["created_at"]):
            orders_with_date["created_at"] = pd.to_datetime(orders_with_date["created_at"], errors="coerce", utc=True)
            orders_with_date = orders_with_date[orders_with_date["created_at"].notna()]
            if orders_with_date.empty:
                return {}

        orders_with_date["date"] = orders_with_date["created_at"].dt.date
        by_date = orders_with_date.groupby("date")["order_total"].sum()

        return {str(k): float(v) for k, v in by_date.items()}
