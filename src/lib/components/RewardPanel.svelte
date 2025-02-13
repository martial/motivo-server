<script>
  import { REWARD_TYPES } from '../stores/rewardStore';
  import { websocketService } from '../services/websocketService';
  import ParameterControl from './ParameterControl.svelte';
  import ParameterGroup from './ParameterGroup.svelte';
  import { v4 as uuidv4 } from 'uuid';
  import { onMount, onDestroy } from 'svelte';

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
    ],
    'Behavior Rewards': [
      'standing', 'upright', 'movement-control', 'small-control',
      'position', 'balance', 'symmetry', 'energy-efficiency',
      'natural-motion', 'gaze-direction', 'ground-contact',
      'stable-standing', 'natural-walking'
    ]
  };

  let selectedGroup = $state(Object.keys(REWARD_GROUPS)[0]);
  let selectedRewardType = $state(REWARD_GROUPS[selectedGroup][0]);
  let activeParameters = $state(initializeParameters(selectedRewardType));
  let activeRewards = $state(null);
  let cleanupHandler;

  function initializeParameters(rewardType) {
    const params = {};
    Object.entries(REWARD_TYPES[rewardType]).forEach(([key, config]) => {
      params[key] = config.default;
    });
    return params;
  }

  $effect(() => {
    // Update reward type when group changes
    if (!REWARD_GROUPS[selectedGroup].includes(selectedRewardType)) {
      selectedRewardType = REWARD_GROUPS[selectedGroup][0];
    }
  });

  $effect(() => {
    // Reset parameters when reward type changes
    activeParameters = initializeParameters(selectedRewardType);
  });

  onMount(() => {
    cleanupHandler = websocketService.addMessageHandler((data) => {
      if (data.type === 'debug_model_info') {
        activeRewards = data.active_rewards;
      }
    });
  });

  onDestroy(() => {
    if (cleanupHandler) cleanupHandler();
  });

  function handleParameterChange(param, value) {
    activeParameters = {
      ...activeParameters,
      [param]: value
    };
  }

  function addReward() {
    const rewardId = uuidv4();
    const newReward = {
      id: rewardId,
      name: selectedRewardType,
      ...activeParameters
    };

    // Create new rewards array, properly handling the case when activeRewards exists
    const updatedRewards = {
      rewards: activeRewards?.rewards ? [...activeRewards.rewards, newReward] : [newReward],
      weights: activeRewards?.weights ? [...activeRewards.weights, 1.0] : [1.0],
      combinationType: activeRewards?.combinationType || 'geometric'
    };

    // Send combined rewards through websocket
    websocketService.getSocket()?.send(JSON.stringify({
      type: 'request_reward',
      reward: updatedRewards,
      timestamp: new Date().toISOString()
    }));

    // Request updated state after adding reward
    websocketService.getSocket()?.send(JSON.stringify({
      type: "debug_model_info"
    }));
  }
</script>

<div class="w-96 ">
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

      <button
        on:click={addReward}
        class="w-full bg-blue-600 text-white px-3 py-1 text-sm rounded hover:bg-blue-700"
      >
        Add Reward
      </button>
    </div>
  </div>
</div> 