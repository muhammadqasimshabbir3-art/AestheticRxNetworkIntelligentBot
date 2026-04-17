"""Order Comparator - Compares orders between API and Google Sheet.

Handles:
- Comparing orders by ID
- Finding orders where API status is 'pending' but Sheet status is 'completed'
"""

from libraries.logger import logger


class OrderComparator:
    """Compares orders between API (paymentToProcess) and Sheet (sheetPayments)."""

    @staticmethod
    def get_order_id(order: dict) -> str:
        """Extract order ID from order dictionary.

        Args:
            order: Order dictionary

        Returns:
            str: Order ID or empty string
        """
        return str(order.get("id") or order.get("ID") or "").strip()

    @staticmethod
    def get_payment_status(order: dict) -> str:
        """Get payment status from order (lowercase).

        Args:
            order: Order dictionary

        Returns:
            str: Payment status (lowercase)
        """
        for key in ["payment_status", "paymentStatus", "Payment Status"]:
            if key in order:
                return str(order[key]).lower().strip()
        return ""

    @staticmethod
    def get_payment_amount(order: dict) -> str:
        """Get payment amount from order.

        Args:
            order: Order dictionary

        Returns:
            str: Payment amount as string
        """
        for key in ["order_total", "Order Total", "orderTotal", "payment_amount", "Payment Amount"]:
            if order.get(key):
                return str(order[key])
        return "0"

    def build_sheet_map(self, sheet_payments: list[dict]) -> dict[str, dict]:
        """Build a lookup map from sheet payments by ID.

        Args:
            sheet_payments: Orders from Google Sheet

        Returns:
            dict: Map of order_id -> order
        """
        orders_map: dict[str, dict] = {}
        for order in sheet_payments:
            order_id = self.get_order_id(order)
            if order_id:
                orders_map[order_id] = order
        return orders_map

    def filter_matching_orders(
        self,
        payment_to_process: list[dict],
        sheet_payments: list[dict],
    ) -> list[dict]:
        """Filter orders that exist in both API (pending) and Sheet.

        Args:
            payment_to_process: Orders from API (with pending status)
            sheet_payments: Orders from Google Sheet

        Returns:
            list[dict]: Orders that exist in both lists (filtered_payment_data)
        """
        logger.info("=" * 60)
        logger.info("Filtering orders that exist in both API and Sheet...")
        logger.info("=" * 60)

        # Build lookup map from sheet payments
        sheet_map = self.build_sheet_map(sheet_payments)

        logger.info(f"API orders (pending): {len(payment_to_process)}")
        logger.info(f"Sheet orders: {len(sheet_map)}")

        # Find orders that exist in both
        filtered_payment_data: list[dict] = []

        for api_order in payment_to_process:
            order_id = self.get_order_id(api_order)
            if not order_id:
                continue

            # Check if this order exists in sheet
            sheet_order = sheet_map.get(order_id)
            if sheet_order:
                filtered_payment_data.append(
                    {
                        "order_id": order_id,
                        "api_order": api_order,
                        "sheet_order": sheet_order,
                        "api_status": self.get_payment_status(api_order),
                        "sheet_status": self.get_payment_status(sheet_order),
                        "payment_amount": self.get_payment_amount(api_order),
                    }
                )

        logger.info(f"✓ Found {len(filtered_payment_data)} orders in both lists")

        return filtered_payment_data

    def find_orders_to_update(
        self,
        filtered_payment_data: list[dict],
    ) -> list[dict]:
        """Find orders that need status update.

        Condition: API payment_status = "pending" AND Sheet payment_status in ("completed", "paid")

        Args:
            filtered_payment_data: Orders that exist in both API and Sheet

        Returns:
            list[dict]: Orders that need to be updated
        """
        logger.info("=" * 60)
        logger.info("Finding orders to update...")
        logger.info("Condition: API status='pending' AND Sheet status in ('completed', 'paid')")
        logger.info("=" * 60)

        # Statuses that indicate payment is complete
        completed_statuses = {"completed", "paid", "success"}

        orders_to_update: list[dict] = []

        for order_data in filtered_payment_data:
            order_id = order_data["order_id"]
            api_status = order_data["api_status"]
            sheet_status = order_data["sheet_status"]

            logger.info(f"Order {order_id}:")
            logger.info(f"  API status: '{api_status}'")
            logger.info(f"  Sheet status: '{sheet_status}'")

            # Check condition: API pending + Sheet completed/paid → needs update
            if api_status == "pending" and sheet_status in completed_statuses:
                logger.info("  → NEEDS UPDATE to 'completed'")
                orders_to_update.append(order_data)
            else:
                logger.info("  → No update needed")

        logger.info("=" * 60)
        logger.info(f"Total orders needing update: {len(orders_to_update)}")
        logger.info("=" * 60)

        return orders_to_update

    def find_new_orders(
        self,
        payment_to_process: list[dict],
        sheet_payments: list[dict],
    ) -> list[dict]:
        """Find new orders - pending from API but NOT in sheet.

        These are new orders that need to be added to the sheet.

        Args:
            payment_to_process: Orders from API (with pending status)
            sheet_payments: Orders from Google Sheet

        Returns:
            list[dict]: New orders (API orders not in sheet)
        """
        logger.info("=" * 60)
        logger.info("Finding NEW orders (in API but NOT in sheet)...")
        logger.info("=" * 60)

        # Build lookup map from sheet payments
        sheet_map = self.build_sheet_map(sheet_payments)

        # Find orders in API that are NOT in sheet
        new_orders: list[dict] = []

        for api_order in payment_to_process:
            order_id = self.get_order_id(api_order)
            if not order_id:
                continue

            # Check if this order does NOT exist in sheet
            if order_id not in sheet_map:
                new_orders.append(api_order)
                logger.info(f"  📌 NEW order: {order_id}")

        logger.info("=" * 60)
        logger.info(f"✓ Found {len(new_orders)} new orders to add")
        logger.info("=" * 60)

        return new_orders

    def find_orders_to_sync_from_api(
        self,
        api_completed_orders: list[dict],
        sheet_payments: list[dict],
    ) -> list[dict]:
        """Find orders that are COMPLETED in API but NOT completed in sheet.

        NEW SCENARIO: If API already has status='completed', just update the sheet.

        Args:
            api_completed_orders: Orders from API with completed status
            sheet_payments: Orders from Google Sheet

        Returns:
            list[dict]: Orders where API=completed but Sheet!=completed
        """
        logger.info("=" * 60)
        logger.info("Finding orders to sync from API (API=completed, Sheet!=completed)...")
        logger.info("=" * 60)

        # Build lookup map from sheet payments
        sheet_map = self.build_sheet_map(sheet_payments)

        # Statuses that indicate completion
        completed_statuses = {"completed", "success"}

        orders_to_sync: list[dict] = []

        for api_order in api_completed_orders:
            order_id = self.get_order_id(api_order)
            if not order_id:
                continue

            # Check if this order exists in sheet
            sheet_order = sheet_map.get(order_id)
            if sheet_order:
                sheet_status = self.get_payment_status(sheet_order)

                # If sheet status is NOT completed, we need to sync
                if sheet_status not in completed_statuses:
                    logger.info(f"Order {order_id}:")
                    logger.info("  API status: 'completed'")
                    logger.info(f"  Sheet status: '{sheet_status}'")
                    logger.info("  → SYNC NEEDED: Update sheet to 'completed'")

                    orders_to_sync.append(
                        {
                            "order_id": order_id,
                            "api_order": api_order,
                            "sheet_order": sheet_order,
                            "api_status": "completed",
                            "sheet_status": sheet_status,
                        }
                    )

        logger.info("=" * 60)
        logger.info(f"✓ Found {len(orders_to_sync)} orders to sync from API to sheet")
        logger.info("=" * 60)

        return orders_to_sync
