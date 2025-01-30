<script>
  import { rewardStore, REWARD_TYPES, COMBINATION_TYPES } from '../stores/rewardStore';
  import { favoriteStore } from '../stores/favoriteStore';
  import ParameterControl from './ParameterControl.svelte';
  import ParameterGroup from './ParameterGroup.svelte';
  import { v4 as uuidv4 } from 'uuid';

  const REWARD_GROUPS = {
    'Basic Movements': ['move-ego', 'jump', 'rotation', 'crawl'],
    'Poses': ['raisearms', 'headstand', 'liedown', 'sit', 'split'],
    'Combined Actions': ['move-and-raise-arms'],
    'Hand Controls': [
      'left-hand-height', 'left-hand-lateral', 'left-hand-forward',
      'right-hand-height', 'right-hand-lateral', 'right-hand-forward',
      'hand-height', 'hand-lateral'
    ],
    'Foot Controls': [
      'left-foot-height', 'right-foot-height',
      'left-foot-lateral', 'right-foot-lateral',
      'left-foot-forward', 'right-foot-forward'
    ],
    'Other Controls': [
      'stay-upright', 'head-height', 'pelvis-height'
    ]
  };

  let selectedGroup = Object.keys(REWARD_GROUPS)[0];
  let selectedRewardType = REWARD_GROUPS[selectedGroup][0];
  let previousRewardType = selectedRewardType;
  let activeParameters = initializeParameters(selectedRewardType);

  // Initialize display weights from store and ensure they're numbers
  let displayWeights = $rewardStore.weights.map(w => Number(w) || 0);

  // Subscribe to store changes to keep display weights in sync
  $: {
    displayWeights = $rewardStore.weights.map(w => Number(w) || 0);
  }

  // Remove the local favorites variable and use the store directly
  $: favorites = $favoriteStore;

  // Update save favorite function
  function saveAsFavorite() {
    const name = prompt('Enter a name for this favorite:');
    if (name) {
      const favoriteData = {
        activeRewards: $rewardStore.activeRewards.map(reward => ({
          ...reward,
          weight: $rewardStore.weights[$rewardStore.activeRewards.indexOf(reward)]
        })),
        combinationType: $rewardStore.combinationType
      };
      favoriteStore.saveFavorite(name, favoriteData);
    }
  }

  // Update delete favorite function
  function deleteFavorite(name, event) {
    event.stopPropagation();
    if (confirm(`Delete favorite "${name}"?`)) {
      favoriteStore.deleteFavorite(name);
    }
  }

  function initializeParameters(rewardType) {
    const params = {};
    Object.entries(REWARD_TYPES[rewardType]).forEach(([key, config]) => {
      params[key] = config.default;
    });
    return params;
  }

  $: {
    if (previousRewardType !== selectedRewardType) {
      activeParameters = initializeParameters(selectedRewardType);
      previousRewardType = selectedRewardType;
    }
  }

  function handleParameterChange(param, value) {
    activeParameters = {
      ...activeParameters,
      [param]: value
    };
  }

  function addReward() {
    const rewardId = uuidv4();
    const rewardParams = {
      id: rewardId,
      name: selectedRewardType,
      ...activeParameters
    };
    console.log("Adding reward:", rewardParams);
    rewardStore.addReward(selectedRewardType, rewardParams, rewardId);
  }

  // Update selected reward type when group changes
  $: {
    if (!REWARD_GROUPS[selectedGroup].includes(selectedRewardType)) {
      selectedRewardType = REWARD_GROUPS[selectedGroup][0];
    }
  }

  // Add debounce function at the top of the script
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

  // Update the debounced version to only handle store updates
  const debouncedUpdateWeight = debounce((id, value) => {
    rewardStore.updateWeight(id, value);
  }, 300);

  // Update the weight handling function to ensure numeric values
  function handleWeightChange(index, value) {
    const numericValue = Number(value) || 0;
    const reward = $rewardStore.activeRewards[index];
    displayWeights[index] = numericValue;
    displayWeights = [...displayWeights];
    debouncedUpdateWeight(reward.id, numericValue);
  }
</script>

