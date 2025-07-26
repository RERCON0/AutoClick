"""
Модуль для валидации пользовательского ввода
Содержит ValidationHelper класс для проверки корректности данных
"""

import re
from config import *

class ValidationHelper:
    """Класс для валидации пользовательского ввода"""
    
    @staticmethod
    def validate_interval(value):
        """Валидация интервала между кликами"""
        try:
            interval = float(value)
            if MIN_INTERVAL <= interval <= MAX_INTERVAL:
                return True, interval, ""
            else:
                return False, None, f"Интервал должен быть от {MIN_INTERVAL} до {MAX_INTERVAL} секунд"
        except ValueError:
            return False, None, "Интервал должен быть числом"
            
    @staticmethod
    def validate_color_hex(color):
        """Валидация HEX цвета"""
        if not color:
            return False, "Цвет не может быть пустым"
            
        # Убираем # если есть
        color = color.lstrip('#')
        
        # Проверяем формат
        if not re.match(r'^[0-9A-Fa-f]{6}$', color):
            return False, "Неверный формат цвета. Используйте формат #RRGGBB"
            
        return True, f"#{color.upper()}"
        
    @staticmethod
    def validate_color_tolerance(tolerance):
        """Валидация толерантности цвета"""
        try:
            tol = int(tolerance)
            if 0 <= tol <= 100:
                return True, tol, ""
            else:
                return False, None, "Толерантность должна быть от 0 до 100"
        except ValueError:
            return False, None, "Толерантность должна быть целым числом"
            
    @staticmethod
    def validate_confidence(confidence):
        """Валидация уровня точности поиска изображений"""
        try:
            conf = float(confidence)
            if 0.1 <= conf <= 1.0:
                return True, conf, ""
            else:
                return False, None, "Точность должна быть от 0.1 до 1.0"
        except ValueError:
            return False, None, "Точность должна быть числом"
            
    @staticmethod
    def validate_coordinates(x, y):
        """Валидация координат"""
        try:
            x_int = int(x)
            y_int = int(y)
            
            if x_int < 0 or y_int < 0:
                return False, None, None, "Координаты не могут быть отрицательными"
                
            # Проверяем что координаты в пределах экрана
            import pyautogui
            screen_width, screen_height = pyautogui.size()
            
            if x_int >= screen_width or y_int >= screen_height:
                return False, None, None, f"Координаты выходят за пределы экрана ({screen_width}x{screen_height})"
                
            return True, x_int, y_int, ""
            
        except ValueError:
            return False, None, None, "Координаты должны быть целыми числами"
            
    @staticmethod
    def validate_area(x1, y1, x2, y2):
        """Валидация области"""
        # Сначала валидируем отдельные координаты
        valid1, x1_int, y1_int, msg1 = ValidationHelper.validate_coordinates(x1, y1)
        if not valid1:
            return False, None, msg1
            
        valid2, x2_int, y2_int, msg2 = ValidationHelper.validate_coordinates(x2, y2)
        if not valid2:
            return False, None, msg2
            
        # Проверяем что область имеет положительный размер
        if abs(x2_int - x1_int) < 10 or abs(y2_int - y1_int) < 10:
            return False, None, "Область слишком маленькая (минимум 10x10 пикселей)"
            
        # Нормализуем координаты (левый верхний угол должен быть меньше правого нижнего)
        area = (
            min(x1_int, x2_int),
            min(y1_int, y2_int),
            max(x1_int, x2_int),
            max(y1_int, y2_int)
        )
        
        return True, area, ""
        
    @staticmethod
    def validate_sequence_length(sequence, max_length, item_name):
        """Валидация длины последовательности"""
        if len(sequence) >= max_length:
            return False, f"Максимальное количество {item_name}: {max_length}"
        return True, ""
        
    @staticmethod
    def validate_clicks_count(clicks):
        """Валидация количества кликов"""
        try:
            clicks_int = int(clicks)
            if 1 <= clicks_int <= VALIDATION["MAX_KEY_PRESSES"]:
                return True, clicks_int, ""
            else:
                return False, None, f"Количество кликов должно быть от 1 до {VALIDATION['MAX_KEY_PRESSES']}"
        except ValueError:
            return False, None, "Количество кликов должно быть целым числом"
            
    @staticmethod
    def validate_repeats(repeats):
        """Валидация количества повторений"""
        try:
            repeats_int = int(repeats)
            if 1 <= repeats_int <= 1000:
                return True, repeats_int, ""
            else:
                return False, None, "Количество повторений должно быть от 1 до 1000"
        except ValueError:
            return False, None, "Количество повторений должно быть целым числом"
            
    @staticmethod
    def validate_key_name(key):
        """Валидация названия клавиши"""
        if not key or not isinstance(key, str):
            return False, "Название клавиши не может быть пустым"
            
        key = key.strip().lower()
        
        # Список допустимых клавиш
        valid_keys = [
            # Буквы
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            # Цифры
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            # Функциональные клавиши
            'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
            # Специальные клавиши
            'space', 'enter', 'tab', 'esc', 'escape', 'backspace', 'delete',
            'insert', 'home', 'end', 'page up', 'page down', 'pageup', 'pagedown',
            'up', 'down', 'left', 'right',
            # Модификаторы
            'ctrl', 'alt', 'shift', 'win', 'cmd',
            # Знаки препинания и символы
            'comma', 'period', 'semicolon', 'apostrophe', 'grave',
            'minus', 'equal', 'backslash', 'slash',
            'left bracket', 'right bracket', '[', ']',
            # Numpad
            'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6', 'num7', 'num8', 'num9',
            'numlock', 'multiply', 'add', 'subtract', 'decimal', 'divide'
        ]
        
        if key in valid_keys:
            return True, key
        else:
            return False, f"Неизвестная клавиша: {key}"
            
    @staticmethod
    def sanitize_filename(filename):
        """Очистка имени файла от недопустимых символов"""
        # Удаляем недопустимые символы для Windows
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
            
        # Удаляем пробелы в начале и конце
        filename = filename.strip()
        
        # Ограничиваем длину
        if len(filename) > 100:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            max_name_length = 95 - len(ext)
            filename = name[:max_name_length] + ('.' + ext if ext else '')
            
        return filename if filename else "untitled"
        
    @staticmethod
    def validate_json_structure(data, required_fields=None):
        """Валидация структуры JSON настроек"""
        if not isinstance(data, dict):
            return False, "Настройки должны быть в формате JSON объекта"
            
        if required_fields:
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
                    
            if missing_fields:
                return False, f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"
                
        return True, "OK"
        
    @staticmethod
    def is_safe_path(path):
        """Проверка безопасности пути к файлу"""
        if not path:
            return False
            
        # Проверяем на попытки выхода за пределы текущей директории
        if '..' in path or path.startswith('/') or ':' in path[1:]:
            return False
            
        return True 