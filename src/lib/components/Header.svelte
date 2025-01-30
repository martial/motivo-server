<script>
  import { onMount, onDestroy } from 'svelte';
  import { websocketService } from '../services/websocketService';
  import { writable } from 'svelte/store';

  export let title = "Liminal Motivo Server";
  
  const connectedClients = writable(0);
  const uniqueClients = writable(0);
  let cleanupMessageHandler;

  function handleMessage(data) {
    if (data.type === "debug_model_info") {
      $connectedClients = data.connected_clients;
      $uniqueClients = data.unique_clients;
    }
  }

  onMount(() => {
    cleanupMessageHandler = websocketService.addMessageHandler(handleMessage);
  });

  onDestroy(() => {
    if (cleanupMessageHandler) cleanupMessageHandler();
  });
</script>

<header class="w-full bg-white py-6">
  <div class="px-8 flex justify-between items-center">
    <h1 class="text-4xl font-black text-black">
      {title}
    </h1>
    <div class="flex items-center gap-4">
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
  </div>
</header> 