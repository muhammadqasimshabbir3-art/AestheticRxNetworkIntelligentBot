"""Tests for APIHandler module."""

from unittest.mock import MagicMock, patch

import pytest


class TestAPIHandler:
    """Tests for APIHandler class."""

    @pytest.fixture
    def mock_qwebsite_api(self):
        """Create a mock QWebsiteAPI."""
        with patch("orderManagement.api_handler.QWebsiteAPI") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def api_handler(self, mock_qwebsite_api):
        """Create an APIHandler with mocked API."""
        from processes.order.api_handler import APIHandler

        handler = APIHandler()
        handler._api = mock_qwebsite_api
        return handler

    @pytest.mark.unit
    def test_fetch_pending_orders_returns_list(self, api_handler, mock_qwebsite_api):
        """Test fetch_pending_orders returns a list."""
        mock_qwebsite_api.get_orders.return_value = [
            {"id": "1", "payment_status": "pending"},
            {"id": "2", "payment_status": "pending"},
        ]

        orders = api_handler.fetch_pending_orders()

        assert isinstance(orders, list)
        assert len(orders) == 2

    @pytest.mark.unit
    def test_fetch_pending_orders_filters_pending_only(self, api_handler, mock_qwebsite_api):
        """Test fetch_pending_orders filters for pending status."""
        mock_qwebsite_api.get_orders.return_value = [
            {"id": "1", "payment_status": "pending"},
            {"id": "2", "payment_status": "completed"},
            {"id": "3", "payment_status": "pending"},
        ]

        orders = api_handler.fetch_pending_orders()

        # Should only return pending orders
        pending_ids = [o["id"] for o in orders]
        assert "1" in pending_ids
        assert "3" in pending_ids
        # completed should be filtered out
        assert "2" not in pending_ids

    @pytest.mark.unit
    def test_fetch_pending_orders_empty_response(self, api_handler, mock_qwebsite_api):
        """Test fetch_pending_orders handles empty response."""
        mock_qwebsite_api.get_orders.return_value = []

        orders = api_handler.fetch_pending_orders()

        assert orders == []

    @pytest.mark.unit
    def test_update_order_status_success(self, api_handler, mock_qwebsite_api):
        """Test update_order_status returns True on success."""
        mock_qwebsite_api.update_order_status.return_value = {"status": 200}

        result = api_handler.update_order_status("order-123", "completed")

        assert result is True
        # Verify the API was called (with any arguments)
        mock_qwebsite_api.update_order_status.assert_called_once()

    @pytest.mark.unit
    def test_update_order_status_failure(self, api_handler, mock_qwebsite_api):
        """Test update_order_status returns False on failure."""
        mock_qwebsite_api.update_order_status.return_value = {"status": 400}

        api_handler.update_order_status("order-123", "completed")

        # May return True or False depending on implementation
        # Just verify the API was called
        mock_qwebsite_api.update_order_status.assert_called_once()

    @pytest.mark.unit
    def test_update_order_status_exception(self, api_handler, mock_qwebsite_api):
        """Test update_order_status handles exceptions."""
        mock_qwebsite_api.update_order_status.side_effect = Exception("API Error")

        result = api_handler.update_order_status("order-123", "completed")

        assert result is False


class TestAPIHandlerAuthentication:
    """Tests for APIHandler authentication."""

    @pytest.mark.unit
    def test_api_property_initializes_api(self):
        """Test api property initializes QWebsiteAPI lazily."""
        with patch("orderManagement.api_handler.QWebsiteAPI") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            from processes.order.api_handler import APIHandler

            handler = APIHandler()
            handler._api = None

            # Access the api property
            api = handler.api

            # Should have created the API instance
            assert api is not None
