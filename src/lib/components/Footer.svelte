<script>
  import { onMount, onDestroy } from 'svelte';
  import { websocketService } from '../services/websocketService';
  import { writable } from 'svelte/store';

  const connectedClients = writable(0);
  const uniqueClients = writable(0);
  let cleanupMessageHandler;
  let intervalId;

  function handleMessage(data) {
    if (data.type === "debug_model_info") {
      $connectedClients = data.connected_clients;
      $uniqueClients = data.unique_clients;
    }
  }

  function requestDebugInfo() {
    websocketService.send({
      type: "debug_model_info"
    });
  }

  onMount(() => {
    cleanupMessageHandler = websocketService.addMessageHandler(handleMessage);
    
    // Request initial debug info
    requestDebugInfo();
    
    // Set up periodic updates every 5 seconds
    intervalId = setInterval(requestDebugInfo, 5000);
  });

  onDestroy(() => {
    if (cleanupMessageHandler) cleanupMessageHandler();
    if (intervalId) clearInterval(intervalId);
  });
</script>

<footer class="fixed bottom-0 left-0 w-full py-4 bg-white shadow-md">
  <div class="w-full px-4 flex justify-center gap-4">
    <div class="flex items-center gap-2">
      <span class="text-sm font-medium text-gray-500">Total Connections:</span>
      <span class="px-2 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
        {$connectedClients}
      </span>
    </div>
    <div class="flex items-center gap-2">
      <span class="text-sm font-medium text-gray-500">Unique Users:</span>
      <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
        {$uniqueClients}
      </span>
    </div>
  </div>
</footer> 