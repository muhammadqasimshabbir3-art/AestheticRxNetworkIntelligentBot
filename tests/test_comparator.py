"""Tests for OrderComparator module."""

import pytest

from processes.order.comparator import OrderComparator


class TestOrderComparator:
    """Tests for OrderComparator class."""

    @pytest.fixture
    def comparator(self):
        """Create a fresh comparator instance."""
        return OrderComparator()

    @pytest.mark.unit
    def test_get_order_id_with_lowercase_id(self, comparator):
        """Test get_order_id with lowercase 'id' key."""
        order = {"id": "order-123", "name": "Test"}
        assert comparator.get_order_id(order) == "order-123"

    @pytest.mark.unit
    def test_get_order_id_with_uppercase_id(self, comparator):
        """Test get_order_id with uppercase 'ID' key."""
        order = {"ID": "order-456", "name": "Test"}
        assert comparator.get_order_id(order) == "order-456"

    @pytest.mark.unit
    def test_get_order_id_strips_whitespace(self, comparator):
        """Test get_order_id strips whitespace from ID."""
        order = {"id": "  order-789  ", "name": "Test"}
        assert comparator.get_order_id(order) == "order-789"

    @pytest.mark.unit
    def test_get_order_id_returns_empty_when_missing(self, comparator):
        """Test get_order_id returns empty string when ID is missing."""
        order = {"name": "Test", "status": "pending"}
        assert comparator.get_order_id(order) == ""

    @pytest.mark.unit
    def test_get_payment_status_with_payment_status_key(self, comparator):
        """Test get_payment_status with 'payment_status' key."""
        order = {"id": "1", "payment_status": "pending"}
        assert comparator.get_payment_status(order) == "pending"

    @pytest.mark.unit
    def test_get_payment_status_with_paymentStatus_key(self, comparator):
        """Test get_payment_status with 'paymentStatus' key."""
        order = {"id": "1", "paymentStatus": "paid"}
        assert comparator.get_payment_status(order) == "paid"

    @pytest.mark.unit
    def test_get_payment_status_with_payment_status_space_key(self, comparator):
        """Test get_payment_status with 'Payment Status' key."""
        order = {"id": "1", "Payment Status": "completed"}
        assert comparator.get_payment_status(order) == "completed"

    @pytest.mark.unit
    def test_get_payment_status_returns_lowercase(self, comparator):
        """Test get_payment_status returns lowercase status."""
        order = {"id": "1", "payment_status": "PENDING"}
        assert comparator.get_payment_status(order) == "pending"

    @pytest.mark.unit
    def test_filter_matching_orders(self, comparator):
        """Test filter_matching_orders returns orders present in both lists."""
        api_orders = [
            {"id": "order-1", "payment_status": "pending"},
            {"id": "order-2", "payment_status": "pending"},
            {"id": "order-3", "payment_status": "pending"},
        ]
        sheet_orders = [
            {"id": "order-1", "payment_status": "paid"},
            {"id": "order-3", "payment_status": "completed"},
            {"id": "order-4", "payment_status": "pending"},
        ]

        matching = comparator.filter_matching_orders(api_orders, sheet_orders)

        # Should contain order-1 and order-3 (present in both)
        # Returns list of dicts with 'order_id' key
        matching_ids = [o["order_id"] for o in matching]
        assert "order-1" in matching_ids
        assert "order-3" in matching_ids
        assert "order-2" not in matching_ids
        assert "order-4" not in matching_ids

    @pytest.mark.unit
    def test_filter_matching_orders_empty_api_orders(self, comparator):
        """Test filter_matching_orders with empty API orders."""
        api_orders = []
        sheet_orders = [{"id": "order-1", "payment_status": "paid"}]

        matching = comparator.filter_matching_orders(api_orders, sheet_orders)
        assert matching == []

    @pytest.mark.unit
    def test_filter_matching_orders_empty_sheet_orders(self, comparator):
        """Test filter_matching_orders with empty sheet orders."""
        api_orders = [{"id": "order-1", "payment_status": "pending"}]
        sheet_orders = []

        matching = comparator.filter_matching_orders(api_orders, sheet_orders)
        assert matching == []

    @pytest.mark.unit
    def test_find_orders_to_update(self, comparator):
        """Test find_orders_to_update returns orders where API=pending and sheet=paid/completed."""
        # First, create filtered_payment_data (output of filter_matching_orders)
        filtered_payment_data = [
            {
                "order_id": "order-1",
                "api_order": {"id": "order-1", "payment_status": "pending"},
                "sheet_order": {"id": "order-1", "payment_status": "paid"},
                "api_status": "pending",
                "sheet_status": "paid",  # Should be updated
            },
            {
                "order_id": "order-2",
                "api_order": {"id": "order-2", "payment_status": "pending"},
                "sheet_order": {"id": "order-2", "payment_status": "pending"},
                "api_status": "pending",
                "sheet_status": "pending",  # Same status, skip
            },
            {
                "order_id": "order-3",
                "api_order": {"id": "order-3", "payment_status": "pending"},
                "sheet_order": {"id": "order-3", "payment_status": "completed"},
                "api_status": "pending",
                "sheet_status": "completed",  # Should be updated
            },
        ]

        to_update = comparator.find_orders_to_update(filtered_payment_data)

        update_ids = [o["order_id"] for o in to_update]
        assert "order-1" in update_ids
        assert "order-3" in update_ids
        assert "order-2" not in update_ids

    @pytest.mark.unit
    def test_find_new_orders(self, comparator):
        """Test find_new_orders returns orders in API but not in sheet."""
        api_orders = [
            {"id": "order-1", "payment_status": "pending"},
            {"id": "order-2", "payment_status": "pending"},
            {"id": "order-3", "payment_status": "pending"},
        ]
        sheet_orders = [
            {"id": "order-1", "payment_status": "paid"},
            {"id": "order-4", "payment_status": "pending"},
        ]

        new_orders = comparator.find_new_orders(api_orders, sheet_orders)

        new_ids = [comparator.get_order_id(o) for o in new_orders]
        assert "order-2" in new_ids
        assert "order-3" in new_ids
        assert "order-1" not in new_ids  # Already in sheet

    @pytest.mark.unit
    def test_find_new_orders_all_new(self, comparator):
        """Test find_new_orders when all API orders are new."""
        api_orders = [
            {"id": "order-1", "payment_status": "pending"},
            {"id": "order-2", "payment_status": "pending"},
        ]
        sheet_orders = []

        new_orders = comparator.find_new_orders(api_orders, sheet_orders)
        assert len(new_orders) == 2

    @pytest.mark.unit
    def test_find_new_orders_none_new(self, comparator):
        """Test find_new_orders when no API orders are new."""
        api_orders = [
            {"id": "order-1", "payment_status": "pending"},
        ]
        sheet_orders = [
            {"id": "order-1", "payment_status": "paid"},
        ]

        new_orders = comparator.find_new_orders(api_orders, sheet_orders)
        assert len(new_orders) == 0


