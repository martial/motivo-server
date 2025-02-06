import asyncio
from typing import Set, Dict, Any
import json
import websockets
from datetime import datetime
from websockets.asyncio.server import broadcast

class WebSocketManager:
    def __init__(self):
        self._lock = asyncio.Lock()
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.unique_clients: Set[str] = set()
    
    async def add_client(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """Safely add a new client connection"""
        async with self._lock:
            self.connected_clients.add(websocket)
            # Add unique identifier (using websocket id or connection info)
            client_id = str(id(websocket))
            self.unique_clients.add(client_id)
            print(f"Client added. Total connections: {len(self.connected_clients)}")
    
    async def remove_client(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """Safely remove a client connection"""
        async with self._lock:
            self.connected_clients.discard(websocket)
            # Remove unique identifier
            client_id = str(id(websocket))
            self.unique_clients.discard(client_id)
            print(f"Client removed. Total connections: {len(self.connected_clients)}")
    
    async def broadcast(self, message: Dict[Any, Any]) -> None:
        """Efficiently broadcast a message to all connected clients"""
        if not isinstance(message, str):
            message = json.dumps(message)
            
        async with self._lock:
            # Use the built-in broadcast helper
            broadcast(self.connected_clients, message)
    
    def get_stats(self) -> Dict[str, int]:
        """Get current connection statistics"""
        return {
            "connected_clients": len(self.connected_clients),
            "unique_clients": len(self.unique_clients)
        } 