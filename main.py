from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import menu, order, auth, webhooks
import multiprocessing
import uvicorn
import os
import sys
from dotenv import load_dotenv
from config.database import db
from models.menu import MenuService




# Load environment variables
load_dotenv()

app = FastAPI(
    title="Restaurant Menu & Order API",
    description="""
    API for managing restaurant menu items and orders with authentication.
    
    ## Authentication
    1. Register at `/api/v1/auth/register`
    2. Login at `/api/v1/auth/login`
    3. Use Bearer token for protected endpoints
    
    ## Roles
    - Customer: view menu, own orders
    - Staff: manage menu, view/update orders
    - Admin: full access
    """,
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(menu.router, prefix="/api/v1/menu", tags=["menu"])
app.include_router(order.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])

@app.get("/")
async def root():
    return {
        "message": "Restaurant Menu & Order API",
        "version": "2.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "menu": "/api/v1/menu",
            "orders": "/api/v1/orders",
            "webhooks": "/api/v1/webhooks",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def initialize_menu():
    """Initialize menu if it's empty"""
    try:
        # Check if menu collection has items
        menu_count = db.menu.count_documents({})
        print(f"📊 Current menu items in database: {menu_count}")
        
        if menu_count == 0:
            print("📋 Menu is empty. Initializing with default items...")
            MenuService.initialize_menu(db.menu)
            
            # Verify initialization
            new_count = db.menu.count_documents({})
            print(f"✅ Menu initialized successfully! Added {new_count} items")
        else:
            print(f"✅ Menu already has {menu_count} items")
            
    except Exception as e:
        print(f"❌ Error initializing menu: {e}")
        import traceback
        traceback.print_exc()

def run_api_server():
    """Run FastAPI server"""
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    print(f"\n🚀 Starting API server on {host}:{port}")
    print(f"📚 Documentation: http://localhost:{port}/docs")
    
    # Initialize menu before starting server
    initialize_menu()
    
    # Run without reload in production mode
    uvicorn.run(
        "main:app",  # Use string import to avoid issues
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

def run_whatsapp_bot():
    """Run WhatsApp bot in a separate process"""
    # Set up the path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        print("\n🤖 Starting WhatsApp Bot...")
        
        # Initialize menu for WhatsApp bot process too (since it's a separate process)
        initialize_menu()
        
        from handlers.whatsapp_handler import WhatsAppHandler
        from config.settings import settings
        
        handler = WhatsAppHandler(
            instance_id=settings.WHATSAPP_INSTANCE_ID,
            token=settings.WHATSAPP_TOKEN
        )
        
        # Run the bot
        handler.run()
        
    except Exception as e:
        print(f"❌ Error starting WhatsApp bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("🍕 EZ Order - Restaurant Ordering System")
    print("=" * 60)
    print("\nStarting both API server and WhatsApp bot...\n")
    
    # Create separate processes for each service
    api_process = multiprocessing.Process(target=run_api_server, name="API-Server")
    bot_process = multiprocessing.Process(target=run_whatsapp_bot, name="WhatsApp-Bot")
    
    # Start both processes
    api_process.start()
    bot_process.start()
    
    print("\n✅ Both services are starting...")
    print("\n📌 Services running:")
    print("    - API Server: http://localhost:8000")
    print("    - API Docs: http://localhost:8000/docs")
    print("    - WhatsApp Bot: Active and listening for messages")
    print("\n⚠  Press Ctrl+C to stop both services\n")
    
    try:
        # Wait for both processes
        api_process.join()
        bot_process.join()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        
        # Terminate processes gracefully
        api_process.terminate()
        bot_process.terminate()
        
        # Wait for processes to finish
        api_process.join(timeout=5)
        bot_process.join(timeout=5)
        
        # Force kill if still running
        if api_process.is_alive():
            api_process.kill()
        if bot_process.is_alive():
            bot_process.kill()
        
        print("👋 Goodbye!")
        sys.exit(0)
