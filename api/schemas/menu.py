from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MenuItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the menu item")
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    category: str = Field(..., min_length=1, max_length=50, description="Category of the item")
    description: str = Field(..., min_length=1, max_length=200, description="Description of the item")

class MenuItemCreate(MenuItemBase):
    """Schema for creating a new menu item"""
    pass

class MenuItemUpdate(BaseModel):
    """Schema for updating a menu item - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=200)

class MenuItemResponse(MenuItemBase):
    """Schema for menu item response"""
    id: int = Field(..., description="Unique identifier for the menu item")
    created_at: Optional[datetime] = Field(None, description="When the item was created")
    updated_at: Optional[datetime] = Field(None, description="When the item was last updated")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class MenuItemList(BaseModel):
    """Schema for list of menu items"""
    items: List[MenuItemResponse]
    total: int
    category_filter: Optional[str] = None

class MenuBulkOperation(BaseModel):
    """Schema for bulk operations"""
    item_ids: List[int] = Field(..., min_items=1, description="List of menu item IDs")

class OperationResponse(BaseModel):
    """Generic operation response"""
    success: bool
    message: str
    data: Optional[dict] = None

class MenuCategoryUpdate(BaseModel):
    """Schema for updating category name"""
    old_category: str = Field(..., min_length=1, max_length=50)
    new_category: str = Field(..., min_length=1, max_length=50)
