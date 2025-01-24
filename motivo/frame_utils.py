import os
import cv2
import numpy as np
import json
import pickle
from datetime import datetime
from smpl_utils import qpos_to_smpl, SMPL_BONE_ORDER_NAMES

def save_frame_data(frame, qpos, qvel, env=None, smpl_data=None):
    """
    Save current frame image and state data with bone ordering information
    """
    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("captured_frames", timestamp)
    os.makedirs(output_dir, exist_ok=True)
    
    # Save image
    image_path = os.path.join(output_dir, "frame.png")
    cv2.imwrite(image_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    
    # Convert to SMPL if environment is provided and smpl_data is not
    if env is not None and smpl_data is None:
        pose, trans = qpos_to_smpl(qpos, env.unwrapped.model)
        smpl_data = {
            'poses': pose,
            'trans': trans[0],
            'betas': None
        }
    
    # Save state data as NPZ (for numerical data)
    npz_data = {
        'qpos': qpos,
        'qvel': qvel,
        'timestamp': timestamp
    }
    if smpl_data:
        npz_data.update(smpl_data)
    
    data_path = os.path.join(output_dir, "state_data.npz")
    np.savez(data_path, **npz_data)
    
    # Save SMPL data as pickle if available
    if smpl_data:
        # Get poses and ensure correct shape (frames, joints*3)
        poses = smpl_data['poses']
        
        # Debug print before reshaping
        print(f"Original poses shape: {poses.shape}")
        
        # If poses is 1D (72 values), reshape to (1, 72)
        if len(poses.shape) == 1 and poses.shape[0] == 72:
            print("Case 1: Converting 1D poses (72) to (1, 72)")
            poses = poses.reshape(1, 72)
        # If poses is 3D (batch, 24, 3), reshape to (batch, 72)
        elif len(poses.shape) == 3 and poses.shape[1:] == (24, 3):
            print("Case 2: Converting 3D poses (batch, 24, 3) to (batch, 72)")
            poses = poses.reshape(poses.shape[0], 72)
        # If poses is already 2D (batch, 72), keep as is
        elif len(poses.shape) == 2 and poses.shape[1] == 72:
            print("Case 3: Poses already in correct format (batch, 72)")
            poses = poses
        else:
            print(f"ERROR: Unhandled pose shape: {poses.shape}")
            raise ValueError(f"Unexpected poses shape: {poses.shape}")
            
        # Debug print after reshaping
        print(f"Final poses shape: {poses.shape}")
            
        pkl_data = {
            'smpl_poses': poses,  # Will be shape (frames, 72)
            'smpl_trans': smpl_data['trans'][np.newaxis, :] if isinstance(smpl_data['trans'], np.ndarray) else np.array([smpl_data['trans']])
        }
        
        pkl_path = os.path.join(output_dir, "smpl_data.pkl")
        with open(pkl_path, 'wb') as f:
            pickle.dump(pkl_data, f)
    
    # Create metadata JSON
    metadata = {
        'metadata': {
            'timestamp': timestamp,
            'format_version': '1.0',
            'description': 'Humanoid pose capture data'
        },
        'bone_hierarchy': {
            'order': SMPL_BONE_ORDER_NAMES,
            'root': 'Pelvis',
            'description': 'Bone order for pose reconstruction'
        },
        'data_format': {
            'qpos': {
                'description': 'MuJoCo joint positions',
                'shape': list(qpos.shape),
                'dtype': str(qpos.dtype)
            },
            'qvel': {
                'description': 'MuJoCo joint velocities',
                'shape': list(qvel.shape),
                'dtype': str(qvel.dtype)
            }
        },
        'image': {
            'path': 'frame.png',
            'format': 'PNG',
            'colorspace': 'RGB'
        }
    }
    
    # Add SMPL format info if available
    if smpl_data:
        metadata['smpl_format'] = {
            'description': 'SMPL pose parameters',
            'poses': {
                'shape': list(smpl_data['poses'].shape),
                'dtype': str(smpl_data['poses'].dtype),
                'format': 'rotation vectors (radians)',
                'bone_order': SMPL_BONE_ORDER_NAMES
            },
            'translation': {
                'description': 'Root translation relative to Pelvis',
                'format': 'XYZ coordinates'
            }
        }
    
    # Create separate data JSON
    pose_data = {
        'timestamp': timestamp,
        'qpos': qpos.tolist(),
        'qvel': qvel.tolist()
    }
    
    if smpl_data:
        pose_data['smpl'] = {
            'poses': smpl_data['poses'].tolist(),
            'translation': smpl_data['trans'].tolist() if isinstance(smpl_data['trans'], np.ndarray) else smpl_data['trans']
        }
    
    # Save both JSON files
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    data_path = os.path.join(output_dir, "pose_data.json")
    with open(data_path, 'w') as f:
        json.dump(pose_data, f, indent=2)
    
    print(f"Saved frame and state data to: {output_dir}")

class FrameRecorder:
    def __init__(self):
        self.frames = []
        self.qpos_list = []
        self.qvel_list = []
        self.smpl_data_list = []
        self.recording = False
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Set timestamp at initialization

    def record_frame_data(self, frame, qpos, qvel, env=None, smpl_data=None):
        """
        Record a single frame and its associated data
        """
        if not self.recording:
            # Don't reset timestamp here anymore since it's set in __init__
            self.recording = True
            print(f"Started recording with timestamp: {self.timestamp}")
            
        # Convert to SMPL if environment is provided and smpl_data is not
        if env is not None and smpl_data is None:
            pose, trans = qpos_to_smpl(qpos, env.unwrapped.model)
            smpl_data = {
                'poses': pose,
                'trans': trans[0],
                'betas': None
            }
            
        # Store frame data
        self.frames.append(frame)
        self.qpos_list.append(qpos)
        self.qvel_list.append(qvel)
        if smpl_data:
            self.smpl_data_list.append(smpl_data)
            
    def end_record(self):
        """
        Save all recorded frames and data
        """
        if not self.recording or not self.frames:
            print("No frames recorded")
            return
            
        print(f"Ending recording with timestamp: {self.timestamp}")
        
        # Create output directory with timestamp
        output_dir = os.path.join("captured_frames", self.timestamp)
        os.makedirs(output_dir, exist_ok=True)
        
        # Save frames as video
        video_path = os.path.join(output_dir, "frames.mp4")
        height, width = self.frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, 30.0, (width, height))
        
        for frame in self.frames:
            out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        out.release()
        
        # Convert lists to numpy arrays
        qpos_array = np.stack(self.qpos_list)
        qvel_array = np.stack(self.qvel_list)
        
        # Save state data as NPZ
        npz_data = {
            'qpos': qpos_array,
            'qvel': qvel_array,
            'timestamp': self.timestamp
        }
        
        # Process SMPL data if available
        if self.smpl_data_list:
            # Stack all poses and ensure correct shape
            all_poses = np.stack([data['poses'] for data in self.smpl_data_list])
            all_trans = np.stack([data['trans'] for data in self.smpl_data_list])
            
            # Debug print before reshaping
            print(f"Original poses shape: {all_poses.shape}")
            
            # Handle various possible pose shapes and convert to (batch, 72) format
            if len(all_poses.shape) == 4 and all_poses.shape[2:] == (24, 3):
                print("Case 1: Converting 4D poses (batch, 1, 24, 3) to (batch, 72)")
                all_poses = all_poses.reshape(all_poses.shape[0], -1)  # Flatten to (batch, 72)
            elif len(all_poses.shape) == 3 and all_poses.shape[1:] == (24, 3):
                print("Case 2: Converting 3D poses (batch, 24, 3) to (batch, 72)")
                all_poses = all_poses.reshape(all_poses.shape[0], 72)
            elif len(all_poses.shape) == 2 and all_poses.shape[1] == 72:
                print("Case 3: Poses already in correct format (batch, 72)")
                all_poses = all_poses
            else:
                print(f"ERROR: Unhandled pose shape: {all_poses.shape}")
                raise ValueError(f"Unexpected poses shape: {all_poses.shape}")
            
            # Debug print after reshaping
            print(f"Final poses shape: {all_poses.shape}")
            
            npz_data.update({
                'smpl_poses': all_poses,  # Now in (batch, 72) format
                'smpl_trans': all_trans
            })
            
            # Save SMPL data as pickle
            pkl_data = {
                'smpl_poses': all_poses,  # Now in (batch, 72) format
                'smpl_trans': all_trans
            }
            
            pkl_path = os.path.join(output_dir, "smpl_data.pkl")
            with open(pkl_path, 'wb') as f:
                pickle.dump(pkl_data, f)
        
        # Save NPZ data
        data_path = os.path.join(output_dir, "state_data.npz")
        np.savez(data_path, **npz_data)
        
        # Create and save metadata
        metadata = {
            'metadata': {
                'timestamp': self.timestamp,
                'format_version': '1.0',
                'description': 'Humanoid pose capture sequence',
                'frame_count': len(self.frames)
            },
            'bone_hierarchy': {
                'order': SMPL_BONE_ORDER_NAMES,
                'root': 'Pelvis',
                'description': 'Bone order for pose reconstruction'
            },
            'data_format': {
                'qpos': {
                    'description': 'MuJoCo joint positions sequence',
                    'shape': list(qpos_array.shape),
                    'dtype': str(qpos_array.dtype)
                },
                'qvel': {
                    'description': 'MuJoCo joint velocities sequence',
                    'shape': list(qvel_array.shape),
                    'dtype': str(qvel_array.dtype)
                }
            },
            'video': {
                'path': 'frames.mp4',
                'format': 'MP4',
                'fps': 30,
                'frame_count': len(self.frames)
            }
        }
        
        metadata_path = os.path.join(output_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        # Reset recorder state
        self.frames = []
        self.qpos_list = []
        self.qvel_list = []
        self.smpl_data_list = []
        self.recording = False
        # Don't reset timestamp here anymore
        
        print(f"Saved sequence data to: {output_dir}") 