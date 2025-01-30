<script>
  export let isLoading = false;
  export let isConnected = false;
  export let isRecording = false;
</script>

<div class="bg-white rounded-lg shadow p-2">
  <div class="flex gap-4 text-sm">
    <div class="flex items-center gap-2">
      <div class={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
      <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
    </div>
    
    <div class="flex items-center gap-2">
      <div class={`w-2 h-2 rounded-full ${isLoading ? 'bg-yellow-500' : 'bg-green-500'}`}></div>
      <span>{isLoading ? 'Loading' : 'Ready'}</span>
    </div>

    {#if isRecording}
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
        <span class="text-red-500">Recording</span>
      </div>
    {/if}
  </div>
</div> 