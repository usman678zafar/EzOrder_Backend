from agents import function_tool
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get a fresh database connection"""
    try:
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            print("❌ MONGO_URI not found in environment variables")
            from config.database import db
            return db
        
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        
        client.admin.command('ping')
        return client['restaurant_db']
        
    except Exception as e:
        print(f"❌ Error creating database connection: {e}")
        try:
            from config.database import db
            return db
        except:
            return None

def show_menu_base(category: str = "all") -> str:
    """Base function that shows restaurant menu with proper WhatsApp formatting and spacing"""
    try:
        database = get_db_connection()
        if database is None:
            print("❌ Could not establish database connection")
            return "🍽️ I'm having trouble accessing the menu. Please try again in a moment."
        
        menu_collection = database.menu if hasattr(database, 'menu') else database['menu']
        
        total_count = menu_collection.count_documents({})
        print(f"📊 Total menu items found: {total_count}")
        
        query = {}
        if category and category.lower() != "all":
            query = {"category": {"$regex": f"^{category}$", "$options": "i"}}
        
        cursor = menu_collection.find(query)
        items = list(cursor.sort([("category", 1), ("id", 1)]))
        
        print(f"📋 Retrieved {len(items)} items from menu")
        
        if not items:
            if total_count > 0:
                print(f"⚠️ Query returned no items but {total_count} exist in collection")
                items = list(menu_collection.find({}).sort([("category", 1), ("id", 1)]))
                print(f"📋 Retry without query: {len(items)} items")
            
            if not items:
                print("❌ No menu items found in database")
                try:
                    from models.menu import MenuService
                    print("📝 Attempting to initialize menu...")
                    MenuService.initialize_menu(menu_collection)
                    items = list(menu_collection.find(query).sort([("category", 1), ("id", 1)]))
                    if items:
                        print(f"✅ Menu initialized with {len(items)} items")
                except Exception as init_error:
                    print(f"❌ Failed to initialize menu: {init_error}")
                
                if not items:
                    return "🍽️ Menu is being prepared. Please try again in a moment or contact support."
        
        menu_text = "🍽️ *RESTAURANT MENU* 🍽️\n"
        menu_text += "━━━━━━━━━━━━━━━━━━\n\n"
        
        current_category = ""
        for item in items:
            item_id = item.get('id', 'N/A')
            item_name = item.get('name', 'Unknown Item')
            item_price = item.get('price', 0)
            item_category = item.get('category', 'Other')
            item_description = item.get('description', 'No description')
            
            if item_category != current_category:
                current_category = item_category
                menu_text += f"*{current_category.upper()}*\n\n"
            
            menu_text += f"*{item_id}.* {item_name} - *PKR {item_price:.2f}*\n"
            menu_text += f"     _{item_description}_\n\n"
        
        menu_text += "━━━━━━━━━━━━━━━━━━\n\n"
        menu_text += "*HOW TO ORDER:*\n\n"
        menu_text += "• Send *'add 1'* to add item #1\n"
        menu_text += "• Send *'add 1 and 3'* for multiple\n"
        menu_text += "• Send *'view order'* to see cart\n"
        menu_text += "• Send *'confirm'* when ready\n"
        
        print(f"✅ Menu generated successfully with {len(items)} items")
        return menu_text
        
    except Exception as e:
        print(f"❌ Error in show_menu: {str(e)}")
        import traceback
        traceback.print_exc()
        return "🍽️ I'm having trouble loading the menu right now. Please try typing *'menu'* again or contact support if the issue persists."

def test_menu_connection_base() -> str:
    """Base function to test if menu can be accessed properly"""
    try:
        database = get_db_connection()
        if database is None:
            return "❌ Database connection failed"
        
        menu_collection = database.menu if hasattr(database, 'menu') else database['menu']
        count = menu_collection.count_documents({})
        
        if count > 0:
            sample = menu_collection.find_one()
            return f"✅ Menu connection OK - {count} items found. Sample: {sample.get('name', 'Unknown')}"
        else:
            return "⚠️ Menu is empty"
            
    except Exception as e:
        return f"❌ Error testing menu: {str(e)}"

# Decorated versions for agent use
@function_tool
def show_menu(category: str = "all") -> str:
    """Shows restaurant menu with proper WhatsApp formatting and spacing"""
    return show_menu_base(category)

@function_tool
def test_menu_connection() -> str:
    """Test if menu can be accessed properly"""
    return test_menu_connection_base()
