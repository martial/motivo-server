<script>
  import { onMount, onDestroy } from 'svelte';
  import { fade } from 'svelte/transition';
  import { DbService } from '../services/db';
  import { websocketService } from '../services/websocketService';
  import { parameterStore } from '../stores/parameterStore';
  import PresetTimeline from './PresetTimeline.svelte';

  let presets = [];
  let selectedType = 'all';
  let isLoading = true;
  let isSaving = false;
  let thumbnail = null;
  let videoBuffer;
  let saveError = '';
  let loadError = '';
  
  const apiUrl = import.meta.env.VITE_API_URL;

  class VideoBuffer {
    constructor() {
      this.mediaRecorder = null;
      this.recordedChunks = [];
      this.canvas = document.createElement('canvas');
      this.ctx = this.canvas.getContext('2d');
      this.stream = null;
    }

    async initializeBuffer(width = 320, height = 240) {
      this.canvas.width = width;
      this.canvas.height = height;
      
      this.stream = this.canvas.captureStream(30);
      
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: 'video/webm;codecs=vp9',
        videoBitsPerSecond: 2500000
      });

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.recordedChunks.push(event.data);
        }
      };
    }

    updateFrame(imageUrl) {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
      };
      img.src = imageUrl;
    }

    startRecording() {
      this.recordedChunks = [];
      this.mediaRecorder.start();
      
      setTimeout(() => {
        this.mediaRecorder.stop();
      }, 2000);
    }

    async getBuffer() {
      return new Promise((resolve) => {
        this.mediaRecorder.onstop = () => {
          const blob = new Blob(this.recordedChunks, {
            type: 'video/webm'
          });
          resolve(blob);
        };
      });
    }
  }

  async function loadPresets() {
    try {
      presets = await DbService.getAllConfigs();
      loadError = '';
    } catch (error) {
      console.error('Failed to load presets:', error);
      loadError = 'Failed to load presets. Please try again.';
    }
  }

  async function loadPresetConfig(preset) {
    try {
      if (preset.data?.environmentParams) {
        // Update parameter store with saved environment parameters
        Object.entries(preset.data.environmentParams).forEach(([key, value]) => {
          parameterStore.updateParameter(key, value);
        });

        // Send environment parameters to backend
        await websocketService.send({
          type: "update_environment",
          params: preset.data.environmentParams
        });
      }

      if (preset.type === 'rewards' && preset.data?.rewards) {
        // Send request_reward message
        await websocketService.send({
          type: "request_reward",
          reward: {
            rewards: preset.data.rewards,
            weights: preset.data.weights,
            combinationType: preset.data.combinationType
          },
          timestamp: new Date().toISOString()
        });

        // Request updated state after loading rewards
        await websocketService.send({
          type: "debug_model_info"
        });
      }
      
      loadError = '';
    } catch (error) {
      console.error('Failed to load preset configuration:', error);
      loadError = 'Failed to load preset. Please try again.';
    }
  }

  onMount(async () => {
    try {
      await loadPresets();
      
      videoBuffer = new VideoBuffer();
      await videoBuffer.initializeBuffer();
      
      setInterval(() => {
        const currentUrl = `${apiUrl}/amjpeg?${Date.now()}`;
        videoBuffer.updateFrame(currentUrl);
      }, 33);
      
    } catch (error) {
      console.error('Failed during initialization:', error);
      loadError = 'Failed to initialize. Please refresh the page.';
    } finally {
      isLoading = false;
    }
  });

  onDestroy(() => {
    if (videoBuffer?.stream) {
      videoBuffer.stream.getTracks().forEach(track => track.stop());
    }
  });

  function filterPresets(presets) {
    if (selectedType === 'all') return presets;
    return presets.filter(preset => preset.type === selectedType);
  }

  async function deletePreset(id) {
    try {
      await DbService.deleteConfig(id);
      await loadPresets();
      saveError = '';
    } catch (error) {
      console.error('Failed to delete preset:', error);
      saveError = 'Failed to delete preset. Please try again.';
    }
  }

  async function saveCurrentConfig() {
    const title = prompt('Enter a name for this configuration:');
    if (!title) return;

    isSaving = true;
    saveError = '';
    
    try {
      videoBuffer.startRecording();
      const videoBlob = await videoBuffer.getBuffer();
      
      const base64Thumbnail = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64String = reader.result.split(',')[1];
          resolve(base64String);
        };
        reader.readAsDataURL(videoBlob);
      });

      let rewardsData = null;

      try {
        // Request current model info
        websocketService.send({
          type: "debug_model_info"
        });

        const modelInfo = await new Promise((resolve, reject) => {
          const cleanup = websocketService.addMessageHandler((data) => {
            if (data.type === 'debug_model_info') {
              cleanup();
              resolve(data);
            }
          });

          setTimeout(() => {
            cleanup();
            reject(new Error('Timeout waiting for model info'));
          }, 5000);
        });

        if (modelInfo?.active_rewards) {
          rewardsData = {
            rewards: modelInfo.active_rewards.rewards,
            weights: modelInfo.active_rewards.weights,
            combinationType: modelInfo.active_rewards.combinationType,
          };
        }
      } catch (error) {
        console.log('No rewards data available:', error);
      }

      // Get current environment parameters from store
      const environmentParams = {
        gravity: $parameterStore.gravity,
        density: $parameterStore.density,
        wind_x: $parameterStore.wind_x,
        wind_y: $parameterStore.wind_y,
        wind_z: $parameterStore.wind_z,
        viscosity: $parameterStore.viscosity,
        timestep: $parameterStore.timestep
      };
      
      const config = {
        title,
        type: rewardsData ? 'rewards' : 'environment',
        thumbnail: base64Thumbnail,
        data: {
          ...(rewardsData && { ...rewardsData }),
          environmentParams
        }
      };
      
      await DbService.addConfig(config);
      await loadPresets();

    } catch (error) {
      console.error('Failed to save configuration:', error);
      saveError = 'Failed to save configuration. Please try again.';
    } finally {
      isSaving = false;
    }
  }
