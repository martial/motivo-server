import json
import os
from typing import Dict, Any
import asyncio
from datetime import datetime
import torch
from functools import lru_cache
import hashlib
import numpy as np
from pathlib import Path

class RewardContextCache:
    def __init__(self, max_memory_entries=100, cache_dir=None, model=None, env=None, buffer_data=None):
        self.computation_cache = {}
        self.max_memory_entries = max_memory_entries
        self.cache_dir = cache_dir or Path(os.path.expanduser('~/.motivo/cache'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # LRU cache for frequently accessed items
        self._get_cached_context = lru_cache(maxsize=max_memory_entries)(self._get_cached_context_impl)

        # Pre-compute default context if model and env are provided
        if model is not None and env is not None and buffer_data is not None:
            self.precompute_default_context(model, env, buffer_data)
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """Get the path to the cache file for a given key"""
        # Use hash to create a safe filename
        hashed_key = hashlib.sha256(cache_key.encode()).hexdigest()
        return self.cache_dir / f"{hashed_key}.npz"
    
    def _save_to_disk(self, cache_key: str, z: torch.Tensor) -> None:
        """Save context to disk cache"""
        try:
            cache_file = self._get_cache_file(cache_key)
            # Convert to numpy and save
            z_np = z.cpu().numpy()
            np.savez_compressed(cache_file, z=z_np)
            print(f"\nSaved context to disk cache: {cache_file}")
        except Exception as e:
            print(f"\nWarning: Failed to save to disk cache: {e}")
    
    def _load_from_disk(self, cache_key: str) -> torch.Tensor:
        """Load context from disk cache"""
        try:
            cache_file = self._get_cache_file(cache_key)
            if cache_file.exists():
                # Load from numpy and convert back to tensor
                data = np.load(cache_file)
                # Get the device that should be used
                if torch.backends.mps.is_available():
                    device = torch.device('mps')
                elif torch.cuda.is_available():
                    device = torch.device('cuda')
                else:
                    device = torch.device('cpu')
                
                # Convert to tensor and move to correct device
                z = torch.from_numpy(data['z']).to(device=device, dtype=torch.float32)
                print(f"\nLoaded context from disk cache: {cache_file} (device: {z.device})")
                return z
        except Exception as e:
            print(f"\nWarning: Failed to load from disk cache: {e}")
        return None
    
    def get_cache_key(self, reward_config: Dict[str, Any]) -> str:
        """Generate a consistent cache key for a reward configuration"""
        # Sort rewards by name and parameters for consistency
        sorted_rewards = sorted(
            reward_config['rewards'],
            key=lambda x: (x['name'], json.dumps({k: v for k, v in x.items() if k != 'id'}, sort_keys=True))
        )
        
        # Create a normalized config for hashing
        normalized_config = {
            'rewards': [{k: v for k, v in r.items() if k != 'id'} for r in sorted_rewards],
            'combinationType': reward_config.get('combinationType', 'multiplicative'),
            'weights': reward_config.get('weights', [1.0] * len(sorted_rewards))
        }
        
        return json.dumps(normalized_config, sort_keys=True)
    
    @lru_cache(maxsize=1000)
    def _get_cached_context_impl(self, cache_key: str) -> torch.Tensor:
        """Internal implementation of context retrieval with LRU cache"""
        # Check memory cache first
        if cache_key in self.computation_cache:
            z = self.computation_cache[cache_key]
            print("\nUSING MEMORY CACHE ✓")
            print(f"Cached tensor device: {z.device}")
            return z
        
        # Try loading from disk cache
        z = self._load_from_disk(cache_key)
        if z is not None:
            # Store in memory cache if there's room
            if len(self.computation_cache) < self.max_memory_entries:
                self.computation_cache[cache_key] = z
            return z
        
        return None
    
    async def get_cached_context(self, reward_config: Dict[str, Any], compute_fn) -> Any:
        """Get context from cache or compute new one with improved caching"""
        cache_key = self.get_cache_key(reward_config)
        
        # Try to get from cache (memory or disk)
        cached_z = self._get_cached_context_impl(cache_key)
        if cached_z is not None:
            return cached_z
        
        print("\nCOMPUTING NEW CONTEXT - Cache miss ⚙️")
        z = await compute_fn(reward_config)
        
        # Store in memory cache if there's room
        if len(self.computation_cache) < self.max_memory_entries:
            self.computation_cache[cache_key] = z
        
        # Always store in disk cache
        self._save_to_disk(cache_key, z)
        
        # Update LRU cache
        self._get_cached_context_impl.cache_clear()
        self._get_cached_context_impl(cache_key)
        
        return z
    
    def clear_cache(self) -> None:
        """Clear all caches"""
        self.computation_cache.clear()
        self._get_cached_context_impl.cache_clear()
        # Optionally clear disk cache
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.npz"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    print(f"Warning: Failed to delete cache file {cache_file}: {e}")
    
    def precompute_default_context(self, model, env, buffer_data):
        """Pre-compute and cache the default reward context"""
        default_config = {
            'rewards': [
                {
                    'name': 'move-ego',
                    'move_speed': 0.0,
                    'stand_height': 1.4
                }
            ],
            'weights': [1.0]
        }
        
        cache_key = self.get_cache_key(default_config)
        
        # Check if already cached
        if self._get_cached_context_impl(cache_key) is not None:
            print("\nDefault context already cached")
            return
        
        print("\nPre-computing default context...")
        try:
            from reward_context import compute_reward_context
            z = compute_reward_context(default_config, env, model, buffer_data)
            
            # Store in memory cache
            if len(self.computation_cache) < self.max_memory_entries:
                self.computation_cache[cache_key] = z
            
            # Store in disk cache
            self._save_to_disk(cache_key, z)
            
            print("Default context pre-computed and cached successfully")
        except Exception as e:
            print(f"\nWarning: Failed to pre-compute default context: {e}") 