<div class="w-96 py-4">
  <div class="bg-white rounded-lg shadow-lg p-4">
    <h1 class="text-lg font-bold mb-4 text-gray-800">Add Reward</h1>
    
    <div class="space-y-3">
      <!-- Group Selection -->
      <select
        bind:value={selectedGroup}
        class="block w-full text-sm rounded-md border-0 py-2 pl-3 pr-12 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-blue-600 bg-white shadow-sm appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20fill%3D%22none%22%20viewBox%3D%220%200%2020%2020%22%3E%3Cpath%20stroke%3D%22%236b7280%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20stroke-width%3D%221.5%22%20d%3D%22m6%208%204%204%204-4%22%2F%3E%3C%2Fsvg%3E')] bg-[position:right_0.5rem_center] bg-[length:1.5em_1.5em] bg-no-repeat"
      >
        {#each Object.keys(REWARD_GROUPS) as group}
          <option value={group}>{group}</option>
        {/each}
      </select>

      <!-- Reward Type Selection -->
      <select
        bind:value={selectedRewardType}
        class="block w-full text-sm rounded-md border-0 py-2 pl-3 pr-12 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-blue-600 bg-white shadow-sm appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20fill%3D%22none%22%20viewBox%3D%220%200%2020%2020%22%3E%3Cpath%20stroke%3D%22%236b7280%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20stroke-width%3D%221.5%22%20d%3D%22m6%208%204%204%204-4%22%2F%3E%3C%2Fsvg%3E')] bg-[position:right_0.5rem_center] bg-[length:1.5em_1.5em] bg-no-repeat"
      >
        {#each REWARD_GROUPS[selectedGroup] as type}
          <option value={type}>{type}</option>
        {/each}
      </select>

      <ParameterGroup>
        {#each Object.entries(REWARD_TYPES[selectedRewardType]) as [param, config]}
          <ParameterControl
            name={param}
            label={param}
            type={config.type}
            min={config.min}
            max={config.max}
            step={config.step}
            options={config.options?.map(opt => ({ value: opt, label: opt }))}
            value={activeParameters[param]}
            on:change={({ detail }) => handleParameterChange(detail.name, detail.value)}
          />
        {/each}
      </ParameterGroup>

      <div class="mt-2">
        <div class="flex justify-between items-center mb-2">
          <h3 class="text-sm font-semibold">Favorites</h3>
          <button
            on:click={saveAsFavorite}
            class="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded"
          >
            Save Current
          </button>
        </div>
        <!--
        {#if Object.keys(favorites).length > 0}
          <div class="space-y-1 max-h-32 overflow-y-auto">
            {#each Object.entries(favorites) as [name, _]}
              <div
                class="flex items-center justify-between bg-gray-50 px-2 py-1 rounded text-sm cursor-pointer hover:bg-gray-100"
                on:click={() => favoriteStore.loadFavorite(name)}
              >
                <span>{name}</span>
                <button
                  class="text-red-500 hover:text-red-700"
                  on:click={(e) => deleteFavorite(name, e)}
                >
                  ×
                </button>
              </div>
            {/each}
          </div>
        {:else}
          <div class="text-sm text-gray-500 italic">No favorites saved</div>
        {/if}
    -->
      </div>
     

      <button
        on:click={addReward}
        class="w-full bg-blue-600 text-white px-3 py-1 text-sm rounded hover:bg-blue-700"
      >
        Add Reward
      </button>
    </div>
  </div>

  <!-- Add active rewards list with IDs -->
  {#if $rewardStore.activeRewards.length > 0}
    <div class="mt-4 bg-white rounded-lg shadow-lg p-4">
      <h2 class="text-lg font-bold mb-4 text-gray-800">Active Rewards</h2>
      <div class="space-y-2">
        {#each $rewardStore.activeRewards as reward, index}
          <div class="flex items-center gap-3 bg-gray-50 p-3 rounded-md hover:bg-gray-100 transition-colors">
            <span class="text-xs text-gray-500 font-mono">{reward.id.slice(0,8)}</span>
            <span class="flex-grow font-medium text-gray-700">{reward.name}</span>
            <input
              type="number"
              class="w-24 text-sm rounded-md border-0 py-1.5 px-2 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-blue-600 bg-white shadow-sm"
              value={displayWeights[index]}
              on:input={(e) => handleWeightChange(index, e.target.value)}
            />
            <button
              class="text-red-500 hover:text-red-700 p-1 rounded-full hover:bg-red-50 transition-colors"
              on:click={() => rewardStore.removeReward(reward.id)}
            >
              ×
            </button>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div> 