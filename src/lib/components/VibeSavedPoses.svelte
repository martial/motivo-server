<script>
  import { onMount, onDestroy } from 'svelte';
  const apiUrl = import.meta.env.VITE_API_URL;

  let savedPoses = [];
  let interval;

  // Assuming video is 30fps - adjust this value based on your video fps
  const FPS = 30;

  function frameToTime(frame) {
      return frame / FPS;
  }

  async function loadSavedPoses() {
    try {
      const response = await fetch(`${apiUrl}/api/vibeconf`);
      if (response.ok) {
        savedPoses = await response.json();
      }
    } catch (error) {
      console.error('Error loading saved poses:', error);
    }
  }

  async function deletePose(id) {
    try {
      const response = await fetch(`${apiUrl}/api/vibeconf/delete/${id}`, {
      });
      if (response.ok) {
        savedPoses = savedPoses.filter(pose => pose.id !== id);
      }
    } catch (error) {
      console.error('Error deleting pose:', error);
    }
  }

  function handleVideoLoad(event, frame) {
    const video = event.target;
    // Convert frame to time and seek to that position
    video.currentTime = frameToTime(frame);
  }

  // Stop video from playing automatically after seeking
  function handleSeeked(event) {
    const video = event.target;
    video.pause();
  }

  onMount(() => {
    loadSavedPoses();
    interval = setInterval(loadSavedPoses, 1500);
  });

  onDestroy(() => {
    if (interval) {
      clearInterval(interval);
    }
  });
</script>

<section class="p-4">
  <h2 class="text-xl font-bold mb-4">Saved Poses</h2>
  
  {#if savedPoses.length === 0}
    <p class="text-gray-600">No saved poses yet.</p>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each savedPoses as pose (pose.id)}
        <div class="border rounded-lg p-4 shadow-sm">
          <video 
            src={`${apiUrl}/video/renders/${pose.video}`}
            class="w-full h-32 object-cover rounded mb-2"
            controls
            on:loadedmetadata={(e) => handleVideoLoad(e, pose.frame)}
            on:seeked={handleSeeked}
            preload="metadata"
          >
            Your browser does not support the video element.
          </video>
          <h3 class="font-semibold">{pose.title}</h3>
          <p class="text-sm text-gray-600">Video: {pose.video}</p>
          <p class="text-sm text-gray-600">Frame: {pose.frame} (Time: {frameToTime(pose.frame).toFixed(2)}s)</p>
          
          <div class="flex justify-end gap-2 mt-2">
            <button
              class="px-3 py-1 text-sm text-blue-600 hover:text-blue-800"
              on:click={() => {/* Add load pose functionality */}}
            >
              Load
            </button>
            <button
              class="px-3 py-1 text-sm text-red-600 hover:text-red-800"
              on:click={() => deletePose(pose.id)}
            >
              Delete
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</section>