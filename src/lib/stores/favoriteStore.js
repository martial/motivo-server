import { writable } from "svelte/store";
import { rewardStore } from "./rewardStore";
import { websocketService } from "../services/websocketService";

function createFavoriteStore() {
  // Initialize from localStorage
  const storedFavorites = JSON.parse(
    localStorage.getItem("rewardFavorites") || "{}"
  );
  const { subscribe, set, update } = writable(storedFavorites);

  return {
    subscribe,
    saveFavorite(name, rewards) {
      update((favorites) => {
        const newFavorites = {
          ...favorites,
          [name]: rewards,
        };
        localStorage.setItem("rewardFavorites", JSON.stringify(newFavorites));
        return newFavorites;
      });
    },
    deleteFavorite(name) {
      update((favorites) => {
        const newFavorites = { ...favorites };
        delete newFavorites[name];
        localStorage.setItem("rewardFavorites", JSON.stringify(newFavorites));
        return newFavorites;
      });
    },
    loadFavorite(name) {
      const favorites = JSON.parse(
        localStorage.getItem("rewardFavorites") || "{}"
      );
      const favorite = favorites[name];
      console.log("Loading favorite:", name, favorite); // Debug log

      if (favorite) {
        const newState = {
          activeRewards: favorite.activeRewards,
          weights: favorite.activeRewards.map((reward) => reward.weight),
          combinationType: favorite.combinationType,
        };
        console.log("Setting rewardStore to:", newState); // Debug log

        // First update the store
        rewardStore.set(newState);

        // Then send the configuration to the WebSocket server
        const ws = websocketService.getSocket();
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(
            JSON.stringify({
              type: "request_reward",
              reward: {
                rewards: newState.activeRewards,
                weights: newState.weights,
                combinationType: newState.combinationType,
              },
            })
          );
        }
      } else {
        console.warn("No favorite found with name:", name); // Debug warning
      }
    },
    serializeConfig(name) {
      const favorites = JSON.parse(
        localStorage.getItem("rewardFavorites") || "{}"
      );
      const favorite = favorites[name];
      if (!favorite) return null;

      return btoa(JSON.stringify(favorite)); // Base64 encode
    },
    deserializeConfig(serialized) {
      try {
        return JSON.parse(atob(serialized)); // Base64 decode
      } catch (e) {
        console.error("Failed to deserialize config:", e);
        return null;
      }
    },
    importConfig(name, serialized) {
      const config = this.deserializeConfig(serialized);
      if (config) {
        this.saveFavorite(name, config);
        return true;
      }
      return false;
    },
  };
}

export const favoriteStore = createFavoriteStore();
