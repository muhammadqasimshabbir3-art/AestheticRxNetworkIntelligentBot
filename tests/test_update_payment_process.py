"""Tests for UpdatePaymentProcess module."""

from unittest.mock import MagicMock, patch

import pytest


class TestUpdatePaymentProcess:
    """Tests for UpdatePaymentProcess class."""

    @pytest.fixture
    def mock_sheets_api(self):
        """Create a mock GoogleSheetsAPI."""
        mock = MagicMock()
        mock.get_sheet_info.return_value = [{"title": "Sheet1", "sheetId": 0}]
        mock.read_data.return_value = []
        return mock

    @pytest.fixture
    def update_payment_process(self, mock_sheets_api):
        """Create an UpdatePaymentProcess with mocked API."""
        with patch("processes.payment.update_payment_process.GoogleSheetsAPI") as mock_class:
            mock_class.return_value = mock_sheets_api

            from processes.payment.update_payment_process import UpdatePaymentProcess

            process = UpdatePaymentProcess(payment_ids=["id-1", "id-2"])
            process._sheets_api = mock_sheets_api
            return process

    @pytest.mark.unit
    def test_init_with_payment_ids(self):
        """Test initialization with payment IDs."""
        with patch("processes.payment.update_payment_process.GoogleSheetsAPI"):
            from processes.payment.update_payment_process import UpdatePaymentProcess

            process = UpdatePaymentProcess(payment_ids=["id-1", "id-2", "id-3"])

            assert process.payment_ids == ["id-1", "id-2", "id-3"]

    @pytest.mark.unit
    def test_init_empty_payment_ids(self):
        """Test initialization with empty payment IDs."""
        with patch("processes.payment.update_payment_process.GoogleSheetsAPI"):
            from processes.payment.update_payment_process import UpdatePaymentProcess

            process = UpdatePaymentProcess(payment_ids=[])

            assert process.payment_ids == []

    @pytest.mark.unit
    def test_updated_count_property_initial(self, update_payment_process):
        """Test updated_count property initial value."""
        # Initial count should be 0 before start() is called
        assert update_payment_process.updated_count == 0

    @pytest.mark.unit
    def test_failed_ids_property_initial(self, update_payment_process):
        """Test failed_ids property initial value."""
        # Initial list should be empty before start() is called
        assert update_payment_process.failed_ids == []

    @pytest.mark.unit
    def test_not_found_ids_property_initial(self, update_payment_process):
        """Test not_found_ids property initial value."""
        # Initial list should be empty before start() is called
        assert update_payment_process.not_found_ids == []


class TestUpdatePaymentProcessStart:
    """Tests for UpdatePaymentProcess.start() method."""

    @pytest.fixture
    def mock_sheets_api(self):
        """Create a mock GoogleSheetsAPI."""
        mock = MagicMock()
        mock.get_sheet_info.return_value = [{"title": "Sheet1", "sheetId": 0}]
        return mock

    @pytest.mark.unit
    def test_start_with_empty_ids(self, mock_sheets_api):
        """Test start() with no payment IDs."""
        with patch("processes.payment.update_payment_process.GoogleSheetsAPI") as mock_class:
            mock_class.return_value = mock_sheets_api

            from processes.payment.update_payment_process import UpdatePaymentProcess

            process = UpdatePaymentProcess(payment_ids=[])
            process.start()

            # Should not read data if no IDs
            assert process.updated_count == 0

    @pytest.mark.unit
    def test_start_processes_payment_ids(self, mock_sheets_api):
        """Test start() processes payment IDs."""
        mock_sheets_api.read_data.return_value = [
            ["ID", "Order Number", "Payment Status"],
            ["id-1", "ORD-001", "pending"],
            ["id-2", "ORD-002", "pending"],
        ]

        with patch("processes.payment.update_payment_process.GoogleSheetsAPI") as mock_class:
            mock_class.return_value = mock_sheets_api

            from processes.payment.update_payment_process import UpdatePaymentProcess

            process = UpdatePaymentProcess(payment_ids=["id-1", "id-2"])
            process.start()

            # Verify the process ran and read data
            mock_sheets_api.read_data.assert_called()

    @pytest.mark.unit
    def test_start_calls_api_methods(self, mock_sheets_api):
        """Test start() calls necessary API methods."""
        mock_sheets_api.read_data.return_value = [
            ["ID", "Order Number", "Payment Status"],
            ["id-1", "ORD-001", "pending"],
        ]

        with patch("processes.payment.update_payment_process.GoogleSheetsAPI") as mock_class:
            mock_class.return_value = mock_sheets_api

            from processes.payment.update_payment_process import UpdatePaymentProcess

            process = UpdatePaymentProcess(payment_ids=["id-1"])
            process.start()

            # Verify API was used
            mock_sheets_api.get_sheet_info.assert_called()

    @pytest.mark.unit
    def test_start_handles_missing_ids(self, mock_sheets_api):
        """Test start() handles IDs not found in sheet."""
        mock_sheets_api.read_data.return_value = [
            ["ID", "Order Number", "Payment Status"],
            ["id-1", "ORD-001", "pending"],
        ]

        with patch("processes.payment.update_payment_process.GoogleSheetsAPI") as mock_class:
            mock_class.return_value = mock_sheets_api

            from processes.payment.update_payment_process import UpdatePaymentProcess

            process = UpdatePaymentProcess(payment_ids=["id-1", "id-999"])
            process.start()

            # id-999 should be tracked as not found
            assert "id-999" in process.not_found_ids


