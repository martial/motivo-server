<script>
    import { websocketService } from "../services/websocketService";
    import { onMount, onDestroy } from "svelte";
    const apiUrl = import.meta.env.VITE_API_URL;
  
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
  
    // Modal controls
    let showSaveModal = false;
    let poseTitle = "";
    export let videoFilename = ""; // This should be passed as a prop or extracted from videoBase64
  
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
  
    async function handleSavePose() {
      try {
        const response = await fetch(`${apiUrl}/api/vibeconf`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            title: poseTitle,
            thumbnail: videoBase64, // You might want to generate a thumbnail instead
            video: videoFilename,
            frame: frame,
            pose: {
              person_1: {
                poses: [pose.person_1.poses[frame]],
                trans: [pose.person_1.trans[frame]],
                orig_cam: [pose.person_1.orig_cam[frame]]
              }
            }
          })
        });
  
        if (response.ok) {
          showSaveModal = false;
          poseTitle = "";
          // Optionally trigger a refresh of saved poses
        }
      } catch (error) {
        console.error('Error saving pose:', error);
      }
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
  
            <!-- Save and Send Pose Buttons -->
            <div class="space-y-4">
                <button 
                    class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors w-full"
                    on:click={() => showSaveModal = true}
                >
                    Save Pose
                </button>
  
                <button 
                    class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors w-full"
                    on:click={() => sendPose(frame)}
                >
                    Send Pose
                </button>
            </div>
        </div>
    </div>
  
    <!-- Save Modal -->
    {#if showSaveModal}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white p-6 rounded-lg w-96">
            <h2 class="text-xl font-bold mb-4">Save Vibe Pose</h2>
            <p class="text-gray-600 mb-4">Video: {videoFilename || 'Unknown'}</p>
            
            <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Pose Title
                </label>
                <input 
                    type="text"
                    bind:value={poseTitle}
                    class="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="Enter pose title"
                />
            </div>
  
            <div class="flex justify-end gap-4">
                <button 
                    class="px-4 py-2 text-gray-600 hover:text-gray-800"
                    on:click={() => showSaveModal = false}
                >
                    Cancel
                </button>
                <button 
                    class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    on:click={handleSavePose}
                >
                    Save
                </button>
            </div>
        </div>
    </div>
    {/if}
  
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