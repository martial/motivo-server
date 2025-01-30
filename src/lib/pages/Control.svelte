<script>
    import { onMount, onDestroy } from 'svelte';
    import LiveFeed from '../components/LiveFeed.svelte';
    import ParameterPanel from '../components/ParameterPanel.svelte';
    import RewardPanel from '../components/RewardPanel.svelte';
    import RecordButton from '../components/RecordButton.svelte';
    import FavoritesOverview from '../components/FavoritesOverview.svelte';
    import ActiveRewardsPanel from '../components/ActiveRewardsPanel.svelte';
    import { parameterStore } from '../stores/parameterStore';
    import { rewardStore } from '../stores/rewardStore';
    import { websocketService } from '../services/websocketService';
    
    let isSocketReady = $state(false);
    let cleanupListener;

    onMount(() => {
        cleanupListener = websocketService.onReadyStateChange((ready) => {
            isSocketReady = ready;
        });
        isSocketReady = websocketService.getSocket()?.readyState === WebSocket.OPEN;
    });
    
    onDestroy(() => {
        if (cleanupListener) cleanupListener();
    });
</script>
  
<div class="bg-gray-50 p-2">
    <!-- Main Content - All panels in flex layout -->
    <div class="flex flex-wrap gap-2">
        <div class="w-[400px] p-2 order-1">
            <ParameterPanel />
        </div>
        
        <div class="w-[400px] p-2 order-2">
            <RewardPanel />
        </div>

        <div class="w-[400px] p-2 order-3">
            <ActiveRewardsPanel />
        </div>

        <div class="w-[400px] p-2 order-4 lg:order-3">
            <LiveFeed />
            <div class="mt-4 flex justify-center">
                {#if isSocketReady}
                    <RecordButton socket={websocketService.getSocket()} />
                {/if}
            </div>
        </div>
    </div>

    <!-- Favorites Overview Section -->
    <div class="mt-8">
        <FavoritesOverview />
    </div>
</div>