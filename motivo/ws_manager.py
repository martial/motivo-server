import websockets
from typing import Set, Dict, Any
import json
from datetime import datetime

class WebSocketManager:
    def __init__(self):
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.unique_clients: Set[str] = set()
    
    def add_client(self, websocket: websockets.WebSocketServerProtocol):
        """Add new client connection and track IP"""
        client_ip = websocket.remote_address[0]
        self.connected_clients.add(websocket)
        self.unique_clients.add(client_ip)
        print(f"\nNew client connected:")
        print(f"Connected clients: {len(self.connected_clients)}")
        print(f"Unique IPs: {len(self.unique_clients)}")
    
    def remove_client(self, websocket: websockets.WebSocketServerProtocol):
        """Remove client connection and update IP tracking"""
        client_ip = websocket.remote_address[0]
        self.connected_clients.remove(websocket)
        # Only remove IP if no other connections from that IP
        if not any(ws.remote_address[0] == client_ip for ws in self.connected_clients):
            self.unique_clients.remove(client_ip)
        print(f"\nClient disconnected:")
        print(f"Connected clients: {len(self.connected_clients)}")
        print(f"Unique IPs: {len(self.unique_clients)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        disconnected_clients = set()
        
        for client in self.connected_clients:
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.remove_client(client)
    
    def get_stats(self) -> Dict[str, int]:
        """Get current connection statistics"""
        return {
            "connected_clients": len(self.connected_clients),
            "unique_clients": len(self.unique_clients)
        } 