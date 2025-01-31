import torch
import cv2
import time
import numpy as np
from humenv import make_humenv
from gymnasium.wrappers import FlattenObservation, TransformObservation, TimeLimit
from metamotivo.fb_cpr.huggingface import FBcprModel
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import PIL.Image

def setup_basic_env(device, max_steps=1000):
    """Setup basic environment with humanoid"""
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
    
    # Set up physics parameters
    unwrapped_env = env.unwrapped
    unwrapped_env.model.opt.density = 1.2
    unwrapped_env.model.opt.wind = np.array([0., 0., 0.])
    unwrapped_env.model.opt.viscosity = 0.0
    unwrapped_env.model.opt.integrator = 0
    unwrapped_env.model.opt.timestep = 0.002
    
    return TimeLimit(env, max_episode_steps=max_steps)

def get_goal_context(model, env, goal_qpos, inference_type="goal"):
    """Get context vector for a goal pose
    Args:
        model: The FB-CPR model
        env: The environment
        goal_qpos: The goal pose array
        inference_type: Type of inference to use ("goal", "tracking", or "context")
    """
    env.unwrapped.set_physics(qpos=goal_qpos, qvel=np.zeros(75))
    goal_obs = torch.tensor(
        env.unwrapped.get_obs()["proprio"].reshape(1, -1), 
        device=model.cfg.device, 
        dtype=torch.float32
    )
    
    print(f"Using {inference_type} inference...")
    
    if inference_type == "goal":
        z = model.goal_inference(next_obs=goal_obs)
    elif inference_type == "tracking":
        z = model.tracking_inference(next_obs=goal_obs)
    else:  # context
        z = model.context_inference(goal_obs)
    
    return z

def run_simulation(model, env, context, context_type, context_description):
    """Run simulation with keyboard control for switching behaviors"""
    observation, _ = env.reset()
    
    # Initialize physics parameters
    unwrapped_env = env.unwrapped
    gravity_normal = True
    wind_active = False
    viscosity_active = False
    
    # Default values
    default_gravity = unwrapped_env.model.opt.gravity[2]
    low_gravity = default_gravity / 2
    default_wind = np.array([0., 0., 0.])
    strong_wind = np.array([20., 0., 0.])
    default_viscosity = 0.0
    high_viscosity = 1.0
    
    print("\nControls:")
    print("- G: Toggle gravity (normal/low)")
    print("- W: Toggle wind (off/on)")
    print("- V: Toggle viscosity (off/on)")
    print("- ESC: Quit")
    
    status_lines = [
        f"Behavior: {context_description} ({context_type})",
        f"Gravity: {'Normal' if gravity_normal else 'Low'} ({unwrapped_env.model.opt.gravity[2]:.2f})",
        f"Wind: {'On' if wind_active else 'Off'} ({unwrapped_env.model.opt.wind[0]:.1f}, {unwrapped_env.model.opt.wind[1]:.1f}, {unwrapped_env.model.opt.wind[2]:.1f})",
        f"Viscosity: {'On' if viscosity_active else 'Off'} ({unwrapped_env.model.opt.viscosity:.3f})"
    ]
    
    try:
        while True:
            action = model.act(observation, context, mean=True)
            observation, _, terminated, truncated, _ = env.step(action.cpu().numpy().ravel())
            
            frame = env.render()
            
            # Add status text
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
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('g'):
                gravity_normal = not gravity_normal
                unwrapped_env.model.opt.gravity[2] = default_gravity if gravity_normal else low_gravity
            elif key == ord('w'):
                wind_active = not wind_active
                unwrapped_env.model.opt.wind[:] = strong_wind if wind_active else default_wind
            elif key == ord('v'):
                viscosity_active = not viscosity_active
                unwrapped_env.model.opt.viscosity = high_viscosity if viscosity_active else default_viscosity
            
            status_lines[1] = f"Gravity: {'Normal' if gravity_normal else 'Low'} ({unwrapped_env.model.opt.gravity[2]:.2f})"
            status_lines[2] = f"Wind: {'On' if wind_active else 'Off'} ({unwrapped_env.model.opt.wind[0]:.1f}, {unwrapped_env.model.opt.wind[1]:.1f}, {unwrapped_env.model.opt.wind[2]:.1f})"
            status_lines[3] = f"Viscosity: {'On' if viscosity_active else 'Off'} ({unwrapped_env.model.opt.viscosity:.3f})"
            
            time.sleep(1/30)  # Cap at 30 FPS
            
            if terminated:
                observation, _ = env.reset()
            
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
    
    cv2.destroyAllWindows()

