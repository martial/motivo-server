import torch
import cv2
import time
import h5py
import numpy as np
from humenv import make_humenv, rewards as humenv_rewards
from humenv.env import make_from_name
import gymnasium as gym
from gymnasium.wrappers import FlattenObservation, TransformObservation, TimeLimit
from metamotivo.fb_cpr.huggingface import FBcprModel
from huggingface_hub import hf_hub_download
from metamotivo.wrappers.humenvbench import relabel

def download_buffer(model_name="metamotivo-M-1", dataset="buffer_inference_500000.hdf5"):
    """Download inference buffer data"""
    local_dir = f"{model_name}-datasets"
    buffer_path = hf_hub_download(
        repo_id=f"facebook/{model_name}",
        filename=f"data/{dataset}",
        repo_type="model",
        local_dir=local_dir,
    )
    
    print(f"Loading buffer from: {buffer_path}")
    with h5py.File(buffer_path, "r") as hf:
        data = {k: np.array(v) for k, v in hf.items()}
    return data

def setup_basic_env(device, max_steps=1000):
    """Setup basic environment with humanoid"""
    # Create environment with proper wrappers
    env, info = make_humenv(
        num_envs=1,
        wrappers=[
            FlattenObservation,
            lambda env: TransformObservation(
                env, 
                lambda obs: torch.tensor(obs.reshape(1, -1), 
                                      dtype=torch.float32, 
                                      device=device),
                env.observation_space
            ),
        ],
    )
    
    # Set up physics parameters in the environment
    unwrapped_env = env.unwrapped
    unwrapped_env.model.opt.density = 1.2      # Air density (kg/m³)
    unwrapped_env.model.opt.wind = np.array([0., 0., 0.])  # Initial wind vector
    unwrapped_env.model.opt.viscosity = 0.0    # Fluid viscosity
    unwrapped_env.model.opt.integrator = 0     # 0: Euler, 1: RK4
    unwrapped_env.model.opt.timestep = 0.002   # Simulation timestep
    
    # Wrap environment with time limit
    env = TimeLimit(env, max_episode_steps=max_steps)
    return env

