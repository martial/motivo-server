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
        try:
            if not isinstance(message, str):
                message = json.dumps(message)
        except Exception:
            return

        if not self.connected_clients:
            return

        # Use a list to avoid "set changed size during iteration" errors
        for websocket in list(self.connected_clients):
            try:
                await websocket.send(message)
            except:  # Catch any possible error
                self.connected_clients.discard(websocket)
                continue

    def get_stats(self) -> Dict[str, int]:
        """Get current connection statistics"""
        return {
            "connected_clients": len(self.connected_clients)
        } 