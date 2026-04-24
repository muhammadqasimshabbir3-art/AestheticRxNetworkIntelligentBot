"""Analytics module for historical trend analysis, forecasting, and anomaly detection."""

from processes.business_report.analytics.anomaly_detector import AnomalyDetector
from processes.business_report.analytics.comparative_analyzer import ComparativeAnalyzer
from processes.business_report.analytics.forecast_engine import ForecastEngine
from processes.business_report.analytics.trend_analyzer import TrendAnalyzer

__all__ = [
    "AnomalyDetector",
    "ComparativeAnalyzer",
    "ForecastEngine",
    "TrendAnalyzer",
]
