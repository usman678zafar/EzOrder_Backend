from typing import List, Dict
from datetime import datetime
from agents import function_tool
from config.database import db
from models.order import Order, OrderItem
from utils.phone_utils import clean_phone_number
import json

class OrderManager:
    user_states: Dict[str, Dict] = {}
    
    @classmethod
    def get_or_create_order(cls, phone_number: str) -> Order:
        """Get or create order with consistent phone handling"""
        cleaned_phone = clean_phone_number(phone_number)
        
        if cleaned_phone not in cls.user_states:
            cls.user_states[cleaned_phone] = {}
            
        if 'current_order' not in cls.user_states[cleaned_phone]:
            cls.user_states[cleaned_phone]['current_order'] = Order(cleaned_phone)
            
        return cls.user_states[cleaned_phone]['current_order']
    
    @classmethod
    def clear_order(cls, phone_number: str):
        """Clear order for a user"""
        cleaned_phone = clean_phone_number(phone_number)
        
        if cleaned_phone in cls.user_states:
            cls.user_states[cleaned_phone]['current_order'] = Order(cleaned_phone)

# Base functions that can be called directly

def add_to_order_base(phone_number: str, item_ids: List[int], quantities: List[int] = None) -> str:
    """Base function that adds items to order with better formatting"""
    try:
        cleaned_phone = clean_phone_number(phone_number)
        
        # Verify user exists
        user = db.users.find_one({"phone_number": cleaned_phone})
        if not user:
            return "❌ Please complete registration first."
            
        if quantities is None:
            quantities = [1] * len(item_ids)
            
        order = OrderManager.get_or_create_order(cleaned_phone)
        order_summary = "✅ *Added to your order:*\n\n"
        items_added = 0
        
        for item_id, quantity in zip(item_ids, quantities):
            if quantity <= 0:
                continue
                
            item = db.menu.find_one({"id": item_id})
            if item:
                # Create OrderItem and add to order
                order_item = OrderItem(
                    id=item['id'],
                    name=item['name'],
                    price=item['price'],
                    quantity=quantity
                )
                order.add_item(order_item)
                
                order_summary += f"• {quantity}x *{item['name']}* - *PKR{item['price'] * quantity:.2f}*\n"
                items_added += 1
        
        if items_added > 0:
            order_summary += f"\n💰 *Current Total: PKR{order.total:.2f}*\n\n"
            order_summary += "_Send *'view order'* to see cart_\n"
            order_summary += "_Send *'menu'* for more items_\n"
            order_summary += "_Send *'confirm'* when ready_"
        else:
            order_summary = "❌ No items added. Please check item numbers."
            
        return order_summary
        
    except Exception as e:
        print(f"Error in add_to_order: {str(e)}")
        return f"❌ Error: Please try again."

def view_current_order_base(phone_number: str) -> str:
    """Base function that shows the current order for the user"""
    try:
        cleaned_phone = clean_phone_number(phone_number)
        
        order = OrderManager.get_or_create_order(cleaned_phone)
        if not order.items:
            return "🛒 *Your cart is empty*\n\n_Type_ *'menu'* _to see our offerings!_"
        
        order_text = "🛒 *YOUR CURRENT ORDER:*\n"
        order_text += "━━━━━━━━━━━━━━━━━━\n"
        
        for item in order.items:
            order_text += f"• {item.quantity}x *{item.name}* - *PKR{item.subtotal:.2f}*\n"
        
        order_text += "━━━━━━━━━━━━━━━━━━\n"
        order_text += f"💰 *TOTAL: PKR{order.total:.2f}*\n\n"
        order_text += "_Type_ *'confirm order'* _to place this order_\n"
        order_text += "_Type_ *'menu'* _to add more items_"
        
        return order_text
        
    except Exception as e:
        print(f"Error in view_current_order: {str(e)}")
        return f"❌ Error viewing order: {str(e)}"

