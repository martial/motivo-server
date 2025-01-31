import numpy as np
import torch
from humenv import rewards as humenv_rewards
from humenv.env import make_from_name
from metamotivo.wrappers.humenvbench import relabel
from custom_rewards import (
    StayUprightReward,
    HeadHeightReward,
    PelvisHeightReward,
    HandHeightReward,
    HandLateralDistanceReward,
    LeftHandHeightReward,
    LeftHandLateralDistanceReward,
    LeftHandForwardDistanceReward,
    RightHandHeightReward,
    RightHandLateralDistanceReward,
    RightHandForwardDistanceReward,
    LeftFootHeightReward,
    LeftFootLateralDistanceReward,
    LeftFootForwardDistanceReward,
    RightFootHeightReward,
    RightFootLateralDistanceReward,
    RightFootForwardDistanceReward,
    print_available_rewards
)
import inspect
import sys
import contextlib

def create_reward_function(reward_type, weight):
    """Create a reward function based on config"""
    name = reward_type['name']
    
    # Try to create standard reward first
    all_rewards = inspect.getmembers(sys.modules["humenv.rewards"], inspect.isclass)
    for reward_class_name, reward_cls in all_rewards:
        if not inspect.isabstract(reward_cls):
            try:
                reward_obj = reward_cls.reward_from_name(name)
                if reward_obj is not None:
                    return (reward_obj, weight)
            except Exception as e:
                continue
    
    # Handle basic movements
    if name == 'jump':
        return (humenv_rewards.JumpReward(
            jump_height=reward_type.get('jump_height', 1.6),
            max_velocity=reward_type.get('max_velocity', 5.0)
        ), weight)
    elif name == 'rotation':
        return (humenv_rewards.RotationReward(
            axis=reward_type.get('axis', 'x'),
            target_ang_velocity=reward_type.get('target_ang_velocity', 5.0),
            stand_pelvis_height=reward_type.get('stand_pelvis_height', 0.8)
        ), weight)
    elif name == 'crawl':
        return (humenv_rewards.CrawlReward(
            spine_height=reward_type.get('spine_height', 0.3),
            move_angle=reward_type.get('move_angle', 0),
            move_speed=reward_type.get('move_speed', 1),
            direction=reward_type.get('direction', -1)
        ), weight)
    
    # Handle poses
    elif name == 'raisearms':
        return (humenv_rewards.ArmsReward(
            stand_height=reward_type.get('stand_height', 1.4),
            left_pose=reward_type.get('left_pose', 'h'),
            right_pose=reward_type.get('right_pose', 'h')
        ), weight)
    elif name == 'headstand':
        return (humenv_rewards.HeadstandReward(
            balance_factor=reward_type.get('balance_factor', 1.0)
        ), weight)
    elif name == 'liedown':
        return (humenv_rewards.LieDownReward(
            target_height=reward_type.get('target_height', 0.2)
        ), weight)
    elif name == 'sit':
        return (humenv_rewards.SitReward(
            target_height=reward_type.get('target_height', 0.6)
        ), weight)
    elif name == 'split':
        return (humenv_rewards.SplitReward(
            target_angle=reward_type.get('target_angle', 180)
        ), weight)
    
    # Handle custom reward types with consistent parameter naming
    if name == 'head-height':
        return (HeadHeightReward(target_height=reward_type.get('target_height', 1.4)), weight)
    elif name == 'pelvis-height':
        return (PelvisHeightReward(target_height=reward_type.get('target_height', 0.8)), weight)
    elif name == 'hand-height':
        return (HandHeightReward(target_height=reward_type.get('target_height', 1.8)), weight)
    elif name == 'hand-lateral':
        return (HandLateralDistanceReward(target_distance=reward_type.get('target_distance', 0.5)), weight)
    elif name == 'left-hand-height':
        return (LeftHandHeightReward(target_height=reward_type.get('target_height', 1.0)), weight)
    elif name == 'left-hand-lateral':
        return (LeftHandLateralDistanceReward(target_distance=reward_type.get('target_distance', 0.5)), weight)
    elif name == 'left-hand-forward':
        return (LeftHandForwardDistanceReward(target_distance=reward_type.get('target_distance', 0.5)), weight)
    elif name == 'right-hand-height':
        return (RightHandHeightReward(target_height=reward_type.get('target_height', 1.0)), weight)
    elif name == 'right-hand-lateral':
        return (RightHandLateralDistanceReward(target_distance=reward_type.get('target_distance', 0.5)), weight)
    elif name == 'right-hand-forward':
        return (RightHandForwardDistanceReward(target_distance=reward_type.get('target_distance', 0.5)), weight)
    elif name == 'left-foot-height':
        return (LeftFootHeightReward(target_height=reward_type.get('target_height', 0.1)), weight)
    elif name == 'left-foot-lateral':
        return (LeftFootLateralDistanceReward(target_distance=reward_type.get('target_distance', 0.2)), weight)
    elif name == 'left-foot-forward':
        return (LeftFootForwardDistanceReward(target_distance=reward_type.get('target_distance', 0.2)), weight)
    elif name == 'right-foot-height':
        return (RightFootHeightReward(target_height=reward_type.get('target_height', 0.1)), weight)
    elif name == 'right-foot-lateral':
        return (RightFootLateralDistanceReward(target_distance=reward_type.get('target_distance', 0.2)), weight)
    elif name == 'right-foot-forward':
        return (RightFootForwardDistanceReward(target_distance=reward_type.get('target_distance', 0.2)), weight)
    
    # Handle configurable rewards that need custom parameters
    if name == 'move-ego':
        return (humenv_rewards.LocomotionReward(
            move_speed=reward_type.get('move_speed', 2.0),
            stand_height=reward_type.get('stand_height', 1.4),
            move_angle=reward_type.get('move_angle', 0),
            egocentric_target=reward_type.get('egocentric_target', True),
            low_height=reward_type.get('low_height', 0.6),
            stay_low=reward_type.get('stay_low', False)
        ), weight)
    
    elif name == 'move-and-raise-arms':
        return (humenv_rewards.MoveAndRaiseArmsReward(
            move_speed=reward_type.get('move_speed', 2.0),
            move_angle=reward_type.get('move_angle', 0),
            left_pose=reward_type.get('left_pose', 'h'),
            right_pose=reward_type.get('right_pose', 'h'),
            stand_height=reward_type.get('stand_height', 1.4),
            low_height=reward_type.get('low_height', 0.6),
            stay_low=reward_type.get('stay_low', False),
            egocentric_target=reward_type.get('egocentric_target', True),
            arm_coeff=reward_type.get('arm_coeff', 1.0),
            loc_coeff=reward_type.get('loc_coeff', 1.0)
        ), weight)
    
    # Handle custom reward types not in humenv.rewards
    elif name == 'stay-upright':
        return (StayUprightReward(), weight)
    else:
        raise ValueError(f"Unknown reward type: {name}")

