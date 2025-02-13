"""
Core reward components for humanoid control.
These can be used individually or combined to create complex behaviors.
"""

import numpy as np
from humenv import rewards as humenv_rewards
from dm_control.utils import rewards
import mujoco
from typing import Optional
import dataclasses

# Utility functions
def get_xpos(model, data, name):
    """Get position of a named body."""
    return data.xpos[model.body(name).id]

def get_xmat(model, data, name):
    """Get rotation matrix of a named body."""
    return data.xmat[model.body(name).id].reshape(3, 3)

def get_chest_upright(model, data):
    """Get upright value of the chest."""
    return data.xmat[model.body('Torso').id][2, 2]

def get_center_of_mass(model, data):
    """Calculate center of mass of the humanoid."""
    total_mass = 0
    weighted_pos = np.zeros(3)
    
    for i in range(model.nbody):
        mass = model.body_mass[i]
        pos = data.xpos[i]
        weighted_pos += mass * pos
        total_mass += mass
    
    return weighted_pos / total_mass

def get_center_of_mass_linvel(model, data):
    """Calculate linear velocity of the center of mass."""
    total_mass = 0
    weighted_vel = np.zeros(3)
    
    for i in range(model.nbody):
        mass = model.body_mass[i]
        vel = data.cvel[i][:3]  # Linear velocity component
        weighted_vel += mass * vel
        total_mass += mass
    
    return weighted_vel / total_mass

@dataclasses.dataclass
class StandingReward(humenv_rewards.RewardFunction):
    """Rewards maintaining a target standing height."""
    target_height: float = 1.4
    margin: float = 0.2

    @classmethod
    def reward_from_name(cls, name):
        if name == 'standing':
            return cls()
        return None

    def compute(self, model: mujoco.MjModel, data: mujoco.MjData) -> float:
        head_height = get_xpos(model, data, name="Head")[-1]
        return rewards.tolerance(
            head_height,
            bounds=(self.target_height, float("inf")),
            margin=self.margin,
            value_at_margin=0.01,
            sigmoid="linear"
        )

@dataclasses.dataclass
class UprightReward(humenv_rewards.RewardFunction):
    """Rewards maintaining an upright posture."""
    min_upright: float = 0.9
    margin: float = 1.9

    @classmethod
    def reward_from_name(cls, name):
        if name == 'upright':
            return cls()
        return None

    def compute(self, model: mujoco.MjModel, data: mujoco.MjData) -> float:
        chest_upright = get_chest_upright(model, data)
        return rewards.tolerance(
            chest_upright,
            bounds=(self.min_upright, float("inf")),
            sigmoid="linear",
            margin=self.margin,
            value_at_margin=0
        )

@dataclasses.dataclass
class MovementControlReward(humenv_rewards.RewardFunction):
    """Penalizes excessive movement."""
    margin: float = 0.5

    @classmethod
    def reward_from_name(cls, name):
        if name == 'movement-control':
            return cls()
        return None

    def compute(self, model: mujoco.MjModel, data: mujoco.MjData) -> float:
        velocity = get_center_of_mass_linvel(model, data)
        return rewards.tolerance(
            velocity, 
            margin=self.margin
        ).mean()

@dataclasses.dataclass
class SmallControlReward(humenv_rewards.RewardFunction):
    """Penalizes large control inputs."""
    margin: float = 1.0
    weight: float = 0.8  # (4/5)

    @classmethod
    def reward_from_name(cls, name):
        if name == 'small-control':
            return cls()
        return None

    def compute(self, model: mujoco.MjModel, data: mujoco.MjData) -> float:
        control = rewards.tolerance(
            data.ctrl, 
            margin=self.margin, 
            value_at_margin=0, 
            sigmoid="quadratic"
        ).mean()
        return (self.weight * control) + (1 - self.weight)

@dataclasses.dataclass
class PositionReward(humenv_rewards.RewardFunction):
    """Rewards achieving a target position for a specific body part."""
    body_name: str
    target_pos: np.ndarray
    margin: float = 0.2
    
    @classmethod
    def reward_from_name(cls, name):
        if name == 'position':
            return cls(body_name="", target_pos=np.zeros(3))
        return None

    def compute(self, model: mujoco.MjModel, data: mujoco.MjData) -> float:
        current_pos = get_xpos(model, data, name=self.body_name)
        distance = np.linalg.norm(current_pos - self.target_pos)
        return rewards.tolerance(
            distance,
            bounds=(0, 0.1),
            margin=self.margin,
            value_at_margin=0.01,
            sigmoid="linear"
        )

