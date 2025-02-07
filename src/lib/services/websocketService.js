import { writable } from "svelte/store";

// Create a shared computing status store
export const computingStatus = writable(false);

class WebSocketService {
  static instance; // Déclarer la propriété statique

  constructor() {
    if (WebSocketService.instance) {
      return WebSocketService.instance;
    }
    WebSocketService.instance = this;

    this.socket = null;
    this.isReady = false;
    this.wsUrl = import.meta.env.VITE_WS_URL;
    this.readyStateListeners = new Set();

    // Add reconnection settings
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectTimeout = null;
    this.reconnectInterval = 3000; // 3 seconds

    // Add message handlers collection
    this.messageHandlers = new Set();

    this.statusInterval = null;
  }

  startStatusCheck() {
    // Clear any existing interval first
    if (this.statusInterval) {
      clearInterval(this.statusInterval);
    }

    // Start new status check with shorter interval (e.g., every second)
    this.checkModelStatus();
    this.statusInterval = setInterval(() => this.checkModelStatus(), 1000);
  }

  stopStatusCheck() {
    if (this.statusInterval) {
      clearInterval(this.statusInterval);
      this.statusInterval = null;
    }
  }

  checkModelStatus() {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(
        JSON.stringify({
          type: "debug_model_info",
          timestamp: new Date().toISOString(),
        })
      );
    }
  }

  connect() {
    if (this.socket?.readyState === WebSocket.OPEN) {
      console.log("Already connected, skipping connection attempt");
      return;
    }

    if (this.socket?.readyState === WebSocket.CONNECTING) {
      console.log("Already connecting, skipping connection attempt");
      return;
    }

    try {
      console.log(`Attempting to connect to ${this.wsUrl}`);
      this.socket = new WebSocket(this.wsUrl);

      this.socket.onopen = () => {
        console.log(`Successfully connected to ${this.wsUrl}`);
        this.isReady = true;
        this.reconnectAttempts = 0;
        this.notifyReadyStateListeners();
        this.startStatusCheck();
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error(
            "Error processing WebSocket message:",
            error,
            event.data
          );
        }
      };

      this.socket.onclose = (event) => {
        const reason = event.reason || "No reason provided";
        console.log(
          `WebSocket disconnected - Code: ${event.code}, Reason: ${reason}, Clean: ${event.wasClean}`
        );
        this.isReady = false;
        this.notifyReadyStateListeners();
        this.stopStatusCheck();

        // Only reconnect for specific error codes
        if (!event.wasClean && event.code !== 1000) {
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            const delay = Math.min(
              1000 * Math.pow(2, this.reconnectAttempts),
              10000
            );
            console.log(
              `Scheduling reconnect attempt ${this.reconnectAttempts + 1}/${
                this.maxReconnectAttempts
              } in ${delay}ms`
            );
            this.reconnectTimeout = setTimeout(() => {
              this.reconnectAttempts++;
              this.connect();
            }, delay);
          } else {
            console.log("Max reconnection attempts reached");
          }
        }
      };

      this.socket.onerror = (error) => {
        console.error("WebSocket error details:", {
          url: this.wsUrl,
          readyState: this.socket?.readyState,
          error: error,
        });
      };
    } catch (error) {
      console.error("Error creating WebSocket connection:", error);
    }
  }

  handleMessage(data) {
    // Handle debug_model_info at service level
    if (data.type === "debug_model_info") {
      // Update computing status
      computingStatus.set(data.is_computing);

      // Broadcast the raw message to all handlers
      this.messageHandlers.forEach((handler) => {
        handler({
          type: "debug_model_info",
          connected_clients: data.connected_clients,
          unique_clients: data.unique_clients,
          is_computing: data.is_computing,
          active_rewards: data.active_rewards,
        });
      });
    } else {
      // Handle other message types
      this.messageHandlers.forEach((handler) => handler(data));
    }
  }

  notifyStores() {
    // Update stores with new socket instance
    import("../stores/parameterStore").then((module) => {
      module.parameterStore.setSocket(this.socket);
    });
    import("../stores/rewardStore").then((module) => {
      module.rewardStore.setSocket(this.socket);
    });
  }

  disconnect() {
    this.stopStatusCheck();
    // Clear any pending reconnection attempts
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.socket) {
      this.socket.close(1000, "Intentional disconnect"); // Use 1000 for normal closure
      this.socket = null;
      this.reconnectAttempts = 0;
    }
  }

  getSocket() {
    return this.socket;
  }

  onReadyStateChange(callback) {
    this.readyStateListeners.add(callback);
    // Return cleanup function
    return () => this.readyStateListeners.delete(callback);
  }

  notifyReadyStateListeners() {
    for (const listener of this.readyStateListeners) {
      listener(this.isReady);
    }
  }

  // Add method to register message handlers
  addMessageHandler(handler) {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler); // Return cleanup function
  }

  updateReward(rewardIndex, updatedParams) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(
        JSON.stringify({
          type: "update_reward",
          index: rewardIndex,
          parameters: updatedParams,
          timestamp: new Date().toISOString(),
        })
      );
    }
  }

  send(data) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      // If this is a clean_rewards message, schedule an immediate debug check
      if (data.type === "clean_rewards") {
        this.socket.send(
          JSON.stringify({
            ...data,
            timestamp: new Date().toISOString(),
          })
        );

        // Trigger immediate debug check
        setTimeout(() => {
          this.socket.send(
            JSON.stringify({
              type: "debug_model_info",
              timestamp: new Date().toISOString(),
            })
          );
        }, 100); // Small delay to ensure reset completes first
      } else {
        // Normal message sending
        this.socket.send(
          JSON.stringify({
            ...data,
            timestamp: new Date().toISOString(),
          })
        );
      }
    } else {
      console.warn("WebSocket is not connected. Message not sent:", data);
    }
  }
}

export const websocketService = new WebSocketService();
