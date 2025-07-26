"""
OmniaClick - Захват шаблонов

Система захвата шаблонов изображений с экрана для поиска
"""

import tkinter as tk
from tkinter import messagebox
import pyautogui
import threading
import time
import os
import uuid
from typing import Optional, Callable, Tuple

from config import *


class TemplateCapture:
    """Захват шаблонов изображений с экрана"""
    
    def __init__(self, overlay_manager):
        self.overlay_manager = overlay_manager
        
        # Состояние захвата
        self.capture_active = False
        self.capture_thread = None
        
        # Коллбэки
        self.callbacks = {}
        
    def set_callbacks(self, **callbacks):
        """Установка коллбэков"""
        self.callbacks.update(callbacks)
        
    def capture_template(self, callback: Optional[Callable] = None) -> Optional[str]:
        """Запуск захвата шаблона"""
        if self.capture_active:
            if 'on_show_message' in self.callbacks:
                self.callbacks['on_show_message'](
                    "Предупреждение", 
                    "Захват шаблона уже активен",
                    "warning"
                )
            return None
            
        # Вызываем коллбэк для остановки кликера если нужно
        if 'on_before_capture' in self.callbacks:
            was_clicking = self.callbacks['on_before_capture']()
        else:
            was_clicking = False
            
        # Отключаем горячие клавиши во время захвата
        if 'on_disable_hotkeys' in self.callbacks:
            self.callbacks['on_disable_hotkeys']()
            
        # Показываем инструкцию
        if 'on_show_message' in self.callbacks:
            self.callbacks['on_show_message'](
                "Захват шаблона", 
                "Зажмите левую кнопку мыши и выделите область для шаблона.\n" +
                "Отпустите кнопку для завершения.\nНажмите ESC для отмены.",
                "info"
            )
        else:
            messagebox.showinfo("Захват шаблона", 
                               "Зажмите левую кнопку мыши и выделите область для шаблона.\n" +
                               "Отпустите кнопку для завершения.\nНажмите ESC для отмены.")
            
        # Запускаем захват в отдельном потоке
        self.capture_thread = threading.Thread(
            target=self._capture_template_thread, 
            args=(was_clicking, callback), 
            daemon=True
        )
        self.capture_thread.start()
        
    def _capture_template_thread(self, was_clicking: bool = False, callback: Optional[Callable] = None):
        """Поток для захвата шаблона"""
        try:
            self.capture_active = True
            
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
                    
                    # Проверяем ESC для отмены
                    try:
                        import keyboard
                        if keyboard.is_pressed('esc'):
                            if 'on_enable_hotkeys' in self.callbacks:
                                self.callbacks['on_enable_hotkeys']()
                            if was_clicking and 'on_after_capture' in self.callbacks:
                                self.callbacks['on_after_capture']()
                            return None
                    except:
                        pass
                        
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
                            
                            # Обновляем оверлей только если позиция изменилась
                            if current_pos != last_pos:
                                self.overlay_manager.show_selection_overlay(
                                    start_pos[0], start_pos[1], current_pos[0], current_pos[1]
                                )
                                last_pos = current_pos
                            time.sleep(0.05)  # Ограничиваем частоту обновлений
                        else:
                            break
                    except:
                        # Fallback на pyautogui
                        if pyautogui.mouseDown():
                            current_pos = pyautogui.position()
                            if current_pos != last_pos:
                                self.overlay_manager.show_selection_overlay(
                                    start_pos[0], start_pos[1], current_pos[0], current_pos[1]
                                )
                                last_pos = current_pos
                            time.sleep(0.05)
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
                    time.sleep(0.05)
                 
            end_pos = pyautogui.position()
            
            # Скрываем динамический оверлей
            self.overlay_manager.hide_selection_overlay()
            
            # Определяем область
            left = min(start_pos[0], end_pos[0])
            top = min(start_pos[1], end_pos[1])
            width = abs(end_pos[0] - start_pos[0])
            height = abs(end_pos[1] - start_pos[1])
             
            if width > 5 and height > 5:  # Минимальный размер
                # Делаем скриншот области
                screenshot = pyautogui.screenshot(region=(left, top, width, height))
                
                # Сохраняем временный файл
                template_path = f"{TEMP_TEMPLATE_PREFIX}{uuid.uuid4().hex[:8]}.png"
                screenshot.save(template_path)
                
                # Показываем фиксированный оверлей области (зеленый)
                self.overlay_manager.show_success_overlay(
                    left + width // 2, 
                    top + height // 2, 
                    duration=2.0
                )
                
                # Вызываем коллбэк с результатом
                template_info = {
                    "path": template_path,
                    "name": f"Захват {width}x{height}",
                    "size": (width, height),
                    "region": (left, top, width, height)
                }
                
                if callback:
                    callback(template_info)
                elif 'on_template_captured' in self.callbacks:
                    self.callbacks['on_template_captured'](template_info)
                
                # Показываем сообщение об успехе
                if 'on_show_message' in self.callbacks:
                    self.callbacks['on_show_message'](
                        "Шаблон захвачен", 
                        f"Шаблон сохранен: {template_path}\nРазмер: {width}x{height}",
                        "info"
                    )
                    
                print(f"Шаблон захвачен: {template_path}, размер: {width}x{height}")
                return template_path
            else:
                if 'on_show_message' in self.callbacks:
                    self.callbacks['on_show_message'](
                        "Ошибка", 
                        "Выбранная область слишком мала",
                        "error"
                    )
                return None
            
        except Exception as e:
            print(f"Ошибка захвата шаблона: {e}")
            if 'on_show_message' in self.callbacks:
                self.callbacks['on_show_message'](
                    "Ошибка", 
                    f"Ошибка захвата шаблона: {e}",
                    "error"
                )
            return None
        finally:
            # Гарантированно снимаем флаг захвата
            self.capture_active = False
            
            # Гарантированно включаем горячие клавиши
            if 'on_enable_hotkeys' in self.callbacks:
                self.callbacks['on_enable_hotkeys']()
                
            # Скрываем оверлей выбора
            self.overlay_manager.hide_selection_overlay()
            
            # Возобновляем кликер если он работал
            if was_clicking and 'on_after_capture' in self.callbacks:
                time.sleep(1)  # Небольшая пауза
                self.callbacks['on_after_capture']()
                
    def capture_from_search_area(self, search_area: Tuple[int, int, int, int]) -> Optional[str]:
        """Создание шаблона из заданной области поиска"""
        try:
            left, top, right, bottom = search_area
            width = right - left
            height = bottom - top
            
            if width <= 0 or height <= 0:
                if 'on_show_message' in self.callbacks:
                    self.callbacks['on_show_message'](
                        "Ошибка", 
                        "Некорректная область поиска",
                        "error"
                    )
                return None
                
            # Делаем скриншот области
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            
            # Сохраняем временный файл
            template_path = f"{TEMP_TEMPLATE_PREFIX}{uuid.uuid4().hex[:8]}.png"
            screenshot.save(template_path)
            
            # Показываем оверлей успеха
            self.overlay_manager.show_success_overlay(
                left + width // 2, 
                top + height // 2, 
                duration=2.0
            )
            
            # Вызываем коллбэк
            template_info = {
                "path": template_path,
                "name": f"Из области {width}x{height}",
                "size": (width, height),
                "region": (left, top, width, height)
            }
            
            if 'on_template_captured' in self.callbacks:
                self.callbacks['on_template_captured'](template_info)
            
            print(f"Шаблон создан из области поиска: {template_path}")
            return template_path
            
        except Exception as e:
            print(f"Ошибка создания шаблона из области: {e}")
            if 'on_show_message' in self.callbacks:
                self.callbacks['on_show_message'](
                    "Ошибка", 
                    f"Ошибка создания шаблона: {e}",
                    "error"
                )
            return None
            
    def cleanup_temp_templates(self) -> int:
        """Очистка временных шаблонов"""
        count = 0
        try:
            # Получаем список всех файлов в текущей директории
            for filename in os.listdir('.'):
                if filename.startswith(TEMP_TEMPLATE_PREFIX) and filename.endswith('.png'):
                    try:
                        os.remove(filename)
                        count += 1
                        print(f"Удален временный шаблон: {filename}")
                    except Exception as e:
                        print(f"Ошибка удаления {filename}: {e}")
                        
        except Exception as e:
            print(f"Ошибка очистки временных шаблонов: {e}")
            
        return count
        
    def is_capturing(self) -> bool:
        """Проверка активности захвата"""
        return self.capture_active 