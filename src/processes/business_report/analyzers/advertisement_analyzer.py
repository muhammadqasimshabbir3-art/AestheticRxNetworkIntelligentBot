"""Advertisement Analyzer - Analytics for ads and placements.

This module analyzes advertisement data including:
- Ad status distribution
- Ad type distribution
- Payment status breakdown
- Placement performance
- Impressions, clicks, views
- Google Sheet integration for paid amounts
"""

import logging
from typing import TYPE_CHECKING, Any, Optional

import pandas as pd

if TYPE_CHECKING:
    from libraries.google_sheets import GoogleSheetsAPI
    from processes.business_report.data_loader import DataLoader

logger = logging.getLogger(__name__)


class AdvertisementAnalyzer:
    """Analyzes advertisement data."""

    def __init__(self, data_loader: "DataLoader", sheets_api: Optional["GoogleSheetsAPI"] = None) -> None:
        """Initialize the analyzer.

        Args:
            data_loader: DataLoader instance with loaded CSV data.
            sheets_api: Optional GoogleSheetsAPI instance for reading payment data from sheet.
        """
        self._loader = data_loader
        self._sheets_api = sheets_api
        self._sheet_data: pd.DataFrame | None = None

    def analyze(self) -> dict[str, Any]:
        """Run all advertisement analytics.

        Returns:
            Dictionary containing all advertisement analytics.
        """
        logger.info("Running advertisement analytics...")

        # Load Google Sheet data for payment information
        self._load_sheet_data()

        # Get Google Sheet payment metrics
        sheet_metrics = self._get_sheet_payment_metrics()

        results = {
            # Basic counts
            "total_ads": self._count_ads(),
            "active_ads": self._count_active_ads(),
            "pending_ads": self._count_pending_ads(),
            "completed_ads": self._count_completed_ads(),
            # Video/Banner breakdown
            "video_ads": self._count_video_ads(),
            "banner_ads": self._count_banner_ads(),
            # Revenue metrics from CSV
            "total_ad_revenue": self._calculate_total_ad_revenue(),
            "paid_ad_revenue": self._calculate_paid_ad_revenue(),
            "pending_ad_revenue": self._calculate_pending_ad_revenue(),
            # Revenue metrics from Google Sheet
            "sheet_total_revenue": sheet_metrics.get("total_revenue", 0.0),
            "sheet_paid_revenue": sheet_metrics.get("paid_revenue", 0.0),
            "sheet_pending_revenue": sheet_metrics.get("pending_revenue", 0.0),
            "sheet_paid_count": sheet_metrics.get("paid_count", 0),
            "sheet_pending_count": sheet_metrics.get("pending_count", 0),
            # Performance metrics
            "total_impressions": self._count_total_impressions(),
            "total_clicks": self._count_total_clicks(),
            "total_views": self._count_total_views(),
            "click_through_rate": self._calculate_ctr(),
            # Status distributions
            "status_distribution": self._get_status_distribution(),
            "payment_status_distribution": self._get_payment_status_distribution(),
            "type_distribution": self._get_type_distribution(),
            "placement_distribution": self._get_placement_distribution(),
            # Applications
            "total_applications": self._count_applications(),
            # Placements
            "total_placements": self._count_placements(),
            # Top performers
            "top_ads_by_views": self._get_top_ads_by_views(),
            # Pricing
            "pricing_configs": self._count_pricing_configs(),
            # Trends
            "ads_by_date": self._get_ads_by_date(),
            # Sheet data available flag
            "has_sheet_data": self._sheet_data is not None and not self._sheet_data.empty,
        }

        logger.info(f"  ✓ Ads: {results['total_ads']}, Revenue: {results['total_ad_revenue']:,.2f}")
        if results["has_sheet_data"]:
            logger.info(f"  ✓ Sheet: Paid={results['sheet_paid_count']}, Revenue={results['sheet_paid_revenue']:,.2f}")
        return results

    def _load_sheet_data(self) -> None:
        """Load advertisement data from Google Sheet."""
        if self._sheets_api is None:
            logger.debug("No Google Sheets API available, skipping sheet data load")
            return

        # Lazy import to avoid circular dependencies
        from config import CONFIG

        spreadsheet_id = CONFIG.ADVERTISEMENT_SPREADSHEET_ID
        if not spreadsheet_id:
            logger.debug("No ADVERTISEMENT_SPREADSHEET_ID configured")
            return

        try:
            # Get sheet info to find the data range
            sheet_info = self._sheets_api.get_sheet_info(spreadsheet_id)
            if not sheet_info or "sheets" not in sheet_info:
                return

            # Get the first sheet name
            first_sheet = sheet_info["sheets"][0]["properties"]["title"]
            read_range = f"{first_sheet}!A:Z"

            # Read all data
            data = self._sheets_api.read_spreadsheet(spreadsheet_id, read_range)
            if not data or len(data) < 2:
                return

            # Convert to DataFrame
            headers = data[0]
            rows = data[1:]
            self._sheet_data = pd.DataFrame(rows, columns=headers)

            logger.info(f"  ✓ Loaded {len(self._sheet_data)} ads from Google Sheet")

        except Exception as e:
            logger.warning(f"Failed to load advertisement sheet data: {e}")
            self._sheet_data = None

    def _get_sheet_payment_metrics(self) -> dict[str, Any]:
        """Get payment metrics from Google Sheet data.

        Returns:
            Dictionary with payment metrics from the sheet.
        """
        if self._sheet_data is None or self._sheet_data.empty:
            return {
                "total_revenue": 0.0,
                "paid_revenue": 0.0,
                "pending_revenue": 0.0,
                "paid_count": 0,
                "pending_count": 0,
            }

        df = self._sheet_data.copy()

        # Find payment status and amount columns
        payment_status_col = None
        amount_col = None

        for col in df.columns:
            col_lower = col.lower()
            if "payment" in col_lower and "status" in col_lower:
                payment_status_col = col
            elif col_lower in ["total_cost", "amount", "price", "cost", "paid_amount"]:
                amount_col = col

        # Also check for "Payment Status" with exact case
        if payment_status_col is None and "Payment Status" in df.columns:
            payment_status_col = "Payment Status"
        if amount_col is None and "Total Cost" in df.columns:
            amount_col = "Total Cost"

        # Convert amount to numeric
        if amount_col and amount_col in df.columns:
            df["_amount"] = pd.to_numeric(df[amount_col], errors="coerce").fillna(0)
        else:
            df["_amount"] = 0.0

        total_revenue = float(df["_amount"].sum())

        # Calculate paid vs pending
        paid_revenue = 0.0
        pending_revenue = 0.0
        paid_count = 0
        pending_count = 0

        if payment_status_col and payment_status_col in df.columns:
            df["_status_lower"] = df[payment_status_col].astype(str).str.lower().str.strip()

            paid_mask = df["_status_lower"].isin(["paid", "completed", "success"])
            pending_mask = df["_status_lower"].isin(["pending", "unpaid", ""])

            paid_revenue = float(df.loc[paid_mask, "_amount"].sum())
            pending_revenue = float(df.loc[pending_mask, "_amount"].sum())
            paid_count = int(paid_mask.sum())
            pending_count = int(pending_mask.sum())

        return {
            "total_revenue": total_revenue,
            "paid_revenue": paid_revenue,
            "pending_revenue": pending_revenue,
            "paid_count": paid_count,
            "pending_count": pending_count,
        }

    def _count_ads(self) -> int:
        """Count total advertisements."""
        return len(self._loader.advertisements)

    def _count_active_ads(self) -> int:
        """Count active advertisements."""
        ads = self._loader.advertisements
        if ads.empty or "status" not in ads.columns:
            return 0
        return len(ads[ads["status"] == "active"])

    def _count_pending_ads(self) -> int:
        """Count pending advertisements."""
        ads = self._loader.advertisements
        if ads.empty or "status" not in ads.columns:
            return 0
        return len(ads[ads["status"] == "pending"])

    def _count_completed_ads(self) -> int:
        """Count completed advertisements."""
        ads = self._loader.advertisements
        if ads.empty or "status" not in ads.columns:
            return 0
        return len(ads[ads["status"] == "completed"])

    def _count_video_ads(self) -> int:
        """Count video advertisements."""
        video_ads = self._loader.get("video_advertisements")
        if not video_ads.empty:
            return len(video_ads)

        # Fall back to type in main ads table
        ads = self._loader.advertisements
        if ads.empty or "type" not in ads.columns:
            return 0
        return len(ads[ads["type"] == "video"])

    def _count_banner_ads(self) -> int:
        """Count banner advertisements."""
        banner_ads = self._loader.get("banner_advertisements")
        if not banner_ads.empty:
            return len(banner_ads)

        # Fall back to type in main ads table
        ads = self._loader.advertisements
        if ads.empty or "type" not in ads.columns:
            return 0
        return len(ads[ads["type"] == "banner"])

    def _calculate_total_ad_revenue(self) -> float:
        """Calculate total ad revenue."""
        ads = self._loader.advertisements
        if ads.empty or "total_cost" not in ads.columns:
            return 0.0
        return float(ads["total_cost"].sum())

    def _calculate_paid_ad_revenue(self) -> float:
        """Calculate paid ad revenue."""
        ads = self._loader.advertisements
        if ads.empty:
            return 0.0

        if "paid_amount" in ads.columns:
            return float(ads["paid_amount"].sum())

        if "payment_status" in ads.columns and "total_cost" in ads.columns:
            paid = ads[ads["payment_status"].isin(["paid", "completed"])]
            return float(paid["total_cost"].sum())

        return 0.0

    def _calculate_pending_ad_revenue(self) -> float:
        """Calculate pending ad revenue."""
        ads = self._loader.advertisements
        if ads.empty:
            return 0.0

        if "payment_status" in ads.columns and "total_cost" in ads.columns:
            pending = ads[ads["payment_status"].isin(["pending", "unpaid"])]
            return float(pending["total_cost"].sum())

        return 0.0

    def _count_total_impressions(self) -> int:
        """Count total ad impressions."""
        ads = self._loader.advertisements
        if ads.empty or "impressions" not in ads.columns:
            return 0
        return int(ads["impressions"].sum())

    def _count_total_clicks(self) -> int:
        """Count total ad clicks."""
        ads = self._loader.advertisements
        if ads.empty or "clicks" not in ads.columns:
            return 0
        return int(ads["clicks"].sum())

    def _count_total_views(self) -> int:
        """Count total ad views."""
        ads = self._loader.advertisements
        if ads.empty or "views" not in ads.columns:
            return 0
        return int(ads["views"].sum())

    def _calculate_ctr(self) -> float:
        """Calculate click-through rate."""
        impressions = self._count_total_impressions()
        if impressions == 0:
            return 0.0
        clicks = self._count_total_clicks()
        return round((clicks / impressions) * 100, 2)

    def _get_status_distribution(self) -> dict[str, int]:
        """Get distribution of ads by status."""
        ads = self._loader.advertisements
        if ads.empty or "status" not in ads.columns:
            return {}

        distribution = ads["status"].value_counts().to_dict()
        return {str(k): int(v) for k, v in distribution.items() if k and str(k) != "nan"}

    def _get_payment_status_distribution(self) -> dict[str, int]:
        """Get distribution of ads by payment status."""
        ads = self._loader.advertisements
        if ads.empty or "payment_status" not in ads.columns:
            return {}

        distribution = ads["payment_status"].value_counts().to_dict()
        return {str(k): int(v) for k, v in distribution.items() if k and str(k) != "nan"}

    def _get_type_distribution(self) -> dict[str, int]:
        """Get distribution of ads by type."""
        ads = self._loader.advertisements
        if ads.empty or "type" not in ads.columns:
            return {}

        distribution = ads["type"].value_counts().to_dict()
        return {str(k): int(v) for k, v in distribution.items() if k and str(k) != "nan"}

    def _get_placement_distribution(self) -> dict[str, int]:
        """Get distribution of ads by placement area."""
        ads = self._loader.advertisements
        if ads.empty or "selected_area" not in ads.columns:
            return {}

        distribution = ads["selected_area"].value_counts().to_dict()
        return {str(k): int(v) for k, v in distribution.items() if k and str(k) != "nan"}

    def _count_applications(self) -> int:
        """Count ad applications."""
        return len(self._loader.get("advertisement_applications"))

    def _count_placements(self) -> int:
        """Count ad placements."""
        return len(self._loader.get("advertisement_placements"))

    def _get_top_ads_by_views(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top ads by view count."""
        ads = self._loader.advertisements
        if ads.empty or "views" not in ads.columns:
            return []

        top_ads = ads.nlargest(limit, "views")

        return [
            {
                "id": row.get("id", "N/A"),
                "title": str(row.get("title", "Untitled"))[:40],
                "type": row.get("type", "N/A"),
                "status": row.get("status", "N/A"),
                "views": int(row.get("views", 0)),
                "clicks": int(row.get("clicks", 0)),
                "impressions": int(row.get("impressions", 0)),
            }
            for _, row in top_ads.iterrows()
        ]

    def _count_pricing_configs(self) -> int:
        """Count pricing configurations."""
        return len(self._loader.get("advertisement_pricing_configs"))

    def _get_ads_by_date(self) -> dict[str, int]:
        """Get ads grouped by creation date."""
        ads = self._loader.advertisements
        if ads.empty or "created_at" not in ads.columns:
            return {}

        ads_with_date = ads[ads["created_at"].notna()].copy()
        if ads_with_date.empty:
            return {}

        # Convert to datetime if not already
        ads_with_date["created_at"] = pd.to_datetime(ads_with_date["created_at"], errors="coerce")
        ads_with_date = ads_with_date[ads_with_date["created_at"].notna()]
        if ads_with_date.empty:
            return {}

        ads_with_date["date"] = ads_with_date["created_at"].dt.date
        by_date = ads_with_date.groupby("date").size()

        return {str(k): int(v) for k, v in by_date.items()}

