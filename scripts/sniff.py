import asyncio
import websockets
import logging
import json
import numpy as np
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

async def send_fake_smpl_pose(websocket):
    # Create a realistic SMPL pose based on sample data
    fake_pose = [
        0.017441272078737146, 0.45619148679542426, -0.07552543405604054,
        -0.22330807380650328, -0.17182861078555783, 0.05428369699770573,
        -0.00457316366932735, -0.3735833617857662, 0.06002956237969323,
        0.8601181619200136, -0.0917155214223193, 0.23290778760760045,
        0.19956260249681804, -0.0769628940936461, -0.10740945192236724,
        -0.009381148785909727, -0.1150299996396832, 0.08485111644562089,
        0.11227570214536008, 0.031172725976768324, -0.03128664947749358,
        0.6191039383332614, 0.32965596663729096, 0.07150543817550722,
        0.20644543619144207, -0.3400360352318141, 0.030041181777997618,
        0.02547235905406732, -0.007446797651292281, -0.03681356003490967,
        0.39218773751295277, -0.0613268961623882, -0.09185592162476884,
        0.3906575825208223, -0.06193444910623656, -0.09128919710439902,
        0.05443566679246781, -0.1812555897903745, 0.006073958076222322,
        0.018828470945021315, 0.22220400988740838, -0.39684609815215244,
        -0.10193169121241222, -0.1418140059491835, 0.29433394983588795,
        0.33088827958671546, 0.16180533355386373, 0.25461576447704043,
        0.5971931577184358, -0.4433038171215747, -0.5066867677088595,
        0.8205170492437239, -0.9748714557359849, 0.7241528882064233,
        0.035258675535545084, -1.204249797402286, 0.0063320669982186864,
        -0.3271152847373648, 0.6677311870003668, -0.1907906957687962,
        0.2942797197352062, -0.2915051957816511, 0.2827035978143476,
        0.3079917047928932, 0.161590964566566, -0.38883131647218216,
        -0.1559902290179879, 0.343271708237279, 0.08318362362289357,
        -0.19242860797528188, -0.5176177384159464, 0.08710288561368576
    ]

    # Basic translation (x, y, z)
    fake_trans = [0.0, 0.0, 0.91437225]  # Default translation
    
    # Simplified message structure to match main.py changes
    message = {
        "type": "load_pose_smpl",
        "pose": fake_pose,
        "trans": fake_trans,
        "model": "smpl",
        "inference_type": "goal",
        "timestamp": datetime.now().isoformat()
    }
    
    print("\nSending fake SMPL pose...")
    await websocket.send(json.dumps(message))
    
    # Wait for response
    response = await websocket.recv()
    print(f"Received response: {response}")

async def listen_smpl():
    uri = "ws://localhost:8765"
    #uri = "ws://51.159.163.145:8765"
    async with websockets.connect(uri) as websocket:
        print("Connected!")
        
        # Send fake pose first
        await send_fake_smpl_pose(websocket)
        
        # Then continue listening
        while False:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                if "pose" in data and "trans" in data:
                    print(f"\nTimestamp: {data.get('timestamp', 'N/A')}")
                    print(f"Pose: {data['pose'][:5]}...")  # Show first 5 values
                    print(f"Trans: {data['trans']}")
                    print(f"Positions: {data['positions'][:2]}...")  # Show first 2 positions
                    print(f"Position Names: {data['position_names'][:5]}...")  # Show first 5 names
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(listen_smpl())