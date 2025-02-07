<script>
  import { onMount, onDestroy } from "svelte";
  import { websocketService, computingStatus } from "../services/websocketService";
  import { writable } from "svelte/store";
  import LiveFeed from "../components/LiveFeed.svelte";
  import VibePanel from "../components/VibePanel.svelte";
  import SmplPoseLoader from "../components/SmplPoseLoader.svelte";

  // Reactive stores
  const status = writable("Disconnected");
  const isComputing = writable(false);

  // Handle WebSocket ready state changes
  let cleanupListener;
  let cleanupMessageHandler;
  let statusInterval;

  let poseInput = "";
  let poseError = "";

  // Add new reactive variables
  let mixWeight = 0.5; // Default to 50/50 mix
  let currentReward = {
    rewards: [
      { name: "move-ego", move_speed: 0.0, stand_height: 1.4 }
    ],
    weights: [1.0]
  };

  let parsedPose = [];
  let parsedTrans = [0, 0, 0]; // Default translation

  function handleMessage(data) {
    if (data.type === "debug_model_info") {
      $isComputing = data.is_computing;
    }
    // Handle other message types
    switch (data.type) {
      case "parameters":
      case "parameters_updated":
        import("../stores/parameterStore").then((module) => {
          //module.parameterStore.set(data.parameters);
        });
        break;
      case "recording_status":
        console.log("Recording status update:", data.status);
        break;
    }
  }

  function handleReadyState(isReady) {
    $status = isReady ? "Connected" : "Disconnected";
    if (!isReady) {
      // Reset computing state when connection is lost
      $isComputing = false;
    }
  }

  // Test functions
  function testStanding() {
    const socket = websocketService.getSocket();
    if (!socket) return;
    
    socket.send(JSON.stringify({
      type: "request_reward",
      reward: {
        rewards: [
          { name: "move-ego", move_speed: 0.0, stand_height: 1.4 }
        ],
        weights: [1.0]
      }
    }));
  }

  function testWalking() {
    const socket = websocketService.getSocket();
    if (!socket) return;
    
    socket.send(JSON.stringify({
      type: "request_reward",
      reward: {
        rewards: [
          { name: "move-ego", move_speed: 1.0, stand_height: 1.4 }
        ],
        weights: [1.0]
      }
    }));
  }

  function testZeroPose() {
    const socket = websocketService.getSocket();
    if (!socket) return;
    
    // Create array of 76 zeros for qpos
    const zeroPose = new Array(76).fill(0);
    
    socket.send(JSON.stringify({
      type: "load_pose",
      pose: zeroPose,
      inference_type: "goal"
    }));
  }

  function checkModelStatus() {
    const socket = websocketService.getSocket();
    if (socket && $status === "Connected") {
      socket.send(JSON.stringify({ type: "debug_model_info" }));
    }
  }

  function parsePoseInput(input) {
    try {
      // Remove newlines and multiple spaces, split by commas
      const values = input
        .replace(/\n/g, '')
        .replace(/\s+/g, ' ')
        .trim()
        .split(',')
        .map(v => parseFloat(v.trim()));

      if (values.length !== 76) {
        throw new Error(`Invalid pose length: ${values.length}, expected 76 values`);
      }

      if (values.some(v => isNaN(v))) {
        throw new Error('Invalid numeric values found');
      }

      return values;
    } catch (error) {
      throw new Error(`Failed to parse pose: ${error.message}`);
    }
  }

  function testCustomPose() {
    try {
      parsedPose = parsePoseInput(poseInput);
      mixPoseAndReward();
      poseError = ""; // Clear any previous errors
    } catch (error) {
      poseError = error.message;
    }
  }

  // Add new function for mixing pose and reward
  function mixPoseAndReward() {
    const socket = websocketService.getSocket();
    if (!socket) return;
    
    try {
      const pose = parsePoseInput(poseInput);
      poseError = ""; // Clear any previous errors
      
      socket.send(JSON.stringify({
        type: "load_pose",
        pose: pose,
       //reward: currentReward,
        //mix_weight: mixWeight
      }));
    } catch (error) {
      poseError = error.message;
    }
  }

  // Add function to update current reward
  function updateReward(moveSpeed = 0.0, standHeight = 1.4) {
    currentReward = {
      rewards: [
        { name: "move-ego", move_speed: moveSpeed, stand_height: standHeight }
      ],
      weights: [1.0]
    };
  }

  onMount(() => {
    // Connect WebSocket
    websocketService.connect();
    
    // Setup ready state listener and message handler
    cleanupListener = websocketService.onReadyStateChange(handleReadyState);
    cleanupMessageHandler = websocketService.addMessageHandler(handleMessage);
    
    // Initialize status based on current connection state
    $status = websocketService.getSocket()?.readyState === WebSocket.OPEN 
      ? "Connected" 
      : "Disconnected";
    
    // Start status check immediately
    checkModelStatus();
    
    // Set up regular status check
    statusInterval = setInterval(checkModelStatus, 1000);
  });

  onDestroy(() => {
    if (cleanupListener) cleanupListener();
    if (cleanupMessageHandler) cleanupMessageHandler();
    if (statusInterval) clearInterval(statusInterval);
  });
