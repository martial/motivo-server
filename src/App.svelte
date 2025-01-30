<script>
  import { Router, Link, Route } from "svelte-routing";
  import { onMount, onDestroy } from "svelte";
  import { websocketService } from "./lib/services/websocketService";
  import Header from './lib/components/Header.svelte';
  import LiveFeed from './lib/components/LiveFeed.svelte';
  import Home from './lib/pages/Home.svelte';
  import About from './lib/pages/About.svelte';
  import Control from './lib/pages/Control.svelte';
  import Footer from './lib/components/Footer.svelte';
  
  export let url = "";

  onMount(() => {
    websocketService.connect();
  });

  onDestroy(() => {
    websocketService.disconnect();
  });
</script>

<div class="min-h-screen">
  <Router {url}>
    <main class="pb-16 flex flex-col bg-gray-50">
      <Header />
      
      <div class="w-full px-4 flex-grow">
        <Route path="/"><Home /></Route>
        <Route path="/about"><About /></Route>
        <Route path="/live"><LiveFeed /></Route>
        <Route path="/control"><Control /></Route>
      </div>

      <Footer />
    </main>
  </Router>
</div>

