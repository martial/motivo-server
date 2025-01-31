<script>
  import { onMount, onDestroy } from 'svelte';
  import { websocketService } from '../services/websocketService';
  import { writable } from 'svelte/store';
  import { Link } from "svelte-routing";
  import { versionInfo } from '../stores/versionStore';

  export let title = "Liminal Motivo Server";
  
  const connectedClients = writable(0);
  const uniqueClients = writable(0);
  let cleanupMessageHandler;

  $: isDev = $versionInfo.environment === 'development';

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

<header class="w-full bg-white shadow-sm">
  <div class="container mx-auto">
    <div class="px-8 py-2 flex justify-between items-center">
      <h1 class="text-2xl font-black text-black">
        {title}
      </h1>
      <nav class="flex gap-4">
        <Link to="/" class="hover:text-blue-600">Home</Link>
        <Link to="/live" class="hover:text-blue-600">Live Feed</Link>
        <Link to="/control" class="hover:text-blue-600">Control</Link>
      </nav>
    </div>

    {#if isDev}
      <div class="px-8 pb-2">
        <div class="text-xs bg-yellow-100 px-2 py-0.5 rounded-md inline-block">
          🔧 Dev Build: {$versionInfo.version} 
          <span class="text-gray-600">({$versionInfo.commitHash.substring(0, 7)})</span>
        </div>
      </div>
    {/if}
  </div>
</header> 