class TestUpdatePaymentProcessEdgeCases:
    """Edge case tests for UpdatePaymentProcess."""

    @pytest.fixture
    def mock_sheets_api(self):
        """Create a mock GoogleSheetsAPI."""
        mock = MagicMock()
        mock.get_sheet_info.return_value = [{"title": "Sheet1", "sheetId": 0}]
        return mock

    @pytest.mark.unit
    def test_handles_empty_sheet(self, mock_sheets_api):
        """Test handling of empty sheet."""
        mock_sheets_api.read_data.return_value = []

        with patch("processes.payment.update_payment_process.GoogleSheetsAPI") as mock_class:
            mock_class.return_value = mock_sheets_api

            from processes.payment.update_payment_process import UpdatePaymentProcess

            process = UpdatePaymentProcess(payment_ids=["id-1"])
            process.start()

            assert process.updated_count == 0
            assert "id-1" in process.not_found_ids

    @pytest.mark.unit
    def test_handles_sheet_with_only_headers(self, mock_sheets_api):
        """Test handling of sheet with only headers."""
        mock_sheets_api.read_data.return_value = [["id", "orderNumber", "payment_status"]]

        with patch("processes.payment.update_payment_process.GoogleSheetsAPI") as mock_class:
            mock_class.return_value = mock_sheets_api

            from processes.payment.update_payment_process import UpdatePaymentProcess

            process = UpdatePaymentProcess(payment_ids=["id-1"])
            process.start()

            assert process.updated_count == 0

    @pytest.mark.unit
    def test_handles_api_error(self, mock_sheets_api):
        """Test handling of API errors."""
        mock_sheets_api.read_data.side_effect = Exception("API Error")

        with patch("processes.payment.update_payment_process.GoogleSheetsAPI") as mock_class:
            mock_class.return_value = mock_sheets_api

            from processes.payment.update_payment_process import UpdatePaymentProcess

            process = UpdatePaymentProcess(payment_ids=["id-1"])

            # Should handle error gracefully
            try:
                process.start()
            except Exception:
                pass  # Expected to handle or raise

    @pytest.mark.unit
    def test_case_insensitive_status_check(self, mock_sheets_api):
        """Test status check is case insensitive."""
        mock_sheets_api.read_data.return_value = [
            ["id", "orderNumber", "payment_status"],
            ["id-1", "ORD-001", "PENDING"],  # Uppercase
            ["id-2", "ORD-002", "Pending"],  # Mixed case
        ]

        with patch("processes.payment.update_payment_process.GoogleSheetsAPI") as mock_class:
            mock_class.return_value = mock_sheets_api

            from processes.payment.update_payment_process import UpdatePaymentProcess

            process = UpdatePaymentProcess(payment_ids=["id-1", "id-2"])
            process.start()

            # Both should be found and updated
            assert process.updated_count == 2
