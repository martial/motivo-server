import { writable } from "svelte/store";
import { websocketService } from "../services/websocketService";
import { v4 as uuidv4 } from "uuid";

// Define reward types and their parameters
export const REWARD_TYPES = {
  // Basic Movements
  "move-ego": {
    move_speed: { type: "range", min: 0, max: 5, step: 0.1, default: 2.0 },
    stand_height: { type: "range", min: 0, max: 2, step: 0.1, default: 1.4 },
    move_angle: { type: "range", min: -360, max: 360, step: 15, default: 0 },
    egocentric_target: { type: "checkbox", default: true },
    low_height: { type: "range", min: 0, max: 2, step: 0.1, default: 0.6 },
    stay_low: { type: "checkbox", default: false },
  },
  jump: {
    jump_height: { type: "range", min: 0.5, max: 2.5, step: 0.1, default: 1.6 },
    max_velocity: { type: "range", min: 0, max: 10, step: 0.5, default: 5.0 },
  },
  rotation: {
    axis: { type: "select", options: ["x", "y", "z"], default: "x" },
    target_ang_velocity: {
      type: "range",
      min: -10,
      max: 10,
      step: 0.5,
      default: 5.0,
    },
    stand_pelvis_height: {
      type: "range",
      min: 0.3,
      max: 1.5,
      step: 0.1,
      default: 0.8,
    },
  },
  crawl: {
    spine_height: {
      type: "range",
      min: 0.1,
      max: 1.0,
      step: 0.1,
      default: 0.3,
    },
    move_angle: { type: "range", min: -360, max: 360, step: 15, default: 0 },
    move_speed: { type: "range", min: 0, max: 2, step: 0.1, default: 1.0 },
    direction: { type: "select", options: [-1, 1], default: -1 },
  },

  // Poses
  raisearms: {
    target_height: { type: "range", min: 0, max: 2.5, step: 0.1, default: 1.8 },
  },
  headstand: {
    balance_factor: { type: "range", min: 0, max: 2, step: 0.1, default: 1.0 },
  },
  liedown: {
    target_height: { type: "range", min: 0, max: 0.5, step: 0.1, default: 0.2 },
  },
  sit: {
    target_height: { type: "range", min: 0, max: 1, step: 0.1, default: 0.6 },
  },
  split: {
    target_angle: { type: "range", min: 90, max: 180, step: 5, default: 180 },
  },

  // Combined Actions
  "move-and-raise-arms": {
    move_speed: { type: "range", min: 0, max: 5, step: 0.1, default: 2.0 },
    move_angle: { type: "range", min: -360, max: 360, step: 15, default: 0 },
    left_pose: { type: "select", options: ["h", "l", "m"], default: "h" },
    right_pose: { type: "select", options: ["h", "l", "m"], default: "h" },
    stand_height: { type: "range", min: 0, max: 2, step: 0.1, default: 1.4 },
    low_height: { type: "range", min: 0, max: 2, step: 0.1, default: 0.6 },
    stay_low: { type: "checkbox", default: false },
    egocentric_target: { type: "checkbox", default: true },
    arm_coeff: { type: "range", min: 0, max: 2, step: 0.1, default: 1.0 },
    loc_coeff: { type: "range", min: 0, max: 2, step: 0.1, default: 1.0 },
  },

  // Hand Controls
  "hand-height": {
    target_height: { type: "range", min: 0, max: 2.5, step: 0.1, default: 1.8 },
  },
  "hand-lateral": {
    target_distance: { type: "range", min: 0, max: 1, step: 0.1, default: 0.5 },
  },
  "left-hand-height": {
    target_height: { type: "range", min: 0, max: 2, step: 0.1, default: 1.0 },
  },
  "left-hand-lateral": {
    target_distance: { type: "range", min: 0, max: 1, step: 0.1, default: 0.5 },
  },
  "left-hand-forward": {
    target_distance: { type: "range", min: 0, max: 1, step: 0.1, default: 0.5 },
  },
  "right-hand-height": {
    target_height: { type: "range", min: 0, max: 2, step: 0.1, default: 1.0 },
  },
  "right-hand-lateral": {
    target_distance: { type: "range", min: 0, max: 1, step: 0.1, default: 0.5 },
  },
  "right-hand-forward": {
    target_distance: { type: "range", min: 0, max: 1, step: 0.1, default: 0.5 },
  },

  // Foot Controls
  "left-foot-height": {
    target_height: { type: "range", min: 0, max: 1, step: 0.1, default: 0.1 },
  },
  "left-foot-lateral": {
    target_distance: { type: "range", min: 0, max: 1, step: 0.1, default: 0.2 },
  },
  "left-foot-forward": {
    target_distance: { type: "range", min: 0, max: 1, step: 0.1, default: 0.2 },
  },
  "right-foot-height": {
    target_height: { type: "range", min: 0, max: 1, step: 0.1, default: 0.1 },
  },
  "right-foot-lateral": {
    target_distance: { type: "range", min: 0, max: 1, step: 0.1, default: 0.2 },
  },
  "right-foot-forward": {
    target_distance: { type: "range", min: 0, max: 1, step: 0.1, default: 0.2 },
  },

  // Other Controls
  "stay-upright": {}, // No parameters needed
  "head-height": {
    target_height: { type: "range", min: 0, max: 2, step: 0.1, default: 1.4 },
  },
  "pelvis-height": {
    target_height: { type: "range", min: 0, max: 2, step: 0.1, default: 0.8 },
  },
};

