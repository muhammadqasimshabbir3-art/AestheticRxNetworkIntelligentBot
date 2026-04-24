"""Comparative analysis for period-over-period comparisons.

This module provides side-by-side comparison of different time periods,
ranking of days by performance, and percentile calculations.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd

from libraries.logger import logger
from processes.business_report.data_persistence.historical_loader import HistoricalLoader


@dataclass
class PeriodComparison:
    """Comparison between two periods."""

    metric: str
    current_value: float
    previous_value: float
    absolute_change: float
    percent_change: float
    improved: bool


@dataclass
class RankedDay:
    """A day ranked by a specific metric."""

    date: date
    value: float
    rank: int
    percentile: float


class ComparativeAnalyzer:
    """Analyzes metrics across different time periods."""

    # Key metrics for comparison
    KEY_METRICS = [
        "revenue_total",
        "orders_total",
        "users_total",
        "doctors_total",
        "collection_rate",
        "avg_order_value",
        "completion_rate",
    ]

    def __init__(self, historical_loader: HistoricalLoader) -> None:
        """Initialize the comparative analyzer.

        Args:
            historical_loader: Loader for historical data
        """
        self._loader = historical_loader

    def analyze(self, current_metrics: dict | None = None) -> dict[str, Any]:
        """Run full comparative analysis.

        Args:
            current_metrics: Today's metrics for comparison

        Returns:
            Dictionary with comparison results
        """
        logger.info("Running comparative analysis...")

        result = {
            "has_data": False,
            "today_vs_yesterday": {},
            "today_vs_last_week": {},
            "today_vs_last_month": {},
            "this_week_vs_last_week": {},
            "month_to_date": {},
            "rankings": {},
            "percentiles": {},
        }

        # Get comparison data
        comparison_data = self._loader.get_comparison_data()

        # Today vs Yesterday
        yesterday = comparison_data.get("yesterday")
        if yesterday and current_metrics:
            result["today_vs_yesterday"] = self._compare_dicts(current_metrics, yesterday, "Today vs Yesterday")
            result["has_data"] = True

        # Today vs Same Day Last Week
        last_week_same_day = comparison_data.get("last_week_same_day")
        if last_week_same_day and current_metrics:
            result["today_vs_last_week"] = self._compare_dicts(
                current_metrics, last_week_same_day, "Today vs Last Week"
            )

        # Today vs Same Day Last Month
        last_month_same_day = comparison_data.get("last_month_same_day")
        if last_month_same_day and current_metrics:
            result["today_vs_last_month"] = self._compare_dicts(
                current_metrics, last_month_same_day, "Today vs Last Month"
            )

        # This Week vs Last Week (aggregate)
        this_week_df = comparison_data.get("this_week")
        prev_week_df = comparison_data.get("previous_week")
        if (
            isinstance(this_week_df, pd.DataFrame)
            and isinstance(prev_week_df, pd.DataFrame)
            and not this_week_df.empty
            and not prev_week_df.empty
        ):
            result["this_week_vs_last_week"] = self._compare_aggregates(
                this_week_df, prev_week_df, "This Week vs Last Week"
            )

        # Month-to-date progress
        mtd_df = comparison_data.get("month_to_date")
        prev_month_df = comparison_data.get("previous_month")
        if isinstance(mtd_df, pd.DataFrame) and not mtd_df.empty:
            result["month_to_date"] = self._calculate_mtd_progress(mtd_df, prev_month_df)

        # Rankings
        historical = self._loader.load_historical_data(days=90)
        if historical.has_data:
            df = self._loader.prepare_for_analysis(historical.df)
            for metric in self.KEY_METRICS:
                if metric in df.columns:
                    result["rankings"][metric] = self._rank_days_by_metric(df, metric)
                    if current_metrics and metric in current_metrics:
                        result["percentiles"][metric] = self._calculate_percentile(df, metric, current_metrics[metric])

        logger.info("✓ Comparative analysis complete")
        return result

    def _compare_dicts(
        self,
        current: dict,
        previous: dict,
        label: str,
    ) -> dict[str, Any]:
        """Compare two metric dictionaries.

        Args:
            current: Current period metrics
            previous: Previous period metrics
            label: Label for the comparison

        Returns:
            Dictionary with comparison results
        """
        comparisons = {}

        for metric in self.KEY_METRICS:
            current_val = self._get_numeric(current, metric)
            previous_val = self._get_numeric(previous, metric)

            if current_val is None or previous_val is None:
                continue

            abs_change = current_val - previous_val
            pct_change = ((abs_change / previous_val) * 100) if previous_val != 0 else 0

            comparisons[metric] = {
                "current": current_val,
                "previous": previous_val,
                "absolute_change": round(abs_change, 2),
                "percent_change": round(pct_change, 2),
                "improved": abs_change > 0,
                "direction": "up" if abs_change > 0 else ("down" if abs_change < 0 else "flat"),
            }

        return {
            "label": label,
            "metrics": comparisons,
            "summary": self._summarize_comparison(comparisons),
        }

    def _compare_aggregates(
        self,
        current_df: pd.DataFrame,
        previous_df: pd.DataFrame,
        label: str,
    ) -> dict[str, Any]:
        """Compare aggregated metrics from two DataFrames.

        Args:
            current_df: Current period data
            previous_df: Previous period data
            label: Label for the comparison

        Returns:
            Dictionary with comparison results
        """
        comparisons = {}

        for metric in self.KEY_METRICS:
            if metric not in current_df.columns or metric not in previous_df.columns:
                continue

            # Use sum for counts, mean for rates
            if "rate" in metric or "avg" in metric:
                current_val = current_df[metric].mean()
                previous_val = previous_df[metric].mean()
            else:
                current_val = current_df[metric].sum()
                previous_val = previous_df[metric].sum()

            if pd.isna(current_val) or pd.isna(previous_val):
                continue

            abs_change = current_val - previous_val
            pct_change = ((abs_change / previous_val) * 100) if previous_val != 0 else 0

            comparisons[metric] = {
                "current": round(current_val, 2),
                "previous": round(previous_val, 2),
                "absolute_change": round(abs_change, 2),
                "percent_change": round(pct_change, 2),
                "improved": abs_change > 0,
                "current_days": len(current_df),
                "previous_days": len(previous_df),
            }

        return {
            "label": label,
            "metrics": comparisons,
            "summary": self._summarize_comparison(comparisons),
        }

    def _calculate_mtd_progress(
        self,
        mtd_df: pd.DataFrame,
        prev_month_df: pd.DataFrame | None,
    ) -> dict[str, Any]:
        """Calculate month-to-date progress.

        Args:
            mtd_df: Month-to-date data
            prev_month_df: Previous month data (full month)

        Returns:
            Dictionary with MTD progress
        """
        today = date.today()
        days_elapsed = today.day
        days_in_month = 31  # Approximation

        result = {
            "days_elapsed": days_elapsed,
            "days_remaining": days_in_month - days_elapsed,
            "progress_percent": round((days_elapsed / days_in_month) * 100, 1),
            "metrics": {},
        }

        for metric in self.KEY_METRICS:
            if metric not in mtd_df.columns:
                continue

            # Calculate MTD total/average
            if "rate" in metric or "avg" in metric:
                mtd_value = mtd_df[metric].mean()
            else:
                mtd_value = mtd_df[metric].sum()

            metric_result = {
                "mtd_value": round(mtd_value, 2) if not pd.isna(mtd_value) else 0,
            }

            # Compare to previous month if available
            if isinstance(prev_month_df, pd.DataFrame) and metric in prev_month_df.columns:
                if "rate" in metric or "avg" in metric:
                    prev_value = prev_month_df[metric].mean()
                else:
                    prev_value = prev_month_df[metric].sum()

                if not pd.isna(prev_value) and prev_value > 0:
                    # Project full month based on current pace
                    daily_avg = mtd_value / days_elapsed if days_elapsed > 0 else 0
                    projected_month = daily_avg * days_in_month

                    metric_result.update(
                        {
                            "prev_month_value": round(prev_value, 2),
                            "projected_month": round(projected_month, 2),
                            "vs_prev_month_pct": round((projected_month / prev_value - 1) * 100, 1),
                            "on_track": projected_month >= prev_value,
                        }
                    )

            result["metrics"][metric] = metric_result

        return result

    def _rank_days_by_metric(
        self,
        df: pd.DataFrame,
        metric: str,
        top_n: int = 10,
    ) -> dict[str, Any]:
        """Rank days by a specific metric.

        Args:
            df: Historical data
            metric: Metric to rank by
            top_n: Number of top days to return

        Returns:
            Dictionary with rankings
        """
        if metric not in df.columns:
            return {}

        series = df[metric].dropna()
        if series.empty:
            return {}

        # Sort descending
        ranked = series.sort_values(ascending=False)

        top_days = []
        for i, (idx, value) in enumerate(ranked.head(top_n).items()):
            if isinstance(idx, pd.Timestamp):
                date_str = idx.strftime("%Y-%m-%d")
            else:
                date_str = str(idx)

            top_days.append(
                {
                    "rank": i + 1,
                    "date": date_str,
                    "value": round(value, 2),
                }
            )

        return {
            "top_days": top_days,
            "total_days": len(series),
            "max_value": round(series.max(), 2),
            "min_value": round(series.min(), 2),
            "mean_value": round(series.mean(), 2),
        }

    def _calculate_percentile(
        self,
        df: pd.DataFrame,
        metric: str,
        current_value: float,
    ) -> dict[str, Any]:
        """Calculate where a value ranks percentile-wise.

        Args:
            df: Historical data
            metric: Metric name
            current_value: Value to rank

        Returns:
            Dictionary with percentile info
        """
        if metric not in df.columns:
            return {}

        series = df[metric].dropna()
        if series.empty:
            return {}

        # Count how many values are below current
        below_count = (series < current_value).sum()
        percentile = (below_count / len(series)) * 100

        return {
            "percentile": round(percentile, 1),
            "rank": len(series) - below_count + 1,
            "total_days": len(series),
            "is_top_10_pct": percentile >= 90,
            "is_bottom_10_pct": percentile <= 10,
        }

    def _summarize_comparison(self, comparisons: dict) -> dict[str, Any]:
        """Summarize a set of comparisons.

        Args:
            comparisons: Dictionary of metric comparisons

        Returns:
            Summary statistics
        """
        if not comparisons:
            return {}

        improved_count = sum(1 for c in comparisons.values() if c.get("improved"))
        declined_count = sum(
            1 for c in comparisons.values() if not c.get("improved") and c.get("percent_change", 0) != 0
        )

        return {
            "total_metrics": len(comparisons),
            "improved": improved_count,
            "declined": declined_count,
            "unchanged": len(comparisons) - improved_count - declined_count,
            "overall_sentiment": "positive"
            if improved_count > declined_count
            else ("negative" if declined_count > improved_count else "neutral"),
        }

    def _get_numeric(self, d: dict, key: str) -> float | None:
        """Safely get a numeric value from a dictionary.

        Args:
            d: Dictionary
            key: Key to retrieve

        Returns:
            Numeric value or None
        """
        val = d.get(key)
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def compare_specific_dates(
        self,
        date1: date,
        date2: date,
    ) -> dict[str, Any]:
        """Compare metrics between two specific dates.

        Args:
            date1: First date
            date2: Second date

        Returns:
            Comparison results
        """
        metrics1 = self._loader.storage.get_metrics_for_date(date1)
        metrics2 = self._loader.storage.get_metrics_for_date(date2)

        if not metrics1 or not metrics2:
            return {"error": "Data not available for one or both dates"}

        return self._compare_dicts(metrics1, metrics2, f"{date1.isoformat()} vs {date2.isoformat()}")
