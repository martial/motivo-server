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
      default: 0.95,
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
    stand_height: { type: "range", min: 0, max: 2.5, step: 0.1, default: 1.4 },
    left_pose: { type: "select", options: ["l", "m", "h", "x"], default: "h" },
    right_pose: { type: "select", options: ["l", "m", "h", "x"], default: "h" },
  },
  headstand: {
    balance_factor: { type: "range", min: 0, max: 2, step: 0.1, default: 1.0 },
    stand_pelvis_height: {
      type: "range",
      min: 0.3,
      max: 1.5,
      step: 0.1,
      default: 0.95,
    },
  },
  liedown: {
    direction: { type: "select", options: ["up", "down"], default: "up" },
  },
  sit: {
    pelvis_height_th: { type: "range", min: 0, max: 1, step: 0.1, default: 0 },
    constrained_knees: { type: "checkbox", default: true },
    knees_not_on_ground: { type: "checkbox", default: false },
  },
  split: {
    distance: { type: "range", min: 0.5, max: 2.5, step: 0.1, default: 1.5 },
  },

  // Combined Actions
  "move-and-raise-arms": {
    move_speed: { type: "range", min: 0, max: 5, step: 0.1, default: 2.0 },
    move_angle: { type: "range", min: -360, max: 360, step: 15, default: 0 },
    left_pose: { type: "select", options: ["l", "m", "h", "x"], default: "h" },
    right_pose: { type: "select", options: ["l", "m", "h", "x"], default: "h" },
    stand_height: { type: "range", min: 0, max: 2, step: 0.1, default: 1.4 },
    low_height: { type: "range", min: 0, max: 2, step: 0.1, default: 0.6 },
    stay_low: { type: "checkbox", default: false },
    egocentric_target: { type: "checkbox", default: true },
    arm_coeff: { type: "range", min: 0, max: 2, step: 0.1, default: 1.0 },
    loc_coeff: { type: "range", min: 0, max: 2, step: 0.1, default: 1.0 },
    visualize_target_angle: { type: "checkbox", default: true },
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

  // Behavior Rewards
  standing: {
    target_height: { type: "range", min: 0, max: 2.5, step: 0.1, default: 1.4 },
    margin: { type: "range", min: 0, max: 1, step: 0.1, default: 0.2 },
  },
  upright: {
    min_upright: { type: "range", min: 0, max: 2, step: 0.1, default: 0.9 },
    margin: { type: "range", min: 0, max: 2, step: 0.1, default: 1.9 },
  },
  "movement-control": {
    margin: { type: "range", min: 0, max: 2, step: 0.1, default: 0.5 },
  },
  "small-control": {
    margin: { type: "range", min: 0, max: 2, step: 0.1, default: 1.0 },
    control_weight: { type: "range", min: 0, max: 1, step: 0.1, default: 0.8 },
  },
  position: {
    body_name: { type: "text", default: "" },
    target_pos: { type: "vector3", default: [0, 0, 0] },
    margin: { type: "range", min: 0, max: 1, step: 0.1, default: 0.2 },
  },
  balance: {
    margin: { type: "range", min: 0, max: 1, step: 0.1, default: 0.2 },
  },
  symmetry: {
    weight_hands: { type: "range", min: 0, max: 1, step: 0.1, default: 0.5 },
    weight_feet: { type: "range", min: 0, max: 1, step: 0.1, default: 0.5 },
    margin: { type: "range", min: 0, max: 1, step: 0.1, default: 0.2 },
  },
  "energy-efficiency": {
    vel_margin: { type: "range", min: 0, max: 2, step: 0.1, default: 1.0 },
    ctrl_margin: { type: "range", min: 0, max: 2, step: 0.1, default: 0.5 },
  },
  "natural-motion": {
    smoothness_weight: {
      type: "range",
      min: 0,
      max: 1,
      step: 0.1,
      default: 0.5,
    },
    coordination_weight: {
      type: "range",
      min: 0,
      max: 1,
      step: 0.1,
      default: 0.5,
    },
  },
  "gaze-direction": {
    target_point: { type: "vector3", default: [1.0, 0.0, 1.7] },
    angle_margin: { type: "range", min: 0, max: 2, step: 0.1, default: 0.5 },
  },
  "ground-contact": {
    desired_contacts: {
      type: "multiselect",
      options: ["L_Toe", "R_Toe"],
      default: ["L_Toe", "R_Toe"],
    },
  },
  "stable-standing": {
    standing_weight: { type: "range", min: 0, max: 1, step: 0.1, default: 0.3 },
    upright_weight: { type: "range", min: 0, max: 1, step: 0.1, default: 0.3 },
    balance_weight: { type: "range", min: 0, max: 1, step: 0.1, default: 0.2 },
    control_weight: { type: "range", min: 0, max: 1, step: 0.1, default: 0.2 },
  },
  "natural-walking": {
    balance_weight: { type: "range", min: 0, max: 1, step: 0.1, default: 0.3 },
    energy_weight: { type: "range", min: 0, max: 1, step: 0.1, default: 0.2 },
    symmetry_weight: { type: "range", min: 0, max: 1, step: 0.1, default: 0.2 },
    natural_motion_weight: {
      type: "range",
      min: 0,
      max: 1,
      step: 0.1,
      default: 0.3,
    },
  },
};

