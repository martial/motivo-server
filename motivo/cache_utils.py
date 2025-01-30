import json
from typing import Dict, Any
import asyncio
from datetime import datetime

class RewardContextCache:
    def __init__(self):
        self.computation_cache = {}
    
    def get_cache_key(self, reward_config: Dict[str, Any]) -> str:
        """Generate a consistent cache key for a reward configuration"""
        unique_rewards = []
        seen_configs = set()
        
        for reward in reward_config['rewards']:
            # Create a normalized reward config string
            reward_config_str = json.dumps({
                'name': reward['name'],
                **{k: v for k, v in reward.items() 
                   if k not in ['id', 'name'] and not isinstance(v, (dict, list))}
            }, sort_keys=True)
            
            if reward_config_str not in seen_configs:
                seen_configs.add(reward_config_str)
                unique_rewards.append(json.loads(reward_config_str))
        
        # Create final cache key with unique rewards only
        return json.dumps({
            'params': sorted(unique_rewards, key=lambda x: (x['name'], json.dumps(x, sort_keys=True))),
            'combinationType': reward_config.get('combinationType', 'multiplicative')
        }, sort_keys=True)
    
    async def get_cached_context(self, reward_config: Dict[str, Any], compute_fn) -> Any:
        """Get context from cache or compute new one"""
        params_key = self.get_cache_key(reward_config)
        
        print("\n=== Cache Debug Info ===")
        print(f"Generated cache key: {params_key}")
        print(f"Computation cache keys: {list(self.computation_cache.keys())}")
        print(f"Cache hit? {'Yes' if params_key in self.computation_cache else 'No'}")
        
        if params_key in self.computation_cache:
            print("\nUSING CACHED COMPUTATION ✓")
            return self.computation_cache[params_key]
        else:
            print("\nCOMPUTING NEW CONTEXT ⚙️")
            z = await compute_fn(reward_config)
            self.computation_cache[params_key] = z
            return z 