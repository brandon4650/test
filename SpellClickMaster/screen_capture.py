"""
Screen Capture Module
Handles capturing screenshots of the game for processing
"""
import logging
import numpy as np
import cv2
import os
import platform
import ctypes
from ctypes import windll, c_void_p, Structure, c_long, c_int, byref, c_byte, sizeof
from ctypes.wintypes import DWORD, LONG, WORD, LPVOID, RECT, HWND
logger = logging.getLogger('screen_capture')
# Define the BITMAPINFOHEADER structure
class BITMAPINFOHEADER(Structure):
    _fields_ = [
        ("biSize", DWORD),
        ("biWidth", LONG),
        ("biHeight", LONG),
        ("biPlanes", WORD),
        ("biBitCount", WORD),
        ("biCompression", DWORD),
        ("biSizeImage", DWORD),
        ("biXPelsPerMeter", LONG),
        ("biYPelsPerMeter", LONG),
        ("biClrUsed", DWORD),
        ("biClrImportant", DWORD)
    ]
# Define the BITMAPINFO structure
class BITMAPINFO(Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", DWORD * 3)
    ]
class ScreenCapture:
    """Class for capturing screen images for processing"""
    
    def __init__(self):
        """Initialize the screen capture utility"""
        self.user32 = ctypes.windll.user32
        self.gdi32 = ctypes.windll.gdi32
        self.last_capture = None
        
    def get_screen_size(self):
        """Get the screen dimensions"""
        return (self.user32.GetSystemMetrics(0), self.user32.GetSystemMetrics(1))
    
    def capture_full_screen(self):
        """Capture the entire screen and return as an OpenCV image"""
        try:
            # Get screen dimensions
            width, height = self.get_screen_size()
            
            # Get device context
            hwnd = self.user32.GetDesktopWindow()
            wDC = self.user32.GetWindowDC(hwnd)
            dcObj = self.gdi32.CreateCompatibleDC(wDC)
            
            # Create compatible bitmap
            bmp = self.gdi32.CreateCompatibleBitmap(wDC, width, height)
            self.gdi32.SelectObject(dcObj, bmp)
            
            # Copy screen to bitmap
            self.gdi32.BitBlt(dcObj, 0, 0, width, height, wDC, 0, 0, 0x00CC0020)  # SRCCOPY
            
            # Convert bitmap to numpy array
            bmpInfo = BITMAPINFO()
            bmpInfo.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmpInfo.bmiHeader.biWidth = width
            bmpInfo.bmiHeader.biHeight = -height  # Negative for top-down
            bmpInfo.bmiHeader.biPlanes = 1
            bmpInfo.bmiHeader.biBitCount = 32
            bmpInfo.bmiHeader.biCompression = 0  # BI_RGB
            
            # Create buffer for image data
            size = width * height * 4
            buf = (c_byte * size)()
            
            # Get bitmap bits
            self.gdi32.GetDIBits(dcObj, bmp, 0, height, buf, byref(bmpInfo), 0)
            
            # Convert to numpy array
            arr = np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 4)
            
            # Convert BGRA to BGR for OpenCV
            img = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
            
            # Clean up
            self.gdi32.DeleteObject(bmp)
            self.gdi32.DeleteDC(dcObj)
            self.user32.ReleaseDC(hwnd, wDC)
            
            return img
            
        except Exception as e:
            logger.error(f"Failed to capture screen: {str(e)}", exc_info=True)
            return None
            
    def capture_region(self, region):
        """
        Capture a specific region of the screen
        
        Args:
            region (tuple): (x, y, width, height) of the region to capture
            
        Returns:
            numpy.ndarray: OpenCV image of the captured region or None on failure
        """
        try:
            # Unpack region
            x, y, width, height = region
            
            # Get device context
            hwnd = self.user32.GetDesktopWindow()
            wDC = self.user32.GetWindowDC(hwnd)
            dcObj = self.gdi32.CreateCompatibleDC(wDC)
            
            # Create compatible bitmap
            bmp = self.gdi32.CreateCompatibleBitmap(wDC, width, height)
            self.gdi32.SelectObject(dcObj, bmp)
            
            # Copy screen region to bitmap
            self.gdi32.BitBlt(dcObj, 0, 0, width, height, wDC, x, y, 0x00CC0020)  # SRCCOPY
            
            # Convert bitmap to numpy array
            bmpInfo = BITMAPINFO()
            bmpInfo.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmpInfo.bmiHeader.biWidth = width
            bmpInfo.bmiHeader.biHeight = -height  # Negative for top-down
            bmpInfo.bmiHeader.biPlanes = 1
            bmpInfo.bmiHeader.biBitCount = 32
            bmpInfo.bmiHeader.biCompression = 0  # BI_RGB
            
            # Create buffer for image data
            size = width * height * 4
            buf = (c_byte * size)()
            
            # Get bitmap bits
            self.gdi32.GetDIBits(dcObj, bmp, 0, height, buf, byref(bmpInfo), 0)
            
            # Convert to numpy array
            arr = np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 4)
            
            # Convert BGRA to BGR for OpenCV
            img = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
            
            # Clean up
            self.gdi32.DeleteObject(bmp)
            self.gdi32.DeleteDC(dcObj)
            self.user32.ReleaseDC(hwnd, wDC)
            
            self.last_capture = img
            return img
            
        except Exception as e:
            logger.error(f"Failed to capture region {region}: {str(e)}", exc_info=True)
            return None
            
    def capture_with_margin(self, center_x, center_y, width, height):
        """
        Capture a region centered around a point with given dimensions
        
        Args:
            center_x, center_y: Center coordinates of the region
            width, height: Dimensions of the region
            
        Returns:
            numpy.ndarray: OpenCV image of the captured region
        """
        # Calculate top-left corner
        x = max(0, center_x - width // 2)
        y = max(0, center_y - height // 2)
        
        return self.capture_region((x, y, width, height))