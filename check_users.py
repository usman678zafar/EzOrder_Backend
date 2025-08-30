#!/usr/bin/env python3
"""
Check and manage users in MongoDB
"""
from config.database import db
import json
from bson import ObjectId

def list_all_users():
    """List all users in the database"""
    users = list(db.users.find({}))
    print(f"=== TOTAL USERS: {len(users)} ===\n")
    
    for i, user in enumerate(users, 1):
        print(f"User {i}:")
        print(f"  ID: {user['_id']}")
        print(f"  Email: {user.get('email', 'N/A')}")
        print(f"  Name: {user.get('name', 'N/A')}")
        print(f"  Role: {user.get('role', 'N/A')}")
        print(f"  Phone: {user.get('phone_number', 'N/A')}")
        print(f"  Active: {user.get('is_active', user.get('active', 'N/A'))}")
        print(f"  Created: {user.get('created_at', 'N/A')}")
        print("-" * 50)

def update_user_role(user_id, new_role):
    """Update user role"""
    try:
        # Convert string ID to ObjectId if needed
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        result = db.users.update_one(
            {"_id": user_id},
            {"$set": {"role": new_role}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Successfully updated user role to '{new_role}'")
            return True
        else:
            print(f"❌ No user found with ID: {user_id}")
            return False
    except Exception as e:
        print(f"❌ Error updating user: {e}")
        return False

def make_user_admin(email_or_id):
    """Make a user admin by email or ID"""
    try:
        # Try to find by email first
        if "@" in email_or_id:
            user = db.users.find_one({"email": email_or_id})
        else:
            # Try to find by ID
            user = db.users.find_one({"_id": ObjectId(email_or_id)})
        
        if user:
            result = db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"role": "admin"}}
            )
            
            if result.modified_count > 0:
                print(f"✅ Successfully made user '{user.get('name', user.get('email', 'Unknown'))}' an admin!")
                return True
            else:
                print(f"❌ Failed to update user role")
                return False
        else:
            print(f"❌ No user found with email/ID: {email_or_id}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    list_all_users()
    
    print("\n" + "="*60)
    print("To make a user admin, you can use:")
    print("python check_users.py")
    print("Then call: make_user_admin('user@example.com') or make_user_admin('user_id')")
