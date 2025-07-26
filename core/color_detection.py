"""
Модуль для обнаружения и поиска цветов на экране
Содержит ColorDetector класс для работы с цветовым кликингом
"""

import pyautogui
from PIL import Image
import threading
import time
from config import *

class ColorDetector:
    """Класс для обнаружения цветов на экране"""
    
    def __init__(self):
        self.target_color = DEFAULT_COLOR
        self.tolerance = DEFAULT_COLOR_TOLERANCE
        self.search_area = None  # (x1, y1, x2, y2)
        
        # Оптимизация поиска
        self.last_found_position = None
        self.last_target_color = None
        self.last_tolerance = None
        self.clicks_since_last_search = 0
        self.recheck_interval = DEFAULT_RECHECK_INTERVAL
        
        # Коллбэки
        self.on_color_found_callback = None
        self.on_color_not_found_callback = None
        
    def set_callbacks(self, on_found=None, on_not_found=None):
        """Установка коллбэков для результатов поиска"""
        self.on_color_found_callback = on_found
        self.on_color_not_found_callback = on_not_found
        
    def set_target_color(self, color_hex):
        """Установка целевого цвета в формате #RRGGBB"""
        self.target_color = color_hex
        self._invalidate_cache()
        
    def set_tolerance(self, tolerance):
        """Установка допустимого отклонения цвета (0-100)"""
        self.tolerance = max(0, min(100, tolerance))
        self._invalidate_cache()
        
    def set_search_area(self, x1, y1, x2, y2):
        """Установка области поиска"""
        self.search_area = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        self._invalidate_cache()
        
    def clear_search_area(self):
        """Очистка области поиска (поиск по всему экрану)"""
        self.search_area = None
        self._invalidate_cache()
        
    def _invalidate_cache(self):
        """Сброс кэша для принудительного нового поиска"""
        self.last_found_position = None
        self.last_target_color = None
        self.last_tolerance = None
        self.clicks_since_last_search = 0
        
    def hex_to_rgb(self, hex_color):
        """Конвертация HEX цвета в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
    def color_matches(self, pixel_color, target_color):
        """Проверка соответствия цвета с учетом толерантности"""
        target_rgb = self.hex_to_rgb(target_color) if isinstance(target_color, str) else target_color
        pixel_rgb = pixel_color[:3] if len(pixel_color) > 3 else pixel_color
        
        # Вычисляем разность по каждому каналу
        diff = sum(abs(p - t) for p, t in zip(pixel_rgb, target_rgb))
        max_diff = 3 * 255 * (self.tolerance / 100.0)
        
        return diff <= max_diff
        
    def find_color_position(self, use_cache: bool = True) -> tuple:
        """
        Поиск позиции цвета на экране
        
        Args:
            use_cache: Использовать кэширование
            
        Returns:
            tuple: (найдено, (x, y)) или (False, None)
        """
        try:
            # Проверяем кэш если разрешено
            if use_cache and self._can_use_cache():
                return True, self.last_found_position
                
            # Выполняем поиск
            found, position = self._search_color_in_image()
            
            # Обновляем кэш
            if found:
                self._update_cache(position)
                return True, position
            else:
                self.last_found_position = None
                return False, None
                
        except Exception as e:
            print(f"Ошибка поиска цвета: {e}")
            if 'on_error' in self.callbacks:
                self.callbacks['on_error'](f"Ошибка поиска цвета: {e}")
            return False, None
            
    def find_and_click_color(self, click_type: str = "left") -> bool:
        """
        Поиск и клик по цвету (с оптимизацией)
        
        Args:
            click_type: Тип клика ("left", "right", "middle")
            
        Returns:
            bool: Успешность операции
        """
        try:
            # Если пользователь недавно был активен — сбрасываем позицию
            if hasattr(self, 'user_activity_detected') and self.user_activity_detected:
                self.last_found_position = None
                self.user_activity_detected = False
            
            # Проверяем, изменились ли настройки цвета
            if (self.last_target_color != self.target_color or 
                self.last_tolerance != self.tolerance):
                # Настройки изменились, нужно искать заново
                self.last_found_position = None
                self._invalidate_cache()
            
            # Если позиция уже найдена — кликаем по ней
            if self.last_found_position:
                # Периодически проверяем, что цвет еще там
                self.clicks_since_last_search += 1
                if self.clicks_since_last_search >= self.recheck_interval:
                    # Время для перепроверки
                    found, pos = self._search_color_in_image()
                    if found:
                        self.last_found_position = pos
                        self.clicks_since_last_search = 0
                        self._update_cache(pos)
                    else:
                        # Цвет исчез, сбрасываем позицию
                        self.last_found_position = None
                        self.clicks_since_last_search = 0
                        return False
                
                # Выполняем клик
                import pyautogui
                pyautogui.click(self.last_found_position, button=click_type)
                
                # Вызываем коллбэк успешного клика
                if 'on_click_success' in self.callbacks:
                    self.callbacks['on_click_success'](self.last_found_position)
                    
                return True
            
            # Иначе ищем цвет
            found, pos = self._search_color_in_image()
            if found:
                self.last_found_position = pos
                self.clicks_since_last_search = 0
                self._update_cache(pos)
                
                # Выполняем клик
                import pyautogui
                pyautogui.click(pos, button=click_type)
                
                # Вызываем коллбэк успешного клика
                if 'on_click_success' in self.callbacks:
                    self.callbacks['on_click_success'](pos)
                    
                return True
            else:
                self.last_found_position = None
                if 'on_click_failed' in self.callbacks:
                    self.callbacks['on_click_failed']("Цвет не найден")
                return False
                
        except Exception as e:
            print(f"Ошибка при поиске и клике по цвету: {e}")
            if 'on_error' in self.callbacks:
                self.callbacks['on_error'](f"Ошибка клика по цвету: {e}")
            return False
            
    def _search_color_in_image(self) -> tuple:
        """
        Ищет цвет на экране и возвращает (найдено, позиция)
        
        Returns:
            tuple: (True, (x, y)) или (False, None)
        """
        try:
            import pyautogui
            
            # Определяем область поиска
            if self.search_area:
                x1, y1, x2, y2 = self.search_area
                screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
                offset_x, offset_y = x1, y1
            else:
                screenshot = pyautogui.screenshot()
                offset_x, offset_y = 0, 0
            
            # Преобразуем цель в RGB
            target_rgb = self.hex_to_rgb(self.target_color)
            
            # Поиск пикселя (оптимизированный алгоритм)
            width, height = screenshot.size
            step = max(1, min(width, height) // 100)  # Адаптивный шаг поиска
            
            for x in range(0, width, step):
                for y in range(0, height, step):
                    pixel = screenshot.getpixel((x, y))
                    if self.color_matches(pixel, target_rgb):
                        click_x = x + offset_x
                        click_y = y + offset_y
                        return True, (click_x, click_y)
                        
            return False, None
            
        except Exception as e:
            print(f"Ошибка при поиске цвета в изображении: {e}")
            return False, None
            
    def _find_exact_position(self, pixel_rgb: tuple) -> tuple:
        """
        Поиск точной позиции цвета (детальный поиск)
        
        Args:
            pixel_rgb: RGB цвет для поиска
            
        Returns:
            tuple: (найдено, (x, y)) или (False, None)
        """
        try:
            import pyautogui
            
            # Определяем область детального поиска
            if self.search_area:
                x1, y1, x2, y2 = self.search_area
                screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
                offset_x, offset_y = x1, y1
            else:
                screenshot = pyautogui.screenshot()
                offset_x, offset_y = 0, 0
            
            width, height = screenshot.size
            
            # Детальный поиск пиксель за пикселем
            for x in range(width):
                for y in range(height):
                    pixel = screenshot.getpixel((x, y))
                    if self.color_matches(pixel, pixel_rgb):
                        return True, (x + offset_x, y + offset_y)
                        
            return False, None
            
        except Exception as e:
            print(f"Ошибка детального поиска цвета: {e}")
            return False, None
            
    def reset_search_cache(self):
        """Сброс кэша поиска"""
        self.last_found_position = None
        self.clicks_since_last_search = 0
        self.last_target_color = None
        self.last_tolerance = None
        self.last_search_time = 0
        
    def set_user_activity_detected(self, detected: bool):
        """Установка флага активности пользователя"""
        self.user_activity_detected = detected
        if detected:
            self.reset_search_cache()
            
    def pick_color_at_position(self, x, y):
        """Получение цвета в определенной позиции экрана"""
        try:
            pixel = pyautogui.pixel(x, y)
            # Конвертируем RGB в HEX
            return f"#{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}"
        except Exception as e:
            print(f"Ошибка при получении цвета в позиции ({x}, {y}): {e}")
            return None
            
    def get_search_area_info(self):
        """Получение информации об области поиска"""
        if not self.search_area:
            return "Весь экран"
            
        x1, y1, x2, y2 = self.search_area
        width = x2 - x1
        height = y2 - y1
        return f"Область: {x1},{y1} - {x2},{y2} ({width}x{height})" 