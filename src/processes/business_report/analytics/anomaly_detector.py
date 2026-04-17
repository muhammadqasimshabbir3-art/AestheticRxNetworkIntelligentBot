"""Anomaly detection for business metrics.

This module provides statistical anomaly detection using Z-score
and IQR methods, threshold-based alerts, and pattern deviation detection.
"""

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any

import pandas as pd

from libraries.logger import logger
from processes.business_report.data_persistence.historical_loader import HistoricalLoader
from processes.business_report.data_persistence.metrics_storage import MetricsStorage


class AlertSeverity(Enum):
    """Severity levels for alerts."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of anomaly alerts."""

    ZSCORE_HIGH = "zscore_high"
    ZSCORE_LOW = "zscore_low"
    IQR_OUTLIER = "iqr_outlier"
    THRESHOLD_BREACH = "threshold_breach"
    PATTERN_DEVIATION = "pattern_deviation"
    SUDDEN_CHANGE = "sudden_change"


@dataclass
class Alert:
    """An anomaly alert."""

    date: date
    alert_type: AlertType
    severity: AlertSeverity
    metric_name: str
    current_value: float
    expected_value: float
    deviation: float
    message: str


class AnomalyDetector:
    """Detects anomalies in business metrics using statistical methods."""

    # Default thresholds
    DEFAULT_THRESHOLDS = {
        "collection_rate": {"min": 85.0, "critical_min": 75.0},
        "completion_rate": {"min": 80.0, "critical_min": 70.0},
        "approval_rate": {"min": 50.0},
    }

    # Z-score thresholds
    ZSCORE_WARNING = 2.0
    ZSCORE_CRITICAL = 3.0

    # IQR multiplier
    IQR_MULTIPLIER = 1.5

    # Sudden change threshold (percent)
    SUDDEN_CHANGE_THRESHOLD = 50.0

    # Metrics to monitor
    MONITORED_METRICS = [
        "revenue_total",
        "orders_total",
        "users_total",
        "collection_rate",
        "completion_rate",
        "avg_order_value",
    ]

    def __init__(
        self,
        historical_loader: HistoricalLoader,
        storage: MetricsStorage | None = None,
        custom_thresholds: dict | None = None,
    ) -> None:
        """Initialize the anomaly detector.

        Args:
            historical_loader: Loader for historical data
            storage: Optional metrics storage for persisting alerts
            custom_thresholds: Custom threshold configurations
        """
        self._loader = historical_loader
        self._storage = storage
        self._thresholds = {**self.DEFAULT_THRESHOLDS}
        if custom_thresholds:
            self._thresholds.update(custom_thresholds)

    def analyze(self, current_metrics: dict | None = None) -> dict[str, Any]:
        """Run full anomaly detection analysis.

        Args:
            current_metrics: Today's metrics to analyze

        Returns:
            Dictionary with anomaly detection results
        """
        logger.info("Running anomaly detection...")

        result = {
            "has_data": False,
            "alerts": [],
            "anomalies_by_metric": {},
            "anomaly_summary": {},
            "zscore_results": {},
            "iqr_results": {},
            "threshold_breaches": [],
            "pattern_deviations": [],
        }

        # Load historical data
        historical = self._loader.load_historical_data(days=90)
        if not historical.has_data or historical.days_available < 7:
            logger.warning("Insufficient data for anomaly detection")
            return result

        df = self._loader.prepare_for_analysis(historical.df)
        result["has_data"] = True

        all_alerts = []

        for metric in self.MONITORED_METRICS:
            if metric not in df.columns:
                continue

            series = df[metric].dropna()
            if len(series) < 7:
                continue

            current_val = None
            if current_metrics and metric in current_metrics:
                current_val = current_metrics.get(metric)

            # Z-score analysis
            zscore_result = self._detect_zscore_anomaly(series, current_val, metric)
            result["zscore_results"][metric] = zscore_result
            if zscore_result.get("is_anomaly"):
                all_alerts.append(zscore_result["alert"])

            # IQR analysis
            iqr_result = self._detect_iqr_outliers(series, current_val, metric)
            result["iqr_results"][metric] = iqr_result
            if iqr_result.get("is_anomaly") and not zscore_result.get("is_anomaly"):
                # Avoid duplicate alerts
                all_alerts.append(iqr_result["alert"])

            # Threshold checks
            if metric in self._thresholds and current_val is not None:
                threshold_result = self._check_thresholds(metric, current_val)
                if threshold_result.get("breached"):
                    all_alerts.append(threshold_result["alert"])
                    result["threshold_breaches"].append(threshold_result)

            # Pattern deviation
            pattern_result = self._detect_pattern_deviation(series, current_val, metric)
            if pattern_result.get("is_deviation"):
                all_alerts.append(pattern_result["alert"])
                result["pattern_deviations"].append(pattern_result)

            # Sudden change detection
            if current_val is not None:
                sudden_change = self._detect_sudden_change(series, current_val, metric)
                if sudden_change.get("is_sudden"):
                    all_alerts.append(sudden_change["alert"])

        # Store alerts
        result["alerts"] = [self._alert_to_dict(a) for a in all_alerts]

        # Group anomalies by metric
        for alert in all_alerts:
            if alert.metric_name not in result["anomalies_by_metric"]:
                result["anomalies_by_metric"][alert.metric_name] = []
            result["anomalies_by_metric"][alert.metric_name].append(
                self._alert_to_dict(alert)
            )

        # Summary
        result["anomaly_summary"] = {
            "total_alerts": len(all_alerts),
            "critical_alerts": sum(1 for a in all_alerts if a.severity == AlertSeverity.CRITICAL),
            "warning_alerts": sum(1 for a in all_alerts if a.severity == AlertSeverity.WARNING),
            "info_alerts": sum(1 for a in all_alerts if a.severity == AlertSeverity.INFO),
            "metrics_with_anomalies": len(result["anomalies_by_metric"]),
        }

        # Persist alerts to storage
        if self._storage:
            for alert in all_alerts:
                self._storage.store_alert(
                    alert_date=alert.date,
                    alert_type=alert.alert_type.value,
                    metric_name=alert.metric_name,
                    current_value=alert.current_value,
                    threshold_value=alert.expected_value,
                    deviation=alert.deviation,
                    message=alert.message,
                    severity=alert.severity.value,
                )

        logger.info(f"✓ Found {len(all_alerts)} anomalies")
        return result

    def _detect_zscore_anomaly(
        self,
        series: pd.Series,
        current_value: float | None,
        metric_name: str,
    ) -> dict[str, Any]:
        """Detect anomalies using Z-score method.

        Args:
            series: Historical values
            current_value: Current value to check
            metric_name: Name of the metric

        Returns:
            Dictionary with Z-score analysis
        """
        mean = series.mean()
        std = series.std()

        result = {
            "mean": round(mean, 2),
            "std": round(std, 2),
            "is_anomaly": False,
        }

        if std == 0 or current_value is None:
            return result

        zscore = (current_value - mean) / std
        result["zscore"] = round(zscore, 3)

        # Determine if anomaly
        if abs(zscore) >= self.ZSCORE_CRITICAL:
            severity = AlertSeverity.CRITICAL
            result["is_anomaly"] = True
        elif abs(zscore) >= self.ZSCORE_WARNING:
            severity = AlertSeverity.WARNING
            result["is_anomaly"] = True
        else:
            return result

        # Create alert
        direction = "above" if zscore > 0 else "below"
        result["alert"] = Alert(
            date=date.today(),
            alert_type=AlertType.ZSCORE_HIGH if zscore > 0 else AlertType.ZSCORE_LOW,
            severity=severity,
            metric_name=metric_name,
            current_value=current_value,
            expected_value=mean,
            deviation=zscore,
            message=f"{metric_name} is {abs(zscore):.1f}σ {direction} average ({current_value:,.0f} vs avg {mean:,.0f})",
        )

        return result

    def _detect_iqr_outliers(
        self,
        series: pd.Series,
        current_value: float | None,
        metric_name: str,
    ) -> dict[str, Any]:
        """Detect outliers using IQR method.

        Args:
            series: Historical values
            current_value: Current value to check
            metric_name: Name of the metric

        Returns:
            Dictionary with IQR analysis
        """
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - (self.IQR_MULTIPLIER * iqr)
        upper_bound = q3 + (self.IQR_MULTIPLIER * iqr)

        result = {
            "q1": round(q1, 2),
            "q3": round(q3, 2),
            "iqr": round(iqr, 2),
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "is_anomaly": False,
        }

        if current_value is None:
            return result

        if current_value < lower_bound:
            result["is_anomaly"] = True
            deviation = (lower_bound - current_value) / iqr if iqr > 0 else 0
            result["alert"] = Alert(
                date=date.today(),
                alert_type=AlertType.IQR_OUTLIER,
                severity=AlertSeverity.WARNING,
                metric_name=metric_name,
                current_value=current_value,
                expected_value=lower_bound,
                deviation=deviation,
                message=f"{metric_name} ({current_value:,.0f}) below IQR lower bound ({lower_bound:,.0f})",
            )
        elif current_value > upper_bound:
            result["is_anomaly"] = True
            deviation = (current_value - upper_bound) / iqr if iqr > 0 else 0
            result["alert"] = Alert(
                date=date.today(),
                alert_type=AlertType.IQR_OUTLIER,
                severity=AlertSeverity.INFO,  # High values often positive
                metric_name=metric_name,
                current_value=current_value,
                expected_value=upper_bound,
                deviation=deviation,
                message=f"{metric_name} ({current_value:,.0f}) above IQR upper bound ({upper_bound:,.0f})",
            )

        return result

    def _check_thresholds(
        self,
        metric_name: str,
        current_value: float,
    ) -> dict[str, Any]:
        """Check if value breaches defined thresholds.

        Args:
            metric_name: Name of the metric
            current_value: Current value

        Returns:
            Dictionary with threshold check result
        """
        thresholds = self._thresholds.get(metric_name, {})
        result = {"breached": False, "metric": metric_name}

        # Check minimum thresholds
        critical_min = thresholds.get("critical_min")
        warning_min = thresholds.get("min")

        if critical_min is not None and current_value < critical_min:
            result["breached"] = True
            result["threshold_type"] = "critical_min"
            result["threshold_value"] = critical_min
            result["alert"] = Alert(
                date=date.today(),
                alert_type=AlertType.THRESHOLD_BREACH,
                severity=AlertSeverity.CRITICAL,
                metric_name=metric_name,
                current_value=current_value,
                expected_value=critical_min,
                deviation=current_value - critical_min,
                message=f"CRITICAL: {metric_name} ({current_value:.1f}%) below critical threshold ({critical_min}%)",
            )
        elif warning_min is not None and current_value < warning_min:
            result["breached"] = True
            result["threshold_type"] = "warning_min"
            result["threshold_value"] = warning_min
            result["alert"] = Alert(
                date=date.today(),
                alert_type=AlertType.THRESHOLD_BREACH,
                severity=AlertSeverity.WARNING,
                metric_name=metric_name,
                current_value=current_value,
                expected_value=warning_min,
                deviation=current_value - warning_min,
                message=f"WARNING: {metric_name} ({current_value:.1f}%) below threshold ({warning_min}%)",
            )

        # Check maximum thresholds
        critical_max = thresholds.get("critical_max")
        warning_max = thresholds.get("max")

        if critical_max is not None and current_value > critical_max:
            result["breached"] = True
            result["threshold_type"] = "critical_max"
            result["threshold_value"] = critical_max
            result["alert"] = Alert(
                date=date.today(),
                alert_type=AlertType.THRESHOLD_BREACH,
                severity=AlertSeverity.CRITICAL,
                metric_name=metric_name,
                current_value=current_value,
                expected_value=critical_max,
                deviation=current_value - critical_max,
                message=f"CRITICAL: {metric_name} ({current_value:.1f}) above critical threshold ({critical_max})",
            )
        elif warning_max is not None and current_value > warning_max:
            result["breached"] = True
            result["threshold_type"] = "warning_max"
            result["threshold_value"] = warning_max
            result["alert"] = Alert(
                date=date.today(),
                alert_type=AlertType.THRESHOLD_BREACH,
                severity=AlertSeverity.WARNING,
                metric_name=metric_name,
                current_value=current_value,
                expected_value=warning_max,
                deviation=current_value - warning_max,
                message=f"WARNING: {metric_name} ({current_value:.1f}) above threshold ({warning_max})",
            )

        return result

    def _detect_pattern_deviation(
        self,
        series: pd.Series,
        current_value: float | None,
        metric_name: str,
    ) -> dict[str, Any]:
        """Detect deviations from day-of-week patterns.

        Args:
            series: Historical values
            current_value: Current value
            metric_name: Name of the metric

        Returns:
            Dictionary with pattern deviation analysis
        """
        result = {"is_deviation": False}

        if current_value is None or len(series) < 14:
            return result

        # Get day-of-week averages
        if not isinstance(series.index, pd.DatetimeIndex):
            return result

        today_dow = date.today().weekday()
        dow_mask = series.index.dayofweek == today_dow
        same_day_values = series[dow_mask]

        if len(same_day_values) < 2:
            return result

        expected = same_day_values.mean()
        std = same_day_values.std()

        if std == 0:
            return result

        deviation = (current_value - expected) / std

        result["expected"] = round(expected, 2)
        result["deviation_sigma"] = round(deviation, 2)

        # Flag if more than 2 sigma from expected pattern
        if abs(deviation) > 2:
            result["is_deviation"] = True
            direction = "higher" if deviation > 0 else "lower"
            result["alert"] = Alert(
                date=date.today(),
                alert_type=AlertType.PATTERN_DEVIATION,
                severity=AlertSeverity.INFO,
                metric_name=metric_name,
                current_value=current_value,
                expected_value=expected,
                deviation=deviation,
                message=f"{metric_name} is {abs(deviation):.1f}σ {direction} than typical for this day of week",
            )

        return result

    def _detect_sudden_change(
        self,
        series: pd.Series,
        current_value: float,
        metric_name: str,
    ) -> dict[str, Any]:
        """Detect sudden changes from previous value.

        Args:
            series: Historical values
            current_value: Current value
            metric_name: Name of the metric

        Returns:
            Dictionary with sudden change analysis
        """
        result = {"is_sudden": False}

        if len(series) < 2:
            return result

        previous = series.iloc[-1]
        if previous == 0:
            return result

        change_pct = ((current_value - previous) / abs(previous)) * 100
        result["change_pct"] = round(change_pct, 2)

        if abs(change_pct) >= self.SUDDEN_CHANGE_THRESHOLD:
            result["is_sudden"] = True
            direction = "increased" if change_pct > 0 else "decreased"
            severity = AlertSeverity.INFO if change_pct > 0 else AlertSeverity.WARNING
            result["alert"] = Alert(
                date=date.today(),
                alert_type=AlertType.SUDDEN_CHANGE,
                severity=severity,
                metric_name=metric_name,
                current_value=current_value,
                expected_value=previous,
                deviation=change_pct,
                message=f"{metric_name} {direction} {abs(change_pct):.0f}% from yesterday ({previous:,.0f} → {current_value:,.0f})",
            )

        return result

    def _alert_to_dict(self, alert: Alert) -> dict[str, Any]:
        """Convert Alert to dictionary.

        Args:
            alert: Alert object

        Returns:
            Dictionary representation
        """
        return {
            "date": alert.date.isoformat(),
            "type": alert.alert_type.value,
            "severity": alert.severity.value,
            "metric": alert.metric_name,
            "current_value": alert.current_value,
            "expected_value": alert.expected_value,
            "deviation": round(alert.deviation, 3),
            "message": alert.message,
        }

    def get_alert_summary_html(self, alerts: list[dict]) -> str:
        """Generate HTML summary of alerts for report header.

        Args:
            alerts: List of alert dictionaries

        Returns:
            HTML string
        """
        if not alerts:
            return ""

        critical = [a for a in alerts if a.get("severity") == "critical"]
        warnings = [a for a in alerts if a.get("severity") == "warning"]

        html_parts = []

        if critical:
            html_parts.append(
                f'<div class="alert alert-critical">🚨 {len(critical)} Critical Alert(s)</div>'
            )

        if warnings:
            html_parts.append(
                f'<div class="alert alert-warning">⚠️ {len(warnings)} Warning(s)</div>'
            )

        return "\n".join(html_parts)

