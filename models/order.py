from typing import List, Dict, Optional
from datetime import datetime

class OrderItem:
    def __init__(self, id: int, name: str, price: float, quantity: int):
        self.id = id
        self.name = name
        self.price = price
        self.quantity = quantity
        self.subtotal = price * quantity

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'quantity': self.quantity,
            'subtotal': self.subtotal
        }

class Order:
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        self.items: List[OrderItem] = []
        self.total = 0.0

    def add_item(self, item: OrderItem):
        self.items.append(item)
        self.total += item.subtotal

    def to_dict(self) -> Dict:
        return {
            'items': [item.to_dict() for item in self.items],
            'total': self.total
        }
