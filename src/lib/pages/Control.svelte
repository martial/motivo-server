<script>
    import { onMount, onDestroy } from 'svelte';
    import LiveFeed from '../components/LiveFeed.svelte';
    import ParameterPanel from '../components/ParameterPanel.svelte';
    import RewardPanel from '../components/RewardPanel.svelte';
    import RecordButton from '../components/RecordButton.svelte';
    import { parameterStore } from '../stores/parameterStore';
    import { rewardStore } from '../stores/rewardStore';
  
    let socket;
    // get vite VITE_WS_URL
    const wsUrl = import.meta.env.VITE_WS_URL;
    let isSocketReady = false;

    onMount(() => {
    
      console.log("wsUrl", wsUrl);
      socket = new WebSocket(wsUrl);
      
      socket.onopen = () => {
        console.log('WebSocket connected');
        isSocketReady = true;
      };
  
      socket.onmessage = (event) => {
        console.log('Control received:', event.data);
        const data = JSON.parse(event.data);
        // Route messages to appropriate stores based on type
        if (data.type === "parameters" || data.type === "parameters_updated") {
          parameterStore.set(data.parameters);
        }
        // Log recording status messages
        if (data.type === "recording_status") {
          console.log('Recording status update:', data.status);
        }
      };
  
      socket.onclose = () => {
        console.log('WebSocket disconnected');
        isSocketReady = false;
      };
  
      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        isSocketReady = false;
      };
  
      // Set the socket in both stores once connected
      parameterStore.setSocket(socket);
      rewardStore.setSocket(socket);
    });
  
    onDestroy(() => {
      if (socket) {
        parameterStore.disconnect();
        rewardStore.disconnect();
        socket.close();
      }
    });
  </script>
  
  <div class="bg-gray-50 p-6 relative">
    <!-- Live Feed - Fixed Top Right -->
    <div class="absolute top-6 right-6 w-[320px] mt-[30px]">
      <LiveFeed />
      <div class="mt-4 flex justify-center">
        {#if isSocketReady}
          <RecordButton {socket} />
        {/if}
      </div>
    </div>

    <!-- Main Content - Fixed width panels with static spacing -->
    <div class="mr-[344px]">
      <div class="flex gap-8">
        <div class="w-[400px] p-4">
          <ParameterPanel />
        </div>
        
        <div class="w-[400px] p-4">
          <RewardPanel />
        </div>
      </div>
    </div>
  </div>