"""
OmniaClick - Интерактивный выбор области

Система для интерактивного выбора области поиска на экране
"""

import tkinter as tk
from tkinter import messagebox
import pyautogui
import threading
import time
from typing import Optional, Tuple, Callable

from config import *


class AreaSelector:
    """Интерактивный выбор области поиска"""
    
    def __init__(self, overlay_manager):
        self.overlay_manager = overlay_manager
        
        # Состояние выбора
        self.selection_active = False
        self.selection_thread = None
        
        # Коллбэки
        self.callbacks = {}
        
    def set_callbacks(self, **callbacks):
        """Установка коллбэков"""
        self.callbacks.update(callbacks)
        
    def select_search_area(self, callback: Optional[Callable] = None) -> Optional[Tuple[int, int, int, int]]:
        """Запуск интерактивного выбора области поиска"""
        if self.selection_active:
            messagebox.showwarning("Предупреждение", "Выбор области уже активен")
            return None
            
        # Вызываем коллбэк для остановки кликера если нужно
        if 'on_before_selection' in self.callbacks:
            was_clicking = self.callbacks['on_before_selection']()
        else:
            was_clicking = False
            
        # Отключаем горячие клавиши во время выбора области
        if 'on_disable_hotkeys' in self.callbacks:
            self.callbacks['on_disable_hotkeys']()
            
        messagebox.showinfo("Выбор области", 
                           "Зажмите левую кнопку мыши и выделите прямоугольную область.\n" +
                           "Отпустите кнопку для завершения выбора.\n" +
                           "Прямоугольник будет показан поверх всех окон.")
        
        # Запускаем выбор области в отдельном потоке
        self.selection_thread = threading.Thread(
            target=self._select_area_thread, 
            args=(was_clicking, callback), 
            daemon=True
        )
        self.selection_thread.start()
        
    def _select_area_thread(self, was_clicking: bool = False, callback: Optional[Callable] = None):
        """Поток для выбора области"""
        try:
            self.selection_active = True
            start_pos = None
            
            # Ожидаем нажатия левой кнопки мыши
            if WIN32_AVAILABLE:
                import win32api
                while True:
                    try:
                        if win32api.GetAsyncKeyState(0x01) & 0x8000:  # VK_LBUTTON
                            break
                    except:
                        # Fallback на pyautogui если win32api недоступен
                        if pyautogui.mouseDown():
                            break
                    time.sleep(0.01)
            else:
                # Fallback без win32api
                while not pyautogui.mouseDown():
                    time.sleep(0.01)
                     
            start_pos = pyautogui.position()
            last_pos = start_pos
            
            # Показываем динамический прямоугольник во время выбора
            if WIN32_AVAILABLE:
                import win32api
                while True:
                    try:
                        if win32api.GetAsyncKeyState(0x01) & 0x8000:  # VK_LBUTTON
                            current_pos = pyautogui.position()
                            
                            # Обновляем прямоугольник выбора если позиция изменилась
                            if current_pos != last_pos and current_pos[0] != start_pos[0] and current_pos[1] != start_pos[1]:
                                self.overlay_manager.show_selection_overlay(
                                    start_pos[0], start_pos[1], current_pos[0], current_pos[1]
                                )
                                last_pos = current_pos
                            
                            time.sleep(0.01)
                        else:
                            break
                    except:
                        # Fallback на pyautogui
                        if pyautogui.mouseDown():
                            current_pos = pyautogui.position()
                            
                            # Обновляем прямоугольник выбора если позиция изменилась
                            if current_pos != last_pos and current_pos[0] != start_pos[0] and current_pos[1] != start_pos[1]:
                                self.overlay_manager.show_selection_overlay(
                                    start_pos[0], start_pos[1], current_pos[0], current_pos[1]
                                )
                                last_pos = current_pos
                            
                            time.sleep(0.01)
                        else:
                            break
            else:
                # Fallback без win32api
                while pyautogui.mouseDown():
                    current_pos = pyautogui.position()
                    if current_pos != last_pos:
                        self.overlay_manager.show_selection_overlay(
                            start_pos[0], start_pos[1], current_pos[0], current_pos[1]
                        )
                        last_pos = current_pos
                    time.sleep(0.01)
            
            end_pos = pyautogui.position()
            
            # Проверяем, что выбранная область валидна
            if start_pos[0] == end_pos[0] or start_pos[1] == end_pos[1]:
                if 'on_show_message' in self.callbacks:
                    self.callbacks['on_show_message'](
                        "Предупреждение", 
                        "Выбранная область слишком мала. Попробуйте еще раз.",
                        "warning"
                    )
                return None
            
            # Скрываем временный прямоугольник выбора
            self.overlay_manager.hide_selection_overlay()
            
            # Вычисляем область поиска
            search_area = (
                min(start_pos[0], end_pos[0]),
                min(start_pos[1], end_pos[1]),
                max(start_pos[0], end_pos[0]),
                max(start_pos[1], end_pos[1])
            )
            
            # Показываем фиксированный прямоугольник выбранной области
            self.overlay_manager.show_area_overlay(*search_area)
            
            # Обновляем интерфейс
            area_text = f"Область: ({search_area[0]}, {search_area[1]}) - ({search_area[2]}, {search_area[3]})"
            
            # Вызываем коллбэк с результатом
            if callback:
                callback(search_area, area_text)
            elif 'on_area_selected' in self.callbacks:
                self.callbacks['on_area_selected'](search_area, area_text)
            
            # Показываем сообщение об успехе
            if 'on_show_message' in self.callbacks:
                self.callbacks['on_show_message'](
                    "Область выбрана", 
                    f"Область поиска установлена: {area_text}",
                    "info"
                )
            
            # Возобновляем кликер если он работал
            if was_clicking and 'on_after_selection' in self.callbacks:
                time.sleep(1)  # Небольшая пауза
                self.callbacks['on_after_selection']()
            
            return search_area
            
        except Exception as e:
            print(f"Ошибка выбора области: {e}")
            if 'on_show_message' in self.callbacks:
                self.callbacks['on_show_message'](
                    "Ошибка", 
                    f"Ошибка выбора области: {e}",
                    "error"
                )
            return None
        finally:
            # Гарантированно снимаем флаг выбора области
            self.selection_active = False
            
            # Гарантированно включаем горячие клавиши
            if 'on_enable_hotkeys' in self.callbacks:
                self.callbacks['on_enable_hotkeys']()
                
            # Скрываем оверлей выбора
            self.overlay_manager.hide_selection_overlay()
            
    def clear_search_area(self):
        """Очистка области поиска"""
        self.overlay_manager.hide_area_overlay()
        
        if 'on_area_cleared' in self.callbacks:
            self.callbacks['on_area_cleared']()
            
    def is_selecting(self) -> bool:
        """Проверка активности выбора области"""
        return self.selection_active 