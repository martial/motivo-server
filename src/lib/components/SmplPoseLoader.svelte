<script>
  import { websocketService } from "../services/websocketService";

  // Props
  export let pose = [];
  export let trans = [];

  // File handling state
  let fileInput;
  let fileName = "";
  let currentFrame = 0;
  let totalFrames = 0;
  let poseData = null;

  // SMPL Parameters with defaults
  let normalize = false;
  let randomRoot = false;
  let countOffset = true;
  let useQuat = false;
  let eulerOrder = "ZYX";
  let modelType = "smpl";
  let inferenceType = "goal";

  // Add rotation controls
  let targetRotation = {
    x: -90,
    y: 0,
    z: -90
  };

  async function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    fileName = file.name;
    try {
      const text = await file.text();
      poseData = JSON.parse(text);
      totalFrames = poseData.poses.length;
      currentFrame = 0;
      
      // Load first frame automatically
      loadFrame(0);
    } catch (error) {
      console.error("Error loading file:", error);
      alert("Error loading file. Please ensure it's a valid JSON file.");
    }
  }

  function loadFrame(frameIndex) {
    if (!poseData || frameIndex < 0 || frameIndex >= totalFrames) return;

    pose = poseData.poses[frameIndex];
    trans = poseData.trans[frameIndex];
    currentFrame = frameIndex;
    
    // Send pose immediately when frame is loaded
    sendPose();
  }

  function nextFrame() {
    if (currentFrame < totalFrames - 1) {
      loadFrame(currentFrame + 1);
    }
  }

  function previousFrame() {
    if (currentFrame > 0) {
      loadFrame(currentFrame - 1);
    }
  }

  function sendPose() {
    const socket = websocketService.getSocket();
    if (!socket || !pose.length) return;

    console.log("Sending pose with rotation:", targetRotation);
    console.log(pose);
    console.log(trans);

    socket.send(JSON.stringify({
      type: 'load_pose_smpl',
      pose,
      trans,
      inference_type: inferenceType,
      normalize,
      random_root: randomRoot,
      count_offset: countOffset,
      use_quat: useQuat,
      euler_order: eulerOrder,
      model: modelType,
      target_rotation: targetRotation  // Add rotation data
    }));
  }
</script>

