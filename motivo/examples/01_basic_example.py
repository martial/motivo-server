import torch
import cv2
import time
from humenv import make_humenv
from gymnasium.wrappers import FlattenObservation, TransformObservation, TimeLimit
from metamotivo.fb_cpr.huggingface import FBcprModel

def setup_basic_env(device="cpu", max_steps=2000):
    # Create basic environment first
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
    
    # Print environment info before wrapping
    print("Environment info before TimeLimit:", info)
    print("Current max episode steps:", getattr(env, "_max_episode_steps", "Not set"))
    
    # Then wrap it with TimeLimit explicitly
    env = TimeLimit(env, max_episode_steps=max_steps)
    print("TimeLimit wrapper max steps:", env._max_episode_steps)
    return env

def run_basic_simulation(model, env, chunk_size=20):
    """
    Run continuous simulation in chunks while maintaining state
    """
    # Get initial context vector
    z = model.sample_z(1)
    
    # Reset environment
    observation, _ = env.reset()
    
    # Add counters for logging
    step_count = 0
    episode_count = 0
    
    try:
        while True:  # Run indefinitely until interrupted
            # Run simulation loop for chunk_size steps
            for _ in range(chunk_size):
                step_count += 1
                
                # Get action from model (using defaults)
                action = model.act(observation, z, mean=True)
                
                # Take step in environment
                observation, _, terminated, truncated, _ = env.step(
                    action.cpu().numpy().ravel()
                )
                
                # Display current frame
                frame = env.render()
                cv2.imshow('Humanoid Simulation', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                cv2.waitKey(1)
                time.sleep(1/30)  # Cap at 30 FPS
                
                # Only reset if truly terminated (ignore truncations)
                if terminated:  # removed truncated condition
                    episode_count += 1
                    print(f"\nReset occurred at step {step_count}")
                    print(f"Episode {episode_count} ended due to environment termination")
                    observation, _ = env.reset()
            
            print(f"Completed chunk {step_count//chunk_size}, continuing... (Total steps: {step_count})")
            
    except KeyboardInterrupt:
        print(f"\nSimulation stopped by user after {step_count} steps and {episode_count} episodes")
        cv2.destroyAllWindows()

def main():
    # Setup on CPU for simplicity
    device = "cpu"
    print("Setting up simulation...")
    
    # Load model with defaults
    model = FBcprModel.from_pretrained("facebook/metamotivo-S-1")
    model.to(device)
    
    # Setup environment with longer time limit
    max_steps = 2000000
    env = setup_basic_env(device, max_steps=max_steps)
    
    print("Running simulation...")
    print(f"Final max episode steps: {env._max_episode_steps}")
    run_basic_simulation(model, env)
    
    print("Simulation complete!")
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()