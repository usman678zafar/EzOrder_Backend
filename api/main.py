from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import menu, order, auth  # Add auth import

app = FastAPI(
    title="Restaurant Menu & Order API",
    description="""
    API for managing restaurant menu items and orders with authentication.
    
    ## Authentication
    Most endpoints require authentication. To authenticate:
    1. Register a new account at `/api/v1/auth/register`
    2. Login at `/api/v1/auth/login` to get access tokens
    3. Include the access token in the Authorization header: `Bearer <token>`
    
    ## Roles
    - **Customer**: Can view menu, view their own orders
    - **Staff**: Can manage menu items, view and update all orders
    - **Admin**: Full access to all endpoints
    
    ## Public Endpoints
    - GET `/api/v1/menu` - View menu items
    - GET `/api/v1/menu/{id}` - View specific menu item
    - GET `/api/v1/menu/categories` - View menu categories
    - POST `/api/v1/menu/search` - Search menu items
    """,
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(menu.router, prefix="/api/v1/menu", tags=["menu"])
app.include_router(order.router, prefix="/api/v1/orders", tags=["orders"])

@app.get("/")
async def root():
    return {
        "message": "Restaurant Menu & Order API",
        "version": "2.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "menu": "/api/v1/menu",
            "orders": "/api/v1/orders",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
