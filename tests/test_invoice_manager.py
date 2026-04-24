"""Tests for invoice generation manager."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from config import CONFIG


@pytest.fixture
def invoice_manager(tmp_path, monkeypatch):
    """Create an InvoiceManager with mocked external dependencies."""
    cache_dir = tmp_path / "cache"
    output_dir = tmp_path / "invoices"
    processed_log = tmp_path / "processed_invoices.json"

    monkeypatch.setattr(CONFIG, "DRIVE_CACHE_DIR", cache_dir)
    monkeypatch.setattr(CONFIG, "INVOICE_OUTPUT_DIR", output_dir)
    monkeypatch.setattr(CONFIG, "INVOICE_PROCESSED_LOG", processed_log)

    with (
        patch("processes.invoice.invoice_manager.GoogleDriveAPI") as drive_cls,
        patch("processes.invoice.invoice_manager.APIHandler") as api_cls,
    ):
        drive = MagicMock()
        api = MagicMock()

        drive.get_file.return_value = {
            "id": "file-1",
            "name": "pending.xlsx",
            "modifiedTime": "2026-01-01T00:00:00.000Z",
            "size": "10",
        }

        def _download(_, local_path):
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            Path(local_path).write_bytes(b"xlsx")

        drive.download_file.side_effect = _download
        api.fetch_unpaid_orders.return_value = []

        drive_cls.return_value = drive
        api_cls.return_value = api

        from processes.invoice.invoice_manager import InvoiceManager

        manager = InvoiceManager()
        return manager, drive


@pytest.mark.unit
def test_download_drive_file_uses_cache(invoice_manager):
    manager, drive = invoice_manager

    first = manager.download_drive_file("file-1")
    second = manager.download_drive_file("file-1")

    assert first.exists()
    assert second == first
    assert drive.download_file.call_count == 1


@pytest.mark.unit
def test_process_order_skips_already_processed(invoice_manager):
    manager, _ = invoice_manager

    manager._save_processed_orders({"order-1": {"order_id": "order-1"}})
    result = manager.process_order({"id": "order-1", "order_number": "INV-001"})

    assert result is None
    assert "order-1" in manager.skipped_orders


@pytest.mark.unit
def test_process_order_generates_invoice(invoice_manager):
    manager, _ = invoice_manager
    manager.pending_orders_df = pd.DataFrame(
        [
            {
                "id": "order-2",
                "doctor_name": "Dr Test",
                "doctor_email": "dr@example.com",
                "product_name": "PDO",
                "product_id": "P-100",
                "qty": 2,
                "product_price": 2500,
            }
        ]
    )

    with patch("processes.invoice.invoice_manager.generate_invoice_files") as gen:
        gen.return_value = {
            "pdf": str(CONFIG.INVOICE_OUTPUT_DIR / "INV-002.pdf"),
            "excel": str(CONFIG.INVOICE_OUTPUT_DIR / "INV-002.xlsx"),
        }

        result = manager.process_order(
            {
                "id": "order-2",
                "order_number": "INV-002",
                "doctor_name": "Dr Test",
                "product_name": "PDO",
                "qty": 2,
                "product_price": 2500,
            }
        )

    assert result is not None
    assert result["order_id"] == "order-2"
    assert len(manager.generated_invoices) == 1
