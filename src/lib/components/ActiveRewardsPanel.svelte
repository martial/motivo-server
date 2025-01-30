<script>
  import { rewardStore, COMBINATION_TYPES } from '../stores/rewardStore';

  // Initialize display weights from store and ensure they're numbers
  let displayWeights = $rewardStore.weights.map(w => Number(w) || 0);

  // Subscribe to store changes to keep display weights in sync
  $: {
    displayWeights = $rewardStore.weights.map(w => Number(w) || 0);
  }

  // Debounce function
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  const debouncedUpdateWeight = debounce((index, value) => {
    rewardStore.updateWeight(index, value);
  }, 300);

  function handleWeightChange(index, value) {
    const numericValue = Number(value) || 0;
    displayWeights[index] = numericValue;
    displayWeights = [...displayWeights];
    debouncedUpdateWeight(index, numericValue);
  }
</script>

<div class="w-96 py-4">
  <div class="bg-white rounded-lg shadow-lg p-4">
    <h1 class="text-lg font-bold mb-4 text-gray-800">Active Rewards</h1>
    
    {#if $rewardStore.activeRewards.length > 0}
      <div class="mb-4">
        {#each $rewardStore.activeRewards as reward, i}
          <div class="flex items-center gap-2 mb-2 bg-gray-50 p-2 rounded">
            <div class="flex-grow">
              <div class="text-sm font-medium">{reward.name}</div>
              <div class="text-xs text-gray-500">
                Weight: 
                <input 
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={displayWeights[i]}
                  on:input={(e) => handleWeightChange(i, parseFloat(e.target.value))}
                  class="w-24 inline-block"
                />
                {(displayWeights[i] * 100).toFixed(0)}%
              </div>
            </div>
            <button
              on:click={() => rewardStore.removeReward(i)}
              class="text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        {/each}

        <select
          bind:value={$rewardStore.combination_type}
          class="mt-2 block w-full text-sm rounded-md border-0 py-2 pl-3 pr-12 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-blue-600 bg-white shadow-sm appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20fill%3D%22none%22%20viewBox%3D%220%200%2020%2020%22%3E%3Cpath%20stroke%3D%22%236b7280%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20stroke-width%3D%221.5%22%20d%3D%22m6%208%204%204%204-4%22%2F%3E%3C%2Fsvg%3E')] bg-[position:right_0.5rem_center] bg-[length:1.5em_1.5em] bg-no-repeat"
        >
          {#each COMBINATION_TYPES as type}
            <option value={type}>{type}</option>
          {/each}
        </select>

        <button
          on:click={() => rewardStore.cleanRewards()}
          class="mt-2 w-full bg-red-600 text-white px-3 py-1 text-sm rounded hover:bg-red-700"
        >
          Clear All Rewards
        </button>
      </div>
    {:else}
      <div class="text-sm text-gray-500 italic">No active rewards</div>
    {/if}
  </div>
</div> 