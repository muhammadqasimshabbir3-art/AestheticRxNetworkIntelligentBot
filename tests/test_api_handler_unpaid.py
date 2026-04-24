"""Tests for unpaid order filtering in APIHandler."""

from unittest.mock import MagicMock

import pytest

from processes.order.api_handler import APIHandler


@pytest.mark.unit
def test_fetch_unpaid_orders_filters_paid_statuses():
    api = MagicMock()
    api.get_orders.return_value = [
        {"id": "1", "payment_status": "pending"},
        {"id": "2", "payment_status": "completed"},
        {"id": "3", "payment_status": "paid"},
        {"id": "4", "payment_status": "success"},
        {"id": "5", "payment_status": "failed"},
    ]

    handler = APIHandler(api=api)
    unpaid = handler.fetch_unpaid_orders()

    assert [item["id"] for item in unpaid] == ["1", "5"]
