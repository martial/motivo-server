from typing import Union
import numpy as np

def normalize_q_value(q_value: Union[float, np.ndarray], min_q: float = -1000.0, max_q: float = 1000.0) -> float:
    """
    Normalize Q-value to percentage (0-100%)
    
    Args:
        q_value: Raw Q-value or numpy array of Q-values
        min_q: Expected minimum Q-value (-1000 based on observations)
        max_q: Expected maximum Q-value (1000 based on observations)
    
    Returns:
        Normalized value between 0 and 100
    """
    # Clip the value to min/max range
    q_value = np.clip(q_value, min_q, max_q)
    
    # Normalize to 0-1 range
    normalized = (q_value - min_q) / (max_q - min_q)
    
    # Convert to percentage
    percentage = normalized * 100
    
    return float(percentage) 