import { writable } from "svelte/store";

export const location = writable(window.location.pathname);

// Update location on navigation
const originalPushState = history.pushState;
history.pushState = function (...args) {
  originalPushState.apply(this, args);
  location.set(window.location.pathname);
};

window.addEventListener("popstate", () => {
  location.set(window.location.pathname);
});
