<script>
  import { onMount, onDestroy } from 'svelte';
  import StatusBar from './StatusBar.svelte';
  
  const apiUrl = import.meta.env.VITE_API_URL;

  let currentImageUrl = `${apiUrl}/amjpeg?${Date.now()}`;
  let nextImageUrl;
  let refreshInterval;
  let isLoading = true;
  
  function loadNextImage() {
    nextImageUrl = `${apiUrl}/amjpeg?${Date.now()}`;
  }

  function handleImageLoad() {
    isLoading = false;
    currentImageUrl = nextImageUrl;
    setTimeout(loadNextImage, 100);
  }

  function handleImageError() {
    loadNextImage();
  }
  
  onMount(() => {
    loadNextImage();
  });
  
  onDestroy(() => {
    if (refreshInterval) clearInterval(refreshInterval);
  });
</script>

<div class="max-w-[320px] mx-auto">
  <!-- Image Container -->
  <div class="relative rounded-xl overflow-hidden bg-white shadow-lg border border-gray-200">
    {#if isLoading}
      <div class="absolute inset-0 flex items-center justify-center bg-gray-50/80 backdrop-blur-sm">
        <div class="animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
      </div>
    {/if}
    
    <img 
      src={currentImageUrl}
      alt="MJPEG Feed"
      class="w-[320px] h-[240px] object-contain"
    />
    <img 
      src={nextImageUrl}
      alt="MJPEG Feed"
      class="hidden"
      on:load={handleImageLoad}
      on:error={handleImageError}
    />
  </div>

  <StatusBar {isLoading} />
</div> 