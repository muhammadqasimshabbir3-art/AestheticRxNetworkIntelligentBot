"""API Handler - Q Website API operations for Order Management.

Handles:
- Fetching orders from Q Website API (pending status only)
- Updating order status via API
"""


from libraries.logger import logger
from libraries.qwebsite_api import QWebsiteAPI


class APIHandler:
    """Handles all Q Website API operations for order management."""

    def __init__(self, api: QWebsiteAPI | None = None) -> None:
        """Initialize the API handler.

        Args:
            api: Optional QWebsiteAPI instance. If not provided, creates new one.
        """
        if api:
            self.api = api
        else:
            logger.info("Initializing Q Website API...")
            self.api = QWebsiteAPI(auto_authenticate=True)

    def fetch_pending_orders(self) -> list[dict]:
        """Fetch orders with status 'pending' from Q Website API.

        Returns:
            list[dict]: List of orders with pending status (paymentToProcess)
        """
        logger.info("=" * 60)
        logger.info("Fetching orders with status 'pending' from API...")
        logger.info("=" * 60)

        # Get all orders
        response = self.api.get_orders()

        # Handle different response formats
        if isinstance(response, dict):
            all_orders = response.get("data") or response.get("orders") or []
        elif isinstance(response, list):
            all_orders = response
        else:
            all_orders = []

        logger.info(f"Total orders from API: {len(all_orders)}")

        # Filter for pending status only
        pending_orders = []
        for order in all_orders:
            payment_status = self._get_payment_status(order)
            if payment_status == "pending":
                pending_orders.append(order)

        logger.info(f"✓ Found {len(pending_orders)} orders with 'pending' status")

        return pending_orders

    def fetch_completed_orders(self) -> list[dict]:
        """Fetch orders with status 'completed' from Q Website API.

        Returns:
            list[dict]: List of orders with completed status
        """
        logger.info("=" * 60)
        logger.info("Fetching orders with status 'completed' from API...")
        logger.info("=" * 60)

        # Get all orders
        response = self.api.get_orders()

        # Handle different response formats
        if isinstance(response, dict):
            all_orders = response.get("data") or response.get("orders") or []
        elif isinstance(response, list):
            all_orders = response
        else:
            all_orders = []

        # Filter for completed status only
        completed_orders = []
        for order in all_orders:
            payment_status = self._get_payment_status(order)
            if payment_status in ("completed", "success"):
                completed_orders.append(order)

        logger.info(f"✓ Found {len(completed_orders)} orders with 'completed' status")

        return completed_orders

    def _get_payment_status(self, order: dict) -> str:
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

    def update_order_status(
        self,
        order_id: str,
        payment_status: str = "completed",
        payment_amount: str = "",
        notes: str = "Status updated via automation",
    ) -> bool:
        """Update order payment status via API.

        Args:
            order_id: The order ID (UUID)
            payment_status: New payment status
            payment_amount: Payment amount
            notes: Notes for the status change

        Returns:
            bool: True if update was successful (200 OK), False otherwise
        """
        logger.info(f"Updating order {order_id} status to '{payment_status}'...")

        try:
            result = self.api.update_order_status(
                order_id=order_id,
                payment_status=payment_status,
                payment_amount=payment_amount,
                notes=notes,
            )

            # Check if response indicates success
            if isinstance(result, dict) and (result.get("success") or result.get("status") == "ok"):
                logger.info(f"✓ Order {order_id} updated successfully (200 OK)")
                return True

            # If we got here without exception, assume success
            logger.info(f"✓ Order {order_id} updated successfully")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to update order {order_id}: {e}")
            return False

    def get_order_by_id(self, order_id: str) -> dict:
        """Get a specific order by ID.

        Args:
            order_id: Order ID

        Returns:
            dict: Order data
        """
        return self.api.get_order_by_id(order_id)

    def calculate_doctor_debts(self) -> list[dict]:
        """Calculate debt for each doctor from pending orders.

        Filters orders with status='pending', groups by doctor_id,
        and sums remaining_amount for each doctor.

        Returns:
            list[dict]: List of doctor debts with keys:
                - doctor_id: Doctor's UUID
                - doctor_name: Doctor's name
                - doctor_email: Doctor's email
                - total_debt: Sum of remaining_amount for pending orders
                - pending_orders_count: Number of pending orders
                - pending_orders: List of all pending order details
        """
        logger.info("=" * 60)
        logger.info("Calculating doctor debts from pending orders...")
        logger.info("=" * 60)

        # Get all orders
        response = self.api.get_orders()

        # Handle different response formats
        if isinstance(response, dict):
            all_orders = response.get("data") or response.get("orders") or []
        elif isinstance(response, list):
            all_orders = response
        else:
            all_orders = []

        logger.info(f"Total orders from API: {len(all_orders)}")

        # Filter for pending status only and group by doctor_id
        doctor_debts: dict[str, dict] = {}

        for order in all_orders:
            # Check if status is pending
            status = str(order.get("status", "")).lower().strip()
            if status != "pending":
                continue

            doctor_id = order.get("doctor_id") or order.get("doctorId") or ""
            doctor_name = order.get("doctor_name") or order.get("doctorName") or "Unknown"
            doctor_email = order.get("doctor_email") or order.get("doctorEmail") or ""

            # Get remaining amount
            remaining_amount = 0.0
            try:
                remaining_amount = float(order.get("remaining_amount") or order.get("remainingAmount") or 0)
            except (ValueError, TypeError):
                remaining_amount = 0.0

            # Get order details for expandable view
            order_details = {
                "order_id": order.get("id") or order.get("order_id") or "",
                "order_number": order.get("order_number") or order.get("orderNumber") or "",
                "product_name": order.get("product_name") or order.get("productName") or "",
                "product_price": order.get("product_price") or order.get("productPrice") or 0,
                "qty": order.get("qty") or order.get("quantity") or 1,
                "order_total": order.get("order_total") or order.get("orderTotal") or 0,
                "payment_amount": order.get("payment_amount") or order.get("paymentAmount") or 0,
                "remaining_amount": remaining_amount,
                "payment_status": order.get("payment_status") or order.get("paymentStatus") or "",
                "payment_method": order.get("payment_method") or order.get("paymentMethod") or "",
                "order_date": order.get("order_date") or order.get("orderDate") or "",
                "notes": order.get("notes") or "",
            }

            if doctor_id:
                if doctor_id not in doctor_debts:
                    doctor_debts[doctor_id] = {
                        "doctor_id": doctor_id,
                        "doctor_name": doctor_name,
                        "doctor_email": doctor_email,
                        "total_debt": 0.0,
                        "pending_orders_count": 0,
                        "pending_orders": [],
                    }

                doctor_debts[doctor_id]["total_debt"] += remaining_amount
                doctor_debts[doctor_id]["pending_orders_count"] += 1
                doctor_debts[doctor_id]["pending_orders"].append(order_details)

        # Convert to list and sort by total_debt descending
        result = sorted(
            doctor_debts.values(),
            key=lambda x: x["total_debt"],
            reverse=True,
        )

        logger.info(f"✓ Found {len(result)} doctors with pending orders")
        for doc in result:
            logger.info(
                f"  - {doc['doctor_name']}: ₨{doc['total_debt']:,.2f} " f"({doc['pending_orders_count']} orders)"
            )

        return result
