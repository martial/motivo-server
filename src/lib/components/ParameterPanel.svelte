<script>
  import { parameterStore } from '../stores/parameterStore';
  import ParameterControl from './ParameterControl.svelte';
  import ParameterGroup from './ParameterGroup.svelte';

  // Subscribe to the store values
  $: parameters = $parameterStore;

  function handleParameterChange(event) {
    const { name, value } = event.detail;
    parameterStore.updateParameter(name, value);
  }
</script>

<div class="w-96 py-4">
  <div class="bg-white rounded-lg shadow-lg p-4">
    <h1 class="text-lg font-bold mb-4 text-gray-800">Environment Parameters</h1>
    
    <div class="space-y-3">
      <!-- Basic Parameters -->
      <ParameterGroup columns={2}>
        <ParameterControl
          name="gravity"
          label="Gravity"
          type="range"
          min={-30}
          max={0}
          step={0.1}
          value={parameters.gravity}
          defaultValue={-9.81}
          on:change={handleParameterChange}
        />
        <ParameterControl
          name="density"
          label="Density"
          type="range"
          min={0}
          max={5}
          step={0.1}
          value={parameters.density}
          defaultValue={1.0}
          on:change={handleParameterChange}
        />
      </ParameterGroup>

      <!-- Wind Controls -->
      <ParameterGroup title="Wind Controls" columns={3}>
        {#each ['x', 'y', 'z'] as axis}
          <ParameterControl
            name={`wind_${axis}`}
            label={axis.toUpperCase()}
            type="range"
            min={-10}
            max={100}
            step={0.1}
            value={parameters[`wind_${axis}`]}
            defaultValue={0}
            on:change={handleParameterChange}
          />
        {/each}
      </ParameterGroup>

      <!-- Additional Parameters -->
      <ParameterGroup columns={2}>
        <ParameterControl
          name="viscosity"
          label="Viscosity"
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={parameters.viscosity}
          defaultValue={0.1}
          on:change={handleParameterChange}
        />
        <ParameterControl
          name="timestep"
          label="Timestep"
          type="range"
          min={0.0001}
          max={0.002}
          step={0.0001}
          value={Number(parameters.timestep).toFixed(4)}
          defaultValue={0.0005}
          on:change={handleParameterChange}
        />
      </ParameterGroup>


      <button 
        on:click={() => parameterStore.reset()}
        class="w-full bg-gray-600 text-white px-3 py-1 text-sm rounded hover:bg-gray-700 transition-colors"
      >
        Reset to Defaults
      </button>
    </div>
  </div>
</div> 