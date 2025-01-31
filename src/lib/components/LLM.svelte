<script>
  import { websocketService } from '../services/websocketService';
  import { onMount, onDestroy } from 'svelte';
  import { v4 as uuidv4 } from 'uuid';
  import { rewardStore } from '../stores/rewardStore';

  const API_URL = import.meta.env.VITE_API_URL;

  let prompt = $state('');
  let isProcessing = $state(false);
  let sessionId = $state(null);
  let response = $state('');
  let cleanupHandler;
  let conversation = $state([]);
  let showJson = $state(false);

  onMount(() => {
    // Generate a session ID when component mounts
    sessionId = uuidv4();
    
    cleanupHandler = websocketService.addMessageHandler((data) => {
      if (data.type === 'llm_response') {
        isProcessing = false;
      }
    });
  });

  onDestroy(() => {
    if (cleanupHandler) cleanupHandler();
  });

  async function handleSubmit() {
    if (!prompt.trim()) return;
    
    isProcessing = true;
    
    try {
      const res = await fetch(`${API_URL}/generate-reward`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          sessionId
        })
      });

      const data = await res.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      sessionId = data.sessionId;
      response = data.reward_config;
      conversation = data.conversation;

      // If the response contains valid reward configuration,
      // send it through websocket for real-time behavior update
      try {
        const rewardConfig = JSON.parse(data.reward_config);
        
        // Use rewardStore to properly handle the reward configuration
        if (rewardConfig.rewards && Array.isArray(rewardConfig.rewards)) {
          // Clean existing rewards first
          rewardStore.cleanRewards();
          
          // Add each reward from the configuration
          rewardConfig.rewards.forEach((reward, index) => {
            rewardStore.addReward(reward.name, {
              id: reward.id || uuidv4(),
              name: reward.name,
              ...reward
            });
            
            // Update weight if specified
            if (rewardConfig.weights?.[index] !== undefined) {
              rewardStore.updateWeight(index, rewardConfig.weights[index]);
            }
          });
        } else {
          console.log('Invalid reward configuration format');
        }
      } catch (e) {
        console.log('Error processing reward configuration:', e);
      }

    } catch (error) {
      console.error('Error:', error);
      response = `Error: ${error.message}`;
    } finally {
      isProcessing = false;
    }
  }
</script>

<div class="flex gap-4">
  <div class="w-96">
    <div class="bg-white rounded-lg shadow-lg p-4">
      <h1 class="text-lg font-bold mb-4 text-gray-800">Natural Language Control</h1>
      
      <div class="space-y-3">
        <div class="space-y-2">
          <label for="prompt" class="block text-sm font-medium text-gray-700">
            Behavior Description
          </label>
          <textarea
            id="prompt"
            bind:value={prompt}
            rows="4"
            placeholder="Describe the desired behavior (e.g., 'Walk forward while waving both hands')"
            class="block w-full rounded-md border-0 py-2 px-3 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-blue-600 resize-none"
          ></textarea>
        </div>

        <button
          on:click={handleSubmit}
          disabled={isProcessing}
          class="w-full bg-blue-600 text-white px-3 py-1 text-sm rounded hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {#if isProcessing}
            <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Processing...
          {:else}
            Generate Behavior
          {/if}
        </button>

        {#if response}
          <div class="mt-4">
            <h2 class="text-sm font-medium text-gray-700 mb-2">Response:</h2>
            <div class="bg-gray-50 rounded-md p-3 text-sm text-gray-600 whitespace-pre-wrap">
              {response}
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Conversation History -->
  <div class="w-96">
    <div class="bg-white rounded-lg shadow-lg p-4">
      <h2 class="text-lg font-bold mb-4 text-gray-800">Conversation History</h2>
      <div class="space-y-4 max-h-[500px] overflow-y-auto">
        {#each conversation as message}
          <div class="flex flex-col gap-1">
            <div class="text-sm font-medium text-gray-600">
              {message.role === 'user' ? 'You' : 'Assistant'}:
            </div>
            {#if message.role === 'user'}
              <div class="bg-gray-50 rounded-md p-3 text-sm text-gray-600 whitespace-pre-wrap">
                {message.content}
              </div>
            {:else}
              <div class="space-y-2">
                <button
                  on:click={() => showJson = !showJson}
                  class="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
                >
                  {showJson ? 'Hide' : 'Show'} JSON
                  <svg
                    class="w-4 h-4 transform transition-transform {showJson ? 'rotate-180' : ''}"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {#if showJson}
                  <div class="bg-gray-50 rounded-md p-3 text-sm text-gray-600 font-mono whitespace-pre-wrap">
                    {message.content}
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  </div>
</div> 