import numpy as np
import torch
from humenv import rewards as humenv_rewards
from humenv.env import make_from_name
from metamotivo.wrappers.humenvbench import relabel
from task_rewards import (
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
from behaviour_rewards import (
    StandingReward,
    UprightReward,
    MovementControlReward,
    SmallControlReward,
    PositionReward,
    BalanceReward,
    SymmetryReward,
    EnergyEfficiencyReward,
    NaturalMotionReward,
    GazeDirectionReward,
    GroundContactReward,
    StableStandingReward,
    NaturalWalkingReward
)
from position_rewards import PositionReward, PositionTarget
import inspect
import sys
from contextlib import nullcontext
import os
from concurrent.futures import ThreadPoolExecutor
import torch.multiprocessing as mp

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
            stand_pelvis_height=reward_type.get('stand_pelvis_height', 0.95)
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
            stand_pelvis_height=reward_type.get('stand_pelvis_height', 0.95)
        ), weight)
    elif name == 'liedown':
        return (humenv_rewards.LieDownReward(
            direction=reward_type.get('direction', 'up')
        ), weight)
    elif name == 'sit':
        return (humenv_rewards.SitOnGroundReward(
            pelvis_height_th=reward_type.get('pelvis_height_th', 0),
            constrained_knees=reward_type.get('constrained_knees', True),
            knees_not_on_ground=reward_type.get('knees_not_on_ground', False)
        ), weight)
    elif name == 'split':
        return (humenv_rewards.SplitReward(
            distance=reward_type.get('distance', 1.5)
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
            loc_coeff=reward_type.get('loc_coeff', 1.0),
            visualize_target_angle=reward_type.get('visualize_target_angle', True)
        ), weight)
    
    # Handle custom reward types not in humenv.rewards
    elif name == 'stay-upright':
        return (StayUprightReward(), weight)
    
    # Handle behaviour rewards
    elif name == 'standing':
        return (StandingReward(
            target_height=reward_type.get('target_height', 1.4),
            margin=reward_type.get('margin', 0.2)
        ), weight)
    elif name == 'upright':
        return (UprightReward(
            min_upright=reward_type.get('min_upright', 0.9),
            margin=reward_type.get('margin', 1.9)
        ), weight)
    elif name == 'movement-control':
        return (MovementControlReward(
            margin=reward_type.get('margin', 0.5)
        ), weight)
    elif name == 'small-control':
        return (SmallControlReward(
            margin=reward_type.get('margin', 1.0),
            weight=reward_type.get('control_weight', 0.8)
        ), weight)
    elif name == 'position':
        # Adapt to match the WebSocket API format
        targets = {}
        for target in reward_type.get('targets', []):
            body_name = target['body']
            targets[body_name] = PositionTarget(
                x=target.get('x'),
                y=target.get('y'),
                z=target.get('z'),
                weight=target.get('weight', 1.0),
                margin=target.get('margin', 0.2)
            )
        
        return (PositionReward(
            targets=targets,
            upright_weight=reward_type.get('upright_weight', 0.3),
            control_weight=reward_type.get('control_weight', 0.2)
        ), weight)
    elif name == 'balance':
        return (BalanceReward(
            margin=reward_type.get('margin', 0.2)
        ), weight)
    elif name == 'symmetry':
        return (SymmetryReward(
            weight_hands=reward_type.get('weight_hands', 0.5),
            weight_feet=reward_type.get('weight_feet', 0.5),
            margin=reward_type.get('margin', 0.2)
        ), weight)
    elif name == 'energy-efficiency':
        return (EnergyEfficiencyReward(
            vel_margin=reward_type.get('vel_margin', 1.0),
            ctrl_margin=reward_type.get('ctrl_margin', 0.5)
        ), weight)
    elif name == 'natural-motion':
        return (NaturalMotionReward(
            smoothness_weight=reward_type.get('smoothness_weight', 0.5),
            coordination_weight=reward_type.get('coordination_weight', 0.5)
        ), weight)
    elif name == 'gaze-direction':
        return (GazeDirectionReward(
            target_point=np.array(reward_type.get('target_point', [1.0, 0.0, 1.7])),
            angle_margin=reward_type.get('angle_margin', 0.5)
        ), weight)
    elif name == 'ground-contact':
        return (GroundContactReward(
            desired_contacts=reward_type.get('desired_contacts', ['L_Toe', 'R_Toe'])
        ), weight)
    elif name == 'stable-standing':
        return (StableStandingReward(
            standing_weight=reward_type.get('standing_weight', 0.3),
            upright_weight=reward_type.get('upright_weight', 0.3),
            balance_weight=reward_type.get('balance_weight', 0.2),
            control_weight=reward_type.get('control_weight', 0.2)
        ), weight)
    elif name == 'natural-walking':
        return (NaturalWalkingReward(
            balance_weight=reward_type.get('balance_weight', 0.3),
            energy_weight=reward_type.get('energy_weight', 0.2),
            symmetry_weight=reward_type.get('symmetry_weight', 0.2),
            natural_motion_weight=reward_type.get('natural_motion_weight', 0.3)
        ), weight)
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
    combination_type = reward_config.get('combination_type', 'geometric')
    
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
    if torch.backends.mps.is_available():
        print("Using Apple Silicon MPS device")
        return torch.device('mps'), torch.float32
    elif torch.cuda.is_available():
        return torch.device('cuda'), torch.float32
    return torch.device('cpu'), torch.float64  # CPU can handle float64

