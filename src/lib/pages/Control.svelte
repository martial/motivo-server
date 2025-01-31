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
    import VibePanel from '../components/VibePanel.svelte';
    
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
  
<div class="bg-gray-50 min-h-screen p-4">
    <div class="flex flex-col gap-8">
        <div class="flex flex-wrap gap-8">
            <!-- Left column with LiveFeed and VibePanel -->
            <div class="flex-none w-[420px] flex flex-col gap-8 bg-blue-100/50 p-4 rounded-xl">
                <LiveFeed />
                <ParameterPanel class="flex-1 min-w-[400px]" />

                <!--<VibePanel />-->
            </div>
            
            <!-- Right section with reward panels -->
            <div class="flex-1 flex flex-wrap gap-8">
                <!-- Isolated RewardPanel with its own background -->
                <div class="flex-1 max-w-[420px] bg-amber-100/50 p-4 rounded-xl">
                    <RewardPanel />
                </div>
                
                <!-- Isolated ActiveRewardsPanel with its own background -->
                <div class="flex-1 min-w-[400px] bg-green-100/50 p-4 rounded-xl">
                    <ActiveRewardsPanel />
                </div>
            </div>
        </div>
        
        <!-- Full-width FavoritesOverview at the bottom -->
        <div class="w-full bg-purple-100/50 p-4 rounded-xl">
            <FavoritesOverview />
        </div>
    </div>
</div>

<style>
    /* Custom grid layout for auto-fitting columns */
    .grid-auto-fit {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 600px), 1fr));
    }
</style>