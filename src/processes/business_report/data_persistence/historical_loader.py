"""Historical data loader for trend analysis.

This module provides pandas DataFrame operations for loading
and preparing historical metrics for analytics.
"""

from dataclasses import dataclass
from datetime import date, timedelta

import pandas as pd

from libraries.logger import logger
from processes.business_report.data_persistence.metrics_storage import MetricsStorage


@dataclass
class HistoricalData:
    """Container for historical metrics data."""

    df: pd.DataFrame
    start_date: date | None
    end_date: date | None
    days_available: int
    has_data: bool

    @property
    def is_sufficient(self) -> bool:
        """Check if we have enough data for meaningful analysis (7+ days)."""
        return self.days_available >= 7


class HistoricalLoader:
    """Loads and prepares historical metrics for analysis."""

    # Minimum days needed for different analyses
    MIN_DAYS_FOR_TRENDS = 7
    MIN_DAYS_FOR_FORECAST = 14
    MIN_DAYS_FOR_ANOMALY = 30

    def __init__(self, storage: MetricsStorage | None = None) -> None:
        """Initialize the historical loader.

        Args:
            storage: MetricsStorage instance. Creates new one if not provided.
        """
        self._storage = storage or MetricsStorage()
        self._cached_data: HistoricalData | None = None
        self._cache_date: date | None = None

    @property
    def storage(self) -> MetricsStorage:
        """Get the underlying storage instance."""
        return self._storage

    def load_historical_data(
        self,
        days: int = 90,
        force_refresh: bool = False,
    ) -> HistoricalData:
        """Load historical metrics data.

        Args:
            days: Number of days to load
            force_refresh: If True, bypass cache

        Returns:
            HistoricalData container with DataFrame and metadata
        """
        today = date.today()

        # Check cache
        if not force_refresh and self._cached_data and self._cache_date == today:
            if self._cached_data.days_available >= days:
                logger.debug("Using cached historical data")
                return self._cached_data

        logger.info(f"Loading historical data for last {days} days...")

        df = self._storage.get_latest_n_days(days)

        if df.empty:
            logger.warning("No historical data available")
            return HistoricalData(
                df=df,
                start_date=None,
                end_date=None,
                days_available=0,
                has_data=False,
            )

        # Get date range
        date_range = self._storage.get_date_range()
        start_date, end_date = date_range

        historical_data = HistoricalData(
            df=df,
            start_date=start_date,
            end_date=end_date,
            days_available=len(df),
            has_data=len(df) > 0,
        )

        # Cache the result
        self._cached_data = historical_data
        self._cache_date = today

        logger.info(f"✓ Loaded {len(df)} days of historical data")
        if start_date and end_date:
            logger.info(f"  Date range: {start_date} to {end_date}")

        return historical_data

    def get_metric_history(
        self,
        metric_name: str,
        days: int = 30,
    ) -> pd.Series:
        """Get historical values for a single metric.

        Args:
            metric_name: Name of the metric column
            days: Number of days

        Returns:
            pandas Series with metric values indexed by date
        """
        return self._storage.get_metric_series(metric_name, days)

    def get_yesterday_metrics(self) -> dict | None:
        """Get metrics from yesterday.

        Returns:
            Dictionary of metrics or None
        """
        yesterday = date.today() - timedelta(days=1)
        return self._storage.get_metrics_for_date(yesterday)

    def get_last_week_metrics(self) -> pd.DataFrame:
        """Get metrics from the last 7 days.

        Returns:
            DataFrame with last week's metrics
        """
        return self._storage.get_latest_n_days(7)

    def get_previous_week_metrics(self) -> pd.DataFrame:
        """Get metrics from 8-14 days ago (the week before last).

        Returns:
            DataFrame with previous week's metrics
        """
        end_date = date.today() - timedelta(days=8)
        start_date = end_date - timedelta(days=6)
        return self._storage.get_metrics_range(start_date, end_date)

    def get_same_day_last_week(self) -> dict | None:
        """Get metrics from exactly 7 days ago.

        Returns:
            Dictionary of metrics or None
        """
        last_week = date.today() - timedelta(days=7)
        return self._storage.get_metrics_for_date(last_week)

    def get_same_day_last_month(self) -> dict | None:
        """Get metrics from approximately 30 days ago.

        Returns:
            Dictionary of metrics or None
        """
        last_month = date.today() - timedelta(days=30)
        return self._storage.get_metrics_for_date(last_month)

    def get_month_to_date_metrics(self) -> pd.DataFrame:
        """Get all metrics from the current month.

        Returns:
            DataFrame with month-to-date metrics
        """
        today = date.today()
        month_start = today.replace(day=1)
        return self._storage.get_metrics_range(month_start, today)

    def get_previous_month_metrics(self) -> pd.DataFrame:
        """Get all metrics from the previous month.

        Returns:
            DataFrame with previous month's metrics
        """
        today = date.today()
        month_start = today.replace(day=1)
        prev_month_end = month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        return self._storage.get_metrics_range(prev_month_start, prev_month_end)

    def can_analyze_trends(self) -> bool:
        """Check if we have enough data for trend analysis.

        Returns:
            True if sufficient data exists
        """
        return self._storage.get_date_count() >= self.MIN_DAYS_FOR_TRENDS

    def can_forecast(self) -> bool:
        """Check if we have enough data for forecasting.

        Returns:
            True if sufficient data exists
        """
        return self._storage.get_date_count() >= self.MIN_DAYS_FOR_FORECAST

    def can_detect_anomalies(self) -> bool:
        """Check if we have enough data for anomaly detection.

        Returns:
            True if sufficient data exists
        """
        return self._storage.get_date_count() >= self.MIN_DAYS_FOR_ANOMALY

    def get_data_quality_summary(self) -> dict:
        """Get a summary of historical data quality.

        Returns:
            Dictionary with data quality metrics
        """
        date_count = self._storage.get_date_count()
        date_range = self._storage.get_date_range()
        start_date, end_date = date_range

        # Calculate expected days if we have a range
        expected_days = 0
        coverage = 0.0
        if start_date and end_date:
            expected_days = (end_date - start_date).days + 1
            coverage = (date_count / expected_days * 100) if expected_days > 0 else 0.0

        return {
            "total_days": date_count,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "expected_days": expected_days,
            "coverage_percent": round(coverage, 1),
            "can_analyze_trends": self.can_analyze_trends(),
            "can_forecast": self.can_forecast(),
            "can_detect_anomalies": self.can_detect_anomalies(),
        }

    def prepare_for_analysis(
        self,
        df: pd.DataFrame,
        fill_missing: bool = True,
    ) -> pd.DataFrame:
        """Prepare DataFrame for analysis by handling missing values.

        Args:
            df: Input DataFrame
            fill_missing: If True, forward-fill missing values

        Returns:
            Cleaned DataFrame ready for analysis
        """
        if df.empty:
            return df

        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex) and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)

        # Sort by date
        df.sort_index(inplace=True)

        # Handle missing values
        if fill_missing:
            # Forward fill then backward fill for remaining
            df = df.ffill().bfill()

        # Drop metadata columns if present
        drop_cols = ["created_at", "updated_at"]
        df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

        return df

    def get_comparison_data(self) -> dict:
        """Get data structured for period comparisons.

        Returns:
            Dictionary with comparison periods
        """
        return {
            "yesterday": self.get_yesterday_metrics(),
            "last_week_same_day": self.get_same_day_last_week(),
            "last_month_same_day": self.get_same_day_last_month(),
            "this_week": self.get_last_week_metrics(),
            "previous_week": self.get_previous_week_metrics(),
            "month_to_date": self.get_month_to_date_metrics(),
            "previous_month": self.get_previous_month_metrics(),
        }

