"""
Advanced position-based rewards for precise 3D control of humanoid body parts.
"""

import numpy as np
from humenv import rewards as humenv_rewards
from dm_control.utils import rewards
import mujoco
from typing import Optional, Dict
import dataclasses
from humenv.rewards import get_chest_upright

@dataclasses.dataclass
class PositionTarget:
    """Target configuration for a body part."""
    x: Optional[float] = None  # None means this axis is ignored
    y: Optional[float] = None
    z: Optional[float] = None
    weight: float = 1.0
    margin: float = 0.2

@dataclasses.dataclass
class PositionReward(humenv_rewards.RewardFunction):
    """
    Reward for controlling multiple body parts' positions.
    Supports selective axis control with individual weights.
    """
    targets: Dict[str, PositionTarget]  # body_name -> target
    upright_weight: float = 0.3
    control_weight: float = 0.2

    def compute(self, model: mujoco.MjModel, data: mujoco.MjData) -> float:
        # Position rewards
        position_rewards = []
        total_weight = sum(target.weight for target in self.targets.values())

        for body_name, target in self.targets.items():
            current_pos = data.xpos[model.body(body_name).id].copy()
            axis_rewards = []

            # Check each axis
            if target.x is not None:
                x_reward = rewards.tolerance(
                    abs(current_pos[0] - target.x),
                    bounds=(0, target.margin),
                    margin=target.margin,
                    value_at_margin=0.01,
                    sigmoid="linear"
                )
                # Handle both tensor and float return types
                x_reward = x_reward.item() if hasattr(x_reward, 'item') else float(x_reward)
                axis_rewards.append(x_reward)

            if target.y is not None:
                y_reward = rewards.tolerance(
                    abs(current_pos[1] - target.y),
                    bounds=(0, target.margin),
                    margin=target.margin,
                    value_at_margin=0.01,
                    sigmoid="linear"
                )
                # Handle both tensor and float return types
                y_reward = y_reward.item() if hasattr(y_reward, 'item') else float(y_reward)
                axis_rewards.append(y_reward)

            if target.z is not None:
                z_reward = rewards.tolerance(
                    abs(current_pos[2] - target.z),
                    bounds=(0, target.margin),
                    margin=target.margin,
                    value_at_margin=0.01,
                    sigmoid="linear"
                )
                # Handle both tensor and float return types
                z_reward = z_reward.item() if hasattr(z_reward, 'item') else float(z_reward)
                axis_rewards.append(z_reward)

            if axis_rewards:
                # Multiplicative combination of axis rewards
                body_reward = np.prod(axis_rewards)
                weighted_reward = np.power(body_reward, target.weight / total_weight)
                position_rewards.append(weighted_reward)

        # Multiplicative combination of body part rewards
        position_reward = np.prod(position_rewards) if position_rewards else 0.0
        
        # Get upright reward
        upright_reward = get_chest_upright(model, data)
        upright_reward = upright_reward.item() if hasattr(upright_reward, 'item') else float(upright_reward)
        
        # Compute control cost (penalize large actions)
        ctrl = data.ctrl.copy()
        control_reward = rewards.tolerance(
            np.linalg.norm(ctrl),
            bounds=(0, 1),
            margin=1,
            value_at_margin=0,
            sigmoid="quadratic"
        )
        control_reward = control_reward.item() if hasattr(control_reward, 'item') else float(control_reward)
        
        # Combine rewards with weights
        final_reward = (
            (1 - self.upright_weight - self.control_weight) * position_reward +
            self.upright_weight * upright_reward +
            self.control_weight * control_reward
        )
        
        return float(final_reward)

    @staticmethod
    def reward_from_name(name: str) -> Optional["humenv_rewards.RewardFunction"]:
        """
        Parse reward configuration from name string.
        Format: position-{body1}-x{val}-y{val}-z{val}-w{val}_{body2}...
        Example: position-Head-x1.5-z1.7-w1.0_L_Hand-x0.5-y0.3-z1.2-w0.8
        """
        if not name.startswith("position-"):
            return None

        try:
            targets = {}
            parts = name[9:].split("_")  # Remove "position-" prefix
            
            for part in parts:
                configs = part.split("-")
                body_name = configs[0]
                target = PositionTarget()
                
                for config in configs[1:]:
                    if config.startswith("x"):
                        target.x = float(config[1:])
                    elif config.startswith("y"):
                        target.y = float(config[1:])
                    elif config.startswith("z"):
                        target.z = float(config[1:])
                    elif config.startswith("w"):
                        target.weight = float(config[1:])
                
                targets[body_name] = target

            return PositionReward(targets=targets)

        except (ValueError, IndexError) as e:
            print(f"Warning: Invalid position reward format: {name}")
            print(f"Error: {e}")
            return None

    @staticmethod
    def create(targets: Dict[str, PositionTarget]) -> "PositionReward":
        """
        Create a position reward directly with a dictionary of targets.
        
        Example:
        reward = PositionReward.create({
            "Head": PositionTarget(z=1.7, weight=1.0),
            "L_Hand": PositionTarget(x=0.5, y=0.3, z=1.2, weight=0.8)
        })
        """
        return PositionReward(targets=targets)

    @staticmethod
    def print_usage():
        """Print usage instructions."""
        print("\nPositionReward Usage:")
        print("\nMethod 1 - String format:")
        print("position-{body}-x{val}-y{val}-z{val}-w{val}_{body2}...")
        print("Example: position-Head-x1.5-z1.7-w1.0_L_Hand-x0.5-y0.3-z1.2-w0.8")
        
        print("\nMethod 2 - Direct creation:")
        print("""
reward = PositionReward.create({
    "Head": PositionTarget(z=1.7, weight=1.0),
    "L_Hand": PositionTarget(x=0.5, y=0.3, z=1.2, weight=0.8)
})
        """)
        
        print("\nAvailable body parts:")
        print("- Head, Pelvis")
        print("- L_Hand, R_Hand")
        print("- L_Toe, R_Toe")
        print("- Torso, Chest")
        
        print("\nParameters:")
        print("- x, y, z: target positions (optional)")
        print("- weight: importance (default: 1.0)")
        print("- margin: tolerance (default: 0.2)") 