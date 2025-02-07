from scipy.spatial.transform import Rotation as sRot
import numpy as np
import torch
import mujoco

# Since we're in the utils folder, use relative import with .
from .torch_geometry_transforms import angle_axis_to_rotation_matrix, rotation_matrix_to_quaternion, vertizalize_smpl_root

# Updated to match the exact order
SMPL_BONE_ORDER_NAMES = [
    "Pelvis",
    "L_Hip",
    "R_Hip",
    "Torso",
    "L_Knee",
    "R_Knee",
    "Spine",
    "L_Ankle",
    "R_Ankle",
    "Chest",
    "L_Toe",
    "R_Toe",
    "Neck",
    "L_Thorax",
    "R_Thorax",
    "Head",
    "L_Shoulder",
    "R_Shoulder",
    "L_Elbow",
    "R_Elbow",
    "L_Wrist",
    "R_Wrist",
    "L_Hand",
    "R_Hand",
]

SMPLH_BONE_ORDER_NAMES = [
    # Add SMPLH bone names if needed
]

# Add these constants at the top of the file
DEG_TO_RAD = np.pi / 180
RAD_TO_DEG = 180 / np.pi

def get_body_qposaddr(model):
    """Get the position address mapping for each body in the model"""
    body_qposaddr = dict()
    
    # Handle both old and new MuJoCo API
    try:
        # New MuJoCo API
        for i in range(model.nbody):
            body_name = model.body(i).name
            start_joint = model.body_jntadr[i]
            if start_joint < 0:
                continue
            end_joint = start_joint + model.body_jntnum[i]
            start_qposaddr = model.jnt_qposadr[start_joint]
            if end_joint < len(model.jnt_qposadr):
                end_qposaddr = model.jnt_qposadr[end_joint]
            else:
                end_qposaddr = model.nq
            body_qposaddr[body_name] = (start_qposaddr, end_qposaddr)
    except AttributeError:
        # Old MuJoCo API
        for i, body_name in enumerate(model.body_names):
            start_joint = model.body_jntadr[i]
            if start_joint < 0:
                continue
            end_joint = start_joint + model.body_jntnum[i]
            start_qposaddr = model.jnt_qposadr[start_joint]
            if end_joint < len(model.jnt_qposadr):
                end_qposaddr = model.jnt_qposadr[end_joint]
            else:
                end_qposaddr = model.nq
            body_qposaddr[body_name] = (start_qposaddr, end_qposaddr)
            
    return body_qposaddr

def qpos_to_smpl(qpos, mj_model, smpl_model="smpl"):
    """Convert MuJoCo qpos to SMPL pose parameters using MuJoCo's forward kinematics.
    
    Args:
        qpos: Joint positions array (batch_size x nq)
        mj_model: MuJoCo model
        smpl_model: Model type ("smpl" or "smplh")
    
    Returns:
        pose: SMPL pose parameters (batch_size x num_joints x 3)
        trans: Global translation (batch_size x 3)
        positions: List of global joint positions
    """
    mj_data = mujoco.MjData(mj_model)
    body_qposaddr = get_body_qposaddr(mj_model)
    
    # Convert qpos to numpy if it's a torch tensor
    if hasattr(qpos, 'detach'):
        qpos = qpos.detach().cpu().numpy()
    
    if len(qpos.shape) == 1:
        qpos = qpos.reshape(1, -1)
    
    batch_size = qpos.shape[0]
    trans = qpos[:, :3] - mj_model.body_pos[1]
    smpl_bones_to_use = (SMPL_BONE_ORDER_NAMES if smpl_model == "smpl" else SMPLH_BONE_ORDER_NAMES)
    pose = np.zeros([batch_size, len(smpl_bones_to_use), 3])
    positions = []
    position_names = []

    # Copy qpos to MuJoCo data
    mj_data.qpos[:] = qpos[0]
    mujoco.mj_kinematics(mj_model, mj_data)

    # Create mapping of bone names to MuJoCo body indices
    body_name_to_id = {mj_model.body(i).name: i for i in range(mj_model.nbody)}

    # Get root position and orientation
    root_pos = qpos[:, :3]
    root_quat = qpos[:, 3:7]
    pose[:, 0, :] = sRot.from_quat(root_quat[:, [1, 2, 3, 0]]).as_rotvec()
    positions.append(root_pos[0])
    position_names.append("Pelvis")

    # Get other joint rotations and positions using correct body indices
    for ind1, bone_name in enumerate(smpl_bones_to_use[1:], 1):
        ind2 = body_qposaddr[bone_name]
        # Get correct MuJoCo body index for this bone
        mj_body_id = body_name_to_id[bone_name]
        # Get global position using correct body index
        positions.append(mj_data.xpos[mj_body_id])
        position_names.append(bone_name)
        # Get joint angles from qpos
        pose[:, ind1, :] = sRot.from_euler("XYZ", qpos[:, ind2[0]:ind2[1]]).as_rotvec()

    # Validation checks
    assert len(positions) == len(SMPL_BONE_ORDER_NAMES), (
        f"Number of positions ({len(positions)}) doesn't match "
        f"SMPL_BONE_ORDER_NAMES ({len(SMPL_BONE_ORDER_NAMES)})"
    )
    assert position_names == SMPL_BONE_ORDER_NAMES, (
        f"Position order mismatch!\nExpected: {SMPL_BONE_ORDER_NAMES}\nGot: {position_names}"
    )

    return pose, trans, positions, position_names


