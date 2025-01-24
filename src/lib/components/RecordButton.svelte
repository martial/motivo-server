<script>
  import { websocketService } from '../services/websocketService';
  
  let isRecording = $state(false);
  let isConnected = $state(false);
  
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
      }
    } catch (error) {
      console.error('Error parsing message:', error);
    }
  }

  function toggleRecording() {
    const socket = websocketService.getSocket();
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    const message = {
      type: isRecording ? 'stop_recording' : 'start_recording',
      timestamp: new Date().toISOString()
    };
    
    socket.send(JSON.stringify(message));
  }
</script>

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

<style>
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style> 