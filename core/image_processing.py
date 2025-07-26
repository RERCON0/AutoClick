"""
Модуль для обработки изображений и поиска шаблонов
Содержит ImageProcessor класс для работы с поиском изображений на экране
"""

import pyautogui
import os
import uuid
from PIL import Image
import threading
import time
from config import *

class ImageProcessor:
    """Класс для обработки изображений и поиска шаблонов"""
    
    def __init__(self):
        self.confidence = DEFAULT_IMAGE_CONFIDENCE
        self.search_area = None  # (x1, y1, x2, y2)
        
        # Кэширование для оптимизации
        self.last_found_position = None
        self.last_template_path = None
        self.clicks_since_last_search = 0
        self.recheck_interval = DEFAULT_RECHECK_INTERVAL
        
        # Последовательности изображений
        self.image_sequence = []
        self.current_image_index = 0
        self.image_sequence_clicks = 0
        self.image_sequence_repeats = 1
        self.image_sequence_repeat_count = 0
        
        # Коллбэки
        self.on_image_found_callback = None
        self.on_image_not_found_callback = None
        self.on_sequence_complete_callback = None
        
        self.current_template = None
        self.callbacks = {}
        
    def set_callbacks(self, on_found=None, on_not_found=None, on_sequence_complete=None):
        self.callbacks = {}
        if on_found:
            self.callbacks['on_found'] = on_found
        if on_not_found:
            self.callbacks['on_not_found'] = on_not_found
        if on_sequence_complete:
            self.callbacks['on_sequence_complete'] = on_sequence_complete
        
    def set_confidence(self, confidence):
        """Установка уровня точности поиска (0.0 - 1.0)"""
        self.confidence = max(0.0, min(1.0, confidence))
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
        self.last_template_path = None
        self.clicks_since_last_search = 0
        
    def find_image_position(self, template_path: str, use_cache: bool = True) -> tuple:
        """
        Поиск позиции изображения на экране
        
        Args:
            template_path: Путь к шаблону изображения
            use_cache: Использовать кэширование
            
        Returns:
            tuple: (найдено, (x, y)) или (False, None)
        """
        try:
            # Проверяем существование файла
            if not template_path or not os.path.exists(template_path):
                if 'on_error' in self.callbacks:
                    self.callbacks['on_error'](f"Файл шаблона не найден: {template_path}")
                return False, None
                
            # Проверяем кэш если разрешено
            if use_cache and self._can_use_cache(template_path):
                return True, self.last_found_position
                
            # Выполняем поиск
            found, position = self._search_image_in_screen(template_path)
            
            # Обновляем кэш
            if found:
                self._update_cache(template_path, position)
                return True, position
            else:
                self.last_found_position = None
                return False, None
                
        except Exception as e:
            print(f"Ошибка поиска изображения: {e}")
            if 'on_error' in self.callbacks:
                self.callbacks['on_error'](f"Ошибка поиска изображения: {e}")
            return False, None
            
    def find_and_click_image(self, template_path: str = None, click_type: str = "left") -> bool:
        """
        Поиск и клик по изображению (с оптимизацией)
        
        Args:
            template_path: Путь к шаблону (если None, используется текущий)
            click_type: Тип клика ("left", "right", "middle")
            
        Returns:
            bool: Успешность операции
        """
        try:
            # Если путь не указан, используем текущий шаблон
            if not template_path:
                template_path = self.current_template
                
            # Проверяем существование шаблона
            if not template_path or not os.path.exists(template_path):
                # Если есть область поиска — создаём шаблон автоматически
                if self.search_area:
                    new_template = self._create_template_from_search_area()
                    if new_template:
                        template_path = new_template
                        self.current_template = new_template
                        print(f"Автоматически создан шаблон из области поиска: {new_template}")
                    else:
                        print("Не удалось создать шаблон из области поиска")
                        return False
                else:
                    # Пытаемся найти временный шаблон автоматически
                    template_path = self._find_temp_template()
                    if not template_path:
                        print("Шаблон не выбран или файл не найден")
                        return False
                        
            # Если пользователь недавно был активен — сбрасываем позицию
            if hasattr(self, 'user_activity_detected') and self.user_activity_detected:
                self.last_found_position = None
                self.user_activity_detected = False
                
            # Если позиция уже найдена и шаблон не менялся — кликаем по ней
            if (self.last_found_position and 
                self.last_template_path == template_path):
                # Периодически проверяем, что картинка еще там
                self.clicks_since_last_search += 1
                if self.clicks_since_last_search >= self.recheck_interval:
                    # Время для перепроверки
                    found, pos = self._search_image_in_screen(template_path)
                    if found:
                        self.last_found_position = pos
                        self.clicks_since_last_search = 0
                        self._update_cache(template_path, pos)
                    else:
                        # Картинка исчезла, сбрасываем позицию
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
                
            # Иначе ищем изображение
            found, pos = self._search_image_in_screen(template_path)
            if found:
                self.last_found_position = pos
                self.last_template_path = template_path
                self.clicks_since_last_search = 0
                self._update_cache(template_path, pos)
                
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
                    self.callbacks['on_click_failed']("Изображение не найдено")
                return False
                
        except Exception as e:
            print(f"Ошибка при поиске и клике по изображению: {e}")
            if 'on_error' in self.callbacks:
                self.callbacks['on_error'](f"Ошибка клика по изображению: {e}")
            return False
            
    def _search_image_in_screen(self, template_path: str) -> tuple:
        """
        Поиск изображения на экране
        
        Args:
            template_path: Путь к шаблону
            
        Returns:
            tuple: (True, (x, y)) или (False, None)
        """
        try:
            import pyautogui
            
            # Определяем область поиска
            region = None
            if self.search_area:
                x1, y1, x2, y2 = self.search_area
                region = (x1, y1, x2 - x1, y2 - y1)
                
            # Проверяем размеры шаблона и области поиска
            try:
                from PIL import Image
                template_img = Image.open(template_path)
                template_width, template_height = template_img.size
                print(f"Размер шаблона: {template_width}x{template_height}")
                
                if region:
                    region_width, region_height = region[2], region[3]
                    print(f"Размер области поиска: {region_width}x{region_height}")
                    
                    # Проверяем, не превышает ли шаблон размеры области поиска
                    if template_width > region_width or template_height > region_height:
                        print(f"ОШИБКА: Шаблон ({template_width}x{template_height}) больше области поиска ({region_width}x{region_height})")
                        print("Создаем новый шаблон из области поиска...")
                        
                        # Создаем новый шаблон из области поиска
                        new_template = self._create_template_from_search_area()
                        if new_template:
                            print(f"Используем новый шаблон: {new_template}")
                            # Рекурсивно вызываем поиск с новым шаблоном
                            return self._search_image_in_screen(new_template)
                        else:
                            print("Не удалось создать новый шаблон, используем поиск по всему экрану")
                            region = None  # Используем весь экран
                    else:
                        print("Размеры шаблона подходят для области поиска")
                else:
                    print("Поиск по всему экрану")
                    
            except Exception as e:
                print(f"Ошибка при проверке размеров: {e}")
                
            # Отладочная информация
            print(f"Поиск шаблона: {template_path}")
            if region:
                print(f"Область поиска: {region}")
            else:
                print("Область поиска: весь экран")
                
            # Добавляем таймаут для поиска картинки
            start_time = time.time()
            timeout = 2.0  # 2 секунды таймаут
            
            # Ищем картинку на экране
            if OPENCV_AVAILABLE:
                location = pyautogui.locateOnScreen(
                    template_path, 
                    confidence=self.confidence,
                    region=region
                )
            else:
                # Без OpenCV - точный поиск
                location = pyautogui.locateOnScreen(template_path, region=region)
                
            if location:
                # Получаем центр найденного изображения
                center = pyautogui.center(location)
                print(f"Изображение найдено на позиции: {center}")
                return True, center
            else:
                print("Изображение не найдено")
                return False, None
                
        except pyautogui.ImageNotFoundException:
            print("Изображение не найдено на экране")
            return False, None
        except Exception as e:
            print(f"Ошибка при поиске изображения: {e}")
            return False, None
            
    def _create_template_from_search_area(self) -> str:
        """Создание шаблона из области поиска"""
        try:
            if not self.search_area:
                return None
                
            import pyautogui
            import uuid
            
            x1, y1, x2, y2 = self.search_area
            width = x2 - x1
            height = y2 - y1
            
            if width <= 0 or height <= 0:
                print("Некорректная область поиска")
                return None
                
            # Делаем скриншот области
            screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
            
            # Сохраняем временный файл
            template_path = f"{TEMP_TEMPLATE_PREFIX}{uuid.uuid4().hex[:8]}.png"
            screenshot.save(template_path)
            
            print(f"Шаблон создан из области поиска: {template_path}")
            return template_path
            
        except Exception as e:
            print(f"Ошибка создания шаблона из области: {e}")
            return None
            
    def _find_temp_template(self) -> str:
        """Автоматический поиск временного шаблона"""
        try:
            import glob
            
            # Ищем временные файлы шаблонов
            temp_patterns = [
                f"{TEMP_TEMPLATE_PREFIX}*.png",
                f"{TEMP_TEMPLATE_PREFIX}*.jpg",
                f"{TEMP_TEMPLATE_PREFIX}*.jpeg"
            ]
            
            for pattern in temp_patterns:
                files = glob.glob(pattern)
                if files:
                    # Возвращаем самый новый файл
                    latest_file = max(files, key=os.path.getctime)
                    print(f"Автоматически найден шаблон: {latest_file}")
                    return latest_file
                    
            return None
            
        except Exception as e:
            print(f"Ошибка поиска временного шаблона: {e}")
            return None
            
    def _can_use_cache(self, template_path: str) -> bool:
        """Проверка возможности использования кэшированной позиции"""
        if (self.last_found_position is None or 
            self.last_template_path != template_path or
            self.clicks_since_last_search >= self.recheck_interval):
            return False
            
        return True
        
    def _update_cache(self, template_path: str, position: tuple):
        """Обновление кэша найденной позиции"""
        self.last_found_position = position
        self.last_template_path = template_path
        self.clicks_since_last_search = 0
        self.last_search_time = time.time()
        
    def reset_search_cache(self):
        """Сброс кэша поиска"""
        self.last_found_position = None
        self.clicks_since_last_search = 0
        self.last_template_path = None
        self.last_search_time = 0
        
    def set_user_activity_detected(self, detected: bool):
        """Установка флага активности пользователя"""
        self.user_activity_detected = detected
        if detected:
            self.reset_search_cache()
            
    def capture_template_image(self, save_path=None):
        """Захват шаблонного изображения с экрана"""
        if save_path is None:
            save_path = f"{TEMP_TEMPLATE_PREFIX}{uuid.uuid4().hex[:8]}.png"
            
        try:
            # Ждем немного для подготовки пользователя
            time.sleep(2)
            
            # Делаем скриншот
            if self.search_area:
                x1, y1, x2, y2 = self.search_area
                screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
            else:
                screenshot = pyautogui.screenshot()
                
            screenshot.save(save_path)
            return save_path
            
        except Exception as e:
            print(f"Ошибка при захвате шаблона: {e}")
            return None
            
    def add_to_sequence(self, template_path, clicks_count=1):
        """Добавление изображения в последовательность"""
        if not os.path.exists(template_path):
            return False
            
        if len(self.image_sequence) >= VALIDATION["MAX_IMAGE_SEQUENCE"]:
            return False
            
        self.image_sequence.append({
            'path': template_path,
            'clicks': clicks_count,
            'name': os.path.basename(template_path)
        })
        return True
        
    def remove_from_sequence(self, index):
        """Удаление изображения из последовательности"""
        if 0 <= index < len(self.image_sequence):
            removed = self.image_sequence.pop(index)
            # Если удалили текущий элемент, сдвигаем индекс
            if index <= self.current_image_index and self.current_image_index > 0:
                self.current_image_index -= 1
            return removed
        return None
        
    def clear_sequence(self):
        """Очистка последовательности изображений"""
        self.image_sequence.clear()
        self.current_image_index = 0
        self.image_sequence_clicks = 0
        self.image_sequence_repeat_count = 0
        
    def get_current_sequence_template(self):
        """Получение текущего шаблона в последовательности"""
        if not self.image_sequence or self.current_image_index >= len(self.image_sequence):
            return None
        return self.image_sequence[self.current_image_index]
        
    def process_sequence_click(self):
        """Обработка клика в режиме последовательности"""
        if not self.image_sequence:
            return False, None
            
        current_template = self.get_current_sequence_template()
        if not current_template:
            return False, None
            
        # Ищем текущий шаблон
        found, position = self.find_image_position(current_template['path'])
        
        if found:
            self.image_sequence_clicks += 1
            
            # Проверяем, нужно ли переходить к следующему шаблону
            if self.image_sequence_clicks >= current_template['clicks']:
                self._advance_sequence()
                
        return found, position
        
    def _advance_sequence(self):
        """Переход к следующему элементу в последовательности"""
        self.image_sequence_clicks = 0
        self.current_image_index += 1
        
        # Если дошли до конца последовательности
        if self.current_image_index >= len(self.image_sequence):
            self.current_image_index = 0
            self.image_sequence_repeat_count += 1
            
            # Проверяем лимит повторений
            if self.image_sequence_repeat_count >= self.image_sequence_repeats:
                if self.on_sequence_complete_callback:
                    self.on_sequence_complete_callback()
                self._reset_sequence()
                
    def _reset_sequence(self):
        """Сброс последовательности к началу"""
        self.current_image_index = 0
        self.image_sequence_clicks = 0
        self.image_sequence_repeat_count = 0
        
    def set_sequence_repeats(self, repeats):
        """Установка количества повторений последовательности"""
        self.image_sequence_repeats = max(1, repeats)
        
    def get_sequence_info(self):
        """Получение информации о последовательности"""
        if not self.image_sequence:
            return "Последовательность пуста"
            
        total_templates = len(self.image_sequence)
        current_index = self.current_image_index + 1
        current_repeat = self.image_sequence_repeat_count + 1
        
        return (f"Шаблон {current_index}/{total_templates}, "
               f"Повтор {current_repeat}/{self.image_sequence_repeats}")
               
    def cleanup_temp_files(self):
        """Очистка временных файлов шаблонов"""
        try:
            for file in os.listdir('.'):
                if file.startswith(TEMP_TEMPLATE_PREFIX) and file.endswith('.png'):
                    try:
                        os.remove(file)
                    except:
                        pass
        except Exception as e:
            print(f"Ошибка при очистке временных файлов: {e}")
            
    def validate_template(self, template_path):
        """Проверка валидности шаблона"""
        if not os.path.exists(template_path):
            return False, "Файл не найден"
            
        try:
            with Image.open(template_path) as img:
                width, height = img.size
                if width < 5 or height < 5:
                    return False, "Изображение слишком маленькое"
                if width > 1920 or height > 1080:
                    return False, "Изображение слишком большое"
                return True, "OK"
        except Exception as e:
            return False, f"Ошибка чтения изображения: {e}" 

    def set_current_template(self, template_path):
        """Установка текущего шаблона"""
        if os.path.exists(template_path):
            self.current_template = template_path
            print(f"Установлен текущий шаблон: {template_path}")
        else:
            print(f"Файл шаблона не найден: {template_path}") 