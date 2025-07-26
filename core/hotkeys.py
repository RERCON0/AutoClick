"""
Модуль для управления горячими клавишами
Содержит HotkeyManager класс для регистрации и обработки горячих клавиш
"""

import keyboard
import threading
import time
from config import *

class HotkeyManager:
    """Класс для управления горячими клавишами"""
    
    def __init__(self):
        self.hotkey_start = DEFAULT_HOTKEY_START
        self.hotkey_stop = DEFAULT_HOTKEY_STOP
        self.emergency_stop_key = EMERGENCY_STOP_KEY
        
        self.hotkeys_enabled = False
        self.hotkeys_disabled = False
        
        # Коллбэки для обработки нажатий
        self.on_start_callback = None
        self.on_stop_callback = None
        self.on_emergency_stop_callback = None
        
        # Список зарегистрированных горячих клавиш
        self.registered_hotkeys = []
        
    def set_callbacks(self, on_start=None, on_stop=None, on_emergency_stop=None):
        """Установка коллбэков для обработки горячих клавиш"""
        self.on_start_callback = on_start
        self.on_stop_callback = on_stop
        self.on_emergency_stop_callback = on_emergency_stop
        
    def set_start_hotkey(self, key):
        """Установка горячей клавиши для запуска"""
        if self.is_valid_key(key):
            old_key = self.hotkey_start
            self.hotkey_start = self.normalize_key(key)
            
            # Перерегистрируем горячие клавиши если они активны
            if self.hotkeys_enabled:
                self.disable_hotkeys()
                self.enable_hotkeys()
            return True
        return False
        
    def set_stop_hotkey(self, key):
        """Установка горячей клавиши для остановки"""
        if self.is_valid_key(key):
            old_key = self.hotkey_stop
            self.hotkey_stop = self.normalize_key(key)
            
            # Перерегистрируем горячие клавиши если они активы
            if self.hotkeys_enabled:
                self.disable_hotkeys()
                self.enable_hotkeys()
            return True
        return False
        
    def enable_hotkeys(self, show_message=False):
        """Включение горячих клавиш"""
        if self.hotkeys_enabled or self.hotkeys_disabled:
            return False
            
        try:
            # Регистрируем горячие клавиши
            self._register_hotkey(self.hotkey_start, self._hotkey_start_action)
            self._register_hotkey(self.hotkey_stop, self._hotkey_stop_action)
            self._register_hotkey(self.emergency_stop_key, self._emergency_stop_action)
            
            self.hotkeys_enabled = True
            
            if show_message:
                print(f"Горячие клавиши установлены: {self.hotkey_start.upper()} - запуск, {self.hotkey_stop.upper()} - остановка")
            return True
            
        except Exception as e:
            print(f"Ошибка при установке горячих клавиш: {e}")
            return False
            
    def disable_hotkeys(self):
        """Отключение горячих клавиш"""
        if not self.hotkeys_enabled:
            return False
            
        try:
            # Удаляем все зарегистрированные горячие клавиши
            for hotkey in self.registered_hotkeys:
                try:
                    keyboard.remove_hotkey(hotkey)
                except:
                    pass
                    
            self.registered_hotkeys.clear()
            self.hotkeys_enabled = False
            return True
            
        except Exception as e:
            print(f"Ошибка при отключении горячих клавиш: {e}")
            return False
            
    def temporarily_disable(self):
        """Временное отключение горячих клавиш"""
        self.hotkeys_disabled = True
        
    def re_enable(self):
        """Возобновление работы горячих клавиш"""
        self.hotkeys_disabled = False
        
    def _register_hotkey(self, key, callback):
        """Регистрация горячей клавиши"""
        try:
            hotkey_id = keyboard.add_hotkey(key, callback, suppress=True)
            self.registered_hotkeys.append(hotkey_id)
            return hotkey_id
        except Exception as e:
            print(f"Ошибка при регистрации горячей клавиши {key}: {e}")
            return None
            
    def _hotkey_start_action(self):
        """Обработка нажатия клавиши запуска"""
        if self.hotkeys_disabled:
            return
            
        if self.on_start_callback:
            # Выполняем в отдельном потоке для избежания блокировки
            threading.Thread(target=self.on_start_callback, daemon=True).start()
            
    def _hotkey_stop_action(self):
        """Обработка нажатия клавиши остановки"""
        if self.hotkeys_disabled:
            return
            
        if self.on_stop_callback:
            # Выполняем в отдельном потоке для избежания блокировки
            threading.Thread(target=self.on_stop_callback, daemon=True).start()
            
    def _emergency_stop_action(self):
        """Обработка экстренной остановки"""
        if self.on_emergency_stop_callback:
            # Экстренная остановка выполняется немедленно
            self.on_emergency_stop_callback()
            
    def normalize_key(self, key):
        """Нормализация названия клавиши"""
        if not key:
            return ""
            
        key = key.lower().strip()
        
        # Замены для совместимости
        replacements = {
            'control': 'ctrl',
            'windows': 'win',
            'command': 'cmd',
            'option': 'alt',
            'return': 'enter',
            'escape': 'esc'
        }
        
        for old, new in replacements.items():
            key = key.replace(old, new)
            
        return key
        
    def is_valid_key(self, key):
        """Проверка валидности клавиши"""
        if not key or not isinstance(key, str):
            return False
            
        key = self.normalize_key(key)
        
        # Список недопустимых комбинаций
        invalid_keys = [
            'ctrl+alt+delete',
            'ctrl+shift+esc',
            'alt+tab',
            'win+l',
            'ctrl+c',
            'ctrl+v',
            'ctrl+x',
            'ctrl+z'
        ]
        
        if key in invalid_keys:
            return False
            
        # Проверяем формат клавиши
        try:
            # Пытаемся распарсить клавишу
            parts = key.split('+')
            if len(parts) > 4:  # Слишком много модификаторов
                return False
                
            # Проверяем каждую часть
            valid_modifiers = ['ctrl', 'alt', 'shift', 'win', 'cmd']
            valid_keys = [
                'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
                'enter', 'space', 'esc', 'tab', 'backspace', 'delete', 'insert', 'home', 'end',
                'page up', 'page down', 'up', 'down', 'left', 'right',
                '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'
            ]
            
            main_key = parts[-1]  # Последняя часть - основная клавиша
            modifiers = parts[:-1]  # Все остальные - модификаторы
            
            # Проверяем модификаторы
            for modifier in modifiers:
                if modifier not in valid_modifiers:
                    return False
                    
            # Проверяем основную клавишу
            if main_key not in valid_keys:
                return False
                
            return True
            
        except:
            return False
            
    def get_hotkey_info(self):
        """Получение информации о горячих клавишах"""
        status = "включены" if self.hotkeys_enabled else "отключены"
        if self.hotkeys_disabled:
            status = "временно отключены"
            
        return {
            'start': self.hotkey_start.upper(),
            'stop': self.hotkey_stop.upper(),
            'emergency': self.emergency_stop_key.upper(),
            'status': status,
            'enabled': self.hotkeys_enabled and not self.hotkeys_disabled
        }
        
    def test_hotkey(self, key):
        """Тестирование горячей клавиши (без регистрации)"""
        try:
            # Проверяем, можно ли зарегистрировать клавишу
            test_id = keyboard.add_hotkey(key, lambda: None, suppress=False)
            keyboard.remove_hotkey(test_id)
            return True
        except Exception as e:
            print(f"Ошибка при тестировании клавиши {key}: {e}")
            return False 