<script>
  import { websocketService } from '../services/websocketService';
  import { onMount, onDestroy } from 'svelte';
  import { v4 as uuidv4 } from 'uuid';
  import { rewardStore } from '../stores/rewardStore';
  import { chatStore } from '../stores/chatStore';

  const API_URL = import.meta.env.VITE_API_URL;

  let prompt = $state('');
  let isProcessing = $state(false);
  let chatContainer;
  let showJson = $state(false);
  let cleanupHandler;

  onMount(() => {
    // Only generate a session ID if one doesn't exist
    if (!$chatStore.sessionId) {
      chatStore.update(store => ({
        ...store,
        sessionId: uuidv4()
      }));
    }
    
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
    const currentPrompt = prompt.trim();
    prompt = '';
    
    try {
      const res = await fetch(`${API_URL}/generate-reward`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: currentPrompt,
          sessionId: $chatStore.sessionId
        })
      });

      const data = await res.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      // Update store with new data
      chatStore.update(store => ({
        ...store,
        sessionId: data.sessionId,
        response: data.reward_config,
        conversation: data.conversation
      }));

      // If the response contains valid reward configuration,
      // send it through websocket for real-time behavior update
      try {
        const rewardConfig = JSON.parse(data.reward_config);
        
        if (rewardConfig.rewards && Array.isArray(rewardConfig.rewards)) {
          // First, tell backend to clear active rewards
          const ws = websocketService.getSocket();
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
              type: "clear_active_rewards"
            }));
          }
          
          // Then clean store locally (without sending another WS message)
          rewardStore.cleanRewardsLocal();
          
          // Then add the new rewards
          rewardConfig.rewards.forEach((reward, index) => {
            rewardStore.addReward(reward.name, {
              id: reward.id || uuidv4(),
              name: reward.name,
              ...reward
            });
            
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

      // After updating conversation, scroll to bottom
      setTimeout(() => {
        chatContainer?.scrollTo({
          top: chatContainer.scrollHeight,
          behavior: 'smooth'
        });
      }, 100);

    } catch (error) {
      console.error('Error:', error);
      chatStore.update(store => ({
        ...store,
        response: `Error: ${error.message}`
      }));
    } finally {
      isProcessing = false;
    }
  }

  function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  }

  async function clearChat() {
    try {
      const res = await fetch(`${API_URL}/clear-chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ sessionId: $chatStore.sessionId })
      });

      if (!res.ok) throw new Error('Failed to clear chat');
      
      // Clear store
      chatStore.update(store => ({
        ...store,
        conversation: [],
        response: ''
      }));
      
    } catch (error) {
      console.error('Error clearing chat:', error);
    }
  }
</script>

<div class="flex flex-col h-[600px]">
  <!-- Added clear button -->
  <div class="flex justify-end p-2  border-b">
    <button
      on:click={clearChat}
      class="text-sm px-3 py-1 text-gray-600 hover:text-gray-800 flex items-center gap-1 rounded hover:bg-gray-200"
    >
      <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
      </svg>
      Clear Chat
    </button>
  </div>

  <!-- Chat messages container - fixed height with overflow -->
  <div 
    bind:this={chatContainer}
    class="flex-1 overflow-y-auto p-4 space-y-4"
  >
    {#each $chatStore.conversation as message}
      <div class="flex gap-2 {message.role === 'assistant' ? 'bg-gray-50' : ''} p-4 rounded-lg">
        <!-- Avatar/Icon -->
        <div class="w-8 h-8 rounded-full flex items-center justify-center shrink-0 
                    {message.role === 'assistant' ? 'bg-blue-600' : 'bg-gray-600'}">
          {#if message.role === 'assistant'}
            <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          {:else}
            <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          {/if}
        </div>

        <!-- Message content -->
        <div class="flex-1 space-y-2">
          <div class="font-medium text-sm text-gray-600">
            {message.role === 'user' ? 'You' : 'Motivo'}
          </div>
          {#if message.role === 'user'}
            <div class="text-gray-800">
              {message.content}
            </div>
          {:else}
            <div class="space-y-2">
              <div class="text-gray-800">
                Generated behavior configuration:
              </div>
              <div class="bg-gray-100 rounded p-3 font-mono text-sm">
                {message.content}
              </div>
            </div>
          {/if}
        </div>
      </div>
    {/each}
  </div>

  <!-- Input area - fixed at bottom -->
  <div class="border-t p-4">
    <div class="max-w-4xl mx-auto">
      <form 
        on:submit|preventDefault={handleSubmit}
        class="flex gap-4 items-end"
      >
        <div class="flex-1">
          <textarea
            id="prompt"
            bind:value={prompt}
            rows="3"
            on:keydown={handleKeydown}
            placeholder="Describe the desired behavior (e.g., 'Walk forward while waving both hands')"
            class="block w-full rounded-lg border-0 py-2 px-3 text-gray-900 bg-white ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-blue-600 resize-none shadow-lg"
          ></textarea>
        </div>
        
        <button
          type="submit"
          disabled={isProcessing}
          class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed flex items-center gap-2 h-[42px] shadow-lg"
        >
          {#if isProcessing}
            <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          {:else}
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          {/if}
        </button>
      </form>
    </div>
  </div>
</div> 