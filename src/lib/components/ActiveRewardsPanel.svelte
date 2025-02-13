<script>
  import { onMount, onDestroy } from 'svelte';
  import { websocketService } from '../services/websocketService';
  import { fade } from 'svelte/transition';
  import { REWARD_TYPES } from '../stores/rewardStore';
  import { favoriteStore } from '../stores/favoriteStore';
  import ParameterControl from './ParameterControl.svelte';
  import ParameterGroup from './ParameterGroup.svelte';

  let activeRewards = $state(null);
  let pendingChanges = $state({});
  let cleanupHandler;

  onMount(() => {
    cleanupHandler = websocketService.addMessageHandler((data) => {
      if (data.type === 'debug_model_info') {
        activeRewards = data.active_rewards;
      }
    });

    // Request initial state
    websocketService.getSocket()?.send(JSON.stringify({
      type: "debug_model_info"
    }));
  });

  onDestroy(() => {
    if (cleanupHandler) cleanupHandler();
  });

  function handleParameterChange(rewardIndex, event) {
    const { name, value } = event.detail;
    if (!pendingChanges[rewardIndex]) {
      pendingChanges[rewardIndex] = {};
    }
    
    // Special handling for weight changes
    if (name === 'weight') {
      // Create a copy of the current weights array
      const newWeights = [...activeRewards.weights];
      newWeights[rewardIndex] = value;
      
      // Send immediate weight update
      websocketService.getSocket()?.send(JSON.stringify({
        type: 'request_reward',
        reward: {
          ...activeRewards,
          weights: newWeights
        },
        timestamp: new Date().toISOString()
      }));
    } else {
      // Handle other parameter changes as before
      pendingChanges[rewardIndex][name] = value;
    }
  }

  function updateReward(rewardIndex) {
    if (!activeRewards || !pendingChanges[rewardIndex]) return;
    websocketService.updateReward(rewardIndex, pendingChanges[rewardIndex]);
    delete pendingChanges[rewardIndex];
  }

  function removeReward(rewardIndex) {
    if (!activeRewards) return;
    const updatedRewards = {
      ...activeRewards,
      rewards: activeRewards.rewards.filter((_, idx) => idx !== rewardIndex),
      weights: activeRewards.weights.filter((_, idx) => idx !== rewardIndex)
    };
    websocketService.getSocket()?.send(JSON.stringify({
      type: 'request_reward',
      reward: updatedRewards,
      timestamp: new Date().toISOString()
    }));
  }

  function saveCurrentConfig() {
    const name = prompt('Enter a name for this configuration:');
    if (!name || !activeRewards) return;
    
    // Format the rewards data to include weights
    const rewardsWithWeights = activeRewards.rewards.map((reward, index) => ({
      ...reward,
      weight: activeRewards.weights[index]
    }));

    // Save to favoriteStore
    favoriteStore.saveFavorite(name, {
      activeRewards: rewardsWithWeights,
      combinationType: activeRewards.combinationType
    });
  }
</script>

<div class="h-full w-full">
  <div class="bg-white rounded-lg shadow-lg p-4 h-full">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-lg font-bold text-gray-800">Active Rewards</h1>
      {#if activeRewards?.rewards?.length > 0}
        <button 
          class="bg-green-500 text-white px-3 py-1 text-sm font-medium rounded-md hover:bg-green-600 transition-colors"
          on:click={saveCurrentConfig}
        >
          Save Current
        </button>
      {/if}
    </div>
    
    {#if activeRewards}
      <div class="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4 auto-rows-min">
        {#each activeRewards.rewards as reward, rewardIndex}
          <div class="border rounded-md p-4 bg-white flex flex-col min-h-[200px]" transition:fade>
            <!-- Header - Single row with name and weight -->
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-xl font-bold text-blue-500 font-display tracking-wide">
                {reward.name}
              </h3>
              <div class="flex items-center gap-2">
               
                <div class="w-24 relative">
                  <ParameterControl
                    name="weight"
                    label={"weight"}
                    type="range"
                    value={activeRewards.weights[rewardIndex] * 100}
                    min={0}
                    max={100}
                    step={1}
                    on:change={(e) => {
                      const newEvent = {
                        detail: {
                          name: 'weight',
                          value: e.detail.value / 100
                        }
                      };
                      handleParameterChange(rewardIndex, newEvent);
                    }}
                  />
                </div>
               
              </div>
            </div>

            <!-- Divider -->
            <div class="h-px bg-gray-200 -mx-4 mb-4"></div>

            <!-- Parameters - More compact grid -->
            <div class="space-y-4 flex-1">
              <ParameterGroup columns={2}>
                {#each Object.entries(reward).filter(([key]) => !['id', 'name'].includes(key)) as [param, value]}
                  {#if REWARD_TYPES[reward.name]?.[param]}
                    <ParameterControl
                      name={param}
                      label={param.replace(/_/g, ' ')}
                      type={REWARD_TYPES[reward.name][param].type}
                      min={REWARD_TYPES[reward.name][param].min}
                      max={REWARD_TYPES[reward.name][param].max}
                      step={REWARD_TYPES[reward.name][param].step}
                      options={REWARD_TYPES[reward.name][param].options?.map(opt => ({ value: opt, label: opt }))}
                      value={value}
                      on:change={(e) => handleParameterChange(rewardIndex, e)}
                    />
                  {/if}
                {/each}
              </ParameterGroup>
            </div>

            <!-- Action buttons - More compact -->
            <div class="flex justify-end gap-2 mt-auto pt-3">
              <button 
                class="bg-blue-500 text-white px-3 py-1 text-xs font-medium rounded-md hover:bg-blue-600 transition-colors"
                on:click={() => updateReward(rewardIndex)}
              >
                Update
              </button>
              <button 
                class="bg-red-50 text-red-600 px-3 py-1 text-xs font-medium rounded-md hover:bg-red-100 transition-colors"
                on:click={() => removeReward(rewardIndex)}
              >
                Remove
              </button>
            </div>
          </div>
        {/each}

        <div class="text-sm text-gray-600 col-span-full">
          Combination Type: {activeRewards.combinationType}
        </div>
      </div>
    {:else}
      <p class="text-sm text-gray-500 italic">No active rewards</p>
    {/if}
  </div>
</div>

<style lang="postcss">
  input[type="number"] {
    -moz-appearance: textfield;
  }
  input[type="number"]::-webkit-outer-spin-button,
  input[type="number"]::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }
</style> 