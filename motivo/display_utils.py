import cv2
import numpy as np
from typing import Optional
import os

class DisplayManager:
    def __init__(self, window_name: str = "Humanoid Simulation"):
        self.window_name = window_name
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 800, 600)
        
        # Initialize font
        # Try to load a specific font file if available
        font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSans.ttf')
        if os.path.exists(font_path):
            self.font = cv2.FONT_HERSHEY_DUPLEX  # Fallback to built-in font
        else:
            self.font = cv2.FONT_HERSHEY_SIMPLEX  # Use default font
            
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
        if frame is None:
            return None
            
        try:
            # Ensure frame is in the correct format
            if frame.dtype != np.uint8:
                frame = (frame * 255).astype(np.uint8)
            
            display_frame = frame.copy()
            
            # Convert to BGR if needed
            if len(display_frame.shape) == 3 and display_frame.shape[2] == 3:
                display_frame = cv2.cvtColor(display_frame, cv2.COLOR_RGB2BGR)
            
            # Add Q-value overlay with better visibility
            if q_percentage is not None:
                # Draw text with background for better visibility
                text = f"Quality: {q_percentage:.1f}%"
                font_scale = 0.7
                thickness = 1  # Reduced thickness for better anti-aliasing
                font = self.font
                
                # Get text size
                (text_width, text_height), baseline = cv2.getTextSize(
                    text, font, font_scale, thickness
                )
                
                # Calculate text background rectangle
                padding = 5
                text_x, text_y = 10, 30
                cv2.rectangle(
                    display_frame,
                    (text_x - padding, text_y - text_height - padding),
                    (text_x + text_width + padding, text_y + padding),
                    (0, 0, 0),
                    -1
                )
                
                # Draw text with anti-aliasing
                # First draw slightly thicker black outline for better readability
                cv2.putText(
                    display_frame,
                    text,
                    (text_x, text_y),
                    font,
                    font_scale,
                    (0, 0, 0),
                    thickness + 2,
                    cv2.LINE_AA  # Enable anti-aliasing
                )
                
                # Then draw the white text
                cv2.putText(
                    display_frame,
                    text,
                    (text_x, text_y),
                    font,
                    font_scale,
                    (255, 255, 255),
                    thickness,
                    cv2.LINE_AA  # Enable anti-aliasing
                )
            
            # Add computing indicator with background
            if is_computing:
                text = "Computing rewards..."
                font_scale = 0.6
                thickness = 1  # Reduced thickness
                font = self.font
                
                # Get text size
                (text_width, text_height), baseline = cv2.getTextSize(
                    text, font, font_scale, thickness
                )
                
                # Calculate text background rectangle
                padding = 5
                text_x, text_y = 10, 60
                cv2.rectangle(
                    display_frame,
                    (text_x - padding, text_y - text_height - padding),
                    (text_x + text_width + padding, text_y + padding),
                    (0, 0, 0),
                    -1
                )
                
                # Draw text with anti-aliasing
                # First draw slightly thicker black outline
                cv2.putText(
                    display_frame,
                    text,
                    (text_x, text_y),
                    font,
                    font_scale,
                    (0, 0, 0),
                    thickness + 2,
                    cv2.LINE_AA  # Enable anti-aliasing
                )
                
                # Then draw the yellow text
                cv2.putText(
                    display_frame,
                    text,
                    (text_x, text_y),
                    font,
                    font_scale,
                    (255, 255, 0),  # Yellow text
                    thickness,
                    cv2.LINE_AA  # Enable anti-aliasing
                )
            
            # Display the frame
            cv2.imshow(self.window_name, display_frame)
            
            # Create resized version for saving
            resized_frame = cv2.resize(display_frame, resize_dims, interpolation=cv2.INTER_AREA)
            
            return resized_frame
            
        except Exception as e:
            print(f"Error in show_frame: {str(e)}")
            return None
    
    def check_key(self) -> tuple[bool, bool]:
        """
        Check for key presses
        
        Returns:
            Tuple of (should_quit, should_save)
        """
        try:
            key = cv2.waitKey(1) & 0xFF
            should_quit = key == 27  # ESC
            should_save = key == ord('s')
            return should_quit, should_save
        except Exception as e:
            print(f"Error in check_key: {str(e)}")
            return False, False
    
    def cleanup(self):
        """Clean up OpenCV windows"""
        try:
            cv2.destroyAllWindows()
            for i in range(4):
                cv2.waitKey(1)
        except Exception as e:
            print(f"Error in cleanup: {str(e)}") 