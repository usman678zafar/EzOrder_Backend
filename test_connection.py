#!/usr/bin/env python3
"""
Test MongoDB connection script
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_atlas_connection():
    """Test MongoDB Atlas connection"""
    atlas_uri = "mongodb+srv://chatbot_user:chatbot_password@cluster0.mzyzruz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    
    print("Testing MongoDB Atlas connection...")
    print(f"URI: {atlas_uri}")
    
    try:
        client = MongoClient(
            atlas_uri,
            serverSelectionTimeoutMS=10000,  # 10 seconds timeout
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
        )
        
        # Test the connection
        client.admin.command('ping')
        print("[SUCCESS] Atlas connection successful!")
        
        # List databases
        dbs = client.list_database_names()
        print(f"Available databases: {dbs}")
        
        client.close()
        return True
        
    except (ConnectionFailure, ConfigurationError) as e:
        print(f"[ERROR] Atlas connection failed: {e}")
        return False

def test_local_connection():
    """Test local MongoDB connection"""
    local_uri = "mongodb://localhost:27017/restaurant_db"
    
    print("\nTesting local MongoDB connection...")
    print(f"URI: {local_uri}")
    
    try:
        client = MongoClient(
            local_uri,
            serverSelectionTimeoutMS=5000,  # 5 seconds timeout
            connectTimeoutMS=5000,
        )
        
        # Test the connection
        client.admin.command('ping')
        print("[SUCCESS] Local connection successful!")
        
        # List databases
        dbs = client.list_database_names()
        print(f"Available databases: {dbs}")
        
        client.close()
        return True
        
    except (ConnectionFailure, ConfigurationError) as e:
        print(f"[ERROR] Local connection failed: {e}")
        return False

def main():
    print("MongoDB Connection Test")
    print("=" * 50)
    
    # Test Atlas connection
    atlas_success = test_atlas_connection()
    
    # Test local connection
    local_success = test_local_connection()
    
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"Atlas connection: {'[SUCCESS] Working' if atlas_success else '[ERROR] Failed'}")
    print(f"Local connection: {'[SUCCESS] Working' if local_success else '[ERROR] Failed'}")
    
    if not atlas_success and not local_success:
        print("\n🔧 Recommendations:")
        print("1. Install MongoDB locally: https://www.mongodb.com/try/download/community")
        print("2. Or install Docker and run: docker run -d -p 27017:27017 mongo:latest")
        print("3. Or check your internet connection for Atlas access")

if __name__ == "__main__":
    main()
