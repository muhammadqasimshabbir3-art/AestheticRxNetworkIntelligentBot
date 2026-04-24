"""Trend analysis for historical metrics.

This module provides trend detection, growth rate calculations,
moving averages, and seasonal pattern identification.
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from libraries.logger import logger
from processes.business_report.data_persistence.historical_loader import HistoricalLoader


@dataclass
class TrendInfo:
    """Information about a metric's trend."""

    direction: str  # "upward", "downward", "sideways"
    strength: float  # 0-1, how strong the trend is
    slope: float  # Slope of the trend line
    r_squared: float  # Goodness of fit
    days_analyzed: int


@dataclass
class GrowthRates:
    """Growth rates for a metric."""

    dod: float  # Day-over-day
    wow: float  # Week-over-week
    mom: float  # Month-over-month
    dod_value: float  # Absolute change DoD
    wow_value: float  # Absolute change WoW
    mom_value: float  # Absolute change MoM


@dataclass
class SeasonalPattern:
    """Day-of-week pattern for a metric."""

    day_averages: dict[str, float]  # Mon-Sun averages
    peak_day: str
    low_day: str
    variance: float


@dataclass
class TrendAnalysisResult:
    """Complete trend analysis result for all metrics."""

    growth_rates: dict[str, GrowthRates] = field(default_factory=dict)
    trends: dict[str, TrendInfo] = field(default_factory=dict)
    moving_averages: dict[str, dict[str, float]] = field(default_factory=dict)
    seasonal_patterns: dict[str, SeasonalPattern] = field(default_factory=dict)
    has_sufficient_data: bool = False


