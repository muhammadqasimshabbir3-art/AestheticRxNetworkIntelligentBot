"""Update Payment Sheet Process.

This module handles updating payment status in Google Sheet.
When RUN_UPDATE_PAYMENT_PROCESS is True and PAYMENT_IDS_LIST is provided,
it updates the specified orders' status from 'pending' to 'paid'.

Usage:
    from processes.payment import UpdatePaymentProcess

    process = UpdatePaymentProcess(payment_ids=["id1", "id2"])
    process.start()
"""

from config import CONFIG
from libraries.google_sheets import GoogleSheetsAPI
from libraries.logger import logger
from libraries.sheet_utils import find_column_index, get_cell_reference


class UpdatePaymentProcess:
    """Process to update payment status in Google Sheet.

    Takes a list of payment IDs and updates their status to 'paid'
    in the source Google Sheet document.
    """

    def __init__(self, payment_ids: list[str]) -> None:
        """Initialize the Update Payment Process.

        Args:
            payment_ids: List of payment IDs to update to 'paid' status
        """
        logger.info("=" * 60)
        logger.info("Initializing Update Payment Process")
        logger.info("=" * 60)

        self.payment_ids = payment_ids
        self._sheets_api: GoogleSheetsAPI | None = None
        self.updated_count: int = 0
        self.failed_ids: list[str] = []
        self.not_found_ids: list[str] = []  # Track IDs not found in sheet

        logger.info(f"Payment IDs to update: {len(self.payment_ids)}")
        for pid in self.payment_ids:
            logger.info(f"  - {pid}")

        logger.info("=" * 60)

    @property
    def sheets_api(self) -> GoogleSheetsAPI:
        """Get Google Sheets API (lazy initialization)."""
        if self._sheets_api is None:
            self._sheets_api = GoogleSheetsAPI()
        return self._sheets_api

    def start(self) -> None:
        """Start the update payment process.

        Updates the status of specified orders from 'pending' to 'paid'
        in the source Google Sheet.
        """
        logger.info("=" * 60)
        logger.info("Starting Update Payment Process")
        logger.info("=" * 60)

        if not self.payment_ids:
            logger.warning("No payment IDs provided - nothing to update")
            return

        try:
            self._update_payment_status()
            self._log_results()
        except Exception as e:
            logger.error(f"Update Payment Process failed: {e}")
            raise

    def _update_payment_status(self) -> None:
        """Update payment status in Google Sheet."""
        logger.info(f"Updating {len(self.payment_ids)} payments to 'paid' status...")
        logger.info(f"Source Sheet: {CONFIG.SOURCE_SPREADSHEET_ID}")

        try:
            # Get sheet info to find actual sheet name
            sheet_info = self.sheets_api.get_sheet_info(CONFIG.SOURCE_SPREADSHEET_ID)
            if sheet_info:
                # get_sheet_info returns list with {"sheetId", "title", "index", ...}
                sheet_name = sheet_info[0].get("title", "Sheet1")
            else:
                sheet_name = "Sheet1"

            logger.info(f"Reading from sheet: '{sheet_name}'")

            # Read current data (no quotes needed for sheet names without spaces)
            data = self.sheets_api.read_data(CONFIG.SOURCE_SPREADSHEET_ID, f"{sheet_name}!A:Z")

            if not data or len(data) < 2:
                logger.warning("No data found in sheet")
                self.not_found_ids = self.payment_ids.copy()
                return

            headers = data[0]

            # Find column indices using utility function
            id_col = find_column_index(headers, ["id", "ID"])
            status_col = find_column_index(
                headers, ["payment_status", "Payment Status", "paymentStatus", "Payment_Status"]
            )

            if id_col == -1:
                logger.error("Could not find ID column in sheet")
                return

            if status_col == -1:
                logger.error("Could not find Payment Status column in sheet")
                return

            logger.info(f"ID column index: {id_col} ({headers[id_col]})")
            logger.info(f"Status column index: {status_col} ({headers[status_col]})")

            # Create set for faster lookup and track found IDs
            payment_ids_set = set(self.payment_ids)
            found_ids: set[str] = set()

            # Update matching rows
            for row_idx, row in enumerate(data[1:], start=2):
                if len(row) > id_col:
                    row_id = str(row[id_col]).strip()

                    if row_id in payment_ids_set:
                        found_ids.add(row_id)

                        # Get current status
                        current_status = row[status_col] if len(row) > status_col else ""

                        logger.info(f"Order {row_id}:")
                        logger.info(f"  Current status: '{current_status}'")

                        # Update to 'paid' using utility function for cell reference
                        cell = get_cell_reference(status_col, row_idx)
                        try:
                            self.sheets_api.write_data(
                                CONFIG.SOURCE_SPREADSHEET_ID,
                                [["paid"]],
                                sheet_name=sheet_name,
                                start_cell=cell,
                            )
                            self.updated_count += 1
                            logger.info(f"  ✓ Updated to 'paid' at cell {cell}")
                        except Exception as e:
                            self.failed_ids.append(row_id)
                            logger.error(f"  ✗ Failed to update: {e}")

            # Track IDs that weren't found in the sheet
            self.not_found_ids = list(payment_ids_set - found_ids)

        except Exception as e:
            logger.error(f"Failed to update payment status: {e}")
            raise

    def _log_results(self) -> None:
        """Log the results of the update process."""
        logger.info("=" * 60)
        logger.info("Update Payment Process Results")
        logger.info("=" * 60)
        logger.info(f"Total IDs provided: {len(self.payment_ids)}")
        logger.info(f"Successfully updated: {self.updated_count}")
        logger.info(f"Failed to update: {len(self.failed_ids)}")
        logger.info(f"Not found in sheet: {len(self.not_found_ids)}")

        if self.failed_ids:
            logger.warning("Failed IDs:")
            for pid in self.failed_ids:
                logger.warning(f"  - {pid}")

        if self.not_found_ids:
            logger.warning("IDs not found in sheet:")
            for pid in self.not_found_ids:
                logger.warning(f"  - {pid}")

        logger.info("=" * 60)

    @property
    def is_successful(self) -> bool:
        """Check if all payments were updated successfully."""
        return self.updated_count == len(self.payment_ids)
