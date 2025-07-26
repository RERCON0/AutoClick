"""
OmniaClick - Пипетка для выбора цвета

Интерактивная пипетка для выбора цвета пикселя с экрана
"""

import tkinter as tk
from tkinter import messagebox
import pyautogui
import threading
import time
import keyboard
from typing import Optional, Callable

from config import *


class ColorPicker:
    """Пипетка для выбора цвета с экрана"""
    
    def __init__(self):
        # Состояние пипетки
        self.picking_active = False
        self.pick_thread = None
        
        # Коллбэки
        self.callbacks = {}
        
    def set_callbacks(self, **callbacks):
        """Установка коллбэков"""
        self.callbacks.update(callbacks)
        
    def pick_color(self, callback: Optional[Callable] = None) -> Optional[str]:
        """Запуск пипетки для выбора цвета"""
        if self.picking_active:
            if 'on_show_message' in self.callbacks:
                self.callbacks['on_show_message'](
                    "Предупреждение", 
                    "Пипетка уже активна",
                    "warning"
                )
            return None
            
        # Показываем инструкцию
        if 'on_show_message' in self.callbacks:
            self.callbacks['on_show_message'](
                "Пипетка", 
                "Наведите курсор на нужный цвет и нажмите ПРОБЕЛ (Space).\nНажмите Esc для отмены.",
                "info"
            )
        else:
            messagebox.showinfo("Пипетка", "Наведите курсор на нужный цвет и нажмите ПРОБЕЛ (Space).\nНажмите Esc для отмены.")
            
        # Запускаем пипетку в отдельном потоке
        self.pick_thread = threading.Thread(
            target=self._color_picker_thread, 
            args=(callback,), 
            daemon=True
        )
        self.pick_thread.start()
        
    def _color_picker_thread(self, callback: Optional[Callable] = None):
        """Поток для работы пипетки"""
        try:
            self.picking_active = True
            
            # Отключаем горячие клавиши во время работы пипетки
            if 'on_disable_hotkeys' in self.callbacks:
                self.callbacks['on_disable_hotkeys']()
                
            # Очищаем все предыдущие hotkeys
            keyboard.clear_all_hotkeys()
            
            # Ожидаем нажатие Space или Esc
            while self.picking_active:
                try:
                    if keyboard.is_pressed('space'):
                        # Получаем позицию курсора и цвет пикселя
                        x, y = pyautogui.position()
                        pixel = pyautogui.screenshot().getpixel((x, y))
                        hex_color = f"#{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}"
                        
                        # Вызываем коллбэк с результатом
                        if callback:
                            callback(hex_color)
                        elif 'on_color_picked' in self.callbacks:
                            self.callbacks['on_color_picked'](hex_color)
                            
                        # Показываем сообщение об успехе
                        if 'on_show_message' in self.callbacks:
                            self.callbacks['on_show_message'](
                                "Цвет выбран", 
                                f"Выбран цвет: {hex_color}\nRGB: {pixel}",
                                "info"
                            )
                        
                        print(f"Выбран цвет: {hex_color} на позиции ({x}, {y})")
                        self.picking_active = False
                        return hex_color
                        
                    elif keyboard.is_pressed('esc'):
                        # Отмена выбора цвета
                        if 'on_show_message' in self.callbacks:
                            self.callbacks['on_show_message'](
                                "Отмена", 
                                "Выбор цвета отменен",
                                "info"
                            )
                        self.picking_active = False
                        return None
                        
                except Exception as e:
                    print(f"Ошибка в пипетке: {e}")
                    
                time.sleep(0.05)  # Небольшая задержка для снижения нагрузки на CPU
                
        except Exception as e:
            print(f"Ошибка в потоке пипетки: {e}")
            if 'on_show_message' in self.callbacks:
                self.callbacks['on_show_message'](
                    "Ошибка", 
                    f"Ошибка пипетки: {e}",
                    "error"
                )
            return None
        finally:
            # Гарантированно снимаем флаг активности
            self.picking_active = False
            
            # Очищаем hotkeys
            try:
                keyboard.clear_all_hotkeys()
            except:
                pass
                
            # Включаем горячие клавиши обратно
            if 'on_enable_hotkeys' in self.callbacks:
                self.callbacks['on_enable_hotkeys']()
                
    def stop_picking(self):
        """Принудительная остановка пипетки"""
        self.picking_active = False
        
    def is_picking(self) -> bool:
        """Проверка активности пипетки"""
        return self.picking_active
        
    def hex_to_rgb(self, hex_color: str) -> tuple:
        """Преобразование HEX цвета в RGB"""
        try:
            # Убираем # если есть
            hex_color = hex_color.lstrip('#')
            
            # Преобразуем в RGB
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except Exception as e:
            print(f"Ошибка преобразования цвета {hex_color}: {e}")
            return (255, 0, 0)  # Красный по умолчанию
            
    def rgb_to_hex(self, rgb: tuple) -> str:
        """Преобразование RGB в HEX"""
        try:
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        except Exception as e:
            print(f"Ошибка преобразования RGB {rgb}: {e}")
            return "#FF0000"  # Красный по умолчанию 