def get_available_memory():
    """Get available memory based on device type"""
    device = get_compute_device()[0]
    if device.type == 'cuda':
        total_memory = torch.cuda.get_device_properties(0).total_memory
        free_memory = torch.cuda.memory_reserved(0) - torch.cuda.memory_allocated(0)
        return total_memory, free_memory
    elif device.type == 'mps':
        # MPS doesn't provide direct memory info, use system memory as proxy
        import psutil
        total_memory = psutil.virtual_memory().total
        free_memory = psutil.virtual_memory().available
        return total_memory, free_memory
    else:
        # For CPU, use system memory
        import psutil
        total_memory = psutil.virtual_memory().total
        free_memory = psutil.virtual_memory().available
        return total_memory, free_memory

def parallel_reward_compute(reward_fn, weight, batch_data, device, dtype, batch_size, env, chunk_size=1000, scaler=None):
    """Optimized parallel reward computation with mixed precision support"""
    rewards_batch = torch.zeros(batch_size, device=device, dtype=dtype)
    
    # Convert weight to correct dtype
    weight = torch.as_tensor(weight, device=device, dtype=dtype)
    
    # Use multiple workers for CPU computation
    num_workers = min(os.cpu_count(), 8) if device.type == 'cpu' else 1  # Cap at 8 workers
    
    # Pre-allocate shared memory for parallel processing
    if device.type == 'cpu':
        shared_rewards = torch.zeros(batch_size, dtype=dtype).share_memory_()
    else:
        shared_rewards = None
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        
        for i in range(0, batch_size, chunk_size):
            end_idx = min(i + chunk_size, batch_size)
            chunk_data = {k: v[i:end_idx].clone() for k, v in batch_data.items()}
            
            future = executor.submit(
                _compute_chunk_rewards,
                reward_fn, weight, chunk_data, device, dtype, env,
                shared_rewards[i:end_idx] if shared_rewards is not None else None,
                scaler=scaler
            )
            futures.append((i, future))
        
        for i, future in futures:
            chunk_rewards = future.result()
            if shared_rewards is None:  # GPU/MPS mode
                end_idx = min(i + chunk_size, batch_size)
                rewards_batch[i:end_idx] = chunk_rewards
    
    # Copy from shared memory if using CPU
    if shared_rewards is not None:
        rewards_batch.copy_(shared_rewards)
    
    return rewards_batch

