"""
Keyboard Controller Module
Handles keyboard automation for casting spells
"""
import time
import logging
import pyautogui

logger = logging.getLogger('keyboard_controller')

class KeyboardController:
    """Class for simulating keyboard input to activate spells"""
    
    def __init__(self):
        """Initialize the keyboard controller"""
        # Set a small pause between PyAutoGUI actions for stability
        pyautogui.PAUSE = 0.05
        
        # Disable fail-safe by default (can be enabled in settings)
        pyautogui.FAILSAFE = False
        
        self.last_key_press = 0
        self.minimum_interval = 0.1  # Minimum time between key presses in seconds
        
    def press_key(self, key):
        """
        Press a keyboard key
        
        Args:
            key (str): The key to press (e.g., 'a', '1', 'shift', etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Ensure we don't press keys too rapidly
        current_time = time.time()
        time_since_last = current_time - self.last_key_press
        
        if time_since_last < self.minimum_interval:
            time.sleep(self.minimum_interval - time_since_last)
        
        try:
            pyautogui.press(key)
            self.last_key_press = time.time()
            logger.debug(f"Key pressed: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to press key {key}: {str(e)}", exc_info=True)
            return False
            
    def press_key_combination(self, keys):
        """
        Press a combination of keys simultaneously
        
        Args:
            keys (list): List of keys to press together (e.g., ['ctrl', 'c'])
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not keys:
            return False
            
        # Ensure we don't press keys too rapidly
        current_time = time.time()
        time_since_last = current_time - self.last_key_press
        
        if time_since_last < self.minimum_interval:
            time.sleep(self.minimum_interval - time_since_last)
            
        try:
            # For multiple keys, use hotkey function
            if len(keys) > 1:
                pyautogui.hotkey(*keys)
            else:
                pyautogui.press(keys[0])
                
            self.last_key_press = time.time()
            logger.debug(f"Key combination pressed: {keys}")
            return True
        except Exception as e:
            logger.error(f"Failed to press key combination {keys}: {str(e)}", exc_info=True)
            return False
            
    def set_minimum_interval(self, interval):
        """
        Set the minimum interval between key presses
        
        Args:
            interval (float): Minimum time in seconds between key presses
        """
        if interval > 0:
            self.minimum_interval = interval
            logger.debug(f"Minimum key press interval set to {interval}s")
