<script lang="ts">
  import { websocketService } from '../services/websocketService';
  
  const { socket } = $props<{ socket: WebSocket }>();
  
  let isRecording = $state(false);
  let isConnected = $state(false);
  let downloadUrl = $state(null);
  
  $effect(() => {
    const socket = websocketService.getSocket();
    isConnected = socket?.readyState === WebSocket.OPEN;
    
    if (socket) {
      socket.addEventListener('message', handleMessage);
      return () => socket.removeEventListener('message', handleMessage);
    }
  });

  function handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'recording_status') {
        isRecording = data.status === 'started';
        if (data.status === 'stopped' && data.downloadUrl) {
          downloadUrl = data.downloadUrl;
        }
      }
    } catch (error) {
      console.error('Error parsing message:', error);
    }
  }

  function toggleRecording() {
    downloadUrl = null; // Reset download URL when starting new recording
    const socket = websocketService.getSocket();
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    const message = {
      type: isRecording ? 'stop_recording' : 'start_recording',
      timestamp: new Date().toISOString()
    };
    
    console.log('Sending message:', message);
    socket.send(JSON.stringify(message));
  }
</script>

<div class="flex gap-2">
  <button
    on:click={toggleRecording}
    class="flex items-center gap-2 px-4 py-2 rounded-full font-medium transition-colors {isRecording 
      ? 'bg-red-500 hover:bg-red-600 text-white' 
      : 'bg-green-500 hover:bg-green-600 text-white'}"
    disabled={!isConnected}
  >
    <div class="w-3 h-3 rounded-full {isRecording ? 'animate-pulse bg-white' : 'bg-white'}"></div>
    {isRecording ? 'Stop Recording' : 'Start Recording'}
  </button>

  {#if downloadUrl}
    <a
      href={downloadUrl}
      download="recording.zip"
      class="flex items-center gap-2 px-4 py-2 rounded-full font-medium bg-blue-500 hover:bg-blue-600 text-white transition-colors"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
      Download Recording
    </a>
  {/if}
</div>

<style>
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style> 