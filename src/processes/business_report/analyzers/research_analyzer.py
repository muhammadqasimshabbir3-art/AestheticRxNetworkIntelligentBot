"""Research Analyzer - Analytics for research papers and engagement.

This module analyzes research data including:
- Papers published
- View and upvote metrics
- Engagement rates
- Top performing papers
- Leaderboard rankings
"""

from typing import TYPE_CHECKING, Any

from libraries.logger import logger

if TYPE_CHECKING:
    from processes.business_report.data_loader import DataLoader


class ResearchAnalyzer:
    """Analyzes research and engagement data."""

    def __init__(self, data_loader: "DataLoader") -> None:
        """Initialize the analyzer.

        Args:
            data_loader: DataLoader instance with loaded CSV data.
        """
        self._loader = data_loader

    def analyze(self) -> dict[str, Any]:
        """Run all research analytics.

        Returns:
            Dictionary containing all research analytics.
        """
        logger.info("Running research analytics...")

        results = {
            # Paper counts
            "total_papers": self._count_papers(),
            "approved_papers": self._count_approved_papers(),
            "pending_papers": self._count_pending_papers(),
            # Engagement metrics
            "total_views": self._count_total_views(),
            "total_upvotes": self._count_total_upvotes(),
            "unique_viewers": self._count_unique_viewers(),
            "average_views_per_paper": self._calculate_avg_views_per_paper(),
            "average_upvotes_per_paper": self._calculate_avg_upvotes_per_paper(),
            "engagement_rate": self._calculate_engagement_rate(),
            # Top content
            "top_papers_by_views": self._get_top_papers_by_views(),
            "top_papers_by_upvotes": self._get_top_papers_by_upvotes(),
            # Research reports
            "total_reports": self._count_reports(),
            # Leaderboard
            "leaderboard_entries": self._count_leaderboard_entries(),
            "top_performers": self._get_top_performers(),
            # Hall of pride
            "hall_of_pride_entries": self._count_hall_of_pride(),
            # Certificates
            "total_certificates": self._count_certificates(),
            # Trends
            "papers_by_date": self._get_papers_by_date(),
            "views_by_date": self._get_views_by_date(),
        }

        logger.info(f"  ✓ Papers: {results['total_papers']}, Views: {results['total_views']}")
        return results

    def _count_papers(self) -> int:
        """Count total research papers."""
        return len(self._loader.research_papers)

    def _count_approved_papers(self) -> int:
        """Count approved papers."""
        papers = self._loader.research_papers
        if papers.empty or "is_approved" not in papers.columns:
            return 0
        return len(papers[papers["is_approved"]])

    def _count_pending_papers(self) -> int:
        """Count pending papers."""
        papers = self._loader.research_papers
        if papers.empty or "is_approved" not in papers.columns:
            return 0
        return len(papers[~papers["is_approved"]])

    def _count_total_views(self) -> int:
        """Count total views across all papers."""
        papers = self._loader.research_papers
        if papers.empty:
            return 0

        # First try view_count column in papers
        if "view_count" in papers.columns:
            return int(papers["view_count"].sum())

        # Fall back to research_views table
        views = self._loader.get("research_views")
        return len(views)

    def _count_total_upvotes(self) -> int:
        """Count total upvotes across all papers."""
        papers = self._loader.research_papers
        if papers.empty:
            return 0

        # First try upvote_count column in papers
        if "upvote_count" in papers.columns:
            return int(papers["upvote_count"].sum())

        # Fall back to research_upvotes table
        upvotes = self._loader.get("research_upvotes")
        return len(upvotes)

    def _count_unique_viewers(self) -> int:
        """Count unique viewers."""
        views = self._loader.get("research_views")
        if views.empty:
            return 0

        if "doctor_id" in views.columns:
            return views["doctor_id"].nunique()
        return 0

    def _calculate_avg_views_per_paper(self) -> float:
        """Calculate average views per paper."""
        total_papers = self._count_papers()
        if total_papers == 0:
            return 0.0
        total_views = self._count_total_views()
        return round(total_views / total_papers, 2)

    def _calculate_avg_upvotes_per_paper(self) -> float:
        """Calculate average upvotes per paper."""
        total_papers = self._count_papers()
        if total_papers == 0:
            return 0.0
        total_upvotes = self._count_total_upvotes()
        return round(total_upvotes / total_papers, 2)

    def _calculate_engagement_rate(self) -> float:
        """Calculate engagement rate (upvotes/views ratio)."""
        total_views = self._count_total_views()
        if total_views == 0:
            return 0.0
        total_upvotes = self._count_total_upvotes()
        return round((total_upvotes / total_views) * 100, 2)

    def _get_top_papers_by_views(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top papers by view count."""
        papers = self._loader.research_papers
        if papers.empty or "view_count" not in papers.columns:
            return []

        top_papers = papers.nlargest(limit, "view_count")

        return [
            {
                "id": row.get("id", "N/A"),
                "title": str(row.get("title", "Untitled"))[:50],
                "view_count": int(row.get("view_count", 0)),
                "upvote_count": int(row.get("upvote_count", 0)),
            }
            for _, row in top_papers.iterrows()
        ]

    def _get_top_papers_by_upvotes(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top papers by upvote count."""
        papers = self._loader.research_papers
        if papers.empty or "upvote_count" not in papers.columns:
            return []

        top_papers = papers.nlargest(limit, "upvote_count")

        return [
            {
                "id": row.get("id", "N/A"),
                "title": str(row.get("title", "Untitled"))[:50],
                "view_count": int(row.get("view_count", 0)),
                "upvote_count": int(row.get("upvote_count", 0)),
            }
            for _, row in top_papers.iterrows()
        ]

    def _count_reports(self) -> int:
        """Count research reports."""
        return len(self._loader.get("research_reports"))

    def _count_leaderboard_entries(self) -> int:
        """Count leaderboard entries."""
        return len(self._loader.leaderboard)

    def _get_top_performers(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top performers from leaderboard."""
        leaderboard = self._loader.leaderboard
        if leaderboard.empty:
            return []

        # Get latest snapshot
        if "snapshot_date" in leaderboard.columns:
            latest_date = leaderboard["snapshot_date"].max()
            latest_data = leaderboard[leaderboard["snapshot_date"] == latest_date]
        else:
            latest_data = leaderboard

        if "rank" in latest_data.columns:
            top_data = latest_data.nsmallest(limit, "rank")
        elif "current_sales" in latest_data.columns:
            top_data = latest_data.nlargest(limit, "current_sales")
        else:
            top_data = latest_data.head(limit)

        return [
            {
                "doctor_id": row.get("doctor_id", "N/A"),
                "tier": row.get("tier", "N/A"),
                "current_sales": float(row.get("current_sales", 0)),
                "rank": int(row.get("rank", idx + 1)),
            }
            for idx, (_, row) in enumerate(top_data.iterrows())
        ]

    def _count_hall_of_pride(self) -> int:
        """Count hall of pride entries."""
        return len(self._loader.get("hall_of_pride"))

    def _count_certificates(self) -> int:
        """Count certificates issued."""
        return len(self._loader.get("certificates"))

    def _get_papers_by_date(self) -> dict[str, int]:
        """Get papers grouped by creation date."""
        papers = self._loader.research_papers
        if papers.empty or "created_at" not in papers.columns:
            return {}

        papers_with_date = papers[papers["created_at"].notna()].copy()
        if papers_with_date.empty:
            return {}

        papers_with_date["date"] = papers_with_date["created_at"].dt.date
        by_date = papers_with_date.groupby("date").size()

        return {str(k): int(v) for k, v in by_date.items()}

    def _get_views_by_date(self) -> dict[str, int]:
        """Get views grouped by date."""
        views = self._loader.get("research_views")
        if views.empty or "created_at" not in views.columns:
            return {}

        views_with_date = views[views["created_at"].notna()].copy()
        if views_with_date.empty:
            return {}

        views_with_date["date"] = views_with_date["created_at"].dt.date
        by_date = views_with_date.groupby("date").size()

        return {str(k): int(v) for k, v in by_date.items()}
