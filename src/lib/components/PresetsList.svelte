<!-- PresetsList.svelte -->
<script>
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';
  import { DbService } from '../services/db';
  import { websocketService } from '../services/websocketService';

  let presets = [];
  let selectedType = 'all';
  let isLoading = true;
  let thumbnail = null;
  let videoBuffer;
  
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

  onMount(async () => {
    try {
      presets = await DbService.getAllConfigs();
      
      // Initialize video buffer
      videoBuffer = new VideoBuffer();
      await videoBuffer.initializeBuffer();
      
      // Update frames
      setInterval(() => {
        const currentUrl = `${apiUrl}/amjpeg?${Date.now()}`;
        videoBuffer.updateFrame(currentUrl);
      }, 33);
      
    } catch (error) {
      console.error('Failed to load presets:', error);
    } finally {
      isLoading = false;
    }
  });

  function filterPresets(presets) {
    if (selectedType === 'all') return presets;
    return presets.filter(preset => preset.type === selectedType);
  }

  async function deletePreset(id) {
      try {
        await DbService.deleteConfig(id);
        presets = presets.filter(preset => preset.id !== id);
      } catch (error) {
        console.error('Failed to delete preset:', error);
      }
  }

  async function saveCurrentConfig() {
    const title = prompt('Enter a name for this configuration:');
    if (!title) return;

    try {
      // Start recording thumbnail
      videoBuffer.startRecording();
      const videoBlob = await videoBuffer.getBuffer();
      
      // Convert blob to base64
      const base64Thumbnail = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          // Remove the data URL prefix to get just the base64 string
          const base64String = reader.result.split(',')[1];
          resolve(base64String);
        };
        reader.readAsDataURL(videoBlob);
      });

      // Create a Promise to handle the single response
      const configPromise = new Promise((resolve, reject) => {
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

      websocketService.getSocket()?.send(JSON.stringify({
        type: "debug_model_info"
      }));

      const modelInfo = await configPromise;
      
      const config = {
        title,
        type: 'rewards',
        thumbnail: base64Thumbnail, // Add thumbnail to config
        data: {
          rewards: modelInfo.active_rewards.rewards,
          weights: modelInfo.active_rewards.weights,
          combinationType: modelInfo.active_rewards.combinationType
        }
      };
      
      console.log('Saving configuration:', config);
      const newPreset = await DbService.addConfig(config);
      presets = [...presets, newPreset];

    } catch (error) {
      console.error('Failed to save configuration:', error);
    }
  }

  async function saveThumbnail() {
    videoBuffer.startRecording();
    const videoBlob = await videoBuffer.getBuffer();
    thumbnail = URL.createObjectURL(videoBlob);
  }

  async function createThumbnail() {
    await saveThumbnail();
  }
</script>

<div class="w-full bg-white rounded-lg shadow-lg p-4">
  <div class="flex justify-between items-center mb-4">
    <h2 class="text-lg font-bold text-gray-800">Presets</h2>
    <div class="flex gap-4">
      <select 
        bind:value={selectedType}
        class="border rounded-md px-2 py-1 text-sm"
      >
        <option value="all">All Types</option>
        <option value="llm">LLM</option>
        <option value="rewards">Rewards</option>
      </select>
      <button 
        class="bg-green-500 text-white px-3 py-1 text-sm font-medium rounded-md hover:bg-green-600 transition-colors"
        on:click={saveCurrentConfig}
      >
        Save Current
      </button>
      <button 
        class="bg-blue-500 text-white px-3 py-1 text-sm font-medium rounded-md hover:bg-blue-600 transition-colors"
        on:click={createThumbnail}
      >
        Create Thumbnail
      </button>
    </div>
  </div>

  {#if isLoading}
    <p class="text-gray-500">Loading presets...</p>
  {:else}
    <div class="flex gap-4 overflow-x-auto pb-4">
      {#if thumbnail}
        <div class="flex-shrink-0 w-64 border rounded-lg p-4 bg-white shadow-sm">
          <video src={thumbnail} controls width="320" height="240"></video>
        </div>
      {/if}
      
      {#each filterPresets(presets) as preset (preset.id)}
        <div 
          class="flex-shrink-0 w-64 border rounded-lg p-4 bg-white shadow-sm"
          transition:fade
        >
          {#if preset.thumbnail}
            <video 
              src={`data:video/webm;base64,${preset.thumbnail}`}
              controls
              autoplay
              loop
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
            {#if preset.type === 'rewards'}
              {preset.data.rewards.length} rewards
            {:else}
              LLM Configuration
            {/if}
          </div>

          <div class="flex justify-end gap-2">
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