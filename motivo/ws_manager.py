import asyncio
from typing import Set, Dict, Any
import json
import websockets
from datetime import datetime

class WebSocketManager:
    def __init__(self):
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()

    async def broadcast(self, message: Dict[Any, Any]) -> None:
        """Broadcast a message to all connected clients"""
        if not isinstance(message, str):
            try:
                message = json.dumps(message)
            except Exception as e:
                print(f"Error serializing message: {str(e)}")
                return

        if not self.connected_clients:
            return

        # Just try to send to each client, no fancy checks
        for websocket in self.connected_clients.copy():
            try:
                await websocket.send(message)
            except Exception as e:
                print(f"Error sending to client: {str(e)}")
                self.connected_clients.discard(websocket)

    def get_stats(self) -> Dict[str, int]:
        """Get current connection statistics"""
        return {
            "connected_clients": len(self.connected_clients)
        } 