export const COMBINATION_TYPES = [
  "additive",
  "multiplicative",
  "min",
  "max",
  "geometric",
];

function createRewardStore() {
  const { subscribe, set, update } = writable({
    activeRewards: [],
    weights: [],
    combinationType: "multiplicative",
  });

  return {
    subscribe,
    set,
    update,
    addReward: (type, params) => {
      update((store) => {
        const newStore = {
          ...store,
          activeRewards: [...store.activeRewards, params],
          weights: [...store.weights, 1.0],
        };

        const ws = websocketService.getSocket();
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(
            JSON.stringify({
              type: "request_reward",
              id: params.id,
              reward: {
                rewards: newStore.activeRewards,
                weights: newStore.weights,
                combinationType: newStore.combinationType,
              },
            })
          );
        }

        return newStore;
      });
    },
    removeReward: (rewardId) => {
      update((store) => {
        const rewardIndex = store.activeRewards.findIndex(
          (r) => r.id === rewardId
        );
        if (rewardIndex === -1) return store;

        const newActiveRewards = [...store.activeRewards];
        const newWeights = [...store.weights];

        newActiveRewards.splice(rewardIndex, 1);
        newWeights.splice(rewardIndex, 1);

        const newStore = {
          ...store,
          activeRewards: newActiveRewards,
          weights: newWeights,
        };

        // Send updated configuration to WebSocket
        const ws = websocketService.getSocket();
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(
            JSON.stringify({
              type: "request_reward",
              reward: {
                rewards: newStore.activeRewards,
                weights: newStore.weights,
                combinationType: newStore.combinationType,
              },
            })
          );
        }

        return newStore;
      });
    },
    updateWeight: (index, weight) => {
      update((store) => {
        const newWeights = [...store.weights];
        newWeights[index] = weight;

        const newStore = {
          ...store,
          weights: newWeights,
        };

        const ws = websocketService.getSocket();
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(
            JSON.stringify({
              type: "request_reward",
              reward: {
                rewards: store.activeRewards,
                weights: newWeights,
                combinationType: store.combinationType,
              },
            })
          );
        }

        return newStore;
      });
    },
    cleanRewardsLocal: () => {
      set({
        activeRewards: [],
        weights: [],
        combinationType: "multiplicative",
      });
    },
    cleanRewards: () => {
      set({
        activeRewards: [],
        weights: [],
        combinationType: "multiplicative",
      });

      const ws = websocketService.getSocket();
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(
          JSON.stringify({
            type: "clean_rewards",
          })
        );
      }
    },
  };
}

export const rewardStore = createRewardStore();