def confirm_order_base(phone_number: str, delivery_notes: str = "") -> str:
    """Base function that confirms and saves the order with proper error handling and notifications"""
    try:
        cleaned_phone = clean_phone_number(phone_number)
        
        # Check user exists
        user = db.users.find_one({"phone_number": cleaned_phone})
        if not user:
            return "⚠ Please complete registration before confirming your order."
        
        # Get current order
        order = OrderManager.get_or_create_order(cleaned_phone)
        if not order.items:
            return "⚠ Your cart is empty. Please add items before confirming!"
        
        # Generate simple order number
        order_count = db.orders.count_documents({})
        order_number = f"ORD{order_count + 1:05d}"
        
        # Create order document
        order_doc = {
            "phone_number": cleaned_phone,
            "user_name": user.get('name', 'Customer'),
            "items": [{
                'id': item.id,
                'name': item.name,
                'price': item.price,
                'quantity': item.quantity,
                'subtotal': item.subtotal
            } for item in order.items],
            "total": order.total,
            "delivery_address": user.get('address', ''),
            "delivery_city": user.get('city', ''),
            "delivery_postal": user.get('postal_code', ''),
            "delivery_notes": delivery_notes or "",
            "status": "confirmed",
            "created_at": datetime.utcnow(),
            "order_number": order_number
        }
        
        print(f"Attempting to save order: {order_number}")
        print(f"Order document: {order_doc}")
        
        # Save to database
        try:
            result = db.orders.insert_one(order_doc)
            
            if result.inserted_id:
                print(f"✅ Order saved successfully! ID: {result.inserted_id}")
                
                # Create notification using the webhook notification service
                from services.webhook_notification_service import webhook_notification_service
                webhook_notification_service.create_order_notification(order_doc)
                
                # Clear only after successful save
                OrderManager.clear_order(cleaned_phone)
            else:
                print("❌ Failed to save order - no inserted_id returned")
                return "⚠ Failed to save order. Please try again."
                
        except Exception as e:
            print(f"❌ Database save error: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"⚠ Error saving order: {str(e)}"
        
        # Format WhatsApp confirmation
        confirmation = "✅ *ORDER CONFIRMED!*\n"
        confirmation += "━━━━━━━━━━━━━━━━━━\n\n"
        confirmation += f"📋 *Order #:* {order_number}\n"
        confirmation += f"👤 *Customer:* {user['name']}\n"
        confirmation += f"📍 *Delivery:* {user['address']}, {user['city']}\n"
        if delivery_notes:
            confirmation += f"📝 *Notes:* {delivery_notes}\n"
        
        confirmation += "\n*ORDER DETAILS:*\n"
        for item in order.items:
            confirmation += f"• {item.quantity}x *{item.name}* - *PKR{item.subtotal:.2f}*\n"
        
        confirmation += f"\n💰 *TOTAL: PKR{order.total:.2f}*\n"
        confirmation += "\n⏱ *Estimated delivery:* 30-45 minutes\n"
        confirmation += "📞 We'll call if needed\n\n"
        confirmation += "*Thank you for your order!* 🙏"
        
        return confirmation
        
    except Exception as e:
        print(f"❌ Critical error in confirm_order: {str(e)}")
        import traceback
        traceback.print_exc()
        return "⚠ Critical error. Your order was not processed. Please try again."

# Decorated versions for agent use

@function_tool
def add_to_order(phone_number: str, item_ids: List[int], quantities: List[int] = None) -> str:
    """Adds items to order with better formatting"""
    return add_to_order_base(phone_number, item_ids, quantities)

@function_tool
def view_current_order(phone_number: str) -> str:
    """Shows the current order for the user"""
    return view_current_order_base(phone_number)

@function_tool
def confirm_order(phone_number: str, delivery_notes: str = "") -> str:
    """Confirms and saves the order with proper error handling and notifications"""
    return confirm_order_base(phone_number, delivery_notes)
