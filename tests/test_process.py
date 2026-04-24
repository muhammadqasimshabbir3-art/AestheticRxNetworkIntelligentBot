"""Tests for main Process module."""

from unittest.mock import MagicMock, patch

import pytest


class TestProcess:
    """Tests for Process class."""

    @pytest.fixture
    def mock_order_management_process(self):
        """Create a mock OrderManagementProcess."""
        mock = MagicMock()
        mock.orders = []
        mock.spreadsheet_id = "test-spreadsheet-id"
        mock.spreadsheet_url = "https://docs.google.com/spreadsheets/d/test"
        mock.updated_order_ids = []
        return mock

    @pytest.fixture
    def mock_update_payment_process(self):
        """Create a mock UpdatePaymentProcess."""
        mock = MagicMock()
        mock.updated_count = 0
        mock.failed_ids = []
        mock.not_found_ids = []
        return mock

    @pytest.fixture
    def mock_report_generator(self):
        """Create a mock ReportGenerator."""
        mock = MagicMock()
        mock.generate_report.return_value = "/path/to/report.html"
        return mock

    @pytest.mark.unit
    def test_init_creates_process(self, mock_order_management_process, mock_update_payment_process):
        """Test Process initializes correctly."""
        with (
            patch("workflow.process.OrderManagementProcess"),
            patch("workflow.process.UpdatePaymentProcess"),
            patch("workflow.process.ReportGenerator"),
        ):
            from workflow.process import Process

            process = Process()

            assert process is not None

    @pytest.mark.unit
    def test_orders_property_empty_when_no_process(self):
        """Test orders property returns empty list when no order process."""
        with (
            patch("workflow.process.OrderManagementProcess"),
            patch("workflow.process.UpdatePaymentProcess"),
            patch("workflow.process.ReportGenerator"),
        ):
            from workflow.process import Process

            process = Process()
            process._order_process = None

            assert process.orders == []

    @pytest.mark.unit
    def test_spreadsheet_id_property_none_when_no_process(self):
        """Test spreadsheet_id property returns None when no order process."""
        with (
            patch("workflow.process.OrderManagementProcess"),
            patch("workflow.process.UpdatePaymentProcess"),
            patch("workflow.process.ReportGenerator"),
        ):
            from workflow.process import Process

            process = Process()
            process._order_process = None

            assert process.spreadsheet_id is None

    @pytest.mark.unit
    def test_update_payment_count_zero_when_no_process(self):
        """Test update_payment_count returns 0 when no payment process."""
        with (
            patch("workflow.process.OrderManagementProcess"),
            patch("workflow.process.UpdatePaymentProcess"),
            patch("workflow.process.ReportGenerator"),
        ):
            from workflow.process import Process

            process = Process()
            process._update_payment_process = None

            assert process.update_payment_count == 0


class TestProcessStart:
    """Tests for Process.start() method."""

    @pytest.mark.unit
    def test_process_initializes_successfully(self):
        """Test Process initializes without errors."""
        with (
            patch("workflow.process.OrderManagementProcess"),
            patch("workflow.process.UpdatePaymentProcess"),
            patch("workflow.process.ReportGenerator"),
        ):
            from workflow.process import Process

            process = Process()

            assert process is not None
            assert process._order_process is None  # Not started yet

    @pytest.mark.unit
    def test_start_skips_order_management_when_disabled(self, monkeypatch):
        """Test start() skips order management when disabled."""
        monkeypatch.setenv("RUN_UPDATE_PAYMENT_PROCESS", "False")
        monkeypatch.setenv("RUN_ORDER_MANAGE_SYSTEM", "False")
        monkeypatch.setenv("RUN_USER_MANAGEMENT_PROCESS", "False")
        monkeypatch.setenv("RUN_ADVERTISEMENT_MANAGEMENT_PROCESS", "False")
        monkeypatch.setenv("RUN_SIGNUP_ID_MANAGEMENT_PROCESS", "False")
        monkeypatch.setenv("RUN_DATA_ANALYSIS_PROCESS", "False")
        monkeypatch.setenv("RUN_BUSINESS_REPORT_PROCESS", "False")

        mock_omp = MagicMock()
        mock_report = MagicMock()
        mock_report.generate_report.return_value = "/tmp/test_report.html"

        with (
            patch("workflow.process.OrderManagementProcess", return_value=mock_omp),
            patch("workflow.process.UpdatePaymentProcess"),
            patch("workflow.process.UserManagementProcess"),
            patch("workflow.process.AdvertisementManagementProcess"),
            patch("workflow.process.SignupIDManagementProcess"),
            patch("workflow.process.DataAnalysisProcess"),
            patch("workflow.process.BusinessReportProcess"),
            patch("workflow.process.ReportGenerator", return_value=mock_report),
        ):
            from importlib import reload

            import libraries.workitems

            reload(libraries.workitems)

            import workflow.process

            reload(workflow.process)
            from workflow.process import Process

            process = Process()
            process.start()

            # Order management should not be called
            mock_omp.start.assert_not_called()


class TestProcessFinish:
    """Tests for Process.finish() method."""

    @pytest.mark.unit
    def test_finish_logs_results(self):
        """Test finish() logs results properly."""
        mock_omp = MagicMock()
        mock_omp.orders = [{"id": "1"}, {"id": "2"}]
        mock_omp.spreadsheet_id = "test-id"
        mock_omp.spreadsheet_url = "https://test.url"

        mock_upp = MagicMock()
        mock_upp.updated_count = 3

        with (
            patch("workflow.process.OrderManagementProcess"),
            patch("workflow.process.UpdatePaymentProcess"),
            patch("workflow.process.ReportGenerator"),
        ):
            from workflow.process import Process

            process = Process()
            process._order_process = mock_omp
            process._update_payment_process = mock_upp
            process._report_path = "/path/to/report.html"

            # Should not raise
            process.finish()


class TestProcessHelperMethods:
    """Tests for Process helper methods."""

    @pytest.mark.unit
    def test_get_orders_returns_orders(self):
        """Test get_orders() returns orders list."""
        mock_omp = MagicMock()
        mock_omp.orders = [{"id": "1"}, {"id": "2"}]

        with (
            patch("workflow.process.OrderManagementProcess"),
            patch("workflow.process.UpdatePaymentProcess"),
            patch("workflow.process.ReportGenerator"),
        ):
            from workflow.process import Process

            process = Process()
            process._order_process = mock_omp

            orders = process.get_orders()

            assert len(orders) == 2

    @pytest.mark.unit
    def test_get_spreadsheet_url_returns_url(self):
        """Test get_spreadsheet_url() returns URL."""
        mock_omp = MagicMock()
        mock_omp.spreadsheet_url = "https://docs.google.com/spreadsheets/d/test"

        with (
            patch("workflow.process.OrderManagementProcess"),
            patch("workflow.process.UpdatePaymentProcess"),
            patch("workflow.process.ReportGenerator"),
        ):
            from workflow.process import Process

            process = Process()
            process._order_process = mock_omp

            url = process.get_spreadsheet_url()

            assert url == "https://docs.google.com/spreadsheets/d/test"

    @pytest.mark.unit
    def test_get_report_path_returns_path(self):
        """Test get_report_path() returns report path."""
        with (
            patch("workflow.process.OrderManagementProcess"),
            patch("workflow.process.UpdatePaymentProcess"),
            patch("workflow.process.ReportGenerator"),
        ):
            from workflow.process import Process

            process = Process()
            process._report_path = "/path/to/report.html"

            path = process.get_report_path()

            assert path == "/path/to/report.html"
