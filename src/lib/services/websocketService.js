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

    // Start new status check
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
      this.socket.send(JSON.stringify({ type: "debug_model_info" }));
    }
  }

  connect() {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    if (this.socket?.readyState === WebSocket.CONNECTING) {
      return; // Already trying to connect
    }

    this.socket = new WebSocket(this.wsUrl);

    this.socket.onopen = () => {
      console.log("WebSocket connected");
      this.isReady = true;
      this.reconnectAttempts = 0; // Reset reconnect attempts on successful connection
      this.notifyReadyStateListeners();
      this.startStatusCheck(); // Start status check when connected
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error("Error processing WebSocket message:", error);
      }
    };

    this.socket.onclose = (event) => {
      console.log("WebSocket disconnected", event.code, event.reason);
      this.isReady = false;
      this.notifyReadyStateListeners();
      this.stopStatusCheck(); // Stop status check when disconnected

      // Attempt to reconnect unless explicitly closed
      if (
        !event.wasClean &&
        this.reconnectAttempts < this.maxReconnectAttempts
      ) {
        this.reconnectTimeout = setTimeout(() => {
          this.reconnectAttempts++;
          console.log(
            `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
          );
          this.connect();
        }, this.reconnectInterval);
      }
    };

    this.socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      this.isReady = false;
      this.notifyReadyStateListeners();
    };
  }

  handleMessage(data) {
    // Handle debug_model_info at service level
    if (data.type === "debug_model_info") {
      computingStatus.set(data.is_computing);
    }

    // Notify all registered handlers
    for (const handler of this.messageHandlers) {
      handler(data);
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
}

export const websocketService = new WebSocketService();
