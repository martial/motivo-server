import humenv
from humenv import rewards as humenv_rewards
from humenv.env import make_from_name
import inspect
import itertools

def try_reward_name(name):
    """Try to create a reward from a name pattern"""
    try:
        reward = make_from_name(name)
        return True
    except:
        return False

def generate_ego_move_rewards():
    """Generate all possible ego movement reward names"""
    speeds = [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]
    angles = [0, -90, 90, 180]  # Added angles based on LOCOMOTION_TASKS
    rewards = []
    for speed, angle in itertools.product(speeds, angles):
        name = f"move-ego-{angle}-{speed}"
        if try_reward_name(name):
            rewards.append(name)
    return rewards

def generate_raise_arms_rewards():
    """Generate all possible raise arms reward names"""
    positions = ['l', 'm', 'h']  # low, medium, high
    rewards = []
    for left, right in itertools.product(positions, positions):
        name = f"raisearms-{left}-{right}"
        if try_reward_name(name):
            rewards.append(name)
    return rewards

def generate_crawl_rewards():
    """Generate all possible crawl reward names"""
    heights = [0.3, 0.4, 0.5]
    speeds = [0, 1, 2]
    directions = ['u', 'd']
    rewards = []
    for height, speed, direction in itertools.product(heights, speeds, directions):
        name = f"crawl-{height}-{speed}-{direction}"
        if try_reward_name(name):
            rewards.append(name)
    return rewards

def print_all_rewards():
    print("\n=== Available Reward Classes and Their Parameters ===\n")
    
    # Get all reward classes
    reward_classes = [obj for name, obj in inspect.getmembers(humenv_rewards) 
                     if inspect.isclass(obj) and 'Reward' in name]
    
    for reward_class in sorted(reward_classes, key=lambda x: x.__name__):
        print(f"\n=== {reward_class.__name__} ===")
        if reward_class.__doc__:
            print(f"Description: {reward_class.__doc__.strip()}")
            
        # Get initialization parameters
        try:
            init_signature = inspect.signature(reward_class.__init__)
            params = init_signature.parameters
            if params:
                print("\nParameters:")
                for name, param in params.items():
                    if name != 'self':
                        default = param.default if param.default != inspect.Parameter.empty else "Required"
                        print(f"- {name}: {param.annotation.__name__ if param.annotation != inspect.Parameter.empty else 'Any'} = {default}")
        except:
            print("(Could not retrieve parameters)")

    print("\n\n=== Pre-configured Reward Names ===\n")
    
    # Basic static rewards
    print("Basic Static Rewards:")
    static_rewards = [
        "stand",              # Standing still
        "headstand",          # Headstand position
        "liedown-up",         # Lie on back
        "liedown-down",       # Lie face down
        "sit",               # Sitting position
        "split-0.5",         # Small split
        "split-1",           # Full split
        "jump-2"             # Jump with height 2
    ]
    
    for reward in static_rewards:
        if try_reward_name(reward):
            print(f"- {reward}")
    
    print("\nEgo Movement Rewards (moving relative to body orientation):")
    ego_rewards = generate_ego_move_rewards()
    for reward in sorted(ego_rewards):
        print(f"- {reward}")
    
    print("\nRaise Arms Rewards:")
    arm_rewards = generate_raise_arms_rewards()
    for reward in sorted(arm_rewards):
        print(f"- {reward}")
        
    print("\nCrawling Rewards:")
    crawl_rewards = generate_crawl_rewards()
    for reward in sorted(crawl_rewards):
        print(f"- {reward}")
        
    print("\nRotation Rewards:")
    rotation_rewards = []
    for axis in ['x', 'y', 'z']:
        for speed in [-5, 5]:
            name = f"rotate-{axis}-{speed}-0.8"
            if try_reward_name(name):
                rotation_rewards.append(name)
    for reward in sorted(rotation_rewards):
        print(f"- {reward}")
        
    print("\nNote: You can also create custom rewards by instantiating the reward classes")
    print("with specific parameters.")

if __name__ == "__main__":
    print_all_rewards()

'''
(motivo) (base) screen-club@mac motivo % python 002_print_rewards.py

=== Available Reward Classes and Their Parameters ===


=== ArmsReward ===
Description: ArmsReward(stand_height: float = 1.4, left_pose: str = 'h', right_pose: str = 'h')

Parameters:
- stand_height: float = 1.4
- left_pose: str = h
- right_pose: str = h

=== CrawlReward ===
Description: CrawlReward(spine_height: float = 0.3, move_angle: float = 0, move_speed: float = 1, direction: float = -1)

Parameters:
- spine_height: float = 0.3
- move_angle: float = 0
- move_speed: float = 1
- direction: float = -1

=== HeadstandReward ===
Description: HeadstandReward(stand_pelvis_height: float = 0.95)

Parameters:
- stand_pelvis_height: float = 0.95

=== JumpReward ===
Description: JumpReward(jump_height: float = 1.6, max_velocity: float = 5.0)

Parameters:
- jump_height: float = 1.6
- max_velocity: float = 5.0

=== LieDownReward ===
Description: LieDownReward(direction: str = 'up')

Parameters:
- direction: str = up

=== LocomotionReward ===
Description: LocomotionReward(move_speed: float = 5, stand_height: float = 1.4, move_angle: float = 0, egocentric_target: bool = True, low_height: float = 0.6, stay_low: bool = False)

Parameters:
- move_speed: float = 5
- stand_height: float = 1.4
- move_angle: float = 0
- egocentric_target: bool = True
- low_height: float = 0.6
- stay_low: bool = False

=== MoveAndRaiseArmsReward ===
Description: MoveAndRaiseArmsReward(low_height: float = 0.6, stand_height: float = 1.4, move_speed: float = 5, move_angle: float = 0, stay_low: bool = False, egocentric_target: bool = True, visualize_target_angle: bool = True, left_pose: str = 'h', right_pose: str = 'h', arm_coeff: float = 1.0, loc_coeff: float = 1.0)

Parameters:
- low_height: float = 0.6
- stand_height: float = 1.4
- move_speed: float = 5
- move_angle: float = 0
- stay_low: bool = False
- egocentric_target: bool = True
- visualize_target_angle: bool = True
- left_pose: str = h
- right_pose: str = h
- arm_coeff: float = 1.0
- loc_coeff: float = 1.0

=== RewardFunction ===

Parameters:
- args: Any = Required
- kwargs: Any = Required

=== RotationReward ===
Description: RotationReward(axis: str = 'x', target_ang_velocity: float = 5.0, stand_pelvis_height: float = 0.8)

Parameters:
- axis: str = x
- target_ang_velocity: float = 5.0
- stand_pelvis_height: float = 0.8

=== SitOnGroundReward ===
Description: SitOnGroundReward(pelvis_height_th: float = 0, constrained_knees: bool = False, knees_not_on_ground: bool = False)

Parameters:
- pelvis_height_th: float = 0
- constrained_knees: bool = False
- knees_not_on_ground: bool = False

=== SplitReward ===
Description: SplitReward(distance: float = 1.5)

Parameters:
- distance: float = 1.5

=== ZeroReward ===
Description: ZeroReward()

Parameters:


=== Pre-configured Reward Names ===

Basic Static Rewards:
- stand
- headstand
- liedown-up
- liedown-down
- sit
- split-0.5
- split-1
- jump-2

- rotate-x-5-0.8
World Movement Rewards (moving in absolute directions):
'''