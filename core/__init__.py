"""
Core модули автокликера
Содержит основную логику работы приложения
"""

from .clicker import ClickerEngine
from .hotkeys import HotkeyManager  
from .color_detection import ColorDetector
from .image_processing import ImageProcessor

__all__ = [
    'ClickerEngine',
    'HotkeyManager', 
    'ColorDetector',
    'ImageProcessor'
] 