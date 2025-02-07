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
from frame_utils import FrameRecorder  # Update import to use existing file
from cache_utils import RewardContextCache
from ws_manager import WebSocketManager
from utils.utils import normalize_q_value
from display_utils import DisplayManager
import traceback  



# import from env BACKEND_DOMAIN
BACKEND_DOMAIN = os.getenv("VITE_BACKEND_DOMAIN", "localhost")
WS_PORT = os.getenv("VITE_WS_PORT", 8765)
API_PORT = os.getenv("VITE_API_PORT", 5000)
WEBSERVER_PORT = os.getenv("VITE_WEBSERVER_PORT", 5002)
VITE_WS_URL = os.getenv("VITE_WS_URL", f"ws://{BACKEND_DOMAIN}:{WS_PORT}")
# Global variables
model = None
env = None
buffer_data = None
active_contexts = {}  # Store computed contexts
current_z = None     # Current active context
thread_pool = ThreadPoolExecutor(max_workers=2)  # Increased from 1 to 2
is_computing_reward = False  # New flag to track reward computation status
frame_recorder = None  # Add this line
ws_manager = WebSocketManager()  # Replace connected_clients and unique_clients sets
active_rewards = None  # Current active reward configuration
context_cache = RewardContextCache()
display_manager = DisplayManager()
default_z = None  # Will store the first computed context

async def get_reward_context(reward_config):
    """Async wrapper for reward context computation"""
    global is_computing_reward
    
    try:
        is_computing_reward = True
        print("\n=== Reward Context Computation ===")
        print("Computing... ⚙️")
        
        # Notify clients that computation started
        await ws_manager.broadcast({
            "type": "reward_computation",
            "status": "started",
            "timestamp": datetime.now().isoformat()
        })
        
        # Using asyncio.to_thread instead of ThreadPoolExecutor
        z = await asyncio.to_thread(
            compute_reward_context,
            reward_config,
            env,
            model,
            buffer_data
        )
        
        # Notify clients that computation is complete
        await ws_manager.broadcast({
            "type": "reward_computation",
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        })
        
        return z
    finally:
        is_computing_reward = False
        print("✅ Computation complete!")

async def broadcast_pose(pose_data):
    """Broadcast pose data to all connected clients"""
    await ws_manager.broadcast(pose_data)