class TrendAnalyzer:
    """Analyzes historical trends in business metrics."""

    # Key metrics to analyze
    KEY_METRICS = [
        "revenue_total",
        "orders_total",
        "users_total",
        "doctors_total",
        "collection_rate",
        "avg_order_value",
        "ads_total",
    ]

    # Moving average windows
    MA_WINDOWS = [7, 14, 30]

    def __init__(self, historical_loader: HistoricalLoader) -> None:
        """Initialize the trend analyzer.

        Args:
            historical_loader: Loader for historical data
        """
        self._loader = historical_loader
        self._df: pd.DataFrame | None = None

    def analyze(self, current_metrics: dict | None = None) -> dict[str, Any]:
        """Run full trend analysis.

        Args:
            current_metrics: Today's metrics for comparison

        Returns:
            Dictionary with trend analysis results
        """
        logger.info("Running trend analysis...")

        # Load historical data
        historical_data = self._loader.load_historical_data(days=90)

        if not historical_data.has_data:
            logger.warning("Insufficient data for trend analysis")
            return self._empty_result()

        self._df = self._loader.prepare_for_analysis(historical_data.df)

        if self._df.empty:
            return self._empty_result()

        result = {
            "has_data": True,
            "days_analyzed": len(self._df),
            "date_range": {
                "start": historical_data.start_date.isoformat() if historical_data.start_date else None,
                "end": historical_data.end_date.isoformat() if historical_data.end_date else None,
            },
            "growth_rates": {},
            "trends": {},
            "moving_averages": {},
            "seasonal_patterns": {},
            "current_vs_average": {},
        }

        for metric in self.KEY_METRICS:
            if metric not in self._df.columns:
                continue

            series = self._df[metric].dropna()
            if len(series) < 7:
                continue

            # Calculate growth rates
            growth = self._calculate_growth_rates(metric, current_metrics)
            if growth:
                result["growth_rates"][metric] = growth

            # Identify trend
            trend = self._identify_trend(series)
            if trend:
                result["trends"][metric] = trend

            # Calculate moving averages
            mas = self._calculate_moving_averages(series)
            if mas:
                result["moving_averages"][metric] = mas

            # Detect seasonal patterns
            pattern = self._detect_seasonal_pattern(series)
            if pattern:
                result["seasonal_patterns"][metric] = pattern

            # Current vs average comparison
            if current_metrics and metric in current_metrics:
                current_val = current_metrics.get(metric, 0)
                avg_30d = series.tail(30).mean() if len(series) >= 30 else series.mean()
                result["current_vs_average"][metric] = {
                    "current": current_val,
                    "avg_30d": avg_30d,
                    "diff_percent": ((current_val - avg_30d) / avg_30d * 100) if avg_30d else 0,
                }

        logger.info(f"✓ Analyzed {len(result['growth_rates'])} metrics")
        return result

    def _calculate_growth_rates(
        self,
        metric: str,
        current_metrics: dict | None = None,
    ) -> dict | None:
        """Calculate day-over-day, week-over-week, month-over-month growth.

        Args:
            metric: Metric name
            current_metrics: Today's metrics

        Returns:
            Dictionary with growth rates
        """
        if self._df is None or metric not in self._df.columns:
            return None

        series = self._df[metric].dropna()
        if len(series) < 2:
            return None

        # Get current value
        if current_metrics and metric in current_metrics:
            current_val = current_metrics[metric]
        else:
            current_val = series.iloc[-1] if len(series) > 0 else 0

        # Yesterday (1 day ago)
        yesterday_val = series.iloc[-2] if len(series) >= 2 else current_val

        # Week ago
        week_ago_val = series.iloc[-8] if len(series) >= 8 else series.iloc[0]

        # Month ago
        month_ago_val = series.iloc[-31] if len(series) >= 31 else series.iloc[0]

        def calc_growth(new: float, old: float) -> float:
            if old == 0:
                return 0.0
            return round((new - old) / old * 100, 2)

        return {
            "dod": calc_growth(current_val, yesterday_val),
            "wow": calc_growth(current_val, week_ago_val),
            "mom": calc_growth(current_val, month_ago_val),
            "dod_value": round(current_val - yesterday_val, 2),
            "wow_value": round(current_val - week_ago_val, 2),
            "mom_value": round(current_val - month_ago_val, 2),
            "current": current_val,
            "yesterday": yesterday_val,
            "week_ago": week_ago_val,
            "month_ago": month_ago_val,
        }

    def _identify_trend(self, series: pd.Series, window: int = 7) -> dict | None:
        """Identify trend direction using linear regression.

        Args:
            series: Time series data
            window: Number of days to analyze

        Returns:
            Dictionary with trend info
        """
        if len(series) < window:
            return None

        # Use recent data for trend
        recent = series.tail(window)
        x = np.arange(len(recent))
        y = recent.values

        # Simple linear regression
        try:
            # Calculate slope
            x_mean = x.mean()
            y_mean = y.mean()
            numerator = np.sum((x - x_mean) * (y - y_mean))
            denominator = np.sum((x - x_mean) ** 2)

            if denominator == 0:
                slope = 0
            else:
                slope = numerator / denominator

            # Calculate R-squared
            y_pred = slope * x + (y_mean - slope * x_mean)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - y_mean) ** 2)

            if ss_tot == 0:
                r_squared = 0
            else:
                r_squared = 1 - (ss_res / ss_tot)

            # Determine direction
            threshold = 0.01 * y_mean if y_mean != 0 else 0.01
            if slope > threshold:
                direction = "upward"
            elif slope < -threshold:
                direction = "downward"
            else:
                direction = "sideways"

            # Strength based on R-squared
            strength = min(abs(r_squared), 1.0)

            return {
                "direction": direction,
                "strength": round(strength, 3),
                "slope": round(slope, 4),
                "r_squared": round(r_squared, 4),
                "days_analyzed": window,
            }

        except Exception as e:
            logger.debug(f"Error calculating trend: {e}")
            return None

    def _calculate_moving_averages(self, series: pd.Series) -> dict | None:
        """Calculate moving averages for different windows.

        Args:
            series: Time series data

        Returns:
            Dictionary with MA values
        """
        result = {}

        for window in self.MA_WINDOWS:
            if len(series) >= window:
                ma = series.rolling(window=window).mean().iloc[-1]
                result[f"ma_{window}d"] = round(ma, 2) if not pd.isna(ma) else None

        return result if result else None

    def _detect_seasonal_pattern(self, series: pd.Series) -> dict | None:
        """Detect day-of-week patterns in the data.

        Args:
            series: Time series data with DatetimeIndex

        Returns:
            Dictionary with seasonal pattern info
        """
        if len(series) < 14:  # Need at least 2 weeks
            return None

        try:
            # Group by day of week
            series_with_dow = series.copy()

            if isinstance(series_with_dow.index, pd.DatetimeIndex):
                dow = series_with_dow.index.dayofweek
            else:
                return None

            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_averages = {}

            for i, day_name in enumerate(day_names):
                mask = dow == i
                if mask.any():
                    day_averages[day_name] = round(series_with_dow[mask].mean(), 2)
                else:
                    day_averages[day_name] = 0

            # Find peak and low days
            if day_averages:
                peak_day = max(day_averages, key=day_averages.get)
                low_day = min(day_averages, key=day_averages.get)
                variance = round(np.var(list(day_averages.values())), 2)
            else:
                peak_day = "Unknown"
                low_day = "Unknown"
                variance = 0

            return {
                "day_averages": day_averages,
                "peak_day": peak_day,
                "low_day": low_day,
                "variance": variance,
            }

        except Exception as e:
            logger.debug(f"Error detecting seasonal pattern: {e}")
            return None

    def get_trend_summary(self) -> dict:
        """Get a summary of trends for dashboard display.

        Returns:
            Dictionary with trend summary
        """
        result = self.analyze()

        summary = {
            "metrics_analyzed": len(result.get("growth_rates", {})),
            "upward_trends": 0,
            "downward_trends": 0,
            "sideways_trends": 0,
        }

        for _metric, trend in result.get("trends", {}).items():
            direction = trend.get("direction", "sideways")
            if direction == "upward":
                summary["upward_trends"] += 1
            elif direction == "downward":
                summary["downward_trends"] += 1
            else:
                summary["sideways_trends"] += 1

        return summary

    def _empty_result(self) -> dict:
        """Return empty result when insufficient data."""
        return {
            "has_data": False,
            "days_analyzed": 0,
            "date_range": {"start": None, "end": None},
            "growth_rates": {},
            "trends": {},
            "moving_averages": {},
            "seasonal_patterns": {},
            "current_vs_average": {},
        }
