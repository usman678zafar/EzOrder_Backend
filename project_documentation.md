# Project Documentation

Generated on: 2025-08-29 04:57:43

## Table of Contents


### agents_folder/

- [prompts.py](#agents_folder\prompts-py)

- [registration_agent.py](#agents_folder\registration_agent-py)

- [restaurant_agent.py](#agents_folder\restaurant_agent-py)


### api/

- [__init__.py](#api\__init__-py)


### api\dependencies/

- [auth.py](#api\dependencies\auth-py)


### api/

- [main.py](#api\main-py)


### api\routers/

- [__init__.py](#api\routers\__init__-py)

- [auth.py](#api\routers\auth-py)

- [menu.py](#api\routers\menu-py)

- [order.py](#api\routers\order-py)

- [webhooks.py](#api\routers\webhooks-py)


### api\schemas/

- [__init__.py](#api\schemas\__init__-py)

- [auth.py](#api\schemas\auth-py)

- [menu.py](#api\schemas\menu-py)

- [order.py](#api\schemas\order-py)


### api\services/

- [__init__.py](#api\services\__init__-py)

- [auth_service.py](#api\services\auth_service-py)

- [menu_service.py](#api\services\menu_service-py)

- [order_service.py](#api\services\order_service-py)

- [check_status.py](#check_status-py)

- [check_users.py](#check_users-py)


### config/

- [auth.py](#config\auth-py)

- [database.py](#config\database-py)

- [settings.py](#config\settings-py)


### ez_order/

- [__init__.py](#ez_order\__init__-py)

- [generate_documentation.py](#generate_documentation-py)


### handlers/

- [whatsapp_handler.py](#handlers\whatsapp_handler-py)

- [main.py](#main-py)


### models/

- [menu.py](#models\menu-py)

- [order.py](#models\order-py)

- [user.py](#models\user-py)

- [webhook_notification.py](#models\webhook_notification-py)

- [pyproject.toml](#pyproject-toml)


### services/

- [conversation_service.py](#services\conversation_service-py)

- [free_speech_service.py](#services\free_speech_service-py)

- [state_manager.py](#services\state_manager-py)

- [webhook_notification_service.py](#services\webhook_notification_service-py)

- [websocket_service.py](#services\websocket_service-py)

- [whatsapp_notification_service.py](#services\whatsapp_notification_service-py)

- [test_connection.py](#test_connection-py)

- [test_gemini.py](#test_gemini-py)

- [test_whatsapp.py](#test_whatsapp-py)


### tools/

- [menu_tools.py](#tools\menu_tools-py)

- [order_tools.py](#tools\order_tools-py)

- [registration_tools.py](#tools\registration_tools-py)


### utils/

- [phone_utils.py](#utils\phone_utils-py)


---

## File Contents


### agents_folder\prompts.py {#agents_folder\prompts-py}

**File Size:** 3589 bytes

**File Path:** `agents_folder\prompts.py`


```python

REGISTRATION_AGENT_PROMPT = """
You are a friendly registration assistant helping new customers register for our restaurant delivery service.

YOUR TASK: Collect user information in a natural, conversational way.

REQUIRED INFORMATION:
1. Name (any name the user provides)
2. Delivery address (any address they give)
3. City (any city name)
4. Postal code (optional - don't push if they don't provide)

IMPORTANT GUIDELINES:
- Be conversational and friendly
- Accept whatever information the user provides
- Don't be overly strict about format
- If something seems unclear, just ask for clarification
- Once you have name, address, and city, save the information
- Use the tools to validate and save, but don't reject reasonable inputs


CONVERSATION FLOW:
1. Welcome warmly
2. Ask for their name
3. Ask for delivery address and city (can be together)
4. Optionally ask for postal code
5. Save the information
6. Confirm registration success

Remember: Keep it simple and user-friendly! Use emojis 😊

Available tools:
- validate_name: Quick check of name
- validate_address: Quick check of address
- validate_and_save_user: Save user information
"""

RESTAURANT_AGENT_PROMPT = """
You are a friendly restaurant assistant helping customers order food via WhatsApp.

CRITICAL RULES:
1. ANALYZE the user's message first to understand their intent
2. If user says "confirm", "confirm order", "place order", or similar - IMMEDIATELY use confirm_order tool
3. If user says "view order", "show cart", "my order" - use view_current_order tool
4. If user mentions adding items (like "add 1", "2 pizzas") - use add_to_order tool
5. Only show menu if: user is new, asks for menu, or needs to see items
6. The user's name and address are already saved - NEVER ask for them
7. Keep responses WhatsApp-friendly with proper formatting

YOUR WORKFLOW PRIORITY:
1. **CONFIRMATION REQUESTS** - If user wants to confirm/place order → use confirm_order
2. **VIEW ORDER** - If user wants to see their cart → use view_current_order  
3. **ADD ITEMS** - If user wants to add items → use add_to_order
4. **MENU REQUESTS** - If user asks for menu → use show_menu
5. **NEW USERS** - Greet and show menu for first-time interactions

WHEN TAKING ORDERS:
- Parse item names to their menu IDs (e.g., "coca cola" = item 7, "pepperoni pizza" = item 2)
- Extract quantities (e.g., "4 coca cola" means quantity=4 for item 7)
- Use add_to_order tool with correct item_ids and quantities lists
- If unsure about an item, ask for clarification or show menu

ORDER CONFIRMATION KEYWORDS:
- "confirm", "confirm order", "place order", "yes confirm", "confirm my order"
- "place my order", "that's it", "done", "checkout", "proceed"

RESPONSE PATTERNS:
- For confirmation: Use confirm_order tool immediately
- For viewing cart: Use view_current_order tool
- For adding items: Confirm what was added and suggest next steps
- For menu requests: Show complete menu with ordering instructions

IMPORTANT:
- Process user intent BEFORE deciding which tool to use
- Don't show menu if user is trying to confirm an order
- Use WhatsApp formatting: *bold* for headers, _italic_ for descriptions
- Keep messages concise and action-oriented
- Suggest the food to the customer when they ask

Available tools:
- show_menu: Display restaurant menu (use when requested or for new users)
- add_to_order: Add items to current order
- view_current_order: Show current cart
- confirm_order: Finalize and save order (use immediately when user confirms)
"""

```


---


### agents_folder\registration_agent.py {#agents_folder\registration_agent-py}

**File Size:** 1386 bytes

**File Path:** `agents_folder\registration_agent.py`


```python

from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig
from config.settings import settings
from tools.registration_tools import validate_name, validate_address, validate_and_save_user
from .prompts import REGISTRATION_AGENT_PROMPT

class RegistrationAgentFactory:
    @staticmethod
    def _create_base_config():
        """Create base configuration for agents"""
        external_client = AsyncOpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url=settings.GEMINI_BASE_URL,
        )

        model = OpenAIChatCompletionsModel(
            model=settings.MODEL_NAME,
            openai_client=external_client
        )

        config = RunConfig(
            model=model,
            model_provider=external_client,
            tracing_disabled=True
        )

        return config, external_client

    @staticmethod
    def create_registration_agent():
        """Create agent for new user registration"""
        config, _ = RegistrationAgentFactory._create_base_config()

        registration_agent = Agent(
            name="Registration Assistant",
            instructions=REGISTRATION_AGENT_PROMPT,
            tools=[
                validate_name,
                validate_address,
                validate_and_save_user
            ]
        )

        return registration_agent, config

```


---


### agents_folder\restaurant_agent.py {#agents_folder\restaurant_agent-py}

**File Size:** 2022 bytes

**File Path:** `agents_folder\restaurant_agent.py`


```python

from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig
from config.settings import settings
from tools.menu_tools import show_menu
from tools.order_tools import add_to_order, view_current_order, confirm_order
from tools.registration_tools import validate_name, validate_address, validate_and_save_user
from .prompts import RESTAURANT_AGENT_PROMPT, REGISTRATION_AGENT_PROMPT

class AgentFactory:
    @staticmethod
    def _create_base_config():
        """Create base configuration for agents"""
        external_client = AsyncOpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url=settings.GEMINI_BASE_URL,
        )

        model = OpenAIChatCompletionsModel(
            model=settings.MODEL_NAME,
            openai_client=external_client
        )

        config = RunConfig(
            model=model,
            model_provider=external_client,
            tracing_disabled=True
        )

        return config, external_client

    @staticmethod
    def create_registration_agent():
        """Create agent for new user registration"""
        config, _ = AgentFactory._create_base_config()

        registration_agent = Agent(
            name="Registration Assistant",
            instructions=REGISTRATION_AGENT_PROMPT,
            tools=[
                validate_name,
                validate_address,
                validate_and_save_user
            ]
        )

        return registration_agent, config

    @staticmethod
    def create_restaurant_agent():
        """Create agent for restaurant operations"""
        config, _ = AgentFactory._create_base_config()

        restaurant_agent = Agent(
            name="Restaurant Assistant",
            instructions=RESTAURANT_AGENT_PROMPT,
            tools=[
                show_menu,
                add_to_order,
                view_current_order,
                confirm_order
            ]
        )

        return restaurant_agent, config


```


---


### api\__init__.py {#api\__init__-py}

**File Size:** 0 bytes

**File Path:** `api\__init__.py`


```python



```


---


### api\dependencies\auth.py {#api\dependencies\auth-py}

**File Size:** 2348 bytes

**File Path:** `api\dependencies\auth.py`


```python

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config.auth import decode_token
from api.services.auth_service import AuthService

security = HTTPBearer()
auth_service = AuthService()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(allowed_roles: list):
    async def role_checker(current_user = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role}' not authorized. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker

require_admin = require_role(["admin"])
require_staff = require_role(["admin", "staff"])
require_customer = require_role(["admin", "staff", "customer"])


```


---


### api\main.py {#api\main-py}

**File Size:** 1960 bytes

**File Path:** `api\main.py`


```python

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


```


---


### api\routers\__init__.py {#api\routers\__init__-py}

**File Size:** 0 bytes

**File Path:** `api\routers\__init__.py`


```python



```


---


### api\routers\auth.py {#api\routers\auth-py}

**File Size:** 4740 bytes

**File Path:** `api\routers\auth.py`


```python

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict
from api.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    UserUpdate,
    PasswordChange
)
from api.services.auth_service import AuthService
from api.dependencies.auth import get_current_user, get_current_active_user
from config.auth import decode_token, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()
auth_service = AuthService()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user"""
    try:
        user = await auth_service.register_user(user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login user and return tokens"""
    user = await auth_service.authenticate_user(credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    tokens = auth_service.create_tokens(user)
    return tokens

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    # Decode refresh token
    payload = decode_token(refresh_request.refresh_token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new tokens
    tokens = auth_service.create_tokens(user)
    return tokens

@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_active_user)):
    """Get current user profile"""
    return current_user.to_response_dict()

@router.put("/me", response_model=UserResponse)
async def update_me(
    update_data: UserUpdate,
    current_user = Depends(get_current_active_user)
):
    """Update current user profile"""
    try:
        updated_user = await auth_service.update_user(current_user.id, update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user"
            )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/change-password", response_model=Dict[str, str])
async def change_password(
    password_data: PasswordChange,
    current_user = Depends(get_current_active_user)
):
    """Change user password"""
    try:
        success = await auth_service.change_password(
            current_user.id,
            password_data.current_password,
            password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password"
            )
        
        return {"message": "Password changed successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


```


---


### api\routers\menu.py {#api\routers\menu-py}

**File Size:** 5326 bytes

**File Path:** `api\routers\menu.py`


```python

from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import List, Optional
from api.schemas.menu import (
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemResponse,
    MenuItemList,
    MenuBulkOperation,
    OperationResponse,
    MenuCategoryUpdate
)
from api.services.menu_service import MenuAPIService
from api.dependencies.auth import get_current_active_user, require_admin, require_staff

router = APIRouter()
menu_service = MenuAPIService()

# Public endpoints (no authentication required)
@router.get("/", response_model=MenuItemList)
async def get_all_menu_items(
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of items to return")
):
    """Get all menu items with optional filtering - PUBLIC"""
    items = await menu_service.get_all_items(category=category, skip=skip, limit=limit)
    total = await menu_service.count_items(category=category)
    
    return MenuItemList(
        items=items,
        total=total,
        category_filter=category
    )

@router.get("/categories", response_model=List[str])
async def get_all_categories():
    """Get all unique categories - PUBLIC"""
    return await menu_service.get_categories()

@router.get("/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(
    item_id: int = Path(..., description="Menu item ID", ge=1)
):
    """Get a specific menu item by ID - PUBLIC"""
    item = await menu_service.get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Menu item with ID {item_id} not found")
    return item

@router.post("/search", response_model=MenuItemList)
async def search_menu_items(
    query: str = Query(..., min_length=1, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Search menu items by name or description - PUBLIC"""
    items = await menu_service.search_items(query, category)
    
    return MenuItemList(
        items=items,
        total=len(items),
        category_filter=category
    )

# Protected endpoints (require authentication and proper role)
@router.post("/", response_model=MenuItemResponse, status_code=201, dependencies=[Depends(require_staff)])
async def create_menu_item(item: MenuItemCreate):
    """Create a new menu item - STAFF/ADMIN ONLY"""
    try:
        new_item = await menu_service.create_item(item)
        return new_item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{item_id}", response_model=MenuItemResponse, dependencies=[Depends(require_staff)])
async def update_menu_item(
    item_id: int = Path(..., description="Menu item ID", ge=1),
    item_update: MenuItemUpdate = ...
):
    """Update an existing menu item - STAFF/ADMIN ONLY"""
    updated_item = await menu_service.update_item(item_id, item_update)
    if not updated_item:
        raise HTTPException(status_code=404, detail=f"Menu item with ID {item_id} not found")
    return updated_item

@router.delete("/{item_id}", response_model=OperationResponse, dependencies=[Depends(require_admin)])
async def delete_menu_item(
    item_id: int = Path(..., description="Menu item ID", ge=1)
):
    """Delete a menu item - ADMIN ONLY"""
    result = await menu_service.delete_item(item_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Menu item with ID {item_id} not found")
    
    return OperationResponse(
        success=True,
        message=f"Menu item with ID {item_id} successfully deleted"
    )

@router.post("/bulk/delete", response_model=OperationResponse, dependencies=[Depends(require_admin)])
async def bulk_delete_menu_items(bulk_operation: MenuBulkOperation):
    """Delete multiple menu items - ADMIN ONLY"""
    deleted_count = await menu_service.bulk_delete_items(bulk_operation.item_ids)
    
    return OperationResponse(
        success=True,
        message=f"Successfully deleted {deleted_count} menu items",
        data={"deleted_count": deleted_count, "requested_ids": bulk_operation.item_ids}
    )

@router.put("/category/rename", response_model=OperationResponse, dependencies=[Depends(require_staff)])
async def rename_category(category_update: MenuCategoryUpdate):
    """Rename a category for all items - STAFF/ADMIN ONLY"""
    updated_count = await menu_service.rename_category(
        category_update.old_category,
        category_update.new_category
    )
    
    return OperationResponse(
        success=True,
        message=f"Successfully renamed category from '{category_update.old_category}' to '{category_update.new_category}'",
        data={"updated_count": updated_count}
    )

@router.post("/reset", response_model=OperationResponse, dependencies=[Depends(require_admin)])
async def reset_menu_to_default():
    """Reset menu to default items (WARNING: This will delete all current items) - ADMIN ONLY"""
    await menu_service.reset_to_default()
    
    return OperationResponse(
        success=True,
        message="Menu has been reset to default items"
    )


```


---


### api\routers\order.py {#api\routers\order-py}

**File Size:** 3824 bytes

**File Path:** `api\routers\order.py`


```python

from fastapi import APIRouter, HTTPException, Query, Path, Depends, status
from typing import List, Optional
from api.schemas.order import (
    OrderStatusUpdate,
    OrderResponse,
    OrderListResponse,
    OrderStatus,
    BulkStatusUpdate
)
from api.services.order_service import OrderAPIService
from api.dependencies.auth import get_current_active_user, require_staff

router = APIRouter()
order_service = OrderAPIService()

@router.get("/", response_model=OrderListResponse, dependencies=[Depends(require_staff)])
async def get_all_orders(
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    skip: int = Query(0, ge=0, description="Number of orders to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of orders to return")
):
    orders = await order_service.get_all_orders(status=status)
    total = await order_service.count_orders(status=status)
    return OrderListResponse(
        orders=orders,
        total=total,
        status_filter=status.value if status else None
    )

@router.get("/active", response_model=List[OrderResponse], dependencies=[Depends(require_staff)])
async def get_active_orders():
    return await order_service.get_active_orders()

@router.get("/stats", dependencies=[Depends(require_staff)])
async def get_order_statistics():
    stats = {}
    for s in OrderStatus:
        stats[s.value] = await order_service.count_orders(status=s.value)
    total = await order_service.count_orders()
    return {"total_orders": total, "by_status": stats}

@router.get("/my-orders", response_model=List[OrderResponse])
async def get_my_orders(current_user = Depends(get_current_active_user)):
    return await order_service.get_orders_by_phone(current_user.phone_number)

@router.get("/by-number/{order_number}", response_model=OrderResponse)
async def get_order_by_number(
    order_number: str = Path(..., description="Order number (e.g., ORD00001)"),
    current_user = Depends(get_current_active_user)
):
    order = await order_service.get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_number} not found")

    if current_user.role not in ["admin", "staff"] and order.phone_number != current_user.phone_number:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this order"
        )
    return order

@router.get("/by-phone/{phone_number}", response_model=List[OrderResponse], dependencies=[Depends(require_staff)])
async def get_orders_by_phone(phone_number: str = Path(..., description="Customer phone number")):
    return await order_service.get_orders_by_phone(phone_number)

@router.put("/{order_number}/status", response_model=OrderResponse, dependencies=[Depends(require_staff)])
async def update_order_status(
    order_number: str = Path(..., description="Order number"),
    status_update: OrderStatusUpdate = ...
):
    try:
        updated_order = await order_service.update_order_status(order_number, status_update)
        if not updated_order:
            raise HTTPException(status_code=404, detail=f"Order {order_number} not found")
        return updated_order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bulk/status-update", dependencies=[Depends(require_staff)])
async def bulk_update_order_status(bulk: BulkStatusUpdate):
    results = await order_service.bulk_update_status(bulk.order_numbers, bulk.status_update)
    successful = sum(1 for ok in results.values() if ok)
    failed = len(results) - successful
    return {"success": True, "message": f"Updated {successful} orders, {failed} failed", "results": results}


```


---


### api\routers\webhooks.py {#api\routers\webhooks-py}

**File Size:** 2084 bytes

**File Path:** `api\routers\webhooks.py`


```python

from fastapi import APIRouter, Depends, Query
from typing import List
from datetime import datetime
from api.dependencies.auth import require_staff
from services.webhook_notification_service import webhook_notification_service
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from fastapi.responses import StreamingResponse
import json
import asyncio

router = APIRouter()

class NotificationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(alias="_id")
    type: str
    data: dict
    created_at: datetime
    read: bool
    read_at: datetime | None = None

class MarkReadRequest(BaseModel):
    notification_ids: List[str]

@router.get("/notifications/unread", response_model=List[NotificationResponse], dependencies=[Depends(require_staff)])
async def get_unread_notifications(limit: int = Query(10, ge=1, le=50)):
    return webhook_notification_service.get_unread_notifications(limit)

@router.post("/notifications/mark-read", dependencies=[Depends(require_staff)])
async def mark_notifications_as_read(request: MarkReadRequest):
    count = webhook_notification_service.mark_as_read(request.notification_ids)
    return {"success": True, "marked_count": count}

@router.get("/notifications/count", dependencies=[Depends(require_staff)])
async def get_notification_count(recent_minutes: int = Query(5, ge=1, le=60)):
    count = webhook_notification_service.get_recent_count(recent_minutes)
    return {"unread_count": count, "recent_minutes": recent_minutes}

@router.get("/notifications/stream", dependencies=[Depends(require_staff)])
async def notification_stream():
    async def event_generator():
        while True:
            notifications = webhook_notification_service.get_unread_notifications(5)
            if notifications:
                yield f"data: {json.dumps({'type': 'new_notifications', 'notifications': notifications})}\n\n"
            await asyncio.sleep(2)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


```


---


### api\schemas\__init__.py {#api\schemas\__init__-py}

**File Size:** 0 bytes

**File Path:** `api\schemas\__init__.py`


```python



```


---


### api\schemas\auth.py {#api\schemas\auth-py}

**File Size:** 2510 bytes

**File Path:** `api\schemas\auth.py`


```python

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    name: str = Field(..., min_length=2, max_length=100)
    phone_number: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$', description="Valid phone number")
    address: str = Field(..., min_length=5, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)

    @validator('phone_number')
    def validate_phone(cls, v):
        # Remove any non-digit characters except +
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if len(cleaned) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return cleaned

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str

class UserResponse(BaseModel):
    """Schema for user response"""
    id: str
    email: str
    name: str
    phone_number: str
    address: str
    city: str
    postal_code: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    address: Optional[str] = Field(None, min_length=5, max_length=200)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)

class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str = Field(..., min_length=6)
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


```


---


### api\schemas\menu.py {#api\schemas\menu-py}

**File Size:** 2145 bytes

**File Path:** `api\schemas\menu.py`


```python

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MenuItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the menu item")
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    category: str = Field(..., min_length=1, max_length=50, description="Category of the item")
    description: str = Field(..., min_length=1, max_length=200, description="Description of the item")

class MenuItemCreate(MenuItemBase):
    """Schema for creating a new menu item"""
    pass

class MenuItemUpdate(BaseModel):
    """Schema for updating a menu item - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=200)

class MenuItemResponse(MenuItemBase):
    """Schema for menu item response"""
    id: int = Field(..., description="Unique identifier for the menu item")
    created_at: Optional[datetime] = Field(None, description="When the item was created")
    updated_at: Optional[datetime] = Field(None, description="When the item was last updated")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class MenuItemList(BaseModel):
    """Schema for list of menu items"""
    items: List[MenuItemResponse]
    total: int
    category_filter: Optional[str] = None

class MenuBulkOperation(BaseModel):
    """Schema for bulk operations"""
    item_ids: List[int] = Field(..., min_items=1, description="List of menu item IDs")

class OperationResponse(BaseModel):
    """Generic operation response"""
    success: bool
    message: str
    data: Optional[dict] = None

class MenuCategoryUpdate(BaseModel):
    """Schema for updating category name"""
    old_category: str = Field(..., min_length=1, max_length=50)
    new_category: str = Field(..., min_length=1, max_length=50)


```


---


### api\schemas\order.py {#api\schemas\order-py}

**File Size:** 1512 bytes

**File Path:** `api\schemas\order.py`


```python

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    notes: Optional[str] = Field(None, description="Additional notes about the status change")
    estimated_time: Optional[int] = Field(None, description="Estimated time in minutes for next status")

class OrderItemResponse(BaseModel):
    id: int
    name: str
    price: float
    quantity: int
    subtotal: float

class OrderResponse(BaseModel):
    order_number: str
    user_name: str
    phone_number: str
    items: List[OrderItemResponse]
    total: float
    delivery_address: str
    delivery_city: str
    delivery_postal: Optional[str]
    delivery_notes: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    status_history: List[Dict] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    status_filter: Optional[str] = None

class BulkStatusUpdate(BaseModel):
    order_numbers: List[str]
    status_update: OrderStatusUpdate


```


---


### api\services\__init__.py {#api\services\__init__-py}

**File Size:** 0 bytes

**File Path:** `api\services\__init__.py`


```python



```


---


### api\services\auth_service.py {#api\services\auth_service-py}

**File Size:** 6536 bytes

**File Path:** `api\services\auth_service.py`


```python

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


```


---


### api\services\menu_service.py {#api\services\menu_service-py}

**File Size:** 7548 bytes

**File Path:** `api\services\menu_service.py`


```python

from typing import List, Optional, Dict
from datetime import datetime
from pymongo import ASCENDING, DESCENDING
from config.database import db
from models.menu import MenuService
from api.schemas.menu import MenuItemCreate, MenuItemUpdate, MenuItemResponse

class MenuAPIService:
    def __init__(self):
        self.collection = db.menu
    
    async def get_next_id(self) -> int:
        """Get the next available ID for a new menu item"""
        # Find the highest ID in the collection
        highest = self.collection.find_one(sort=[("id", DESCENDING)])
        if highest and "id" in highest:
            return highest["id"] + 1
        return 1
    
    async def get_all_items(
        self, 
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MenuItemResponse]:
        """Get all menu items with optional filtering"""
        query = {}
        if category:
            query["category"] = {"$regex": category, "$options": "i"}
        
        cursor = self.collection.find(query).sort("id", ASCENDING).skip(skip).limit(limit)
        items = []
        
        for item in cursor:
            item_dict = {
                "id": item["id"],
                "name": item["name"],
                "price": item["price"],
                "category": item["category"],
                "description": item["description"],
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at")
            }
            items.append(MenuItemResponse(**item_dict))
        
        return items
    
    async def count_items(self, category: Optional[str] = None) -> int:
        """Count menu items with optional category filter"""
        query = {}
        if category:
            query["category"] = {"$regex": category, "$options": "i"}
        return self.collection.count_documents(query)
    
    async def get_item_by_id(self, item_id: int) -> Optional[MenuItemResponse]:
        """Get a specific menu item by ID"""
        item = self.collection.find_one({"id": item_id})
        if not item:
            return None
        
        return MenuItemResponse(
            id=item["id"],
            name=item["name"],
            price=item["price"],
            category=item["category"],
            description=item["description"],
            created_at=item.get("created_at"),
            updated_at=item.get("updated_at")
        )
    
    async def create_item(self, item_data: MenuItemCreate) -> MenuItemResponse:
        """Create a new menu item"""
        # Check if item with same name exists
        existing = self.collection.find_one({"name": {"$regex": f"^{item_data.name}$", "$options": "i"}})
        if existing:
            raise ValueError(f"Menu item with name '{item_data.name}' already exists")
        
        # Get next ID
        new_id = await self.get_next_id()
        
        # Create document
        now = datetime.utcnow()
        item_doc = {
            "id": new_id,
            "name": item_data.name,
            "price": item_data.price,
            "category": item_data.category,
            "description": item_data.description,
            "created_at": now,
            "updated_at": now
        }
        
        # Insert into database
        self.collection.insert_one(item_doc)
        
        return MenuItemResponse(**item_doc)
    
    async def update_item(self, item_id: int, item_update: MenuItemUpdate) -> Optional[MenuItemResponse]:
        """Update an existing menu item"""
        # Check if item exists
        existing = self.collection.find_one({"id": item_id})
        if not existing:
            return None
        
        # Build update document
        update_doc = {"updated_at": datetime.utcnow()}
        
        if item_update.name is not None:
            # Check if new name conflicts with another item
            name_exists = self.collection.find_one({
                "name": {"$regex": f"^{item_update.name}$", "$options": "i"},
                "id": {"$ne": item_id}
            })
            if name_exists:
                raise ValueError(f"Another menu item with name '{item_update.name}' already exists")
            update_doc["name"] = item_update.name
        
        if item_update.price is not None:
            update_doc["price"] = item_update.price
        
        if item_update.category is not None:
            update_doc["category"] = item_update.category
        
        if item_update.description is not None:
            update_doc["description"] = item_update.description
        
        # Update in database
        self.collection.update_one({"id": item_id}, {"$set": update_doc})
        
        # Return updated item
        return await self.get_item_by_id(item_id)
    
    async def delete_item(self, item_id: int) -> bool:
        """Delete a menu item"""
        result = self.collection.delete_one({"id": item_id})
        return result.deleted_count > 0
    
    async def bulk_delete_items(self, item_ids: List[int]) -> int:
        """Delete multiple menu items"""
        result = self.collection.delete_many({"id": {"$in": item_ids}})
        return result.deleted_count
    
    async def get_categories(self) -> List[str]:
        """Get all unique categories"""
        categories = self.collection.distinct("category")
        return sorted(categories)
    
    async def search_items(self, query: str, category: Optional[str] = None) -> List[MenuItemResponse]:
        """Search menu items by name or description"""
        search_query = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}}
            ]
        }
        
        if category:
            search_query["category"] = {"$regex": category, "$options": "i"}
        
        cursor = self.collection.find(search_query).sort("id", ASCENDING)
        items = []
        
        for item in cursor:
            items.append(MenuItemResponse(
                id=item["id"],
                name=item["name"],
                price=item["price"],
                category=item["category"],
                description=item["description"],
                created_at=item.get("created_at"),
                updated_at=item.get("updated_at")
            ))
        
        return items
    
    async def rename_category(self, old_category: str, new_category: str) -> int:
        """Rename a category for all items"""
        result = self.collection.update_many(
            {"category": {"$regex": f"^{old_category}$", "$options": "i"}},
            {
                "$set": {
                    "category": new_category,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count
    
    async def reset_to_default(self):
        """Reset menu to default items"""
        # Clear existing menu
        self.collection.delete_many({})
        
        # Use the existing MenuService to initialize default menu
        MenuService.initialize_menu(self.collection)
        
        # Add timestamps to all items
        now = datetime.utcnow()
        self.collection.update_many(
            {},
            {"$set": {"created_at": now, "updated_at": now}}
        )


```


---


### api\services\order_service.py {#api\services\order_service-py}

**File Size:** 5633 bytes

**File Path:** `api\services\order_service.py`


```python

from typing import List, Optional, Dict, Union
from datetime import datetime
from pymongo import DESCENDING
from bson import ObjectId
from config.database import db
from api.schemas.order import OrderStatus, OrderStatusUpdate, OrderResponse
from services.whatsapp_notification_service import WhatsAppNotificationService

class OrderAPIService:
    def __init__(self):
        self.collection = db.orders
        self.whatsapp_service = WhatsAppNotificationService()

    async def get_all_orders(
        self,
        status: Optional[Union[OrderStatus, str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrderResponse]:
        query = {}
        if status:
            query["status"] = status.value if isinstance(status, OrderStatus) else status
        cursor = self.collection.find(query).sort("created_at", DESCENDING).skip(skip).limit(limit)
        return [OrderResponse(**self._format_order_response(o)) for o in cursor]

    async def count_orders(self, status: Optional[Union[OrderStatus, str]] = None) -> int:
        query = {}
        if status:
            query["status"] = status.value if isinstance(status, OrderStatus) else status
        return self.collection.count_documents(query)

    async def get_order_by_number(self, order_number: str) -> Optional[OrderResponse]:
        order = self.collection.find_one({"order_number": order_number})
        if not order:
            return None
        return OrderResponse(**self._format_order_response(order))

    async def get_order_by_id(self, order_id: str) -> Optional[OrderResponse]:
        try:
            order = self.collection.find_one({"_id": ObjectId(order_id)})
            if not order:
                return None
            return OrderResponse(**self._format_order_response(order))
        except:
            return None

    async def update_order_status(self, order_number: str, status_update: OrderStatusUpdate) -> Optional[OrderResponse]:
        order = self.collection.find_one({"order_number": order_number})
        if not order:
            return None

        current_status = order.get("status", "confirmed")
        new_status = status_update.status.value

        if not self._is_valid_status_transition(current_status, new_status):
            raise ValueError(f"Invalid status transition from {current_status} to {new_status}")

        status_entry = {
            "status": new_status,
            "timestamp": datetime.utcnow(),
            "notes": status_update.notes,
            "estimated_time": status_update.estimated_time
        }

        self.collection.update_one(
            {"order_number": order_number},
            {"$set": {"status": new_status, "updated_at": datetime.utcnow()},
             "$push": {"status_history": status_entry}}
        )

        self.whatsapp_service.send_order_status_notification(
            phone_number=order["phone_number"],
            order_number=order_number,
            status=new_status,
            customer_name=order["user_name"],
            estimated_time=status_update.estimated_time,
            notes=status_update.notes
        )

        return await self.get_order_by_number(order_number)

    async def get_orders_by_phone(self, phone_number: str) -> List[OrderResponse]:
        cursor = self.collection.find({"phone_number": phone_number}).sort("created_at", DESCENDING)
        return [OrderResponse(**self._format_order_response(o)) for o in cursor]

    async def get_active_orders(self) -> List[OrderResponse]:
        query = {"status": {"$nin": [OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value]}}
        cursor = self.collection.find(query).sort("created_at", DESCENDING)
        return [OrderResponse(**self._format_order_response(o)) for o in cursor]

    async def bulk_update_status(self, order_numbers: List[str], status_update: OrderStatusUpdate) -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        for num in order_numbers:
            try:
                updated_order = await self.update_order_status(num, status_update)
                results[num] = updated_order is not None
            except Exception as e:
                print(f"Error updating order {num}: {str(e)}")
                results[num] = False
        return results

    def _format_order_response(self, order: Dict) -> Dict:
        return {
            "order_number": order["order_number"],
            "user_name": order["user_name"],
            "phone_number": order["phone_number"],
            "items": order["items"],
            "total": order["total"],
            "delivery_address": order["delivery_address"],
            "delivery_city": order["delivery_city"],
            "delivery_postal": order.get("delivery_postal", ""),
            "delivery_notes": order.get("delivery_notes", ""),
            "status": order["status"],
            "created_at": order["created_at"],
            "updated_at": order.get("updated_at"),
            "status_history": order.get("status_history", [])
        }

    def _is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        valid_transitions = {
            "confirmed": ["preparing", "cancelled"],
            "preparing": ["ready", "cancelled"],
            "ready": ["out_for_delivery", "cancelled"],
            "out_for_delivery": ["delivered", "cancelled"],
            "delivered": [],
            "cancelled": []
        }
        return new_status in valid_transitions.get(current_status, [])


```


---


### check_status.py {#check_status-py}

**File Size:** 1623 bytes

**File Path:** `check_status.py`


```python

#!/usr/bin/env python3
"""
Quick WhatsApp status checker
"""
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

def check_status():
    instance_id = os.getenv("WHATSAPP_INSTANCE_ID")
    token = os.getenv("WHATSAPP_TOKEN")
    
    status_url = f"https://api.green-api.com/waInstance{instance_id}/getStateInstance/{token}"
    
    try:
        response = requests.get(status_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            state = data.get('stateInstance')
            
            print(f"📱 WhatsApp Instance Status: {state}")
            
            if state == 'authorized':
                print("✅ READY! Your WhatsApp bot is authorized and ready to receive messages!")
                return True
            elif state == 'starting':
                print("🔄 Still starting... Please wait and try again in a few minutes")
                return False
            elif state == 'notAuthorized':
                print("❌ Not authorized. Please scan the QR code:")
                print("🔗 https://api.green-api.com/waInstance7105219783/qr/8a2bac7488884cfdaacf9c83f0ce5dd715801ff16dac411dbf")
                return False
            else:
                print(f"⚠️ Unknown state: {state}")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    print("Checking WhatsApp authorization status...")
    check_status()


```


---


### check_users.py {#check_users-py}

**File Size:** 2685 bytes

**File Path:** `check_users.py`


```python

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


```


---


### config\auth.py {#config\auth-py}

**File Size:** 1835 bytes

**File Path:** `config\auth.py`


```python

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

# Security settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


```


---


### config\database.py {#config\database-py}

**File Size:** 1690 bytes

**File Path:** `config\database.py`


```python

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


```


---


### config\settings.py {#config\settings-py}

**File Size:** 1504 bytes

**File Path:** `config\settings.py`


```python

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # MongoDB Configuration
    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        raise ValueError("MONGO_URI environment variable is required")
    
    # Gemini Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    
    GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    
    # WhatsApp Configuration
    WHATSAPP_INSTANCE_ID = os.getenv("WHATSAPP_INSTANCE_ID")
    if not WHATSAPP_INSTANCE_ID:
        raise ValueError("WHATSAPP_INSTANCE_ID environment variable is required")
    
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
    if not WHATSAPP_TOKEN:
        raise ValueError("WHATSAPP_TOKEN environment variable is required")
    
    # Model Configuration
    MODEL_NAME = os.getenv("MODEL_NAME")
    
    # Conversation History Settings
    CONVERSATION_HISTORY_LIMIT = int(os.getenv("CONVERSATION_HISTORY_LIMIT"))
    CONVERSATION_HISTORY_HOURS = int(os.getenv("CONVERSATION_HISTORY_HOURS"))
    
    # API Server Configuration
    API_HOST = os.getenv("API_HOST")
    API_PORT = int(os.getenv("API_PORT"))
    
    # Other Settings
    OLD_CONVERSATION_CLEANUP_DAYS = int(os.getenv("OLD_CONVERSATION_CLEANUP_DAYS"))

settings = Settings()


```


---


### ez_order\__init__.py {#ez_order\__init__-py}

**File Size:** 0 bytes

**File Path:** `ez_order\__init__.py`


```python



```


---


### generate_documentation.py {#generate_documentation-py}

**File Size:** 6019 bytes

**File Path:** `generate_documentation.py`


```python

import os
from pathlib import Path
from datetime import datetime

# Directories and files to skip
SKIP_DIRS = {
    '__pycache__',
    '.git',
    'vosk-model-small-en-us-0.15',
    'vosk-model-small-hi-0.22',
    'venv',
    'env',
    '.venv',
    'node_modules',
    '.pytest_cache',
    '__pycache__'
}

SKIP_FILES = {
    '.pyc',
    '.pyo',
    '.pyd',
    '.so',
    '.dll',
    '.dylib',
    '.db',
    '.sqlite',
    '.log',
    'poetry.lock',
    '.DS_Store',
    'Thumbs.db'
}

IMPORTANT_EXTENSIONS = {
    '.py',
    '.toml',
    '.env.example',
    '.yml',
    '.yaml',
    '.json',
    '.md',
    '.txt',
    '.ini',
    '.cfg'
}

def should_skip_file(file_path):
    """Check if a file should be skipped."""
    file_name = os.path.basename(file_path)
    file_ext = os.path.splitext(file_name)[1]
    
    # Skip compiled Python files
    if file_ext in SKIP_FILES:
        return True
    
    # Skip files without important extensions (unless they're special files)
    if file_ext and file_ext not in IMPORTANT_EXTENSIONS and file_name not in ['Dockerfile', 'Makefile', 'requirements.txt']:
        return True
    
    # Skip hidden files (except .env.example)
    if file_name.startswith('.') and file_name != '.env.example':
        return True
    
    return False

def should_skip_dir(dir_name):
    """Check if a directory should be skipped."""
    return dir_name in SKIP_DIRS

def get_language_from_extension(file_path):
    """Get the language identifier for code blocks based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.json': 'json',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.toml': 'toml',
        '.sh': 'bash',
        '.sql': 'sql',
        '.md': 'markdown',
        '.txt': 'text',
        '.env': 'env',
        '.ini': 'ini',
        '.cfg': 'ini'
    }
    return language_map.get(ext, '')

def read_file_content(file_path):
    """Read file content safely."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except:
            return f"[Binary or unreadable file: {file_path}]"
    except Exception as e:
        return f"[Error reading file: {str(e)}]"

def generate_documentation(root_dir):
    """Generate project documentation."""
    documentation = []
    
    # Add header
    documentation.append("# Project Documentation\n")
    documentation.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    documentation.append("## Table of Contents\n")
    
    # Collect all files first for table of contents
    all_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Remove directories that should be skipped
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(file_path, root_dir)
            
            if not should_skip_file(file_path):
                all_files.append(relative_path)
    
    # Sort files for better organization
    all_files.sort()
    
    # Generate table of contents
    current_dir = None
    for file_path in all_files:
        dir_path = os.path.dirname(file_path)
        if dir_path != current_dir:
            current_dir = dir_path
            if dir_path:
                documentation.append(f"\n### {dir_path}/\n")
        
        file_name = os.path.basename(file_path)
        anchor = file_path.replace('/', '-').replace('.', '-').replace(' ', '-').lower()
        documentation.append(f"- [{file_name}](#{anchor})\n")
    
    documentation.append("\n---\n\n## File Contents\n")
    
    # Add file contents
    for relative_path in all_files:
        file_path = os.path.join(root_dir, relative_path)
        
        # Create section header
        anchor = relative_path.replace('/', '-').replace('.', '-').replace(' ', '-').lower()
        documentation.append(f"\n### {relative_path} {{#{anchor}}}\n")
        
        # Add file info
        file_size = os.path.getsize(file_path)
        documentation.append(f"**File Size:** {file_size} bytes\n")
        documentation.append(f"**File Path:** `{relative_path}`\n\n")
        
        # Read and add content
        content = read_file_content(file_path)
        language = get_language_from_extension(file_path)
        
        documentation.append(f"```{language}\n")
        documentation.append(content)
        documentation.append("\n```\n")
        documentation.append("\n---\n")
    
    return '\n'.join(documentation)

def main():
    """Main function to generate documentation."""
    # Get the current directory (where the script is run from)
    root_dir = os.getcwd()
    
    print(f"Generating documentation for: {root_dir}")
    print("This may take a moment...")
    
    # Generate documentation
    doc_content = generate_documentation(root_dir)
    
    # Write to file
    output_file = "project_documentation.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    # Calculate some statistics
    total_size = len(doc_content)
    line_count = doc_content.count('\n')
    
    print(f"\n✅ Documentation generated successfully!")
    print(f"📄 Output file: {output_file}")
    print(f"📊 Total size: {total_size:,} characters")
    print(f"📊 Total lines: {line_count:,}")
    
    # Show file count
    file_count = doc_content.count("### ")
    print(f"📊 Files documented: {file_count}")

if __name__ == "__main__":
    main()


```


---


### handlers\whatsapp_handler.py {#handlers\whatsapp_handler-py}

**File Size:** 24361 bytes

**File Path:** `handlers\whatsapp_handler.py`


```python

from whatsapp_chatbot_python import GreenAPIBot, Notification
from agents import Runner
from config.database import db
from services.conversation_service import ConversationService
from services.state_manager import StateManager
from agents_folder.restaurant_agent import AgentFactory
from agents_folder.registration_agent import RegistrationAgentFactory
from utils.phone_utils import clean_phone_number
from services.free_speech_service import HybridSpeechToTextService
from typing import Optional
import asyncio
import concurrent.futures
import threading
import nest_asyncio
import time

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

class WhatsAppHandler:
    def __init__(self, instance_id: str, token: str):
        self.bot = GreenAPIBot(instance_id, token)
        self.conversation_service = ConversationService()
        self.state_manager = StateManager
        self.speech_service = HybridSpeechToTextService()
        
        # Create both agents
        self.registration_agent, self.registration_config = RegistrationAgentFactory.create_registration_agent()
        self.restaurant_agent, self.restaurant_config = AgentFactory.create_restaurant_agent()
        
        # Thread pool for running agents with more workers for better concurrency
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
        self._setup_handlers()

    def _setup_handlers(self):
        @self.bot.router.message()
        def message_handler(notification: Notification) -> None:
            # Handle message in a separate thread to avoid blocking
            self.executor.submit(self._handle_message_wrapper, notification)

    def _handle_message_wrapper(self, notification: Notification):
        """Wrapper to handle exceptions in threaded execution"""
        try:
            self._handle_message(notification)
        except Exception as e:
            print(f"❌ Error in message handler wrapper: {e}")
            try:
                notification.answer("Sorry, I encountered an error. Please try again.")
            except:
                pass

    def _run_agent_safely(self, agent, context, config, agent_type="Agent"):
        """Run agent with proper event loop handling and improved timeout"""
        start_time = time.time()
        print(f"🤖 Starting {agent_type}...")
        
        def run_with_new_loop():
            """Run agent in a new event loop"""
            # Create new event loop for this execution
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the agent
                result = Runner.run_sync(
                    starting_agent=agent,
                    input=context,
                    run_config=config
                )
                return result.final_output
            except Exception as e:
                print(f"❌ Error in {agent_type}: {e}")
                import traceback
                traceback.print_exc()
                raise e
            finally:
                # Clean up the loop
                loop.close()
        
        try:
            # Execute in thread pool with reduced timeout
            future = self.executor.submit(run_with_new_loop)
            # Reduced timeout from 30 to 15 seconds
            result = future.result(timeout=15)
            
            elapsed_time = time.time() - start_time
            print(f"✅ {agent_type} completed in {elapsed_time:.2f} seconds")
            return result
            
        except concurrent.futures.TimeoutError:
            elapsed_time = time.time() - start_time
            print(f"⏱ {agent_type} timed out after {elapsed_time:.2f} seconds")
            return f"🤖 I'm taking a bit longer than expected. Please try again or type 'menu' to see our offerings!"
        except Exception as e:
            print(f"❌ {agent_type} execution error: {e}")
            return f"🤖 I encountered an issue. Please try again or type 'menu' to see our offerings!"

    def _send_quick_acknowledgment(self, notification: Notification, phone_number: str):
        """Send immediate acknowledgment to user"""
        try:
            quick_responses = [
                "Got it! Let me process that for you... 🔄",
                "Thanks! Processing your request... ⏳",
                "Received! Just a moment... 💭",
                "On it! Getting that ready... 🚀"
            ]
            import random
            acknowledgment = random.choice(quick_responses)
            notification.answer(acknowledgment)
            return True
        except:
            return False

    def _handle_message(self, notification: Notification):
        try:
            # Extract and clean phone number
            raw_phone_number = notification.sender
            phone_number = clean_phone_number(raw_phone_number)
            
            # Debug: Print notification details
            print(f"📨 Received message from {phone_number}")
            
            # Get message data using the available method
            message_data = None
            if hasattr(notification, 'get_message_data'):
                try:
                    message_data = notification.get_message_data()
                except Exception as e:
                    print(f"❌ Error getting message data: {e}")
            
            # Check if it's a voice message
            is_voice_message = False
            if message_data and isinstance(message_data, dict):
                msg_type = message_data.get('typeMessage', '')
                is_voice_message = msg_type in ['audioMessage', 'voiceMessage', 'pttMessage']
                
                # Check fileMessageData for audio files
                if not is_voice_message and 'fileMessageData' in message_data:
                    file_data = message_data['fileMessageData']
                    if isinstance(file_data, dict):
                        mime_type = file_data.get('mimeType', '')
                        if 'audio' in mime_type or 'voice' in mime_type:
                            is_voice_message = True
            
            if is_voice_message:
                print(f"🎤 Processing voice message from {phone_number}")
                # Send quick acknowledgment for voice messages
                self._send_quick_acknowledgment(notification, phone_number)
                # Handle voice message
                message = self._process_voice_message(notification, phone_number)
                if not message:
                    print(f"❌ Voice processing failed for {phone_number}")
                    # Fallback message
                    message = "Hello"
                    # Notify user about the voice issue
                    self.conversation_service.save_conversation(
                        phone_number,
                        "assistant", 
                        "🎤 I received your voice message but couldn't process it clearly. How can I help you today?"
                    )
                else:
                    print(f"✅ Voice message processed: {message}")
            else:
                # Regular text message
                message = notification.message_text
                print(f"💬 Text message: {message}")
            
            # Ensure message is not None
            if not message:
                print(f"❌ Received empty message from {phone_number}")
                notification.answer("Sorry, I didn't receive any message. Please try again.")
                return
            
            # Save user message to conversation history
            self.conversation_service.save_conversation(phone_number, "user", message)
            
            # Clear old conversations periodically
            self.conversation_service.clear_old_conversations(phone_number)
            
            # Get user state
            print(f"🔍 Checking user state for {phone_number}...")
            user_state = self.state_manager.get_user_state(phone_number)
            user_exists = user_state['is_registered']
            user_data = user_state['user_data']
            
            print(f"👤 User registered: {user_exists}")
            if user_data:
                print(f"👤 User name: {user_data.get('name', 'Not set')}")
            
            # Get limited conversation history
            conversation_history = self.conversation_service.get_conversation_history(phone_number, limit=25)
            
            # Quick responses for common queries (no agent needed)
            lower_message = message.lower() if message else ""
            
            # Handle quick menu request
            if lower_message in ['menu', 'show menu', 'mnu', 'm']:
                from tools.menu_tools import show_menu
                quick_menu = show_menu()
                self.conversation_service.save_conversation(phone_number, "assistant", quick_menu)
                notification.answer(quick_menu)
                return
            
            # Handle quick order view
            if lower_message in ['view order', 'show cart', 'cart', 'my order']:
                if user_exists:
                    from tools.order_tools import view_current_order
                    order_view = view_current_order(phone_number)
                    self.conversation_service.save_conversation(phone_number, "assistant", order_view)
                    notification.answer(order_view)
                    return
            
            if user_exists:
                # Existing user - use restaurant agent
                print(f"🍕 Using Restaurant Agent for existing user")
                
                # Check if this is likely a greeting or general message
                recent_messages = conversation_history.get('messages', [])
                
                # Count only USER messages to determine if it's a new session
                user_message_count = sum(1 for msg in recent_messages if msg.get('role') == 'user')
                is_new_session = user_message_count <= 1  # This is their first or second message
                
                # Determine user intent
                is_greeting = any(word in lower_message for word in 
                                ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 
                                 'good evening', 'salam', 'assalam', 'aoa'])
                
                is_confirmation = any(word in lower_message for word in 
                                    ['confirm', 'place order', 'yes confirm', 'checkout', 'proceed', "that's it", 'done'])
                is_view_order = any(word in lower_message for word in 
                                  ['view order', 'show cart', 'my order', 'current order'])
                is_adding_items = any(word in lower_message for word in 
                                    ['add', 'want', 'order']) and any(char.isdigit() for char in (message or ""))
                is_menu_request = any(word in lower_message for word in 
                                    ['menu', 'show menu', 'what do you have'])
                
                print(f"📊 Intent Analysis:")
                print(f"   - Greeting: {is_greeting}")
                print(f"   - Confirmation: {is_confirmation}")
                print(f"   - View Order: {is_view_order}")
                print(f"   - Adding Items: {is_adding_items}")
                print(f"   - Menu Request: {is_menu_request}")
                print(f"   - New Session: {is_new_session}")
                print(f"   - User message count: {user_message_count}")
                
                # Determine if we should show menu
                should_show_menu = is_new_session or is_greeting or is_menu_request
                
                # Create optimized context
                context = f"""
                CUSTOMER: {user_data['name']} (Phone: {phone_number})
                ADDRESS: {user_data['address']}, {user_data['city']}
                
                CURRENT MESSAGE: {message}
                {"(Voice message)" if is_voice_message else ""}
                
                INTENT:
                - Greeting: {is_greeting}
                - Confirming order: {is_confirmation}
                - Viewing order: {is_view_order}
                - Adding items: {is_adding_items}
                - Menu request: {is_menu_request}
                - Should show menu: {should_show_menu}
                
                RECENT CONVERSATION (Last 3):
                {self._get_recent_messages(conversation_history, limit=3)}
                
                INSTRUCTIONS: Respond immediately based on the detected intent. Be concise.
                """
                
                # Update state
                self.state_manager.update_user_state(phone_number, 'ordering')
                
                # Run restaurant agent with proper event loop handling
                response = self._run_agent_safely(
                    self.restaurant_agent,
                    context,
                    self.restaurant_config,
                    "Restaurant Agent"
                )
                
                # Ensure we have a response
                if not response or response.strip() == "":
                    print("⚠️ Empty response from agent, generating default response")
                    if is_greeting or is_new_session:
                        response = f"Hello {user_data.get('name', 'there')}! 👋 Welcome back to our restaurant! Let me show you our menu..."
                        # Force show menu
                        from tools.menu_tools import show_menu
                        menu_text = show_menu()
                        response = response + "\n\n" + menu_text
                    else:
                        response = "I'm here to help you with your order! You can:\n• Say 'menu' to see our offerings\n• Say 'view order' to check your cart\n• Tell me what you'd like to order!"
                
            else:
                # New user - use registration agent
                print(f"📝 Using Registration Agent for new user")
                
                # Send quick acknowledgment for new users
                try:
                    notification.answer("Welcome! I'll help you get registered. Just a moment... 🎯")
                except:
                    pass
                
                context = f"""
                NEW USER REGISTRATION
                Phone: {phone_number}
                
                RECENT CONVERSATION:
                {self._get_recent_messages(conversation_history, limit=5)}
                
                CURRENT MESSAGE: {message}
                {"(Voice message)" if is_voice_message else ""}
                
                Help this new user register by collecting their details.
                """
                
                # Update state
                self.state_manager.update_user_state(phone_number, 'registering')
                
                # Run registration agent with proper event loop handling
                response = self._run_agent_safely(
                    self.registration_agent,
                    context,
                    self.registration_config,
                    "Registration Agent"
                )
                
                # Check if registration was completed
                new_state = self.state_manager.get_user_state(phone_number)
                if new_state['is_registered'] and not user_exists:
                    # User just registered
                    print(f"✅ User registration completed! Showing menu...")
                    # Add menu immediately without running another agent
                    from tools.menu_tools import show_menu
                    menu_text = show_menu()
                    response = response + "\n\n" + menu_text
            
            # Save assistant response
            self.conversation_service.save_conversation(phone_number, "assistant", response)
            
            # Send response back to WhatsApp
            print(f"📤 Sending response to WhatsApp...")
            notification.answer(response)
            print(f"✅ Message handling completed successfully")
            
        except Exception as e:
            error_msg = f"Sorry, an error occurred: {str(e)}"
            print(f"❌ Error in message handler: {e}")
            import traceback
            traceback.print_exc()
            notification.answer(error_msg)
            if 'phone_number' in locals():
                self.conversation_service.save_conversation(phone_number, "assistant", error_msg)

    def _get_recent_messages(self, conversation_history, limit=3):
        """Get only recent messages for context"""
        messages = conversation_history.get('messages', [])
        recent = messages[-limit:] if len(messages) > limit else messages
        
        formatted = ""
        for msg in recent:
            role = "Customer" if msg["role"] == "user" else "Assistant"
            formatted += f"{role}: {msg['message']}\n"
        
        return formatted if formatted else "No recent messages"

    def _process_voice_message(self, notification: Notification, phone_number: str) -> Optional[str]:
        """Process voice message and convert to text"""
        try:
            print(f"🎤 Processing voice message from {phone_number}")
            
            # Get audio URL from notification
            audio_url = None
            
            # Check messageData using get_message_data()
            if hasattr(notification, 'get_message_data'):
                try:
                    message_data = notification.get_message_data()
                    if isinstance(message_data, dict):
                        print(f"📋 Searching for audio URL in message_data: {message_data}")
                        
                        # Check fileMessageData (common structure for files)
                        if 'fileMessageData' in message_data:
                            file_data = message_data['fileMessageData']
                            if isinstance(file_data, dict):
                                audio_url = file_data.get('downloadUrl')
                                if audio_url:
                                    print(f"📎 Found audio URL via get_message_data().fileMessageData.downloadUrl: {audio_url}")
                
                except Exception as e:
                    print(f"❌ Error accessing get_message_data(): {e}")
            
            if not audio_url:
                print("❌ No audio URL found in notification")
                return None
            
            print(f"🎤 Processing voice message from {phone_number}")
            print(f"🔗 Audio URL: {audio_url}")
            
            # Try to detect language from recent messages
            language = self._detect_language(phone_number)
            print(f"🌐 Detected language: {language}")
            
            # Convert voice to text using hybrid service
            try:
                text = self.speech_service.convert_voice_to_text(audio_url, language)
                
                if text and text.strip():
                    print(f"✅ Voice transcribed: {text}")
                    # Save with voice indicator
                    voice_indicator = "[🎤 Voice Message] " if language == "en" else "[🎤 صوتی پیغام] "
                    self.conversation_service.save_conversation(
                        phone_number,
                        "user",
                        f"{voice_indicator}{text}",
                        metadata={
                            "type": "voice",
                            "original_url": audio_url,
                            "detected_language": language
                        }
                    )
                    return text.strip()
                else:
                    print("❌ Failed to transcribe voice message - empty result")
                    return None
            except Exception as speech_error:
                print(f"❌ Speech service error: {speech_error}")
                return None
                
        except Exception as e:
            print(f"❌ Error processing voice message: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _detect_language(self, phone_number: str) -> str:
        """Simple language detection based on recent messages"""
        try:
            # Get recent conversation
            history = self.conversation_service.get_conversation_history(phone_number, limit=10)
            messages = history.get('messages', [])
            
            # Count Urdu characters in recent messages
            urdu_count = 0
            english_count = 0
            total_chars = 0
            
            for msg in messages:
                if msg['role'] == 'user':
                    text = msg['message']
                    # Remove voice message indicators
                    text = text.replace('[🎤 Voice Message] ', '').replace('[🎤 صوتی پیغام] ', '')
                    
                    # Count characters
                    for char in text:
                        if '\u0600' <= char <= '\u06FF':  # Arabic/Urdu script range
                            urdu_count += 1
                        elif 'a' <= char.lower() <= 'z':  # English characters
                            english_count += 1
                    
                    total_chars += len(text)
            
            # Determine language based on character count
            if total_chars > 0:
                urdu_percentage = urdu_count / total_chars
                english_percentage = english_count / total_chars
                
                print(f"Language detection - Urdu: {urdu_percentage:.2%}, English: {english_percentage:.2%}")
                
                # If more than 20% Urdu characters, assume Urdu
                if urdu_percentage > 0.2:
                    return 'ur'
                # If mostly English
                elif english_percentage > 0.5:
                    return 'en'
            
            # Default to English
            return 'en'
            
        except Exception as e:
            print(f"Error in language detection: {str(e)}")
            return 'en'  # Default to English

    def run(self):
        """Run the WhatsApp bot"""
        print("🍕 Restaurant WhatsApp Bot is running...")
        print("Features enabled:")
        print("✅ Dual Agent System (Registration + Restaurant)")
        print("✅ Proactive Menu Display")
        print("✅ WhatsApp Formatting")
        print("✅ Smart Conversation Management")
        print("✅ FREE Voice Message Support (English & Urdu) - Hybrid Mode")
        print("\nAgents initialized:")
        print("1️⃣ Registration Agent - For new users")
        print("2️⃣ Restaurant Agent - For existing users (shows menu proactively)")
        print("🎤 Hybrid Speech Recognition - Online + Offline Support")
        print("   • Primary: Google Web Speech API (Free, Online)")
        print("   • Fallback: Vosk (Offline)")
        print("\nVoice Message Features:")
        print("   • Automatic language detection (English/Urdu)")
        print("   • Multiple language fallbacks")
        print("   • Works without API keys")
        print("\n✅ Event loop handling configured for multi-threaded execution")
        
        self.bot.run_forever()

    def __del__(self):
        """Cleanup thread pool on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


```


---


### main.py {#main-py}

**File Size:** 5557 bytes

**File Path:** `main.py`


```python

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


```


---


### models\menu.py {#models\menu-py}

**File Size:** 1891 bytes

**File Path:** `models\menu.py`


```python

from typing import List, Dict, Optional

class MenuItem:
    def __init__(self, id: int, name: str, price: float, category: str, description: str):
        self.id = id
        self.name = name
        self.price = price
        self.category = category
        self.description = description

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "category": self.category,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'MenuItem':
        return cls(
            id=data['id'],
            name=data['name'],
            price=data['price'],
            category=data['category'],
            description=data['description']
        )

class MenuService:
    DEFAULT_MENU_ITEMS = [
        MenuItem(1, "Margherita Pizza", 12.99, "Pizza", "Classic tomato sauce, mozzarella, basil"),
        MenuItem(2, "Pepperoni Pizza", 14.99, "Pizza", "Tomato sauce, mozzarella, pepperoni"),
        MenuItem(3, "Caesar Salad", 8.99, "Salad", "Romaine lettuce, croutons, parmesan"),
        MenuItem(4, "Grilled Chicken", 16.99, "Main", "Herb-marinated chicken breast"),
        MenuItem(5, "Pasta Carbonara", 13.99, "Pasta", "Creamy pasta with bacon"),
        MenuItem(6, "Tiramisu", 6.99, "Dessert", "Classic Italian dessert"),
        MenuItem(7, "Coca Cola", 2.99, "Beverage", "330ml can"),
        MenuItem(8, "Fresh Orange Juice", 4.99, "Beverage", "Freshly squeezed"),
    ]
    
    @classmethod
    def initialize_menu(cls, menu_collection):
        """Initialize menu items in MongoDB"""
        menu_collection.delete_many({})
        menu_items = [item.to_dict() for item in cls.DEFAULT_MENU_ITEMS]
        menu_collection.insert_many(menu_items)
        print("Menu initialized!")


```


---


### models\order.py {#models\order-py}

**File Size:** 997 bytes

**File Path:** `models\order.py`


```python

from typing import List, Dict, Optional
from datetime import datetime

class OrderItem:
    def __init__(self, id: int, name: str, price: float, quantity: int):
        self.id = id
        self.name = name
        self.price = price
        self.quantity = quantity
        self.subtotal = price * quantity

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'quantity': self.quantity,
            'subtotal': self.subtotal
        }

class Order:
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        self.items: List[OrderItem] = []
        self.total = 0.0

    def add_item(self, item: OrderItem):
        self.items.append(item)
        self.total += item.subtotal

    def to_dict(self) -> Dict:
        return {
            'items': [item.to_dict() for item in self.items],
            'total': self.total
        }


```


---


### models\user.py {#models\user-py}

**File Size:** 2163 bytes

**File Path:** `models\user.py`


```python

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


```


---


### models\webhook_notification.py {#models\webhook_notification-py}

**File Size:** 753 bytes

**File Path:** `models\webhook_notification.py`


```python

from datetime import datetime
from typing import Dict, Optional
from enum import Enum

class NotificationType(str, Enum):
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_STATUS_CHANGED = "order_status_changed"

class WebhookNotification:
    def __init__(self, notification_type: NotificationType, data: Dict):
        self.type = notification_type
        self.data = data
        self.created_at = datetime.utcnow()
        self.read = False
        self.read_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "data": self.data,
            "created_at": self.created_at,
            "read": self.read,
            "read_at": self.read_at
        }


```


---


### pyproject.toml {#pyproject-toml}

**File Size:** 777 bytes

**File Path:** `pyproject.toml`


```toml

[tool.poetry]
name = "ez-order"
version = "0.1.0"
description = "A WhatsApp chatbot system using FastAPI, Gemini-compatible client, and MongoDB"
authors = ["Your Name <usman678zafar@gmail.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "^3.9"
python-dotenv = "^1.0.1"
pymongo = "^4.6.1"
whatsapp-api-client-python = "^0.0.49"
whatsapp-chatbot-python = "0.9.6"
openai = "^1.43.0"
anthropic = "^0.30.0"
fastapi = "^0.110.0"
uvicorn = "^0.22.0"
pydantic = "^2.5.0"
python-jose = "^3.3.0"
passlib = "^1.7.4"
bcrypt = "^4.1.2"
python-multipart = "^0.0.9"
email-validator = "^2.1.0"
openai-agents = "^0.1.0"
SpeechRecognition = "^3.10.0"
pydub = "^0.25.1"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"


```


---


### services\conversation_service.py {#services\conversation_service-py}

**File Size:** 6783 bytes

**File Path:** `services\conversation_service.py`


```python

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

```


---


### services\free_speech_service.py {#services\free_speech_service-py}

**File Size:** 15373 bytes

**File Path:** `services\free_speech_service.py`


```python

import os
import tempfile
import requests
from typing import Optional, List
import speech_recognition as sr
from pydub import AudioSegment
import json

class FreeSpeechToTextService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Configure recognizer for better accuracy
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        
    def convert_voice_to_text(self, audio_url: str, language: str = "en") -> Optional[str]:
        """
        Convert voice message to text using free Google Web Speech API
        
        Args:
            audio_url: URL of the voice message
            language: Language code ('en' for English, 'ur' for Urdu)
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Download audio file
            print(f"📥 Downloading audio from: {audio_url}")
            audio_data = self._download_audio(audio_url)
            if not audio_data:
                return None
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_audio:
                temp_audio.write(audio_data)
                temp_audio_path = temp_audio.name
            
            # Convert to WAV format (required for speech recognition)
            wav_path = self._convert_to_wav(temp_audio_path)
            
            # Load audio file
            with sr.AudioFile(wav_path) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                
                # Record audio
                audio = self.recognizer.record(source)
            
            # Convert language code
            primary_lang = "en-US" if language == "en" else "ur-PK"
            
            print(f"🎤 Converting speech to text (Primary language: {primary_lang})...")
            
            # Try multiple recognition approaches
            text = self._recognize_with_fallback(audio, primary_lang)
            
            if text:
                print(f"✅ Transcribed text: {text}")
                return text
            else:
                print("❌ Could not understand audio in any language")
                return None
            
        except Exception as e:
            print(f"❌ Error in speech-to-text conversion: {str(e)}")
            return None
        finally:
            # Clean up temporary files
            if 'temp_audio_path' in locals():
                try:
                    os.unlink(temp_audio_path)
                except:
                    pass
            if 'wav_path' in locals():
                try:
                    os.unlink(wav_path)
                except:
                    pass
    
    def _recognize_with_fallback(self, audio, primary_language: str) -> Optional[str]:
        """
        Try to recognize speech with multiple language fallbacks
        
        Args:
            audio: Audio data
            primary_language: Primary language to try first
            
        Returns:
            Transcribed text or None
        """
        # Define language fallback order
        language_fallback_order = {
            "ur-PK": ["ur-PK", "hi-IN", "en-US", "en-IN"],  # Urdu → Hindi → English
            "en-US": ["en-US", "en-IN", "ur-PK", "hi-IN"],  # English → Urdu → Hindi
            "hi-IN": ["hi-IN", "ur-PK", "en-IN", "en-US"],  # Hindi → Urdu → English
        }
        
        # Get fallback languages
        languages_to_try = language_fallback_order.get(primary_language, [primary_language, "en-US"])
        
        # Try each language
        for lang_code in languages_to_try:
            try:
                print(f"🔍 Trying language: {lang_code}")
                text = self.recognizer.recognize_google(audio, language=lang_code)
                
                if text and text.strip():
                    print(f"✅ Successfully recognized with {lang_code}")
                    # If we used a fallback language, indicate it
                    if lang_code != primary_language:
                        return f"{text} [Auto-detected: {self._get_language_name(lang_code)}]"
                    return text
                    
            except sr.UnknownValueError:
                print(f"❌ Could not understand audio in {lang_code}")
                continue
            except sr.RequestError as e:
                print(f"❌ Error with Google Speech Recognition for {lang_code}: {e}")
                continue
            except Exception as e:
                print(f"❌ Unexpected error with {lang_code}: {e}")
                continue
        
        # If all languages fail, try without specifying language (auto-detect)
        try:
            print("🔍 Trying auto-detection...")
            text = self.recognizer.recognize_google(audio)
            if text and text.strip():
                print("✅ Successfully recognized with auto-detection")
                return f"{text} [Auto-detected]"
        except:
            pass
        
        return None
    
    def _get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name"""
        language_names = {
            "en-US": "English",
            "en-IN": "Indian English",
            "ur-PK": "Urdu",
            "hi-IN": "Hindi"
        }
        return language_names.get(lang_code, lang_code)
    
    def _download_audio(self, audio_url: str) -> Optional[bytes]:
        """Download audio file from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(audio_url, headers=headers, timeout=30)
            if response.status_code == 200:
                print(f"✅ Audio downloaded successfully ({len(response.content)} bytes)")
                return response.content
            else:
                print(f"❌ Failed to download audio: Status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error downloading audio: {str(e)}")
            return None
    
    def _convert_to_wav(self, audio_path: str) -> str:
        """Convert audio to WAV format with optimal settings for speech recognition"""
        try:
            # Load audio file
            audio = AudioSegment.from_file(audio_path)
            
            # Convert to optimal format for speech recognition
            # - Mono channel
            # - 16kHz sample rate (optimal for speech)
            # - 16-bit depth
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            audio = audio.set_sample_width(2)  # 16-bit
            
            # Apply noise reduction if audio is too quiet
            if audio.dBFS < -30:
                audio = audio + 10  # Increase volume by 10dB
            
            # Save as WAV
            wav_path = audio_path.replace('.ogg', '.wav')
            audio.export(wav_path, format="wav")
            
            print(f"✅ Audio converted to WAV format (16kHz, mono)")
            return wav_path
            
        except Exception as e:
            print(f"❌ Error converting audio: {str(e)}")
            raise


# Alternative implementation using Vosk for completely offline support
class VoskSpeechToTextService:
    def __init__(self):
        # Import vosk only if being used
        try:
            import vosk
            self.vosk = vosk
        except ImportError:
            print("❌ Vosk not installed. Run: pip install vosk")
            self.vosk = None
            
        # Setup models
        self.models = {}
        if self.vosk:
            self.models = {
                'en': self._setup_model('en'),
                'ur': self._setup_model('ur'),
                'hi': self._setup_model('hi')  # Hindi as fallback for Urdu
            }
    
    def _setup_model(self, language: str):
        """Setup Vosk model for language"""
        if not self.vosk:
            return None
            
        model_info = {
            'en': {
                'path': 'vosk-model-small-en-us-0.15',
                'url': 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip',
                'size': '40MB'
            },
            'ur': {
                'path': 'vosk-model-small-ur-0.22',
                'url': 'https://alphacephei.com/vosk/models/vosk-model-small-ur-0.22.zip',
                'size': '40MB'
            },
            'hi': {
                'path': 'vosk-model-small-hi-0.22',
                'url': 'https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip',
                'size': '42MB'
            }
        }
        
        info = model_info.get(language)
        if not info:
            return None
        
        model_path = info['path']
        
        # Check if model exists
        if not os.path.exists(model_path):
            print(f"📥 {language.upper()} model not found.")
            print(f"Please download from: {info['url']} ({info['size']})")
            print(f"Extract to: {model_path}")
            
            # Try to auto-download if possible
            self._try_download_model(info['url'], model_path)
            
            if not os.path.exists(model_path):
                return None
        
        try:
            print(f"✅ Loading {language.upper()} model...")
            return self.vosk.Model(model_path)
        except Exception as e:
            print(f"❌ Failed to load {language} model: {e}")
            return None
    
    def _try_download_model(self, url: str, path: str):
        """Try to automatically download and extract model"""
        try:
            print(f"🔄 Attempting to download model...")
            import zipfile
            import io
            
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                # Download and extract
                z = zipfile.ZipFile(io.BytesIO(response.content))
                z.extractall('.')
                print(f"✅ Model downloaded and extracted")
            else:
                print(f"❌ Failed to download model")
        except Exception as e:
            print(f"❌ Auto-download failed: {e}")
            print("Please download manually")
    
    def convert_voice_to_text(self, audio_url: str, language: str = "en") -> Optional[str]:
        """Convert voice to text using Vosk (offline)"""
        if not self.vosk:
            print("❌ Vosk not available")
            return None
            
        # Try primary language and fallbacks
        languages_to_try = []
        if language == "ur":
            languages_to_try = ["ur", "hi", "en"]  # Urdu → Hindi → English
        else:
            languages_to_try = [language, "en"]  # Primary → English
        
        for lang in languages_to_try:
            model = self.models.get(lang)
            if model:
                result = self._recognize_with_model(audio_url, model, lang)
                if result:
                    if lang != language:
                        return f"{result} [Fallback: {lang.upper()}]"
                    return result
        
        return None
    
    def _recognize_with_model(self, audio_url: str, model, language: str) -> Optional[str]:
        """Recognize speech using specific Vosk model"""
        try:
            # Download audio
            audio_data = self._download_audio(audio_url)
            if not audio_data:
                return None
            
            # Save and convert to WAV
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_audio:
                temp_audio.write(audio_data)
                temp_audio_path = temp_audio.name
            
            # Convert to 16kHz mono WAV
            audio = AudioSegment.from_file(temp_audio_path)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            
            wav_path = temp_audio_path.replace('.ogg', '.wav')
            audio.export(wav_path, format="wav", parameters=["-ac", "1"])
            
            # Recognize with Vosk
            rec = self.vosk.KaldiRecognizer(model, 16000)
            rec.SetWords(True)  # Enable word-level recognition
            
            results = []
            with open(wav_path, 'rb') as wf:
                while True:
                    data = wf.read(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        if result.get('text'):
                            results.append(result['text'])
                
                # Get final result
                final_result = json.loads(rec.FinalResult())
                if final_result.get('text'):
                    results.append(final_result['text'])
            
            # Clean up
            os.unlink(temp_audio_path)
            os.unlink(wav_path)
            
            # Combine all text
            text = ' '.join(results)
            return text.strip() if text else None
            
        except Exception as e:
            print(f"❌ Error in Vosk recognition ({language}): {str(e)}")
            return None
    
    def _download_audio(self, audio_url: str) -> Optional[bytes]:
        """Download audio file"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(audio_url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.content
            return None
        except:
            return None


# Hybrid service that tries online first, then offline
class HybridSpeechToTextService:
    def __init__(self):
        self.online_service = FreeSpeechToTextService()
        self.offline_service = VoskSpeechToTextService()
        
    def convert_voice_to_text(self, audio_url: str, language: str = "en") -> Optional[str]:
        """Try online service first, fallback to offline if needed"""
        # Try online first (better accuracy)
        print("🌐 Trying online speech recognition...")
        result = self.online_service.convert_voice_to_text(audio_url, language)
        
        if result:
            return result
        
        # Fallback to offline
        if self.offline_service.vosk:
            print("💾 Trying offline speech recognition...")
            result = self.offline_service.convert_voice_to_text(audio_url, language)
            if result:
                return f"{result} [Offline]"
        
        return None


```


---


### services\state_manager.py {#services\state_manager-py}

**File Size:** 1500 bytes

**File Path:** `services\state_manager.py`


```python

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


```


---


### services\webhook_notification_service.py {#services\webhook_notification_service-py}

**File Size:** 3300 bytes

**File Path:** `services\webhook_notification_service.py`


```python

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from config.database import db
from models.webhook_notification import NotificationType, WebhookNotification
import asyncio

class WebhookNotificationService:
    def __init__(self):
        self.collection = db.notifications
        
    def create_order_notification(self, order_data: Dict) -> bool:
        """Create a new order notification"""
        try:
            notification = WebhookNotification(
                notification_type=NotificationType.ORDER_CONFIRMED,
                data={
                    "order_number": order_data.get("order_number"),
                    "customer_name": order_data.get("user_name"),
                    "phone_number": order_data.get("phone_number"),
                    "total": order_data.get("total"),
                    "items": order_data.get("items", []),
                    "delivery_address": order_data.get("delivery_address"),
                    "delivery_city": order_data.get("delivery_city"),
                    "created_at": order_data.get("created_at", datetime.utcnow())
                }
            )
            
            result = self.collection.insert_one(notification.to_dict())
            print(f"✅ Order notification created: {notification.data['order_number']}")
            return bool(result.inserted_id)
            
        except Exception as e:
            print(f"❌ Error creating notification: {e}")
            return False
    
    def get_unread_notifications(self, limit: int = 10) -> List[Dict]:
        """Get unread notifications"""
        try:
            notifications = list(self.collection.find(
                {"read": False}
            ).sort("created_at", -1).limit(limit))
            
            # Convert ObjectId to string
            for notif in notifications:
                notif["_id"] = str(notif["_id"])
                
            return notifications
        except Exception as e:
            print(f"Error fetching notifications: {e}")
            return []
    
    def mark_as_read(self, notification_ids: List[str]) -> int:
        """Mark notifications as read"""
        from bson import ObjectId
        try:
            object_ids = [ObjectId(id) for id in notification_ids]
            result = self.collection.update_many(
                {"_id": {"$in": object_ids}},
                {
                    "$set": {
                        "read": True,
                        "read_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count
        except Exception as e:
            print(f"Error marking notifications as read: {e}")
            return 0
    
    def get_recent_count(self, minutes: int = 5) -> int:
        """Get count of recent notifications"""
        try:
            since = datetime.utcnow() - timedelta(minutes=minutes)
            count = self.collection.count_documents({
                "created_at": {"$gte": since},
                "read": False
            })
            return count
        except:
            return 0

# Global instance
webhook_notification_service = WebhookNotificationService()


```


---


### services\websocket_service.py {#services\websocket_service-py}

**File Size:** 3131 bytes

**File Path:** `services\websocket_service.py`


```python

import socketio
from typing import Dict, Set
import json
from datetime import datetime

# Create async Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Create ASGI app
socket_app = socketio.ASGIApp(
    sio,
    socketio_path='/socket.io/'
)

class WebSocketManager:
    def __init__(self):
        self.connected_clients: Dict[str, Set[str]] = {}
        self.user_sessions: Dict[str, str] = {}  # session_id -> user_id
        
    async def connect_client(self, sid: str, user_id: str = None):
        """Register a new client connection"""
        if user_id:
            if user_id not in self.connected_clients:
                self.connected_clients[user_id] = set()
            self.connected_clients[user_id].add(sid)
            self.user_sessions[sid] = user_id
            print(f"Client {sid} connected for user {user_id}")
            
    async def disconnect_client(self, sid: str):
        """Remove client connection"""
        user_id = self.user_sessions.get(sid)
        if user_id and user_id in self.connected_clients:
            self.connected_clients[user_id].discard(sid)
            if not self.connected_clients[user_id]:
                del self.connected_clients[user_id]
        if sid in self.user_sessions:
            del self.user_sessions[sid]
        print(f"Client {sid} disconnected")
        
    async def emit_order_notification(self, order_data: dict):
        """Emit order notification to all connected staff/admin users"""
        notification = {
            'type': 'order_confirmed',
            'order': {
                'order_number': order_data.get('order_number'),
                'customer_name': order_data.get('user_name'),
                'total': order_data.get('total'),
                'items': order_data.get('items', []),
                'phone_number': order_data.get('phone_number'),
                'delivery_address': order_data.get('delivery_address'),
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        # Emit to all connected clients (you can filter by role if needed)
        await sio.emit('new_order', notification)
        print(f"Order notification sent for order {order_data.get('order_number')}")

# Create global instance
ws_manager = WebSocketManager()

# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    print(f"Client {sid} attempting to connect")
    await ws_manager.connect_client(sid)
    await sio.emit('connected', {'message': 'Connected to server'}, to=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    await ws_manager.disconnect_client(sid)

@sio.event
async def authenticate(sid, data):
    """Authenticate WebSocket connection"""
    user_id = data.get('user_id')
    if user_id:
        await ws_manager.connect_client(sid, user_id)
        await sio.emit('authenticated', {'status': 'success'}, to=sid)


```


---


### services\whatsapp_notification_service.py {#services\whatsapp_notification_service-py}

**File Size:** 3785 bytes

**File Path:** `services\whatsapp_notification_service.py`


```python

from whatsapp_api_client_python import API
from config.settings import settings
from typing import Optional
import asyncio

class WhatsAppNotificationService:
    def __init__(self):
        self.greenAPI = API.GreenAPI(
            idInstance=settings.WHATSAPP_INSTANCE_ID,
            apiTokenInstance=settings.WHATSAPP_TOKEN
        )
    
    def send_order_status_notification(self, phone_number: str, order_number: str, 
                                     status: str, customer_name: str, 
                                     estimated_time: Optional[int] = None,
                                     notes: Optional[str] = None) -> bool:
        """Send order status update to customer via WhatsApp"""
        try:
            # Format phone number for WhatsApp
            whatsapp_number = f"{phone_number}@c.us"
            
            # Create status-specific messages
            status_messages = {
                "preparing": f"""🍳 *Order Update*

Hi {customer_name}! 

Your order *#{order_number}* is now being *PREPARED* by our chef! 👨‍🍳

{f"⏱️ Estimated time: *{estimated_time} minutes*" if estimated_time else ""}
{f"📝 Note: {notes}" if notes else ""}

We'll notify you when it's ready!""",

                "ready": f"""✅ *Order Ready!*

Hi {customer_name}! 

Great news! Your order *#{order_number}* is *READY* and will be out for delivery soon! 📦

{f"⏱️ Estimated delivery time: *{estimated_time} minutes*" if estimated_time else ""}
{f"📝 Note: {notes}" if notes else ""}

Our delivery partner will be on their way shortly!""",

                "out_for_delivery": f"""🚗 *Out for Delivery!*

Hi {customer_name}! 

Your order *#{order_number}* is *ON THE WAY* to you! 🛵

{f"⏱️ Estimated arrival: *{estimated_time} minutes*" if estimated_time else ""}
{f"📝 Note: {notes}" if notes else ""}

Our delivery partner will call you upon arrival.""",

                "delivered": f"""✅ *Order Delivered!*

Hi {customer_name}! 

Your order *#{order_number}* has been *DELIVERED*! 🎉

{f"📝 Note: {notes}" if notes else ""}

Thank you for choosing us! We hope you enjoy your meal! 🍽️

_Rate your experience by replying with 1-5 stars ⭐_""",

                "cancelled": f"""❌ *Order Cancelled*

Hi {customer_name}, 

Your order *#{order_number}* has been *CANCELLED*.

{f"📝 Reason: {notes}" if notes else ""}

If you have any questions, please feel free to message us.

We hope to serve you again soon! 🙏"""
            }
            
            # Get the appropriate message
            message = status_messages.get(status)
            
            if not message:
                message = f"""📋 *Order Update*

Hi {customer_name}!

Your order *#{order_number}* status: *{status.upper()}*

{f"📝 Note: {notes}" if notes else ""}"""
            
            # Send the message
            response = self.greenAPI.sending.sendMessage(whatsapp_number, message)
            
            if response.data:
                print(f"✅ WhatsApp notification sent for order {order_number} - Status: {status}")
                return True
            else:
                print(f"❌ Failed to send WhatsApp notification: {response.error}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending WhatsApp notification: {str(e)}")
            return False
    
    async def send_order_status_notification_async(self, *args, **kwargs):
        """Async wrapper for sending notifications"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send_order_status_notification, *args, **kwargs)


```


---


### test_connection.py {#test_connection-py}

**File Size:** 2886 bytes

**File Path:** `test_connection.py`


```python

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


```


---


### test_gemini.py {#test_gemini-py}

**File Size:** 1631 bytes

**File Path:** `test_gemini.py`


```python

#!/usr/bin/env python3
"""
Test Gemini API connection
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_gemini_api():
    """Test Gemini API with current credentials"""
    api_key = os.getenv("GEMINI_API_KEY")
    base_url = os.getenv("GEMINI_BASE_URL")
    model_name = os.getenv("MODEL_NAME")
    
    print(f"Testing Gemini API...")
    print(f"API Key: {api_key[:20]}...")
    print(f"Base URL: {base_url}")
    print(f"Model: {model_name}")
    
    # Test API endpoint
    try:
        url = f"{base_url}chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": "Hello, this is a test message."}
            ],
            "max_tokens": 50
        }
        
        print(f"\n[TEST] Testing API endpoint: {url}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("[SUCCESS] Gemini API is working!")
            print(f"Response: {data}")
            return True
        else:
            print(f"[ERROR] API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return False

if __name__ == "__main__":
    test_gemini_api()


```


---


### test_whatsapp.py {#test_whatsapp-py}

**File Size:** 7894 bytes

**File Path:** `test_whatsapp.py`


```python

#!/usr/bin/env python3
"""
Test WhatsApp Green API connection
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_whatsapp_connection():
    """Test WhatsApp Green API connection and status"""
    instance_id = os.getenv("WHATSAPP_INSTANCE_ID")
    token = os.getenv("WHATSAPP_TOKEN")
    
    if not instance_id or not token:
        print("❌ Missing WhatsApp credentials in .env file")
        return False
    
    print(f"Testing WhatsApp connection...")
    print(f"Instance ID: {instance_id}")
    print(f"Token: {token[:20]}...")
    
    # Test 1: Check instance status
    try:
        status_url = f"https://api.green-api.com/waInstance{instance_id}/getStateInstance/{token}"
        print(f"\n[INFO] Checking instance status...")
        print(f"URL: {status_url}")
        
        response = requests.get(status_url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Instance Status: {data}")
            
            state = data.get('stateInstance')
            if state == 'authorized':
                print("✅ WhatsApp instance is authorized and ready!")
            elif state == 'notAuthorized':
                print("❌ WhatsApp instance is NOT authorized!")
                print("📱 Please scan QR code to authorize your WhatsApp instance")
                return False
            elif state == 'starting':
                print("🔄 WhatsApp instance is starting up...")
                print("⏳ Please wait a few minutes for the instance to fully start")
                print("📱 You may need to scan QR code if this is the first time")
                return False
            elif state == 'sleepMode':
                print("😴 WhatsApp instance is in sleep mode")
                print("💡 Send a message to wake it up or restart the instance")
                return False
            else:
                print(f"⚠️ Unknown instance state: {state}")
                print("📖 Possible states: authorized, notAuthorized, starting, sleepMode")
                
        else:
            print(f"❌ Failed to get instance status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking instance status: {str(e)}")
        return False
    
    # Test 2: Check webhook settings
    try:
        webhook_url = f"https://api.green-api.com/waInstance{instance_id}/getSettings/{token}"
        print(f"\n🔍 Checking webhook settings...")
        
        response = requests.get(webhook_url, timeout=10)
        if response.status_code == 200:
            settings = response.json()
            print(f"✅ Webhook Settings: {settings}")
            
            # Check if incoming webhooks are enabled
            if settings.get('incomingWebhook') == 'yes':
                print("✅ Incoming webhooks are enabled")
            else:
                print("⚠️ Incoming webhooks are disabled - this might cause issues")
                
        else:
            print(f"❌ Failed to get webhook settings: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking webhook settings: {str(e)}")
    
    # Test 3: Test receiving notifications
    try:
        receive_url = f"https://api.green-api.com/waInstance{instance_id}/receiveNotification/{token}"
        print(f"\n🔍 Testing notification receiving...")
        
        response = requests.get(receive_url, timeout=5)
        print(f"Receive Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data is None:
                print("✅ No pending notifications (this is normal)")
            else:
                print(f"📨 Received notification: {data}")
        else:
            print(f"❌ Failed to receive notifications: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing notifications: {str(e)}")

    return True

def get_qr_code():
    """Get QR code for WhatsApp authorization"""
    instance_id = os.getenv("WHATSAPP_INSTANCE_ID")
    token = os.getenv("WHATSAPP_TOKEN")

    try:
        qr_url = f"https://api.green-api.com/waInstance{instance_id}/qr/{token}"
        print(f"\n📱 Getting QR code for authorization...")
        print(f"QR URL: {qr_url}")

        response = requests.get(qr_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('type') == 'qrCode':
                print("✅ QR Code received!")
                print(f"📱 QR Code: {data.get('message')}")
                print("\n🔗 Open this link in your browser to see the QR code:")
                print(f"   {qr_url}")
                print("\n📱 Steps to authorize:")
                print("1. Open WhatsApp on your phone")
                print("2. Go to Settings > Linked Devices")
                print("3. Tap 'Link a Device'")
                print("4. Scan the QR code from the URL above")
                return True
            else:
                print(f"⚠️ Unexpected QR response: {data}")
                return False
        else:
            print(f"❌ Failed to get QR code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error getting QR code: {str(e)}")
        return False

def test_whatsapp_library():
    """Test if the WhatsApp library is working"""
    try:
        from whatsapp_chatbot_python import GreenAPIBot
        print("[SUCCESS] whatsapp_chatbot_python library imported successfully")
        
        instance_id = os.getenv("WHATSAPP_INSTANCE_ID")
        token = os.getenv("WHATSAPP_TOKEN")
        
        # Try to create bot instance
        bot = GreenAPIBot(instance_id, token)
        print("[SUCCESS] GreenAPIBot instance created successfully")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] Failed to import whatsapp_chatbot_python: {e}")
        print("[INFO] Try: pip install whatsapp-chatbot-python")
        return False
    except Exception as e:
        print(f"[ERROR] Error creating bot instance: {e}")
        return False

def main():
    print("WhatsApp Green API Connection Test")
    print("=" * 50)
    
    # Test library import
    library_ok = test_whatsapp_library()
    
    print("\n" + "=" * 50)
    
    # Test API connection
    if library_ok:
        api_ok = test_whatsapp_connection()
    else:
        api_ok = False
    
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"Library Import: {'✅ OK' if library_ok else '❌ Failed'}")
    print(f"API Connection: {'✅ OK' if api_ok else '❌ Failed'}")
    
    if not library_ok or not api_ok:
        print("\n🔧 Troubleshooting:")
        if not library_ok:
            print("1. Install WhatsApp library: pip install whatsapp-chatbot-python")
        if not api_ok:
            print("2. Check your WhatsApp instance authorization")
            print("3. Verify WHATSAPP_INSTANCE_ID and WHATSAPP_TOKEN in .env")
            print("4. Make sure your Green API account is active")

            # Offer to get QR code
            print("\n📱 Would you like to get the QR code for authorization?")
            try:
                choice = input("Enter 'y' to get QR code, or any other key to skip: ").lower()
                if choice == 'y':
                    get_qr_code()
            except KeyboardInterrupt:
                print("\n👋 Cancelled by user")

if __name__ == "__main__":
    main()


```


---


### tools\menu_tools.py {#tools\menu_tools-py}

**File Size:** 6345 bytes

**File Path:** `tools\menu_tools.py`


```python

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
            # Try to use the existing db if available
            from config.database import db
            return db
        
        # Create a new connection
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        
        # Test connection
        client.admin.command('ping')
        
        # Return the restaurant_db database
        return client['restaurant_db']
        
    except Exception as e:
        print(f"❌ Error creating database connection: {e}")
        # Fallback to existing db
        try:
            from config.database import db
            return db
        except:
            return None

@function_tool
def show_menu(category: str = "all") -> str:
    """Shows restaurant menu with proper WhatsApp formatting and spacing"""
    try:
        # Get a fresh database connection
        database = get_db_connection()
        if database is None:  # <- FIXED: Use 'is None' instead of 'not database'
            print("❌ Could not establish database connection")
            return "🍽️ I'm having trouble accessing the menu. Please try again in a moment."
        
        # Get the menu collection
        menu_collection = database.menu if hasattr(database, 'menu') else database['menu']
        
        # Debug: Count items
        total_count = menu_collection.count_documents({})
        print(f"📊 Total menu items found: {total_count}")
        
        # Filter by category if provided (case-insensitive), else show all
        query = {}
        if category and category.lower() != "all":
            query = {"category": {"$regex": f"^{category}$", "$options": "i"}}
        
        # Get items with explicit list conversion
        cursor = menu_collection.find(query)
        items = list(cursor.sort([("category", 1), ("id", 1)]))
        
        print(f"📋 Retrieved {len(items)} items from menu")
        
        if not items:
            # If no items found but we know there should be some
            if total_count > 0:
                print(f"⚠️ Query returned no items but {total_count} exist in collection")
                # Try without any query
                items = list(menu_collection.find({}).sort([("category", 1), ("id", 1)]))
                print(f"📋 Retry without query: {len(items)} items")
            
            if not items:
                print("❌ No menu items found in database")
                # Try to initialize menu if empty
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
        
        # Build menu text
        menu_text = "🍽️ *RESTAURANT MENU* 🍽️\n"
        menu_text += "━━━━━━━━━━━━━━━━━━\n\n"
        
        current_category = ""
        for item in items:
            # Ensure all fields exist with defaults
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
        
        # Return a user-friendly message
        return "🍽️ I'm having trouble loading the menu right now. Please try typing *'menu'* again or contact support if the issue persists."

# Add a helper function to test menu availability
@function_tool
def test_menu_connection() -> str:
    """Test if menu can be accessed properly"""
    try:
        database = get_db_connection()
        if database is None:  # <- FIXED: Use 'is None' instead of 'not database'
            return "❌ Database connection failed"
        
        menu_collection = database.menu if hasattr(database, 'menu') else database['menu']
        count = menu_collection.count_documents({})
        
        if count > 0:
            # Get one item as sample
            sample = menu_collection.find_one()
            return f"✅ Menu connection OK - {count} items found. Sample: {sample.get('name', 'Unknown')}"
        else:
            return "⚠️ Menu is empty"
            
    except Exception as e:
        return f"❌ Error testing menu: {str(e)}"


```


---


### tools\order_tools.py {#tools\order_tools-py}

**File Size:** 8241 bytes

**File Path:** `tools\order_tools.py`


```python

from typing import List, Dict
from datetime import datetime
from agents import function_tool
from config.database import db
from models.order import Order, OrderItem
from utils.phone_utils import clean_phone_number
import json

class OrderManager:
    user_states: Dict[str, Dict] = {}
    
    @classmethod
    def get_or_create_order(cls, phone_number: str) -> Order:
        """Get or create order with consistent phone handling"""
        cleaned_phone = clean_phone_number(phone_number)
        
        if cleaned_phone not in cls.user_states:
            cls.user_states[cleaned_phone] = {}
            
        if 'current_order' not in cls.user_states[cleaned_phone]:
            cls.user_states[cleaned_phone]['current_order'] = Order(cleaned_phone)
            
        return cls.user_states[cleaned_phone]['current_order']
    
    @classmethod
    def clear_order(cls, phone_number: str):
        """Clear order for a user"""
        cleaned_phone = clean_phone_number(phone_number)
        
        if cleaned_phone in cls.user_states:
            cls.user_states[cleaned_phone]['current_order'] = Order(cleaned_phone)

@function_tool
def add_to_order(phone_number: str, item_ids: List[int], quantities: List[int] = None) -> str:
    """Adds items to order with better formatting"""
    try:
        cleaned_phone = clean_phone_number(phone_number)
        
        # Verify user exists
        user = db.users.find_one({"phone_number": cleaned_phone})
        if not user:
            return "❌ Please complete registration first."
            
        if quantities is None:
            quantities = [1] * len(item_ids)
            
        order = OrderManager.get_or_create_order(cleaned_phone)
        order_summary = "✅ *Added to your order:*\n\n"
        items_added = 0
        
        for item_id, quantity in zip(item_ids, quantities):
            if quantity <= 0:
                continue
                
            item = db.menu.find_one({"id": item_id})
            if item:
                # Create OrderItem and add to order
                order_item = OrderItem(
                    id=item['id'],
                    name=item['name'],
                    price=item['price'],
                    quantity=quantity
                )
                order.add_item(order_item)
                
                order_summary += f"• {quantity}x *{item['name']}* - *PKR{item['price'] * quantity:.2f}*\n"
                items_added += 1
        
        if items_added > 0:
            order_summary += f"\n💰 *Current Total: PKR{order.total:.2f}*\n\n"
            order_summary += "_Send *'view order'* to see cart_\n"
            order_summary += "_Send *'menu'* for more items_\n"
            order_summary += "_Send *'confirm'* when ready_"
        else:
            order_summary = "❌ No items added. Please check item numbers."
            
        return order_summary
        
    except Exception as e:
        return f"❌ Error: Please try again."

@function_tool
def view_current_order(phone_number: str) -> str:
    """Shows the current order for the user"""
    try:
        cleaned_phone = clean_phone_number(phone_number)
        
        order = OrderManager.get_or_create_order(cleaned_phone)
        if not order.items:
            return "🛒 *Your cart is empty*\n\n_Type_ *'menu'* _to see our offerings!_"
        
        order_text = "🛒 *YOUR CURRENT ORDER:*\n"
        order_text += "━━━━━━━━━━━━━━━━━━\n"
        
        for item in order.items:
            order_text += f"• {item.quantity}x *{item.name}* - *PKR{item.subtotal:.2f}*\n"
        
        order_text += "━━━━━━━━━━━━━━━━━━\n"
        order_text += f"💰 *TOTAL: PKR{order.total:.2f}*\n\n"
        order_text += "_Type_ *'confirm order'* _to place this order_\n"
        order_text += "_Type_ *'menu'* _to add more items_"
        
        return order_text
        
    except Exception as e:
        print(f"Error in view_current_order: {str(e)}")
        return f"❌ Error viewing order: {str(e)}"

@function_tool
def confirm_order(phone_number: str, delivery_notes: str = "") -> str:
    """Confirms and saves the order with proper error handling and notifications"""
    try:
        cleaned_phone = clean_phone_number(phone_number)
        
        # Check user exists
        user = db.users.find_one({"phone_number": cleaned_phone})
        if not user:
            return "⚠ Please complete registration before confirming your order."
        
        # Get current order
        order = OrderManager.get_or_create_order(cleaned_phone)
        if not order.items:
            return "⚠ Your cart is empty. Please add items before confirming!"
        
        # Generate simple order number
        order_count = db.orders.count_documents({})
        order_number = f"ORD{order_count + 1:05d}"
        
        # Create order document
        order_doc = {
            "phone_number": cleaned_phone,
            "user_name": user.get('name', 'Customer'),
            "items": [{
                'id': item.id,
                'name': item.name,
                'price': item.price,
                'quantity': item.quantity,
                'subtotal': item.subtotal
            } for item in order.items],
            "total": order.total,
            "delivery_address": user.get('address', ''),
            "delivery_city": user.get('city', ''),
            "delivery_postal": user.get('postal_code', ''),
            "delivery_notes": delivery_notes or "",
            "status": "confirmed",
            "created_at": datetime.utcnow(),
            "order_number": order_number
        }
        
        print(f"Attempting to save order: {order_number}")
        print(f"Order document: {order_doc}")
        
        # Save to database
        try:
            result = db.orders.insert_one(order_doc)
            
            if result.inserted_id:
                print(f"✅ Order saved successfully! ID: {result.inserted_id}")
                
                # Create notification using the webhook notification service
                from services.webhook_notification_service import webhook_notification_service
                webhook_notification_service.create_order_notification(order_doc)
                
                # Clear only after successful save
                OrderManager.clear_order(cleaned_phone)
            else:
                print("❌ Failed to save order - no inserted_id returned")
                return "⚠ Failed to save order. Please try again."
                
        except Exception as e:
            print(f"❌ Database save error: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"⚠ Error saving order: {str(e)}"
        
        # Format WhatsApp confirmation
        confirmation = "✅ *ORDER CONFIRMED!*\n"
        confirmation += "━━━━━━━━━━━━━━━━━━\n\n"
        confirmation += f"📋 *Order #:* {order_number}\n"
        confirmation += f"👤 *Customer:* {user['name']}\n"
        confirmation += f"📍 *Delivery:* {user['address']}, {user['city']}\n"
        if delivery_notes:
            confirmation += f"📝 *Notes:* {delivery_notes}\n"
        
        confirmation += "\n*ORDER DETAILS:*\n"
        for item in order.items:
            confirmation += f"• {item.quantity}x *{item.name}* - *PKR{item.subtotal:.2f}*\n"
        
        confirmation += f"\n💰 *TOTAL: PKR{order.total:.2f}*\n"
        confirmation += "\n⏱ *Estimated delivery:* 30-45 minutes\n"
        confirmation += "📞 We'll call if needed\n\n"
        confirmation += "*Thank you for your order!* 🙏"
        
        return confirmation
        
    except Exception as e:
        print(f"❌ Critical error in confirm_order: {str(e)}")
        import traceback
        traceback.print_exc()
        return "⚠ Critical error. Your order was not processed. Please try again."


```


---


### tools\registration_tools.py {#tools\registration_tools-py}

**File Size:** 2871 bytes

**File Path:** `tools\registration_tools.py`


```python

from datetime import datetime
from agents import function_tool
from config.database import db
from utils.phone_utils import clean_phone_number

@function_tool
def validate_and_save_user(phone_number: str, name: str, address: str, city: str, postal_code: str = "") -> str:
    """Saves user information with minimal validation - let the LLM handle validation logic"""
    try:
        cleaned_phone = clean_phone_number(phone_number)

        cleaned_name = name.strip() if name else ""
        cleaned_address = address.strip() if address else ""
        cleaned_city = city.strip() if city else ""
        cleaned_postal = postal_code.strip() if postal_code else ""

        if not cleaned_name:
            return " ⚠ Name is required for registration."
        if not cleaned_address:
            return " ⚠ Address is required for delivery."
        if not cleaned_city:
            return " ⚠ City is required for delivery."

        user_doc = {
            "phone_number": cleaned_phone,
            "name": cleaned_name,
            "address": cleaned_address,
            "city": cleaned_city,
            "postal_code": cleaned_postal,
            "is_verified": True,
            "is_active": True,
            "updated_at": datetime.utcnow(),
        }

        existing = db.users.find_one({"phone_number": cleaned_phone})
        if existing:
            db.users.update_one({"phone_number": cleaned_phone}, {"$set": user_doc})
        else:
            user_doc["created_at"] = datetime.utcnow()
            user_doc.setdefault("role", "customer")
            db.users.update_one({"phone_number": cleaned_phone}, {"$set": user_doc}, upsert=True)

        return f""" ✅ *Registration Successful!*
Welcome *{cleaned_name}*! 🎉

Your delivery details:
📍 *Address:* {cleaned_address}
🏙 *City:* {cleaned_city}{f"""
📮 *Postal Code:* {cleaned_postal}""" if cleaned_postal else ""}

You're all set! I'll show you our menu now... 🍕 """
    except Exception as e:
        print(f"Error in validate_and_save_user: {str(e)}")
        return " ⚠ Sorry, there was an error saving your details. Please try again."

@function_tool
def validate_name(name: str) -> str:
    if not name or not name.strip():
        return " ⚠ Please provide a name."
    return f" ✅ Name '{name.strip()}' looks good!"

@function_tool
def validate_address(address: str, city: str, postal_code: str = "") -> str:
    if not address or not address.strip():
        return " ⚠ Please provide an address."
    if not city or not city.strip():
        return " ⚠ Please provide a city."
    return f""" ✅ Address looks complete!
📍 *Address:* {address.strip()}
🏙 *City:* {city.strip()}{f"""
📮 *Postal Code:* {postal_code.strip()}""" if postal_code and postal_code.strip() else ""}"""


```


---


### utils\phone_utils.py {#utils\phone_utils-py}

**File Size:** 223 bytes

**File Path:** `utils\phone_utils.py`


```python

def clean_phone_number(phone: str) -> str:
    """Centralized phone number cleaning - removes WhatsApp suffixes"""
    if not phone:
        return ""
    return phone.replace("@c.us", "").replace("@g.us", "").strip()


```


---
