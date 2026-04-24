"""Order model for AestheticRxNetwork API."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class Order(BaseModel):
    """Order model representing an order from AestheticRxNetwork API."""

    id: str
    order_number: str
    doctor_id: int
    doctor_name: str
    doctor_email: str
    product_id: int
    product_name: str
    product_price: Decimal
    qty: int
    order_total: Decimal
    payment_amount: Decimal
    remaining_amount: Decimal
    payment_status: str
    payment_method: str | None = None
    order_date: datetime | None = None
    payment_date: datetime | None = None
    notes: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


class OrderList(BaseModel):
    """Container for a list of orders."""

    orders: list[Order] = Field(default_factory=list)

    @property
    def count(self) -> int:
        """Get the number of orders."""
        return len(self.orders)

    @classmethod
    def from_api_response(cls, data: list[dict]) -> "OrderList":
        """Create OrderList from API response data."""
        return cls(orders=[Order(**item) for item in data])
