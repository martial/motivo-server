import json
import numpy as np
import torch
from datetime import datetime
import os
import traceback
from typing import Dict, Any, Optional
from frame_utils import FrameRecorder
from reward_context import compute_reward_context
import asyncio

class MessageHandler:
    def __init__(self, model, env, ws_manager, context_cache):
        self.model = model
        self.env = env
        self.ws_manager = ws_manager
        self.context_cache = context_cache
        self.buffer_data = None  # Will be set by AppState
        self.current_z = None
        self.active_rewards = None
        self.is_computing_reward = False
        self.default_z = None
        self.frame_recorder = None
        
        # Environment variables
        self.backend_domain = os.getenv("VITE_BACKEND_DOMAIN", "localhost")
        self.webserver_port = os.getenv("VITE_WEBSERVER_PORT", 5002)

    def set_buffer_data(self, buffer_data):
        """Set the buffer data needed for reward computation"""
        self.buffer_data = buffer_data

    async def get_reward_context(self, reward_config):
        """Compute reward context"""
        try:
            self.is_computing_reward = True
            # Create a wrapper function that includes all required arguments
            async def compute_wrapper(config):
                return await asyncio.to_thread(
                    compute_reward_context,
                    config,
                    self.env,
                    self.model,
                    self.buffer_data
                )
            return await self.context_cache.get_cached_context(reward_config, compute_wrapper)
        finally:
            self.is_computing_reward = False

    async def handle_message(self, websocket, message: str) -> None:
        try:
            data = json.loads(message)
            message_type = data.get("type", "")
            
            # Map message types to handler methods
            handlers = {
                "mix_pose_reward": self.handle_mix_pose_reward,
                "debug_model_info": self.handle_debug_model_info,
                "request_reward": self.handle_request_reward,
                "clean_rewards": self.handle_clean_rewards,
                "update_parameters": self.handle_update_parameters,
                "load_pose_smpl": self.handle_load_pose_smpl,
                "start_recording": self.handle_start_recording,
                "stop_recording": self.handle_stop_recording,
                "load_pose": self.handle_load_pose,
                "clear_active_rewards": self.handle_clear_active_rewards,
                "update_reward": self.handle_update_reward,
            }
            
            handler = handlers.get(message_type)
            if handler:
                await handler(websocket, data)
            else:
                print(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            print("Error: Invalid JSON message")
            await websocket.send(json.dumps({"error": "Invalid JSON"}))

    async def handle_start_recording(self, websocket, data: Dict[str, Any]) -> None:
        print("Starting recording...")
        self.frame_recorder = FrameRecorder()
        self.frame_recorder.recording = True
        response = {
            "type": "recording_status",
            "status": "started",
            "timestamp": datetime.now().isoformat()
        }
        print("Starting recording, recorder state:", self.frame_recorder.recording)
        await websocket.send(json.dumps(response))

    async def handle_stop_recording(self, websocket, data: Dict[str, Any]) -> None:
        print("Stopping recording...")
        if self.frame_recorder and self.frame_recorder.recording:
            try:
                print(f"Frames recorded: {len(self.frame_recorder.frames)}")
                
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
                self.frame_recorder.end_record(zip_path)
                
                # Create download URL using WEBSERVER_PORT
                download_url = f"http://{self.backend_domain}:{self.webserver_port}/downloads/{zip_filename}"
                print(f"Download URL created: {download_url}")
                
                response = {
                    "type": "recording_status",
                    "status": "stopped",
                    "downloadUrl": download_url,
                    "timestamp": datetime.now().isoformat()
                }
                print(f"Sending response: {response}")
                await websocket.send(json.dumps(response))
                self.frame_recorder = None
            except Exception as e:
                print(f"Error stopping recording: {str(e)}")
                traceback.print_exc()
                
                error_response = {
                    "type": "recording_status",
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(error_response))

    async def handle_load_pose(self, websocket, data: Dict[str, Any]) -> None:
        try:
            print("\nLoading pose configuration...")
            goal_qpos = np.array(data.get("pose", []))
            print(f"Received pose array length: {len(goal_qpos)}")
            print(f"First few values: {goal_qpos[:5]}")
            
            if len(goal_qpos) != 76:  # Expect 76 values for qpos
                raise ValueError(f"Invalid pose length: {len(goal_qpos)}, expected 76")
            
            # Reset environment with new pose
            print("Setting physics...")
            self.env.unwrapped.set_physics(
                qpos=goal_qpos,  # Use all 76 values for qpos
                qvel=np.zeros(75)  # Use 75 zeros for qvel
            )
            
            print("Getting observation...")
            goal_obs = torch.tensor(
                self.env.unwrapped.get_obs()["proprio"].reshape(1, -1),
                device=self.model.cfg.device,
                dtype=torch.float32
            )
            print(f"Observation shape: {goal_obs.shape}")
            
            # Use goal inference to get context
            inference_type = data.get("inference_type", "goal")
            print(f"Using inference type: {inference_type}")
            
            if inference_type == "goal":
                z = self.model.goal_inference(next_obs=goal_obs)
            elif inference_type == "tracking":
                z = self.model.tracking_inference(next_obs=goal_obs)
            else:
                # If unsupported type, default to goal inference
                print(f"Warning: Unsupported inference type '{inference_type}', defaulting to goal inference")
                z = self.model.goal_inference(next_obs=goal_obs)
            
            # Update current context
            self.current_z = z
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

    async def handle_clear_active_rewards(self, websocket, data: Dict[str, Any]) -> None:
        print("\nClearing active rewards...")
        self.active_rewards = None
        self.current_z = self.default_z
        print("Active rewards cleared ✅")
        
        response = {
            "type": "rewards_cleared",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(response))

    async def handle_update_reward(self, websocket, data: Dict[str, Any]) -> None:
        try:
            reward_index = data.get("index")
            new_parameters = data.get("parameters")
            
            print("\n=== Processing Reward Update ===")
            print(f"Reward Index: {reward_index}")
            print(f"Incoming parameters: {json.dumps(new_parameters, indent=2)}")
            
            if self.active_rewards and 'rewards' in self.active_rewards:
                print("\nCurrent active rewards before update:")
                print(json.dumps(self.active_rewards, indent=2))
                
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
                self.active_rewards['rewards'][reward_index].update(new_parameters)
                
                print("\nActive rewards after update:")
                print(json.dumps(self.active_rewards, indent=2))
                
                print("\nRecomputing context...")
                self.current_z = await self.context_cache.get_cached_context(
                    self.active_rewards,
                    self.get_reward_context
                )
                print("Context recomputed ✅")
                
                response = {
                    "type": "reward_updated",
                    "status": "success",
                    "active_rewards": self.active_rewards,
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

    async def handle_mix_pose_reward(self, websocket, data: Dict[str, Any]) -> None:
        try:
            print("\nMixing pose and reward behaviors...")
            goal_qpos = np.array(data.get("pose", []))
            reward_config = data.get("reward", {})
            mix_weight = data.get("mix_weight", 0.5)
            
            if len(goal_qpos) != 76:
                raise ValueError(f"Invalid pose length: {len(goal_qpos)}, expected 76")
            
            # Get pose-based context
            self.env.unwrapped.set_physics(
                qpos=goal_qpos,
                qvel=np.zeros(75)
            )
            
            goal_obs = torch.tensor(
                self.env.unwrapped.get_obs()["proprio"].reshape(1, -1),
                device=self.model.cfg.device,
                dtype=torch.float32
            )
            
            pose_z = self.model.goal_inference(next_obs=goal_obs)
            reward_z = await self.context_cache.get_cached_context(reward_config, self.get_reward_context)
            
            # Interpolate between contexts
            self.current_z = (1 - mix_weight) * pose_z + mix_weight * reward_z
            
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
            
            response = {
                "type": "mix_updated",
                "status": "error",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(response))

    async def handle_debug_model_info(self, websocket, data: Dict[str, Any]) -> None:
        stats = self.ws_manager.get_stats()
        response = {
            "type": "debug_model_info",
            "is_computing": self.is_computing_reward,
            "active_rewards": self.active_rewards,
            **stats
        }
        await self.ws_manager.broadcast(response)

    async def handle_request_reward(self, websocket, data: Dict[str, Any]) -> None:
        print("\n=== Processing Reward Combination ===")
        
        if self.is_computing_reward:
            print("⚠️ Reward computation already in progress, request ignored")
            response = {
                "type": "reward",
                "status": "computing_in_progress",
                "timestamp": data.get("timestamp", ""),
                "is_computing": True
            }
            await websocket.send(json.dumps(response))
            return
        
        self.active_rewards = data['reward']
        self.current_z = await self.context_cache.get_cached_context(
            self.active_rewards, 
            self.get_reward_context
        )
        
        response = {
            "type": "reward",
            "value": 1.0,
            "timestamp": data.get("timestamp", ""),
            "is_computing": self.is_computing_reward
        }
        await websocket.send(json.dumps(response))
        
        print(f"\nStatus:")
        print(f"Active Rewards: {json.dumps(self.active_rewards['rewards'], indent=2)}")
        print(f"Cached Computations: {len(self.context_cache.computation_cache)}")
        print("=== End Processing ===\n")

    async def handle_clean_rewards(self, websocket, data: Dict[str, Any]) -> None:
        print("\nCleaning active rewards...")
        
        self.current_z = self.default_z
        self.active_rewards = None
        
        observation, _ = self.env.reset()
        print("Environment reset completed")
        
        debug_info = {
            "type": "debug_model_info",
            "is_computing": self.is_computing_reward,
            "active_rewards": self.active_rewards,
            **self.ws_manager.get_stats()
        }
        await self.ws_manager.broadcast(debug_info)
        
        response = {
            "type": "clean_rewards",
            "status": "success",
            "timestamp": data.get("timestamp", "")
        }
        await websocket.send(json.dumps(response))

    async def handle_update_parameters(self, websocket, data: Dict[str, Any]) -> None:
        new_params = data.get("parameters", {})
        self.env.update_parameters(new_params)
        
        response = {
            "type": "parameters_updated",
            "parameters": self.env.get_parameters(),
            "timestamp": data.get("timestamp", "")
        }
        await websocket.send(json.dumps(response))

    async def handle_load_pose_smpl(self, websocket, data: Dict[str, Any]) -> None:
        try:
            print("\nProcessing SMPL pose as goal...")
            smpl_pose = np.array(data.get("pose", []))
            smpl_trans = np.array(data.get("trans", [0, 0, 0.91437225]))
            model_type = data.get("model", "smpl")
            
            if len(smpl_pose) != 72:
                raise ValueError(f"Invalid SMPL pose length: {len(smpl_pose)}, expected 72")
            
            smpl_pose = torch.tensor(smpl_pose).reshape(1, 72)
            smpl_trans = np.array(smpl_trans).reshape(1, 3)
            
            # Convert SMPL pose to qpos
            from utils.smpl_utils import smpl_to_qpose
            goal_qpos = smpl_to_qpose(
                pose=smpl_pose,
                mj_model=self.env.unwrapped.model,
                trans=smpl_trans,
                smpl_model=model_type
            )
            
            # Store current state
            current_qpos = self.env.unwrapped.data.qpos.copy()
            current_qvel = self.env.unwrapped.data.qvel.copy()
            
            # Set goal state temporarily
            self.env.unwrapped.set_physics(
                qpos=goal_qpos.flatten(),
                qvel=np.zeros(75)
            )
            
            goal_obs = torch.tensor(
                self.env.unwrapped.get_obs()["proprio"].reshape(1, -1),
                device=self.model.cfg.device,
                dtype=torch.float32
            )
            
            # Restore original state
            self.env.unwrapped.set_physics(
                qpos=current_qpos,
                qvel=current_qvel
            )
            
            # Get context using specified inference type
            inference_type = data.get("inference_type", "goal")
            if inference_type == "goal":
                z = self.model.goal_inference(next_obs=goal_obs)
            elif inference_type == "tracking":
                z = self.model.tracking_inference(next_obs=goal_obs)
            else:
                raise ValueError(f"Unsupported inference type: {inference_type}")
            
            self.current_z = z
            print("Context updated successfully")
            
            response = {
                "type": "pose_loaded",
                "status": "success",
                "inference_type": inference_type,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(response))
            
        except Exception as e:
            error_msg = f"Error processing SMPL pose: {str(e)}"
            print(error_msg)
            
            response = {
                "type": "pose_loaded",
                "status": "error",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(response))

    def get_current_z(self) -> Optional[torch.Tensor]:
        return self.current_z

    def set_default_z(self, z: torch.Tensor) -> None:
        self.default_z = z
        self.current_z = z 