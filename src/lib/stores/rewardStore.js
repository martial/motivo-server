import { writable } from "svelte/store";

// Define reward types and their parameters
export const REWARD_TYPES = {
  "move-ego": {
    move_speed: { type: "range", default: 2.0, min: 0, max: 5, step: 0.1 },
    stand_height: { type: "range", default: 1.4, min: 0.5, max: 2, step: 0.1 },
    move_angle: { type: "range", default: 0, min: -180, max: 180, step: 1 },
    egocentric_target: { type: "boolean", default: true },
    low_height: { type: "range", default: 0.6, min: 0.2, max: 1, step: 0.1 },
    stay_low: { type: "boolean", default: false },
  },
  raisearms: {
    left: { type: "select", options: ["l", "m", "h"], default: "m" },
    right: { type: "select", options: ["l", "m", "h"], default: "m" },
  },
  "move-and-raise-arms": {
    move_speed: { type: "range", default: 2.0, min: 0, max: 5, step: 0.1 },
    move_angle: { type: "range", default: 0, min: -180, max: 180, step: 1 },
    left_pose: { type: "select", options: ["l", "m", "h"], default: "m" },
    right_pose: { type: "select", options: ["l", "m", "h"], default: "m" },
    stand_height: { type: "range", default: 1.4, min: 0.5, max: 2, step: 0.1 },
    arm_coeff: { type: "range", default: 1.0, min: 0, max: 2, step: 0.1 },
    loc_coeff: { type: "range", default: 1.0, min: 0, max: 2, step: 0.1 },
  },
  jump: {
    jump_height: { type: "range", default: 1.6, min: 0.5, max: 3, step: 0.1 },
    max_velocity: { type: "range", default: 5.0, min: 1, max: 10, step: 0.1 },
  },
  rotation: {
    axis: { type: "select", options: ["x", "y", "z"], default: "y" },
    target_ang_velocity: {
      type: "range",
      default: 5.0,
      min: -10,
      max: 10,
      step: 0.1,
    },
    stand_pelvis_height: {
      type: "range",
      default: 0.8,
      min: 0.4,
      max: 1.5,
      step: 0.1,
    },
  },
  headstand: {
    stand_pelvis_height: {
      type: "range",
      default: 0.95,
      min: 0.5,
      max: 1.5,
      step: 0.05,
    },
  },
  crawl: {
    spine_height: {
      type: "range",
      default: 0.3,
      min: 0.1,
      max: 0.6,
      step: 0.05,
    },
    move_speed: { type: "range", default: 1.0, min: 0, max: 3, step: 0.1 },
    direction: { type: "select", options: ["u", "d"], default: "u" },
  },
  liedown: {
    direction: { type: "select", options: ["up", "down"], default: "down" },
  },
  sit: {
    pelvis_height_th: {
      type: "range",
      default: 0,
      min: -0.5,
      max: 0.5,
      step: 0.1,
    },
    constrained_knees: { type: "boolean", default: false },
  },
  split: {
    distance: { type: "range", default: 1.5, min: 0.5, max: 2.5, step: 0.1 },
  },
  // Custom Body Part Controls
  "left-hand-height": {
    height: { type: "range", default: 1.0, min: 0, max: 2, step: 0.1 },
  },
  "left-hand-lateral": {
    position: { type: "range", default: 0, min: -1, max: 1, step: 0.1 },
  },
  "left-hand-forward": {
    position: { type: "range", default: 0, min: -1, max: 1, step: 0.1 },
  },
  "right-hand-height": {
    height: { type: "range", default: 1.0, min: 0, max: 2, step: 0.1 },
  },
  "right-hand-lateral": {
    position: { type: "range", default: 0, min: -1, max: 1, step: 0.1 },
  },
  "right-hand-forward": {
    position: { type: "range", default: 0, min: -1, max: 1, step: 0.1 },
  },
  "left-foot-height": {
    height: { type: "range", default: 0, min: 0, max: 2.0, step: 0.1 },
  },
  "right-foot-height": {
    height: { type: "range", default: 0, min: 0, max: 2.0, step: 0.1 },
  },
  "left-foot-lateral": {
    position: { type: "range", default: 0, min: -1, max: 1, step: 0.1 },
  },
  "right-foot-lateral": {
    position: { type: "range", default: 0, min: -1, max: 1, step: 0.1 },
  },
  "left-foot-forward": {
    position: { type: "range", default: 0, min: -1, max: 2.0, step: 0.1 },
  },
  "right-foot-forward": {
    position: { type: "range", default: 0, min: -1, max: 2.0, step: 0.1 },
  },
  "stay-upright": {
    strength: { type: "range", default: 1.0, min: 0, max: 2.0, step: 0.1 },
  },
  "head-height": {
    height: { type: "range", default: 1.6, min: 0.2, max: 2, step: 0.1 },
  },
  "pelvis-height": {
    height: { type: "range", default: 1.0, min: 0.2, max: 10.0, step: 0.1 },
  },
  "hand-height": {
    height: { type: "range", default: 1.0, min: 0, max: 2, step: 0.1 },
  },
  "hand-lateral": {
    position: { type: "range", default: 0, min: -1, max: 1, step: 0.1 },
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

  let socket;

  function setSocket(ws) {
    console.log("try set socket");
    socket = ws;
  }

  function sendRewardRequest(rewards, weights, combinationType) {
    console.log("try reward request");
    if (socket?.readyState === WebSocket.OPEN) {
      const rewardRequest = {
        type: "request_reward",
        reward: {
          rewards,
          weights,
          combination_type: combinationType,
        },
        timestamp: new Date().toISOString(),
      };
      console.log("Sending reward request:", rewardRequest);
      socket.send(JSON.stringify(rewardRequest));
    }
  }

  function cleanRewards() {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(
        JSON.stringify({
          type: "clean_rewards",
          timestamp: new Date().toISOString(),
        })
      );
      set({ activeRewards: [], weights: [], combinationType: "additive" });
    }
  }

  return {
    subscribe,
    setSocket,
    addReward: (rewardType, parameters) => {
      update((state) => {
        const newRewards = [
          ...state.activeRewards,
          {
            name: rewardType,
            ...parameters,
          },
        ];
        const newWeights = [...state.weights, 1.0];

        // Normalize weights
        const weightSum = newWeights.reduce((a, b) => a + b, 0);
        const normalizedWeights = newWeights.map((w) => w / weightSum);

        sendRewardRequest(newRewards, normalizedWeights, state.combinationType);

        return {
          ...state,
          activeRewards: newRewards,
          weights: normalizedWeights,
        };
      });
    },
    removeReward: (index) => {
      update((state) => {
        const newRewards = state.activeRewards.filter((_, i) => i !== index);
        const newWeights = state.weights.filter((_, i) => i !== index);

        // Normalize remaining weights
        const weightSum = newWeights.reduce((a, b) => a + b, 0);
        const normalizedWeights = weightSum
          ? newWeights.map((w) => w / weightSum)
          : [];

        sendRewardRequest(newRewards, normalizedWeights, state.combinationType);

        return {
          ...state,
          activeRewards: newRewards,
          weights: normalizedWeights,
        };
      });
    },
    updateWeight: (index, weight) => {
      update((state) => {
        const newWeights = [...state.weights];
        newWeights[index] = weight;

        // Normalize weights
        const weightSum = newWeights.reduce((a, b) => a + b, 0);
        const normalizedWeights = newWeights.map((w) => w / weightSum);

        sendRewardRequest(
          state.activeRewards,
          normalizedWeights,
          state.combinationType
        );

        return {
          ...state,
          weights: normalizedWeights,
        };
      });
    },
    setCombinationType: (type) => {
      update((state) => {
        sendRewardRequest(state.activeRewards, state.weights, type);
        return { ...state, combinationType: type };
      });
    },
    cleanRewards,
  };
}

export const rewardStore = createRewardStore();
