"""Order Manager - Main orchestrator for Order Management workflow.

This is the main entry point for the order management process.
It coordinates between:
- SheetHandler: Google Sheets operations
- APIHandler: AestheticRxNetwork API operations
- OrderComparator: Order comparison logic

Workflow:
1. Get API data of orders with status only 'pending' → paymentToProcess
2. Read Google Sheet file → sheetPayments
3. filtered_payment_data = [compare on ID for both data for same ID]
4. new_orders = [API pending orders NOT in sheet] → these are new orders
5. For payment in filtered_payment_data:
   - If paymentToProcess has order with pending status while from Google Sheet it is completed:
     - API call to update the status
     - If response is 200 OK → add to successfullyProcessedPayment
6. For each successfulPayment in successfullyProcessedPayment:
   - Update these row status to completed in the source file
7. Append new_orders to source sheet (new orders that don't exist in sheet yet)
"""

from config import CONFIG
from libraries.logger import logger
from processes.order.api_handler import APIHandler
from processes.order.comparator import OrderComparator
from processes.order.sheet_handler import SheetHandler


class OrderManager:
    """Main orchestrator for the Order Management workflow."""

    def __init__(self) -> None:
        """Initialize the Order Manager."""
        logger.info("=" * 60)
        logger.info("Initializing Order Manager")
        logger.info("=" * 60)

        # Log configuration
        logger.info(f"Google Drive Folder: {CONFIG.GOOGLE_DRIVE_FOLDER_ID}")
        logger.info(f"Spreadsheet Prefix: {CONFIG.SPREADSHEET_NAME_PREFIX}")

        # Initialize handlers
        self.api_handler = APIHandler()
        self.sheet_handler = SheetHandler()
        self.comparator = OrderComparator()

        # Data storage
        self.payment_to_process: list[dict] = []  # API orders (pending only)
        self.api_completed_orders: list[dict] = []  # API orders (completed)
        self.sheet_payments: list[dict] = []  # Orders from Google Sheet
        self.filtered_payment_data: list[dict] = []  # Orders in both lists
        self.new_orders: list[dict] = []  # New orders (API pending, NOT in sheet)
        self.successfully_processed_payment: list[dict] = []  # Orders updated successfully
        self.synced_from_api: list[dict] = []  # Orders synced from API (already completed)

        self.orders: list[dict] = []
        self.updated_order_ids: list[str] = []
        self.synced_order_ids: list[str] = []  # Orders synced from API to sheet
        self.new_order_count: int = 0
        self.spreadsheet_id: str = CONFIG.SOURCE_SPREADSHEET_ID  # Always use source sheet

        # Report data
        self.duplicates_removed: list[str] = []
        self.status_breakdown: dict[str, int] = {}
        self.doctor_debts: list[dict] = []  # Doctor debts (pending orders grouped by doctor)

        logger.info("=" * 60)
        logger.info("Order Manager initialized")
        logger.info("=" * 60)

    def start(self) -> None:
        """Start the order management workflow."""
        logger.info("=" * 60)
        logger.info("Starting Order Management Workflow")
        logger.info("=" * 60)

        # ============================================
        # STEP 0: Remove duplicates from source sheet
        # ============================================
        self._remove_duplicates()

        # ============================================
        # STEP 1: Get API data (pending status only)
        # ============================================
        self._fetch_payment_to_process()

        if not self.payment_to_process:
            logger.warning("No pending orders found from API!")
            return

        # ============================================
        # STEP 2: Read Google Sheet file
        # ============================================
        self._read_sheet_payments()

        if not self.sheet_payments:
            logger.info("No existing orders in Google Sheet - all API orders are NEW")
            # All pending orders are new, append them
            self.new_orders = self.payment_to_process
            self._append_new_orders()
            self._log_completion()
            return

        # ============================================
        # STEP 3: Compare on ID for both data
        # ============================================
        self._filter_matching_orders()

        # ============================================
        # STEP 4: Find NEW orders (API pending but NOT in sheet)
        # ============================================
        self._find_new_orders()

        # ============================================
        # STEP 5: Process orders and update API
        # ============================================
        if self.filtered_payment_data:
            self._process_payments()
        else:
            logger.info("No matching orders to process")

        # ============================================
        # STEP 5.5: Sync completed orders from API to sheet
        # NEW SCENARIO: If API status is already 'completed', just update the sheet
        # ============================================
        self._sync_completed_from_api()

        # ============================================
        # STEP 6: Update source sheet rows
        # ============================================
        if self.successfully_processed_payment or self.synced_from_api:
            self._update_source_sheet()

        # ============================================
        # STEP 7: Append NEW orders to source sheet
        # ============================================
        if self.new_orders:
            self._append_new_orders()

        # ============================================
        # STEP 8: Calculate doctor debts from pending orders
        # ============================================
        self._calculate_doctor_debts()

        # Log completion
        self._log_completion()

    def _remove_duplicates(self) -> None:
        """Step 0: Remove any duplicate rows from source sheet."""
        logger.info("=" * 60)
        logger.info("STEP 0: Checking for duplicates in source sheet...")
        logger.info("=" * 60)

        removed, duplicate_ids = self.sheet_handler.remove_duplicates_with_ids()
        self.duplicates_removed = duplicate_ids
        if removed > 0:
            logger.info(f"✓ Removed {removed} duplicate rows")
        else:
            logger.info("✓ No duplicates found")

    def _fetch_payment_to_process(self) -> None:
        """Step 1: Get API data of orders with status only 'pending'."""
        logger.info("=" * 60)
        logger.info("STEP 1: Fetching paymentToProcess (pending orders from API)...")
        logger.info("=" * 60)

        self.payment_to_process = self.api_handler.fetch_pending_orders()
        logger.info(f"✓ paymentToProcess: {len(self.payment_to_process)} orders")

    def _read_sheet_payments(self) -> None:
        """Step 2: Read Google Sheet file."""
        logger.info("=" * 60)
        logger.info("STEP 2: Reading sheetPayments (orders from Google Sheet)...")
        logger.info("=" * 60)

        self.sheet_payments = self.sheet_handler.read_sheet_payments()
        self.status_breakdown = self.sheet_handler.get_status_breakdown()
        logger.info(f"✓ sheetPayments: {len(self.sheet_payments)} orders")

    def _filter_matching_orders(self) -> None:
        """Step 3: Compare on ID for both data for same ID."""
        logger.info("=" * 60)
        logger.info("STEP 3: Filtering matching orders by ID...")
        logger.info("=" * 60)

        self.filtered_payment_data = self.comparator.filter_matching_orders(
            payment_to_process=self.payment_to_process,
            sheet_payments=self.sheet_payments,
        )
        logger.info(f"✓ filtered_payment_data: {len(self.filtered_payment_data)} orders")

    def _find_new_orders(self) -> None:
        """Step 4: Find NEW orders (API pending but NOT in sheet)."""
        logger.info("=" * 60)
        logger.info("STEP 4: Finding NEW orders (API pending, NOT in sheet)...")
        logger.info("=" * 60)

        self.new_orders = self.comparator.find_new_orders(
            payment_to_process=self.payment_to_process,
            sheet_payments=self.sheet_payments,
        )
        logger.info(f"✓ new_orders: {len(self.new_orders)} orders")

    def _process_payments(self) -> None:
        """Step 5: Process payments and call API to update status."""
        logger.info("=" * 60)
        logger.info("STEP 5: Processing payments...")
        logger.info("=" * 60)

        # Find orders to update (API pending + Sheet completed)
        orders_to_update = self.comparator.find_orders_to_update(self.filtered_payment_data)

        if not orders_to_update:
            logger.info("No orders need status update")
            return

        logger.info(f"Processing {len(orders_to_update)} orders for API update...")

        # Process each order
        for order_data in orders_to_update:
            order_id = order_data["order_id"]
            payment_amount = order_data["payment_amount"]

            # Call API to update status
            success = self.api_handler.update_order_status(
                order_id=order_id,
                payment_status="completed",
                payment_amount=payment_amount,
                notes="Status updated via automation - marked as completed in sheet",
            )

            # If response is 200 OK, add to successfully processed
            if success:
                self.successfully_processed_payment.append(order_data)
                self.updated_order_ids.append(order_id)
                logger.info(f"✓ Added {order_id} to successfullyProcessedPayment")
            else:
                logger.warning(f"✗ Failed to process {order_id}")

        logger.info(f"✓ successfullyProcessedPayment: {len(self.successfully_processed_payment)} orders")

    def _sync_completed_from_api(self) -> None:
        """Step 5.5: Sync completed orders from API to sheet.

        NEW SCENARIO: If API already has status='completed' but sheet doesn't,
        just update the sheet to 'completed' without calling API.
        """
        logger.info("=" * 60)
        logger.info("STEP 5.5: Syncing completed orders from API to sheet...")
        logger.info("=" * 60)

        # Fetch completed orders from API
        self.api_completed_orders = self.api_handler.fetch_completed_orders()

        if not self.api_completed_orders:
            logger.info("No completed orders found in API")
            return

        # Find orders that need to be synced (API=completed, Sheet!=completed)
        orders_to_sync = self.comparator.find_orders_to_sync_from_api(
            api_completed_orders=self.api_completed_orders,
            sheet_payments=self.sheet_payments,
        )

        if not orders_to_sync:
            logger.info("All completed orders are already synced in sheet")
            return

        # Add to synced list (no API call needed, just sheet update)
        for order_data in orders_to_sync:
            order_id = order_data["order_id"]
            self.synced_from_api.append(order_data)
            self.synced_order_ids.append(order_id)
            logger.info(f"✓ Will sync {order_id} from API to sheet")

        logger.info(f"✓ synced_from_api: {len(self.synced_from_api)} orders to sync")

    def _update_source_sheet(self) -> None:
        """Step 6: Update source sheet rows to 'completed'."""
        logger.info("=" * 60)
        logger.info("STEP 6: Updating source sheet rows → 'completed'...")
        logger.info("=" * 60)

        # Get order IDs from successfully processed payments (API was updated)
        api_updated_ids = [p["order_id"] for p in self.successfully_processed_payment]

        # Get order IDs from synced orders (API was already completed)
        synced_ids = [p["order_id"] for p in self.synced_from_api]

        # Combine all IDs to update
        all_order_ids = api_updated_ids + synced_ids

        if api_updated_ids:
            logger.info(f"Orders updated via API ({len(api_updated_ids)}):")
            for oid in api_updated_ids:
                logger.info(f"  📋 {oid} (API updated → Sheet update)")

        if synced_ids:
            logger.info(f"Orders synced from API ({len(synced_ids)}):")
            for oid in synced_ids:
                logger.info(f"  🔄 {oid} (API already completed → Sheet update)")

        # Update rows in source sheet
        updated_count = self.sheet_handler.update_rows_status(
            order_ids=all_order_ids,
            new_status="completed",
        )

        logger.info(f"✓ Updated {updated_count} rows in source sheet → 'completed'")

    def _append_new_orders(self) -> None:
        """Step 7: Append NEW orders to source sheet."""
        logger.info("=" * 60)
        logger.info("STEP 7: Appending NEW orders to source sheet...")
        logger.info("=" * 60)

        # Append new orders to source sheet
        self.new_order_count = self.sheet_handler.append_new_orders(self.new_orders)

        # Track all orders
        self.orders = self.payment_to_process

        logger.info(f"✓ Appended {self.new_order_count} new orders to source sheet")

    def _calculate_doctor_debts(self) -> None:
        """Step 8: Calculate doctor debts from pending orders."""
        logger.info("=" * 60)
        logger.info("STEP 8: Calculating doctor debts from pending orders...")
        logger.info("=" * 60)

        self.doctor_debts = self.api_handler.calculate_doctor_debts()

        if self.doctor_debts:
            total_debt = sum(d["total_debt"] for d in self.doctor_debts)
            logger.info(f"✓ Total debt from {len(self.doctor_debts)} doctors: ₨{total_debt:,.2f}")
        else:
            logger.info("✓ No doctor debts found (no pending orders)")

    def _log_completion(self) -> None:
        """Log workflow completion."""
        logger.info("=" * 60)
        logger.info("✅ ORDER MANAGEMENT WORKFLOW COMPLETED!")
        logger.info("=" * 60)
        logger.info(f"paymentToProcess (API pending): {len(self.payment_to_process)}")
        logger.info(f"apiCompletedOrders (API completed): {len(self.api_completed_orders)}")
        logger.info(f"sheetPayments (from Sheet): {len(self.sheet_payments)}")
        logger.info(f"filtered_payment_data (matching): {len(self.filtered_payment_data)}")
        logger.info(f"new_orders (added to sheet): {len(self.new_orders)}")
        logger.info(f"successfullyProcessedPayment (API updated): {len(self.successfully_processed_payment)}")
        logger.info(f"syncedFromAPI (sheet updated): {len(self.synced_from_api)}")
        logger.info(f"doctorDebts: {len(self.doctor_debts)} doctors with pending orders")
        logger.info(f"Source spreadsheet: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")
        logger.info("=" * 60)

    def get_orders(self) -> list[dict]:
        """Get all orders."""
        return self.orders

    def get_updated_order_ids(self) -> list[str]:
        """Get IDs of orders that were updated."""
        return self.updated_order_ids

    def get_spreadsheet_url(self) -> str:
        """Get URL of the source spreadsheet."""
        return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"

    def finish(self) -> None:
        """Finalize the order manager."""
        logger.info("Finalizing Order Manager...")
        logger.info(f"Total pending orders from API: {len(self.payment_to_process)}")
        logger.info(f"Total completed orders from API: {len(self.api_completed_orders)}")
        logger.info(f"New orders added to sheet: {self.new_order_count}")
        logger.info(f"Orders updated to completed (via API): {len(self.updated_order_ids)}")
        logger.info(f"Orders synced from API to sheet: {len(self.synced_order_ids)}")
        logger.info(f"Source spreadsheet: {self.get_spreadsheet_url()}")
        logger.info("Order Manager finalized")
