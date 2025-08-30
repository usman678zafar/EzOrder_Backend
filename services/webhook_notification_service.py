from typing import List, Dict, Optional
from datetime import datetime, timedelta
from config.database import db
from models.webhook_notification import NotificationType, WebhookNotification
import asyncio

class WebhookNotificationService:
    def __init__(self):
        self.collection = db.notifications
        
    def create_order_notification(self, order_data: Dict) -> bool:
        """Create a new order notification"""
        try:
            notification = WebhookNotification(
                notification_type=NotificationType.ORDER_CONFIRMED,
                data={
                    "order_number": order_data.get("order_number"),
                    "customer_name": order_data.get("user_name"),
                    "phone_number": order_data.get("phone_number"),
                    "total": order_data.get("total"),
                    "items": order_data.get("items", []),
                    "delivery_address": order_data.get("delivery_address"),
                    "delivery_city": order_data.get("delivery_city"),
                    "created_at": order_data.get("created_at", datetime.utcnow())
                }
            )
            
            result = self.collection.insert_one(notification.to_dict())
            print(f"✅ Order notification created: {notification.data['order_number']}")
            return bool(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Error creating notification: {e}")
            return False
    
    def get_unread_notifications(self, limit: int = 10) -> List[Dict]:
        """Get unread notifications"""
        try:
            notifications = list(self.collection.find(
                {"read": False}
            ).sort("created_at", -1).limit(limit))
            
            # Convert ObjectId to string
            for notif in notifications:
                notif["_id"] = str(notif["_id"])
                
            return notifications
        except Exception as e:
            print(f"Error fetching notifications: {e}")
            return []
    
    def mark_as_read(self, notification_ids: List[str]) -> int:
        """Mark notifications as read"""
        from bson import ObjectId
        try:
            object_ids = [ObjectId(id) for id in notification_ids]
            result = self.collection.update_many(
                {"_id": {"$in": object_ids}},
                {
                    "$set": {
                        "read": True,
                        "read_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count
        except Exception as e:
            print(f"Error marking notifications as read: {e}")
            return 0
    
    def get_recent_count(self, minutes: int = 5) -> int:
        """Get count of recent notifications"""
        try:
            since = datetime.utcnow() - timedelta(minutes=minutes)
            count = self.collection.count_documents({
                "created_at": {"$gte": since},
                "read": False
            })
            return count
        except:
            return 0

# Global instance
webhook_notification_service = WebhookNotificationService()
