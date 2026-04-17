"""Business Report Process - Entry point for business intelligence reporting.

This module provides the public interface for generating business reports
from exported CSV data with historical trend analysis and forecasting.
"""

import zipfile
from datetime import date
from pathlib import Path
from typing import Any

from config import CONFIG
from libraries.google_drive import GoogleDriveAPI
from libraries.google_sheets import GoogleSheetsAPI
from libraries.logger import logger
from processes.business_report.analyzers import (
    AdvertisementAnalyzer,
    BusinessKPIAnalyzer,
    FinancialAnalyzer,
    OrderAnalyzer,
    PaymentAnalyzer,
    ResearchAnalyzer,
    UserAnalyzer,
)
from processes.business_report.data_loader import DataLoader
from processes.business_report.data_persistence import HistoricalLoader, MetricsStorage
from processes.business_report.financial_tracking_loader import FinancialTrackingLoader
from processes.business_report.report_builder import ReportBuilder


class BusinessReportProcess:
    """Public entry point for the Business Report workflow."""

    def __init__(self, export_zip_path: str | None = None) -> None:
        """Initialize the BusinessReportProcess.

        Args:
            export_zip_path: Path to the export ZIP file. If None, uses the latest export.
        """
        logger.info("=" * 60)
        logger.info("Initializing Business Report Process")
        logger.info("=" * 60)

        self._export_zip_path = export_zip_path
        self._extract_dir: Path | None = None
        self._data_loader: DataLoader | None = None
        self._report_path: str | None = None

        # Analyzers
        self._user_analyzer: UserAnalyzer | None = None
        self._order_analyzer: OrderAnalyzer | None = None
        self._payment_analyzer: PaymentAnalyzer | None = None
        self._research_analyzer: ResearchAnalyzer | None = None
        self._ad_analyzer: AdvertisementAnalyzer | None = None
        self._financial_analyzer: FinancialAnalyzer | None = None
        self._business_kpi_analyzer: BusinessKPIAnalyzer | None = None
        self._financial_tracking_loader: FinancialTrackingLoader | None = None

        # Analysis results
        self.user_analytics: dict = {}
        self.order_analytics: dict = {}
        self.payment_analytics: dict = {}
        self.research_analytics: dict = {}
        self.ad_analytics: dict = {}
        self.financial_analytics: dict = {}
        self.business_kpi_analytics: dict = {}
        self.executive_summary: dict = {}

        # Google APIs
        self._drive_api: GoogleDriveAPI | None = None
        self._sheets_api: GoogleSheetsAPI | None = None
        self._uploaded_file_id: str | None = None
        self._uploaded_file_url: str | None = None

        # Historical data components
        self._metrics_storage: MetricsStorage | None = None
        self._historical_loader: HistoricalLoader | None = None
        self.historical_data: Any | None = None
        self.trend_analytics: dict = {}
        self.forecast_analytics: dict = {}
        self.anomaly_analytics: dict = {}
        self.comparison_analytics: dict = {}

        logger.info("Business Report Process initialized")

    def start(self) -> None:
        """Start the business report generation workflow."""
        logger.info("=" * 60)
        logger.info("Starting Business Report Workflow")
        logger.info("=" * 60)

        # Step 1: Find and extract the export ZIP
        self._find_and_extract_export()

        # Step 2: Load data
        self._load_data()

        # Step 3: Load financial tracking data (from Google Sheet)
        self._load_financial_tracking()

        # Step 4: Run analyzers
        self._run_analyzers()

        # Step 5: Store daily metrics for historical tracking
        self._store_daily_metrics()

        # Step 6: Load historical data
        self._load_historical_data()

        # Step 7: Run historical analytics (trends, forecasts, anomalies)
        self._run_historical_analytics()

        # Step 8: Generate executive summary
        self._generate_executive_summary()

        # Step 9: Generate HTML report
        self._generate_report()

        # Step 10: Upload report to Google Drive
        self._upload_to_drive()

        logger.info("=" * 60)
        logger.info("✅ BUSINESS REPORT WORKFLOW COMPLETED!")
        logger.info("=" * 60)
        if self._report_path:
            logger.info(f"Report generated: {self._report_path}")
        if self._uploaded_file_url:
            logger.info(f"Uploaded to Drive: {self._uploaded_file_url}")

    def _find_and_extract_export(self) -> None:
        """Find the export ZIP file and extract it."""
        logger.info("Finding and extracting export data...")

        exports_dir = CONFIG.OUTPUT_DIR / "exports"

        # Find the ZIP file
        if self._export_zip_path:
            zip_path = Path(self._export_zip_path)
        else:
            # Find the latest export ZIP
            zip_files = list(exports_dir.glob("*.zip"))
            if not zip_files:
                raise FileNotFoundError(f"No export ZIP files found in {exports_dir}")
            zip_path = max(zip_files, key=lambda p: p.stat().st_mtime)

        logger.info(f"Using export: {zip_path.name}")

        # Extract to a directory
        self._extract_dir = exports_dir / "extracted_data"
        self._extract_dir.mkdir(exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(self._extract_dir)

        csv_files = list(self._extract_dir.glob("*.csv"))
        logger.info(f"✓ Extracted {len(csv_files)} CSV files")

    def _load_data(self) -> None:
        """Load data from CSV files."""
        logger.info("Loading data from CSV files...")

        if not self._extract_dir:
            raise RuntimeError("Extract directory not set")

        self._data_loader = DataLoader(self._extract_dir)
        self._data_loader.load_all()

        logger.info("✓ Data loaded successfully")

    def _load_financial_tracking(self) -> None:
        """Load financial tracking data from Google Sheet."""
        logger.info("Loading financial tracking data...")

        if not CONFIG.FINANCIAL_TRACKING_SPREADSHEET_ID:
            logger.info("  No Financial Tracking Sheet configured - skipping")
            logger.info("  Run financial_sheet_setup.py to create one")
            return

        try:
            self._financial_tracking_loader = FinancialTrackingLoader()
            financial_data = self._financial_tracking_loader.load()

            if financial_data.has_data:
                logger.info("✓ Financial tracking data loaded")
            else:
                logger.info("  Financial tracking sheet is empty (no actual data entered)")
        except Exception as e:
            logger.warning(f"  Could not load financial tracking data: {e}")

    def _run_analyzers(self) -> None:
        """Run all business analyzers."""
        logger.info("Running business analyzers...")

        if not self._data_loader:
            raise RuntimeError("Data loader not initialized")

        # User Analytics
        logger.info("  → Analyzing users and doctors...")
        self._user_analyzer = UserAnalyzer(self._data_loader)
        self.user_analytics = self._user_analyzer.analyze()

        # Order Analytics
        logger.info("  → Analyzing orders and revenue...")
        self._order_analyzer = OrderAnalyzer(self._data_loader)
        self.order_analytics = self._order_analyzer.analyze()

        # Payment Analytics
        logger.info("  → Analyzing payments and revenue trends...")
        self._payment_analyzer = PaymentAnalyzer(self._data_loader.data_frames)
        self.payment_analytics = self._payment_analyzer.analyze()
        logger.info(f"  ✓ Revenue: {self.payment_analytics.get('total_paid_amount', 0):,.2f}, "
                    f"Completion: {self.payment_analytics.get('payment_completion_rate', 0)}%")

        # Research Analytics
        logger.info("  → Analyzing research and engagement...")
        self._research_analyzer = ResearchAnalyzer(self._data_loader)
        self.research_analytics = self._research_analyzer.analyze()

        # Advertisement Analytics (with Google Sheet integration for payment data)
        logger.info("  → Analyzing advertisements...")
        if self._sheets_api is None:
            try:
                self._sheets_api = GoogleSheetsAPI()
            except Exception as e:
                logger.warning(f"Could not initialize Google Sheets API: {e}")
        self._ad_analyzer = AdvertisementAnalyzer(self._data_loader, sheets_api=self._sheets_api)
        self.ad_analytics = self._ad_analyzer.analyze()

        # Financial Analytics
        logger.info("  → Analyzing financials...")
        self._financial_analyzer = FinancialAnalyzer(self._data_loader)
        self.financial_analytics = self._financial_analyzer.analyze()

        # Business KPI Analytics (from downloaded data + optional Financial Tracking Sheet)
        logger.info("  → Analyzing business KPIs...")
        financial_data = None
        if self._financial_tracking_loader and self._financial_tracking_loader.data:
            financial_data = self._financial_tracking_loader.data

        self._business_kpi_analyzer = BusinessKPIAnalyzer(
            data_frames=self._data_loader.data_frames,
            financial_data=financial_data,
        )
        self.business_kpi_analytics = self._business_kpi_analyzer.analyze()
        if self.business_kpi_analytics.get("has_data"):
            logger.info(f"  ✓ Business KPIs: Revenue={self.business_kpi_analytics.get('total_revenue', 0):,.0f}, "
                        f"ROI={self.business_kpi_analytics.get('roi_percent', 0):.1f}%")

        logger.info("✓ All analyzers completed")

    def _store_daily_metrics(self) -> None:
        """Store today's metrics to the historical database."""
        logger.info("Storing daily metrics for historical tracking...")

        try:
            # Initialize storage if needed
            if self._metrics_storage is None:
                self._metrics_storage = MetricsStorage()

            # Extract metrics from analyzers
            metrics = self._metrics_storage.extract_metrics_from_analytics(
                user_analytics=self.user_analytics,
                order_analytics=self.order_analytics,
                payment_analytics=self.payment_analytics,
                research_analytics=self.research_analytics,
                ad_analytics=self.ad_analytics,
                financial_analytics=self.financial_analytics,
                business_kpi_analytics=self.business_kpi_analytics,
            )

            # Store for today
            today = date.today()
            success = self._metrics_storage.store_daily_metrics(today, metrics)

            if success:
                logger.info(f"✓ Stored {len(metrics)} metrics for {today}")
            else:
                logger.warning(f"  Failed to store metrics for {today}")

        except Exception as e:
            logger.warning(f"  Could not store daily metrics: {e}")

    def _load_historical_data(self) -> None:
        """Load historical metrics for trend analysis."""
        logger.info("Loading historical data...")

        try:
            # Initialize historical loader if needed
            if self._historical_loader is None:
                if self._metrics_storage is None:
                    self._metrics_storage = MetricsStorage()
                self._historical_loader = HistoricalLoader(self._metrics_storage)

            # Load last 90 days
            self.historical_data = self._historical_loader.load_historical_data(days=90)

            quality = self._historical_loader.get_data_quality_summary()

            if self.historical_data.has_data:
                logger.info(f"✓ Loaded {quality['total_days']} days of historical data")
                logger.info(f"  Coverage: {quality['coverage_percent']}%")
                logger.info(f"  Can analyze trends: {quality['can_analyze_trends']}")
                logger.info(f"  Can forecast: {quality['can_forecast']}")
            else:
                logger.info("  No historical data available yet")
                logger.info("  Run the report daily to build history")

        except Exception as e:
            logger.warning(f"  Could not load historical data: {e}")

    def _run_historical_analytics(self) -> None:
        """Run trend analysis, anomaly detection, and forecasting."""
        logger.info("Running historical analytics...")

        # Check if we have enough data
        if not self.historical_data or not self.historical_data.has_data:
            logger.info("  Insufficient historical data - skipping analytics")
            return

        if not self._historical_loader:
            logger.info("  Historical loader not initialized - skipping analytics")
            return

        try:
            # Import analytics modules (lazy import to handle missing dependencies)
            from processes.business_report.analytics import (
                AnomalyDetector,
                ComparativeAnalyzer,
                ForecastEngine,
                TrendAnalyzer,
            )

            # Get current metrics for comparison
            today = date.today()
            current_metrics = self._metrics_storage.get_metrics_for_date(today) if self._metrics_storage else None

            # Trend Analysis
            if self._historical_loader.can_analyze_trends():
                logger.info("  → Analyzing trends...")
                trend_analyzer = TrendAnalyzer(self._historical_loader)
                self.trend_analytics = trend_analyzer.analyze(current_metrics)
                logger.info("  ✓ Trend analysis complete")

            # Comparative Analysis
            logger.info("  → Running comparative analysis...")
            comparative_analyzer = ComparativeAnalyzer(self._historical_loader)
            self.comparison_analytics = comparative_analyzer.analyze(current_metrics)
            logger.info("  ✓ Comparative analysis complete")

            # Anomaly Detection
            if self._historical_loader.can_detect_anomalies():
                logger.info("  → Detecting anomalies...")
                anomaly_detector = AnomalyDetector(self._historical_loader, self._metrics_storage)
                self.anomaly_analytics = anomaly_detector.analyze(current_metrics)
                logger.info("  ✓ Anomaly detection complete")

            # Forecasting
            if self._historical_loader.can_forecast():
                logger.info("  → Generating forecasts...")
                forecast_engine = ForecastEngine(self._historical_loader, self._metrics_storage)
                self.forecast_analytics = forecast_engine.analyze()
                logger.info("  ✓ Forecast generation complete")

            logger.info("✓ Historical analytics completed")

        except ImportError as e:
            logger.warning(f"  Analytics modules not available: {e}")
            logger.info("  Install numpy, scikit-learn, statsmodels for advanced analytics")
        except Exception as e:
            logger.warning(f"  Error in historical analytics: {e}")

    def _generate_executive_summary(self) -> None:
        """Generate executive summary from all analytics."""
        logger.info("Generating executive summary...")

        self.executive_summary = {
            # User metrics
            "total_users": self.user_analytics.get("total_users", 0),
            "total_doctors": self.user_analytics.get("total_doctors", 0),
            "active_users": self.user_analytics.get("active_users", 0),
            # Order metrics
            "total_orders": self.order_analytics.get("total_orders", 0),
            "completed_orders": self.order_analytics.get("completed_orders", 0),
            # Payment metrics (from PaymentAnalyzer)
            "total_revenue": self.payment_analytics.get("total_revenue", 0),
            "total_paid_amount": self.payment_analytics.get("total_paid_amount", 0),
            "total_pending_amount": self.payment_analytics.get("total_pending_amount", 0),
            "payment_completion_rate": self.payment_analytics.get("payment_completion_rate", 0),
            "avg_order_value": self.payment_analytics.get("avg_order_value", 0),
            # Research metrics
            "total_papers": self.research_analytics.get("total_papers", 0),
            "total_views": self.research_analytics.get("total_views", 0),
            "total_upvotes": self.research_analytics.get("total_upvotes", 0),
            # Ad metrics
            "active_ads": self.ad_analytics.get("active_ads", 0),
            "total_ad_revenue": self.ad_analytics.get("total_ad_revenue", 0),
            # Signup metrics
            "signup_usage_rate": self.user_analytics.get("signup_usage_rate", 0),
        }

        logger.info("✓ Executive summary generated")

    def _generate_report(self) -> None:
        """Generate the HTML business report."""
        logger.info("Generating HTML report...")

        report_builder = ReportBuilder(
            executive_summary=self.executive_summary,
            user_analytics=self.user_analytics,
            order_analytics=self.order_analytics,
            payment_analytics=self.payment_analytics,
            research_analytics=self.research_analytics,
            ad_analytics=self.ad_analytics,
            financial_analytics=self.financial_analytics,
            business_kpi_analytics=self.business_kpi_analytics,
            # Historical analytics
            trend_analytics=self.trend_analytics,
            forecast_analytics=self.forecast_analytics,
            anomaly_analytics=self.anomaly_analytics,
            comparison_analytics=self.comparison_analytics,
        )

        self._report_path = report_builder.generate()
        logger.info(f"✓ Report generated: {self._report_path}")

    def _upload_to_drive(self) -> None:
        """Upload the generated report to Google Drive."""
        if not self._report_path:
            logger.warning("No report to upload - skipping Drive upload")
            return

        logger.info("Uploading report to Google Drive...")

        try:
            self._drive_api = GoogleDriveAPI()

            # Upload the file
            self._uploaded_file_id = self._drive_api.upload_file(
                local_path=self._report_path,
                parent_id=CONFIG.GOOGLE_DRIVE_FOLDER_ID,
            )

            # Generate the file URL
            self._uploaded_file_url = (
                f"https://drive.google.com/file/d/{self._uploaded_file_id}/view"
            )

            logger.info("✓ Report uploaded to Google Drive")
            logger.info(f"  File ID: {self._uploaded_file_id}")
            logger.info(f"  URL: {self._uploaded_file_url}")

        except Exception as e:
            logger.error(f"Failed to upload report to Google Drive: {e}")
            # Don't fail the whole process if upload fails

    @property
    def report_path(self) -> str | None:
        """Get the path to the generated report."""
        return self._report_path

    @property
    def uploaded_file_id(self) -> str | None:
        """Get the Google Drive file ID of the uploaded report."""
        return self._uploaded_file_id

    @property
    def uploaded_file_url(self) -> str | None:
        """Get the Google Drive URL of the uploaded report."""
        return self._uploaded_file_url

