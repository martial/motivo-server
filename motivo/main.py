import torch
import asyncio
import websockets
import json
import cv2
from concurrent.futures import ThreadPoolExecutor
from metamotivo.fb_cpr.huggingface import FBcprModel
import os
from datetime import datetime
import numpy as np
from frame_utils import save_frame_data
from utils.smpl_utils import qpos_to_smpl, smpl_to_qpose

from env_setup import setup_environment
from buffer_utils import download_buffer
from reward_context import compute_reward_context, compute_q_value
from task_rewards import print_model_info, list_model_body_names, print_available_rewards
from humenv import rewards as humenv_rewards
from typing import Dict, Any
from frame_utils import FrameRecorder
from cache_utils import RewardContextCache
from ws_manager import WebSocketManager
from utils.utils import normalize_q_value
from display_utils import DisplayManager
from message_handler import MessageHandler
import traceback

# Environment variables
BACKEND_DOMAIN = os.getenv("VITE_BACKEND_DOMAIN", "localhost")
WS_PORT = os.getenv("VITE_WS_PORT", 8765)
API_PORT = os.getenv("VITE_API_PORT", 5000)
WEBSERVER_PORT = os.getenv("VITE_WEBSERVER_PORT", 5002)
VITE_WS_URL = os.getenv("VITE_WS_URL", f"ws://{BACKEND_DOMAIN}:{WS_PORT}")

# Application state
class AppState:
    def __init__(self):
        self.model = None
        self.env = None
        self.buffer_data = None
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        self.ws_manager = WebSocketManager()
        self.context_cache = None  # Initialize later when we have model, env, and buffer_data
        self.display_manager = DisplayManager()
        self.message_handler = None

    def initialize(self, model, env, buffer_data):
        self.model = model
        self.env = env
        self.buffer_data = buffer_data
        # Create cache with all required components
        self.context_cache = RewardContextCache(model=model, env=env, buffer_data=buffer_data)
        self.message_handler = MessageHandler(model, env, self.ws_manager, self.context_cache)
        self.message_handler.set_buffer_data(buffer_data)

    async def get_reward_context(self, reward_config):
        """Async wrapper for reward context computation"""
        try:
            self.message_handler.is_computing_reward = True
            print("\n=== Reward Context Computation ===")
            print("Computing... ⚙️")
            
            # Notify clients that computation started
            await self.ws_manager.broadcast({
                "type": "reward_computation",
                "status": "started",
                "timestamp": datetime.now().isoformat()
            })
            
            # Using asyncio.to_thread instead of ThreadPoolExecutor
            z = await asyncio.to_thread(
                compute_reward_context,
                reward_config,
                self.env,
                self.model,
                self.buffer_data
            )
            
            # Notify clients that computation is complete
            await self.ws_manager.broadcast({
                "type": "reward_computation",
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            })
            
            return z
        finally:
            self.message_handler.is_computing_reward = False
            print("✅ Computation complete!")

app_state = AppState()

async def handle_websocket(websocket):
    """Handle websocket connections"""
    print("\n=== New WebSocket Connection Established ===")
    app_state.ws_manager.connected_clients.add(websocket)
    print(f"Total connections: {len(app_state.ws_manager.connected_clients)}")
    
    try:
        async for message in websocket:
            await app_state.message_handler.handle_message(websocket, message)
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        app_state.ws_manager.connected_clients.discard(websocket)
        print(f"Client disconnected. Total connections: {len(app_state.ws_manager.connected_clients)}")

async def broadcast_pose(pose_data):
    """Broadcast pose data to all connected clients"""
    await app_state.ws_manager.broadcast(pose_data)

async def run_simulation():
    """Continuous simulation loop"""
    observation, _ = app_state.env.reset()
    
    while True:
        # Get action and step environment
        current_z = app_state.message_handler.get_current_z()
        action = app_state.model.act(observation, current_z, mean=True)
        q_value = compute_q_value(app_state.model, observation, current_z, action)
        q_percentage = normalize_q_value(q_value)
        observation, _, terminated, truncated, _ = app_state.env.step(action.cpu().numpy().ravel())
        
        # Broadcast pose data using WebSocketManager
        try:
            qpos = app_state.env.unwrapped.data.qpos
            pose, trans, positions, position_names = qpos_to_smpl(qpos, app_state.env.unwrapped.model)
            
            pose_data = {
                "type": "smpl_update",
                "pose": pose.tolist(),
                "trans": trans.tolist(),
                "positions": [pos.tolist() for pos in positions],
                "qpos": qpos.tolist(),
                "timestamp": datetime.now().isoformat(),
                "position_names": position_names
            }
            
            await app_state.ws_manager.broadcast(pose_data)
            
        except Exception as e:
            print(f"Error broadcasting pose data: {str(e)}")
            traceback.print_exc()
        
        # Render and display frame
        frame = app_state.env.render()
        resized_frame = app_state.display_manager.show_frame(
            frame,
            q_percentage=q_percentage,
            is_computing=app_state.message_handler.is_computing_reward
        )
        cv2.imwrite('../output.jpg', resized_frame)
        
        # Check for key presses
        should_quit, should_save = app_state.display_manager.check_key()
        if should_quit:
            break
        elif should_save:
            try:
                env_data = app_state.env.unwrapped.data
                save_frame_data(
                    frame=frame,
                    qpos=env_data.qpos.copy(),
                    qvel=env_data.qvel.copy(),
                    env=app_state.env
                )
                print("Frame saved! 📸")
            except Exception as e:
                print("Error during frame save:", str(e))
        
        if terminated:
            observation, _ = app_state.env.reset()
        
        await asyncio.sleep(1/60)  # 60 FPS target

async def main():
    """Main function"""
    try:
      
        # Device selection with CUDA support
        if torch.cuda.is_available():
            device = "cuda"
            torch.backends.cudnn.benchmark = True
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
        print(f"Using device: {device}")
        
        print("Loading model and environment...")
        model_name = "metamotivo-M-1"
        model = FBcprModel.from_pretrained(f"facebook/{model_name}")
        model.to(device)
        model.eval()
        
        env = setup_environment(device)
        buffer_data = download_buffer(model_name=model_name)
        
        # Initialize application state
        app_state.initialize(model, env, buffer_data)
        
        # Get default context from cache or compute if needed
        default_config = {
            'rewards': [
                { 'name': 'move-ego', 'move_speed': 0.0, 'stand_height': 1.4 }
            ],
            'weights': [1.0]
        }
        
        # Try to get from cache first
        cache_key = app_state.context_cache.get_cache_key(default_config)
        default_z = app_state.context_cache._get_cached_context_impl(cache_key)
        
        if default_z is None:
            print("\nDefault context not found in cache, computing...")
            default_z = await app_state.get_reward_context(default_config)
        else:
            print("\nUsing cached default context")
            
        if default_z is None:
            raise RuntimeError("Failed to compute initial context")
            
        app_state.message_handler.set_default_z(default_z)
        
        print("\nStarting WebSocket server and simulation...")
        server = await websockets.serve(handle_websocket, "0.0.0.0", WS_PORT)
        print(f"WebSocket server started at ws://{BACKEND_DOMAIN}:{WS_PORT}")
        
        await asyncio.gather(
            server.wait_closed(),
            run_simulation()
        )
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        app_state.display_manager.cleanup()
        app_state.thread_pool.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
