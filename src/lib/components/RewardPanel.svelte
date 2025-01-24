<script>
  import { rewardStore, REWARD_TYPES, COMBINATION_TYPES } from '../stores/rewardStore';
  import ParameterControl from './ParameterControl.svelte';
  import ParameterGroup from './ParameterGroup.svelte';

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

  function initializeParameters(rewardType) {
    console.log('=== Initializing Parameters ===');
    console.log('Reward Type:', rewardType);
    // Initialize all parameters from REWARD_TYPES
    const params = {};
    Object.entries(REWARD_TYPES[rewardType]).forEach(([key, config]) => {
      params[key] = config.default;
      console.log(`Setting ${key} to default:`, config.default);
    });
    console.log('Initialized params:', params);
    return params;
  }

  $: {
    console.log('=== Reactive Update ===');
    console.log('Selected reward type changed to:', selectedRewardType);
    if (previousRewardType !== selectedRewardType) {
      console.log('Reward type changed, initializing new parameters');
      activeParameters = initializeParameters(selectedRewardType);
      previousRewardType = selectedRewardType;
    } else {
      console.log('Same reward type, keeping current parameters');
    }
  }

  function handleParameterChange(param, value) {
    console.log('=== Parameter Change ===');
    console.log(`Changing ${param} from ${activeParameters[param]} to ${value}`);
    // Create a new object with all existing parameters plus the updated one
    activeParameters = {
      ...activeParameters,  // Keep all existing parameters
      [param]: value       // Update the changed parameter
    };
    console.log('Updated activeParameters:', activeParameters);
  }

  function addReward() {
    console.log('=== Adding Reward ===');
    console.log('Current activeParameters:', activeParameters);
    const rewardParams = {
      name: selectedRewardType,
      ...activeParameters  // Spread all parameters
    };
    console.log('Final reward params to be sent:', rewardParams);
    rewardStore.addReward(selectedRewardType, rewardParams);
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
  const debouncedUpdateWeight = debounce((index, value) => {
    rewardStore.updateWeight(index, value);
  }, 300);

  // Update the weight handling function to ensure numeric values
  function handleWeightChange(index, value) {
    const numericValue = Number(value) || 0;
    displayWeights[index] = numericValue;
    displayWeights = [...displayWeights]; // Trigger reactivity
    debouncedUpdateWeight(index, numericValue);
  }
</script>

<div class="w-96 py-4">
  <div class="bg-white rounded-lg shadow-lg p-4">
    <h1 class="text-lg font-bold mb-4 text-gray-800">Reward Controls</h1>
    
    <!-- Active Rewards -->
    {#if $rewardStore.activeRewards.length > 0}
      <div class="mb-4">
        <h2 class="text-sm font-semibold mb-2">Active Rewards</h2>
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
          bind:value={$rewardStore.combinationType}
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
    {/if}

    <!-- Add New Reward -->
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
            on:change={({ detail }) => {
              console.log(`=== ParameterControl Change Event ===`);
              console.log(`Parameter: ${detail.name}`);
              console.log(`Old value:`, activeParameters[param]);
              console.log(`New value:`, detail.value);
              handleParameterChange(detail.name, detail.value);
            }}
          />
        {/each}
      </ParameterGroup>

      <button
        on:click={addReward}
        class="w-full bg-blue-600 text-white px-3 py-1 text-sm rounded hover:bg-blue-700"
      >
        Add Reward
      </button>
    </div>
  </div>
</div> 