"""Tests for OrderManager module."""

from unittest.mock import MagicMock, patch

import pytest


class TestOrderManager:
    """Tests for OrderManager class."""

    @pytest.fixture
    def mock_api_handler(self):
        """Create a mock APIHandler."""
        mock = MagicMock()
        mock.fetch_pending_orders.return_value = []
        mock.update_order_status.return_value = True
        return mock

    @pytest.fixture
    def mock_sheet_handler(self):
        """Create a mock SheetHandler."""
        mock = MagicMock()
        mock.read_sheet_payments.return_value = []
        mock.get_status_breakdown.return_value = {}
        mock.remove_duplicates_with_ids.return_value = (0, [])
        mock.update_rows_status.return_value = True
        mock.append_new_orders.return_value = 0
        return mock

    @pytest.fixture
    def mock_comparator(self):
        """Create a mock OrderComparator."""
        mock = MagicMock()
        mock.filter_matching_orders.return_value = []
        mock.find_orders_to_update.return_value = []
        mock.find_new_orders.return_value = []
        mock.get_order_id.side_effect = lambda x: x.get("id", "")
        mock.get_payment_status.side_effect = lambda x: x.get("payment_status", "")
        return mock

    @pytest.fixture
    def order_manager(self, mock_api_handler, mock_sheet_handler, mock_comparator):
        """Create an OrderManager with mocked dependencies."""
        with (
            patch("orderManagement.order_manager.APIHandler") as api_class,
            patch("orderManagement.order_manager.SheetHandler") as sheet_class,
            patch("orderManagement.order_manager.OrderComparator") as comp_class,
        ):
            api_class.return_value = mock_api_handler
            sheet_class.return_value = mock_sheet_handler
            comp_class.return_value = mock_comparator

            from processes.order.order_manager import OrderManager

            manager = OrderManager()
            return manager

    @pytest.mark.unit
    def test_init_creates_handlers(self, order_manager):
        """Test OrderManager initializes handlers."""
        assert order_manager.api_handler is not None
        assert order_manager.sheet_handler is not None
        assert order_manager.comparator is not None

    @pytest.mark.unit
    def test_init_creates_empty_lists(self, order_manager):
        """Test OrderManager initializes empty data lists."""
        assert order_manager.payment_to_process == []
        assert order_manager.sheet_payments == []
        assert order_manager.filtered_payment_data == []
        assert order_manager.new_orders == []
        assert order_manager.successfully_processed_payment == []
        assert order_manager.updated_order_ids == []

    @pytest.mark.unit
    def test_start_initializes_workflow(self, mock_api_handler, mock_sheet_handler, mock_comparator):
        """Test start() initializes the workflow."""
        with (
            patch("orderManagement.order_manager.APIHandler") as api_class,
            patch("orderManagement.order_manager.SheetHandler") as sheet_class,
            patch("orderManagement.order_manager.OrderComparator") as comp_class,
        ):
            api_class.return_value = mock_api_handler
            sheet_class.return_value = mock_sheet_handler
            comp_class.return_value = mock_comparator

            from processes.order.order_manager import OrderManager

            manager = OrderManager()
            manager.start()

            # Verify duplicate check was called
            mock_sheet_handler.remove_duplicates_with_ids.assert_called()
            # Verify API was called
            mock_api_handler.fetch_pending_orders.assert_called()


