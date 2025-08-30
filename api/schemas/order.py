from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    notes: Optional[str] = Field(None, description="Additional notes about the status change")
    estimated_time: Optional[int] = Field(None, description="Estimated time in minutes for next status")

class OrderItemResponse(BaseModel):
    id: int
    name: str
    price: float
    quantity: int
    subtotal: float

class OrderResponse(BaseModel):
    order_number: str
    user_name: str
    phone_number: str
    items: List[OrderItemResponse]
    total: float
    delivery_address: str
    delivery_city: str
    delivery_postal: Optional[str]
    delivery_notes: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    status_history: List[Dict] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    status_filter: Optional[str] = None

class BulkStatusUpdate(BaseModel):
    order_numbers: List[str]
    status_update: OrderStatusUpdate
