"""Order Management Module.

This module handles the complete order management workflow:
- Reading orders from Google Sheets
- Fetching orders from AestheticRxNetwork API
- Comparing orders and updating statuses
- Writing orders back to Google Sheets

Main Entry Point:
    from processes.order import OrderManagementProcess

    process = OrderManagementProcess()
    process.start()

For advanced usage:
    from processes.order import OrderManager, SheetHandler, APIHandler, OrderComparator
"""

from processes.order.api_handler import APIHandler
from processes.order.comparator import OrderComparator
from processes.order.order_management_process import OrderManagementProcess
from processes.order.order_manager import OrderManager
from processes.order.sheet_handler import SheetHandler

__all__ = [
    "APIHandler",
    "OrderComparator",
    "OrderManagementProcess",  # Main entry point
    "OrderManager",
    "SheetHandler",
]
