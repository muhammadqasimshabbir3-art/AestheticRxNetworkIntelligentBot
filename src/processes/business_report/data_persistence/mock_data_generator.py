"""Mock data generator for historical metrics.

This module generates realistic mock historical data for testing
trend analysis, forecasting, and anomaly detection.
"""

import random
from datetime import date, timedelta

import numpy as np

from libraries.logger import logger
from processes.business_report.data_persistence.metrics_storage import MetricsStorage


class MockDataGenerator:
    """Generates realistic mock historical metrics data."""

    # Base values for metrics
    BASE_VALUES = {
        "revenue_total": 80_000_000,  # 80M base
        "revenue_medical": 60_000_000,
        "revenue_beauty": 20_000_000,
        "orders_total": 85,
        "orders_completed": 80,
        "orders_pending": 5,
        "avg_order_value": 950_000,
        "completion_rate": 94.0,
        "users_total": 150,
        "doctors_total": 120,
        "new_signups": 3,
        "approval_rate": 85.0,
        "ads_total": 15,
        "ads_active": 10,
        "ads_pending": 5,
        "collection_rate": 92.0,
        "pending_amount": 5_000_000,
        "research_papers": 25,
        "research_views": 500,
        "research_upvotes": 150,
    }

    # Day of week multipliers (0=Monday, 6=Sunday)
    DOW_MULTIPLIERS = {
        0: 1.0,  # Monday - baseline
        1: 1.05,  # Tuesday - slightly higher
        2: 1.15,  # Wednesday - peak
        3: 1.10,  # Thursday - good
        4: 0.95,  # Friday - slightly lower
        5: 0.75,  # Saturday - lower
        6: 0.65,  # Sunday - lowest
    }

    # Growth rate per day (compound)
    DAILY_GROWTH_RATE = 0.002  # 0.2% daily growth

    # Noise level (standard deviation as % of value)
    NOISE_LEVEL = 0.08  # 8%

    def __init__(self, storage: MetricsStorage | None = None) -> None:
        """Initialize the mock data generator.

        Args:
            storage: MetricsStorage to populate. Creates new one if not provided.
        """
        self._storage = storage or MetricsStorage()
        self._rng = np.random.default_rng(42)  # Seed for reproducibility

    def generate(self, days: int = 90, end_date: date | None = None) -> int:
        """Generate mock historical data.

        Args:
            days: Number of days of data to generate
            end_date: End date for data (defaults to yesterday)

        Returns:
            Number of records generated
        """
        if end_date is None:
            end_date = date.today() - timedelta(days=1)

        start_date = end_date - timedelta(days=days - 1)

        logger.info(f"Generating {days} days of mock data ({start_date} to {end_date})...")

        records_generated = 0

        for i in range(days):
            current_date = start_date + timedelta(days=i)

            # Skip if data already exists
            if self._storage.has_data_for_date(current_date):
                continue

            metrics = self._generate_day_metrics(current_date, i, days)
            success = self._storage.store_daily_metrics(current_date, metrics)

            if success:
                records_generated += 1

        logger.info(f"✓ Generated {records_generated} mock data records")
        return records_generated

    def _generate_day_metrics(
        self,
        target_date: date,
        day_index: int,
        total_days: int,
    ) -> dict:
        """Generate metrics for a single day.

        Args:
            target_date: Date to generate metrics for
            day_index: Index of day from start (0-based)
            total_days: Total days being generated

        Returns:
            Dictionary of metric values
        """
        dow = target_date.weekday()
        dow_mult = self.DOW_MULTIPLIERS[dow]

        # Growth factor (compounding)
        growth_factor = (1 + self.DAILY_GROWTH_RATE) ** day_index

        metrics = {}

        for metric, base_value in self.BASE_VALUES.items():
            # Apply growth
            value = base_value * growth_factor

            # Apply day-of-week pattern (only for volume metrics)
            if metric not in ["completion_rate", "approval_rate", "collection_rate"]:
                value *= dow_mult

            # Add noise
            noise = self._rng.normal(0, self.NOISE_LEVEL * value)
            value += noise

            # Ensure non-negative
            value = max(0, value)

            # Round appropriately
            if metric in ["completion_rate", "approval_rate", "collection_rate"]:
                value = round(min(100, value), 1)  # Rates capped at 100%
            elif "total" in metric or metric in ["new_signups"]:
                value = round(value)
            else:
                value = round(value, 2)

            metrics[metric] = value

        # Ensure logical consistency
        metrics["orders_completed"] = min(metrics["orders_completed"], metrics["orders_total"])
        metrics["orders_pending"] = max(0, metrics["orders_total"] - metrics["orders_completed"])
        metrics["ads_active"] = min(metrics["ads_active"], metrics["ads_total"])
        metrics["ads_pending"] = max(0, metrics["ads_total"] - metrics["ads_active"])

        # Inject anomalies occasionally (for testing detection)
        if random.random() < 0.03:  # 3% chance of anomaly
            self._inject_anomaly(metrics)

        return metrics

    def _inject_anomaly(self, metrics: dict) -> None:
        """Inject an anomaly into the metrics for testing detection.

        Args:
            metrics: Metrics dictionary to modify
        """
        anomaly_type = random.choice(["revenue_spike", "orders_drop", "collection_dip"])

        if anomaly_type == "revenue_spike":
            metrics["revenue_total"] *= 2.5  # 150% increase
            metrics["revenue_medical"] *= 2.0
        elif anomaly_type == "orders_drop":
            metrics["orders_total"] = int(metrics["orders_total"] * 0.3)  # 70% drop
            metrics["orders_completed"] = int(metrics["orders_completed"] * 0.3)
        elif anomaly_type == "collection_dip":
            metrics["collection_rate"] = max(50, metrics["collection_rate"] - 30)

    def clear_all_data(self) -> bool:
        """Clear all mock data from storage.

        WARNING: This deletes all historical data!

        Returns:
            True if cleared successfully
        """
        import sqlite3

        try:
            with sqlite3.connect(self._storage.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM daily_metrics")
                cursor.execute("DELETE FROM alerts_history")
                cursor.execute("DELETE FROM forecasts")
                conn.commit()
                logger.info("✓ Cleared all historical data")
                return True
        except Exception as e:
            logger.error(f"Failed to clear data: {e}")
            return False


def generate_mock_data(days: int = 90) -> int:
    """Convenience function to generate mock data.

    Args:
        days: Number of days to generate

    Returns:
        Number of records generated
    """
    generator = MockDataGenerator()
    return generator.generate(days)


if __name__ == "__main__":
    # Run directly to generate mock data
    import sys

    days = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    generate_mock_data(days)
