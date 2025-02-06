from scipy.spatial.transform import Rotation as sRot
import numpy as np
import torch

# Since we're in the utils folder, use relative import with .
from .torch_geometry_transforms import angle_axis_to_rotation_matrix, rotation_matrix_to_quaternion

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
    body_qposaddr = get_body_qposaddr(mj_model)
    
    # Convert qpos to numpy if it's a torch tensor
    if hasattr(qpos, 'detach'):
        qpos = qpos.detach().cpu().numpy()
    
    # Ensure qpos is 2D
    if len(qpos.shape) == 1:
        qpos = qpos.reshape(1, -1)
    
    batch_size = qpos.shape[0]
    trans = qpos[:, :3] - mj_model.body_pos[1]
    smpl_bones_to_use = (SMPL_BONE_ORDER_NAMES if smpl_model == "smpl" else SMPLH_BONE_ORDER_NAMES)
    pose = np.zeros([batch_size, len(smpl_bones_to_use), 3])
    
    for ind1, bone_name in enumerate(smpl_bones_to_use):
        ind2 = body_qposaddr[bone_name]
       # print(f"ind1: {ind1}, Bone: {bone_name}, Indices: {ind2}")
        if ind1 == 0:
            quat = qpos[:, 3:7]
            pose[:, ind1, :] = sRot.from_quat(quat[:, [1, 2, 3, 0]]).as_rotvec()
        else:
            pose[:, ind1, :] = sRot.from_euler("XYZ", qpos[:, ind2[0]:ind2[1]]).as_rotvec()

    return pose, trans 



def smpl_to_qpose(
    pose,
    mj_model,
    trans=None,
    normalize=False,
    random_root=False,
    count_offset=True,
    use_quat=False,
    euler_order="ZYX",
    model="smpl",
):
    """
    Expect pose to be batch_size x 72
    trans to be batch_size x 3
    differentiable 
    """
    if trans is None:
        trans = np.zeros((pose.shape[0], 3))
        trans[:, 2] = 0.91437225
    if normalize:
        pose, trans = normalize_smpl_pose(pose, trans, random_root=random_root)

    if not torch.is_tensor(pose):
        pose = torch.tensor(pose)

    if model == "smpl":
        joint_names = SMPL_BONE_ORDER_NAMES
        if pose.shape[-1] == 156:
            pose = smplh_to_smpl(pose)
    elif model == "smplx":
        joint_names = SMPLH_BONE_ORDER_NAMES
        if pose.shape[-1] == 72:
            pose = smpl_to_smplh(pose)

    num_joints = len(joint_names)
    num_angles = num_joints * 3
    smpl_2_mujoco = [joint_names.index(q) for q in list(get_body_qposaddr(mj_model).keys()) if q in joint_names]

    pose = pose.reshape(-1, num_angles)

    curr_pose_mat = angle_axis_to_rotation_matrix(pose.reshape(-1, 3)).reshape(pose.shape[0], -1, 4, 4)

    curr_spose = sRot.from_matrix(curr_pose_mat[:, :, :3, :3].reshape(-1, 3, 3).numpy())
    if use_quat:
        curr_spose = curr_spose.as_quat()[:, [3, 0, 1, 2]].reshape(curr_pose_mat.shape[0], -1)
        num_angles = num_joints * (4 if use_quat else 3)
    else:
        curr_spose = curr_spose.as_euler(euler_order, degrees=False).reshape(curr_pose_mat.shape[0], -1)

    curr_spose = curr_spose.reshape(-1, num_joints, 4 if use_quat else 3)[:, smpl_2_mujoco, :].reshape(-1, num_angles)
    if use_quat:
        curr_qpos = np.concatenate([trans, curr_spose], axis=1)
    else:
        root_quat = rotation_matrix_to_quaternion(curr_pose_mat[:, 0, :3, :])
        curr_qpos = np.concatenate((trans, root_quat, curr_spose[:, 3:]), axis=1)

    if count_offset:

        curr_qpos[:, :3] = trans + mj_model.body_pos[1]

    return curr_qpos

def smplh_to_smpl(pose):
    batch_size = pose.shape[0]
    return torch.cat([pose[:, :66], torch.zeros((batch_size, 6))], dim=1)


def smpl_to_smplh(pose):
    batch_size = pose.shape[0]
    return torch.cat([pose[:, :66], torch.zeros((batch_size, 90))], dim=1)

def normalize_smpl_pose(pose_aa, trans=None, random_root=False):
    root_aa = pose_aa[0, :3]
    root_rot = sRot.from_rotvec(np.array(root_aa))
    root_euler = np.array(root_rot.as_euler("xyz", degrees=False))
    target_root_euler = (root_euler.copy())  # take away Z axis rotation so the human is always facing same direction
    if random_root:
        target_root_euler[2] = np.random.random(1) * np.pi * 2
    else:
        target_root_euler[2] = -1.57
    target_root_rot = sRot.from_euler("xyz", target_root_euler, degrees=False)
    target_root_aa = target_root_rot.as_rotvec()

    target_root_mat = target_root_rot.as_matrix()
    root_mat = root_rot.as_matrix()
    apply_mat = np.matmul(target_root_mat, np.linalg.inv(root_mat))

    if torch.is_tensor(pose_aa):
        pose_aa = vertizalize_smpl_root(pose_aa, root_vec=target_root_aa)
    else:
        pose_aa = vertizalize_smpl_root(torch.from_numpy(pose_aa), root_vec=target_root_aa)

    if not trans is None:
        trans[:, [0, 1]] -= trans[0, [0, 1]]
        trans[:, [2]] = trans[:, [2]] - trans[0, [2]] + 0.91437225
        trans = np.matmul(apply_mat, trans.T).T
    return pose_aa, trans