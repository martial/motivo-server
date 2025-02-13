import { websocketService } from "./websocketService";

  
export function wsSendPose(frameNb, pose, normalize = false, randomRoot = false, countOffset = true, useQuat = false, eulerOrder = 'XYZ', modelType = 'smpl') {
    console.log('Sending pose for frame', frameNb, pose);
    const poseToSend = pose.person_1.poses[frameNb];
    const transToSend = pose.person_1.trans[frameNb];

    websocketService.connect();
    console.log('Sending pose for frame', frameNb, poseToSend);
    websocketService.send({
        type: 'load_pose_smpl',
        pose: poseToSend,
        trans: transToSend,
        inference_type: 'goal',
        // Add SMPL parameters
        normalize,
        random_root: randomRoot,
        count_offset: countOffset,
        use_quat: useQuat,
        euler_order: eulerOrder,
        model: modelType
    });
    websocketService.disconnect();
}