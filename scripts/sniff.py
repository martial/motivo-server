import asyncio
import websockets
import logging

logging.basicConfig(level=logging.DEBUG)

async def listen_smpl():
    uri = "wss://ws-motivo.doesnotexist.club:8443/smpl"  # Try port 8443
    async with websockets.connect(uri) as websocket:
        print("Connected!")
        while True:
            try:
                message = await websocket.recv()
                print(f"Received: {message}")
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break

asyncio.run(listen_smpl())