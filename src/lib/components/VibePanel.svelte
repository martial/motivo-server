<script>
    import { onMount } from 'svelte';
  
    let imageUrl = '';
    let fileInput;
    let dragOver = false;
    let errorMessage = '';
    let isLoading = false;
  
    // Configurable options
    export let maxSizeInMB = 5;
    export let acceptedTypes = ['image/jpeg', 'image/png', 'image/gif'];
    
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
      errorMessage = '';
      
      // Validate file type
      if (!acceptedTypes.includes(file.type)) {
        errorMessage = 'Please upload a valid image file (JPEG, PNG, or GIF)';
        return;
      }
  
      // Validate file size
      if (file.size > maxSizeInMB * 1024 * 1024) {
        errorMessage = `File size must be less than ${maxSizeInMB}MB`;
        return;
      }
  
      // Create preview URL
      imageUrl = URL.createObjectURL(file);
      
      // Simulate upload
      uploadFile(file);
    }
  
    async function uploadFile(file) {
      isLoading = true;
      
      try {
        // Simulate API call with delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Here you would typically send the file to your server
        // const formData = new FormData();
        // formData.append('image', file);
        // const response = await fetch('/api/upload', {
        //   method: 'POST',
        //   body: formData
        // });
        
        console.log('File uploaded successfully:', file.name);
      } catch (error) {
        errorMessage = 'Error uploading file. Please try again.';
        console.error('Upload error:', error);
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
  
    onMount(() => {
      return () => {
        // Clean up object URL on component destroy
        if (imageUrl) {
          URL.revokeObjectURL(imageUrl);
        }
      };
    });
  </script>
  
  <div 
    class="w-full max-w-lg min-h-[200px] border-2 border-dashed border-gray-300 rounded-lg p-5 text-center transition-all duration-300 ease-in-out {dragOver ? 'border-blue-500 bg-blue-50' : ''}"
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
    on:drop={handleDrop}
  >
    <input
      bind:this={fileInput}
      type="file"
      accept={acceptedTypes.join(',')}
      on:change={handleFileSelect}
      class="hidden"
    />
    
    {#if isLoading}
      <div class="text-blue-500 my-5">Uploading...</div>
    {:else if imageUrl}
      <div class="mt-5">
        <img src={imageUrl} alt="Preview" class="max-w-full max-h-[300px] mb-3 mx-auto" />
        <button 
          on:click={() => fileInput.click()}
          class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors duration-300"
        >
          Change Image
        </button>
      </div>
    {:else}
      <div class="text-gray-600">
        <p class="mb-4">Drag and drop an image here or click to select</p>
        <button 
          on:click={() => fileInput.click()}
          class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors duration-300"
        >
          Select Image
        </button>
      </div>
    {/if}
  
    {#if errorMessage}
      <div class="text-red-500 mt-3">{errorMessage}</div>
    {/if}
  </div>