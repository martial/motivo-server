import json
import asyncio
import websockets
from typing import Dict, Any
import traceback
import os

# import from env BACKEND_DOMAIN
BACKEND_DOMAIN = os.getenv("VITE_BACKEND_DOMAIN", "localhost")
WS_PORT = os.getenv("VITE_WS_PORT", 8765)
API_PORT = os.getenv("VITE_API_PORT", 5000)

async def test_individual_reward(websocket, reward_config: Dict[Any, Any], name: str, settings: Dict[Any, Any] = None):
    """Test a single reward configuration"""
    try:
        print(f"\n=== Testing {name} ===")
        
        # Request model info
        debug_message = {
            "type": "debug_model_info",
            "timestamp": "test"
        }
        await websocket.send(json.dumps(debug_message))
        debug_response = await websocket.recv()
        print("\nModel Body Names:", end=" ")
        try:
            response_data = json.loads(debug_response)
            if isinstance(response_data, list):
                print(", ".join(response_data))
            else:
                print(f"Error: {debug_response}")
        except json.JSONDecodeError:
            print(f"Invalid JSON: {debug_response}")
        
        # Print reward info in a single line for each reward
        for reward in reward_config["rewards"]:
            reward_type = reward["name"]
            if "target_height" in reward:
                print(f"Reward: {reward_type} - Target Height: {reward['target_height']}m")
            elif "target_distance" in reward:
                print(f"Reward: {reward_type} - Target Distance: {reward['target_distance']}m")
            else:
                print(f"Reward: {reward_type}")

        print(f"Config: {reward_config['combination_type']} combination, Weights: {reward_config['weights']}")
        
        message = {
            "type": "request_reward",
            "reward": reward_config,
            "timestamp": "test"
        }
        
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        print(f"Response: {response}")
        
        await asyncio.sleep(10)
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        raise

async def run_reward_tests():
    """Run a series of reward tests"""
    try:
        uri = f"ws://{BACKEND_DOMAIN}:{WS_PORT}"
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")

            # Test StayUprightReward
         
            await test_individual_reward(
                websocket,
                {
                    "rewards": [{"name": "stay-upright"}],
                    "weights": [1.0],
                    "combination_type": "multiplicative"
                },
                "StayUprightReward Test"
            )

           
            # Test height rewards for different body parts
            height_tests = [
                #("head-height", 0.25, 0.8, 1.5),
                #("pelvis-height", 0.7, 0.8, 0.9),
                ("left-hand-height", 0.2, 1.0, 2.0),
                ("right-hand-height", 0.2, 1.0, 2.0),
                #("left-foot-height", 0.1, 0.5, 0.8),
                #("right-foot-height", 0.1, 0.5, 0.8)
            ]

            for reward_name, *heights in height_tests:
                for height in heights:
                    await test_individual_reward(
                        websocket,
                        {
                            "rewards": [
                                {"name": reward_name, "target_height": height}
                            ],
                            "weights": [1.0],
                            "combination_type": "multiplicative"
                        },
                        f"{reward_name} Test (height: {height}m)"
                    )

            # Test distance rewards for hands and feet
            distance_tests = [
                ("left-hand-lateral", 0.3, 0.5, 0.7),
                ("left-hand-forward", 0.3, 0.5, 0.7),
                ("right-hand-lateral", 0.3, 0.5, 0.7),
                ("right-hand-forward", 0.3, 0.5, 0.7),
                ("left-foot-lateral", 0.2, 0.3, 0.4),
                ("left-foot-forward", 0.2, 0.3, 0.4),
                ("right-foot-lateral", 0.2, 0.3, 0.4),
                ("right-foot-forward", 0.2, 0.3, 0.4)
            ]

            for reward_name, *distances in distance_tests:
                for distance in distances:
                    target_key = "target_distance"
                    await test_individual_reward(
                        websocket,
                        {
                            "rewards": [
                                {"name": reward_name, target_key: distance}
                            ],
                            "weights": [1.0],
                            "combination_type": "multiplicative"
                        },
                        f"{reward_name} Test (distance: {distance}m)"
                    )

            # Test combinations of multiple rewards
            combinations = [
                {
                    "rewards": [
                        {"name": "head-height", "target_height": .2},
                        {"name": "left-hand-height", "target_height"   : 0.1},
                        {"name": "pelvis-height", "target_height"   : 0.1},
                        {"name": "left-foot-height", "target_height"   : 0.8},
                    ],
                    "weights": [1.0, 1.0, 1.0],
                },
                {
                    "rewards": [
                        {"name": "head-height", "target_height": 1.4},
                        {"name": "left-foot-height", "target_height"   : 0.5},
                    ],
                    "weights": [1.0, 1.0, 1.0],
                },
                {
                    "rewards": [
                        {"name": "stay-upright"},
                        {"name": "right-hand-height", "target_height": 1.2},
                        {"name": "left-foot-forward", "target_distance": 0.3}
                    ],
                    "weights": [1.0, 1.2, 0.8],
                },
                {
                    "rewards": [
                        {"name": "pelvis-height", "target_height": 0.8},
                        {"name": "left-hand-forward", "target_distance": 0.4},
                        {"name": "right-foot-lateral", "target_distance": 0.3}
                    ],
                    "weights": [1.0, 0.8, 1.2],
                }
            ]
            
            for i, config in enumerate(combinations, 1):
                config["combination_type"] = "multiplicative"
                await test_individual_reward(
                    websocket,
                    config,
                    f"Combined Rewards Test (variant {i})"
                )

            # Clean up at the end
            print("\nCleaning up...")
            cleanup_message = {
                "type": "clean_rewards",
                "timestamp": "test"
            }
            await websocket.send(json.dumps(cleanup_message))
            cleanup_response = await websocket.recv()
            print(f"Cleanup response: {cleanup_response}")

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"\nWebSocket connection closed unexpectedly: {str(e)}")
        print("Make sure the main websocket server (04_ws_example.py) is running!")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    print("Starting reward tests...")
    print("Make sure the main websocket server (04_ws_example.py) is running first!")
    print("Press Ctrl+C to stop the tests at any time.")
    try:
        asyncio.run(run_reward_tests())
    except KeyboardInterrupt:
        print("\nTests stopped by user.")
    except Exception as e:
        print(f"\nError running tests: {str(e)}")
        print(traceback.format_exc()) 