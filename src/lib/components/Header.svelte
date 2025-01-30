<script>
  import { onMount, onDestroy } from 'svelte';
  import { websocketService } from '../services/websocketService';
  import { writable } from 'svelte/store';
  import { Link } from "svelte-routing";

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
    <nav class="flex gap-4">
      <Link to="/" class="hover:text-blue-600">Home</Link>
      <Link to="/live" class="hover:text-blue-600">Live Feed</Link>
      <Link to="/control" class="hover:text-blue-600">Control</Link>
    </nav>
  </div>
</header> 