from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserModel:
    """User model for database operations"""
    def __init__(self, data: Dict):
        self.id = str(data.get('_id', ''))
        self.phone_number = data.get('phone_number', '')
        self.email = data.get('email', '')
        self.name = data.get('name', '')
        self.password_hash = data.get('password_hash', '')
        self.address = data.get('address', '')
        self.city = data.get('city', '')
        self.postal_code = data.get('postal_code', '')
        self.is_active = data.get('is_active', True)
        self.is_verified = data.get('is_verified', False)
        self.role = data.get('role', 'customer')  # customer, admin, staff
        self.created_at = data.get('created_at', datetime.utcnow())
        self.updated_at = data.get('updated_at', datetime.utcnow())

    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage"""
        return {
            'phone_number': self.phone_number,
            'email': self.email,
            'name': self.name,
            'password_hash': self.password_hash,
            'address': self.address,
            'city': self.city,
            'postal_code': self.postal_code,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'role': self.role,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def to_response_dict(self) -> Dict:
        """Convert to dictionary for API response (without sensitive data)"""
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'email': self.email,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'postal_code': self.postal_code,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'role': self.role,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
