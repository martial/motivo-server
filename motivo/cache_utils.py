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
        current_rewards = reward_config['rewards']
        
        def compare_rewards_ignoring_id(r1, r2):
            """Compare two rewards ignoring their IDs"""
            r1_copy = r1.copy()
            r2_copy = r2.copy()
            # Remove IDs before comparison
            r1_copy.pop('id', None)
            r2_copy.pop('id', None)
            return r1_copy == r2_copy
        
        # Check if we have an exact match in the cache
        for cached_key in self.computation_cache:
            cached_config = json.loads(cached_key)
            cached_rewards = cached_config['rewards']
            
            if (len(current_rewards) == len(cached_rewards) and 
                all(compare_rewards_ignoring_id(r1, r2) 
                    for r1, r2 in zip(sorted(current_rewards, key=lambda x: x['name']), 
                                    sorted(cached_rewards, key=lambda x: x['name'])))):
                print("\nUSING CACHED COMPUTATION - Exact match (ignoring IDs) ✓")
                return self.computation_cache[cached_key]
        
        print("\nCOMPUTING NEW CONTEXT - Different configuration ⚙️")
        z = await compute_fn(reward_config)
        # Store in cache without IDs
        cache_config = {
            'rewards': [{k: v for k, v in r.items() if k != 'id'} 
                       for r in reward_config['rewards']],
            'combinationType': reward_config.get('combinationType', 'multiplicative')
        }
        cache_key = json.dumps(cache_config, sort_keys=True)
        self.computation_cache[cache_key] = z
        return z 