def compute_reward_context(reward_config, env, model, buffer_data, use_gpu=True):
    """Compute reward context with optional GPU acceleration"""
    if use_gpu:
        return compute_reward_context_gpu(reward_config, env, model, buffer_data)
    else:
        return compute_reward_context_cpu(reward_config, env, model, buffer_data)

def compute_reward_context_cpu(reward_config, env, model, buffer_data):
    """Original CPU implementation"""
    combination_type = reward_config.get('combination_type', 'multiplicative')
    
    print("\n" + "="*50)
    print(f"USING REWARD COMBINATION METHOD: {combination_type.upper()} (CPU)")
    print("="*50 + "\n")
    
    batch_size = 10_000
    idx = np.random.randint(0, len(buffer_data['next_qpos']), batch_size)
    
    batch = {
        'next_qpos': buffer_data['next_qpos'][idx],
        'next_qvel': buffer_data['next_qvel'][idx],
        'action': buffer_data['action'][idx],
        'next_observation': buffer_data['next_observation'][idx]
    }
    
    # Create reward functions based on config
    rewards = []
    weights = reward_config.get('weights', [1.0])
    
    for reward_type, weight in zip(reward_config['rewards'], weights):
        rewards.append(create_reward_function(reward_type, weight))
    
    def additive_reward_fn(*args, **kwargs):
        total_reward = 0
        for reward_fn, weight in rewards:
            total_reward += weight * reward_fn(*args, **kwargs)
        return total_reward
    
    def multiplicative_reward_fn(*args, **kwargs):
        total_reward = 1
        for reward_fn, weight in rewards:
            total_reward *= reward_fn(*args, **kwargs) ** weight
        return total_reward
    
    def min_reward_fn(*args, **kwargs):
        rewards_list = []
        for reward_fn, weight in rewards:
            rewards_list.append(weight * reward_fn(*args, **kwargs))
        return min(rewards_list)
    
    def max_reward_fn(*args, **kwargs):
        rewards_list = []
        for reward_fn, weight in rewards:
            rewards_list.append(weight * reward_fn(*args, **kwargs))
        return max(rewards_list)
    
    def geometric_mean_reward_fn(*args, **kwargs):
        rewards_list = []
        for reward_fn, weight in rewards:
            rewards_list.append(max(1e-8, reward_fn(*args, **kwargs)) ** weight)
        return np.prod(rewards_list) ** (1.0 / len(rewards_list))

    reward_combiners = {
        'additive': additive_reward_fn,
        'multiplicative': multiplicative_reward_fn,
        'min': min_reward_fn,
        'max': max_reward_fn,
        'geometric': geometric_mean_reward_fn
    }
    
    combined_reward_fn = reward_combiners.get(combination_type, additive_reward_fn)
    
    print(f"Computing reward context with {combined_reward_fn.__name__}")
    computed_rewards = relabel(
        env,
        qpos=batch['next_qpos'],
        qvel=batch['next_qvel'],
        action=batch['action'],
        reward_fn=combined_reward_fn,
        max_workers=8
    )
    
    print(f"Computed rewards: {computed_rewards}")
    z = model.reward_wr_inference(
        next_obs=torch.tensor(batch['next_observation'], device=model.cfg.device, dtype=torch.float32),
        reward=torch.tensor(computed_rewards, device=model.cfg.device, dtype=torch.float32)
    )
    print(f"Computed z: {z}")
    
    return z

