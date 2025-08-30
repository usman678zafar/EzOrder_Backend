from typing import List, Optional, Dict, Union
from datetime import datetime
from pymongo import DESCENDING
from bson import ObjectId
from config.database import db
from api.schemas.order import OrderStatus, OrderStatusUpdate, OrderResponse
from services.whatsapp_notification_service import WhatsAppNotificationService

class OrderAPIService:
    def __init__(self):
        self.collection = db.orders
        self.whatsapp_service = WhatsAppNotificationService()

    async def get_all_orders(
        self,
        status: Optional[Union[OrderStatus, str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrderResponse]:
        query = {}
        if status:
            query["status"] = status.value if isinstance(status, OrderStatus) else status
        cursor = self.collection.find(query).sort("created_at", DESCENDING).skip(skip).limit(limit)
        return [OrderResponse(**self._format_order_response(o)) for o in cursor]

    async def count_orders(self, status: Optional[Union[OrderStatus, str]] = None) -> int:
        query = {}
        if status:
            query["status"] = status.value if isinstance(status, OrderStatus) else status
        return self.collection.count_documents(query)

    async def get_order_by_number(self, order_number: str) -> Optional[OrderResponse]:
        order = self.collection.find_one({"order_number": order_number})
        if not order:
            return None
        return OrderResponse(**self._format_order_response(order))

    async def get_order_by_id(self, order_id: str) -> Optional[OrderResponse]:
        try:
            order = self.collection.find_one({"_id": ObjectId(order_id)})
            if not order:
                return None
            return OrderResponse(**self._format_order_response(order))
        except:
            return None

    async def update_order_status(self, order_number: str, status_update: OrderStatusUpdate) -> Optional[OrderResponse]:
        order = self.collection.find_one({"order_number": order_number})
        if not order:
            return None

        current_status = order.get("status", "confirmed")
        new_status = status_update.status.value

        if not self._is_valid_status_transition(current_status, new_status):
            raise ValueError(f"Invalid status transition from {current_status} to {new_status}")

        status_entry = {
            "status": new_status,
            "timestamp": datetime.utcnow(),
            "notes": status_update.notes,
            "estimated_time": status_update.estimated_time
        }

        self.collection.update_one(
            {"order_number": order_number},
            {"$set": {"status": new_status, "updated_at": datetime.utcnow()},
             "$push": {"status_history": status_entry}}
        )

        self.whatsapp_service.send_order_status_notification(
            phone_number=order["phone_number"],
            order_number=order_number,
            status=new_status,
            customer_name=order["user_name"],
            estimated_time=status_update.estimated_time,
            notes=status_update.notes
        )

        return await self.get_order_by_number(order_number)

    async def get_orders_by_phone(self, phone_number: str) -> List[OrderResponse]:
        cursor = self.collection.find({"phone_number": phone_number}).sort("created_at", DESCENDING)
        return [OrderResponse(**self._format_order_response(o)) for o in cursor]

    async def get_active_orders(self) -> List[OrderResponse]:
        query = {"status": {"$nin": [OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value]}}
        cursor = self.collection.find(query).sort("created_at", DESCENDING)
        return [OrderResponse(**self._format_order_response(o)) for o in cursor]

    async def bulk_update_status(self, order_numbers: List[str], status_update: OrderStatusUpdate) -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        for num in order_numbers:
            try:
                updated_order = await self.update_order_status(num, status_update)
                results[num] = updated_order is not None
            except Exception as e:
                print(f"Error updating order {num}: {str(e)}")
                results[num] = False
        return results

    def _format_order_response(self, order: Dict) -> Dict:
        return {
            "order_number": order["order_number"],
            "user_name": order["user_name"],
            "phone_number": order["phone_number"],
            "items": order["items"],
            "total": order["total"],
            "delivery_address": order["delivery_address"],
            "delivery_city": order["delivery_city"],
            "delivery_postal": order.get("delivery_postal", ""),
            "delivery_notes": order.get("delivery_notes", ""),
            "status": order["status"],
            "created_at": order["created_at"],
            "updated_at": order.get("updated_at"),
            "status_history": order.get("status_history", [])
        }

    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        valid_transitions = {
            "confirmed": ["preparing", "cancelled"],
            "preparing": ["ready", "cancelled"],
            "ready": ["out_for_delivery", "cancelled"],
            "out_for_delivery": ["delivered", "cancelled"],
            "delivered": [],
            "cancelled": []
        }
        return new_status in valid_transitions.get(current_status, [])
