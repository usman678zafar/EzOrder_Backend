from typing import Optional, Dict
from datetime import datetime, timedelta
from bson import ObjectId
from config.database import db
from config.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from models.user import UserModel
from api.schemas.auth import UserRegister, UserUpdate

class AuthService:
    def __init__(self):
        self.collection = db.users
    
    async def register_user(self, user_data: UserRegister) -> Optional[Dict]:
        """Register a new user"""
        # Check if user already exists
        existing_user = self.collection.find_one({
            "$or": [
                {"email": user_data.email},
                {"phone_number": user_data.phone_number}
            ]
        })
        
        if existing_user:
            if existing_user.get('email') == user_data.email:
                raise ValueError("Email already registered")
            else:
                raise ValueError("Phone number already registered")
        
        # Create user document
        user_doc = {
            "email": user_data.email,
            "password_hash": get_password_hash(user_data.password),
            "name": user_data.name,
            "phone_number": user_data.phone_number,
            "address": user_data.address,
            "city": user_data.city,
            "postal_code": user_data.postal_code,
            "is_active": True,
            "is_verified": False,  # You can add email verification later
            "role": "customer",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert user
        result = self.collection.insert_one(user_doc)
        
        if result.inserted_id:
            user_doc['_id'] = result.inserted_id
            user = UserModel(user_doc)
            return user.to_response_dict()
        
        return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserModel]:
        """Authenticate user by email and password"""
        user_doc = self.collection.find_one({"email": email})
        
        if not user_doc:
            return None
        
        if not verify_password(password, user_doc.get('password_hash', '')):
            return None
        
        if not user_doc.get('is_active', True):
            raise ValueError("Account is deactivated")
        
        return UserModel(user_doc)
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """Get user by ID"""
        try:
            user_doc = self.collection.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                return UserModel(user_doc)
        except:
            pass
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email"""
        user_doc = self.collection.find_one({"email": email})
        if user_doc:
            return UserModel(user_doc)
        return None
    
    async def update_user(self, user_id: str, update_data: UserUpdate) -> Optional[Dict]:
        """Update user profile"""
        try:
            # Build update document
            update_doc = {"updated_at": datetime.utcnow()}
            
            if update_data.name is not None:
                update_doc["name"] = update_data.name
            
            if update_data.phone_number is not None:
                # Check if phone number is already used
                existing = self.collection.find_one({
                    "phone_number": update_data.phone_number,
                    "_id": {"$ne": ObjectId(user_id)}
                })
                if existing:
                    raise ValueError("Phone number already in use")
                update_doc["phone_number"] = update_data.phone_number
            
            if update_data.address is not None:
                update_doc["address"] = update_data.address
            
            if update_data.city is not None:
                update_doc["city"] = update_data.city
            
            if update_data.postal_code is not None:
                update_doc["postal_code"] = update_data.postal_code
            
            # Update user
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_doc}
            )
            
            if result.modified_count > 0:
                user = await self.get_user_by_id(user_id)
                if user:
                    return user.to_response_dict()
            
        except Exception as e:
            raise e
        
        return None
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            
            # Verify current password
            if not verify_password(current_password, user.password_hash):
                raise ValueError("Current password is incorrect")
            
            # Update password
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password_hash": get_password_hash(new_password),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            raise e
    
    def create_tokens(self, user: UserModel) -> Dict:
        """Create access and refresh tokens for user"""
        # Token payload
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role
        }
        
        # Create tokens
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user.to_response_dict()
        }
