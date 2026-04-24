"""Signup ID Manager - Core logic for signup ID management.

This module handles:
- Fetching signup IDs from the API
- Calculating usage statistics
- Determining emergency status
"""

from libraries.aestheticrxnetwork_api import AestheticRxNetworkAPI
from libraries.logger import logger


class SignupIDManager:
    """Manages signup ID operations and statistics."""

    # Emergency threshold - warn if fewer than this many unused IDs remain
    EMERGENCY_THRESHOLD = 20

    def __init__(self) -> None:
        """Initialize the SignupIDManager."""
        logger.info("Initializing SignupIDManager...")
        self._api = AestheticRxNetworkAPI()

        # Data storage
        self.signup_ids: list[dict] = []
        self.total_count: int = 0
        self.used_count: int = 0
        self.unused_count: int = 0
        self.usage_percentage: float = 0.0

        self.used_signup_ids: list[dict] = []
        self.unused_signup_ids: list[dict] = []
        self.recent_signups: list[dict] = []

        self.emergency_threshold = self.EMERGENCY_THRESHOLD

        logger.info("SignupIDManager initialized")

    @property
    def is_emergency(self) -> bool:
        """Check if signup IDs are critically low."""
        return self.unused_count < self.emergency_threshold

    def start(self) -> None:
        """Start the signup ID management workflow."""
        logger.info("=" * 60)
        logger.info("Starting Signup ID Management Workflow")
        logger.info("=" * 60)

        # Step 1: Fetch all signup IDs from API
        self._fetch_signup_ids()

        # Step 2: Calculate statistics
        self._calculate_statistics()

        # Step 3: Log results
        self._log_summary()

        logger.info("=" * 60)
        logger.info("Signup ID Management Workflow completed")
        logger.info("=" * 60)

    def _fetch_signup_ids(self) -> None:
        """Fetch all signup IDs from the API."""
        logger.info("Fetching signup IDs from API...")

        try:
            self.signup_ids = self._api.get_signup_ids()
            self.total_count = len(self.signup_ids)
            logger.info(f"✓ Fetched {self.total_count} signup IDs")
        except Exception as e:
            logger.error(f"✗ Failed to fetch signup IDs: {e}")
            raise

    def _calculate_statistics(self) -> None:
        """Calculate usage statistics."""
        logger.info("Calculating statistics...")

        # Separate used and unused
        self.used_signup_ids = [sid for sid in self.signup_ids if sid.get("is_used")]
        self.unused_signup_ids = [sid for sid in self.signup_ids if not sid.get("is_used")]

        self.used_count = len(self.used_signup_ids)
        self.unused_count = len(self.unused_signup_ids)

        # Calculate usage percentage
        if self.total_count > 0:
            self.usage_percentage = (self.used_count / self.total_count) * 100
        else:
            self.usage_percentage = 0.0

        # Sort recent signups by used_at (most recent first)
        self.recent_signups = sorted(
            [sid for sid in self.used_signup_ids if sid.get("used_at")],
            key=lambda x: x.get("used_at", ""),
            reverse=True,
        )[:10]  # Top 10 most recent

        logger.info(f"  Total: {self.total_count}")
        logger.info(f"  Used: {self.used_count}")
        logger.info(f"  Unused: {self.unused_count}")
        logger.info(f"  Usage: {self.usage_percentage:.1f}%")

    def _log_summary(self) -> None:
        """Log summary of signup ID status."""
        logger.info("=" * 60)
        logger.info("📊 SIGNUP ID SUMMARY")
        logger.info("=" * 60)
        logger.info(f"  📌 Total Signup IDs: {self.total_count}")
        logger.info(f"  ✅ Used: {self.used_count}")
        logger.info(f"  🔓 Available: {self.unused_count}")
        logger.info(f"  📈 Usage: {self.usage_percentage:.1f}%")
        logger.info(f"  ⚠️ Emergency Threshold: {self.emergency_threshold}")

        if self.is_emergency:
            logger.warning("=" * 60)
            logger.warning("🚨 EMERGENCY ALERT 🚨")
            logger.warning(f"Only {self.unused_count} signup IDs remaining!")
            logger.warning("Please add more signup IDs immediately!")
            logger.warning("=" * 60)
        elif self.unused_count < self.emergency_threshold * 2:
            logger.warning(f"⚠️ Warning: Signup IDs running low ({self.unused_count} remaining)")

        if self.recent_signups:
            logger.info("")
            logger.info("📋 Recent Signups:")
            for signup in self.recent_signups[:5]:
                logger.info(
                    f"  - {signup.get('signup_id')} → {signup.get('used_by_email')} "
                    f"({signup.get('used_at', 'N/A')[:10]})"
                )