async def handle_websocket(websocket):
    """Handle websocket connections"""
    global current_z, active_rewards, is_computing_reward, frame_recorder
    
    print("\n=== New WebSocket Connection Established ===")
    ws_manager.connected_clients.add(websocket)
    print(f"Total connections: {len(ws_manager.connected_clients)}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get("type", "")
                #1print(f"Received message type: {message_type}")

                # Add handler for mixed pose and reward
                if message_type == "mix_pose_reward":
                    try:
                        print("\nMixing pose and reward behaviors...")
                        goal_qpos = np.array(data.get("pose", []))
                        reward_config = data.get("reward", {})
                        mix_weight = data.get("mix_weight", 0.5)  # 0 = all pose, 1 = all reward
                        
                        # Get pose-based context
                        if len(goal_qpos) != 76:
                            raise ValueError(f"Invalid pose length: {len(goal_qpos)}, expected 76")
                        
                        env.unwrapped.set_physics(
                            qpos=goal_qpos,
                            qvel=np.zeros(75)
                        )
                        
                        goal_obs = torch.tensor(
                            env.unwrapped.get_obs()["proprio"].reshape(1, -1),
                            device=model.cfg.device,
                            dtype=torch.float32
                        )
                        
                        pose_z = model.goal_inference(next_obs=goal_obs)
                        
                        # Get reward-based context
                        reward_z = await get_reward_context(reward_config)
                        
                        # Interpolate between contexts
                        current_z = (1 - mix_weight) * pose_z + mix_weight * reward_z
                        
                        response = {
                            "type": "mix_updated",
                            "status": "success",
                            "mix_weight": mix_weight,
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(response))
                        
                    except Exception as e:
                        error_msg = f"Error mixing behaviors: {str(e)}"
                        print(error_msg)
                        traceback.print_exc()
                        
                        response = {
                            "type": "mix_updated",
                            "status": "error",
                            "error": error_msg,
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(response))

                elif message_type == "load_pose":
                    try:
                        print("\nLoading pose configuration...")
                        goal_qpos = np.array(data.get("pose", []))
                        print(f"Received pose array length: {len(goal_qpos)}")
                        print(f"First few values: {goal_qpos[:5]}")
                        
                        if len(goal_qpos) != 76:  # Expect 76 values for qpos
                            raise ValueError(f"Invalid pose length: {len(goal_qpos)}, expected 76")
                        
                        # Reset environment with new pose
                        print("Setting physics...")
                        env.unwrapped.set_physics(
                            qpos=goal_qpos,  # Use all 76 values for qpos
                            qvel=np.zeros(75)  # Use 75 zeros for qvel
                        )
                        
                        print("Getting observation...")
                        goal_obs = torch.tensor(
                            env.unwrapped.get_obs()["proprio"].reshape(1, -1),
                            device=model.cfg.device,
                            dtype=torch.float32
                        )
                        print(f"Observation shape: {goal_obs.shape}")
                        
                        # Use goal inference to get context
                        inference_type = data.get("inference_type", "goal")
                        print(f"Using inference type: {inference_type}")
                        
                        if inference_type == "goal":
                            z = model.goal_inference(next_obs=goal_obs)
                        elif inference_type == "tracking":
                            z = model.tracking_inference(next_obs=goal_obs)
                        else:
                            # If unsupported type, default to goal inference
                            print(f"Warning: Unsupported inference type '{inference_type}', defaulting to goal inference")
                            z = model.goal_inference(next_obs=goal_obs)
                        
                        # Update current context
                        current_z = z
                        print("Context updated successfully")
                        
                        response = {
                            "type": "pose_loaded",
                            "status": "success",
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(response))
                        print("Success response sent")
                        
                    except Exception as e:
                        error_msg = f"Error loading pose: {str(e)}"
                        print(error_msg)
                        traceback.print_exc()
                        
                        response = {
                            "type": "pose_loaded",
                            "status": "error",
                            "error": error_msg,
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(response))

                elif message_type == "debug_model_info":
                    stats = ws_manager.get_stats()
                    response = {
                        "type": "debug_model_info",
                        "is_computing": is_computing_reward,
                        "active_rewards": active_rewards,
                        **stats
                    }
                    await ws_manager.broadcast(response)
                
                elif message_type == "request_reward":
                    print("\n=== Processing Reward Combination ===")
                    
                    if is_computing_reward:
                        print("⚠️ Reward computation already in progress, request ignored")
                        response = {
                            "type": "reward",
                            "status": "computing_in_progress",
                            "timestamp": data.get("timestamp", ""),
                            "is_computing": True
                        }
                        await websocket.send(json.dumps(response))
                        return
                    
                    # Update active rewards
                    active_rewards = data['reward']
                    current_z = await context_cache.get_cached_context(active_rewards, get_reward_context)
                    
                    response = {
                        "type": "reward",
                        "value": 1.0,
                        "timestamp": data.get("timestamp", ""),
                        "is_computing": is_computing_reward
                    }
                    await websocket.send(json.dumps(response))
                    
                    print(f"\nStatus:")
                    print(f"Active Rewards: {json.dumps(active_rewards['rewards'], indent=2)}")
                    print(f"Cached Computations: {len(context_cache.computation_cache)}")
                    print("=== End Processing ===\n")
                
                elif message_type == "clean_rewards":
                    print("\nCleaning active rewards...")
                    
                    # Reset to default context
                    current_z = default_z
                    active_rewards = None
                    
                    # Reset environment
                    observation, _ = env.reset()
                    print("Environment reset completed")
                    
                    # Send debug info immediately after reset
                    debug_info = {
                        "type": "debug_model_info",
                        "is_computing": is_computing_reward,
                        "active_rewards": active_rewards,
                        **ws_manager.get_stats()
                    }
                    await ws_manager.broadcast(debug_info)
                    
                    response = {
                        "type": "clean_rewards",
                        "status": "success",
                        "timestamp": data.get("timestamp", "")
                    }
                    await websocket.send(json.dumps(response))
                
                elif message_type == "update_parameters":
                    # Handle parameter updates - call update_parameters directly on env
                    new_params = data.get("parameters", {})
                    env.update_parameters(new_params)  # Changed from env.unwrapped.update_parameters
                    
                    # Send confirmation back to client
                    response = {
                        "type": "parameters_updated",
                        "parameters": env.get_parameters(),  # Changed from env.unwrapped.get_parameters
                        "timestamp": data.get("timestamp", "")
                    }
                    await websocket.send(json.dumps(response))

                elif message_type == "get_parameters":
                    # Return current parameter values
                    response = {
                        "type": "parameters",
                        "parameters": env.get_parameters(),  # Changed from env.unwrapped.get_parameters
                        "timestamp": data.get("timestamp", "")
                    }
                    await websocket.send(json.dumps(response))
                
                elif message_type == "start_recording":
                    print("Starting recording...")
                    global frame_recorder  # Ensure we're using the global variable
                    frame_recorder = FrameRecorder()
                    frame_recorder.recording = True
                    response = {
                        "type": "recording_status",
                        "status": "started",
                        "timestamp": datetime.now().isoformat()
                    }
                    print("Starting recording, recorder state:", frame_recorder.recording)
                    await websocket.send(json.dumps(response))
                
                elif message_type == "stop_recording":
                    print("Stopping recording...")
                    if frame_recorder and frame_recorder.recording:
                        try:
                            print(f"Frames recorded: {len(frame_recorder.frames)}")
                            
                            # Create a unique filename for the zip
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            zip_filename = f"recording_{timestamp}.zip"
                            
                            # Use path relative to motivo directory
                            downloads_dir = os.path.join(os.path.dirname(__file__), 'downloads')
                            zip_path = os.path.join(downloads_dir, zip_filename)
                            
                            # Ensure downloads directory exists
                            os.makedirs(downloads_dir, exist_ok=True)
                            print(f"Saving recording to: {zip_path}")
                            
                            # Save the recording and get the zip path
                            frame_recorder.end_record(zip_path)
                            
                            # Create download URL using WEBSERVER_PORT
                            download_url = f"http://{BACKEND_DOMAIN}:{WEBSERVER_PORT}/downloads/{zip_filename}"
                            print(f"Download URL created: {download_url}")
                            
                            response = {
                                "type": "recording_status",
                                "status": "stopped",
                                "downloadUrl": download_url,
                                "timestamp": datetime.now().isoformat()
                            }
                            print(f"Sending response: {response}")
                            await websocket.send(json.dumps(response))
                            frame_recorder = None
                        except Exception as e:
                            print(f"Error stopping recording: {str(e)}")
                            traceback.print_exc()
                            
                            # Send error response to client
                            error_response = {
                                "type": "recording_status",
                                "status": "error",
                                "error": str(e),
                                "timestamp": datetime.now().isoformat()
                            }
                            await websocket.send(json.dumps(error_response))
                
                elif message_type == "update_reward":
                    try:
                        reward_index = data.get("index")
                        new_parameters = data.get("parameters")
                        
                        print("\n=== Processing Reward Update ===")
                        print(f"Reward Index: {reward_index}")
                        print(f"Incoming parameters: {json.dumps(new_parameters, indent=2)}")
                        
                        if active_rewards and 'rewards' in active_rewards:
                            print("\nCurrent active rewards before update:")
                            print(json.dumps(active_rewards, indent=2))
                            
                            # Convert string numbers to float for numeric parameters
                            for key, value in new_parameters.items():
                                try:
                                    if isinstance(value, (list, tuple)):
                                        print(f"Converting sequence {key}: {value} to float")
                                        new_parameters[key] = float(value[0])
                                    elif isinstance(value, str):
                                        print(f"Converting string {key}: {value} to float")
                                        new_parameters[key] = float(value)
                                    elif isinstance(value, bool):
                                        print(f"Keeping boolean {key}: {value}")
                                        continue
                                    else:
                                        print(f"Converting {key}: {value} ({type(value)}) to float")
                                        new_parameters[key] = float(value)
                                except (ValueError, TypeError) as e:
                                    print(f"⚠️ Warning: Could not convert {key}={value}: {str(e)}")
                                    continue
                            
                            print(f"\nConverted parameters: {json.dumps(new_parameters, indent=2)}")
                            
                            # Update the specific reward's parameters
                            active_rewards['rewards'][reward_index].update(new_parameters)
                            
                            print("\nActive rewards after update:")
                            print(json.dumps(active_rewards, indent=2))
                            
                            print("\nRecomputing context...")
                            current_z = await context_cache.get_cached_context(active_rewards, get_reward_context)
                            print("Context recomputed ✅")
                            
                            response = {
                                "type": "reward_updated",
                                "status": "success",
                                "active_rewards": active_rewards,
                                "timestamp": datetime.now().isoformat()
                            }
                            await websocket.send(json.dumps(response))
                            print("\n✅ Update successful - Response sent")
                            
                    except Exception as e:
                        error_msg = f"❌ Error updating reward: {str(e)}"
                        print("\n=== Error Details ===")
                        print(error_msg)
                        traceback.print_exc()
                        print("===================")
                        
                        response = {
                            "type": "reward_updated",
                            "status": "error",
                            "error": error_msg,
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(response))
                
                elif message_type == "clear_active_rewards":
                    print("\nClearing active rewards...")
                    active_rewards = None
                    current_z = default_z
                    print("Active rewards cleared ✅")
                    
                    response = {
                        "type": "rewards_cleared",
                        "status": "success",
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(response))
                
                elif message_type == "load_pose_smpl":
                    try:
                        print("\nLoading SMPL pose configuration...")
                        smpl_pose = np.array(data.get("pose", []))
                        smpl_trans = np.array(data.get("trans", [0, 0, 0.91437225]))
                        
                        # Add target_rotation parameter
                        target_rotation = data.get("target_rotation", None)  # Get from websocket message
                        normalize = data.get("normalize", True)
                        random_root = data.get("random_root", False)
                        count_offset = data.get("count_offset", True)
                        use_quat = data.get("use_quat", False)
                        euler_order = data.get("euler_order", "ZYX")
                        model_type = data.get("model", "smpl")
                        
                        print(f"Received SMPL pose array length: {len(smpl_pose)}")
                        print(f"Parameters: normalize={normalize}, random_root={random_root}, "
                              f"count_offset={count_offset}, use_quat={use_quat}, "
                              f"euler_order={euler_order}, model={model_type}")
                        if target_rotation:
                            print(f"Target rotation: {target_rotation}")
                        
                        if len(smpl_pose) != 72:
                            raise ValueError(f"Invalid SMPL pose length: {len(smpl_pose)}, expected 72")
                        
                        # Convert SMPL pose to qpos with additional parameters
                        smpl_pose = torch.tensor(smpl_pose).reshape(1, 72)
                        smpl_trans = np.array(smpl_trans).reshape(1, 3)
                        qpos = smpl_to_qpose(
                            pose=smpl_pose,
                            mj_model=env.unwrapped.model,
                            trans=smpl_trans,
                            #normalize=normalize,
                            #random_root=random_root,
                            #count_offset=count_offset,
                            #use_quat=use_quat,
                            #euler_order=euler_order,
                            smpl_model=model_type,
                            #target_rotation=target_rotation  # Add new parameter
                        )
                        
                        print("Setting physics with converted qpos...")
                        env.unwrapped.set_physics(
                            qpos=qpos.flatten(),  # Use converted qpos
                            qvel=np.zeros(75)  # Use 75 zeros for qvel
                        )
                        
                        # Get observation and compute context
                        print("Getting observation...")
                        goal_obs = torch.tensor(
                            env.unwrapped.get_obs()["proprio"].reshape(1, -1),
                            device=model.cfg.device,
                            dtype=torch.float32
                        )
                        
                        # Use goal inference to get context
                        inference_type = data.get("inference_type", "goal")
                        print(f"Using inference type: {inference_type}")
                        
                        if inference_type == "goal":
                            z = model.goal_inference(next_obs=goal_obs)
                        elif inference_type == "tracking":
                            z = model.tracking_inference(next_obs=goal_obs)
                        else:
                            # If unsupported type, default to goal inference
                            print(f"Warning: Unsupported inference type '{inference_type}', defaulting to goal inference")
                            z = model.goal_inference(next_obs=goal_obs)
                        
                        # Update current context
                        current_z = z
                        print("Context updated successfully")
                        
                        response = {
                            "type": "pose_loaded",
                            "status": "success",
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(response))
                        print("Success response sent")
                        
                    except Exception as e:
                        error_msg = f"Error loading SMPL pose: {str(e)}"
                        print(error_msg)
                        traceback.print_exc()
                        
                        response = {
                            "type": "pose_loaded",
                            "status": "error",
                            "error": error_msg,
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(response))

            except json.JSONDecodeError:
                print("Error: Invalid JSON message")
                await websocket.send(json.dumps({"error": "Invalid JSON"}))
                
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        ws_manager.connected_clients.discard(websocket)
        print(f"Client disconnected. Total connections: {len(ws_manager.connected_clients)}")
        
        if frame_recorder and frame_recorder.recording:
            try:
                frame_recorder.end_record()
            except Exception as e:
                print(f"Error in cleanup: {str(e)}")
                traceback.print_exc()
        print("WebSocket connection closed")

async def run_simulation():
    """Continuous simulation loop"""
    global current_z, is_computing_reward, frame_recorder
    observation, _ = env.reset()
    
    while True:
        # Get action and step environment
        action = model.act(observation, current_z, mean=True)
        q_value = compute_q_value(model, observation, current_z, action)
        q_percentage = normalize_q_value(q_value)
        observation, _, terminated, truncated, _ = env.step(action.cpu().numpy().ravel())
        
        # Broadcast pose data using WebSocketManager
        try:
            qpos = env.unwrapped.data.qpos


            #make a temp fake qpos with 
            
            pose, trans, positions, position_names = qpos_to_smpl(qpos, env.unwrapped.model)  # Now capturing positions
            
            pose_data = {
                "type": "smpl_update",
                "pose": pose.tolist(),
                "trans": trans.tolist(),
                "positions": [pos.tolist() for pos in positions],  # Convert numpy arrays to lists
                "qpos": qpos.tolist(),  # Add qpos to the message
                "timestamp": datetime.now().isoformat(),
                "position_names": position_names
            }
            
            # Use the WebSocketManager's broadcast method
            await ws_manager.broadcast(pose_data)
            
        except Exception as e:
            print(f"Error broadcasting pose data: {str(e)}")
            traceback.print_exc()
        
        # Render and display frame
        frame = env.render()
        resized_frame = display_manager.show_frame(
            frame,
            q_percentage=q_percentage,
            is_computing=is_computing_reward
        )
        cv2.imwrite('../output.jpg', resized_frame)
        
        # Check for key presses
        should_quit, should_save = display_manager.check_key()
        if should_quit:
            break
        elif should_save:
            try:
                env_data = env.unwrapped.data
                save_frame_data(
                    frame=frame,
                    qpos=env_data.qpos.copy(),
                    qvel=env_data.qvel.copy(),
                    env=env
                )
                print("Frame saved! 📸")
            except Exception as e:
                print("Error during frame save:", str(e))
                print("Observation shape:", observation.shape)
                print("Data structure:", type(env.unwrapped.data))
        
        if terminated:
            observation, _ = env.reset()
        
        await asyncio.sleep(1/60)  # 60 FPS target

async def main():
    """Main function"""
    global model, env, buffer_data, current_z, default_z
    
    try:
        print("\n=== Available Rewards ===")
        print_available_rewards()
        print("\n=== System Setup ===")
        
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
        model = FBcprModel.from_pretrained("facebook/metamotivo-M-1")
        model.to(device)
        model.eval()
        
        env = setup_environment(device)
        
        '''
        # Quick test of smpl_to_qpose with JSON data
        try:
            with open('poses_test.json', 'r') as f:
                test_data = json.load(f)
                first_pose = test_data['poses'][0]  # Get first pose from the 'poses' array
                print(f"\nPoints in pose array: {len(first_pose)}")  # Should be 72
                test_pose = torch.tensor(first_pose).reshape(1, 72)  # Reshape to 1x72
                test_trans = np.array([0, 0, 0.91437225]).reshape(1, 3)  # Default translation
                print(f"Points in trans array: {len(test_trans[0])}")  # Should be 3
                test_qpos = smpl_to_qpose(test_pose, env.unwrapped.model, trans=test_trans)
                print("\nTest qpos shape:", test_qpos.shape)
                print("First few values:", test_qpos[0, :5])
                print("Pose shape:", test_pose.shape)
                print("Trans shape:", test_trans.shape)
        except Exception as e:
            print(f"Test failed: {str(e)}")
            traceback.print_exc()
        '''
        
        print("Downloading buffer data...")
        buffer_data = download_buffer()
        
        # Pre-compute default context and store both as current and default
        default_config = {
            'rewards': [
                { 'name': 'move-ego', 'move_speed': 0.0, 'stand_height': 1.4 }
            ],
            'weights': [1.0]
        }
        print("\nPre-computing default context...")
        
        default_z = await get_reward_context(default_config)  # Store directly, not using cache
        current_z = default_z
        
        if default_z is None:
            raise RuntimeError("Failed to compute initial context")
            
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
        display_manager.cleanup()
        thread_pool.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
