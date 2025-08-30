from datetime import datetime
from typing import Dict, Optional
from enum import Enum

class NotificationType(str, Enum):
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_STATUS_CHANGED = "order_status_changed"

class WebhookNotification:
    def __init__(self, notification_type: NotificationType, data: Dict):
        self.type = notification_type
        self.data = data
        self.created_at = datetime.utcnow()
        self.read = False
        self.read_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "data": self.data,
            "created_at": self.created_at,
            "read": self.read,
            "read_at": self.read_at
        }
