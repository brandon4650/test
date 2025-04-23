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
        pyautogui.PAUSE = 0.03  # Reduced from 0.05 to 0.03 for faster reactions
        
        # Disable fail-safe by default (can be enabled in settings)
        pyautogui.FAILSAFE = False
        
        self.last_key_press = 0
        self.minimum_interval = 0.05  # Reduced from 0.1 to 0.05 seconds for faster reactions
        
    def press_key(self, key):
        """Press a keyboard key using direct methods for better game compatibility"""
        # Ensure we don't press keys too rapidly
        current_time = time.time()
        time_since_last = current_time - self.last_key_press
        
        if time_since_last < self.minimum_interval:
            time.sleep(self.minimum_interval - time_since_last)
        
        # Find and focus WoW window
        wow_hwnd = self.find_wow_window()
        if not wow_hwnd:
            logger.warning("Could not find WoW window")
        
        logger.info(f"Attempting to press key: {key}")
        
        try:
            # Check if this is a key combination with a modifier
            if '+' in key:
                parts = key.lower().split('+')
                logger.info(f"Detected key combination: {parts}")
                
                # Try direct input to WoW window
                if wow_hwnd:
                    try:
                        import win32api
                        import win32con
                        
                        # Simulate direct key input to the window
                        vk_codes = {
                            'alt': win32con.VK_MENU,
                            '3': 0x33  # Virtual key code for '3'
                        }
                        
                        # Send the keys to the WoW window
                        win32api.SendMessage(wow_hwnd, win32con.WM_KEYDOWN, vk_codes['alt'], 0)
                        time.sleep(0.05)
                        win32api.SendMessage(wow_hwnd, win32con.WM_KEYDOWN, vk_codes['3'], 0)
                        time.sleep(0.1)
                        win32api.SendMessage(wow_hwnd, win32con.WM_KEYUP, vk_codes['3'], 0)
                        time.sleep(0.05)
                        win32api.SendMessage(wow_hwnd, win32con.WM_KEYUP, vk_codes['alt'], 0)
                        
                        logger.info("Keys sent directly to WoW window")
                        self.last_key_press = time.time()
                        return True
                    except Exception as e:
                        logger.error(f"Error sending keys to WoW: {str(e)}")
                        # Fall back to PyAutoGUI if direct method fails
                
                # Fall back to PyAutoGUI
                # Hold keys longer and add small delays
                try:
                    # Press down modifier keys
                    for modifier in parts[:-1]:
                        logger.info(f"Pressing down modifier: {modifier}")
                        pyautogui.keyDown(modifier)
                        time.sleep(0.1)  # Longer delay
                    
                    # Press the final key
                    logger.info(f"Pressing key: {parts[-1]}")
                    pyautogui.keyDown(parts[-1])
                    time.sleep(0.2)  # Hold down longer (200ms)
                    pyautogui.keyUp(parts[-1])
                    time.sleep(0.1)
                    
                    # Release modifier keys in reverse order
                    for modifier in reversed(parts[:-1]):
                        logger.info(f"Releasing modifier: {modifier}")
                        pyautogui.keyUp(modifier)
                        time.sleep(0.1)
                        
                    logger.info(f"Key combination pressed successfully: {key}")
                except Exception as e:
                    logger.error(f"PyAutoGUI method failed: {str(e)}")
                    return False
            else:
                pyautogui.press(key)
                logger.info(f"Key pressed: {key}")
                    
            self.last_key_press = time.time()
            return True
        except Exception as e:
            logger.error(f"Failed to press key {key}: {str(e)}", exc_info=True)
            return False

    def find_wow_window(self):
        """Find the World of Warcraft window handle"""
        try:
            import win32gui
            
            def callback(hwnd, hwnds):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if "World of Warcraft" in title or "WoW" in title:
                        hwnds.append(hwnd)
                return True
            
            hwnds = []
            win32gui.EnumWindows(callback, hwnds)
            
            if hwnds:
                return hwnds[0]
            return None
        except Exception as e:
            logger.error(f"Error finding WoW window: {str(e)}")
            return None
            
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
        
        # Ensure game window has focus
        self.ensure_game_focus()
            
        try:
            logger.info(f"Attempting key combination: {keys}")
            
            # For multiple keys, use more reliable approach
            if len(keys) > 1:
                # Press down all modifier keys
                for i in range(len(keys) - 1):
                    pyautogui.keyDown(keys[i])
                    logger.info(f"Pressed down: {keys[i]}")
                    
                # Press and release the final key
                pyautogui.press(keys[-1])
                logger.info(f"Pressed and released: {keys[-1]}")
                
                # Release all modifier keys in reverse order
                for i in range(len(keys) - 2, -1, -1):
                    pyautogui.keyUp(keys[i])
                    logger.info(f"Released: {keys[i]}")
            else:
                pyautogui.press(keys[0])
                logger.info(f"Single key pressed: {keys[0]}")
                
            self.last_key_press = time.time()
            logger.info(f"Key combination pressed: {keys}")
            return True
        except Exception as e:
            logger.error(f"Failed to press key combination {keys}: {str(e)}", exc_info=True)
            # Try to release any potentially stuck keys
            try:
                for key in keys:
                    pyautogui.keyUp(key)
            except:
                pass
            return False
            
    def set_minimum_interval(self, interval):
        """
        Set the minimum interval between key presses
        
        Args:
            interval (float): Minimum time in seconds between key presses
        """
        if interval > 0:
            self.minimum_interval = interval
            logger.info(f"Minimum key press interval set to {interval}s")
            
    def ensure_game_focus(self):
        """Make sure the game window has focus before pressing keys"""
        try:
            # Try to use win32gui if available (Windows only)
            try:
                import win32gui
                import win32con
                
                # Find windows with common game names
                game_titles = [
                    "World of Warcraft", 
                    "WoW",
                    "Blizzard"
                ]
                
                for title in game_titles:
                    wow_window = win32gui.FindWindow(None, title)
                    if wow_window:
                        # Check if the window is minimized
                        if win32gui.IsIconic(wow_window):
                            win32gui.ShowWindow(wow_window, win32con.SW_RESTORE)
                            time.sleep(0.1)  # Small delay for window to restore
                            
                        # Bring window to front
                        win32gui.SetForegroundWindow(wow_window)
                        time.sleep(0.05)  # Small delay for focus to take effect
                        return True
                        
                # If specific window not found, at least make sure our app isn't focused
                # on some dialog that would prevent keystrokes from reaching the game
                foreground_window = win32gui.GetForegroundWindow()
                foreground_title = win32gui.GetWindowText(foreground_window)
                if "spell" in foreground_title.lower() or "config" in foreground_title.lower():
                    # Our app window is in focus, try to alt-tab to game
                    pyautogui.keyDown('alt')
                    pyautogui.press('tab')
                    pyautogui.keyUp('alt')
                    time.sleep(0.1)
                
            except ImportError:
                # win32gui not available, use alternative method
                pass
                
            return True
        except Exception as e:
            logger.warning(f"Failed to ensure game focus: {str(e)}")
            return False
            
    def release_all_keys(self):
        """
        Release all potentially pressed keys to avoid stuck keys
        """
        try:
            # Common keys that might be stuck
            keys_to_release = [
                'alt', 'ctrl', 'shift', 'win', 
                'tab', 'escape', 'space',
                '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
                '-', '=', 'backspace'
            ]
            
            for key in keys_to_release:
                try:
                    pyautogui.keyUp(key)
                except:
                    pass
                    
            logger.info("All keys released")
            return True
        except Exception as e:
            logger.error(f"Error releasing keys: {str(e)}")
            return False