@dataclasses.dataclass
class BalanceReward(humenv_rewards.RewardFunction):
    """Rewards maintaining balance over the support polygon."""
    margin: float = 0.2

    @classmethod
    def reward_from_name(cls, name):
        if name == 'balance':
            return cls()
        return None

    def compute(self, model: mujoco.MjModel, data: mujoco.MjData) -> float:
        com = get_center_of_mass(model, data)
        feet_center = (get_xpos(model, data, "L_Toe") + get_xpos(model, data, "R_Toe")) / 2
        horizontal_distance = np.linalg.norm(com[:2] - feet_center[:2])
        return rewards.tolerance(
            horizontal_distance,
            bounds=(0, 0.1),
            margin=self.margin,
            sigmoid="linear"
        )

@dataclasses.dataclass
class SymmetryReward(humenv_rewards.RewardFunction):
    """Rewards symmetric postures."""
    weight_hands: float = 0.5
    weight_feet: float = 0.5
    margin: float = 0.2

    @classmethod
    def reward_from_name(cls, name):
        if name == 'symmetry':
            return cls()
        return None

    def compute(self, model: mujoco.MjModel, data: mujoco.MjData) -> float:
        l_hand = get_xpos(model, data, "L_Hand")
        r_hand = get_xpos(model, data, "R_Hand")
        l_foot = get_xpos(model, data, "L_Toe")
        r_foot = get_xpos(model, data, "R_Toe")
        
        hand_symmetry = rewards.tolerance(
            np.abs(l_hand[0] + r_hand[0]),
            bounds=(0, 0.1),
            margin=self.margin,
            sigmoid="linear"
        )
        foot_symmetry = rewards.tolerance(
            np.abs(l_foot[0] + r_foot[0]),
            bounds=(0, 0.1),
            margin=self.margin,
            sigmoid="linear"
        )
        return self.weight_hands * hand_symmetry + self.weight_feet * foot_symmetry

@dataclasses.dataclass
class EnergyEfficiencyReward(humenv_rewards.RewardFunction):
    """Rewards energy-efficient movements."""
    vel_margin: float = 1.0
    ctrl_margin: float = 0.5

    @classmethod
    def reward_from_name(cls, name):
        if name == 'energy-efficiency':
            return cls()
        return None

    def compute(self, model: mujoco.MjModel, data: mujoco.MjData) -> float:
        joint_vel_cost = rewards.tolerance(
            data.qvel,
            margin=self.vel_margin,
            value_at_margin=0,
            sigmoid="quadratic"
        ).mean()
        
        control_cost = rewards.tolerance(
            data.ctrl,
            margin=self.ctrl_margin,
            value_at_margin=0,
            sigmoid="quadratic"
        ).mean()
        
        return (joint_vel_cost + control_cost) / 2

@dataclasses.dataclass
class NaturalMotionReward(humenv_rewards.RewardFunction):
    """Rewards smooth, coordinated movements."""
    smoothness_weight: float = 0.5
    coordination_weight: float = 0.5

    @classmethod
    def reward_from_name(cls, name):
        if name == 'natural-motion':
            return cls()
        return None

    def compute(self, model: mujoco.MjModel, data: mujoco.MjData) -> float:
        # Compute motion smoothness based on velocity
        velocity_changes = np.diff(data.qvel)
        smoothness = 1.0 / (1.0 + np.mean(np.square(velocity_changes)))
        
        # Compute motion coordination based on joint velocities
        joint_correlations = np.corrcoef(data.qvel)
        coordination = np.mean(np.abs(joint_correlations))
        
        return (
            self.smoothness_weight * smoothness + 
            self.coordination_weight * coordination
        )

@dataclasses.dataclass
class GazeDirectionReward(humenv_rewards.RewardFunction):
    """Rewards looking at a specific target."""
    target_point: np.ndarray = dataclasses.field(default_factory=lambda: np.array([1.0, 0.0, 1.7]))
    angle_margin: float = 0.5

    @classmethod
    def reward_from_name(cls, name):
        if name == 'gaze-direction':
            return cls()
        return None

    def compute(self, model: mujoco.MjModel, data: mujoco.MjData) -> float:
        head_pos = get_xpos(model, data, "Head")
        head_rot = get_xmat(model, data, "Head")
        forward_vec = head_rot[:3, 0]
        
        target_dir = self.target_point - head_pos
        target_dir = target_dir / np.linalg.norm(target_dir)
        
        angle = np.arccos(np.clip(np.dot(forward_vec, target_dir), -1.0, 1.0))
        return rewards.tolerance(
            angle,
            bounds=(0, 0.1),
            margin=self.angle_margin,
            sigmoid="linear"
        )

