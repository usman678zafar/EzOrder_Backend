from datetime import datetime, timedelta
from typing import Dict, Optional
from config.database import db
from utils.phone_utils import clean_phone_number

class StateManager:
    """Manages user states and sessions"""
    
    @staticmethod
    def get_user_state(phone_number: str) -> Dict:
        """Get comprehensive user state"""
        cleaned_phone = clean_phone_number(phone_number)
        user = db.users.find_one({"phone_number": cleaned_phone})
        
        # Get last state from database
        state_doc = db.user_states.find_one({"phone_number": cleaned_phone})
        
        return {
            'is_registered': user is not None,
            'user_data': user,
            'last_state': state_doc.get('current_state', 'new') if state_doc else 'new',
            'last_interaction': datetime.utcnow()
        }
    
    @staticmethod
    def update_user_state(phone_number: str, state: str, additional_data: Dict = None):
        """Update user state in database"""
        cleaned_phone = clean_phone_number(phone_number)
        
        update_doc = {
            "phone_number": cleaned_phone,
            "current_state": state,
            "last_updated": datetime.utcnow()
        }
        
        if additional_data:
            update_doc.update(additional_data)
        
        db.user_states.update_one(
            {"phone_number": cleaned_phone},
            {"$set": update_doc},
            upsert=True
        )
