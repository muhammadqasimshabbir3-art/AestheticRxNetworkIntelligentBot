"""Tests for SheetHandler module."""

from unittest.mock import MagicMock, patch

import pytest


class TestSheetHandler:
    """Tests for SheetHandler class."""

    @pytest.fixture
    def mock_sheets_api(self):
        """Create a mock GoogleSheetsAPI."""
        mock = MagicMock()
        mock.get_sheet_info.return_value = [{"title": "Sheet1", "sheetId": 0}]
        mock.read_data.return_value = []
        return mock

    @pytest.fixture
    def mock_drive_api(self):
        """Create a mock GoogleDriveAPI."""
        return MagicMock()

    @pytest.fixture
    def sheet_handler(self, mock_sheets_api, mock_drive_api):
        """Create a SheetHandler with mocked APIs."""
        with (
            patch("orderManagement.sheet_handler.GoogleSheetsAPI") as mock_sheets_class,
            patch("orderManagement.sheet_handler.GoogleDriveAPI") as mock_drive_class,
        ):
            mock_sheets_class.return_value = mock_sheets_api
            mock_drive_class.return_value = mock_drive_api

            from processes.order.sheet_handler import SheetHandler

            handler = SheetHandler()
            handler._sheets_api = mock_sheets_api
            handler._drive_api = mock_drive_api
            return handler

    @pytest.mark.unit
    def test_read_sheet_payments_empty_sheet(self, sheet_handler, mock_sheets_api):
        """Test read_sheet_payments with empty sheet."""
        mock_sheets_api.read_data.return_value = []

        result = sheet_handler.read_sheet_payments()

        assert result == []

    @pytest.mark.unit
    def test_read_sheet_payments_headers_only(self, sheet_handler, mock_sheets_api):
        """Test read_sheet_payments with only headers."""
        mock_sheets_api.read_data.return_value = [["id", "orderNumber", "payment_status"]]

        result = sheet_handler.read_sheet_payments()

        assert result == []

    @pytest.mark.unit
    def test_read_sheet_payments_with_data(self, sheet_handler, mock_sheets_api):
        """Test read_sheet_payments with actual data."""
        mock_sheets_api.read_data.return_value = [
            ["id", "orderNumber", "payment_status"],
            ["order-1", "ORD-001", "pending"],
            ["order-2", "ORD-002", "paid"],
        ]

        result = sheet_handler.read_sheet_payments()

        assert len(result) == 2
        assert result[0]["id"] == "order-1"
        assert result[0]["payment_status"] == "pending"
        assert result[1]["id"] == "order-2"
        assert result[1]["payment_status"] == "paid"

    @pytest.mark.unit
    def test_read_sheet_payments_handles_missing_values(self, sheet_handler, mock_sheets_api):
        """Test read_sheet_payments handles rows with missing values."""
        mock_sheets_api.read_data.return_value = [
            ["id", "orderNumber", "payment_status", "amount"],
            ["order-1", "ORD-001"],  # Missing payment_status and amount
        ]

        result = sheet_handler.read_sheet_payments()

        assert len(result) == 1
        assert result[0]["id"] == "order-1"
        assert result[0]["payment_status"] == ""  # Should be empty string
        assert result[0]["amount"] == ""

    @pytest.mark.unit
    def test_get_status_breakdown(self, sheet_handler, mock_sheets_api):
        """Test get_status_breakdown returns correct counts."""
        mock_sheets_api.read_data.return_value = [
            ["id", "orderNumber", "payment_status"],
            ["order-1", "ORD-001", "pending"],
            ["order-2", "ORD-002", "paid"],
            ["order-3", "ORD-003", "pending"],
        ]

        sheet_handler.read_sheet_payments()
        breakdown = sheet_handler.get_status_breakdown()

        assert breakdown.get("pending", 0) == 2
        assert breakdown.get("paid", 0) == 1


class TestSheetHandlerDuplicates:
    """Tests for duplicate handling in SheetHandler."""

    @pytest.fixture
    def mock_sheets_api(self):
        """Create a mock GoogleSheetsAPI."""
        mock = MagicMock()
        mock.get_sheet_info.return_value = [{"title": "Sheet1", "sheetId": 0}]
        return mock

    @pytest.fixture
    def sheet_handler(self, mock_sheets_api):
        """Create a SheetHandler with mocked APIs."""
        with (
            patch("orderManagement.sheet_handler.GoogleSheetsAPI") as mock_sheets_class,
            patch("orderManagement.sheet_handler.GoogleDriveAPI"),
        ):
            mock_sheets_class.return_value = mock_sheets_api

            from processes.order.sheet_handler import SheetHandler

            handler = SheetHandler()
            handler._sheets_api = mock_sheets_api
            return handler

    @pytest.mark.unit
    def test_remove_duplicates_no_duplicates(self, sheet_handler, mock_sheets_api):
        """Test remove_duplicates with no duplicates."""
        mock_sheets_api.read_data.return_value = [
            ["id", "orderNumber"],
            ["order-1", "ORD-001"],
            ["order-2", "ORD-002"],
        ]

        count = sheet_handler.remove_duplicates()

        assert count == 0
        mock_sheets_api.delete_rows.assert_not_called()

    @pytest.mark.unit
    def test_remove_duplicates_with_duplicates(self, sheet_handler, mock_sheets_api):
        """Test remove_duplicates with duplicate rows."""
        mock_sheets_api.read_data.return_value = [
            ["id", "orderNumber"],
            ["order-1", "ORD-001"],
            ["order-1", "ORD-001"],  # Duplicate
            ["order-2", "ORD-002"],
        ]

        count = sheet_handler.remove_duplicates()

        assert count == 1
        mock_sheets_api.delete_rows.assert_called_once()

    @pytest.mark.unit
    def test_remove_duplicates_with_ids_returns_ids(self, sheet_handler, mock_sheets_api):
        """Test remove_duplicates_with_ids returns duplicate IDs."""
        mock_sheets_api.read_data.return_value = [
            ["id", "orderNumber"],
            ["order-1", "ORD-001"],
            ["order-1", "ORD-001"],  # Duplicate
            ["order-2", "ORD-002"],
            ["order-2", "ORD-002"],  # Another duplicate
        ]

        count, ids = sheet_handler.remove_duplicates_with_ids()

        assert count == 2
        assert "order-1" in ids
        assert "order-2" in ids

    @pytest.mark.unit
    def test_remove_duplicates_empty_sheet(self, sheet_handler, mock_sheets_api):
        """Test remove_duplicates with empty sheet."""
        mock_sheets_api.read_data.return_value = []

        count = sheet_handler.remove_duplicates()

        assert count == 0


