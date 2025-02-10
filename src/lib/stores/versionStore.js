import { writable } from "svelte/store";

export const versionInfo = writable({
  version: "local",
  commitHash: "development",
  lastCommitDate: new Date().toISOString(),
  environment: import.meta.env.DEV ? "development" : "production",
});

// Fetch version info from the Flask backend
async function loadVersionInfo() {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/api/version`);
    if (!response.ok) {
      console.error("Failed to load version info:", response);
    }
    const data = await response.json();

    // Validate the data
    if (!data.version || !data.commitHash || !data.lastCommitDate) {
      console.error("Invalid version info:", data);
    }

    versionInfo.set(data);
  } catch (error) {
    console.error("Failed to load version info:", error);
    // Set fallback values
    versionInfo.set({
      version: "local",
      commitHash: "development",
      lastCommitDate: new Date().toISOString(),
      environment: import.meta.env.DEV ? "development" : "production",
    });
  }
}

// Initial load
loadVersionInfo();

// Refresh every 5 minutes in dev
if (import.meta.env.DEV ) {
  setInterval(loadVersionInfo, 5 * 60 * 1000);
}
