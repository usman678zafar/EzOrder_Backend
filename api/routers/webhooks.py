from fastapi import APIRouter, Depends, Query
from typing import List
from datetime import datetime
from api.dependencies.auth import require_staff
from services.webhook_notification_service import webhook_notification_service
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from fastapi.responses import StreamingResponse
import json
import asyncio

router = APIRouter()

class NotificationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="_id")
    type: str
    data: dict
    created_at: datetime
    read: bool
    read_at: datetime | None = None

class MarkReadRequest(BaseModel):
    notification_ids: List[str]

@router.get("/notifications/unread", response_model=List[NotificationResponse], dependencies=[Depends(require_staff)])
async def get_unread_notifications(limit: int = Query(10, ge=1, le=50)):
    return webhook_notification_service.get_unread_notifications(limit)

@router.post("/notifications/mark-read", dependencies=[Depends(require_staff)])
async def mark_notifications_as_read(request: MarkReadRequest):
    count = webhook_notification_service.mark_as_read(request.notification_ids)
    return {"success": True, "marked_count": count}

@router.get("/notifications/count", dependencies=[Depends(require_staff)])
async def get_notification_count(recent_minutes: int = Query(5, ge=1, le=60)):
    count = webhook_notification_service.get_recent_count(recent_minutes)
    return {"unread_count": count, "recent_minutes": recent_minutes}

@router.get("/notifications/stream", dependencies=[Depends(require_staff)])
async def notification_stream():
    async def event_generator():
        while True:
            notifications = webhook_notification_service.get_unread_notifications(5)
            if notifications:
                yield f"data: {json.dumps({'type': 'new_notifications', 'notifications': notifications})}\n\n"
            await asyncio.sleep(2)
    return StreamingResponse(event_generator(), media_type="text/event-stream")
