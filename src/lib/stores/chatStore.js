import { writable } from "svelte/store";

export const chatStore = writable({
  sessionId: null,
  conversation: [],
  response: "",
});