class TestOrderManagerWorkflow:
    """Tests for OrderManager workflow scenarios."""

    @pytest.fixture
    def setup_mocks(self):
        """Setup all mocks for workflow tests."""
        mock_api = MagicMock()
        mock_sheet = MagicMock()
        mock_comp = MagicMock()

        mock_sheet.remove_duplicates_with_ids.return_value = (0, [])
        mock_sheet.get_status_breakdown.return_value = {}

        return mock_api, mock_sheet, mock_comp

    @pytest.mark.unit
    def test_workflow_no_pending_orders(self, setup_mocks):
        """Test workflow when API returns no pending orders."""
        mock_api, mock_sheet, mock_comp = setup_mocks
        mock_api.fetch_pending_orders.return_value = []
        mock_sheet.read_sheet_payments.return_value = [{"id": "1", "payment_status": "completed"}]

        with (
            patch("orderManagement.order_manager.APIHandler") as api_class,
            patch("orderManagement.order_manager.SheetHandler") as sheet_class,
            patch("orderManagement.order_manager.OrderComparator") as comp_class,
        ):
            api_class.return_value = mock_api
            sheet_class.return_value = mock_sheet
            comp_class.return_value = mock_comp

            from processes.order.order_manager import OrderManager

            manager = OrderManager()
            manager.start()

            # Should not attempt to update anything
            mock_api.update_order_status.assert_not_called()

    @pytest.mark.unit
    def test_workflow_with_matching_paid_orders(self, setup_mocks):
        """Test workflow updates API when sheet has paid orders."""
        mock_api, mock_sheet, mock_comp = setup_mocks

        api_orders = [{"id": "order-1", "payment_status": "pending"}]
        sheet_orders = [{"id": "order-1", "payment_status": "paid"}]

        # Return format from filter_matching_orders
        filtered_data = [
            {
                "order_id": "order-1",
                "api_order": api_orders[0],
                "sheet_order": sheet_orders[0],
                "api_status": "pending",
                "sheet_status": "paid",
                "payment_amount": "100.00",
            }
        ]

        mock_api.fetch_pending_orders.return_value = api_orders
        mock_api.update_order_status.return_value = True
        mock_sheet.read_sheet_payments.return_value = sheet_orders
        mock_comp.filter_matching_orders.return_value = filtered_data
        mock_comp.find_orders_to_update.return_value = filtered_data
        mock_comp.find_new_orders.return_value = []
        mock_comp.get_order_id.side_effect = lambda x: x.get("id", x.get("order_id", ""))
        mock_comp.get_payment_status.side_effect = lambda x: x.get("payment_status", "")

        with (
            patch("orderManagement.order_manager.APIHandler") as api_class,
            patch("orderManagement.order_manager.SheetHandler") as sheet_class,
            patch("orderManagement.order_manager.OrderComparator") as comp_class,
        ):
            api_class.return_value = mock_api
            sheet_class.return_value = mock_sheet
            comp_class.return_value = mock_comp

            from processes.order.order_manager import OrderManager

            manager = OrderManager()
            manager.start()

            # Should update API status
            mock_api.update_order_status.assert_called()

    @pytest.mark.unit
    def test_workflow_appends_new_orders(self, setup_mocks):
        """Test workflow appends new orders to sheet."""
        mock_api, mock_sheet, mock_comp = setup_mocks

        api_orders = [
            {"id": "order-1", "payment_status": "pending"},
            {"id": "order-2", "payment_status": "pending"},
        ]
        sheet_orders = [{"id": "order-1", "payment_status": "paid"}]
        new_orders = [{"id": "order-2", "payment_status": "pending"}]

        mock_api.fetch_pending_orders.return_value = api_orders
        mock_sheet.read_sheet_payments.return_value = sheet_orders
        mock_sheet.append_new_orders.return_value = 1
        mock_comp.filter_matching_orders.return_value = [api_orders[0]]
        mock_comp.find_orders_to_update.return_value = []
        mock_comp.find_new_orders.return_value = new_orders
        mock_comp.get_order_id.side_effect = lambda x: x.get("id", "")

        with (
            patch("orderManagement.order_manager.APIHandler") as api_class,
            patch("orderManagement.order_manager.SheetHandler") as sheet_class,
            patch("orderManagement.order_manager.OrderComparator") as comp_class,
        ):
            api_class.return_value = mock_api
            sheet_class.return_value = mock_sheet
            comp_class.return_value = mock_comp

            from processes.order.order_manager import OrderManager

            manager = OrderManager()
            manager.start()

            # Should append new orders
            mock_sheet.append_new_orders.assert_called_once()


class TestOrderManagerResults:
    """Tests for OrderManager result tracking."""

    @pytest.mark.unit
    def test_tracks_updated_order_ids(self):
        """Test OrderManager tracks successfully updated order IDs."""
        mock_api = MagicMock()
        mock_sheet = MagicMock()
        mock_comp = MagicMock()

        api_orders = [{"id": "order-1", "payment_status": "pending"}]
        sheet_orders = [{"id": "order-1", "payment_status": "paid"}]

        # Return format from filter_matching_orders
        filtered_data = [
            {
                "order_id": "order-1",
                "api_order": api_orders[0],
                "sheet_order": sheet_orders[0],
                "api_status": "pending",
                "sheet_status": "paid",
                "payment_amount": "100.00",
            }
        ]

        mock_api.fetch_pending_orders.return_value = api_orders
        mock_api.update_order_status.return_value = True
        mock_sheet.read_sheet_payments.return_value = sheet_orders
        mock_sheet.remove_duplicates_with_ids.return_value = (0, [])
        mock_sheet.get_status_breakdown.return_value = {}
        mock_comp.filter_matching_orders.return_value = filtered_data
        mock_comp.find_orders_to_update.return_value = filtered_data
        mock_comp.find_new_orders.return_value = []
        mock_comp.get_order_id.side_effect = lambda x: x.get("id", x.get("order_id", ""))
        mock_comp.get_payment_status.side_effect = lambda x: x.get("payment_status", "")

        with (
            patch("orderManagement.order_manager.APIHandler") as api_class,
            patch("orderManagement.order_manager.SheetHandler") as sheet_class,
            patch("orderManagement.order_manager.OrderComparator") as comp_class,
        ):
            api_class.return_value = mock_api
            sheet_class.return_value = mock_sheet
            comp_class.return_value = mock_comp

            from processes.order.order_manager import OrderManager

            manager = OrderManager()
            manager.start()

            assert "order-1" in manager.updated_order_ids

    @pytest.mark.unit
    def test_tracks_duplicates_removed(self):
        """Test OrderManager tracks removed duplicates."""
        mock_api = MagicMock()
        mock_sheet = MagicMock()
        mock_comp = MagicMock()

        mock_api.fetch_pending_orders.return_value = []
        mock_sheet.read_sheet_payments.return_value = []
        mock_sheet.remove_duplicates_with_ids.return_value = (
            2,
            ["dup-1", "dup-2"],
        )
        mock_sheet.get_status_breakdown.return_value = {}
        mock_comp.filter_matching_orders.return_value = []
        mock_comp.find_orders_to_update.return_value = []
        mock_comp.find_new_orders.return_value = []

        with (
            patch("orderManagement.order_manager.APIHandler") as api_class,
            patch("orderManagement.order_manager.SheetHandler") as sheet_class,
            patch("orderManagement.order_manager.OrderComparator") as comp_class,
        ):
            api_class.return_value = mock_api
            sheet_class.return_value = mock_sheet
            comp_class.return_value = mock_comp

            from processes.order.order_manager import OrderManager

            manager = OrderManager()
            manager.start()

            assert manager.duplicates_removed == ["dup-1", "dup-2"]
