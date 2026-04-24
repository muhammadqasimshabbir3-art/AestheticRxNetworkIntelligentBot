"""Forecasting engine for business metrics.

This module provides time series forecasting using multiple methods:
- Simple moving average extrapolation
- Linear regression
- Exponential smoothing (Holt-Winters)
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd

from libraries.logger import logger
from processes.business_report.data_persistence.historical_loader import HistoricalLoader
from processes.business_report.data_persistence.metrics_storage import MetricsStorage

# Try to import advanced libraries
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.debug("statsmodels not available - using simple forecasting")

try:
    from sklearn.linear_model import LinearRegression

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.debug("scikit-learn not available - using simple forecasting")


@dataclass
class Forecast:
    """A single forecast prediction."""

    target_date: date
    predicted_value: float
    confidence_lower: float
    confidence_upper: float
    confidence_level: float = 0.85
    model_used: str = "simple"


@dataclass
class MetricForecast:
    """Forecast results for a single metric."""

    metric_name: str
    forecasts: list[Forecast] = field(default_factory=list)
    model_used: str = "simple"
    model_accuracy: float = 0.0
    historical_mean: float = 0.0
    historical_std: float = 0.0


class ForecastEngine:
    """Generates forecasts for business metrics."""

    # Default forecast horizon
    DEFAULT_HORIZON = 7

    # Metrics to forecast
    FORECASTABLE_METRICS = [
        "revenue_total",
        "orders_total",
        "users_total",
        "doctors_total",
        "avg_order_value",
    ]

    # Confidence level
    DEFAULT_CONFIDENCE = 0.85

    def __init__(
        self,
        historical_loader: HistoricalLoader,
        storage: MetricsStorage | None = None,
    ) -> None:
        """Initialize the forecast engine.

        Args:
            historical_loader: Loader for historical data
            storage: Optional storage for persisting forecasts
        """
        self._loader = historical_loader
        self._storage = storage

    def analyze(self, horizon: int = DEFAULT_HORIZON) -> dict[str, Any]:
        """Generate forecasts for all metrics.

        Args:
            horizon: Number of days to forecast

        Returns:
            Dictionary with forecast results
        """
        logger.info(f"Generating {horizon}-day forecasts...")

        result = {
            "has_data": False,
            "horizon_days": horizon,
            "forecasts_by_metric": {},
            "daily_forecasts": [],
            "historical_data": {},  # Last 14 days of actual data for trajectory chart
            "trajectory_chart_data": {},  # Combined actual + forecast for charting
            "projections": {},
            "goal_tracking": {},
            "model_info": {
                "statsmodels_available": STATSMODELS_AVAILABLE,
                "sklearn_available": SKLEARN_AVAILABLE,
            },
        }

        # Load historical data
        historical = self._loader.load_historical_data(days=90)
        if not historical.has_data or historical.days_available < 14:
            logger.warning("Insufficient data for forecasting (need 14+ days)")
            return result

        df = self._loader.prepare_for_analysis(historical.df)
        result["has_data"] = True

        today = date.today()

        for metric in self.FORECASTABLE_METRICS:
            if metric not in df.columns:
                continue

            series = df[metric].dropna()
            if len(series) < 14:
                continue

            # Generate forecast
            metric_forecast = self._forecast_metric(series, metric, horizon)
            if metric_forecast:
                result["forecasts_by_metric"][metric] = {
                    "forecasts": [self._forecast_to_dict(f) for f in metric_forecast.forecasts],
                    "model_used": metric_forecast.model_used,
                    "historical_mean": metric_forecast.historical_mean,
                    "historical_std": metric_forecast.historical_std,
                }

                # Store forecasts
                if self._storage:
                    for forecast in metric_forecast.forecasts:
                        self._storage.store_forecast(
                            forecast_date=today,
                            target_date=forecast.target_date,
                            metric_name=metric,
                            predicted_value=forecast.predicted_value,
                            confidence_lower=forecast.confidence_lower,
                            confidence_upper=forecast.confidence_upper,
                            confidence_level=forecast.confidence_level,
                            model_used=metric_forecast.model_used,
                        )

        # Create daily forecast table
        result["daily_forecasts"] = self._create_daily_forecast_table(
            result["forecasts_by_metric"],
            horizon,
        )

        # Extract historical data for trajectory chart (last 14 days)
        result["historical_data"] = self._extract_historical_data(df, days=14)

        # Create trajectory chart data (actual + forecast combined)
        result["trajectory_chart_data"] = self._create_trajectory_chart_data(df, result["forecasts_by_metric"], horizon)

        # Calculate monthly projections
        result["projections"] = self._calculate_projections(df)

        # Goal tracking
        result["goal_tracking"] = self._calculate_goal_tracking(df)

        logger.info(f"✓ Generated forecasts for {len(result['forecasts_by_metric'])} metrics")
        return result

    def _forecast_metric(
        self,
        series: pd.Series,
        metric_name: str,
        horizon: int,
    ) -> MetricForecast | None:
        """Generate forecast for a single metric.

        Args:
            series: Historical time series
            metric_name: Name of the metric
            horizon: Forecast horizon in days

        Returns:
            MetricForecast object or None
        """
        # Try Holt-Winters first
        if STATSMODELS_AVAILABLE and len(series) >= 14:
            try:
                return self._holt_winters_forecast(series, metric_name, horizon)
            except Exception as e:
                logger.debug(f"Holt-Winters failed for {metric_name}: {e}")

        # Fall back to linear regression
        if SKLEARN_AVAILABLE:
            try:
                return self._linear_regression_forecast(series, metric_name, horizon)
            except Exception as e:
                logger.debug(f"Linear regression failed for {metric_name}: {e}")

        # Ultimate fallback: simple moving average
        return self._simple_forecast(series, metric_name, horizon)

    def _holt_winters_forecast(
        self,
        series: pd.Series,
        metric_name: str,
        horizon: int,
    ) -> MetricForecast:
        """Generate forecast using Holt-Winters exponential smoothing.

        Args:
            series: Historical time series
            metric_name: Name of the metric
            horizon: Forecast horizon

        Returns:
            MetricForecast object
        """
        # Use additive trend, no seasonality (since we have daily data without clear weekly pattern)
        model = ExponentialSmoothing(
            series.values,
            trend="add",
            seasonal=None,
            damped_trend=True,
        )
        fitted = model.fit(optimized=True)

        # Generate predictions
        predictions = fitted.forecast(horizon)

        # Calculate confidence intervals using residuals
        residuals = series.values - fitted.fittedvalues
        std_residual = np.std(residuals)

        # Z-score for 85% confidence
        z_score = 1.44  # 85% confidence

        today = date.today()
        forecasts = []

        for i, pred in enumerate(predictions):
            target = today + timedelta(days=i + 1)
            # Widen confidence interval as we go further
            interval_width = std_residual * z_score * np.sqrt(1 + i * 0.1)

            forecasts.append(
                Forecast(
                    target_date=target,
                    predicted_value=max(0, round(pred, 2)),
                    confidence_lower=max(0, round(pred - interval_width, 2)),
                    confidence_upper=round(pred + interval_width, 2),
                    confidence_level=self.DEFAULT_CONFIDENCE,
                    model_used="holt_winters",
                )
            )

        return MetricForecast(
            metric_name=metric_name,
            forecasts=forecasts,
            model_used="holt_winters",
            historical_mean=round(series.mean(), 2),
            historical_std=round(series.std(), 2),
        )

    def _linear_regression_forecast(
        self,
        series: pd.Series,
        metric_name: str,
        horizon: int,
    ) -> MetricForecast:
        """Generate forecast using linear regression.

        Args:
            series: Historical time series
            metric_name: Name of the metric
            horizon: Forecast horizon

        Returns:
            MetricForecast object
        """
        X = np.arange(len(series)).reshape(-1, 1)
        y = series.values

        model = LinearRegression()
        model.fit(X, y)

        # Generate predictions
        future_X = np.arange(len(series), len(series) + horizon).reshape(-1, 1)
        predictions = model.predict(future_X)

        # Calculate residual standard error
        residuals = y - model.predict(X)
        std_residual = np.std(residuals)
        z_score = 1.44  # 85% confidence

        today = date.today()
        forecasts = []

        for i, pred in enumerate(predictions):
            target = today + timedelta(days=i + 1)
            interval_width = std_residual * z_score * np.sqrt(1 + i * 0.1)

            forecasts.append(
                Forecast(
                    target_date=target,
                    predicted_value=max(0, round(pred, 2)),
                    confidence_lower=max(0, round(pred - interval_width, 2)),
                    confidence_upper=round(pred + interval_width, 2),
                    confidence_level=self.DEFAULT_CONFIDENCE,
                    model_used="linear_regression",
                )
            )

        return MetricForecast(
            metric_name=metric_name,
            forecasts=forecasts,
            model_used="linear_regression",
            historical_mean=round(series.mean(), 2),
            historical_std=round(series.std(), 2),
        )

    def _simple_forecast(
        self,
        series: pd.Series,
        metric_name: str,
        horizon: int,
    ) -> MetricForecast:
        """Generate forecast using simple moving average.

        Args:
            series: Historical time series
            metric_name: Name of the metric
            horizon: Forecast horizon

        Returns:
            MetricForecast object
        """
        # Use 7-day moving average as prediction
        ma_7 = series.rolling(7).mean().iloc[-1]

        # Calculate trend from last 7 days
        recent = series.tail(7)
        if len(recent) >= 2:
            daily_trend = (recent.iloc[-1] - recent.iloc[0]) / 7
        else:
            daily_trend = 0

        std = series.std()
        z_score = 1.44

        today = date.today()
        forecasts = []

        for i in range(horizon):
            pred = ma_7 + daily_trend * (i + 1)
            target = today + timedelta(days=i + 1)
            interval_width = std * z_score * np.sqrt(1 + i * 0.1)

            forecasts.append(
                Forecast(
                    target_date=target,
                    predicted_value=max(0, round(pred, 2)),
                    confidence_lower=max(0, round(pred - interval_width, 2)),
                    confidence_upper=round(pred + interval_width, 2),
                    confidence_level=self.DEFAULT_CONFIDENCE,
                    model_used="moving_average",
                )
            )

        return MetricForecast(
            metric_name=metric_name,
            forecasts=forecasts,
            model_used="moving_average",
            historical_mean=round(series.mean(), 2),
            historical_std=round(series.std(), 2),
        )

    def _create_daily_forecast_table(
        self,
        forecasts_by_metric: dict,
        horizon: int,
    ) -> list[dict]:
        """Create a table of daily forecasts across all metrics.

        Args:
            forecasts_by_metric: Forecasts by metric
            horizon: Forecast horizon

        Returns:
            List of daily forecast dictionaries
        """
        today = date.today()
        daily = []

        for i in range(horizon):
            target = today + timedelta(days=i + 1)
            day_data = {
                "date": target.isoformat(),
                "day_name": target.strftime("%A"),
                "days_ahead": i + 1,
            }

            for metric, data in forecasts_by_metric.items():
                forecasts = data.get("forecasts", [])
                if i < len(forecasts):
                    f = forecasts[i]
                    day_data[metric] = {
                        "value": f.get("predicted_value"),
                        "lower": f.get("confidence_lower"),
                        "upper": f.get("confidence_upper"),
                    }

            daily.append(day_data)

        return daily

    def _extract_historical_data(
        self,
        df: pd.DataFrame,
        days: int = 14,
    ) -> dict[str, Any]:
        """Extract recent historical data for trajectory visualization.

        Args:
            df: Historical DataFrame
            days: Number of days to extract

        Returns:
            Dictionary with historical data by metric
        """
        historical = {}

        for metric in self.FORECASTABLE_METRICS:
            if metric not in df.columns:
                continue

            series = df[metric].tail(days)
            if series.empty:
                continue

            data_points = []
            for idx, value in series.items():
                if isinstance(idx, pd.Timestamp):
                    date_str = idx.strftime("%Y-%m-%d")
                else:
                    date_str = str(idx)

                data_points.append(
                    {
                        "date": date_str,
                        "value": round(float(value), 2) if not pd.isna(value) else 0,
                    }
                )

            historical[metric] = {
                "data": data_points,
                "mean": round(series.mean(), 2),
                "min": round(series.min(), 2),
                "max": round(series.max(), 2),
            }

        return historical

    def _create_trajectory_chart_data(
        self,
        df: pd.DataFrame,
        forecasts_by_metric: dict,
        horizon: int,
    ) -> dict[str, Any]:
        """Create combined actual + forecast data for trajectory charts.

        Args:
            df: Historical DataFrame
            forecasts_by_metric: Forecast data
            horizon: Forecast horizon

        Returns:
            Dictionary with chart-ready data for each metric
        """
        today = date.today()
        chart_data = {}

        for metric in self.FORECASTABLE_METRICS:
            if metric not in df.columns:
                continue

            # Get last 14 days of actual data
            series = df[metric].tail(14)
            if series.empty:
                continue

            # Build labels (dates)
            labels = []
            actual_values = []
            forecast_values = []
            forecast_lower = []
            forecast_upper = []
            target_values = []

            # Historical data
            for idx, value in series.items():
                if isinstance(idx, pd.Timestamp):
                    date_str = idx.strftime("%m/%d")
                else:
                    date_str = str(idx)[-5:]  # Last 5 chars

                labels.append(date_str)
                actual_values.append(round(float(value), 2) if not pd.isna(value) else None)
                forecast_values.append(None)  # No forecast for historical
                forecast_lower.append(None)
                forecast_upper.append(None)

            # Calculate average as "target" baseline
            avg_value = series.mean()

            # Add target for historical period
            for _ in range(len(actual_values)):
                target_values.append(round(avg_value, 2))

            # Forecast data
            metric_forecasts = forecasts_by_metric.get(metric, {}).get("forecasts", [])
            for i, f in enumerate(metric_forecasts[:horizon]):
                target_date = today + timedelta(days=i + 1)
                labels.append(target_date.strftime("%m/%d"))
                actual_values.append(None)  # No actual for future
                forecast_values.append(f.get("predicted_value", 0))
                forecast_lower.append(f.get("confidence_lower", 0))
                forecast_upper.append(f.get("confidence_upper", 0))
                target_values.append(round(avg_value, 2))  # Extend target line

            chart_data[metric] = {
                "labels": labels,
                "actual": actual_values,
                "forecast": forecast_values,
                "forecast_lower": forecast_lower,
                "forecast_upper": forecast_upper,
                "target": target_values,
                "metric_label": metric.replace("_", " ").title(),
            }

        return chart_data

    def _calculate_projections(self, df: pd.DataFrame) -> dict[str, Any]:
        """Calculate monthly and quarterly projections.

        Args:
            df: Historical data

        Returns:
            Dictionary with projections
        """
        today = date.today()
        days_elapsed = today.day
        days_in_month = 31  # Approximation
        days_remaining = days_in_month - days_elapsed

        projections = {
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "metrics": {},
        }

        for metric in self.FORECASTABLE_METRICS:
            if metric not in df.columns:
                continue

            # Get month-to-date data
            mtd_mask = df.index >= pd.Timestamp(today.replace(day=1))
            mtd_data = df.loc[mtd_mask, metric].dropna()

            if mtd_data.empty:
                continue

            # Calculate
            if "rate" in metric or "avg" in metric:
                mtd_value = mtd_data.mean()
                projected = mtd_value  # Rates don't sum
            else:
                mtd_value = mtd_data.sum()
                daily_avg = mtd_value / days_elapsed if days_elapsed > 0 else 0
                projected = mtd_value + (daily_avg * days_remaining)

            projections["metrics"][metric] = {
                "mtd_value": round(mtd_value, 2),
                "projected_month": round(projected, 2),
                "daily_avg": round(mtd_value / days_elapsed, 2) if days_elapsed > 0 else 0,
            }

        return projections

    def _calculate_goal_tracking(self, df: pd.DataFrame) -> dict[str, Any]:
        """Calculate progress toward goals.

        Args:
            df: Historical data

        Returns:
            Dictionary with goal tracking info
        """
        today = date.today()
        days_elapsed = today.day
        days_remaining = 31 - days_elapsed

        # Example monthly targets (could be loaded from config)
        monthly_targets = {
            "revenue_total": 100_000_000,  # 100M revenue target
            "orders_total": 100,  # 100 orders target
            "users_total": 50,  # 50 new users target
        }

        tracking = {}

        for metric, target in monthly_targets.items():
            if metric not in df.columns:
                continue

            mtd_mask = df.index >= pd.Timestamp(today.replace(day=1))
            mtd_data = df.loc[mtd_mask, metric].dropna()

            if mtd_data.empty:
                continue

            current = mtd_data.sum()
            progress = (current / target) * 100 if target > 0 else 0
            remaining = target - current
            required_daily = remaining / days_remaining if days_remaining > 0 else 0

            tracking[metric] = {
                "target": target,
                "current": round(current, 2),
                "progress_percent": round(progress, 1),
                "remaining": round(remaining, 2),
                "days_remaining": days_remaining,
                "required_daily_avg": round(required_daily, 2),
                "on_track": progress >= (days_elapsed / 31) * 100,
            }

        return tracking

    def _forecast_to_dict(self, forecast: Forecast) -> dict[str, Any]:
        """Convert Forecast object to dictionary.

        Args:
            forecast: Forecast object

        Returns:
            Dictionary representation
        """
        return {
            "target_date": forecast.target_date.isoformat(),
            "predicted_value": forecast.predicted_value,
            "confidence_lower": forecast.confidence_lower,
            "confidence_upper": forecast.confidence_upper,
            "confidence_level": forecast.confidence_level,
            "model_used": forecast.model_used,
        }

    def predict_single_metric(
        self,
        metric_name: str,
        horizon: int = 7,
    ) -> list[dict] | None:
        """Generate forecast for a single metric.

        Args:
            metric_name: Name of the metric
            horizon: Forecast horizon

        Returns:
            List of forecast dictionaries or None
        """
        historical = self._loader.load_historical_data(days=90)
        if not historical.has_data:
            return None

        df = self._loader.prepare_for_analysis(historical.df)
        if metric_name not in df.columns:
            return None

        series = df[metric_name].dropna()
        if len(series) < 14:
            return None

        forecast = self._forecast_metric(series, metric_name, horizon)
        if forecast:
            return [self._forecast_to_dict(f) for f in forecast.forecasts]

        return None