def _compute_chunk_rewards(reward_fn, weight, chunk_data, device, dtype, env, shared_output=None, scaler=None):
    """Helper function to compute rewards for a chunk of data"""
    chunk_size = next(iter(chunk_data.values())).shape[0]
    
    # Use shared memory if provided (CPU mode), otherwise create new tensor
    if shared_output is not None:
        chunk_rewards = shared_output
    else:
        chunk_rewards = torch.zeros(chunk_size, device=device, dtype=dtype)
    
    try:
        # Convert data to numpy once outside the loop
        qpos_np = chunk_data['next_qpos'].cpu().numpy()
        qvel_np = chunk_data['next_qvel'].cpu().numpy()
        action_np = chunk_data['action'].cpu().numpy()
        
        # Vectorize reward computation if possible
        if hasattr(reward_fn, 'compute_vectorized'):
            # MPS doesn't support autocast, so we only use it for CUDA
            with (torch.cuda.amp.autocast() if device.type == 'cuda' else nullcontext()):
                rewards = reward_fn.compute_vectorized(
                    env.unwrapped.model,
                    qpos_np,
                    qvel_np,
                    action_np
                )
                rewards_tensor = torch.tensor(rewards, device=device, dtype=dtype)
                if scaler is not None and device.type == 'cuda':
                    rewards_tensor = scaler.scale(rewards_tensor)
                chunk_rewards[:] = rewards_tensor * weight
        else:
            # Fallback to per-sample computation
            for j in range(chunk_size):
                with (torch.cuda.amp.autocast() if device.type == 'cuda' else nullcontext()):
                    reward = reward_fn(
                        env.unwrapped.model,
                        qpos_np[j],
                        qvel_np[j],
                        action_np[j]
                    )
                    
                    if scaler is not None and device.type == 'cuda':
                        reward = scaler.scale(torch.tensor(reward, device=device, dtype=dtype))
                    else:
                        reward = torch.tensor(reward, device=device, dtype=dtype)
                    
                    chunk_rewards[j] = reward * weight
    except Exception as e:
        print(f"Error in reward computation: {str(e)}")
        raise
    
    return chunk_rewards

def compute_reward_context_gpu(reward_config, env, model, buffer_data):
    """GPU/MPS-accelerated implementation with optimized batching"""
    device, dtype = get_compute_device()
    if device.type == 'cpu':
        print("No GPU/MPS acceleration available, falling back to CPU")
        return compute_reward_context_cpu(reward_config, env, model, buffer_data)
    
    # Ensure model is on the correct device
    model = model.to(device)
    
    combination_type = reward_config.get('combination_type', 'geometric')
    
    # Get memory info and adjust batch size
    total_memory, free_memory = get_available_memory()
    
    # Calculate memory requirements more accurately
    sample_sizes = {
        'next_qpos': buffer_data['next_qpos'][0].nbytes,
        'next_qvel': buffer_data['next_qvel'][0].nbytes,
        'action': buffer_data['action'][0].nbytes,
        'next_observation': buffer_data['next_observation'][0].nbytes
    }
    
    # Add overhead for temporary tensors and computations (2x factor)
    memory_per_sample = sum(sample_sizes.values()) * 2
    
    # Be conservative with memory usage
    memory_fraction = 0.3 if device.type == 'mps' else 0.4
    
    # Calculate batch size based on actual memory requirements
    theoretical_max_samples = int(free_memory * memory_fraction / memory_per_sample)
    batch_size = min(theoretical_max_samples, 30_000)
    batch_size = max(batch_size, 5_000)  # Minimum batch size
    
    print("\n" + "="*50)
    print(f"USING REWARD COMBINATION METHOD: {combination_type.upper()} ({device.type.upper()})")
    print(f"Using dtype: {dtype}, batch_size: {batch_size}")
    print(f"Memory: {free_memory/1024/1024:.1f}MB free of {total_memory/1024/1024:.1f}MB total")
    print(f"Memory per sample: {memory_per_sample/1024:.2f}KB")
    print(f"Sample sizes:")
    for name, size in sample_sizes.items():
        print(f"  - {name}: {size/1024:.2f}KB")
    print(f"Estimated batch memory: {(batch_size * memory_per_sample)/1024/1024:.1f}MB")
    print(f"Memory fraction: {memory_fraction:.1%}")
    print("="*50 + "\n")
    
    idx = np.random.randint(0, len(buffer_data['next_qpos']), batch_size)
    
    # Move data to device with correct dtype
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
    
    # Optimize chunk size based on device type
    chunk_size = 1000 if device.type == 'mps' else 2000
    
    # Scaler only for CUDA
    scaler = torch.cuda.amp.GradScaler() if device.type == 'cuda' else None
    
    try:
        # Compute rewards with correct dtype and optimized batching
        computed_rewards = None  # Initialize to None for error handling
        
        if combination_type == 'additive':
            computed_rewards = torch.zeros(batch_size, device=device, dtype=dtype)
            for reward_fn, weight in rewards:
                with (torch.cuda.amp.autocast() if device.type == 'cuda' else nullcontext()):
                    computed_rewards += parallel_reward_compute(
                        reward_fn, weight, batch, device, dtype, batch_size, env,
                        chunk_size=chunk_size, scaler=scaler
                    )
        elif combination_type == 'multiplicative':
            computed_rewards = torch.ones(batch_size, device=device, dtype=dtype)
            for reward_fn, weight in rewards:
                with (torch.cuda.amp.autocast() if device.type == 'cuda' else nullcontext()):
                    computed_rewards *= parallel_reward_compute(
                        reward_fn, weight, batch, device, dtype, batch_size, env,
                        chunk_size=chunk_size, scaler=scaler
                    ) ** weight
        elif combination_type in ['min', 'max']:
            rewards_list = []
            for reward_fn, weight in rewards:
                with (torch.cuda.amp.autocast() if device.type == 'cuda' else nullcontext()):
                    rewards_list.append(
                        parallel_reward_compute(
                            reward_fn, weight, batch, device, dtype, batch_size, env,
                            chunk_size=chunk_size, scaler=scaler
                        )
                    )
            computed_rewards = torch.stack(rewards_list).min(dim=0)[0] if combination_type == 'min' else torch.stack(rewards_list).max(dim=0)[0]
        elif combination_type == 'geometric':
            epsilon = torch.tensor(1e-8, device=device, dtype=dtype)
            rewards_list = []
            for reward_fn, weight in rewards:
                with (torch.cuda.amp.autocast() if device.type == 'cuda' else nullcontext()):
                    rewards_list.append(
                        torch.max(
                            parallel_reward_compute(
                                reward_fn, weight, batch, device, dtype, batch_size, env,
                                chunk_size=chunk_size, scaler=scaler
                            ),
                            epsilon
                        )
                    )
            computed_rewards = torch.prod(torch.stack(rewards_list), dim=0) ** (1.0 / len(rewards))
        else:
            raise ValueError(f"Unknown combination type: {combination_type}")

        if computed_rewards is None:
            raise RuntimeError("Failed to compute rewards - no valid combination type found")

        print(f"Computed rewards shape: {computed_rewards.shape}, dtype: {computed_rewards.dtype}")
        
        # Ensure all tensors are on the same device for model inference
        next_obs = batch['next_observation'].to(device)
        computed_rewards = computed_rewards.reshape(-1, 1).to(device)
        
        # Perform model inference
        with torch.no_grad():
            z = model.reward_wr_inference(
                next_obs=next_obs,
                reward=computed_rewards
            )
        
        print(f"Computed z shape: {z.shape}, dtype: {z.dtype}, device: {z.device}")
        return z
        
    except Exception as e:
        print(f"Error in reward computation: {str(e)}")
        print(f"Device info:")
        print(f"- Model device: {next(model.parameters()).device}")
        if computed_rewards is not None:
            print(f"- Computed rewards device: {computed_rewards.device}")
        else:
            print("- Computed rewards: Not yet initialized")
        print(f"- Next observation device: {batch['next_observation'].device}")
        raise
    finally:
        if device.type == 'cuda':
            torch.cuda.empty_cache()

