"""Order Management Process - Entry point for order management workflow.

This class provides a single entry point (start method) for the
order management workflow. It wraps the OrderManager and handles
all the internal orchestration.

Usage:
    from processes.order import OrderManagementProcess

    process = OrderManagementProcess()
    process.start()
"""


from libraries.logger import logger
from processes.order.order_manager import OrderManager


class OrderManagementProcess:
    """Order Management Process - Single entry point for order workflow.

    This class encapsulates the entire order management workflow
    and exposes only the start() method for external use.

    The workflow includes:
    1. Read orders from Google Sheet
    2. Fetch orders from Q Website API
    3. Compare orders by ID and update status
    4. Write all orders to spreadsheet
    """

    def __init__(self) -> None:
        """Initialize the Order Management Process."""
        logger.info("=" * 60)
        logger.info("Initializing Order Management Process")
        logger.info("=" * 60)

        self._order_manager: OrderManager | None = None
        self._is_completed: bool = False

    def start(self) -> None:
        """Start the order management workflow.

        This is the main entry point. It initializes the OrderManager
        and runs the complete workflow.
        """
        logger.info("=" * 60)
        logger.info("Starting Order Management Process")
        logger.info("=" * 60)

        try:
            # Initialize OrderManager (this handles API auth, etc.)
            self._order_manager = OrderManager()

            # Run the workflow
            self._order_manager.start()

            self._is_completed = True

            # Log results
            self._log_results()

        except Exception as e:
            logger.error(f"Order Management Process failed: {e}")
            raise

        finally:
            if self._order_manager:
                self._order_manager.finish()

    def _log_results(self) -> None:
        """Log the results of the workflow."""
        if not self._order_manager:
            return

        logger.info("=" * 60)
        logger.info("Order Management Process Results:")
        logger.info(f"  Total orders: {len(self._order_manager.orders)}")
        logger.info(f"  Updated orders: {len(self._order_manager.updated_order_ids)}")
        if self._order_manager.spreadsheet_id:
            logger.info(f"  Spreadsheet: {self._order_manager.get_spreadsheet_url()}")
        logger.info("=" * 60)

    @property
    def is_completed(self) -> bool:
        """Check if the process completed successfully."""
        return self._is_completed

    @property
    def orders(self) -> list[dict]:
        """Get orders (available after start() completes)."""
        if self._order_manager:
            return self._order_manager.orders
        return []

    @property
    def spreadsheet_id(self) -> str | None:
        """Get spreadsheet ID (available after start() completes)."""
        if self._order_manager:
            return self._order_manager.spreadsheet_id
        return None

    @property
    def spreadsheet_url(self) -> str | None:
        """Get spreadsheet URL (available after start() completes)."""
        if self._order_manager:
            return self._order_manager.get_spreadsheet_url()
        return None

    @property
    def updated_order_ids(self) -> list[str]:
        """Get IDs of updated orders (available after start() completes)."""
        if self._order_manager:
            return self._order_manager.updated_order_ids
        return []
