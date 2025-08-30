from fastapi import APIRouter, HTTPException, Query, Path, Depends, status
from typing import List, Optional
from api.schemas.order import (
    OrderStatusUpdate,
    OrderResponse,
    OrderListResponse,
    OrderStatus,
    BulkStatusUpdate
)
from api.services.order_service import OrderAPIService
from api.dependencies.auth import get_current_active_user, require_staff

router = APIRouter()
order_service = OrderAPIService()

@router.get("/", response_model=OrderListResponse, dependencies=[Depends(require_staff)])
async def get_all_orders(
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    skip: int = Query(0, ge=0, description="Number of orders to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of orders to return")
):
    orders = await order_service.get_all_orders(status=status)
    total = await order_service.count_orders(status=status)
    return OrderListResponse(
        orders=orders,
        total=total,
        status_filter=status.value if status else None
    )

@router.get("/active", response_model=List[OrderResponse], dependencies=[Depends(require_staff)])
async def get_active_orders():
    return await order_service.get_active_orders()

@router.get("/stats", dependencies=[Depends(require_staff)])
async def get_order_statistics():
    stats = {}
    for s in OrderStatus:
        stats[s.value] = await order_service.count_orders(status=s.value)
    total = await order_service.count_orders()
    return {"total_orders": total, "by_status": stats}

@router.get("/my-orders", response_model=List[OrderResponse])
async def get_my_orders(current_user = Depends(get_current_active_user)):
    return await order_service.get_orders_by_phone(current_user.phone_number)

@router.get("/by-number/{order_number}", response_model=OrderResponse)
async def get_order_by_number(
    order_number: str = Path(..., description="Order number (e.g., ORD00001)"),
    current_user = Depends(get_current_active_user)
):
    order = await order_service.get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_number} not found")

    if current_user.role not in ["admin", "staff"] and order.phone_number != current_user.phone_number:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this order"
        )
    return order

@router.get("/by-phone/{phone_number}", response_model=List[OrderResponse], dependencies=[Depends(require_staff)])
async def get_orders_by_phone(phone_number: str = Path(..., description="Customer phone number")):
    return await order_service.get_orders_by_phone(phone_number)

@router.put("/{order_number}/status", response_model=OrderResponse, dependencies=[Depends(require_staff)])
async def update_order_status(
    order_number: str = Path(..., description="Order number"),
    status_update: OrderStatusUpdate = ...
):
    try:
        updated_order = await order_service.update_order_status(order_number, status_update)
        if not updated_order:
            raise HTTPException(status_code=404, detail=f"Order {order_number} not found")
        return updated_order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bulk/status-update", dependencies=[Depends(require_staff)])
async def bulk_update_order_status(bulk: BulkStatusUpdate):
    results = await order_service.bulk_update_status(bulk.order_numbers, bulk.status_update)
    successful = sum(1 for ok in results.values() if ok)
    failed = len(results) - successful
    return {"success": True, "message": f"Updated {successful} orders, {failed} failed", "results": results}