class TestOrderComparatorEdgeCases:
    """Edge case tests for OrderComparator."""

    @pytest.fixture
    def comparator(self):
        """Create a fresh comparator instance."""
        return OrderComparator()

    @pytest.mark.unit
    def test_handles_none_values_in_order(self, comparator):
        """Test handling of None values in order dict."""
        order = {"id": None, "payment_status": None}
        # get_order_id returns str(None) which is "None", but stripped
        result = comparator.get_order_id(order)
        # When value is None, the fallback checks other keys
        assert result == "" or result == "None"
        # get_payment_status returns empty for None
        assert comparator.get_payment_status(order) == "none"

    @pytest.mark.unit
    def test_handles_empty_string_values(self, comparator):
        """Test handling of empty string values."""
        order = {"id": "", "payment_status": ""}
        assert comparator.get_order_id(order) == ""
        assert comparator.get_payment_status(order) == ""

    @pytest.mark.unit
    def test_handles_whitespace_in_id(self, comparator):
        """Test handling of whitespace in ID."""
        order = {"id": "  order-123  ", "payment_status": "pending"}
        # Assuming the comparator strips whitespace
        result = comparator.get_order_id(order)
        assert result.strip() == "order-123"

    @pytest.mark.unit
    def test_handles_mixed_case_status(self, comparator):
        """Test handling of mixed case status values."""
        order = {"id": "1", "payment_status": "PeNdInG"}
        assert comparator.get_payment_status(order) == "pending"
