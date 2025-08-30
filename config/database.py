from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
from .settings import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        try:
            # Add connection timeout and server selection timeout
            self.client = MongoClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,  # 5 seconds timeout
                connectTimeoutMS=5000,  # 5 seconds connection timeout
                socketTimeoutMS=5000,   # 5 seconds socket timeout
            )
            
            # Test the connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            self.db = self.client['restaurant_db']
            self.users = self.db['users']
            self.orders = self.db['orders']
            self.menu = self.db['menu']
            self.conversations = self.db['conversations']
            self.user_states = self.db['user_states']
            self.notifications = self.db['notifications']  # Add this line
        
        except (ConnectionFailure, ConfigurationError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            print(f"MongoDB connection failed: {e}")
            print("Please check your MONGO_URI in the .env file and ensure MongoDB is running.")
            raise

# Initialize database connection
try:
    db = Database()
except Exception as e:
    print(f"Failed to initialize database: {e}")
    print("The application will not work without a database connection.")
    db = None
