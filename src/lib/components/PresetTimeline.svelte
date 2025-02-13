<script>
    import { onMount } from 'svelte';
    import { websocketService } from '../services/websocketService';
    
    let duration = 30; // Default duration in seconds
    let isPlaying = false;
    let timelineRef;
    let currentTime = 0;
    let animationFrame;
    let startTime;
    
    // Array to store placed presets
    let placedPresets = [];

    // Add variable to track dragging state
    let isDraggingPreset = null;
    let isDraggingPlayhead = false;
    
    // Handle duration change
    function handleDurationChange(event) {
      duration = parseInt(event.target.value);
      // Validate existing preset positions against new duration
      placedPresets = placedPresets.filter(preset => preset.position <= duration);
    }
    
    // Handle drag over
    function handleDragOver(event) {
      event.preventDefault();
      event.dataTransfer.dropEffect = 'copy';
    }

    // Handle preset dragging
    function handlePresetDragStart(event, preset) {
      isDraggingPreset = preset;
      event.dataTransfer.setData('preset_move', 'true');
    }
    
    // Handle drop for both new presets and moving existing ones
    function handleDrop(event) {
      event.preventDefault();
      const timelineRect = timelineRef.getBoundingClientRect();
      const dropX = event.clientX - timelineRect.left;
      const position = Math.min(Math.max(0, (dropX / timelineRect.width) * duration), duration);

      if (isDraggingPreset) {
        // Move existing preset
        placedPresets = placedPresets
          .map(p => p === isDraggingPreset ? { ...p, position } : p)
          .sort((a, b) => a.position - b.position);
        isDraggingPreset = null;
      } else {
        // Add new preset
        const preset = JSON.parse(event.dataTransfer.getData('preset'));
        placedPresets = [...placedPresets, {
          ...preset,
          position
        }].sort((a, b) => a.position - b.position);
      }
    }

    // Handle timeline click to move playhead
    function handleTimelineClick(event) {
      if (!isDraggingPreset && !isDraggingPlayhead) {
        const timelineRect = timelineRef.getBoundingClientRect();
        const clickX = event.clientX - timelineRect.left;
        currentTime = (clickX / timelineRect.width) * duration;
        if (isPlaying) {
          startTime = Date.now() - (currentTime * 1000);
        }
      }
    }

    // Move to next/previous preset
    function moveToNextPreset() {
      const nextPreset = placedPresets.find(preset => preset.position > currentTime);
      if (nextPreset) {
        currentTime = nextPreset.position;
        if (isPlaying) {
          startTime = Date.now() - (currentTime * 1000);
        }
      }
    }

    function moveToPreviousPreset() {
      const previousPreset = [...placedPresets]
        .reverse()
        .find(preset => preset.position < currentTime);
      if (previousPreset) {
        currentTime = previousPreset.position;
        if (isPlaying) {
          startTime = Date.now() - (currentTime * 1000);
        }
      }
    }
    
    // Handle play/pause
    function togglePlayback() {
      isPlaying = !isPlaying;
      
      if (isPlaying) {
        startTime = Date.now() - (currentTime * 1000);
        playTimeline();
      } else {
        cancelAnimationFrame(animationFrame);
      }
    }
    
    // Timeline playback logic
    function playTimeline() {
      currentTime = (Date.now() - startTime) / 1000;
      
      // Check for presets that need to be activated
      placedPresets.forEach(preset => {
        if (currentTime >= preset.position && preset.position > (currentTime - 0.1)) {
          activatePreset(preset);
        }
      });
      
      if (currentTime >= duration) {
        currentTime = 0;
        startTime = Date.now();
      }
      
      if (isPlaying) {
        animationFrame = requestAnimationFrame(playTimeline);
      }
    }
    
    // Activate preset via websocket
    async function activatePreset(preset) {
      try {
        if (preset.data?.environmentParams) {
          await websocketService.send({
            type: "update_environment",
            params: preset.data.environmentParams
          });
        }
        
        if (preset.type === 'rewards' && preset.data?.rewards) {
          await websocketService.send({
            type: "request_reward",
            reward: {
              rewards: preset.data.rewards,
              weights: preset.data.weights,
              combinationType: preset.data.combinationType
            },
            timestamp: new Date().toISOString()
          });
        }
      } catch (error) {
        console.error('Failed to activate preset:', error);
      }
    }
    
    // Cleanup on component destroy
    onMount(() => {
      return () => {
        if (animationFrame) {
          cancelAnimationFrame(animationFrame);
        }
      };
    });
</script>
  
<div class="w-full bg-white rounded-lg shadow-lg p-4 mb-8">
    <div class="flex items-center gap-4 mb-4">
      <!-- Previous button -->
      <button 
        class="bg-gray-500 text-white px-4 py-2 rounded-md hover:bg-gray-600"
        on:click={moveToPreviousPreset}
      >
        ⏮️ Previous
      </button>

      <!-- Play/pause button -->
      <button 
        class="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600"
        on:click={togglePlayback}
      >
        {isPlaying ? '⏸️ Pause' : '▶️ Play'}
      </button>

      <!-- Next button -->
      <button 
        class="bg-gray-500 text-white px-4 py-2 rounded-md hover:bg-gray-600"
        on:click={moveToNextPreset}
      >
        ⏭️ Next
      </button>
      
      <div class="flex items-center gap-2">
        <input 
          type="range" 
          min="5" 
          max="60" 
          step="5" 
          bind:value={duration}
          on:input={handleDurationChange}
          class="w-48"
        />
        <span class="text-sm text-gray-600">{duration}s</span>
      </div>
    </div>
  
    <div 
      bind:this={timelineRef}
      class="relative w-full h-24 bg-gray-100 rounded-md cursor-pointer"
      on:dragover={handleDragOver}
      on:drop={handleDrop}
      on:click={handleTimelineClick}
    >
      <!-- Timeline markers -->
      {#each Array(duration + 1) as _, i}
        <div 
          class="absolute h-2 w-px bg-gray-300" 
          style="left: {(i / duration) * 100}%"
        ></div>
      {/each}
      
      <!-- Playhead -->
      <div 
        class="absolute top-0 w-px h-full bg-red-500"
        style="left: {(currentTime / duration) * 100}%"
      ></div>
      
      <!-- Placed presets -->
      {#each placedPresets as preset}
        <div 
          class="absolute top-4 transform -translate-x-1/2 cursor-move"
          style="left: {(preset.position / duration) * 100}%"
          draggable="true"
          on:dragstart={(e) => handlePresetDragStart(e, preset)}
        >
          {#if preset.thumbnail}
            <video 
              src={`data:video/webm;base64,${preset.thumbnail}`}
              class="w-16 h-12 rounded border-2 border-blue-500"
              autoplay
              loop
              muted
            ></video>
          {/if}
        </div>
      {/each}
    </div>
</div>
  
<style>
    input[type="range"] {
      -webkit-appearance: none;
      height: 4px;
      background: #e2e8f0;
      border-radius: 2px;
    }
  
    input[type="range"]::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 16px;
      height: 16px;
      background: #3b82f6;
      border-radius: 50%;
      cursor: pointer;
    }
</style>