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
  import VersionInfo from './lib/components/VersionInfo.svelte';
  
  export let url = "";

  onMount(() => {
    websocketService.connect();
  });

  onDestroy(() => {
    websocketService.disconnect();
  });
</script>

<div class="flex flex-col min-h-screen">
  <Router {url}>
    <Header />
    
    <main class="flex-1 bg-gray-50">
      <div class="h-full">
        <Route path="/"><Control /></Route>
        <Route path="/testing"><Home /></Route>
        <Route path="/about"><About /></Route>
        <Route path="/live"><LiveFeed /></Route>
        <Route path="/control"><Control /></Route>
      </div>
    </main>

    <Footer />
   
  </Router>
</div>

