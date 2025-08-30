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
