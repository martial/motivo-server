import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  server: {
    allowedHosts: true,
  },
  plugins: [
    svelte({
      compilerOptions: {
        compatibility: {
          componentApi: 4,
        },
      },
    }),
    tailwindcss(),
  ],
});
