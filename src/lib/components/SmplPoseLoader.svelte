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

  // Add default pose data
  //const defaultPose =[ new Array(72).fill(0); // SMPL has 72 pose parameters]
  const defaultPose = [1.5850721889160841, 0.07498726665742086, 0.037897972505572544, 0.0843521525751471, 0.02069803256395046, 0.14988575735541432, 0.11726372670048717, -0.07824522997883027, 0.008997502566853652, 0.009989143229948072, -0.006622598701523695, -0.03998901998836509, -0.09086070156938798, -0.08445963442698894, -0.12207894682458599, -0.09666895616486985, 0.024597971726213332, 0.08682869968223415, -0.22884568728101604, -0.10812503319873148, -0.02078814195882335, -0.013545852393296505, 0.2785296054132192, -0.0030450019326130474, -0.04243035307568436, -0.2278602466186468, -0.06525237544474191, -0.13633604299619334, 0.0037843634911357144, 0.05597621959927843, 0.0003708710426668533, 0.02187080141780995, -0.00046056991543160495, 0.007912124654258456, 0.048549666375678695, -0.0014180728739292372, 0.045922483619452975, 0.038837584151389916, -0.09921309568416739, -0.2089601802410566, -0.3092193133251381, 0.4875935186935577, -0.20604976579298823, 0.3105462422179398, -0.49742963775601295, -0.059032594721949175, -0.1365553313977156, 0.23345384461918545, -0.6240369535105083, -0.8798565605921523, 0.4801193501817766, -0.5098039218838079, 0.8874405499558582, -0.4817264563641992, -0.13976508143138236, -0.44437478198481345, 0.10345421970508258, -0.004893965510053146, 0.3370897638010854, -0.07282694761737396, 0.3078220365733007, -0.20145631198683608, 0.32178601916207583, 0.2799608543008822, 0.12114536070461993, -0.3337358989097452, 0.15579630715916692, 0.045455665823809874, 0.23945913430417848, 0.1415224044876414, -0.09283800187992292, 0.1455620642520421];

  const defaultTrans = [0, 0, 0]; // Default translation

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
    if (!socket) return;

    // Use default pose if no pose is loaded
    const poseToSend = pose.length ? pose : defaultPose;
    const transToSend = trans.length ? trans : defaultTrans;

    console.log("Sending pose with rotation:", targetRotation);
    console.log(poseToSend);
    console.log(transToSend);

    socket.send(JSON.stringify({
      type: 'load_pose_smpl',
      pose: poseToSend,
      trans: transToSend,
      inference_type: inferenceType,
      normalize,
      random_root: randomRoot,
      count_offset: countOffset,
      use_quat: useQuat,
      euler_order: eulerOrder,
      model: modelType,
      target_rotation: targetRotation
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
    class="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
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