from whatsapp_api_client_python import API
from config.settings import settings
from typing import Optional
import asyncio

class WhatsAppNotificationService:
    def __init__(self):
        self.greenAPI = API.GreenAPI(
            idInstance=settings.WHATSAPP_INSTANCE_ID,
            apiTokenInstance=settings.WHATSAPP_TOKEN
        )
    
    def send_order_status_notification(self, phone_number: str, order_number: str, 
                                     status: str, customer_name: str, 
                                     estimated_time: Optional[int] = None,
                                     notes: Optional[str] = None) -> bool:
        """Send order status update to customer via WhatsApp"""
        try:
            # Format phone number for WhatsApp
            whatsapp_number = f"{phone_number}@c.us"
            
            # Create status-specific messages
            status_messages = {
                "preparing": f"""🍳 *Order Update*

Hi {customer_name}! 

Your order *#{order_number}* is now being *PREPARED* by our chef! 👨‍🍳

{f"⏱️ Estimated time: *{estimated_time} minutes*" if estimated_time else ""}
{f"📝 Note: {notes}" if notes else ""}

We'll notify you when it's ready!""",

                "ready": f"""✅ *Order Ready!*

Hi {customer_name}! 

Great news! Your order *#{order_number}* is *READY* and will be out for delivery soon! 📦

{f"⏱️ Estimated delivery time: *{estimated_time} minutes*" if estimated_time else ""}
{f"📝 Note: {notes}" if notes else ""}

Our delivery partner will be on their way shortly!""",

                "out_for_delivery": f"""🚗 *Out for Delivery!*

Hi {customer_name}! 

Your order *#{order_number}* is *ON THE WAY* to you! 🛵

{f"⏱️ Estimated arrival: *{estimated_time} minutes*" if estimated_time else ""}
{f"📝 Note: {notes}" if notes else ""}

Our delivery partner will call you upon arrival.""",

                "delivered": f"""✅ *Order Delivered!*

Hi {customer_name}! 

Your order *#{order_number}* has been *DELIVERED*! 🎉

{f"📝 Note: {notes}" if notes else ""}

Thank you for choosing us! We hope you enjoy your meal! 🍽️

_Rate your experience by replying with 1-5 stars ⭐_""",

                "cancelled": f"""❌ *Order Cancelled*

Hi {customer_name}, 

Your order *#{order_number}* has been *CANCELLED*.

{f"📝 Reason: {notes}" if notes else ""}

If you have any questions, please feel free to message us.

We hope to serve you again soon! 🙏"""
            }
            
            # Get the appropriate message
            message = status_messages.get(status)
            
            if not message:
                message = f"""📋 *Order Update*

Hi {customer_name}!

Your order *#{order_number}* status: *{status.upper()}*

{f"📝 Note: {notes}" if notes else ""}"""
            
            # Send the message
            response = self.greenAPI.sending.sendMessage(whatsapp_number, message)
            
            if response.data:
                print(f"✅ WhatsApp notification sent for order {order_number} - Status: {status}")
                return True
            else:
                print(f"❌ Failed to send WhatsApp notification: {response.error}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending WhatsApp notification: {str(e)}")
            return False
    
    async def send_order_status_notification_async(self, *args, **kwargs):
        """Async wrapper for sending notifications"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send_order_status_notification, *args, **kwargs)