def smpl_to_qpose(pose, trans, mj_model, smpl_model="smpl"):
    """Convert SMPL pose parameters to MuJoCo qpos.
    
    Args:
        pose: SMPL pose parameters (batch_size x num_joints x 3)
        trans: Global translation (batch_size x 3)
        mj_model: MuJoCo model
        smpl_model: Model type ("smpl" or "smplh")
    
    Returns:
        qpos: Joint positions array (batch_size x nq)
    """
    # Convert inputs to numpy if they're torch tensors
    if hasattr(pose, 'detach'):
        pose = pose.detach().cpu().numpy()
    if hasattr(trans, 'detach'):
        trans = trans.detach().cpu().numpy()
        
    # Ensure inputs are 2D
    if len(pose.shape) == 2:
        pose = pose.reshape(1, -1, 3)
    if len(trans.shape) == 1:
        trans = trans.reshape(1, -1)
        
    batch_size = pose.shape[0]
    nq = mj_model.nq
    body_qposaddr = get_body_qposaddr(mj_model)
    smpl_bones_to_use = (SMPL_BONE_ORDER_NAMES if smpl_model == "smpl" else SMPLH_BONE_ORDER_NAMES)
    
    qpos = np.zeros([batch_size, nq])
    
    # Print initial translation for debugging
    print(f"Initial trans Z: {trans[0, 2]}")
    print(f"Model body pos: {mj_model.body_pos[1]}")
    
    # Add a small base height if starting from 0
    if trans[0, 2] == 0:
        trans[:, 2] = 0.91437225  # Standard SMPL height offset
    
    # Set translation WITHOUT adding model body position
    qpos[:, :3] = trans  # Removed the body_pos addition
    
    # Print height after setting
    print(f"Initial qpos Z: {qpos[0, 2]}")
    
    min_height = 0.6  # Minimum height
    max_height = 1.0  # Maximum height
    qpos[:, 2] = np.clip(qpos[:, 2], min_height, max_height)
    
    # Print final height
    print(f"Final qpos Z: {qpos[0, 2]}")
    
    # Limit horizontal movement speed if there are multiple frames
    if batch_size > 1:
        max_delta = 0.1  # Maximum position change per frame
        for i in range(1, batch_size):
            delta = qpos[i, :2] - qpos[i-1, :2]  # XY plane movement
            if np.linalg.norm(delta) > max_delta:
                delta = delta * (max_delta / np.linalg.norm(delta))
                qpos[i, :2] = qpos[i-1, :2] + delta
    
    # Set root orientation
    root_rot = sRot.from_rotvec(pose[:, 0, :])
    initial_rotation = sRot.from_euler('xyz', [0.0, 0, 0])
    root_matrix = root_rot.as_matrix()
    root_matrix = np.matmul(initial_rotation.as_matrix(), root_matrix)
    root_rot = sRot.from_matrix(root_matrix)
    root_quat = root_rot.as_quat()
    qpos[:, 3:7] = root_quat[:, [3, 0, 1, 2]]
    
    # Set joint angles with slightly tighter limits
    for ind1, bone_name in enumerate(smpl_bones_to_use[1:], 1):
        ind2 = body_qposaddr[bone_name]
        joint_rot = sRot.from_rotvec(pose[:, ind1, :])
        euler_angles = joint_rot.as_euler("XYZ")
        euler_angles = np.clip(euler_angles, -2.5, 2.5)
        qpos[:, ind2[0]:ind2[1]] = euler_angles
    
    return qpos

def smplh_to_smpl(pose):
    batch_size = pose.shape[0]
    return torch.cat([pose[:, :66], torch.zeros((batch_size, 6))], dim=1)


def smpl_to_smplh(pose):
    batch_size = pose.shape[0]
    return torch.cat([pose[:, :66], torch.zeros((batch_size, 90))], dim=1)