@dataclasses.dataclass
class GroundContactReward(humenv_rewards.RewardFunction):
    """Rewards specific ground contact patterns."""
    desired_contacts: list = dataclasses.field(default_factory=lambda: ["L_Toe", "R_Toe"])

    @classmethod
    def reward_from_name(cls, name):
        if name == 'ground-contact':
            return cls()
        return None

    def compute(self, model: mujoco.MjModel, data: mujoco.MjData) -> float:
        contact_score = 0
        for i in range(data.ncon):
            contact = data.contact[i]
            geom1 = model.geom(contact.geom1).name
            geom2 = model.geom(contact.geom2).name
            if geom1 in self.desired_contacts or geom2 in self.desired_contacts:
                contact_score += 1
        
        return rewards.tolerance(
            contact_score,
            bounds=(len(self.desired_contacts), len(self.desired_contacts)),
            margin=1,
            sigmoid="linear"
        )

# Reward Combinations
@dataclasses.dataclass
class StableStandingReward(humenv_rewards.RewardFunction):
    """Combines multiple rewards for stable standing."""
    standing_weight: float = 0.3
    upright_weight: float = 0.3
    balance_weight: float = 0.2
    control_weight: float = 0.2

    @classmethod
    def reward_from_name(cls, name):
        if name == 'stable-standing':
            return cls()
        return None

    def compute(self, model: mujoco.MjModel, data: mujoco.MjData) -> float:
        standing = StandingReward().compute(model, data)
        upright = UprightReward().compute(model, data)
        balance = BalanceReward().compute(model, data)
        control = SmallControlReward().compute(model, data)
        
        return (self.standing_weight * standing +
                self.upright_weight * upright +
                self.balance_weight * balance +
                self.control_weight * control)

@dataclasses.dataclass
class NaturalWalkingReward(humenv_rewards.RewardFunction):
    """Combines rewards for natural walking motion."""
    balance_weight: float = 0.3
    energy_weight: float = 0.2
    symmetry_weight: float = 0.2
    natural_motion_weight: float = 0.3

    @classmethod
    def reward_from_name(cls, name):
        if name == 'natural-walking':
            return cls()
        return None

    def compute(self, model: mujoco.MjModel, data: mujoco.MjData) -> float:
        # Use reward_from_name instead of direct instantiation
        balance = BalanceReward().compute(model, data)
        energy = EnergyEfficiencyReward().compute(model, data)
        symmetry = SymmetryReward().compute(model, data)
        natural = NaturalMotionReward().compute(model, data)
        
        return (self.balance_weight * balance +
                self.energy_weight * energy +
                self.symmetry_weight * symmetry +
                self.natural_motion_weight * natural)

def print_available_rewards():
    """Print all available reward components and combinations."""
    print("\n=== Basic Reward Components ===")
    basic_rewards = [
        "StandingReward - Maintains target standing height",
        "UprightReward - Maintains upright posture",
        "MovementControlReward - Penalizes excessive movement",
        "SmallControlReward - Penalizes large control inputs",
        "PositionReward - Achieves target position for body parts"
    ]
    for reward in basic_rewards:
        print(f"  - {reward}")

    print("\n=== Advanced Reward Components ===")
    advanced_rewards = [
        "BalanceReward - Maintains balance over support polygon",
        "SymmetryReward - Rewards symmetric postures",
        "EnergyEfficiencyReward - Rewards energy-efficient movements",
        "NaturalMotionReward - Rewards smooth, coordinated movements",
        "GazeDirectionReward - Rewards looking at specific targets",
        "GroundContactReward - Rewards specific contact patterns"
    ]
    for reward in advanced_rewards:
        print(f"  - {reward}")

    print("\n=== Reward Combinations ===")
    combinations = [
        "StableStandingReward - Combined reward for stable standing",
        "NaturalWalkingReward - Combined reward for natural walking"
    ]
    for combo in combinations:
        print(f"  - {combo}") 