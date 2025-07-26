"""
Основная логика кликов для автокликера
Содержит ClickerEngine класс для управления различными видами кликов
"""

import threading
import time
import os
import pyautogui
from config import *

try:
    import win32api
    import win32con
except ImportError:
    pass

class ClickerEngine:
    """Основной движок для выполнения кликов"""
    
    def __init__(self):
        self.clicking = False
        self.click_thread = None
        self.click_count = 0
        self.paused = False
        
        # Настройки
        self.interval = DEFAULT_INTERVAL
        self.click_type = DEFAULT_CLICK_TYPE
        self.turbo_mode = False
        self.extreme_mode = False
        
        # Режимы кликов
        self.click_mode = CLICK_MODES["NORMAL"]
        
        # Переменные для последовательностей
        self.current_keyboard_index = 0
        self.keyboard_sequence_presses = 0
        self.current_sequence_index = 0
        self.sequence_clicks = 0
        
        # Настройка pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0
        
        # Коллбэки для обновления UI
        self.on_click_callback = None
        self.on_status_change_callback = None
        
    def set_callbacks(self, on_click=None, on_status_change=None):
        """Установка коллбэков для обновления UI"""
        self.on_click_callback = on_click
        self.on_status_change_callback = on_status_change
        
    def start_clicking(self):
        """Запуск кликера"""
        if self.clicking:
            return False
            
        self.clicking = True
        self.click_count = 0
        
        # Сброс переменных последовательностей
        self.current_keyboard_index = 0
        self.keyboard_sequence_presses = 0
        self.current_sequence_index = 0
        self.sequence_clicks = 0
        # Сброс переменных последовательности изображений
        if hasattr(self, 'image_sequence'):
            self.current_image_index = 0
            self.image_sequence_clicks = 0
            self.image_sequence_repeat_count = 0
        
        if self.on_status_change_callback:
            self.on_status_change_callback("running")
            
        self.click_thread = threading.Thread(target=self._click_loop, daemon=True)
        self.click_thread.start()
        return True
        
    def stop_clicking(self):
        """Остановка кликера"""
        if not self.clicking:
            return False
            
        self.clicking = False
        
        if self.on_status_change_callback:
            self.on_status_change_callback("stopped")
            
        if self.click_thread and self.click_thread.is_alive():
            self.click_thread.join(timeout=1.0)
        return True
        
    def pause(self):
        """Пауза кликера"""
        self.paused = True
        
    def resume(self):
        """Возобновление кликера"""
        self.paused = False
        
    def reset_counter(self):
        """Сброс счетчика кликов"""
        self.click_count = 0
        
        # Уведомляем о сбросе
        if self.on_click_callback:
            self.on_click_callback(self.click_count)
            
    def set_interval(self, interval):
        """Установка интервала между кликами"""
        self.interval = max(MIN_INTERVAL, min(MAX_INTERVAL, interval))
        
    def set_click_type(self, click_type):
        """Установка типа клика"""
        if click_type in CLICK_TYPES:
            self.click_type = click_type
            
    def set_turbo_mode(self, enabled):
        """Включение/выключение турбо режима"""
        self.turbo_mode = enabled
        if enabled:
            self.extreme_mode = False
            self.interval = TURBO_INTERVAL
            
    def set_extreme_mode(self, enabled):
        """Включение/выключение экстремального режима"""
        if not WIN32_AVAILABLE:
            return False
            
        self.extreme_mode = enabled
        if enabled:
            self.turbo_mode = False
            self.interval = EXTREME_INTERVAL
        return True
        
    def set_click_mode(self, mode):
        """Установка режима кликов"""
        if mode in CLICK_MODES.values():
            self.click_mode = mode
            
    def set_color_detector(self, color_detector):
        self.color_detector = color_detector

    def set_image_processor(self, image_processor):
        self.image_processor = image_processor

    def set_keyboard_sequence(self, keyboard_sequence):
        self.keyboard_sequence = keyboard_sequence

    def set_sequence_points(self, sequence_points):
        self.sequence_points = sequence_points
        self.current_sequence_index = 0
        self.sequence_clicks = 0

    def set_image_sequence(self, image_sequence):
        self.image_sequence = image_sequence
        self.current_image_index = 0
        self.image_sequence_clicks = 0
        self.image_sequence_repeat_count = 0

    def set_image_sequence_repeats(self, repeats):
        self.image_sequence_repeats = repeats

    def _click_loop(self):
        """Основной цикл кликов"""
        while self.clicking:
            try:
                if self.paused:
                    time.sleep(0.1)
                    continue

                # Выполняем клик в зависимости от режима
                if self.click_mode == CLICK_MODES["COLOR"]:
                    if hasattr(self, 'color_detector'):
                        found = self.color_detector.find_and_click_color(self.click_type)
                        if found:
                            self.click_count += 1
                            if self.on_click_callback:
                                self.on_click_callback(self.click_count)
                elif self.click_mode == CLICK_MODES["IMAGE"]:
                    if hasattr(self, 'image_processor'):
                        # Проверяем, есть ли последовательность изображений
                        if hasattr(self, 'image_sequence') and self.image_sequence:
                            print(f"DEBUG: Найдена последовательность изображений, длина: {len(self.image_sequence)}")
                            print(f"DEBUG: Первый элемент: {self.image_sequence[0] if self.image_sequence else 'Нет элементов'}")
                            # Режим последовательности изображений с поддержкой клавиш
                            if not hasattr(self, 'current_image_index'):
                                self.current_image_index = 0
                            if not hasattr(self, 'image_sequence_clicks'):
                                self.image_sequence_clicks = 0
                            if not hasattr(self, 'image_sequence_repeat_count'):
                                self.image_sequence_repeat_count = 0
                                
                            current_item = self.image_sequence[self.current_image_index]
                            
                            # Обрабатываем клавиши
                            if current_item.get('type') == 'key':
                                # Нажимаем клавишу
                                key = current_item['key']
                                presses = current_item['presses']
                                
                                import pyautogui
                                import keyboard
                                
                                for _ in range(presses):
                                    try:
                                        keyboard.press_and_release(key)
                                        time.sleep(0.1)  # Небольшая пауза между нажатиями
                                    except Exception as e:
                                        print(f"Ошибка нажатия клавиши {key}: {e}")
                                
                                # Переходим к следующему элементу
                                self.current_image_index = (self.current_image_index + 1) % len(self.image_sequence)
                                
                                # Если прошли всю последовательность
                                if self.current_image_index == 0:
                                    self.image_sequence_repeat_count += 1
                                    
                                    # Проверяем, нужно ли остановиться
                                    max_repeats = getattr(self, 'image_sequence_repeats', 1)
                                    if max_repeats > 0 and self.image_sequence_repeat_count >= max_repeats:
                                        # Останавливаем кликер после завершения последовательности
                                        self.stop_clicking()
                                        continue
                                
                                self.click_count += 1
                                if self.on_click_callback:
                                    self.on_click_callback(self.click_count)
                            
                            # Обрабатываем шаблоны изображений
                            else:
                                # Проверяем существование файла шаблона
                                template_path = current_item.get('path')
                                if not template_path or not os.path.exists(template_path):
                                    print(f"Файл шаблона не найден: {template_path}")
                                    # Переходим к следующему элементу
                                    self.current_image_index = (self.current_image_index + 1) % len(self.image_sequence)
                                    continue
                                
                                # Пытаемся найти и кликнуть по текущему шаблону
                                found = self.image_processor.find_and_click_image(template_path=template_path, click_type=self.click_type)
                                if found:
                                    self.image_sequence_clicks += 1
                                    self.click_count += 1
                                    if self.on_click_callback:
                                        self.on_click_callback(self.click_count)
                                    
                                    # Проверяем, достигли ли нужного количества кликов
                                    if self.image_sequence_clicks >= current_item.get('clicks', 1):
                                        self.image_sequence_clicks = 0
                                        self.current_image_index = (self.current_image_index + 1) % len(self.image_sequence)
                                        
                                        # Если прошли всю последовательность
                                        if self.current_image_index == 0:
                                            self.image_sequence_repeat_count += 1
                                            
                                            # Проверяем, нужно ли остановиться
                                            max_repeats = getattr(self, 'image_sequence_repeats', 1)
                                            if max_repeats > 0 and self.image_sequence_repeat_count >= max_repeats:
                                                # Останавливаем кликер после завершения последовательности
                                                self.stop_clicking()
                                                continue
                                else:
                                    # Если изображение не найдено, делаем небольшую паузу
                                    time.sleep(0.05)
                        else:
                            # Обычный режим поиска изображений
                            template_path = getattr(self.image_processor, 'current_template', None)
                            found = self.image_processor.find_and_click_image(template_path=template_path, click_type=self.click_type)
                            if found:
                                self.click_count += 1
                                if self.on_click_callback:
                                    self.on_click_callback(self.click_count)
                            else:
                                # Если изображение не найдено, делаем небольшую паузу
                                time.sleep(0.05)
                elif self.click_mode == CLICK_MODES["KEYBOARD"]:
                    if hasattr(self, 'keyboard_sequence') and self.keyboard_sequence:
                        import pyautogui
                        
                        current_key_entry = self.keyboard_sequence[self.current_keyboard_index]
                        
                        try:
                            # Нажимаем клавишу
                            key = current_key_entry['key']
                            
                            # Преобразуем некоторые клавиши для pyautogui
                            key_mapping = {
                                'enter': 'enter',
                                'esc': 'escape', 
                                'space': 'space',
                                'tab': 'tab',
                                'shift': 'shift',
                                'ctrl': 'ctrl',
                                'alt': 'alt',
                                'backspace': 'backspace',
                                'delete': 'delete',
                                'home': 'home',
                                'end': 'end',
                                'page_up': 'pageup',
                                'page_down': 'pagedown',
                                'up': 'up',
                                'down': 'down',
                                'left': 'left',
                                'right': 'right',
                                'insert': 'insert',
                                'caps_lock': 'capslock'
                            }
                            
                            # Функциональные клавиши
                            if key.startswith('f') and len(key) >= 2:
                                try:
                                    num = int(key[1:])
                                    if 1 <= num <= 12:
                                        key = f'f{num}'
                                except:
                                    pass
                                    
                            # Цифровая клавиатура
                            if key.startswith('num_'):
                                suffix = key[4:]
                                if suffix.isdigit():
                                    key = f'num{suffix}'
                                elif suffix == 'enter':
                                    key = 'numpadenter'
                                elif suffix == 'plus':
                                    key = 'add'
                                elif suffix == 'minus':
                                    key = 'subtract'
                            
                            # Применяем маппинг
                            key = key_mapping.get(key, key)
                            
                            pyautogui.press(key)
                            self.keyboard_sequence_presses += 1
                            self.click_count += 1
                            
                            if self.on_click_callback:
                                self.on_click_callback(self.click_count)
                            
                            # Проверяем, достигли ли нужного количества нажатий
                            if self.keyboard_sequence_presses >= current_key_entry['presses']:
                                self.keyboard_sequence_presses = 0
                                self.current_keyboard_index = (self.current_keyboard_index + 1) % len(self.keyboard_sequence)
                                
                        except Exception as e:
                            print(f"Ошибка нажатия клавиши {current_key_entry['key']}: {e}")
                            return False
                elif self.click_mode == CLICK_MODES["SEQUENCE"]:
                    if hasattr(self, 'sequence_points') and self.sequence_points:
                        point = self.sequence_points[self.current_sequence_index]
                        import pyautogui
                        pyautogui.click(point['x'], point['y'], button=self.click_type)
                        self.sequence_clicks += 1
                        if self.sequence_clicks >= point.get('clicks', 1):
                            self.sequence_clicks = 0
                            self.current_sequence_index = (self.current_sequence_index + 1) % len(self.sequence_points)
                        self.click_count += 1
                        if self.on_click_callback:
                            self.on_click_callback(self.click_count)
                else:  # NORMAL
                    self._perform_normal_click()

                # Задержка между кликами
                if self.interval > 0:
                    time.sleep(self.interval)

            except Exception as e:
                print(f"Ошибка в цикле кликов: {e}")
                self.stop_clicking()
                break
                
    def _perform_normal_click(self):
        """Выполнение обычного клика в текущей позиции мыши"""
        try:
            if self.extreme_mode and WIN32_AVAILABLE:
                self._extreme_click()
            else:
                self._regular_click()
                
            self.click_count += 1
            if self.on_click_callback:
                self.on_click_callback(self.click_count)
                
        except Exception as e:
            print(f"Ошибка при выполнении клика: {e}")
            
    def _regular_click(self):
        """Обычный клик через pyautogui"""
        if self.click_type == "left":
            pyautogui.click()
        elif self.click_type == "right":
            pyautogui.rightClick()
        elif self.click_type == "middle":
            pyautogui.middleClick()
            
    def _extreme_click(self):
        """Экстремальный клик через win32api"""
        if not WIN32_AVAILABLE:
            return self._regular_click()
            
        x, y = pyautogui.position()
        
        if self.click_type == "left":
            win32api.SetCursorPos((x, y))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
        elif self.click_type == "right":
            win32api.SetCursorPos((x, y))
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x, y, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x, y, 0, 0)
        elif self.click_type == "middle":
            win32api.SetCursorPos((x, y))
            win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, x, y, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, x, y, 0, 0)
            
    def click_at_position(self, x, y):
        """Клик в определенной позиции"""
        try:
            current_x, current_y = pyautogui.position()
            
            if self.extreme_mode and WIN32_AVAILABLE:
                win32api.SetCursorPos((x, y))
                if self.click_type == "left":
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
                elif self.click_type == "right":
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x, y, 0, 0)
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x, y, 0, 0)
                elif self.click_type == "middle":
                    win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, x, y, 0, 0)
                    win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, x, y, 0, 0)
            else:
                if self.click_type == "left":
                    pyautogui.click(x, y)
                elif self.click_type == "right":
                    pyautogui.rightClick(x, y)
                elif self.click_type == "middle":
                    pyautogui.middleClick(x, y)
                    
            self.click_count += 1
            if self.on_click_callback:
                self.on_click_callback(self.click_count)
                
        except Exception as e:
            print(f"Ошибка при клике в позиции ({x}, {y}): {e}")
            
    def is_running(self):
        """Проверка, запущен ли кликер"""
        return self.clicking
        
    def get_click_count(self):
        """Получение количества кликов"""
        return self.click_count 