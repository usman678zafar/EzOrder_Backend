from typing import List, Optional, Dict
from datetime import datetime
from pymongo import ASCENDING, DESCENDING
from config.database import db
from models.menu import MenuService
from api.schemas.menu import MenuItemCreate, MenuItemUpdate, MenuItemResponse

class MenuAPIService:
    def __init__(self):
        self.collection = db.menu
    
    async def get_next_id(self) -> int:
        """Get the next available ID for a new menu item"""
        # Find the highest ID in the collection
        highest = self.collection.find_one(sort=[("id", DESCENDING)])
        if highest and "id" in highest:
            return highest["id"] + 1
        return 1
    
    async def get_all_items(
        self, 
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MenuItemResponse]:
        """Get all menu items with optional filtering"""
        query = {}
        if category:
            query["category"] = {"$regex": category, "$options": "i"}
        
        cursor = self.collection.find(query).sort("id", ASCENDING).skip(skip).limit(limit)
        items = []
        
        for item in cursor:
            item_dict = {
                "id": item["id"],
                "name": item["name"],
                "price": item["price"],
                "category": item["category"],
                "description": item["description"],
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at")
            }
            items.append(MenuItemResponse(**item_dict))
        
        return items
    
    async def count_items(self, category: Optional[str] = None) -> int:
        """Count menu items with optional category filter"""
        query = {}
        if category:
            query["category"] = {"$regex": category, "$options": "i"}
        return self.collection.count_documents(query)
    
    async def get_item_by_id(self, item_id: int) -> Optional[MenuItemResponse]:
        """Get a specific menu item by ID"""
        item = self.collection.find_one({"id": item_id})
        if not item:
            return None
        
        return MenuItemResponse(
            id=item["id"],
            name=item["name"],
            price=item["price"],
            category=item["category"],
            description=item["description"],
            created_at=item.get("created_at"),
            updated_at=item.get("updated_at")
        )
    
    async def create_item(self, item_data: MenuItemCreate) -> MenuItemResponse:
        """Create a new menu item"""
        # Check if item with same name exists
        existing = self.collection.find_one({"name": {"$regex": f"^{item_data.name}$", "$options": "i"}})
        if existing:
            raise ValueError(f"Menu item with name '{item_data.name}' already exists")
        
        # Get next ID
        new_id = await self.get_next_id()
        
        # Create document
        now = datetime.utcnow()
        item_doc = {
            "id": new_id,
            "name": item_data.name,
            "price": item_data.price,
            "category": item_data.category,
            "description": item_data.description,
            "created_at": now,
            "updated_at": now
        }
        
        # Insert into database
        self.collection.insert_one(item_doc)
        
        return MenuItemResponse(**item_doc)
    
    async def update_item(self, item_id: int, item_update: MenuItemUpdate) -> Optional[MenuItemResponse]:
        """Update an existing menu item"""
        # Check if item exists
        existing = self.collection.find_one({"id": item_id})
        if not existing:
            return None
        
        # Build update document
        update_doc = {"updated_at": datetime.utcnow()}
        
        if item_update.name is not None:
            # Check if new name conflicts with another item
            name_exists = self.collection.find_one({
                "name": {"$regex": f"^{item_update.name}$", "$options": "i"},
                "id": {"$ne": item_id}
            })
            if name_exists:
                raise ValueError(f"Another menu item with name '{item_update.name}' already exists")
            update_doc["name"] = item_update.name
        
        if item_update.price is not None:
            update_doc["price"] = item_update.price
        
        if item_update.category is not None:
            update_doc["category"] = item_update.category
        
        if item_update.description is not None:
            update_doc["description"] = item_update.description
        
        # Update in database
        self.collection.update_one({"id": item_id}, {"$set": update_doc})
        
        # Return updated item
        return await self.get_item_by_id(item_id)
    
    async def delete_item(self, item_id: int) -> bool:
        """Delete a menu item"""
        result = self.collection.delete_one({"id": item_id})
        return result.deleted_count > 0
    
    async def bulk_delete_items(self, item_ids: List[int]) -> int:
        """Delete multiple menu items"""
        result = self.collection.delete_many({"id": {"$in": item_ids}})
        return result.deleted_count
    
    async def get_categories(self) -> List[str]:
        """Get all unique categories"""
        categories = self.collection.distinct("category")
        return sorted(categories)
    
    async def search_items(self, query: str, category: Optional[str] = None) -> List[MenuItemResponse]:
        """Search menu items by name or description"""
        search_query = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}}
            ]
        }
        
        if category:
            search_query["category"] = {"$regex": category, "$options": "i"}
        
        cursor = self.collection.find(search_query).sort("id", ASCENDING)
        items = []
        
        for item in cursor:
            items.append(MenuItemResponse(
                id=item["id"],
                name=item["name"],
                price=item["price"],
                category=item["category"],
                description=item["description"],
                created_at=item.get("created_at"),
                updated_at=item.get("updated_at")
            ))
        
        return items
    
    async def rename_category(self, old_category: str, new_category: str) -> int:
        """Rename a category for all items"""
        result = self.collection.update_many(
            {"category": {"$regex": f"^{old_category}$", "$options": "i"}},
            {
                "$set": {
                    "category": new_category,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count
    
    async def reset_to_default(self):
        """Reset menu to default items"""
        # Clear existing menu
        self.collection.delete_many({})
        
        # Use the existing MenuService to initialize default menu
        MenuService.initialize_menu(self.collection)
        
        # Add timestamps to all items
        now = datetime.utcnow()
        self.collection.update_many(
            {},
            {"$set": {"created_at": now, "updated_at": now}}
        )
