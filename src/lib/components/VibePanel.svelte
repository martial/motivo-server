<script>
  import { onMount, onDestroy } from "svelte";

  let videoUrl = "";
  let fileInput;
  let dragOver = false;
  let errorMessage = "";
  let isLoading = false;
  let videoElement;
  let selectedFile = null;
  let uploadedVideoUrl = "";
  let outputVideoBase64 = "";
  let poseData = null;

  const apiUrl = import.meta.env.VITE_API_URL;

  // Configurable options
  export let maxSizeInMB = 50;
  export let acceptedTypes = ["video/mp4", "video/webm", "video/ogg"];

  function handleFileSelect(event) {
    const file = event.target.files[0];
    validateAndProcessFile(file);
  }

  function handleDrop(event) {
    event.preventDefault();
    dragOver = false;

    const file = event.dataTransfer.files[0];
    validateAndProcessFile(file);
  }

  function validateAndProcessFile(file) {
    errorMessage = "";

    // Validate file type
    if (!acceptedTypes.includes(file.type)) {
      errorMessage = "Please upload a valid video file (MP4, WebM, or OGG)";
      return;
    }

    // Validate file size
    if (file.size > maxSizeInMB * 1024 * 1024) {
      errorMessage = `File size must be less than ${maxSizeInMB}MB`;
      return;
    }

    selectedFile = file;
    // Create preview URL
    videoUrl = URL.createObjectURL(file);
  }

  async function handleUpload() {
    if (!selectedFile) {
      errorMessage = "Please select a video file first";
      return;
    }

    isLoading = true;

    try {
      const formData = new FormData();
      formData.append("video", selectedFile);

      // Send POST request to upload endpoint
      const response = await fetch(`${apiUrl}/upload-video`, {
        mode: "no-cors",
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        uploadedVideoUrl = result.video_url;
        outputVideoBase64 = result.prediction?.output?.video;
        poseData = result.prediction?.output?.pose;
        console.log("Upload successful. Video URL:", uploadedVideoUrl);
        console.log("Video metadata:", result);
        console.log("Prediction output:", result.prediction?.output);
      } else {
        throw new Error(result.error || "Upload failed");
      }
    } catch (error) {
      errorMessage = "Error uploading file. Please try again.";
      console.error("Upload error:", error);
    } finally {
      isLoading = false;
    }
  }

  function handleDragOver(event) {
    event.preventDefault();
    dragOver = true;
  }

  function handleDragLeave() {
    dragOver = false;
  }

  function downloadPoseData() {
    if (!poseData) return;    
    // "{\n  \"person_1\": {\n 
    let cleanPoseData = JSON.parse(JSON.stringify(poseData));
    const blob = new Blob([cleanPoseData], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "pose-data.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  onMount(() => {
    // Any mount logic if needed
  });

  onDestroy(() => {
    // Clean up object URLs on component destroy
    if (videoUrl) {
      URL.revokeObjectURL(videoUrl);
    }
  });
</script>

<div class="">
  <div class="bg-white rounded-lg shadow-lg p-4">
    <h1 class="text-lg font-bold mb-4 text-gray-800">Video Upload</h1>

    <div class="space-y-3">
      <div
        class="w-full min-h-[200px] border-2 border-dashed rounded-lg p-5 text-center transition-all duration-300 ease-in-out {dragOver
          ? 'border-gray-600 bg-gray-50'
          : 'border-gray-300'}"
        on:dragover={handleDragOver}
        on:dragleave={handleDragLeave}
        on:drop={handleDrop}
      >
        <input
          bind:this={fileInput}
          type="file"
          accept={acceptedTypes.join(",")}
          on:change={handleFileSelect}
          class="hidden"
        />

        {#if isLoading}
          <div class="text-gray-600 my-5">Uploading... May take up to a minute</div>
        {:else if videoUrl}
          <div class="mt-5">
            <h2 class="text-md font-semibold mb-2">Input Video</h2>
            <video
              bind:this={videoElement}
              src={videoUrl}
              controls
              class="max-w-full max-h-[300px] mb-3 mx-auto"
            >
              <track kind="captions" />
              Your browser does not support the video tag.
            </video>
            <div class="space-x-2">
              <button
                on:click={() => fileInput.click()}
                class="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 transition-colors"
              >
                Change Video
              </button>
              <button
                on:click={handleUpload}
                class="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
              >
                Upload
              </button>
            </div>
          </div>
        {:else}
          <div class="text-gray-600">
            <p class="mb-4">
              Drag and drop a video file here or click to select
            </p>
            <button
              on:click={() => fileInput.click()}
              class="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 transition-colors"
            >
              Select Video
            </button>
          </div>
        {/if}

        {#if errorMessage}
          <div class="text-red-500 mt-3 text-sm">{errorMessage}</div>
        {/if}

        {#if outputVideoBase64}
          <div class="mt-8">
            <h2 class="text-md font-semibold mb-2">Processed Video Output</h2>
            <video
              src={`${outputVideoBase64}`}
              controls
              class="max-w-full max-h-[300px] mb-3 mx-auto"
            >
              <track kind="captions" />
              Your browser does not support the video tag.
            </video>
          </div>
        {/if}

        {#if poseData}
          <div class="mt-4">
            <button
              on:click={downloadPoseData}
              class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
            >
              Download Pose Data (JSON)
            </button>
          </div>
        {/if}

        {#if uploadedVideoUrl}
          <div class="mt-3 text-sm text-green-600">
            Video uploaded successfully!
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>
