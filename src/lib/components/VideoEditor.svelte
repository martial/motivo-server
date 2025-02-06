<script>
  import { websocketService } from "../services/websocketService";
  import { onMount, onDestroy } from "svelte";

  export let videoBase64 = null;
  export let frame = 0;
  export let pose = {};

  let videoElement;
  let currentTime = 0;
  const FPS = 30;

  // Add camera parameter controls
  let camX = 0;
  let camY = 0;
  let camZ = 0;
  let scale = 2;

  // Add SMPL pose parameters
  let normalize = false;
  let randomRoot = false;
  let countOffset = true;
  let useQuat = false;
  let eulerOrder = "ZYX";
  let modelType = "smpl";

  function msToFrame(timeInSeconds) {
      return Math.floor(timeInSeconds * FPS);
  }

  function handleTimeUpdate(e) {
      frame = msToFrame(e.target.currentTime);
  }

  function sendPose(frameNb, customCam = null) {
      const poseToSend = pose.person_1.poses[frameNb];
      const transToSend = pose.person_1.trans[frameNb];
      
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
  }

  $: if (pose?.person_1?.orig_cam?.[frame]) {
      const currentCam = pose.person_1.orig_cam[frame];
      camX = currentCam[0];
      camY = currentCam[1];
      camZ = currentCam[2];
      scale = currentCam[3];
  }

  onMount(() => {
      websocketService.connect();
  });
</script>

<section class="p-4">
  <h2 class="mb-4">Frame Controls</h2>
  <div class="flex gap-8">
      <!-- Video Section -->
      <div class="w-1/2">
          <video
              bind:this={videoElement}
              bind:currentTime
              src={videoBase64}
              controls
              muted
              loop
              controlsList="nodownload nofullscreen noremoteplayback noplaybackrate"
              class="w-full"
              on:timeupdate={handleTimeUpdate}
          />
          <div class="mt-2">Selected frame: {frame}</div>
      </div>

      <!-- Controls Section -->
      <div class="w-1/2 space-y-6">
          <div class="space-y-4">
              <div class="flex items-center gap-4">
                  <label class="w-20">Camera X:</label>
                  <input 
                      type="range" 
                      bind:value={camX} 
                      min="-5" 
                      max="5" 
                      step="0.1"
                      class="flex-grow"
                      on:input={() => sendPose(frame)}
                  />
                  <span class="w-16 text-right">{camX.toFixed(2)}</span>
              </div>

              <div class="flex items-center gap-4">
                  <label class="w-20">Camera Y:</label>
                  <input 
                      type="range" 
                      bind:value={camY} 
                      min="-5" 
                      max="5" 
                      step="0.1"
                      class="flex-grow"
                      on:input={() => sendPose(frame)}
                  />
                  <span class="w-16 text-right">{camY.toFixed(2)}</span>
              </div>

              <div class="flex items-center gap-4">
                  <label class="w-20">Camera Z:</label>
                  <input 
                      type="range" 
                      bind:value={camZ} 
                      min="-5" 
                      max="5" 
                      step="0.1"
                      class="flex-grow"
                      on:input={() => sendPose(frame)}
                  />
                  <span class="w-16 text-right">{camZ.toFixed(2)}</span>
              </div>

              <div class="flex items-center gap-4">
                  <label class="w-20">Scale:</label>
                  <input 
                      type="range" 
                      bind:value={scale} 
                      min="0.1" 
                      max="3" 
                      step="0.1"
                      class="flex-grow"
                      on:input={() => sendPose(frame)}
                  />
                  <span class="w-16 text-right">{scale.toFixed(2)}</span>
              </div>
          </div>

          <!-- SMPL Parameters -->
          <div class="space-y-4">
              <h3 class="font-semibold">SMPL Parameters</h3>
              
              <div class="flex items-center gap-4">
                  <label class="w-32">Normalize:</label>
                  <input 
                      type="checkbox"
                      bind:checked={normalize}
                      class="form-checkbox"
                      on:change={() => sendPose(frame)}
                  />
              </div>

              <div class="flex items-center gap-4">
                  <label class="w-32">Random Root:</label>
                  <input 
                      type="checkbox"
                      bind:checked={randomRoot}
                      class="form-checkbox"
                      on:change={() => sendPose(frame)}
                  />
              </div>

              <div class="flex items-center gap-4">
                  <label class="w-32">Count Offset:</label>
                  <input 
                      type="checkbox"
                      bind:checked={countOffset}
                      class="form-checkbox"
                      on:change={() => sendPose(frame)}
                  />
              </div>

              <div class="flex items-center gap-4">
                  <label class="w-32">Use Quaternion:</label>
                  <input 
                      type="checkbox"
                      bind:checked={useQuat}
                      class="form-checkbox"
                      on:change={() => sendPose(frame)}
                  />
              </div>

              <div class="flex items-center gap-4">
                  <label class="w-32">Euler Order:</label>
                  <select 
                      bind:value={eulerOrder}
                      class="form-select"
                      on:change={() => sendPose(frame)}
                  >
                      <option value="ZYX">ZYX</option>
                      <option value="XYZ">XYZ</option>
                      <option value="YZX">YZX</option>
                  </select>
              </div>

              <div class="flex items-center gap-4">
                  <label class="w-32">Model Type:</label>
                  <select 
                      bind:value={modelType}
                      class="form-select"
                      on:change={() => sendPose(frame)}
                  >
                      <option value="smpl">SMPL</option>
                      <option value="smplh">SMPL-H</option>
                  </select>
              </div>
          </div>

          <button 
              class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors w-full"
              on:click={() => sendPose(frame)}
          >
              Send Pose
          </button>
      </div>
  </div>
</section>

<style>
  video::-webkit-media-controls-panel {
      display: flex;
      justify-content: center;
  }

  video::-webkit-media-controls-play-button,
  video::-webkit-media-controls-current-time-display,
  video::-webkit-media-controls-time-remaining-display,
  video::-webkit-media-controls-mute-button,
  video::-webkit-media-controls-volume-slider,
  video::-webkit-media-controls-fullscreen-button 
  {
      display: none;
  }

  video::-webkit-media-controls-timeline {
      display: block;
      margin: 0;
  }

  .form-checkbox {
      width: 1rem;
      height: 1rem;
      border-radius: 0.25rem;
      border: 1px solid #d1d5db;
      color: #2563eb;
      background-color: #fff;
  }

  .form-select {
      display: block;
      width: 100%;
      padding: 0.375rem 0.75rem;
      font-size: 0.875rem;
      line-height: 1.5;
      color: #374151;
      background-color: #fff;
      border: 1px solid #d1d5db;
      border-radius: 0.375rem;
      box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  }

  .form-select:focus,
  .form-checkbox:focus {
      outline: 2px solid #3b82f6;
      outline-offset: 2px;
  }
</style>