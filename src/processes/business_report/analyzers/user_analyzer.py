"""User Analyzer - Analytics for users, doctors, and signups.

This module analyzes user data including:
- User registration trends
- Tier distribution
- Approval rates
- Top doctors by sales
- Signup ID utilization
"""

from typing import TYPE_CHECKING, Any

from libraries.logger import logger

if TYPE_CHECKING:
    from processes.business_report.data_loader import DataLoader


class UserAnalyzer:
    """Analyzes user and doctor data."""

    def __init__(self, data_loader: "DataLoader") -> None:
        """Initialize the analyzer.

        Args:
            data_loader: DataLoader instance with loaded CSV data.
        """
        self._loader = data_loader

    def analyze(self) -> dict[str, Any]:
        """Run all user analytics.

        Returns:
            Dictionary containing all user analytics.
        """
        logger.info("Running user analytics...")

        results = {
            # Basic counts
            "total_users": self._count_users(),
            "total_doctors": self._count_doctors(),
            "active_users": self._count_active_users(),
            "deactivated_users": self._count_deactivated_users(),
            # Approval metrics
            "approved_users": self._count_approved_users(),
            "pending_approval": self._count_pending_approval(),
            "approval_rate": self._calculate_approval_rate(),
            # Admin metrics
            "admin_count": self._count_admins(),
            # Tier distribution
            "tier_distribution": self._get_tier_distribution(),
            # Signup metrics
            "total_signup_ids": self._count_signup_ids(),
            "used_signup_ids": self._count_used_signup_ids(),
            "available_signup_ids": self._count_available_signup_ids(),
            "signup_usage_rate": self._calculate_signup_usage_rate(),
            # Registration trends
            "registration_by_date": self._get_registration_by_date(),
            # Top performers
            "top_doctors_by_sales": self._get_top_doctors_by_sales(),
            # User types
            "user_type_distribution": self._get_user_type_distribution(),
        }

        logger.info(f"  ✓ Users: {results['total_users']}, Doctors: {results['total_doctors']}")
        return results

    def _count_users(self) -> int:
        """Count total users."""
        return len(self._loader.users)

    def _count_doctors(self) -> int:
        """Count total doctors."""
        doctors = self._loader.doctors
        if doctors.empty:
            # Fall back to users with user_type='doctor'
            users = self._loader.users
            if not users.empty and "user_type" in users.columns:
                return len(users[users["user_type"] == "doctor"])
        return len(doctors)

    def _count_active_users(self) -> int:
        """Count active (non-deactivated) users."""
        users = self._loader.users
        if users.empty:
            return 0
        if "is_deactivated" in users.columns:
            return len(users[~users["is_deactivated"]])
        return len(users)

    def _count_deactivated_users(self) -> int:
        """Count deactivated users."""
        users = self._loader.users
        if users.empty:
            return 0
        if "is_deactivated" in users.columns:
            return len(users[users["is_deactivated"]])
        return 0

    def _count_approved_users(self) -> int:
        """Count approved users."""
        users = self._loader.users
        if users.empty:
            return 0
        if "is_approved" in users.columns:
            return len(users[users["is_approved"]])
        return 0

    def _count_pending_approval(self) -> int:
        """Count users pending approval."""
        users = self._loader.users
        if users.empty:
            return 0
        if "is_approved" in users.columns:
            return len(users[~users["is_approved"]])
        return 0

    def _calculate_approval_rate(self) -> float:
        """Calculate approval rate percentage."""
        total = self._count_users()
        if total == 0:
            return 0.0
        approved = self._count_approved_users()
        return round((approved / total) * 100, 2)

    def _count_admins(self) -> int:
        """Count admin users."""
        users = self._loader.users
        if users.empty:
            return 0
        if "is_admin" in users.columns:
            return len(users[users["is_admin"]])
        return 0

    def _get_tier_distribution(self) -> dict[str, int]:
        """Get distribution of users by tier."""
        users = self._loader.users
        if users.empty or "tier" not in users.columns:
            return {}

        distribution = users["tier"].value_counts().to_dict()
        return {str(k): int(v) for k, v in distribution.items() if k and str(k) != "nan"}

    def _count_signup_ids(self) -> int:
        """Count total signup IDs."""
        return len(self._loader.signup_ids)

    def _count_used_signup_ids(self) -> int:
        """Count used signup IDs."""
        signup_ids = self._loader.signup_ids
        if signup_ids.empty:
            return 0
        if "is_used" in signup_ids.columns:
            return len(signup_ids[signup_ids["is_used"]])
        return 0

    def _count_available_signup_ids(self) -> int:
        """Count available (unused) signup IDs."""
        signup_ids = self._loader.signup_ids
        if signup_ids.empty:
            return 0
        if "is_used" in signup_ids.columns:
            return len(signup_ids[~signup_ids["is_used"]])
        return 0

    def _calculate_signup_usage_rate(self) -> float:
        """Calculate signup ID usage rate percentage."""
        total = self._count_signup_ids()
        if total == 0:
            return 0.0
        used = self._count_used_signup_ids()
        return round((used / total) * 100, 2)

    def _get_registration_by_date(self) -> dict[str, int]:
        """Get user registrations grouped by date."""
        users = self._loader.users
        if users.empty or "created_at" not in users.columns:
            return {}

        # Group by date
        users_with_date = users[users["created_at"].notna()].copy()
        if users_with_date.empty:
            return {}

        users_with_date["date"] = users_with_date["created_at"].dt.date
        by_date = users_with_date.groupby("date").size()

        return {str(k): int(v) for k, v in by_date.items()}

    def _get_top_doctors_by_sales(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top doctors by sales from leaderboard."""
        leaderboard = self._loader.leaderboard
        if leaderboard.empty:
            # Fall back to users data
            users = self._loader.users
            if users.empty or "current_sales" not in users.columns:
                return []

            top_users = users.nlargest(limit, "current_sales")
            return [
                {
                    "doctor_name": row.get("doctor_name", "N/A"),
                    "tier": row.get("tier", "N/A"),
                    "current_sales": float(row.get("current_sales", 0)),
                    "rank": idx + 1,
                }
                for idx, (_, row) in enumerate(top_users.iterrows())
            ]

        # Use leaderboard data - get latest snapshot
        if "snapshot_date" in leaderboard.columns:
            latest_date = leaderboard["snapshot_date"].max()
            latest_data = leaderboard[leaderboard["snapshot_date"] == latest_date]
        else:
            latest_data = leaderboard

        if "rank" in latest_data.columns:
            top_data = latest_data.nsmallest(limit, "rank")
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

    def _get_user_type_distribution(self) -> dict[str, int]:
        """Get distribution of users by type."""
        users = self._loader.users
        if users.empty or "user_type" not in users.columns:
            return {}

        distribution = users["user_type"].value_counts().to_dict()
        return {str(k): int(v) for k, v in distribution.items() if k and str(k) != "nan"}
