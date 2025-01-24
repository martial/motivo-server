<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  export let name;
  export let label;
  export let type = 'range';  // Now supports 'range', 'select', and 'checkbox'
  export let min = 0;
  export let max = 100;
  export let step = 1;
  export let options = undefined;
  export let value; // Accept value from parent
  export let defaultValue = undefined; // Add default value prop

  function handleInput(event) {
    let newValue;
    if (type === 'select') {
      newValue = event.target.value === '' ? null : event.target.value;
    } else if (type === 'range') {
      newValue = parseFloat(event.target.value);
      // Update the bound value immediately for range inputs
      value = newValue;
    } else if (type === 'checkbox') {
      newValue = event.target.checked;
      value = newValue;
    }
    
    if (newValue !== undefined) {
      console.log(`ParameterControl ${name} value changed to:`, newValue);
      // Dispatch both name and value
      dispatch('change', {
        name,
        value: newValue
      });
    }
  }
</script>

<div class="space-y-4 px-4">
  <div class="flex justify-between items-center">
    <label class="text-sm font-medium text-gray-700">
      {label}
    </label>
    {#if type !== 'checkbox'}
      <span class="text-sm font-medium text-gray-600">
        {value}
      </span>
    {/if}
  </div>
  
  {#if type === 'range'}
    <div class="px-1">
      <input 
        {type}
        {value}
        {min}
        {max}
        {step}
        on:input={handleInput}
        class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
      />
    </div>
  {:else if type === 'select'}
    <select 
      {value}
      on:change={handleInput}
      class="block w-full text-sm rounded-md border-0 py-2 pl-3 pr-12 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-blue-600 bg-white shadow-sm appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20fill%3D%22none%22%20viewBox%3D%220%200%2020%2020%22%3E%3Cpath%20stroke%3D%22%236b7280%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20stroke-width%3D%221.5%22%20d%3D%22m6%208%204%204%204-4%22%2F%3E%3C%2Fsvg%3E')] bg-[position:right_0.5rem_center] bg-[length:1.5em_1.5em] bg-no-repeat"
    >
      {#each options as option}
        <option value={option.value} selected={value === option.value}>
          {option.label}
        </option>
      {/each}
    </select>
  {:else if type === 'checkbox'}
    <label class="relative flex items-center cursor-pointer">
      <input
        type="checkbox"
        checked={value}
        on:change={handleInput}
        class="sr-only peer"
      />
      <div class="w-12 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
    </label>
  {/if}
</div> 