"""Financial Analyzer - Analytics for wallets, debt, and revenue.

This module analyzes financial data including:
- Wallet balances
- Debt management
- Revenue trends
"""

from typing import TYPE_CHECKING, Any

from libraries.logger import logger

if TYPE_CHECKING:
    from processes.business_report.data_loader import DataLoader


class FinancialAnalyzer:
    """Analyzes financial data."""

    def __init__(self, data_loader: "DataLoader") -> None:
        """Initialize the analyzer.

        Args:
            data_loader: DataLoader instance with loaded CSV data.
        """
        self._loader = data_loader

    def analyze(self) -> dict[str, Any]:
        """Run all financial analytics.

        Returns:
            Dictionary containing all financial analytics.
        """
        logger.info("Running financial analytics...")

        results = {
            # Wallet metrics
            "total_wallets": self._count_wallets(),
            "total_wallet_balance": self._calculate_total_wallet_balance(),
            "average_wallet_balance": self._calculate_avg_wallet_balance(),
            # Debt metrics
            "total_debt_records": self._count_debt_records(),
            "total_debt_amount": self._calculate_total_debt(),
            "debt_threshold_configs": self._count_debt_thresholds(),
            # Notifications and communications
            "total_notifications": self._count_notifications(),
            "total_emails_sent": self._count_emails_sent(),
            "total_gmail_messages": self._count_gmail_messages(),
            # OTP metrics
            "total_otp_codes": self._count_otp_codes(),
            # Team metrics
            "total_teams": self._count_teams(),
            "total_team_members": self._count_team_members(),
            # AI/API metrics
            "ai_models_count": self._count_ai_models(),
            "api_tokens_count": self._count_api_tokens(),
            # Analytics data
            "analytics_records": self._count_analytics(),
            "user_activity_records": self._count_user_activity(),
            # Badge/award metrics
            "total_badges": self._count_badges(),
            "award_templates": self._count_award_templates(),
        }

        logger.info(f"  ✓ Wallets: {results['total_wallets']}, Balance: {results['total_wallet_balance']:,.2f}")
        return results

    def _count_wallets(self) -> int:
        """Count total wallets."""
        wallets = self._loader.get("user_wallets")
        if wallets.empty:
            wallets = self._loader.get("user_wallets_full")
        return len(wallets)

    def _calculate_total_wallet_balance(self) -> float:
        """Calculate total wallet balance."""
        wallets = self._loader.get("user_wallets_full")
        if wallets.empty:
            wallets = self._loader.get("user_wallets")

        if wallets.empty:
            return 0.0

        # Try different balance column names
        for col in ["balance", "current_balance", "total_balance", "amount"]:
            if col in wallets.columns:
                return float(wallets[col].sum())

        return 0.0

    def _calculate_avg_wallet_balance(self) -> float:
        """Calculate average wallet balance."""
        total = self._calculate_total_wallet_balance()
        count = self._count_wallets()
        if count == 0:
            return 0.0
        return round(total / count, 2)

    def _count_debt_records(self) -> int:
        """Count debt management records."""
        return len(self._loader.get("debt_management"))

    def _calculate_total_debt(self) -> float:
        """Calculate total debt amount."""
        debt = self._loader.get("debt_management")
        if debt.empty:
            return 0.0

        for col in ["amount", "debt_amount", "total_owed", "owed_amount"]:
            if col in debt.columns:
                return float(debt[col].sum())

        return 0.0

    def _count_debt_thresholds(self) -> int:
        """Count debt threshold configurations."""
        return len(self._loader.get("debt_thresholds"))

    def _count_notifications(self) -> int:
        """Count total notifications."""
        return len(self._loader.get("notifications"))

    def _count_emails_sent(self) -> int:
        """Count total emails delivered."""
        return len(self._loader.get("email_deliveries"))

    def _count_gmail_messages(self) -> int:
        """Count gmail messages."""
        return len(self._loader.get("gmail_messages"))

    def _count_otp_codes(self) -> int:
        """Count OTP codes generated."""
        return len(self._loader.get("otp_codes"))

    def _count_teams(self) -> int:
        """Count total teams."""
        return len(self._loader.get("teams"))

    def _count_team_members(self) -> int:
        """Count total team members."""
        return len(self._loader.get("team_members"))

    def _count_ai_models(self) -> int:
        """Count AI models."""
        return len(self._loader.get("ai_models"))

    def _count_api_tokens(self) -> int:
        """Count API tokens."""
        return len(self._loader.get("api_tokens"))

    def _count_analytics(self) -> int:
        """Count analytics records."""
        return len(self._loader.get("analytics"))

    def _count_user_activity(self) -> int:
        """Count user activity records."""
        return len(self._loader.get("user_activity"))

    def _count_badges(self) -> int:
        """Count badges."""
        return len(self._loader.get("badges"))

    def _count_award_templates(self) -> int:
        """Count award message templates."""
        return len(self._loader.get("award_message_templates"))

