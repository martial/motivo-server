<script>
  import { favoriteStore } from '../stores/favoriteStore';

  function formatRewardName(reward) {
    return `${reward.name} (${(reward.weight * 100).toFixed(0)}%)`;
  }

  function formatParameters(reward) {
    // Filter out name and weight as they're shown separately
    const params = Object.entries(reward)
      .filter(([key]) => key !== 'name' && key !== 'weight')
      .map(([key, value]) => {
        if (typeof value === 'boolean') {
          return `${key}=${value ? 'true' : 'false'}`;
        }
        if (typeof value === 'number') {
          return `${key}=${value.toFixed(2)}`;
        }
        return `${key}=${value}`;
      });
    return params.join(' | ');
  }

  async function shareConfig(name) {
    const serialized = favoriteStore.serializeConfig(name);
    if (serialized) {
      try {
        await navigator.clipboard.writeText(serialized);
        alert('Configuration copied to clipboard!');
      } catch (err) {
        console.error('Failed to copy:', err);
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = serialized;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        alert('Configuration copied to clipboard!');
      }
    }
  }

  async function importConfig() {
    const serialized = prompt('Paste the configuration string:');
    if (serialized) {
      const name = prompt('Enter a name for this configuration:');
      if (name) {
        if (favoriteStore.importConfig(name, serialized)) {
          alert('Configuration imported successfully!');
        } else {
          alert('Invalid configuration string');
        }
      }
    }
  }
</script>

<div class="bg-white rounded-lg shadow-lg p-4 mt-8">
  <div class="flex justify-between items-center mb-4">
    <h2 class="text-lg font-bold text-gray-800">Saved Configurations</h2>
    <div class="flex gap-2">
      <button
        on:click={importConfig}
        class="text-sm px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
      >
        Import
      </button>
      <span class="text-sm text-gray-500">
        {Object.keys($favoriteStore).length} configurations
      </span>
    </div>
  </div>
  
  <div class="grid grid-cols-3 gap-4">
    {#each Object.entries($favoriteStore) as [name, favorite]}
      <div class="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
        <div class="flex justify-between items-start mb-2">
          <h3 class="font-semibold text-gray-800">{name}</h3>
          <span class="text-sm px-2 py-0.5 bg-gray-200 rounded-full text-gray-700">
            {favorite.combinationType}
          </span>
        </div>
        
        <div class="text-sm text-gray-600">
          <div class="mb-2">
            <ul class="space-y-2">
              {#each favorite.activeRewards as reward}
                <li class="bg-white rounded p-2 shadow-sm">
                  <div class="font-medium text-gray-700">
                    {formatRewardName(reward)}
                  </div>
                  <div class="text-xs font-mono text-gray-500 mt-1 break-all">
                    {formatParameters(reward)}
                  </div>
                </li>
              {/each}
            </ul>
          </div>
        </div>
        
        <div class="flex gap-2 mt-4">
          <button
            class="flex-1 text-xs bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded-md transition-colors"
            on:click={() => favoriteStore.loadFavorite(name)}
          >
            Load
          </button>
          <button
            class="text-xs bg-green-500 hover:bg-green-600 text-white px-3 py-1.5 rounded-md transition-colors"
            on:click={() => shareConfig(name)}
          >
            Share
          </button>
          <button
            class="text-xs bg-red-500 hover:bg-red-600 text-white px-3 py-1.5 rounded-md transition-colors"
            on:click={() => favoriteStore.deleteFavorite(name)}
          >
            Delete
          </button>
        </div>
      </div>
    {/each}
    
    {#if Object.keys($favoriteStore).length === 0}
      <div class="col-span-3 text-center text-gray-500 italic py-8">
        No saved configurations yet. Create one by clicking "Save Current" in the Reward Panel.
      </div>
    {/if}
  </div>
</div> 