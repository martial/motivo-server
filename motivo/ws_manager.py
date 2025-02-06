import asyncio
from typing import Set, Dict, Any
import json
import websockets
from datetime import datetime

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
            try:
                self.connected_clients.remove(websocket)
                # Remove unique identifier
                client_id = str(id(websocket))
                self.unique_clients.discard(client_id)
                print(f"Client removed. Total connections: {len(self.connected_clients)}")
            except KeyError:
                print("Warning: Attempted to remove non-existent client")
    
    async def broadcast(self, message: Dict[Any, Any]) -> None:
        """Safely broadcast a message to all connected clients"""
        if not isinstance(message, str):
            message = json.dumps(message)

        # Create a copy of connected clients to avoid modification during iteration
        async with self._lock:
            clients = self.connected_clients.copy()

        # Send to all clients, handling disconnections
        disconnected = set()
        for websocket in clients:
            try:
                await websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(websocket)
            except Exception as e:
                print(f"Error broadcasting to client: {str(e)}")
                disconnected.add(websocket)

        # Remove disconnected clients
        for websocket in disconnected:
            await self.remove_client(websocket)
    
    def get_stats(self) -> Dict[str, int]:
        """Get current connection statistics"""
        return {
            "connected_clients": len(self.connected_clients),
            "unique_clients": len(self.unique_clients)
        } 