</script>

<div class="p-4">
  <div class="grid md:grid-cols-2 gap-6">
    <!-- Left Column: Controls -->
    <div class="bg-white rounded-lg shadow-lg p-6">
      
      <!-- Status Section -->
      <div class="mb-6 p-4 bg-gray-100 rounded-lg">
        <h2 class="text-xl font-semibold mb-2">System Status</h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <span class="font-medium">Connection:</span>
            <span class={$status === "Connected" ? "text-green-600" : "text-red-600"}>
              {$status}
            </span>
          </div>
          <div>
            <span class="font-medium">Computing:</span>
            <span class={$status !== "Connected" ? "text-gray-400" : ($computingStatus ? "text-yellow-600" : "text-green-600")}>
              {$status !== "Connected" ? "Unavailable" : ($computingStatus ? "Processing..." : "Ready")}
            </span>
          </div>
        </div>
      </div>

      <!-- Control Section -->
      <div class="mb-6">
        <h2 class="text-xl font-semibold mb-4">Test Controls</h2>
        <div class="flex flex-wrap gap-4">
          <button
            on:click={testStanding}
            class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            disabled={$status !== "Connected"}
          >
            Test Standing
          </button>
          <button
            on:click={testWalking}
            class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
            disabled={$status !== "Connected"}
          >
            Test Walking
          </button>
          <button
            on:click={testZeroPose}
            class="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors"
            disabled={$status !== "Connected"}
          >
            Test Zero Pose
          </button>
        </div>
      </div>

      <!-- Custom Pose Section -->
      <div class="mb-8 bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-semibold mb-4">Custom Pose</h2>
        <div class="space-y-4">
          <div>
            <textarea
              bind:value={poseInput}
              placeholder="Paste pose values here (76 comma-separated numbers)"
              class="w-full h-32 p-2 border rounded-lg font-mono text-sm resize-y"
            ></textarea>
            {#if poseError}
              <p class="text-red-500 text-sm mt-1">{poseError}</p>
            {/if}
          </div>
          <button
            on:click={testCustomPose}
            class="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors"
            disabled={$status !== "Connected"}
          >
            Parse Pose
          </button>
        </div>
      </div>

    
        <SmplPoseLoader 
          pose={parsedPose}
          trans={parsedTrans}
        />

      <!-- New Mix Controls Section -->
      <div class="mb-6">
        <h2 class="text-xl font-semibold mb-4">Mix Pose & Reward</h2>
        <div class="space-y-4">
          <!-- Mix Weight Slider -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Mix Weight: {(mixWeight * 100).toFixed(0)}% Reward
            </label>
            <input 
              type="range" 
              bind:value={mixWeight} 
              min="0" 
              max="1" 
              step="0.1"
              class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div class="flex justify-between text-xs text-gray-500 mt-1">
              <span>All Pose</span>
              <span>All Reward</span>
            </div>
          </div>

          <!-- Reward Presets -->
          <div class="flex flex-wrap gap-2">
            <button
              on:click={() => updateReward(0.0, 1.4)}
              class="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors text-sm"
            >
              Standing
            </button>
            <button
              on:click={() => updateReward(1.0, 1.4)}
              class="px-3 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors text-sm"
            >
              Walking
            </button>
            <button
              on:click={() => updateReward(2.0, 1.4)}
              class="px-3 py-1 bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 transition-colors text-sm"
            >
              Running
            </button>
          </div>

          <!-- Mix Button -->
          <button
            on:click={mixPoseAndReward}
            class="w-full px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded hover:from-purple-700 hover:to-blue-700 transition-colors"
            disabled={$status !== "Connected"}
          >
            Apply Mix
          </button>
        </div>
      </div>
    </div>

    <!-- Right Column: Live Feed -->
    <div>
      <LiveFeed />
    </div>
   
  </div>
</div> 