def get_compute_device():
    """Determine the best available compute device and appropriate dtype"""
    if torch.cuda.is_available():
        return torch.device('cuda'), torch.float32
    elif torch.backends.mps.is_available():
        return torch.device('mps'), torch.float32
    return torch.device('cpu'), torch.float64  # CPU can handle float64

def parallel_reward_compute(reward_fn, weight, batch_data, device, dtype, batch_size, env):
    rewards_batch = torch.zeros(batch_size, device=device, dtype=dtype)
    chunk_size = 1000
    
    # Convert weight to correct dtype
    weight = torch.as_tensor(weight, device=device, dtype=dtype)
    
    for i in range(0, batch_size, chunk_size):
        end_idx = min(i + chunk_size, batch_size)
        chunk_data = {k: v[i:end_idx] for k, v in batch_data.items()}
        
        for j in range(end_idx - i):
            context_manager = (
                torch.cuda.amp.autocast() if device.type == 'cuda'
                else contextlib.nullcontext()
            )
            
            with context_manager:
                reward = reward_fn(
                    env.unwrapped.model,
                    chunk_data['next_qpos'][j].cpu().numpy().astype(np.float64),
                    chunk_data['next_qvel'][j].cpu().numpy().astype(np.float64),
                    chunk_data['action'][j].cpu().numpy().astype(np.float64)
                )
                reward_tensor = torch.tensor(reward, device=device, dtype=dtype)
                rewards_batch[i + j] = reward_tensor * weight
    
    return rewards_batch

def compute_reward_context_gpu(reward_config, env, model, buffer_data):
    """GPU-accelerated implementation with explicit dtype handling"""
    device, dtype = get_compute_device()
    if device.type == 'cpu':
        print("No GPU acceleration available, falling back to CPU")
        return compute_reward_context_cpu(reward_config, env, model, buffer_data)
    
    combination_type = reward_config.get('combination_type', 'multiplicative')
    batch_size = 10_000  # Moved up for clarity
    
    print("\n" + "="*50)
    print(f"USING REWARD COMBINATION METHOD: {combination_type.upper()} ({device.type.upper()})")
    print(f"Using dtype: {dtype}")
    print("="*50 + "\n")
    
    idx = np.random.randint(0, len(buffer_data['next_qpos']), batch_size)
    
    # Move data to accelerator device with correct dtype
    batch = {
        'next_qpos': torch.tensor(buffer_data['next_qpos'][idx], device=device, dtype=dtype),
        'next_qvel': torch.tensor(buffer_data['next_qvel'][idx], device=device, dtype=dtype),
        'action': torch.tensor(buffer_data['action'][idx], device=device, dtype=dtype),
        'next_observation': torch.tensor(buffer_data['next_observation'][idx], device=device, dtype=dtype)
    }
    
    # Create reward functions and weights with correct dtype
    rewards = []
    weights = torch.tensor(reward_config.get('weights', [1.0]), device=device, dtype=dtype)
    
    for reward_type, weight in zip(reward_config['rewards'], weights):
        rewards.append(create_reward_function(reward_type, weight))
    
    print(f"Computing reward context with {combination_type} combination")
    
    # Compute rewards with correct dtype
    if combination_type == 'additive':
        computed_rewards = torch.zeros(batch_size, device=device, dtype=dtype)
        for reward_fn, weight in rewards:
            computed_rewards += parallel_reward_compute(reward_fn, weight, batch, device, dtype, batch_size, env)
    elif combination_type == 'multiplicative':
        computed_rewards = torch.ones(batch_size, device=device, dtype=dtype)
        for reward_fn, weight in rewards:
            computed_rewards *= parallel_reward_compute(reward_fn, weight, batch, device, dtype, batch_size, env) ** weight
    elif combination_type == 'min':
        rewards_list = [parallel_reward_compute(reward_fn, weight, batch, device, dtype, batch_size, env) 
                       for reward_fn, weight in rewards]
        computed_rewards = torch.stack(rewards_list).min(dim=0)[0]
    elif combination_type == 'max':
        rewards_list = [parallel_reward_compute(reward_fn, weight, batch, device, dtype, batch_size, env) 
                       for reward_fn, weight in rewards]
        computed_rewards = torch.stack(rewards_list).max(dim=0)[0]
    elif combination_type == 'geometric':
        epsilon = torch.tensor(1e-8, device=device, dtype=dtype)
        rewards_list = [torch.max(parallel_reward_compute(reward_fn, weight, batch, device, dtype, batch_size, env), epsilon) 
                       for reward_fn, weight in rewards]
        computed_rewards = torch.prod(torch.stack(rewards_list), dim=0) ** (1.0 / len(rewards))
    else:
        raise ValueError(f"Unknown combination type: {combination_type}")

    print(f"Computed rewards shape: {computed_rewards.shape}, dtype: {computed_rewards.dtype}")
    
    # Ensure correct dtype for model inference
    z = model.reward_wr_inference(
        next_obs=batch['next_observation'],
        reward=computed_rewards.reshape(-1, 1)
    )
    print(f"Computed z shape: {z.shape}, dtype: {z.dtype}")
    
    return z

