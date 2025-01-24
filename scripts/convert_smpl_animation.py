"""Test converter module."""

import pickle
import numpy as np
from scipy.spatial.transform import Rotation as R
import argparse

ROOT_JOINT = "Root"
SKEL_JOINTS = [
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


def _write_curve(
    data: np.ndarray,
    offset: float = 0.0,
) -> None:
    data = np.squeeze(data)
    for i in range(data.shape[0]):
        key_value = data[i] + offset
        print(f"Frame {i}: {key_value}")


def _anim_rotation(
    euler,
    axes_order="XYZ",
    offset=(0, 0, 0),
) -> None:
    for idx, axe_name in enumerate(axes_order):
        print(f"\nRotation {axe_name}:")
        _write_curve(euler[:, idx], offset=offset[idx])


def _anim_translation(
    trans,
    axes_order="XYZ",
    offset=(0, 0, 0),
) -> None:
    for idx, axe_name in enumerate(axes_order):
        print(f"\nTranslation {axe_name}:")
        _write_curve(trans[:, idx], offset=offset[idx])

def _get_euler_from_smpl_poses(smpl_poses, idx) -> np.ndarray:
    rotvec = smpl_poses[:, idx * 3 : idx * 3 + 3]
    euler = []
    for _f in range(rotvec.shape[0]):
        rot = R.from_rotvec(
            [rotvec[_f, 0], rotvec[_f, 1], rotvec[_f, 2]],
        )
        _euler = rot.as_euler("xyz", degrees=True)
        euler.append([_euler[0], _euler[1], _euler[2]])
    return np.vstack(euler)


def main_test(pkl_path: str) -> None:
    scale: float = 1.0
    axes_order = (None,)
    pose_offset = (None,)
    bones_remap = (None,)
    
    with open(pkl_path, "rb") as pkl_file:
        smpl_data = pickle.load(pkl_file)

    # 1. Write smpl_poses
    smpl_poses = smpl_data["smpl_poses"]
    for idx, name in enumerate(SKEL_JOINTS):
        print(f"\n=== Processing joint: {name} ===")
        order = "XYZ"
        if axes_order and name in axes_order:
            order = axes_order[name]
        offset = [0, 0, 0]
        if pose_offset and name in pose_offset:
            offset = pose_offset[name]
        if bones_remap and name in bones_remap:
            name = bones_remap[name]
        euler = _get_euler_from_smpl_poses(smpl_poses, idx)
        _anim_rotation(euler)

    # 2. Write smpl_trans to f_avg_root
    print("\n=== Processing root translation ===")
    smpl_trans = smpl_data["smpl_trans"] * scale
    name = ROOT_JOINT
    if bones_remap and name in bones_remap:
        name = bones_remap[name]
    _anim_translation(smpl_trans)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert SMPL animation from pickle file.')
    parser.add_argument('pkl_path', type=str, help='Path to the SMPL pickle file')
    args = parser.parse_args()
    
    main_test(args.pkl_path)