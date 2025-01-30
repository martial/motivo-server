<script>
  import { onMount, onDestroy } from 'svelte';
  import { websocketService } from '../services/websocketService';
  import StatusBar from './StatusBar.svelte';
  
  const apiUrl = import.meta.env.VITE_API_URL;

  // Reactive states
  let currentImageUrl = `${apiUrl}/amjpeg?${Date.now()}`;
  let nextImageUrl;
  let isLoading = true;
  let qValue = 0;
  let isRecording = false;

  // WebSocket status tracking
  let cleanupListener;
  let isConnected = false;

  function loadNextImage() {
    nextImageUrl = `${apiUrl}/amjpeg?${Date.now()}`;
  }

  function handleImageLoad() {
    isLoading = false;
    currentImageUrl = nextImageUrl;
    setTimeout(loadNextImage, 100);
  }

  function handleImageError() {
    isLoading = true;
    setTimeout(loadNextImage, 1000); // Longer retry on error
  }

  // Recording controls
  function toggleRecording() {
    const socket = websocketService.getSocket();
    if (!socket) return;

    if (!isRecording) {
      socket.send(JSON.stringify({
        type: "start_recording",
        timestamp: new Date().toISOString()
      }));
    } else {
      socket.send(JSON.stringify({
        type: "stop_recording",
        timestamp: new Date().toISOString()
      }));
    }
  }

  // Handle WebSocket messages
  websocketService.handleMessage = (data) => {
    if (data.type === "recording_status") {
      isRecording = data.status === "started";
    }
  };

  function handleReadyState(ready) {
    isConnected = ready;
  }
  
  onMount(() => {
    loadNextImage();
    cleanupListener = websocketService.onReadyStateChange(handleReadyState);
  });
  
  onDestroy(() => {
    if (cleanupListener) cleanupListener();
  });
</script>

<div class="max-w-[320px] mx-auto space-y-4">
  <!-- Image Container -->
  <div class="relative rounded-xl overflow-hidden bg-white shadow-lg border border-gray-200">
    {#if isLoading}
      <div class="absolute inset-0 flex items-center justify-center bg-gray-50/80 backdrop-blur-sm">
        <div class="animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
      </div>
    {/if}
    
    <!-- Main Feed -->
    <img 
      src={currentImageUrl}
      alt="Simulation Feed"
      class="w-[320px] h-[240px] object-contain"
    />
    
    <!-- Preload Next Image -->
    <img 
      src={nextImageUrl}
      alt="Preload Feed"
      class="hidden"
      on:load={handleImageLoad}
      on:error={handleImageError}
    />

    <!-- Overlay Controls -->
    <div class="absolute bottom-0 left-0 right-0 p-2 bg-black/50 backdrop-blur-sm">
      <div class="flex items-center justify-between text-white">
        <span class="text-sm font-medium">Q-Value: {qValue.toFixed(3)}</span>
        <button
          on:click={toggleRecording}
          class={`px-3 py-1 rounded text-sm font-medium ${
            isRecording 
              ? 'bg-red-500 hover:bg-red-600' 
              : 'bg-green-500 hover:bg-green-600'
          }`}
          disabled={!isConnected}
        >
          {isRecording ? 'Stop Recording' : 'Start Recording'}
        </button>
      </div>
    </div>
  </div>

  <!-- Status Bar -->
  <StatusBar 
    {isLoading}
    {isConnected}
    {isRecording}
  />

  <!-- Additional Controls -->
  <div class="bg-white rounded-lg shadow p-4">
    <h3 class="text-lg font-semibold mb-2">Feed Controls</h3>
    <div class="flex gap-2">
      <button
        class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        disabled={!isConnected}
        on:click={() => {
          const socket = websocketService.getSocket();
          if (socket) {
            socket.send(JSON.stringify({ type: "clean_rewards" }));
          }
        }}
      >
        Reset Simulation
      </button>
    </div>
  </div>
</div> 