def normalize_smpl_pose(pose_aa, trans=None, random_root=False, target_rotation=None):
    """
    Normalize SMPL pose with specified rotations.
    
    Args:
        pose_aa: SMPL pose in axis-angle format
        trans: Translation vector (optional)
        random_root: If True, applies random rotation around Y-axis
        target_rotation: Dict with target rotations in degrees (optional)
            e.g., {'x': 0, 'y': 90, 'z': 0}
    """
    root_aa = pose_aa[0, :3]
    root_rot = sRot.from_rotvec(np.array(root_aa))
    root_euler = np.array(root_rot.as_euler("xyz", degrees=True))
    target_root_euler = root_euler.copy()
    
    if target_rotation is not None:
        # Apply specified rotations in degrees
        target_root_euler[0] += target_rotation.get('x', target_root_euler[0])
        target_root_euler[1] += target_rotation.get('y', target_root_euler[1])
        target_root_euler[2] += target_rotation.get('z', target_root_euler[2])
    elif random_root:
        # Random rotation around Y-axis (0 to 360 degrees)
        target_root_euler[1] = np.random.random(1) * 360
    else:
        # Default orientation: standing upright, facing forward
        target_root_euler[0] = -90  # X rotation to stand up
        target_root_euler[1] = 0    # No Y rotation
        target_root_euler[2] = -90  # Z rotation to face forward
    
    # Convert back to radians for internal calculations
    target_root_rot = sRot.from_euler("xyz", target_root_euler, degrees=True)
    target_root_aa = target_root_rot.as_rotvec()
    
    target_root_mat = target_root_rot.as_matrix()
    root_mat = root_rot.as_matrix()
    apply_mat = np.matmul(target_root_mat, np.linalg.inv(root_mat))
    
    if torch.is_tensor(pose_aa):
        pose_aa = vertizalize_smpl_root(pose_aa, root_vec=target_root_aa)
    else:
        pose_aa = vertizalize_smpl_root(torch.from_numpy(pose_aa), root_vec=target_root_aa)
    
    if trans is not None:
        trans[:, [0, 1]] -= trans[0, [0, 1]]
        trans[:, [2]] = trans[:, [2]] - trans[0, [2]] + 0.91437225
        trans = np.matmul(apply_mat, trans.T).T
    
    return pose_aa, trans

# Helper function to get current rotation in degrees
def get_current_rotation(pose_aa):
    """
    Get current root rotation in degrees.
    
    Args:
        pose_aa: SMPL pose in axis-angle format
    
    Returns:
        dict: Current rotation angles in degrees {'x': float, 'y': float, 'z': float}
    """
    root_aa = pose_aa[0, :3]
    root_rot = sRot.from_rotvec(np.array(root_aa))
    euler_angles = root_rot.as_euler("xyz", degrees=True)
    
    return {
        'x': euler_angles[0],
        'y': euler_angles[1],
        'z': euler_angles[2]
    }

def rotate_smpl_pose(pose_aa, trans=None, target_rotation=None):
    """
    Rotate SMPL pose with specified rotations without normalization.
    """
    if target_rotation is None:
        return pose_aa, trans
        
    root_aa = pose_aa[0, :3]
    root_rot = sRot.from_rotvec(np.array(root_aa))
    root_euler = np.array(root_rot.as_euler("xyz", degrees=True))
    
    print(f"Initial root rotation (degrees): {root_euler}")
    
    # Instead of adding to current rotation, set absolute rotation while preserving Y
    target_root_euler = root_euler.copy()
    if 'x' in target_rotation:
        # Preserve some of the original X rotation to prevent flying
        current_x = root_euler[0]
        target_x = target_rotation['x']
        # Smooth transition between current and target X rotation
        target_root_euler[0] = target_x + (current_x * 0.2)  # Keep 20% of original rotation
        
    if 'y' in target_rotation:
        # Y rotation is usually safe to apply directly
        target_root_euler[1] = target_rotation['y']
        
    if 'z' in target_rotation:
        # For Z rotation, also preserve some original rotation
        current_z = root_euler[2]
        target_z = target_rotation['z']
        target_root_euler[2] = target_z + (current_z * 0.2)  # Keep 20% of original rotation
    
    # Normalize all angles to -180 to 180 range
    target_root_euler = np.array([((angle + 180) % 360) - 180 for angle in target_root_euler])
    
    print(f"Target root rotation (degrees): {target_root_euler}")
    
    # Convert to rotation matrix with extra validation
    target_root_rot = sRot.from_euler("xyz", target_root_euler, degrees=True)
    target_root_aa = target_root_rot.as_rotvec()
    
    target_root_mat = target_root_rot.as_matrix()
    root_mat = root_rot.as_matrix()
    
    # Calculate transformation
    apply_mat = np.matmul(target_root_mat, np.linalg.inv(root_mat))
    
    if torch.is_tensor(pose_aa):
        pose_aa = vertizalize_smpl_root(pose_aa, root_vec=target_root_aa)
    else:
        pose_aa = vertizalize_smpl_root(torch.from_numpy(pose_aa), root_vec=target_root_aa)
    
    if trans is not None:
        # Preserve original height more strongly
        original_height = trans[0, 2]
        trans_rotated = np.matmul(apply_mat, trans.T).T
        
        # Blend between original and rotated height
        trans_rotated[:, 2] = original_height * 0.8 + trans_rotated[:, 2] * 0.2
        
        # Ensure height stays reasonable
        min_height = 0.7  # Minimum reasonable height
        max_height = 1.2  # Maximum reasonable height
        trans_rotated[:, 2] = np.clip(trans_rotated[:, 2], min_height, max_height)
        
        trans = trans_rotated
    
    # Verify final pose
    final_root_rot = sRot.from_rotvec(pose_aa[0, :3])
    final_euler = final_root_rot.as_euler("xyz", degrees=True)
    print(f"Final root rotation (degrees): {final_euler}")
    
    return pose_aa, trans