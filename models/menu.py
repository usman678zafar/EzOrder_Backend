from typing import List, Dict, Optional

class MenuItem:
    def __init__(self, id: int, name: str, price: float, category: str, description: str):
        self.id = id
        self.name = name
        self.price = price
        self.category = category
        self.description = description

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "category": self.category,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'MenuItem':
        return cls(
            id=data['id'],
            name=data['name'],
            price=data['price'],
            category=data['category'],
            description=data['description']
        )

class MenuService:
    DEFAULT_MENU_ITEMS = [
        MenuItem(1, "Margherita Pizza", 12.99, "Pizza", "Classic tomato sauce, mozzarella, basil"),
        MenuItem(2, "Pepperoni Pizza", 14.99, "Pizza", "Tomato sauce, mozzarella, pepperoni"),
        MenuItem(3, "Caesar Salad", 8.99, "Salad", "Romaine lettuce, croutons, parmesan"),
        MenuItem(4, "Grilled Chicken", 16.99, "Main", "Herb-marinated chicken breast"),
        MenuItem(5, "Pasta Carbonara", 13.99, "Pasta", "Creamy pasta with bacon"),
        MenuItem(6, "Tiramisu", 6.99, "Dessert", "Classic Italian dessert"),
        MenuItem(7, "Coca Cola", 2.99, "Beverage", "330ml can"),
        MenuItem(8, "Fresh Orange Juice", 4.99, "Beverage", "Freshly squeezed"),
    ]
    
    @classmethod
    def initialize_menu(cls, menu_collection):
        """Initialize menu items in MongoDB"""
        menu_collection.delete_many({})
        menu_items = [item.to_dict() for item in cls.DEFAULT_MENU_ITEMS]
        menu_collection.insert_many(menu_items)
        print("Menu initialized!")