def compute_q_value(model, observation, z, action=None):
    """Compute Q-value using forward map and z projections"""
    device = next(model.parameters()).device  # Get the device from the model
    
    with torch.no_grad():
        # Move tensors to the same device as the model
        obs_tensor = torch.tensor(observation, device=device, dtype=torch.float32)
        if len(obs_tensor.shape) == 1:
            obs_tensor = obs_tensor.unsqueeze(0)
        
        # Ensure z is on the correct device
        z = z.to(device)
            
        # If no action is provided, get the optimal action from the actor
        if action is None:
            action = model.act(obs_tensor, z, mean=True)
        else:
            action = torch.tensor(action, device=device, dtype=torch.float32)
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
    
    print("\n=== Behaviour Rewards ===")
    behaviour_rewards = [
        "standing (params: target_height, margin)",
        "upright (params: min_upright, margin)",
        "movement-control (params: margin)",
        "small-control (params: margin, control_weight)",
        "position (params: body_name, target_pos, margin)",
        "balance (params: margin)",
        "symmetry (params: weight_hands, weight_feet, margin)",
        "energy-efficiency (params: vel_margin, ctrl_margin)",
        "natural-motion (params: smoothness_weight, coordination_weight)",
        "gaze-direction (params: target_point, angle_margin)",
        "ground-contact (params: desired_contacts)"
    ]
    
    for reward in behaviour_rewards:
        print(f"  - {reward}")
    
    print("\n=== Combined Behaviour Rewards ===")
    combined_rewards = [
        "stable-standing (params: standing_weight, upright_weight, balance_weight, control_weight)",
        "natural-walking (params: balance_weight, energy_weight, symmetry_weight, natural_motion_weight)"
    ]
    
    for reward in combined_rewards:
        print(f"  - {reward}") 