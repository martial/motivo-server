<script>
  import { createEventDispatcher } from 'svelte';
  import { REWARD_TYPES } from '../stores/rewardStore';
  const dispatch = createEventDispatcher();

  export let name;
  export let label;
  export let type = 'range';  // 'range', 'select', or 'checkbox'
  export let min = 0;
  export let max = 100;
  export let step = 1;
  export let options = undefined;
  export let value;
  export let defaultValue = undefined;

  //console.log("Type is ", type);

  // Instead, use the parameter definitions from REWARD_TYPES
  $: if (name && REWARD_TYPES[name]) {
    const paramConfig = REWARD_TYPES[name][label];
    if (paramConfig) {
      type = paramConfig.type;
      if (type === 'range') {
        min = paramConfig.min;
        max = paramConfig.max;
        step = paramConfig.step;
      } else if (type === 'select') {
        options = paramConfig.options.map(opt => ({ value: opt, label: opt }));
      }
      if (defaultValue === undefined) {
        defaultValue = paramConfig.default;
      }
    }
  }

  // Initialize value with default if not set
  $: if (value === undefined && defaultValue !== undefined) {
    value = defaultValue;
  }

  function handleInput(event) {
    let newValue;
    if (type === 'select') {
      newValue = event.target.value === '' ? null : event.target.value;
    } else if (type === 'range') {
      newValue = parseFloat(event.target.value);
      value = newValue;
    } else if (type === 'checkbox') {
      newValue = event.target.checked;
      value = newValue;
    }
    
    if (newValue !== undefined) {
      console.log(`ParameterControl ${name} value changed to:`, newValue);
      dispatch('change', {
        name,
        value: newValue
      });
    }
  }
</script>

<div class="mb-6">
  {#if name === 'move-ego'}
    <h2 class="text-2xl font-medium bg-gradient-to-r from-blue-600 to-blue-400 bg-clip-text text-transparent mb-4 font-display tracking-wide">
      {name}
    </h2>
  {:else}
    <div class="flex justify-between items-center mb-1.5">
      <label class="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {label}
      </label>
      {#if type !== 'checkbox'}
        <span class="text-xs font-medium text-gray-900 tabular-nums">
          {value?.toFixed?.(2) ?? value}
        </span>
      {/if}
    </div>
  {/if}
  
  <div class="w-full">
    {#if type === 'range'}
      <input 
        type="range"
        {value}
        {min}
        {max}
        {step}
        on:input={handleInput}
        class="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
      />
    {:else if type === 'select'}
      <select 
        {value}
        on:change={handleInput}
        class="block w-full text-xs rounded-md border-0 py-1.5 pl-2 pr-8 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-blue-600 bg-white shadow-sm appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20fill%3D%22none%22%20viewBox%3D%220%200%2020%2020%22%3E%3Cpath%20stroke%3D%22%236b7280%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20stroke-width%3D%221.5%22%20d%3D%22m6%208%204%204%204-4%22%2F%3E%3C%2Fsvg%3E')] bg-[position:right_0.5rem_center] bg-[length:1em_1em] bg-no-repeat"
      >
        {#each options as option}
          <option value={option.value} selected={value === option.value}>
            {option.label}
          </option>
        {/each}
      </select>
    {:else if type === 'checkbox'}
      <label class="relative inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={value}
          on:change={handleInput}
          class="sr-only peer"
        />
        <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
      </label>
    {/if}
  </div>
</div> 