<div class="bg-white rounded-lg shadow p-6 space-y-6">
  <h3 class="text-lg font-semibold">SMPL Pose Loader</h3>
  
  <!-- File Input Section -->
  <div class="space-y-4">
    <div class="flex items-center gap-4">
      <input
        type="file"
        accept=".json"
        on:change={handleFileSelect}
        class="hidden"
        bind:this={fileInput}
      />
      <button
        on:click={() => fileInput.click()}
        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
      >
        Select JSON File
      </button>
      <span class="text-sm text-gray-600">{fileName || "No file selected"}</span>
    </div>

    <!-- Frame Navigation -->
    {#if poseData}
      <div class="space-y-2">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium">Frame: {currentFrame + 1} / {totalFrames}</span>
          <div class="flex gap-2">
            <button
              on:click={previousFrame}
              disabled={currentFrame === 0}
              class="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              on:click={nextFrame}
              disabled={currentFrame === totalFrames - 1}
              class="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
        
        <input 
          type="range"
          min="0"
          max={totalFrames - 1}
          bind:value={currentFrame}
          on:change={() => loadFrame(currentFrame)}
          class="w-full"
        />
      </div>
    {/if}
  </div>

  <!-- Add Rotation Controls -->
  <div class="space-y-4">
    <h4 class="text-sm font-medium text-gray-700">Target Rotation (degrees)</h4>
    <div class="grid grid-cols-1 gap-4">
      <!-- X Rotation -->
      <div class="space-y-2">
        <div class="flex justify-between">
          <label class="text-sm text-gray-600">X Rotation</label>
          <span class="text-sm text-gray-600">{targetRotation.x}°</span>
        </div>
        <input 
          type="range"
          min="-180"
          max="180"
          step="5"
          bind:value={targetRotation.x}
          class="w-full"
        />
      </div>

      <!-- Y Rotation -->
      <div class="space-y-2">
        <div class="flex justify-between">
          <label class="text-sm text-gray-600">Y Rotation</label>
          <span class="text-sm text-gray-600">{targetRotation.y}°</span>
        </div>
        <input 
          type="range"
          min="-180"
          max="180"
          step="5"
          bind:value={targetRotation.y}
          class="w-full"
        />
      </div>

      <!-- Z Rotation -->
      <div class="space-y-2">
        <div class="flex justify-between">
          <label class="text-sm text-gray-600">Z Rotation</label>
          <span class="text-sm text-gray-600">{targetRotation.z}°</span>
        </div>
        <input 
          type="range"
          min="-180"
          max="180"
          step="5"
          bind:value={targetRotation.z}
          class="w-full"
        />
      </div>

      <!-- Quick Presets -->
      <div class="flex gap-2 flex-wrap">
        <button
          on:click={() => {
            targetRotation = { x: -90, y: 0, z: -90 };
          }}
          class="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200"
        >
          Default
        </button>
        <button
          on:click={() => {
            targetRotation = { x: -90, y: 90, z: -90 };
          }}
          class="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200"
        >
          Face Right
        </button>
        <button
          on:click={() => {
            targetRotation = { x: -90, y: -90, z: -90 };
          }}
          class="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200"
        >
          Face Left
        </button>
        <button
          on:click={() => {
            targetRotation = { x: -90, y: 180, z: -90 };
          }}
          class="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200"
        >
          Face Back
        </button>
      </div>
    </div>
  </div>

  <!-- SMPL Parameters -->
  <div class="grid grid-cols-2 gap-4">
    <label class="flex items-center gap-2">
      <input 
        type="checkbox"
        bind:checked={normalize}
        class="form-checkbox"
      />
      <span>Normalize</span>
    </label>

    <label class="flex items-center gap-2">
      <input 
        type="checkbox"
        bind:checked={randomRoot}
        class="form-checkbox"
      />
      <span>Random Root</span>
    </label>

    <label class="flex items-center gap-2">
      <input 
        type="checkbox"
        bind:checked={countOffset}
        class="form-checkbox"
      />
      <span>Count Offset</span>
    </label>

    <label class="flex items-center gap-2">
      <input 
        type="checkbox"
        bind:checked={useQuat}
        class="form-checkbox"
      />
      <span>Use Quaternion</span>
    </label>
  </div>

  <!-- Dropdowns -->
  <div class="grid grid-cols-2 gap-4">
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">
        Euler Order
      </label>
      <select 
        bind:value={eulerOrder}
        class="form-select w-full"
      >
        <option value="ZYX">ZYX</option>
        <option value="XYZ">XYZ</option>
        <option value="YZX">YZX</option>
      </select>
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">
        Model Type
      </label>
      <select 
        bind:value={modelType}
        class="form-select w-full"
      >
        <option value="smpl">SMPL</option>
        <option value="smplh">SMPL-H</option>
      </select>
    </div>

    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">
        Inference Type
      </label>
      <select 
        bind:value={inferenceType}
        class="form-select w-full"
      >
        <option value="goal">Goal</option>
        <option value="current">Current</option>
      </select>
    </div>
  </div>

  <button 
    on:click={sendPose}
    class="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    disabled={!pose.length}
  >
    Send SMPL Pose
  </button>
</div>

<style>
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

  .form-checkbox:focus,
  .form-select:focus {
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
  }

  /* Range input styles using pure CSS */
  input[type="range"] {
    width: 100%;
    height: 8px;
    background-color: #e5e7eb;
    border-radius: 8px;
    appearance: none;
    cursor: pointer;
  }

  input[type="range"]::-webkit-slider-thumb {
    appearance: none;
    width: 16px;
    height: 16px;
    background-color: #2563eb;
    border-radius: 50%;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  input[type="range"]::-moz-range-thumb {
    width: 16px;
    height: 16px;
    background-color: #2563eb;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  /* Hover states */
  input[type="range"]::-webkit-slider-thumb:hover {
    background-color: #1d4ed8;
  }

  input[type="range"]::-moz-range-thumb:hover {
    background-color: #1d4ed8;
  }

  /* Focus states */
  input[type="range"]:focus {
    outline: none;
  }

  input[type="range"]:focus::-webkit-slider-thumb {
    box-shadow: 0 0 0 2px #fff, 0 0 0 4px #2563eb;
  }

  input[type="range"]:focus::-moz-range-thumb {
    box-shadow: 0 0 0 2px #fff, 0 0 0 4px #2563eb;
  }
</style> 