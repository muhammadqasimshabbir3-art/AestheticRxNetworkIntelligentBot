"""Advertisement Manager - Orchestrates the Advertisement Management workflow.

Workflow:
1. Update Payment Status in sheet for provided IDs → set to "paid"
2. Fetch all advertisements from API
3. Filter for ads with status="pending"
4. Approve pending ads via API (status: pending → active)
5. Update Status in sheet to "active" for approved ads
"""


from libraries.google_sheets import GoogleSheetsAPI
from libraries.logger import logger
from libraries.qwebsite_api import QWebsiteAPI
from libraries.sheet_utils import column_index_to_letter, find_column_index

# Advertisement spreadsheet configuration
ADVERTISEMENT_SPREADSHEET_ID = "1E9eA0XrEv7BqvYUgvLQOlaqw9walZUmC7p8atgh2D_s"

# Column headers for advertisement sheet
ADVERTISEMENT_HEADERS = [
    "ID",
    "Doctor ID",
    "Doctor Name",
    "Doctor Email",
    "Clinic Name",
    "Title",
    "Description",
    "Type",
    "Selected Area",
    "Duration Hours",
    "Total Cost",
    "Paid Amount",
    "Start Date",
    "End Date",
    "Status",
    "Payment Status",
    "Payment Method",
    "Impressions",
    "Clicks",
    "Views",
    "Is Quitable",
    "Is Closed By User",
    "Audio Enabled",
    "Rejection Reason",
    "Admin Notes",
    "Created At",
    "Updated At",
]


