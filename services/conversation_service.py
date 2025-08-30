from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config.database import db
from config.settings import settings
from utils.phone_utils import clean_phone_number

class ConversationService:
    @staticmethod
    def save_conversation(phone_number: str, role: str, message: str, metadata: Dict = None):
        """Save conversation message with optional metadata"""
        try:
            cleaned_phone = clean_phone_number(phone_number)
            
            doc = {
                "phone_number": cleaned_phone,
                "role": role,  # "user" or "assistant"
                "message": message,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
            db.conversations.insert_one(doc)
        except Exception as e:
            print(f"Error saving conversation: {e}")

    @staticmethod
    def get_conversation_history(phone_number: str, limit: int = None, hours: int = None) -> Dict:
        """Get structured conversation history with context"""
        # Use environment variables if not specified
        if limit is None:
            limit = settings.CONVERSATION_HISTORY_LIMIT
        if hours is None:
            hours = settings.CONVERSATION_HISTORY_HOURS
            
        try:
            cleaned_phone = clean_phone_number(phone_number)
            
            # Get messages from last N hours to maintain relevance
            time_threshold = datetime.utcnow() - timedelta(hours=hours)
            
            conversations = list(db.conversations.find({
                "phone_number": cleaned_phone,
                "timestamp": {"$gte": time_threshold}
            }).sort("timestamp", -1).limit(limit))
            
            if not conversations:
                return {
                    "summary": "No recent conversation history.",
                    "messages": [],
                    "last_order_mentioned": None,
                    "pending_items": []
                }
            
            # Build structured history
            messages = []
            last_order_mentioned = None
            pending_items = []
            
            for conv in reversed(conversations):
                msg_data = {
                    "role": conv["role"],
                    "message": conv["message"],
                    # Use ISO 8601 format for international standard
                    "timestamp": conv["timestamp"].isoformat() + "Z",
                    # Also include human-readable format
                    "timestamp_readable": conv["timestamp"].strftime("%Y-%m-%d %H:%M:%S UTC")
                }
                messages.append(msg_data)
                
                # Extract context from messages
                if conv["role"] == "user" and conv.get("message"):
                    # Check for order-related keywords
                    message_text = conv["message"]
                    if message_text:  # Ensure message is not None
                        lower_msg = message_text.lower()
                        if any(word in lower_msg for word in ["add", "order", "want", "pizza", "burger"]):
                            last_order_mentioned = message_text

                        # Check for pending actions
                        if "yes" in lower_msg or "confirm" in lower_msg:
                            pending_items.append("user_confirmed_something")
            
            # Create conversation summary
            summary = ConversationService._create_summary(messages)
            
            return {
                "summary": summary,
                "messages": messages,
                "last_order_mentioned": last_order_mentioned,
                "pending_items": pending_items,
                "message_count": len(messages)
            }
            
        except Exception as e:
            print(f"Error retrieving conversation history: {e}")
            return {
                "summary": "Error loading history.",
                "messages": [],
                "last_order_mentioned": None,
                "pending_items": []
            }
    
    @staticmethod
    def _create_summary(messages: List[Dict]) -> str:
        """Create a brief summary of the conversation"""
        if not messages:
            return "No previous conversation."
        
        # Summarize key points
        user_messages = [m for m in messages if m["role"] == "user"]
        
        if len(user_messages) == 0:
            return "No user messages in history."
        elif len(user_messages) == 1:
            return f"User previously said: {user_messages[-1]['message'][:100]}"
        else:
            return f"Ongoing conversation ({len(messages)} messages). Last user message: {user_messages[-1]['message'][:100]}"
    
    @staticmethod
    def get_formatted_history(phone_number: str, limit: int = 10) -> str:
        """Get formatted conversation history for agent context"""
        history_data = ConversationService.get_conversation_history(phone_number, limit)
        
        if not history_data["messages"]:
            return "No recent conversation history."
        
        # Format for agent consumption - SHOW ALL MESSAGES
        formatted = "RECENT CONVERSATION:\n"
        
        # Show ALL messages with full timestamp information
        for msg in history_data["messages"]:
            role = "Customer" if msg["role"] == "user" else "Assistant"
            # Use the readable timestamp format for agent context
            formatted += f"[{msg['timestamp_readable']}] {role}: {msg['message']}\n"
        
        if history_data["last_order_mentioned"]:
            formatted += f"\nLAST ORDER INTENT: {history_data['last_order_mentioned']}\n"
        
        return formatted
    
    
    @staticmethod
    def clear_old_conversations(phone_number: str, days: int = None):
        """Clear conversations older than N days"""
        if days is None:
            days = settings.OLD_CONVERSATION_CLEANUP_DAYS
        try:
            cleaned_phone = clean_phone_number(phone_number)
            threshold = datetime.utcnow() - timedelta(days=days)
            
            result = db.conversations.delete_many({
                "phone_number": cleaned_phone,
                "timestamp": {"$lt": threshold}
            })
            
            if result.deleted_count > 0:
                print(f"Cleared {result.deleted_count} old conversations for {cleaned_phone}")
                
        except Exception as e:
            print(f"Error clearing old conversations: {e}")