<script>
    import { onMount, onDestroy } from 'svelte';
    import LiveFeed from '../components/LiveFeed.svelte';
    import ParameterPanel from '../components/ParameterPanel.svelte';
    import RewardPanel from '../components/RewardPanel.svelte';
    import RecordButton from '../components/RecordButton.svelte';
    import { parameterStore } from '../stores/parameterStore';
    import { rewardStore } from '../stores/rewardStore';
    import { websocketService } from '../services/websocketService';
    
    let isSocketReady = $state(false);
    
    // Subscribe to websocket ready state
    $effect(() => {
        websocketService.isReady.subscribe(ready => {
            isSocketReady = ready;
        });
    });

    onMount(() => {
        websocketService.connect();
    });
    
    onDestroy(() => {
        parameterStore.disconnect();
        rewardStore.disconnect();
        websocketService.disconnect();
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