class AdvertisementManager:
    """Main orchestrator for the Advertisement Management workflow."""

    def __init__(self, paid_ids_list: list[str] | None = None) -> None:
        """Initialize the Advertisement Manager.

        Args:
            paid_ids_list: List of advertisement IDs to mark as 'paid' in the sheet
        """
        logger.info("=" * 60)
        logger.info("Initializing Advertisement Manager")
        logger.info("=" * 60)

        # Input data
        self._paid_ids_list = paid_ids_list or []

        # Data storage
        self._all_advertisements: list[dict] = []
        self._pending_advertisements: list[dict] = []
        self._approved_advertisements: list[dict] = []
        self._failed_approvals: list[str] = []
        self._payment_updated_ids: list[str] = []
        self._payment_update_failed_ids: list[str] = []
        self._status_updated_ids: list[str] = []
        self._total_count: int = 0
        self._status_breakdown: dict[str, int] = {}
        self._type_breakdown: dict[str, int] = {}
        self._payment_status_breakdown: dict[str, int] = {}

        # Sheet data
        self._sheet_data: list[list] = []
        self._sheet_name: str = "Sheet1"
        self._id_column_index: int = 0
        self._status_column_index: int = 14  # "Status" column
        self._payment_status_column_index: int = 15  # "Payment Status" column

        # API and Sheets
        self._api: QWebsiteAPI | None = None
        self._sheets_api: GoogleSheetsAPI | None = None

        logger.info(f"Paid IDs to update: {self._paid_ids_list}")
        logger.info("Advertisement Manager initialized")

    @property
    def all_advertisements(self) -> list[dict]:
        """Get all advertisements."""
        return self._all_advertisements

    @property
    def pending_advertisements(self) -> list[dict]:
        """Get pending advertisements."""
        return self._pending_advertisements

    @property
    def approved_advertisements(self) -> list[dict]:
        """Get approved advertisements."""
        return self._approved_advertisements

    @property
    def failed_approvals(self) -> list[str]:
        """Get failed approval IDs."""
        return self._failed_approvals

    @property
    def payment_updated_ids(self) -> list[str]:
        """Get IDs with updated payment status."""
        return self._payment_updated_ids

    @property
    def payment_update_failed_ids(self) -> list[str]:
        """Get IDs where payment update failed."""
        return self._payment_update_failed_ids

    @property
    def status_updated_ids(self) -> list[str]:
        """Get IDs with updated status to active."""
        return self._status_updated_ids

    @property
    def total_count(self) -> int:
        """Get total advertisement count."""
        return self._total_count

    @property
    def status_breakdown(self) -> dict[str, int]:
        """Get status breakdown."""
        return self._status_breakdown

    @property
    def type_breakdown(self) -> dict[str, int]:
        """Get type breakdown (video/image/animation)."""
        return self._type_breakdown

    @property
    def payment_status_breakdown(self) -> dict[str, int]:
        """Get payment status breakdown."""
        return self._payment_status_breakdown

    def start(self) -> None:
        """Start the advertisement management workflow."""
        logger.info("=" * 60)
        logger.info("Starting Advertisement Management Workflow")
        logger.info("=" * 60)

        # Step 1: Initialize APIs
        self._init_apis()

        # Step 2: Read existing sheet data
        self._read_sheet_data()

        # Step 3: Update Payment Status for provided IDs in sheet
        if self._paid_ids_list:
            self._update_payment_status_in_sheet()

        # Step 4: Fetch all advertisements from API
        self._fetch_advertisements()

        if not self._all_advertisements:
            logger.warning("No advertisements found")
            return

        # Step 5: Calculate statistics
        self._calculate_statistics()

        # Step 6: Filter for pending advertisements
        self._filter_pending_advertisements()

        # Step 7: Approve pending advertisements and update sheet status
        if self._pending_advertisements:
            self._approve_and_update_sheet()

        # Log completion
        self._log_completion()

    def _init_apis(self) -> None:
        """Initialize the APIs."""
        logger.info("Initializing APIs...")

        # Initialize Google Sheets API first (for reading existing data)
        self._sheets_api = GoogleSheetsAPI()

        # Initialize Q Website API
        self._api = QWebsiteAPI(auto_authenticate=True)

    def _read_sheet_data(self) -> None:
        """Read existing data from the sheet."""
        logger.info("=" * 60)
        logger.info("Reading existing sheet data...")
        logger.info("=" * 60)

        try:
            # Get sheet info
            sheet_info = self._sheets_api.get_sheet_info(ADVERTISEMENT_SPREADSHEET_ID)
            if sheet_info and len(sheet_info) > 0:
                self._sheet_name = sheet_info[0].get("title", "Sheet1")
            else:
                self._sheet_name = "Sheet1"

            logger.info(f"Sheet name: {self._sheet_name}")

            # Read all data
            read_range = f"'{self._sheet_name}'!A:AA"
            self._sheet_data = self._sheets_api.read_data(
                ADVERTISEMENT_SPREADSHEET_ID, read_range
            )

            if self._sheet_data and len(self._sheet_data) > 0:
                headers = self._sheet_data[0]
                logger.info(f"Found {len(self._sheet_data) - 1} rows in sheet")

                # Find column indices
                self._id_column_index = find_column_index(headers, ["ID", "id"])
                self._status_column_index = find_column_index(headers, ["Status", "status"])
                self._payment_status_column_index = find_column_index(
                    headers, ["Payment Status", "payment_status", "PaymentStatus"]
                )

                logger.info(f"ID column index: {self._id_column_index}")
                logger.info(f"Status column index: {self._status_column_index}")
                logger.info(f"Payment Status column index: {self._payment_status_column_index}")
            else:
                logger.info("Sheet is empty")
                self._sheet_data = []

        except Exception as e:
            logger.error(f"Failed to read sheet data: {e}")
            self._sheet_data = []

    def _update_payment_status_in_sheet(self) -> None:
        """Update Payment Status to 'paid' for provided IDs in the sheet."""
        logger.info("=" * 60)
        logger.info("Updating Payment Status in sheet...")
        logger.info(f"IDs to update: {self._paid_ids_list}")
        logger.info("=" * 60)

        if not self._sheet_data or len(self._sheet_data) < 2:
            logger.warning("No data in sheet to update")
            for ad_id in self._paid_ids_list:
                self._payment_update_failed_ids.append(ad_id)
            return

        # Build ID to row mapping (row numbers are 1-based, skip header)
        id_to_row: dict[str, int] = {}
        for row_idx, row in enumerate(self._sheet_data[1:], start=2):  # Start from row 2 (after header)
            if len(row) > self._id_column_index:
                row_id = str(row[self._id_column_index]).strip()
                id_to_row[row_id] = row_idx

        # Update each ID
        for ad_id in self._paid_ids_list:
            if ad_id in id_to_row:
                row_num = id_to_row[ad_id]
                col_letter = column_index_to_letter(self._payment_status_column_index)
                cell_ref = f"'{self._sheet_name}'!{col_letter}{row_num}"

                try:
                    self._sheets_api.write_data(
                        spreadsheet_id=ADVERTISEMENT_SPREADSHEET_ID,
                        data=[["paid"]],
                        sheet_name=self._sheet_name,
                        start_cell=f"{col_letter}{row_num}",
                    )
                    logger.info(f"✓ Updated Payment Status to 'paid' for ID {ad_id} at {cell_ref}")
                    self._payment_updated_ids.append(ad_id)
                except Exception as e:
                    logger.error(f"✗ Failed to update Payment Status for ID {ad_id}: {e}")
                    self._payment_update_failed_ids.append(ad_id)
            else:
                logger.warning(f"⚠ ID not found in sheet: {ad_id}")
                self._payment_update_failed_ids.append(ad_id)

        logger.info(f"Payment Status updates: {len(self._payment_updated_ids)} successful, {len(self._payment_update_failed_ids)} failed")

    def _fetch_advertisements(self) -> None:
        """Fetch all advertisements from API."""
        logger.info("=" * 60)
        logger.info("Fetching advertisements from API...")
        logger.info("=" * 60)

        try:
            # Call the admin endpoint for all advertisements
            logger.info("Making GET request to /api/video-advertisements/admin/all")
            response = self._api.get("/api/video-advertisements/admin/all")
            data = response.json()

            if isinstance(data, dict) and data.get("success"):
                ads_data = data.get("data", {})
                self._all_advertisements = ads_data.get("advertisements", [])
                pagination = ads_data.get("pagination", {})
                self._total_count = pagination.get("total", len(self._all_advertisements))

                logger.info(f"✓ Fetched {len(self._all_advertisements)} advertisements")
                logger.info(f"  Total in system: {self._total_count}")
            else:
                logger.warning("⚠ Unexpected API response format")
                self._all_advertisements = []

        except Exception as e:
            logger.error(f"✗ Failed to fetch advertisements: {e}")
            self._all_advertisements = []

    def _calculate_statistics(self) -> None:
        """Calculate statistics from advertisements."""
        logger.info("Calculating advertisement statistics...")

        self._status_breakdown = {}
        self._type_breakdown = {}
        self._payment_status_breakdown = {}

        for ad in self._all_advertisements:
            # Status breakdown
            status = ad.get("status", "unknown")
            self._status_breakdown[status] = self._status_breakdown.get(status, 0) + 1

            # Type breakdown
            ad_type = ad.get("type", "unknown")
            self._type_breakdown[ad_type] = self._type_breakdown.get(ad_type, 0) + 1

            # Payment status breakdown
            payment_status = ad.get("payment_status", "unknown")
            self._payment_status_breakdown[payment_status] = (
                self._payment_status_breakdown.get(payment_status, 0) + 1
            )

        logger.info(f"Status breakdown: {self._status_breakdown}")
        logger.info(f"Type breakdown: {self._type_breakdown}")
        logger.info(f"Payment status: {self._payment_status_breakdown}")

    def _filter_pending_advertisements(self) -> None:
        """Filter for pending advertisements."""
        logger.info("=" * 60)
        logger.info("Filtering for pending advertisements...")
        logger.info("=" * 60)

        self._pending_advertisements = [
            ad for ad in self._all_advertisements if ad.get("status") == "pending"
        ]

        logger.info(f"Found {len(self._pending_advertisements)} pending advertisements")
        for ad in self._pending_advertisements:
            logger.info(f"  - {ad.get('id')}: {ad.get('title')}")

    def _approve_and_update_sheet(self) -> None:
        """Approve pending advertisements via API and update Status in sheet to 'active'."""
        logger.info("=" * 60)
        logger.info("Approving pending advertisements and updating sheet...")
        logger.info("=" * 60)

        # Build ID to row mapping for existing sheet data
        id_to_row: dict[str, int] = {}
        if self._sheet_data and len(self._sheet_data) > 1:
            for row_idx, row in enumerate(self._sheet_data[1:], start=2):
                if len(row) > self._id_column_index:
                    row_id = str(row[self._id_column_index]).strip()
                    id_to_row[row_id] = row_idx

        for ad in self._pending_advertisements:
            ad_id = ad.get("id")
            if not ad_id:
                continue

            try:
                logger.info(f"Approving advertisement: {ad_id} - {ad.get('title')}")

                # Call approve API
                endpoint = f"/api/video-advertisements/admin/{ad_id}/approve"
                response = self._api.put(endpoint)
                data = response.json()

                if data.get("success"):
                    logger.info(f"✓ API Approved: {ad_id}")

                    # Store approved advertisement with updated data
                    approved_ad = data.get("data", ad)
                    self._approved_advertisements.append(approved_ad)

                    # Update Status in sheet to 'active'
                    if ad_id in id_to_row:
                        row_num = id_to_row[ad_id]
                        col_letter = column_index_to_letter(self._status_column_index)

                        try:
                            self._sheets_api.write_data(
                                spreadsheet_id=ADVERTISEMENT_SPREADSHEET_ID,
                                data=[["active"]],
                                sheet_name=self._sheet_name,
                                start_cell=f"{col_letter}{row_num}",
                            )
                            logger.info(f"✓ Updated Status to 'active' in sheet for ID {ad_id}")
                            self._status_updated_ids.append(ad_id)
                        except Exception as e:
                            logger.error(f"✗ Failed to update sheet status for {ad_id}: {e}")
                    else:
                        logger.info(f"  ID {ad_id} not in existing sheet (will be added if needed)")
                        self._status_updated_ids.append(ad_id)
                else:
                    logger.warning(
                        f"⚠ Failed to approve {ad_id}: {data.get('message', 'Unknown error')}"
                    )
                    self._failed_approvals.append(ad_id)

            except Exception as e:
                logger.error(f"✗ Error approving {ad_id}: {e}")
                self._failed_approvals.append(ad_id)

        logger.info(f"Successfully approved: {len(self._approved_advertisements)}")
        logger.info(f"Status updated in sheet: {len(self._status_updated_ids)}")
        logger.info(f"Failed approvals: {len(self._failed_approvals)}")

    def _log_completion(self) -> None:
        """Log workflow completion."""
        logger.info("=" * 60)
        logger.info("✅ ADVERTISEMENT MANAGEMENT WORKFLOW COMPLETED!")
        logger.info("=" * 60)
        logger.info(f"Total advertisements fetched: {self._total_count}")
        logger.info(f"Pending advertisements found: {len(self._pending_advertisements)}")
        logger.info(f"Successfully approved (API): {len(self._approved_advertisements)}")
        logger.info(f"Status updated to 'active' in sheet: {len(self._status_updated_ids)}")
        logger.info(f"Failed approvals: {len(self._failed_approvals)}")
        logger.info(f"Payment Status updated to 'paid': {len(self._payment_updated_ids)}")
        logger.info(f"Payment update failed: {len(self._payment_update_failed_ids)}")
        logger.info(f"Status breakdown: {self._status_breakdown}")
        logger.info(f"Type breakdown: {self._type_breakdown}")
        logger.info(f"Payment status: {self._payment_status_breakdown}")
        sheet_url = f"https://docs.google.com/spreadsheets/d/{ADVERTISEMENT_SPREADSHEET_ID}"
        logger.info(f"Sheet URL: {sheet_url}")
        logger.info("=" * 60)

    def finish(self) -> None:
        """Finalize the advertisement manager."""
        logger.info("Finalizing Advertisement Manager...")
        logger.info(f"Total advertisements processed: {self._total_count}")
        logger.info(f"Approved: {len(self._approved_advertisements)}")
        logger.info("Advertisement Manager finalized")
