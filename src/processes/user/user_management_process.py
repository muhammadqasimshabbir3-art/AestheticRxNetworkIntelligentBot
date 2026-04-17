"""User Management Process - Entry point for user management workflow.

This module provides a clean interface for the user management workflow,
encapsulating the UserManager implementation details.
"""


from libraries.logger import logger
from processes.user.user_manager import UserManager


class UserManagementProcess:
    """Public interface for the User Management workflow.

    This class wraps the UserManager and exposes only the necessary
    public methods for external use.

    Usage:
        process = UserManagementProcess()
        process.start()
    """

    def __init__(self) -> None:
        """Initialize the User Management Process."""
        logger.info("=" * 60)
        logger.info("Initializing User Management Process")
        logger.info("=" * 60)

        self._user_manager: UserManager | None = None

        logger.info("User Management Process initialized")

    def start(self) -> None:
        """Start the user management workflow.

        This method:
        1. Initializes the UserManager
        2. Fetches user data from API
        3. Processes user records
        4. Updates Google Sheet
        """
        logger.info("=" * 60)
        logger.info("Starting User Management Workflow")
        logger.info("=" * 60)

        try:
            self._user_manager = UserManager()
            self._user_manager.start()
            logger.info("✅ User Management workflow completed successfully")
        except Exception as e:
            logger.error(f"❌ User Management workflow failed: {e}")
            raise

    @property
    def users(self) -> list[dict]:
        """Get processed users."""
        if self._user_manager:
            return self._user_manager.users
        return []

    @property
    def users_count(self) -> int:
        """Get count of users processed."""
        if self._user_manager:
            return self._user_manager.users_count
        return 0

    @property
    def new_users(self) -> list[dict]:
        """Get new users added."""
        if self._user_manager:
            return self._user_manager.new_users
        return []

    @property
    def updated_users(self) -> list[str]:
        """Get IDs of users that were updated."""
        if self._user_manager:
            return self._user_manager.updated_users
        return []

    @property
    def approved_users(self) -> list[str]:
        """Get IDs of users that were approved."""
        if self._user_manager:
            return self._user_manager.approved_users
        return []

    @property
    def failed_approvals(self) -> list[str]:
        """Get IDs of users whose approval failed."""
        if self._user_manager:
            return self._user_manager.failed_approvals
        return []

    @property
    def status_breakdown(self) -> dict[str, int]:
        """Get breakdown of user statuses."""
        if self._user_manager:
            return self._user_manager.status_breakdown
        return {}

    @property
    def user_type_breakdown(self) -> dict[str, int]:
        """Get breakdown of user types."""
        if self._user_manager:
            return self._user_manager.user_type_breakdown
        return {}

    @property
    def tier_breakdown(self) -> dict[str, int]:
        """Get breakdown of user tiers."""
        if self._user_manager:
            return self._user_manager.tier_breakdown
        return {}

    @property
    def admin_count(self) -> int:
        """Get count of admin users."""
        if self._user_manager:
            return self._user_manager.admin_count
        return 0

    @property
    def deactivated_count(self) -> int:
        """Get count of deactivated users."""
        if self._user_manager:
            return self._user_manager.deactivated_count
        return 0

    def finish(self) -> None:
        """Finalize the user management process."""
        logger.info("Finalizing User Management Process")
        if self._user_manager:
            self._user_manager.finish()
        logger.info("User Management Process finalized")
