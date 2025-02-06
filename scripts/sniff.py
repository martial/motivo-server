import asyncio
import websockets
import logging
import json

logging.basicConfig(level=logging.DEBUG)

async def listen_smpl():
    uri = "ws://51.159.163.145:8765"  # Try port 8443
    async with websockets.connect(uri) as websocket:
        print("Connected!")
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                if "pose" in data and "trans" in data:
                    print(f"\nTimestamp: {data.get('timestamp', 'N/A')}")
                    print(f"Pose: {data['pose']}")
                    print(f"Trans: {data['trans']}")
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break

asyncio.run(listen_smpl())