def generate_behavior_video(model, env, context, num_frames=30):
    """Generate a video sequence of the behavior"""
    observation, _ = env.reset()
    frames = [env.render()]
    
    for _ in range(num_frames):
        action = model.act(observation, context, mean=True)
        observation, _, terminated, _, _ = env.step(action.cpu().numpy().ravel())
        frames.append(env.render())
    
    return frames

def main():
    device = "cpu"
    print("Setting up simulation...")
    
    # Load model and environment
    model = FBcprModel.from_pretrained("facebook/metamotivo-M-1")
    model.to(device)
    env = setup_basic_env(device, max_steps=2000000)

    # Example sitting pose from the tutorial
    '''
    goal_qpos = np.array([
        0.13769039, -0.20029453, 0.42305034, 0.21707786, 0.94573617, 0.23868944,
        0.03856998, -1.05566834, -0.12680767, 0.11718296, 1.89464102, -0.01371153,
        -0.07981451, -0.70497424, -0.0478, -0.05700732, -0.05363342, -0.0657329,
        0.08163511, -1.06263979, 0.09788937, -0.22008936, 1.85898192, 0.08773695,
        0.06200327, -0.3802791, 0.07829525, 0.06707749, 0.14137152, 0.08834448,
        -0.07649805, 0.78328658, 0.12580912, -0.01076061, -0.35937259, -0.13176489,
        0.07497022, -0.2331914, -0.11682692, 0.04782308, -0.13571422, 0.22827948,
        -0.23456622, -0.12406075, -0.04466465, 0.2311667, -0.12232673, -0.25614032,
        -0.36237662, 0.11197906, -0.08259534, -0.634934, -0.30822742, -0.93798716,
        0.08848668, 0.4083417, -0.30910404, 0.40950143, 0.30815359, 0.03266103,
        1.03959336, -0.19865537, 0.25149713, 0.3277561, 0.16943092, 0.69125975,
        0.21721349, -0.30871948, 0.88890484, -0.08884043, 0.38474549, 0.30884107,
        -0.40933304, 0.30889523, -0.29562966, -0.6271498])
'''
    goal_qpos = np.array([
    0.13026437933891663,
    -0.18346932047695372,
    0.12638228083735759,
    0.9635148790915333,
    0.034200764213223794,
    -0.09407954650447622,
    0.24823058720869107,
    0.04184957044506255,
    0.35084143850984434,
    -0.020396473827607356,
    -0.0988930070165491,
    0.12790798857433,
    -0.1277076151640087,
    0.04393134654219811,
    0.3161116611545828,
    -0.072718380850745,
    0.3875210141927983,
    -0.07756565242606621,
    -0.07782092602401774,
    -0.012389391827338354,
    -0.08227712022909782,
    -0.09052770439206131,
    -0.09826033900231003,
    -0.10978979065343508,
    0.12591085115940737,
    0.18723553459670633,
    -0.011218827017832772,
    0.08020166492971569,
    0.3892144805398383,
    -0.02055955818635069,
    -0.07775539061375314,
    -0.08834328313412945,
    0.334609924202214,
    0.10274780630014388,
    0.24324331740141503,
    -0.05473749849945916,
    0.02125786770543542,
    -0.2788948681890073,
    -0.06476231132941536,
    0.01753200216511123,
    -0.06160582954693823,
    0.1468881040474296,
    0.2949718040452111,
    -0.013739387172207075,
    -0.20064232861255415,
    0.20534636231171396,
    -0.05478444716440679,
    0.10812408221961342,
    0.23459882911669,
    0.29861514508085896,
    -0.8665586772437744,
    -1.01024796449455,
    0.015481053300432611,
    0.1839707772346289,
    -0.3683586500879705,
    0.40611712192840776,
    -0.24736194576884354,
    0.4083900307615621,
    -0.11697815557067164,
    -0.29128385622150793,
    -0.5090411538732923,
    -0.0753939190599887,
    -0.1667678067553776,
    0.2220163571535029,
    0.21715249310533102,
    0.37146572223915486,
    1.174496666907726,
    0.06433353676479678,
    -0.11865156445176728,
    0.03908847326575892,
    0.33603967725546086,
    0.26112347422048643,
    -0.32689428744629107,
    0.18490786357929878,
    -0.04744780849920496,
    0.36078320500716066
    ])

    goal_qpos = np.array([
    2.9197465717793047,
    -0.18727150487975872,
    0.9188429625313872,
    0.31423749653577576,
    0.2648353509203145,
    0.6334280832838625,
    0.655656843158961,
    0.29345900292218813,
    0.07594900612807831,
    0.06375908693955351,
    -0.09682830859775872,
    -0.0880091027216463,
    0.031414602826372255,
    -0.14991954274909655,
    0.2932827773076416,
    0.021778317763953343,
    0.12070087424985318,
    0.04042091696199338,
    -0.06845061917564972,
    0.13874622957465976,
    0.0036874581048330613,
    -0.09435782830813076,
    -0.0978027942773376,
    0.07554267131238945,
    -0.08681422276933966,
    0.01048775011071567,
    -0.027612555225088035,
    0.08837503490956437,
    0.0665309605959763,
    0.044102482333993234,
    0.08838334208841431,
    -0.021850427829316187,
    -0.10169856228218985,
    0.12793081222201472,
    -0.04467136652336878,
    -0.12423060050647401,
    0.11122901433607986,
    0.10919975479926143,
    0.02738505125956441,
    0.27678565051959125,
    0.06751031616353187,
    0.28107526859982856,
    -0.2090005717052572,
    0.20414993711883356,
    -0.22388932000080206,
    -0.16227656200389423,
    -0.059392580048046865,
    -0.23270465794211237,
    -0.23953594940071427,
    -0.7366861080232932,
    -0.5191311779507037,
    0.99205365848061,
    -0.21139049797563597,
    -0.20049312308901818,
    0.08482045104778539,
    0.3395230096181926,
    -0.24375614452195343,
    0.35243645950012925,
    -0.00664472449928548,
    -0.0016269524134062915,
    0.24068209919542172,
    -0.031142242770073422,
    -0.21089028399993587,
    0.4221630695648816,
    0.42852283222978943,
    0.3939659803445424,
    0.29270111241414676,
    0.07540790374766886,
    -0.14335141262622897,
    -0.06447054940671453,
    0.21504136176247918,
    -0.14563926797971863,
    0.32077408014588576,
    -0.05454804044144273,
    -0.24890976012515315,
    0.12032389774312874
    ])
 
    
    print("\nChoose inference type:")
    print("1. Goal inference")
    print("2. Tracking inference")
    print("3. Context inference")
    
    inference_choice = input("Enter choice (1, 2, or 3): ")
    
    inference_type = {
        "1": "goal",
        "2": "tracking",
        "3": "context"
    }.get(inference_choice, "goal")
    
    print("\nComputing context vector...")
    z = get_goal_context(model, env, goal_qpos, inference_type)
    
    # Ask user for visualization mode
    print("\nChoose visualization mode:")
    print("1. Interactive simulation")
    print("2. Generate video sequence")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "2":
        print("\nGenerating video sequence...")
        frames = generate_behavior_video(model, env, z)
        try:
            from IPython import display
            import PIL.Image
            
            # Convert frames to PIL images
            pil_frames = [PIL.Image.fromarray(frame) for frame in frames]
            
            # Display as animation
            display.display(display.HTML(display.HTML(animation.FuncAnimation(
                plt.figure(), 
                lambda i: plt.imshow(pil_frames[i]),
                frames=len(frames),
                interval=1000/30  # 30 FPS
            ).to_jshtml())))
        except ImportError:
            print("Warning: IPython display not available. Video generation requires Jupyter environment.")
    else:
        print("\nStarting behavior exploration...")
        run_simulation(model, env, z, "Goal", "Sitting Pose")

if __name__ == "__main__":
    main()