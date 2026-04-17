"""Sheet Handler - Google Sheets operations for Order Management.

Handles:
- Reading orders from Google Sheets (sheetPayments)
- Writing orders to Google Sheets
- Updating order status in sheets
- Creating and managing spreadsheets
"""

import json
from datetime import datetime

from config import CONFIG
from libraries.google_drive import GoogleDriveAPI
from libraries.google_sheets import GoogleSheetsAPI
from libraries.logger import logger
from libraries.sheet_utils import find_column_index, get_cell_reference


class SheetHandler:
    """Handles all Google Sheets operations for order management."""

    def __init__(self) -> None:
        """Initialize the sheet handler with Google APIs."""
        self._drive_api: GoogleDriveAPI | None = None
        self._sheets_api: GoogleSheetsAPI | None = None
        self._last_status_breakdown: dict[str, int] = {}

    def get_status_breakdown(self) -> dict[str, int]:
        """Get the status breakdown from the last read operation."""
        return self._last_status_breakdown

    @property
    def drive_api(self) -> GoogleDriveAPI:
        """Get Google Drive API (lazy initialization)."""
        if self._drive_api is None:
            self._drive_api = GoogleDriveAPI()
        return self._drive_api

    @property
    def sheets_api(self) -> GoogleSheetsAPI:
        """Get Google Sheets API (lazy initialization)."""
        if self._sheets_api is None:
            self._sheets_api = GoogleSheetsAPI()
        return self._sheets_api

    def read_sheet_payments(self) -> list[dict]:
        """Read orders from the source Google Sheet (sheetPayments).

        Reads from: https://docs.google.com/spreadsheets/d/1wNrE75TQzg4Qkyj0enRvdKw1QSFq1NhU3ZGqbhnzX1E

        Returns:
            list[dict]: List of order dictionaries (sheetPayments)
        """
        logger.info("=" * 60)
        logger.info("Reading sheetPayments from Google Sheet...")
        logger.info(f"Sheet ID: {CONFIG.SOURCE_SPREADSHEET_ID}")
        logger.info("=" * 60)

        try:
            # Get sheet name
            sheet_info = self.sheets_api.get_sheet_info(CONFIG.SOURCE_SPREADSHEET_ID)
            if sheet_info:
                # get_sheet_info returns list with {"sheetId", "title", "index", ...}
                sheet_name = sheet_info[0].get("title", "Sheet1")
            else:
                sheet_name = "Sheet1"

            logger.info(f"Reading from sheet: '{sheet_name}'")

            # Read data
            data = self.sheets_api.read_data(CONFIG.SOURCE_SPREADSHEET_ID, f"{sheet_name}!A:Z")

            if not data or len(data) < 2:
                logger.info("No data found in spreadsheet")
                return []

            headers = data[0]
            orders = []

            for row in data[1:]:
                order = {}
                for i, header in enumerate(headers):
                    order[header] = row[i] if i < len(row) else ""
                orders.append(order)

            logger.info(f"✓ Read {len(orders)} orders from sheet")

            # Log status breakdown
            self._log_status_breakdown(orders)

            return orders

        except Exception as e:
            logger.error(f"Failed to read sheet payments: {e}")
            return []

    def _log_status_breakdown(self, orders: list[dict]) -> dict[str, int]:
        """Log and return payment status breakdown."""
        status_counts: dict[str, int] = {}
        for order in orders:
            status = ""
            for key in ["payment_status", "paymentStatus", "Payment Status"]:
                if key in order:
                    status = str(order[key]).lower()
                    break
            status_counts[status] = status_counts.get(status, 0) + 1

        # Store for access
        self._last_status_breakdown = status_counts

        logger.info("Sheet status breakdown:")
        for status, count in sorted(status_counts.items()):
            logger.info(f"  - {status or 'empty'}: {count}")

    def update_rows_status(
        self,
        order_ids: list[str],
        new_status: str = "completed",
    ) -> int:
        """Update the status of specific orders in the source sheet.

        Args:
            order_ids: List of order IDs to update
            new_status: New status value to set

        Returns:
            int: Number of rows updated
        """
        if not order_ids:
            return 0

        logger.info("=" * 60)
        logger.info(f"Updating {len(order_ids)} rows to status '{new_status}'...")
        logger.info("=" * 60)

        try:
            # Get sheet info
            sheet_info = self.sheets_api.get_sheet_info(CONFIG.SOURCE_SPREADSHEET_ID)
            if sheet_info:
                # get_sheet_info returns list with {"sheetId", "title", "index", ...}
                sheet_name = sheet_info[0].get("title", "Sheet1")
            else:
                sheet_name = "Sheet1"

            # Read current data
            data = self.sheets_api.read_data(CONFIG.SOURCE_SPREADSHEET_ID, f"{sheet_name}!A:Z")

            if not data or len(data) < 2:
                logger.warning("No data found in sheet")
                return 0

            headers = data[0]

            # Find column indices using utility function
            id_col = find_column_index(headers, ["id", "ID"])
            status_col = find_column_index(headers, ["payment_status", "Payment Status", "paymentStatus"])

            if id_col == -1:
                logger.warning("Could not find ID column")
                return 0

            if status_col == -1:
                logger.warning("Could not find Payment Status column")
                return 0

            # Update matching rows
            updated_count = 0
            order_ids_set = set(order_ids)

            for row_idx, row in enumerate(data[1:], start=2):
                if len(row) > id_col:
                    row_id = str(row[id_col]).strip()
                    if row_id in order_ids_set:
                        # Update this cell using utility function
                        cell = get_cell_reference(status_col, row_idx)
                        self.sheets_api.write_data(
                            CONFIG.SOURCE_SPREADSHEET_ID,
                            [[new_status]],
                            sheet_name=sheet_name,
                            start_cell=cell,
                        )
                        updated_count += 1
                        logger.info(f"  ✓ Updated order {row_id} at cell {cell}")

            logger.info(f"✓ Updated {updated_count} rows in source sheet")
            return updated_count

        except Exception as e:
            logger.error(f"Failed to update rows: {e}")
            return 0

    def get_existing_ids(self) -> set[str]:
        """Get all existing order IDs from the source spreadsheet.

        Returns:
            set[str]: Set of existing order IDs
        """
        try:
            sheet_info = self.sheets_api.get_sheet_info(CONFIG.SOURCE_SPREADSHEET_ID)
            sheet_name = sheet_info[0].get("title", "Sheet1") if sheet_info else "Sheet1"

            data = self.sheets_api.read_data(CONFIG.SOURCE_SPREADSHEET_ID, f"'{sheet_name}'!A:A")

            if not data or len(data) < 2:
                return set()

            # Skip header row, get all IDs
            existing_ids = set()
            for row in data[1:]:
                if row and row[0]:
                    existing_ids.add(str(row[0]).strip())

            return existing_ids

        except Exception as e:
            logger.warning(f"Could not get existing IDs: {e}")
            return set()

    def remove_duplicates(self) -> int:
        """Remove duplicate rows from the source spreadsheet.

        Keeps the first occurrence of each ID and removes subsequent duplicates.

        Returns:
            int: Number of duplicate rows removed
        """
        count, _ = self.remove_duplicates_with_ids()
        return count

    def remove_duplicates_with_ids(self) -> tuple[int, list[str]]:
        """Remove duplicate rows and return the IDs of removed duplicates.

        Keeps the first occurrence of each ID and removes subsequent duplicates.

        Returns:
            tuple[int, list[str]]: (Number removed, List of duplicate IDs)
        """
        logger.info("=" * 60)
        logger.info("Checking for duplicate rows in source sheet...")
        logger.info("=" * 60)

        try:
            # Get sheet info
            sheet_info = self.sheets_api.get_sheet_info(CONFIG.SOURCE_SPREADSHEET_ID)
            sheet_name = sheet_info[0].get("title", "Sheet1") if sheet_info else "Sheet1"
            sheet_id = sheet_info[0].get("sheetId", 0) if sheet_info else 0

            # Read all data
            data = self.sheets_api.read_data(CONFIG.SOURCE_SPREADSHEET_ID, f"'{sheet_name}'!A:Z")

            if not data or len(data) < 2:
                logger.info("No data to check for duplicates")
                return 0, []

            # Skip headers row, work with data rows only
            rows = data[1:]

            # Find duplicate row indices (0-based, relative to data rows)
            seen_ids: set[str] = set()
            duplicate_indices: list[int] = []
            duplicate_ids: list[str] = []

            for idx, row in enumerate(rows):
                if row:
                    order_id = str(row[0]).strip() if row[0] else ""
                    if order_id:
                        if order_id in seen_ids:
                            duplicate_indices.append(idx)
                            duplicate_ids.append(order_id)
                            logger.info(f"  🔄 Duplicate found: {order_id} at row {idx + 2}")
                        else:
                            seen_ids.add(order_id)

            if not duplicate_indices:
                logger.info("✓ No duplicates found")
                return 0, []

            logger.info(f"Found {len(duplicate_indices)} duplicate rows to remove")

            # Delete rows from bottom to top to preserve indices
            # Sort indices in reverse but keep track of the IDs
            sorted_pairs = sorted(zip(duplicate_indices, duplicate_ids, strict=False), reverse=True)

            for idx, _dup_id in sorted_pairs:
                # Row index in sheet (1-based, +1 for header)
                row_num = idx + 2

                # Delete row using delete_rows (start_index is 0-based)
                self.sheets_api.delete_rows(
                    CONFIG.SOURCE_SPREADSHEET_ID,
                    sheet_id=sheet_id,
                    start_index=row_num - 1,  # 0-based for API
                    num_rows=1,
                )
                logger.info(f"  ✓ Deleted duplicate row {row_num}")

            logger.info(f"✓ Removed {len(duplicate_indices)} duplicate rows")
            return len(duplicate_indices), duplicate_ids

        except Exception as e:
            logger.error(f"Failed to remove duplicates: {e}")
            return 0, []

    def append_new_orders(self, new_orders: list[dict]) -> int:
        """Append new orders to the source spreadsheet.

        Checks for existing IDs to prevent duplicates.

        Args:
            new_orders: List of new order dictionaries to append

        Returns:
            int: Number of orders appended
        """
        if not new_orders:
            logger.info("No new orders to append")
            return 0

        logger.info("=" * 60)
        logger.info(f"Appending {len(new_orders)} new orders to source sheet...")
        logger.info(f"Sheet ID: {CONFIG.SOURCE_SPREADSHEET_ID}")
        logger.info("=" * 60)

        try:
            # Get existing IDs to prevent duplicates
            existing_ids = self.get_existing_ids()
            logger.info(f"Found {len(existing_ids)} existing orders in sheet")

            # Get sheet name
            sheet_info = self.sheets_api.get_sheet_info(CONFIG.SOURCE_SPREADSHEET_ID)
            sheet_name = sheet_info[0].get("title", "Sheet1") if sheet_info else "Sheet1"

            # Convert orders to rows, skipping duplicates
            headers = CONFIG.ORDER_HEADERS
            rows = []
            skipped = 0

            for order in new_orders:
                order_id = str(order.get("id") or order.get("ID") or "").strip()

                if order_id in existing_ids:
                    logger.info(f"  ⏭ Skipping duplicate: {order_id}")
                    skipped += 1
                    continue

                row = self._order_to_row(order, headers)
                rows.append(row)
                existing_ids.add(order_id)  # Track to avoid within-batch duplicates
                logger.info(f"  📝 Adding order: {order_id}")

            if not rows:
                logger.info(f"All {skipped} orders already exist in sheet - nothing to append")
                return 0

            # Append rows to sheet
            self.sheets_api.append_data(
                CONFIG.SOURCE_SPREADSHEET_ID,
                rows,
                sheet_name=sheet_name,
            )

            logger.info(f"✓ Appended {len(rows)} new orders (skipped {skipped} duplicates)")
            return len(rows)

        except Exception as e:
            logger.error(f"Failed to append new orders: {e}")
            return 0

    def create_output_spreadsheet(self, orders: list[dict]) -> str:
        """Create a new output spreadsheet with all orders.

        Creates a new file with naming convention: PREFIX_YYYY-MM-DD
        Falls back to updating the source spreadsheet if creation fails.

        Args:
            orders: List of order dictionaries to write

        Returns:
            str: Spreadsheet ID
        """
        # Generate title with date
        current_date = datetime.now().strftime("%Y-%m-%d")
        title = f"{CONFIG.SPREADSHEET_NAME_PREFIX}_{current_date}"

        logger.info("=" * 60)
        logger.info(f"Creating output spreadsheet: {title}")
        logger.info("=" * 60)

        try:
            # Create spreadsheet
            spreadsheet_id = self.sheets_api.create_spreadsheet(title)

            # Move to folder
            logger.info(f"Moving to folder {CONFIG.GOOGLE_DRIVE_FOLDER_ID}...")
            try:
                self.drive_api.move_file(spreadsheet_id, CONFIG.GOOGLE_DRIVE_FOLDER_ID)
                logger.info("✓ Moved to folder successfully")
            except Exception as e:
                logger.warning(f"Could not move to folder: {e}")

            # Write orders
            self._write_orders_to_sheet(spreadsheet_id, orders)

            logger.info(f"✓ Created spreadsheet: {spreadsheet_id}")
            logger.info(f"  URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

            return spreadsheet_id

        except Exception as e:
            logger.warning(f"Could not create new spreadsheet: {e}")
            logger.info("Falling back to updating source spreadsheet...")

            # Fall back to source spreadsheet
            spreadsheet_id = CONFIG.SOURCE_SPREADSHEET_ID

            try:
                # Write orders to source spreadsheet
                self._write_orders_to_sheet(spreadsheet_id, orders)

                logger.info(f"✓ Updated source spreadsheet: {spreadsheet_id}")
                logger.info(f"  URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

                return spreadsheet_id
            except Exception as write_error:
                logger.error(f"Failed to write to source spreadsheet: {write_error}")
                raise

    def _write_orders_to_sheet(
        self,
        spreadsheet_id: str,
        orders: list[dict],
    ) -> None:
        """Write orders to a spreadsheet.

        Args:
            spreadsheet_id: Target spreadsheet ID
            orders: List of order dictionaries
        """
        if not orders:
            logger.info("No orders to write")
            return

        logger.info(f"Writing {len(orders)} orders to spreadsheet...")

        # Get sheet name
        try:
            sheet_info = self.sheets_api.get_sheet_info(spreadsheet_id)
            # get_sheet_info returns list with {"sheetId", "title", "index", ...}
            sheet_name = sheet_info[0].get("title", "Sheet1") if sheet_info else "Sheet1"
        except Exception:
            sheet_name = "Sheet1"

        # Use configured headers
        headers = CONFIG.ORDER_HEADERS

        # Write headers
        self.sheets_api.write_data(spreadsheet_id, [headers], sheet_name=sheet_name, start_cell="A1")
        logger.info(f"✓ Written {len(headers)} headers")

        # Convert orders to rows
        rows = []
        for order in orders:
            row = self._order_to_row(order, headers)
            rows.append(row)

        # Write data
        if rows:
            self.sheets_api.write_data(spreadsheet_id, rows, sheet_name=sheet_name, start_cell="A2")
            logger.info(f"✓ Written {len(rows)} data rows")

        # Format
        self.sheets_api.format_header_row(spreadsheet_id)
        self.sheets_api.auto_resize_columns(spreadsheet_id)
        logger.info("✓ Applied formatting")

    def _order_to_row(self, order: dict, headers: list[str]) -> list[str]:
        """Convert an order dictionary to a row based on headers.

        Args:
            order: Order dictionary
            headers: List of header names

        Returns:
            list[str]: Row values
        """
        row = []
        for header in headers:
            # Try different key variants
            key_variants = [
                header,
                header.lower(),
                header.lower().replace(" ", "_"),
                header.replace(" ", "_").lower(),
            ]

            value = ""
            for key in key_variants:
                if key in order:
                    value = order[key]
                    break

            # Convert value to string
            if value is None:
                value = ""
            elif isinstance(value, (dict, list)):
                value = json.dumps(value)
            else:
                value = str(value)

            row.append(value)

        return row

    def get_file_info(self, file_id: str) -> dict:
        """Get file metadata.

        Args:
            file_id: File ID

        Returns:
            dict: File info
        """
        return self.drive_api.get_file(file_id)
