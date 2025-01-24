import { writable } from "svelte/store";

class WebSocketService {
  constructor() {
    if (WebSocketService.instance) {
      return WebSocketService.instance;
    }
    WebSocketService.instance = this;

    this.socket = null;
    this.isReady = writable(false);
    this.wsUrl = import.meta.env.VITE_WS_URL;
  }

  connect() {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.close();
    }

    this.socket = new WebSocket(this.wsUrl);

    this.socket.onopen = () => {
      console.log("WebSocket connected");
      this.isReady.set(true);
      // Notify stores
      this.notifyStores();
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error("Error processing WebSocket message:", error);
      }
    };

    this.socket.onclose = () => {
      console.log("WebSocket disconnected");
      this.isReady.set(false);
    };

    this.socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      this.isReady.set(false);
    };
  }

  handleMessage(data) {
    // Handle different message types
    switch (data.type) {
      case "parameters":
      case "parameters_updated":
        import("../stores/parameterStore").then((module) => {
          module.parameterStore.set(data.parameters);
        });
        break;
      case "recording_status":
        console.log("Recording status update:", data.status);
        break;
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
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  getSocket() {
    return this.socket;
  }
}

export const websocketService = new WebSocketService();
