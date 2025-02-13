<script>
  const version = import.meta.env.VITE_GIT_VERSION || 'development';
  const commitHash = import.meta.env.VITE_GIT_COMMIT_HASH || 'local';
</script>

<div class="text-xs text-gray-500">
  Version: {version} ({commitHash.substring(0, 7)})
</div> 