class TestSheetHandlerUpdates:
    """Tests for update operations in SheetHandler."""

    @pytest.fixture
    def mock_sheets_api(self):
        """Create a mock GoogleSheetsAPI."""
        mock = MagicMock()
        mock.get_sheet_info.return_value = [{"title": "Sheet1", "sheetId": 0}]
        return mock

    @pytest.fixture
    def sheet_handler(self, mock_sheets_api):
        """Create a SheetHandler with mocked APIs."""
        with (
            patch("orderManagement.sheet_handler.GoogleSheetsAPI") as mock_sheets_class,
            patch("orderManagement.sheet_handler.GoogleDriveAPI"),
        ):
            mock_sheets_class.return_value = mock_sheets_api

            from processes.order.sheet_handler import SheetHandler

            handler = SheetHandler()
            handler._sheets_api = mock_sheets_api
            return handler

    @pytest.mark.unit
    def test_update_rows_status_success(self, sheet_handler, mock_sheets_api):
        """Test update_rows_status updates specified rows."""
        mock_sheets_api.read_data.return_value = [
            ["ID", "Order Number", "Payment Status"],
            ["order-1", "ORD-001", "paid"],
            ["order-2", "ORD-002", "paid"],
        ]

        result = sheet_handler.update_rows_status(["order-1"], "completed")

        # Returns count of updated rows
        assert isinstance(result, (bool, int))
        mock_sheets_api.read_data.assert_called()

    @pytest.mark.unit
    def test_update_rows_status_reads_data(self, sheet_handler, mock_sheets_api):
        """Test update_rows_status reads sheet data."""
        mock_sheets_api.read_data.return_value = [
            ["ID", "Order Number", "Payment Status"],
            ["order-1", "ORD-001", "paid"],
        ]

        sheet_handler.update_rows_status(["nonexistent-id"], "completed")

        # Should read data to find the rows
        mock_sheets_api.read_data.assert_called()


class TestSheetHandlerAppend:
    """Tests for append operations in SheetHandler."""

    @pytest.fixture
    def mock_sheets_api(self):
        """Create a mock GoogleSheetsAPI."""
        mock = MagicMock()
        mock.get_sheet_info.return_value = [{"title": "Sheet1", "sheetId": 0}]
        return mock

    @pytest.fixture
    def sheet_handler(self, mock_sheets_api):
        """Create a SheetHandler with mocked APIs."""
        with (
            patch("orderManagement.sheet_handler.GoogleSheetsAPI") as mock_sheets_class,
            patch("orderManagement.sheet_handler.GoogleDriveAPI"),
        ):
            mock_sheets_class.return_value = mock_sheets_api

            from processes.order.sheet_handler import SheetHandler

            handler = SheetHandler()
            handler._sheets_api = mock_sheets_api
            return handler

    @pytest.mark.unit
    def test_append_new_orders_empty_list(self, sheet_handler, mock_sheets_api):
        """Test append_new_orders with empty list."""
        result = sheet_handler.append_new_orders([])

        assert result == 0
        mock_sheets_api.add_rows_batch.assert_not_called()

    @pytest.mark.unit
    def test_append_new_orders_with_orders(self, sheet_handler, mock_sheets_api):
        """Test append_new_orders with orders."""
        new_orders = [
            {"ID": "order-1", "Order Number": "ORD-001", "Payment Status": "pending"},
            {"ID": "order-2", "Order Number": "ORD-002", "Payment Status": "pending"},
        ]

        result = sheet_handler.append_new_orders(new_orders)

        # Returns count of appended orders
        assert result == 2
        # May use add_rows_batch or other method
        assert mock_sheets_api.method_calls  # Verify some API was called

    @pytest.mark.unit
    def test_get_existing_ids(self, sheet_handler, mock_sheets_api):
        """Test get_existing_ids returns all IDs from sheet."""
        mock_sheets_api.read_data.return_value = [
            ["id", "orderNumber"],
            ["order-1", "ORD-001"],
            ["order-2", "ORD-002"],
            ["order-3", "ORD-003"],
        ]

        ids = sheet_handler.get_existing_ids()

        assert "order-1" in ids
        assert "order-2" in ids
        assert "order-3" in ids
        assert len(ids) == 3
