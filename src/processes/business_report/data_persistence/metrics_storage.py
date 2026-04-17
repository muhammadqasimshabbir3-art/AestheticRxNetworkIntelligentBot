"""SQLite-based storage for historical metrics.

This module provides persistent storage for daily business metrics,
enabling historical trend analysis and forecasting.
"""

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from config import CONFIG
from libraries.logger import logger
from processes.business_report.data_persistence.schema import ALL_SCHEMAS


class MetricsStorage:
    """Manages SQLite database for storing and retrieving historical metrics."""

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize the metrics storage.

        Args:
            db_path: Path to SQLite database. Defaults to output/metrics_history.db
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = CONFIG.OUTPUT_DIR / "metrics_history.db"

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        logger.info(f"Initializing metrics database at {self.db_path}")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for schema in ALL_SCHEMAS:
                # Split schema into individual statements
                statements = [s.strip() for s in schema.split(";") if s.strip()]
                for statement in statements:
                    try:
                        cursor.execute(statement)
                    except sqlite3.Error as e:
                        logger.warning(f"Schema execution warning: {e}")
            conn.commit()

        logger.info("✓ Metrics database initialized")

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def store_daily_metrics(
        self,
        metrics_date: date,
        metrics: dict[str, Any],
        update_if_exists: bool = True,
    ) -> bool:
        """Store daily metrics to the database.

        Args:
            metrics_date: Date for the metrics
            metrics: Dictionary of metric name -> value
            update_if_exists: If True, update existing record; else skip

        Returns:
            True if stored successfully, False otherwise
        """
        date_str = metrics_date.isoformat() if isinstance(metrics_date, date) else str(metrics_date)

        # Build the INSERT/UPDATE query dynamically
        columns = ["date"]
        values = [date_str]
        placeholders = ["?"]

        for col, value in metrics.items():
            if col != "date":
                columns.append(col)
                values.append(value)
                placeholders.append("?")

        columns_str = ", ".join(columns)
        placeholders_str = ", ".join(placeholders)

        if update_if_exists:
            # Use INSERT OR REPLACE
            query = f"INSERT OR REPLACE INTO daily_metrics ({columns_str}) VALUES ({placeholders_str})"
        else:
            query = f"INSERT OR IGNORE INTO daily_metrics ({columns_str}) VALUES ({placeholders_str})"

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)
                conn.commit()
                logger.debug(f"Stored metrics for {date_str}: {len(metrics)} fields")
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to store metrics for {date_str}: {e}")
            return False

    def get_metrics_for_date(self, metrics_date: date) -> dict[str, Any] | None:
        """Retrieve metrics for a specific date.

        Args:
            metrics_date: Date to retrieve

        Returns:
            Dictionary of metrics or None if not found
        """
        date_str = metrics_date.isoformat() if isinstance(metrics_date, date) else str(metrics_date)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM daily_metrics WHERE date = ?", (date_str,))
                row = cursor.fetchone()

                if row:
                    return dict(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Failed to get metrics for {date_str}: {e}")
            return None

    def get_metrics_range(
        self,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """Get metrics for a date range as a DataFrame.

        Args:
            start_date: Start of range (inclusive)
            end_date: End of range (inclusive)

        Returns:
            DataFrame with metrics, indexed by date
        """
        start_str = start_date.isoformat() if isinstance(start_date, date) else str(start_date)
        end_str = end_date.isoformat() if isinstance(end_date, date) else str(end_date)

        try:
            with self._get_connection() as conn:
                query = """
                    SELECT * FROM daily_metrics
                    WHERE date >= ? AND date <= ?
                    ORDER BY date ASC
                """
                df = pd.read_sql_query(query, conn, params=(start_str, end_str))

                if not df.empty and "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"])
                    df.set_index("date", inplace=True)

                return df
        except (sqlite3.Error, pd.errors.DatabaseError) as e:
            logger.error(f"Failed to get metrics range: {e}")
            return pd.DataFrame()

    def get_latest_n_days(self, n: int = 30) -> pd.DataFrame:
        """Get the last N days of metrics.

        Args:
            n: Number of days to retrieve

        Returns:
            DataFrame with metrics
        """
        try:
            with self._get_connection() as conn:
                query = """
                    SELECT * FROM daily_metrics
                    ORDER BY date DESC
                    LIMIT ?
                """
                df = pd.read_sql_query(query, conn, params=(n,))

                if not df.empty and "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"])
                    df.set_index("date", inplace=True)
                    df.sort_index(inplace=True)  # Chronological order

                return df
        except (sqlite3.Error, pd.errors.DatabaseError) as e:
            logger.error(f"Failed to get latest {n} days: {e}")
            return pd.DataFrame()

    def get_metric_series(
        self,
        metric_name: str,
        days: int = 30,
    ) -> pd.Series:
        """Get a single metric as a time series.

        Args:
            metric_name: Name of the metric column
            days: Number of days to retrieve

        Returns:
            pandas Series with the metric values
        """
        df = self.get_latest_n_days(days)

        if df.empty or metric_name not in df.columns:
            return pd.Series(dtype=float)

        return df[metric_name]

    def has_data_for_date(self, metrics_date: date) -> bool:
        """Check if metrics exist for a specific date.

        Args:
            metrics_date: Date to check

        Returns:
            True if data exists
        """
        return self.get_metrics_for_date(metrics_date) is not None

    def get_date_count(self) -> int:
        """Get the total number of days with stored metrics.

        Returns:
            Count of unique dates
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(DISTINCT date) FROM daily_metrics")
                result = cursor.fetchone()
                return result[0] if result else 0
        except sqlite3.Error:
            return 0

    def get_date_range(self) -> tuple[date | None, date | None]:
        """Get the earliest and latest dates in the database.

        Returns:
            Tuple of (min_date, max_date) or (None, None) if empty
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MIN(date), MAX(date) FROM daily_metrics")
                result = cursor.fetchone()

                if result and result[0] and result[1]:
                    min_date = datetime.fromisoformat(result[0]).date()
                    max_date = datetime.fromisoformat(result[1]).date()
                    return (min_date, max_date)
                return (None, None)
        except sqlite3.Error:
            return (None, None)

    def store_alert(
        self,
        alert_date: date,
        alert_type: str,
        metric_name: str,
        current_value: float,
        threshold_value: float,
        deviation: float,
        message: str,
        severity: str = "warning",
    ) -> bool:
        """Store an alert to the alerts history.

        Args:
            alert_date: Date of the alert
            alert_type: Type of alert (anomaly, threshold, pattern)
            metric_name: Name of the metric that triggered the alert
            current_value: Current metric value
            threshold_value: Threshold that was breached
            deviation: How much the value deviated
            message: Human-readable alert message
            severity: Alert severity (info, warning, critical)

        Returns:
            True if stored successfully
        """
        date_str = alert_date.isoformat() if isinstance(alert_date, date) else str(alert_date)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO alerts_history
                    (date, alert_type, severity, metric_name, current_value,
                     threshold_value, deviation, message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        date_str,
                        alert_type,
                        severity,
                        metric_name,
                        current_value,
                        threshold_value,
                        deviation,
                        message,
                    ),
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to store alert: {e}")
            return False

    def get_recent_alerts(self, days: int = 7) -> list[dict]:
        """Get recent alerts from the database.

        Args:
            days: Number of days to look back

        Returns:
            List of alert dictionaries
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM alerts_history
                    WHERE date >= ?
                    ORDER BY created_at DESC
                    """,
                    (cutoff_date,),
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []

    def store_forecast(
        self,
        forecast_date: date,
        target_date: date,
        metric_name: str,
        predicted_value: float,
        confidence_lower: float,
        confidence_upper: float,
        confidence_level: float = 0.85,
        model_used: str = "holt_winters",
    ) -> bool:
        """Store a forecast prediction.

        Args:
            forecast_date: Date when forecast was made
            target_date: Date being predicted
            metric_name: Metric being forecasted
            predicted_value: Predicted value
            confidence_lower: Lower bound of confidence interval
            confidence_upper: Upper bound of confidence interval
            confidence_level: Confidence level (default 0.85)
            model_used: Name of forecasting model

        Returns:
            True if stored successfully
        """
        forecast_str = forecast_date.isoformat() if isinstance(forecast_date, date) else str(forecast_date)
        target_str = target_date.isoformat() if isinstance(target_date, date) else str(target_date)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO forecasts
                    (forecast_date, target_date, metric_name, predicted_value,
                     confidence_lower, confidence_upper, confidence_level, model_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        forecast_str,
                        target_str,
                        metric_name,
                        predicted_value,
                        confidence_lower,
                        confidence_upper,
                        confidence_level,
                        model_used,
                    ),
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Failed to store forecast: {e}")
            return False

    def extract_metrics_from_analytics(
        self,
        user_analytics: dict,
        order_analytics: dict,
        payment_analytics: dict,
        research_analytics: dict,
        ad_analytics: dict,
        financial_analytics: dict,
        business_kpi_analytics: dict,
    ) -> dict[str, Any]:
        """Extract storable metrics from analyzer results.

        Args:
            Various analytics dictionaries from analyzers

        Returns:
            Dictionary ready for storage
        """
        metrics = {}

        # Revenue metrics
        metrics["revenue_total"] = payment_analytics.get("total_revenue", 0.0)
        metrics["revenue_paid"] = payment_analytics.get("total_paid_amount", 0.0)
        metrics["revenue_pending"] = payment_analytics.get("total_pending_amount", 0.0)

        # Try to get medical/beauty breakdown from business KPIs
        ft = business_kpi_analytics.get("financial_tracking", {})
        if ft:
            sales = ft.get("sales_breakdown", {})
            metrics["revenue_medical"] = sales.get("medical_products", {}).get("actual", 0.0)
            metrics["revenue_beauty"] = sales.get("beauty_products", {}).get("actual", 0.0)

        # Order metrics
        metrics["orders_total"] = order_analytics.get("total_orders", 0)
        metrics["orders_completed"] = order_analytics.get("completed_orders", 0)
        metrics["orders_pending"] = order_analytics.get("pending_orders", 0)
        metrics["orders_cancelled"] = order_analytics.get("cancelled_orders", 0)
        metrics["avg_order_value"] = payment_analytics.get("avg_order_value", 0.0)
        metrics["completion_rate"] = payment_analytics.get("payment_completion_rate", 0.0)

        # User metrics
        metrics["users_total"] = user_analytics.get("total_users", 0)
        metrics["doctors_total"] = user_analytics.get("total_doctors", 0)
        metrics["approved_users"] = user_analytics.get("approved_users", 0)
        metrics["approval_rate"] = user_analytics.get("approval_rate", 0.0)

        # Advertisement metrics
        metrics["ads_total"] = ad_analytics.get("total_ads", 0)
        metrics["ads_active"] = ad_analytics.get("active_ads", 0)
        metrics["ads_pending"] = ad_analytics.get("pending_ads", 0)
        metrics["ads_revenue"] = ad_analytics.get("total_ad_revenue", 0.0)

        # Collection metrics
        metrics["collection_rate"] = business_kpi_analytics.get("collection_rate", 0.0)
        metrics["pending_amount"] = business_kpi_analytics.get("total_pending", 0.0)

        # Research metrics
        metrics["research_papers"] = research_analytics.get("total_papers", 0)
        metrics["research_views"] = research_analytics.get("total_views", 0)
        metrics["research_upvotes"] = research_analytics.get("total_upvotes", 0)

        # Financial tracking KPIs
        if ft and ft.get("has_financial_data"):
            tva = ft.get("target_vs_actual", {})
            kpis = ft.get("calculated_kpis", {})

            metrics["fin_sales_target"] = ft.get("sales_breakdown", {}).get("total", {}).get("target", 0.0)
            metrics["fin_sales_actual"] = ft.get("total_sales", 0.0)
            metrics["fin_sales_achievement"] = tva.get("sales_achievement", 0.0)
            metrics["fin_investment_total"] = ft.get("total_investment", 0.0)
            metrics["fin_expenses_total"] = ft.get("total_expenses", 0.0)
            metrics["fin_profit"] = ft.get("net_profit", 0.0)
            metrics["fin_roi"] = kpis.get("roi_percent", 0.0)
            metrics["fin_profit_margin"] = kpis.get("profit_margin_percent", 0.0)
            metrics["fin_debt_ratio"] = kpis.get("debt_ratio_percent", 0.0)
            metrics["fin_cac"] = kpis.get("cac", 0.0)

        return metrics

