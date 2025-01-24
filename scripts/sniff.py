import asyncio
import aiohttp
import socket
from datetime import datetime

async def websocket_monitor(uri, udp_host, udp_port):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"UDP socket created for {udp_host}:{udp_port}")
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                print(f"Connecting to {uri}")
                try:
                    async with session.ws_connect(uri, timeout=30) as ws:
                        print(f"Successfully connected to {uri}")
                        print("Waiting for messages...")
                        
                        async for msg in ws:
                            print(f"Received message type: {msg.type}")  # Debug message type
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                timestamp = datetime.now().isoformat()
                                formatted_data = f"[{timestamp}] {msg.data}"
                                
                                try:
                                    udp_socket.sendto(formatted_data.encode(), (udp_host, udp_port))
                                    print(f"Forwarded: {formatted_data}")
                                except socket.error as sock_err:
                                    print(f"UDP socket error: {sock_err}")
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                print(f"WebSocket error: {ws.exception()}")
                                break
                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                print("WebSocket connection closed")
                                break
                            else:
                                print(f"Unhandled message type: {msg.type}, data: {msg.data}")  # Debug unknown messages
                except aiohttp.ClientError as ws_err:
                    print(f"WebSocket connection failed: {ws_err}")
                    raise  # Re-raise to trigger the outer exception handler
                        
        except Exception as e:
            print(f"Connection error: {str(e)}")
            print("Retrying in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    WS_URI = "wss://ws-motivo.doesnotexist.club"
    UDP_HOST = "127.0.0.1"
    UDP_PORT = 9999
    
    try:
        asyncio.run(websocket_monitor(WS_URI, UDP_HOST, UDP_PORT))
    except KeyboardInterrupt:
        print("\nScript terminated by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")