export const COMBINATION_TYPES = [
  "additive",
  "multiplicative",
  "min",
  "max",
  "geometric",
];

let testingInterval = null;
let currentHandler = null;

function createRewardStore() {
  const { subscribe, set, update } = writable({
    activeRewards: [],
    weights: [],
    combinationType: "geometric",
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
        combinationType: "geometric",
      });
    },
    cleanRewards: () => {
      set({
        activeRewards: [],
        weights: [],
        combinationType: "geometric",
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
    startTestingAllOptions: (statusCallback) => {
      if (testingInterval) return; // Already testing

      const rewardTypes = Object.entries(REWARD_TYPES);
      let currentIndex = 0;
      let isWaitingForCompletion = false;
      let currentRewardId = null;
      let computationTimeout = null;
      let hasReceivedResponse = false;

      const COMPUTATION_TIMEOUT = 10 * 60 * 1000; // 10 minutes for computation
      const NEXT_TEST_DELAY = 5000; // 5 seconds between tests

      console.log(
        `🔄 Starting sequential testing of all rewards (${rewardTypes.length} total)`
      );

      if (statusCallback) {
        statusCallback("Starting tests...", 0, rewardTypes.length);
      }

      // Define helper functions first
      const cleanup = () => {
        const ws = websocketService.getSocket();
        if (currentHandler && ws) {
          ws.removeEventListener("message", currentHandler);
          currentHandler = null;
        }
        if (computationTimeout) {
          clearTimeout(computationTimeout);
          computationTimeout = null;
        }
      };

      const moveToNext = () => {
        isWaitingForCompletion = false;
        currentIndex++;

        // Clean up before moving to next test
        cleanup();

        if (statusCallback) {
          statusCallback(
            "Waiting before next test...",
            currentIndex,
            rewardTypes.length
          );
        }

        console.log(
          `\n⏳ Waiting ${NEXT_TEST_DELAY / 1000} seconds before next test...`
        );
        setTimeout(() => {
          rewardStore.cleanRewards();
          testNext();
        }, NEXT_TEST_DELAY);
      };

      const testNext = () => {
        const ws = websocketService.getSocket();
        if (!ws || ws.readyState !== WebSocket.OPEN) {
          console.log("❌ WebSocket not connected, stopping tests");
          if (statusCallback) {
            statusCallback(
              "WebSocket disconnected",
              currentIndex,
              rewardTypes.length
            );
          }
          cleanup();
          return;
        }

        if (currentIndex >= rewardTypes.length) {
          console.log("✅ Finished testing all rewards");
          if (statusCallback) {
            statusCallback(
              "Testing complete!",
              rewardTypes.length,
              rewardTypes.length
            );
          }
          cleanup();
          return;
        }

        const [type, config] = rewardTypes[currentIndex];
        console.log(
          `\n📋 Step ${currentIndex + 1}/${
            rewardTypes.length
          }: Testing "${type}"`
        );

        // Create default parameters for this reward type
        currentRewardId = uuidv4();
        const defaultParams = Object.fromEntries(
          Object.entries(config).map(([key, value]) => [key, value.default])
        );

        const params = {
          id: currentRewardId,
          type: type,
          name: type,
          parameters: defaultParams,
        };

        console.log("⚙️ Parameters:", defaultParams);

        // Remove previous handler if exists
        cleanup();

        // Set up completion listener for this test
        currentHandler = (event) => {
          try {
            const data = JSON.parse(event.data);
            // Only log non-SMPL update messages
            if (data.type !== "smpl_update") {
              console.log("📩 Received:", data.type, data);
            }

            if (data.type === "reward") {
              // Got initial reward response
              console.log(
                `✅ Reward "${type}" request acknowledged, moving to next test in 5 seconds...`
              );

              if (statusCallback) {
                statusCallback(
                  `Testing "${type}" reward...`,
                  currentIndex + 1,
                  rewardTypes.length
                );
              }

              // Move to next test after 5 seconds
              setTimeout(() => {
                moveToNext();
              }, 5000);
            }
          } catch (error) {
            console.error("❌ Error handling message:", error);
            if (statusCallback) {
              statusCallback(
                `Error: ${error.message}`,
                currentIndex,
                rewardTypes.length
              );
            }
          }
        };

        // Add handler and start test
        ws.addEventListener("message", currentHandler);

        console.log("🧹 Cleaning previous rewards...");
        if (statusCallback) {
          statusCallback(
            "Cleaning previous rewards...",
            currentIndex,
            rewardTypes.length
          );
        }
        rewardStore.cleanRewards();

        // Wait a bit longer after cleaning
        setTimeout(() => {
          console.log(`📤 Sending reward request for "${type}"...`);
          if (statusCallback) {
            statusCallback(
              `Sending reward request for "${type}"...`,
              currentIndex,
              rewardTypes.length
            );
          }
          rewardStore.addReward(type, params);
        }, 1000); // Increased delay to 1 second
      };

      // Start the testing sequence
      testNext();
    },

    stopTesting: () => {
      console.log("🛑 Stopping all tests");
      if (testingInterval) {
        const ws = websocketService.getSocket();
        if (ws?.readyState === WebSocket.OPEN && currentHandler) {
          ws.removeEventListener("message", currentHandler);
        }
        clearInterval(testingInterval);
        testingInterval = null;
        rewardStore.cleanRewards();
      }
    },
  };
}

export const rewardStore = createRewardStore();
