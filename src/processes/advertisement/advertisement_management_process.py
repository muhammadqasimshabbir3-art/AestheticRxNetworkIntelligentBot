"""Advertisement Management Process - Public entry point for the workflow.

This class wraps the AdvertisementManager and exposes only necessary methods.
"""

from libraries.logger import logger
from processes.advertisement.advertisement_manager import AdvertisementManager


class AdvertisementManagementProcess:
    """Public entry point for the Advertisement Management workflow."""

    def __init__(self, paid_ids_list: list[str] | None = None) -> None:
        """Initialize the Advertisement Management Process.

        Args:
            paid_ids_list: List of advertisement IDs to mark as 'paid' in the sheet
        """
        logger.info("=" * 60)
        logger.info("Initializing Advertisement Management Process")
        logger.info("=" * 60)

        self._paid_ids_list = paid_ids_list or []
        self._advertisement_manager: AdvertisementManager | None = None

        logger.info(f"Paid IDs to process: {self._paid_ids_list}")
        logger.info("Advertisement Management Process initialized")

    @property
    def all_advertisements(self) -> list[dict]:
        """Get all advertisements."""
        if self._advertisement_manager:
            return self._advertisement_manager.all_advertisements
        return []

    @property
    def pending_advertisements(self) -> list[dict]:
        """Get pending advertisements."""
        if self._advertisement_manager:
            return self._advertisement_manager.pending_advertisements
        return []

    @property
    def approved_advertisements(self) -> list[dict]:
        """Get approved advertisements."""
        if self._advertisement_manager:
            return self._advertisement_manager.approved_advertisements
        return []

    @property
    def failed_approvals(self) -> list[str]:
        """Get failed approval IDs."""
        if self._advertisement_manager:
            return self._advertisement_manager.failed_approvals
        return []

    @property
    def payment_updated_ids(self) -> list[str]:
        """Get IDs with updated payment status."""
        if self._advertisement_manager:
            return self._advertisement_manager.payment_updated_ids
        return []

    @property
    def payment_update_failed_ids(self) -> list[str]:
        """Get IDs where payment update failed."""
        if self._advertisement_manager:
            return self._advertisement_manager.payment_update_failed_ids
        return []

    @property
    def status_updated_ids(self) -> list[str]:
        """Get IDs with status updated to active in sheet."""
        if self._advertisement_manager:
            return self._advertisement_manager.status_updated_ids
        return []

    @property
    def advertisements(self) -> list[dict]:
        """Get all advertisements (alias for all_advertisements)."""
        return self.all_advertisements

    @property
    def total_count(self) -> int:
        """Get total advertisement count."""
        if self._advertisement_manager:
            return self._advertisement_manager.total_count
        return 0

    @property
    def status_breakdown(self) -> dict[str, int]:
        """Get status breakdown."""
        if self._advertisement_manager:
            return self._advertisement_manager.status_breakdown
        return {}

    @property
    def type_breakdown(self) -> dict[str, int]:
        """Get type breakdown."""
        if self._advertisement_manager:
            return self._advertisement_manager.type_breakdown
        return {}

    @property
    def payment_status_breakdown(self) -> dict[str, int]:
        """Get payment status breakdown."""
        if self._advertisement_manager:
            return self._advertisement_manager.payment_status_breakdown
        return {}

    def start(self) -> None:
        """Start the advertisement management workflow."""
        logger.info("=" * 60)
        logger.info("Starting Advertisement Management Workflow")
        logger.info("=" * 60)

        # Initialize manager with paid IDs
        self._advertisement_manager = AdvertisementManager(paid_ids_list=self._paid_ids_list)

        # Run workflow
        self._advertisement_manager.start()

        logger.info("✅ Advertisement Management Process completed")

    def finish(self) -> None:
        """Finalize the process."""
        if self._advertisement_manager:
            self._advertisement_manager.finish()
        logger.info("Advertisement Management Process finalized")
