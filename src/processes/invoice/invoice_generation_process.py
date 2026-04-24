"""Invoice Generation Process - public workflow entry point."""

from libraries.logger import logger
from processes.invoice.invoice_manager import InvoiceManager


class InvoiceGenerationProcess:
    """Public process wrapper for invoice generation."""

    def __init__(self) -> None:
        logger.info("=" * 60)
        logger.info("Initializing Invoice Generation Process")
        logger.info("=" * 60)
        self._manager = InvoiceManager()

    @property
    def generated_invoices(self) -> list[dict]:
        return self._manager.generated_invoices

    @property
    def skipped_orders(self) -> list[str]:
        return self._manager.skipped_orders

    @property
    def failed_orders(self) -> list[dict]:
        return self._manager.failed_orders

    def start(self) -> None:
        logger.info("=" * 60)
        logger.info("Starting Invoice Generation Process")
        logger.info("=" * 60)
        self._manager.start()
        logger.info(f"Invoices generated: {len(self.generated_invoices)}")
        logger.info(f"Orders skipped (already processed): {len(self.skipped_orders)}")

    def finish(self) -> None:
        logger.info("Invoice Generation Process finalized")