</script>

<div class="w-full bg-white rounded-lg shadow-lg p-4 mb-8">
  <div class="w-full">
    <h2 class="text-lg font-bold text-gray-800">Timeline</h2>
    <PresetTimeline />
  </div>
  <div class="flex justify-between items-center mb-4">
    <h2 class="text-lg font-bold text-gray-800">Presets</h2>
    <div class="flex gap-4">
      <select 
        bind:value={selectedType}
        class="border rounded-md px-2 py-1 text-sm"
      >
        <option value="all">All Types</option>
        <option value="environment">Environment</option>
        <option value="rewards">Rewards</option>
      </select>
      <button 
        class="bg-green-500 text-white px-3 py-1 text-sm font-medium rounded-md hover:bg-green-600 transition-colors disabled:bg-gray-400"
        on:click={saveCurrentConfig}
        disabled={isSaving}
      >
        {isSaving ? 'Saving...' : 'Save Current'}
      </button>
    </div>
  </div>

  {#if saveError}
    <div class="text-red-500 mb-4 text-sm">{saveError}</div>
  {/if}

  {#if loadError}
    <div class="text-red-500 mb-4 text-sm">{loadError}</div>
  {/if}

  {#if isLoading}
    <p class="text-gray-500">Loading presets...</p>
  {:else}
    <div class="flex gap-4 overflow-x-auto pb-4">
      {#each filterPresets(presets) as preset (preset.id)}
        <div 
          draggable="true"
          on:dragstart={(e) => {
            e.dataTransfer.setData('preset', JSON.stringify(preset));
          }}
          class="flex-shrink-0 w-52 border rounded-lg p-4 bg-white shadow-sm cursor-move"
          transition:fade
        >
          {#if preset.thumbnail}
            <video 
              src={`data:video/webm;base64,${preset.thumbnail}`}
              autoplay
              muted
              loop
              playsinline
              class="w-full mb-2 rounded"
              height="120"
            ></video>
          {/if}
          
          <div class="flex justify-between items-start mb-2">
            <h3 class="font-semibold text-gray-800">{preset.title}</h3>
            <span class="text-xs px-2 py-1 bg-gray-100 rounded-full">
              {preset.type}
            </span>
          </div>
          
          <div class="text-sm text-gray-600 mb-4">
            {#if preset.data?.environmentParams}
              G: {preset.data.environmentParams.gravity}
              D: {preset.data.environmentParams.density}
              {#if preset.type === 'rewards' && preset.data?.rewards}
                <br>
                {preset.data.rewards.length} rewards
              {/if}
            {/if}
          </div>

          <div class="flex justify-end gap-2">
            <button 
              class="text-sm text-blue-600 hover:text-blue-800"
              on:click={() => loadPresetConfig(preset)}
            >
              Load
            </button>
            <button 
              class="text-sm text-red-600 hover:text-red-800"
              on:click={() => deletePreset(preset.id)}
            >
              Delete
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .overflow-x-auto::-webkit-scrollbar {
    display: none;
  }

  .overflow-x-auto {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
</style>