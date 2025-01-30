<script>
  import { onMount, onDestroy } from 'svelte';
  import { websocketService, computingStatus } from '../services/websocketService';
  import StatusBar from './StatusBar.svelte';
  import RecordButton from './RecordButton.svelte';
  
  const apiUrl = import.meta.env.VITE_API_URL;

  // Reactive states
  let currentImageUrl = `${apiUrl}/amjpeg?${Date.now()}`;
  let nextImageUrl;
  let isLoading = true;
  let qValue = 0;
  let isConnected = false;

  // WebSocket status tracking
  let cleanupListener;

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

  function handleReadyState(ready) {
    isConnected = ready;
    if (!ready) {
      $computingStatus = false;
      isLoading = true;
    }
  }
  
  onMount(() => {
    loadNextImage();
    cleanupListener = websocketService.onReadyStateChange(handleReadyState);
    isConnected = websocketService.getSocket()?.readyState === WebSocket.OPEN;
  });
  
  onDestroy(() => {
    if (cleanupListener) cleanupListener();
  });
</script>

<div class="max-w-[320px] mx-auto space-y-4">

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
  
  <!-- Image Container -->
  <div class="relative rounded-xl overflow-hidden bg-white shadow-lg border border-gray-200">
    {#if !isConnected || isLoading}
      <div class="absolute inset-0 flex items-center justify-center bg-gray-50/80 backdrop-blur-sm">
        <div class="flex flex-col items-center gap-2">
          <div class="animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
          <span class="text-sm text-gray-600">
            {!isConnected ? 'Connecting...' : 'Loading feed...'}
          </span>
        </div>
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

    <!-- Updated Overlay Controls -->
    <div class="absolute bottom-0 left-0 right-0 p-2 bg-black/50 backdrop-blur-sm">
      <div class="flex items-center justify-between text-white">
        <span class="text-sm font-medium">Q-Value: {qValue.toFixed(3)}</span>
        <span class="text-sm font-medium">
          {#if !isConnected}
            <span class="text-red-400">Disconnected</span>
          {:else if $computingStatus}
            <span class="text-yellow-400">Processing...</span>
          {:else}
            <span class="text-green-400">Ready</span>
          {/if}
        </span>
      </div>
    </div>
  </div>

  <!-- Status Bar -->
  <StatusBar 
    {isLoading}
    {isConnected}
  />

 
</div> 