def get_reward_context(model, env, buffer_data, reward_config):
    """Get context vector based on reward configuration"""
    print("\nComputing reward context for combination:")
    for i, reward in enumerate(reward_config['rewards']):
        weight = reward_config.get('weights', [1.0])[i]
        print(f"- {reward['name']} (weight: {weight})")
    
    batch_size = 10_000  # Reduced for faster computation
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
        if reward_type['name'] == 'zero':
            rewards.append((
                humenv_rewards.ZeroReward(),
                weight
            ))
        elif reward_type['name'] == 'jump':
            rewards.append((
                humenv_rewards.JumpReward(
                    jump_height=reward_type.get('jump_height', 1.6),
                    max_velocity=reward_type.get('max_velocity', 5.0)
                ),
                weight
            ))
        elif reward_type['name'] == 'rotation':
            rewards.append((
                humenv_rewards.RotationReward(
                    axis=reward_type.get('axis', 'x'),
                    target_ang_velocity=reward_type.get('target_ang_velocity', 5.0),
                    stand_pelvis_height=reward_type.get('stand_pelvis_height', 0.8)
                ),
                weight
            ))
        elif reward_type['name'] == 'headstand':
            rewards.append((
                humenv_rewards.HeadstandReward(
                    stand_pelvis_height=reward_type.get('stand_pelvis_height', 0.95)
                ),
                weight
            ))
        elif reward_type['name'] == 'crawl':
            # Convert string direction to integer: 'u' -> 1, 'd' -> -1
            direction = 1 if reward_type.get('direction', 'u') == 'u' else -1
            rewards.append((
                humenv_rewards.CrawlReward(
                    spine_height=reward_type.get('spine_height', 0.3),
                    move_speed=reward_type.get('move_speed', 1.0),
                    direction=direction  # Pass integer instead of string
                ),
                weight
            ))
        elif reward_type['name'] == 'liedown':
            rewards.append((
                humenv_rewards.LieDownReward(
                    direction=reward_type.get('direction', 'up')
                ),
                weight
            ))
        elif reward_type['name'] == 'sit':
            rewards.append((
                humenv_rewards.SitOnGroundReward(
                    pelvis_height_th=reward_type.get('pelvis_height_th', 0),
                    constrained_knees=reward_type.get('constrained_knees', False)
                ),
                weight
            ))
        elif reward_type['name'] == 'split':
            rewards.append((
                humenv_rewards.SplitReward(
                    distance=reward_type.get('distance', 1.5)
                ),
                weight
            ))
        elif reward_type['name'].startswith('move-ego'):
            rewards.append((
                humenv_rewards.LocomotionReward(
                    move_speed=reward_type.get('move_speed', 2.0),
                    stand_height=reward_type.get('stand_height', 1.4)
                ),
                weight
            ))
        elif reward_type['name'] == 'raisearms':
            # Convert to predefined task format
            left = reward_type.get('left', 'l')
            right = reward_type.get('right', 'l')
            task_name = f"raisearms-{left}-{right}"
            rewards.append((
                make_from_name(task_name),  # Use imported make_from_name
                weight
            ))
        else:
            raise ValueError(f"Unknown reward type: {reward_type['name']}")
    
    def combined_reward_fn(*args, **kwargs):
        total_reward = 0
        for reward_fn, weight in rewards:
            total_reward += weight * reward_fn(*args, **kwargs)
        return total_reward
    
    # Compute rewards using combined function
    computed_rewards = relabel(
        env,
        qpos=batch['next_qpos'],
        qvel=batch['next_qvel'],
        action=batch['action'],
        reward_fn=combined_reward_fn,
        max_workers=8
    )
    
    # Get context vector from rewards
    z = model.reward_wr_inference(
        next_obs=torch.tensor(batch['next_observation'], device=model.cfg.device, dtype=torch.float32),
        reward=torch.tensor(computed_rewards, device=model.cfg.device, dtype=torch.float32)
    )
    
    return z

def precompute_reward_contexts(model, env, buffer_data, reward_configs):
    """Precompute all reward contexts at startup"""
    contexts = []
    print("\nPrecomputing reward contexts:")
    
    for i, config in enumerate(reward_configs, 1):
        print(f"\nComputing context {i}/{len(reward_configs)}:")
        for j, reward in enumerate(config['rewards']):
            weight = config.get('weights', [1.0])[j]
            print(f"- {reward['name']} (weight: {weight})")
        z = get_reward_context(model, env, buffer_data, config)
        contexts.append(z)
    
    print("\nAll contexts computed!")
    return contexts