def compute_q_value(model, observation, z, action=None):
    """Compute Q-value using forward map and z projections"""
    with torch.no_grad():
        obs_tensor = torch.tensor(observation, device=model.cfg.device, dtype=torch.float32)
        if len(obs_tensor.shape) == 1:
            obs_tensor = obs_tensor.unsqueeze(0)
            
        # If no action is provided, get the optimal action from the actor
        if action is None:
            action = model.act(obs_tensor, z, mean=True)
        else:
            action = torch.tensor(action, device=model.cfg.device, dtype=torch.float32)
            if len(action.shape) == 1:
                action = action.unsqueeze(0)
        
        # Compute forward map
        F = model.forward_map(
            obs=obs_tensor, 
            z=z.repeat(obs_tensor.shape[0], 1), 
            action=action
        )
        
        # Compute z_reward using backward map
        z_reward = torch.sum(
            model.backward_map(obs=obs_tensor) * z,
            dim=0
        )
        z_reward = model.project_z(z_reward)
        
        # Compute Q-value using matrix multiplication
        Q = F @ z_reward.ravel()
        return Q.mean(axis=0).cpu().numpy().item()  # Convert to Python scalar 

def print_available_rewards():
    """Print all available reward types from both humenv.rewards and custom rewards"""
    print("\n=== Standard Rewards from humenv.rewards ===")
    all_rewards = inspect.getmembers(sys.modules["humenv.rewards"], inspect.isclass)
    for reward_class_name, reward_cls in all_rewards:
        if not inspect.isabstract(reward_cls):
            print(f"\n{reward_class_name}:")
            if hasattr(humenv, 'ALL_TASKS'):
                # Print predefined tasks for this reward type if available
                tasks = [task for task in humenv.ALL_TASKS if reward_cls.reward_from_name(task) is not None]
                if tasks:
                    print("  Predefined tasks:")
                    for task in tasks:
                        print(f"    - {task}")
    
    print("\n=== Custom Rewards ===")
    custom_rewards = [
        "stay-upright",
        "head-height (params: target_height)",
        "pelvis-height (params: target_height)",
        "hand-height (params: target_height)",
        "hand-lateral (params: target_distance)",
        "left-hand-height (params: target_height)",
        "left-hand-lateral (params: target_distance)",
        "left-hand-forward (params: target_distance)",
        "right-hand-height (params: target_height)",
        "right-hand-lateral (params: target_distance)",
        "right-hand-forward (params: target_distance)",
        "left-foot-height (params: target_height)",
        "left-foot-lateral (params: target_distance)",
        "left-foot-forward (params: target_distance)",
        "right-foot-height (params: target_height)",
        "right-foot-lateral (params: target_distance)",
        "right-foot-forward (params: target_distance)"
    ]
    
    for reward in custom_rewards:
        print(f"  - {reward}")
    
    print("\n=== Configurable Rewards ===")
    print("  - move-ego (params: move_speed, stand_height, move_angle, egocentric_target, low_height, stay_low)")
    print("  - move-and-raise-arms (params: move_speed, move_angle, left_pose, right_pose, stand_height, low_height, stay_low, egocentric_target, arm_coeff, loc_coeff)") 