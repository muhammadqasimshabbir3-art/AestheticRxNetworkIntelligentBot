"""User Manager - Orchestrates the user management workflow.

This module handles:
- Fetching user data from the API
- Approving unapproved users
- Reading existing users from Google Sheet
- Comparing and updating user records
- Adding new users to the sheet
"""

from libraries.aestheticrxnetwork_api import AestheticRxNetworkAPI
from libraries.google_sheets import GoogleSheetsAPI
from libraries.logger import logger


class UserManager:
    """Orchestrates the user management workflow."""

    # User headers for Google Sheet
    USER_HEADERS = [
        "ID",
        "Email",
        "Name",
        "Role",
        "Status",
        "Is Approved",
        "Created At",
        "Updated At",
    ]

    def __init__(self) -> None:
        """Initialize the User Manager."""
        logger.info("Initializing User Manager...")

        # Initialize APIs
        self._api: AestheticRxNetworkAPI | None = None
        self._sheets_api: GoogleSheetsAPI | None = None

        # Data storage
        self._users: list[dict] = []
        self._sheet_users: list[dict] = []
        self._new_users: list[dict] = []
        self._updated_users: list[str] = []
        self._approved_users: list[str] = []
        self._failed_approvals: list[str] = []

        # Statistics
        self._status_breakdown: dict[str, int] = {}
        self._user_type_breakdown: dict[str, int] = {}
        self._tier_breakdown: dict[str, int] = {}
        self._admin_count: int = 0
        self._deactivated_count: int = 0

        logger.info("User Manager initialized")

    @property
    def api(self) -> AestheticRxNetworkAPI:
        """Get or create AestheticRxNetworkAPI instance."""
        if self._api is None:
            self._api = AestheticRxNetworkAPI()
        return self._api

    @property
    def sheets_api(self) -> GoogleSheetsAPI:
        """Get or create GoogleSheetsAPI instance."""
        if self._sheets_api is None:
            self._sheets_api = GoogleSheetsAPI()
        return self._sheets_api

    @property
    def users(self) -> list[dict]:
        """Get all users from API."""
        return self._users

    @property
    def users_count(self) -> int:
        """Get total count of users."""
        return len(self._users)

    @property
    def new_users(self) -> list[dict]:
        """Get new users added to sheet."""
        return self._new_users

    @property
    def updated_users(self) -> list[str]:
        """Get IDs of updated users."""
        return self._updated_users

    @property
    def approved_users(self) -> list[str]:
        """Get IDs of users that were approved."""
        return self._approved_users

    @property
    def failed_approvals(self) -> list[str]:
        """Get IDs of users whose approval failed."""
        return self._failed_approvals

    @property
    def status_breakdown(self) -> dict[str, int]:
        """Get breakdown of user statuses (approved/unapproved)."""
        return self._status_breakdown

    @property
    def user_type_breakdown(self) -> dict[str, int]:
        """Get breakdown of user types (doctor, employee, regular_user)."""
        return self._user_type_breakdown

    @property
    def tier_breakdown(self) -> dict[str, int]:
        """Get breakdown of user tiers."""
        return self._tier_breakdown

    @property
    def admin_count(self) -> int:
        """Get count of admin users."""
        return self._admin_count

    @property
    def deactivated_count(self) -> int:
        """Get count of deactivated users."""
        return self._deactivated_count

    def start(self) -> None:
        """Start the user management workflow."""
        logger.info("=" * 60)
        logger.info("Starting User Manager Workflow")
        logger.info("=" * 60)

        # Step 1: Fetch users from API
        self._fetch_users()

        # Step 2: Calculate status breakdown
        self._calculate_status_breakdown()

        # Step 3: Find and approve unapproved users
        self._approve_unapproved_users()

        # Step 4: Read existing users from sheet (future implementation)
        # self._read_sheet_users()

        # Step 5: Compare and find new users (future implementation)
        # self._find_new_users()

        # Step 6: Update sheet (future implementation)
        # self._update_sheet()

        logger.info("=" * 60)
        logger.info("User Manager Workflow Completed")
        logger.info("=" * 60)

        # Log summary
        self._log_summary()

    def _fetch_users(self) -> None:
        """Fetch users from the API."""
        logger.info("Fetching users from API...")

        try:
            users_data = self.api.get_users()

            if users_data:
                self._users = users_data
                logger.info(f"✓ Fetched {len(self._users)} users from API")
            else:
                logger.warning("⚠ No users returned from API")
                self._users = []

        except Exception as e:
            logger.error(f"✗ Failed to fetch users: {e}")
            self._users = []

    def _calculate_status_breakdown(self) -> None:
        """Calculate all user statistics and breakdowns."""
        logger.info("Calculating user statistics...")

        # Reset all counters
        self._status_breakdown = {}
        self._user_type_breakdown = {}
        self._tier_breakdown = {}
        self._admin_count = 0
        self._deactivated_count = 0

        for user in self._users:
            # Approval status breakdown
            is_approved = self._get_user_approval_status(user)
            status = "approved" if is_approved else "unapproved"
            self._status_breakdown[status] = self._status_breakdown.get(status, 0) + 1

            # User type breakdown (doctor, employee, regular_user)
            user_type = str(user.get("user_type") or user.get("userType") or "unknown").lower()
            self._user_type_breakdown[user_type] = self._user_type_breakdown.get(user_type, 0) + 1

            # Tier breakdown
            tier = str(user.get("tier") or "Unknown")
            self._tier_breakdown[tier] = self._tier_breakdown.get(tier, 0) + 1

            # Admin count
            is_admin = user.get("is_admin") or user.get("isAdmin") or False
            if isinstance(is_admin, str):
                is_admin = is_admin.lower() == "true"
            if is_admin:
                self._admin_count += 1

            # Deactivated count
            is_deactivated = user.get("is_deactivated") or user.get("isDeactivated") or False
            if isinstance(is_deactivated, str):
                is_deactivated = is_deactivated.lower() == "true"
            if is_deactivated:
                self._deactivated_count += 1

        logger.info(f"Approval status: {self._status_breakdown}")
        logger.info(f"User types: {self._user_type_breakdown}")
        logger.info(f"Tiers: {self._tier_breakdown}")
        logger.info(f"Admins: {self._admin_count}, Deactivated: {self._deactivated_count}")

    def _get_user_approval_status(self, user: dict) -> bool:
        """Get approval status from user dict.

        Args:
            user: User dictionary

        Returns:
            bool: True if approved, False otherwise
        """
        # Check various possible field names
        is_approved = user.get("isApproved") or user.get("is_approved") or user.get("approved") or False

        # Convert string to boolean if needed
        if isinstance(is_approved, str):
            return is_approved.lower() == "true"

        return bool(is_approved)

    def _get_user_id(self, user: dict) -> str:
        """Extract user ID from user dict.

        Args:
            user: User dictionary

        Returns:
            str: User ID or empty string
        """
        return str(user.get("id") or user.get("ID") or user.get("userId") or "").strip()

    def _approve_unapproved_users(self) -> None:
        """Find and approve all unapproved users."""
        logger.info("=" * 60)
        logger.info("Processing User Approvals")
        logger.info("=" * 60)

        # Find unapproved users
        unapproved_users = [user for user in self._users if not self._get_user_approval_status(user)]

        if not unapproved_users:
            logger.info("✓ No unapproved users found - all users are approved")
            return

        logger.info(f"Found {len(unapproved_users)} unapproved users to process")

        # Approve each user
        for user in unapproved_users:
            user_id = self._get_user_id(user)
            if not user_id:
                logger.warning(f"⚠ Skipping user with no ID: {user}")
                continue

            user_email = user.get("email") or user.get("Email") or "N/A"
            logger.info(f"Approving user: {user_email} (ID: {user_id})")

            try:
                result = self.api.approve_user(user_id)

                if result.get("success"):
                    self._approved_users.append(user_id)
                    logger.info(f"  ✓ User {user_id} approved successfully")
                else:
                    self._failed_approvals.append(user_id)
                    logger.error(f"  ✗ Failed to approve user {user_id}: {result.get('message')}")

            except Exception as e:
                self._failed_approvals.append(user_id)
                logger.error(f"  ✗ Exception approving user {user_id}: {e}")

        logger.info("=" * 60)
        logger.info(f"Approval Summary: {len(self._approved_users)} approved, {len(self._failed_approvals)} failed")
        logger.info("=" * 60)

    def _read_sheet_users(self) -> None:
        """Read existing users from Google Sheet.

        Future implementation for reading user data from sheet.
        """
        logger.info("Reading users from Google Sheet...")
        # To be implemented
        self._sheet_users = []

    def _find_new_users(self) -> None:
        """Find users that are in API but not in sheet.

        Future implementation for comparing API and sheet data.
        """
        logger.info("Finding new users...")
        # To be implemented
        self._new_users = []

    def _update_sheet(self) -> None:
        """Update Google Sheet with new/modified users.

        Future implementation for writing user data to sheet.
        """
        logger.info("Updating Google Sheet...")
        # To be implemented

    def _log_summary(self) -> None:
        """Log a summary of the workflow results."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("USER MANAGER SUMMARY")
        logger.info("=" * 60)
        logger.info(f"  Total users fetched: {len(self._users)}")
        logger.info(f"  Users approved: {len(self._approved_users)}")
        logger.info(f"  Failed approvals: {len(self._failed_approvals)}")
        logger.info(f"  New users added: {len(self._new_users)}")
        logger.info(f"  Users updated: {len(self._updated_users)}")
        logger.info("")
        logger.info("Status Breakdown:")
        for status, count in self._status_breakdown.items():
            logger.info(f"    {status}: {count}")
        logger.info("=" * 60)

    def finish(self) -> None:
        """Finalize the user manager."""
        logger.info("Finalizing User Manager...")
        logger.info(f"  Total users: {len(self._users)}")
        logger.info(f"  Approved users: {len(self._approved_users)}")
        logger.info(f"  New users: {len(self._new_users)}")
        logger.info(f"  Updated users: {len(self._updated_users)}")
        logger.info("User Manager finalized")