def run_simulation(model, env, reward_configs, contexts):
    """Run simulation with keyboard control for switching rewards"""
    observation, _ = env.reset()
    step_count = 0
    episode_count = 0
    current_config_idx = 0
    
    # Initialize z with the first context
    z = contexts[0]
    
    # Physics parameters
    gravity_normal = True
    wind_active = False
    viscosity_active = False
    unwrapped_env = env.unwrapped
    
    # Default values
    default_gravity = unwrapped_env.model.opt.gravity[2]
    low_gravity = default_gravity / 2
    default_wind = np.array([0., 0., 0.])
    strong_wind = np.array([20., 0., 0.])
    default_viscosity = 0.0
    high_viscosity = 1.0
    
    print("\nControls:")
    print("- Press SPACE to switch to next reward")
    print("- Press G to toggle gravity (normal/low)")
    print("- Press W to toggle wind (off/on)")
    print("- Press V to toggle viscosity (off/on)")
    
    status_lines = [
        f"Config {current_config_idx + 1}/{len(reward_configs)}: " + " + ".join(
            f"{r['name']}({w})" 
            for r, w in zip(
                reward_configs[current_config_idx]['rewards'],
                reward_configs[current_config_idx].get('weights', [1.0]*len(reward_configs[current_config_idx]['rewards']))
            )
        ),
        f"Gravity: {'Normal' if gravity_normal else 'Low'} ({unwrapped_env.model.opt.gravity[2]:.2f})",
        f"Wind: {'On' if wind_active else 'Off'} ({unwrapped_env.model.opt.wind[0]:.1f}, {unwrapped_env.model.opt.wind[1]:.1f}, {unwrapped_env.model.opt.wind[2]:.1f})",
        f"Viscosity: {'On' if viscosity_active else 'Off'} ({unwrapped_env.model.opt.viscosity:.3f})"
    ]
    
    try:
        while True:
            step_count += 1
            
            action = model.act(observation, z, mean=True)
            observation, _, terminated, truncated, _ = env.step(
                action.cpu().numpy().ravel()
            )
            
            frame = env.render()
            
            # Add status text to frame
            for i, text in enumerate(status_lines):
                cv2.putText(
                    frame,
                    text,
                    (10, 30 + i*30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2
                )
            
            cv2.imshow("Humanoid Simulation", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == 32:  # SPACE
                current_config_idx = (current_config_idx + 1) % len(reward_configs)
                print(f"\nSwitching to reward combination {current_config_idx + 1}/{len(reward_configs)}:")
                for i, reward in enumerate(reward_configs[current_config_idx]['rewards']):
                    weight = reward_configs[current_config_idx].get('weights', [1.0])[i]
                    print(f"- {reward['name']} (weight: {weight})")
                z = contexts[current_config_idx]
            elif key == ord('w'):  # W key
                wind_active = not wind_active
                unwrapped_env.model.opt.wind[:] = strong_wind if wind_active else default_wind
                print(f"Wind set to: {'On' if wind_active else 'Off'} ({unwrapped_env.model.opt.wind[0]:.1f}, {unwrapped_env.model.opt.wind[1]:.1f}, {unwrapped_env.model.opt.wind[2]:.1f})")
            elif key == ord('g'):  # G key
                gravity_normal = not gravity_normal
                unwrapped_env.model.opt.gravity[2] = default_gravity if gravity_normal else low_gravity
                print(f"Gravity set to: {'Normal' if gravity_normal else 'Low'} ({unwrapped_env.model.opt.gravity[2]:.2f})")
            elif key == ord('v'):  # V key
                viscosity_active = not viscosity_active
                unwrapped_env.model.opt.viscosity = high_viscosity if viscosity_active else default_viscosity
                print(f"Viscosity set to: {'On' if viscosity_active else 'Off'} ({unwrapped_env.model.opt.viscosity:.3f})")
            
            # Update status lines
            status_lines = [
                f"Config {current_config_idx + 1}/{len(reward_configs)}: " + " + ".join(
                    f"{r['name']}({w})" 
                    for r, w in zip(
                        reward_configs[current_config_idx]['rewards'],
                        reward_configs[current_config_idx].get('weights', [1.0]*len(reward_configs[current_config_idx]['rewards']))
                    )
                ),
                f"Gravity: {'Normal' if gravity_normal else 'Low'} ({unwrapped_env.model.opt.gravity[2]:.2f})",
                f"Wind: {'On' if wind_active else 'Off'} ({unwrapped_env.model.opt.wind[0]:.1f}, {unwrapped_env.model.opt.wind[1]:.1f}, {unwrapped_env.model.opt.wind[2]:.1f})",
                f"Viscosity: {'On' if viscosity_active else 'Off'} ({unwrapped_env.model.opt.viscosity:.3f})"
            ]
            
            time.sleep(1/30)  # Cap at 30 FPS
            
            if terminated:
                episode_count += 1
                observation, _ = env.reset()
            
    except KeyboardInterrupt:
        print(f"\nSimulation stopped by user")
    
    cv2.destroyAllWindows()

def main():
    device = "cpu"
    print("Setting up simulation...")
    
    # Load model and environment
    model = FBcprModel.from_pretrained("facebook/metamotivo-S-1")
    model.to(device)
    env = setup_basic_env(device, max_steps=2000000)
    
    # Define reward configurations with all available rewards and their parameters
    reward_configs = [
        # Add this as the first configuration
        {'rewards': [{'name': 'zero'}]},  # ZeroReward - makes the humanoid stay still
        
        # === Basic Movement ===
        {'rewards': [{'name': 'move-ego', 'move_speed': 2.0, 'stand_height': 1.4}]},  # Walking
        {'rewards': [{'name': 'move-ego', 'move_speed': 4.0, 'stand_height': 1.4}]},  # Running
        {'rewards': [{'name': 'move-ego-low', 'move_speed': 2.0, 'stand_height': 0.8}]},  # Low walking
        
        # === Acrobatic Moves ===
        {'rewards': [{'name': 'jump', 'jump_height': 1.6, 'max_velocity': 5.0}]},  # Normal jump
        {'rewards': [{'name': 'jump', 'jump_height': 2.0, 'max_velocity': 6.0}]},  # High jump
        
        # === Rotations ===
        # Front/back rotations
        {'rewards': [{'name': 'rotation', 'axis': 'x', 'target_ang_velocity': 5.0, 'stand_pelvis_height': 0.8}]},
        {'rewards': [{'name': 'rotation', 'axis': 'x', 'target_ang_velocity': -5.0, 'stand_pelvis_height': 0.8}]},
        # Spins
        {'rewards': [{'name': 'rotation', 'axis': 'y', 'target_ang_velocity': 5.0, 'stand_pelvis_height': 0.8}]},
        {'rewards': [{'name': 'rotation', 'axis': 'y', 'target_ang_velocity': -5.0, 'stand_pelvis_height': 0.8}]},
        # Side flips
        {'rewards': [{'name': 'rotation', 'axis': 'z', 'target_ang_velocity': 5.0, 'stand_pelvis_height': 0.8}]},
        {'rewards': [{'name': 'rotation', 'axis': 'z', 'target_ang_velocity': -5.0, 'stand_pelvis_height': 0.8}]},
        
        # === Static Poses ===
        {'rewards': [{'name': 'headstand', 'stand_pelvis_height': 0.95}]},  # Headstand
        {'rewards': [{'name': 'liedown', 'direction': 'up'}]},              # Lie on back
        {'rewards': [{'name': 'liedown', 'direction': 'down'}]},            # Lie face down
        {'rewards': [{'name': 'sit', 'pelvis_height_th': 0.3, 'constrained_knees': True}]},  # Sit with bent knees
        {'rewards': [{'name': 'split', 'distance': 0.5}]},                  # Small splits
        {'rewards': [{'name': 'split', 'distance': 1.0}]},                  # Full splits
        
        # === Movement Styles ===
        # Crawling variations
        {'rewards': [{'name': 'crawl', 'spine_height': 0.4, 'move_speed': 0, 'direction': 'u'}]},  # Crawl up static
        {'rewards': [{'name': 'crawl', 'spine_height': 0.4, 'move_speed': 2, 'direction': 'u'}]},  # Crawl up moving
        {'rewards': [{'name': 'crawl', 'spine_height': 0.4, 'move_speed': 0, 'direction': 'd'}]},  # Crawl down static
        {'rewards': [{'name': 'crawl', 'spine_height': 0.4, 'move_speed': 2, 'direction': 'd'}]},  # Crawl down moving
        
        # === Directional Movement ===
        # Different directions of movement (using predefined tasks)
        {'rewards': [{'name': 'move-ego-0-2'}]},     # Forward at speed 2
        {'rewards': [{'name': 'move-ego-90-2'}]},    # Right at speed 2
        {'rewards': [{'name': 'move-ego--90-2'}]},   # Left at speed 2
        {'rewards': [{'name': 'move-ego-180-2'}]},   # Backward at speed 2
        
        # === Arm Movements ===
        # Raise arms combinations (l=low, m=medium, h=high)
        {'rewards': [{'name': 'raisearms', 'left': 'l', 'right': 'l'}]},  # Both arms low
        {'rewards': [{'name': 'raisearms', 'left': 'm', 'right': 'm'}]},  # Both arms medium
        {'rewards': [{'name': 'raisearms', 'left': 'h', 'right': 'h'}]},  # Both arms high
        {'rewards': [{'name': 'raisearms', 'left': 'l', 'right': 'h'}]},  # Left low, right high
        {'rewards': [{'name': 'raisearms', 'left': 'h', 'right': 'l'}]},  # Left high, right low
        
        # === Complex Combinations ===
        # Parkour
        {
            'rewards': [
                {'name': 'move-ego', 'move_speed': 3.0, 'stand_height': 1.4},
                {'name': 'jump', 'jump_height': 1.8, 'max_velocity': 5.0},
                {'name': 'rotation', 'axis': 'z', 'target_ang_velocity': 2.0, 'stand_pelvis_height': 0.8}
            ],
            'weights': [0.4, 0.4, 0.2]
        },
        
        # Breakdance
        {
            'rewards': [
                {'name': 'headstand', 'stand_pelvis_height': 0.95},
                {'name': 'rotation', 'axis': 'y', 'target_ang_velocity': 3.0, 'stand_pelvis_height': 0.8}
            ],
            'weights': [0.6, 0.4]
        },
        
        # Moving with raised arms
        {
            'rewards': [
                {'name': 'move-ego', 'move_speed': 2.0, 'angle': 0, 'stand_height': 1.4},
                {'name': 'raisearms', 'left': 'h', 'right': 'h'}
            ],
            'weights': [0.7, 0.3]
        },
        
        # Acrobatic sequence
        {
            'rewards': [
                {'name': 'jump', 'jump_height': 1.6, 'max_velocity': 5.0},
                {'name': 'rotation', 'axis': 'x', 'target_ang_velocity': 3.0, 'stand_pelvis_height': 0.8},
                {'name': 'split', 'distance': 1.5}
            ],
            'weights': [0.4, 0.4, 0.2]
        },
        
        # Combined arm movements with locomotion
        {
            'rewards': [
                {'name': 'move-ego', 'move_speed': 2.0, 'stand_height': 1.4},
                {'name': 'raisearms', 'left': 'h', 'right': 'l'}
            ],
            'weights': [0.6, 0.4]
        },
        
        # Constrained sitting variations
        {'rewards': [{'name': 'sit', 'pelvis_height_th': 0.3, 'constrained_knees': False}]},  # Regular sit
        {'rewards': [{'name': 'sit', 'pelvis_height_th': 0.3, 'knees_not_on_ground': True}]},  # Hover sit
        
        # Complex movement patterns
        {
            'rewards': [
                {'name': 'move-ego', 'move_speed': 2.0, 'stand_height': 0.8},  # Low movement
                {'name': 'rotation', 'axis': 'y', 'target_ang_velocity': 2.0},  # Slow spin
                {'name': 'raisearms', 'left': 'm', 'right': 'm'}  # Medium arm raise
            ],
            'weights': [0.4, 0.3, 0.3]
        },
        
        # Crawl variations with arm positions
        {
            'rewards': [
                {'name': 'crawl', 'spine_height': 0.3, 'move_speed': 1.0, 'direction': 'u'},
                {'name': 'raisearms', 'left': 'l', 'right': 'l'}
            ],
            'weights': [0.7, 0.3]
        }
    ]
    
    # Download buffer data and precompute contexts
    global buffer_data
    buffer_data = download_buffer()
    
    print("\nPrecomputing reward contexts...")
    contexts = precompute_reward_contexts(model, env, buffer_data, reward_configs)
    
    print("\nStarting reward exploration...")
    print("Use SPACE to switch between rewards, ESC to quit")
    run_simulation(model, env, reward_configs, contexts)

if __name__ == "__main__":
    main()