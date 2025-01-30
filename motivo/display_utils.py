import cv2
import numpy as np
from typing import Optional

class DisplayManager:
    def __init__(self, window_name: str = "Humanoid Simulation"):
        self.window_name = window_name
        
    def show_frame(self, 
                   frame: np.ndarray, 
                   q_percentage: Optional[float] = None,
                   is_computing: bool = False,
                   resize_dims: tuple = (320, 240)) -> np.ndarray:
        """
        Display and process a frame with optional overlays
        
        Args:
            frame: Original frame to display
            q_percentage: Quality percentage to display (0-100)
            is_computing: Whether reward computation is in progress
            resize_dims: Dimensions for the saved frame
            
        Returns:
            Resized frame for saving
        """
        # Create a copy to avoid modifying original frame
        display_frame = frame.copy()
        
        # Add Q-value overlay
        if q_percentage is not None:
            cv2.putText(
                display_frame,
                f"Quality: {q_percentage:.1f}%",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )
        
        # Add computing indicator
        if is_computing:
            cv2.putText(
                display_frame,
                "Computing rewards...",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 0),
                1
            )
        
        # Display the frame
        cv2.imshow(self.window_name, cv2.cvtColor(display_frame, cv2.COLOR_RGB2BGR))
        
        # Create resized version for saving
        resized_frame = cv2.resize(frame, resize_dims, interpolation=cv2.INTER_AREA)
        
        return resized_frame
    
    def check_key(self) -> tuple[bool, bool]:
        """
        Check for key presses
        
        Returns:
            Tuple of (should_quit, should_save)
        """
        key = cv2.waitKey(1) & 0xFF
        should_quit = key == 27  # ESC
        should_save = key == ord('s')
        return should_quit, should_save
    
    def cleanup(self):
        """Clean up OpenCV windows"""
        cv2.destroyAllWindows() 