from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import List, Optional
from api.schemas.menu import (
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemResponse,
    MenuItemList,
    MenuBulkOperation,
    OperationResponse,
    MenuCategoryUpdate
)
from api.services.menu_service import MenuAPIService
from api.dependencies.auth import get_current_active_user, require_admin, require_staff

router = APIRouter()
menu_service = MenuAPIService()

# Public endpoints (no authentication required)
@router.get("/", response_model=MenuItemList)
async def get_all_menu_items(
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return")
):
    """Get all menu items with optional filtering - PUBLIC"""
    items = await menu_service.get_all_items(category=category, skip=skip, limit=limit)
    total = await menu_service.count_items(category=category)
    
    return MenuItemList(
        items=items,
        total=total,
        category_filter=category
    )

@router.get("/categories", response_model=List[str])
async def get_all_categories():
    """Get all unique categories - PUBLIC"""
    return await menu_service.get_categories()

@router.get("/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(
    item_id: int = Path(..., description="Menu item ID", ge=1)
):
    """Get a specific menu item by ID - PUBLIC"""
    item = await menu_service.get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Menu item with ID {item_id} not found")
    return item

@router.post("/search", response_model=MenuItemList)
async def search_menu_items(
    query: str = Query(..., min_length=1, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Search menu items by name or description - PUBLIC"""
    items = await menu_service.search_items(query, category)
    
    return MenuItemList(
        items=items,
        total=len(items),
        category_filter=category
    )

# Protected endpoints (require authentication and proper role)
@router.post("/", response_model=MenuItemResponse, status_code=201, dependencies=[Depends(require_staff)])
async def create_menu_item(item: MenuItemCreate):
    """Create a new menu item - STAFF/ADMIN ONLY"""
    try:
        new_item = await menu_service.create_item(item)
        return new_item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{item_id}", response_model=MenuItemResponse, dependencies=[Depends(require_staff)])
async def update_menu_item(
    item_id: int = Path(..., description="Menu item ID", ge=1),
    item_update: MenuItemUpdate = ...
):
    """Update an existing menu item - STAFF/ADMIN ONLY"""
    updated_item = await menu_service.update_item(item_id, item_update)
    if not updated_item:
        raise HTTPException(status_code=404, detail=f"Menu item with ID {item_id} not found")
    return updated_item

@router.delete("/{item_id}", response_model=OperationResponse, dependencies=[Depends(require_admin)])
async def delete_menu_item(
    item_id: int = Path(..., description="Menu item ID", ge=1)
):
    """Delete a menu item - ADMIN ONLY"""
    result = await menu_service.delete_item(item_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Menu item with ID {item_id} not found")
    
    return OperationResponse(
        success=True,
        message=f"Menu item with ID {item_id} successfully deleted"
    )

@router.post("/bulk/delete", response_model=OperationResponse, dependencies=[Depends(require_admin)])
async def bulk_delete_menu_items(bulk_operation: MenuBulkOperation):
    """Delete multiple menu items - ADMIN ONLY"""
    deleted_count = await menu_service.bulk_delete_items(bulk_operation.item_ids)
    
    return OperationResponse(
        success=True,
        message=f"Successfully deleted {deleted_count} menu items",
        data={"deleted_count": deleted_count, "requested_ids": bulk_operation.item_ids}
    )

@router.put("/category/rename", response_model=OperationResponse, dependencies=[Depends(require_staff)])
async def rename_category(category_update: MenuCategoryUpdate):
    """Rename a category for all items - STAFF/ADMIN ONLY"""
    updated_count = await menu_service.rename_category(
        category_update.old_category,
        category_update.new_category
    )
    
    return OperationResponse(
        success=True,
        message=f"Successfully renamed category from '{category_update.old_category}' to '{category_update.new_category}'",
        data={"updated_count": updated_count}
    )

@router.post("/reset", response_model=OperationResponse, dependencies=[Depends(require_admin)])
async def reset_menu_to_default():
    """Reset menu to default items (WARNING: This will delete all current items) - ADMIN ONLY"""
    await menu_service.reset_to_default()
    
    return OperationResponse(
        success=True,
        message="Menu has been reset to default items"
    )
