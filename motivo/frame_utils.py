import os
import cv2
import numpy as np
import json
import pickle
from datetime import datetime
from utils.smpl_utils import qpos_to_smpl, SMPL_BONE_ORDER_NAMES
import zipfile

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
        self.recording = False

    def record_frame_data(self, frame, qpos, qvel, env):
        if self.recording:
            self.frames.append({
                'frame': frame.copy(),
                'qpos': qpos.copy(),
                'qvel': qvel.copy(),
                'timestamp': datetime.now().isoformat()
            })

    def end_record(self, zip_path=None):
        """End recording and save frames to a zip file"""
        if not zip_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = f"downloads/recording_{timestamp}.zip"
        
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Save each frame and its data
            for i, frame_data in enumerate(self.frames):
                # Save frame as image
                frame_filename = f"frame_{i:04d}.jpg"
                frame_path = os.path.join(os.path.dirname(zip_path), frame_filename)
                cv2.imwrite(frame_path, frame_data['frame'])
                zf.write(frame_path, frame_filename)
                os.remove(frame_path)  # Clean up the temporary image file
                
                # Save state data as JSON
                state_data = {
                    'qpos': frame_data['qpos'].tolist(),
                    'qvel': frame_data['qvel'].tolist(),
                    'timestamp': frame_data['timestamp']
                }
                state_filename = f"state_{i:04d}.json"
                zf.writestr(state_filename, json.dumps(state_data))
        
        self.recording = False
        self.frames = []
        return zip_path 