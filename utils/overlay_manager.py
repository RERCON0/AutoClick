"""
OmniaClick - Система оверлеев

Управление визуальными оверлеями для отображения областей поиска,
выделения и других интерактивных элементов
"""

import tkinter as tk
import pyautogui
import threading
import time
from typing import List, Optional, Tuple

from config import *


class OverlayManager:
    """Менеджер визуальных оверлеев"""
    
    def __init__(self):
        # Список активных оверлеев
        self.active_overlays: List[tk.Toplevel] = []
        self.selection_overlay: Optional[tk.Toplevel] = None
        self.area_overlay: Optional[tk.Toplevel] = None
        
        # Коллбэки
        self.callbacks = {}
        
    def set_callbacks(self, **callbacks):
        """Установка коллбэков"""
        self.callbacks.update(callbacks)
        
    def create_overlay_window(self, x1: int, y1: int, x2: int, y2: int, 
                             color: str = "red", width: int = 2, alpha: float = 0.3) -> Optional[tk.Toplevel]:
        """Создание окна-оверлея для отображения прямоугольника"""
        try:
            # Проверяем, не слишком ли много оверлеев
            if len(self.active_overlays) > 5:
                print("Слишком много активных оверлеев, очищаем старые")
                self.force_cleanup_overlays()
            
            # Проверяем валидность координат
            if x1 == x2 or y1 == y2:
                print(f"Некорректные координаты: ({x1}, {y1}) - ({x2}, {y2})")
                return None
                
            # Вычисляем размеры
            width_rect = abs(x2 - x1)
            height_rect = abs(y2 - y1)
            
            # Проверяем минимальный размер
            if width_rect < 5 or height_rect < 5:
                print(f"Область слишком мала: {width_rect}x{height_rect}")
                return None
                
            # Проверяем, что координаты в пределах экрана
            screen_width, screen_height = pyautogui.size()
            if (x1 < 0 or y1 < 0 or x2 > screen_width or y2 > screen_height or
                x1 > screen_width or y1 > screen_height or x2 < 0 or y2 < 0):
                print(f"Координаты вне экрана: ({x1}, {y1}) - ({x2}, {y2}), экран: {screen_width}x{screen_height}")
                return None
            
            # Очищаем старые оверлеи перед созданием нового
            self.cleanup_old_overlays()
            
            overlay = tk.Toplevel()
            # Добавляем в список активных оверлеев
            self.active_overlays.append(overlay)
            
            overlay.overrideredirect(True)  # Убираем заголовок окна
            overlay.attributes("-topmost", True)  # Поверх всех окон
            overlay.lift()  # Поднимаем окно на передний план
            overlay.focus_force()  # Принудительный фокус
            overlay.attributes("-transparentcolor", "black")  # Прозрачный фон
            overlay.config(bg="black")
            
            # Дополнительные атрибуты для отображения поверх игр
            try:
                overlay.attributes("-toolwindow", True)  # Убираем из панели задач
            except:
                pass
            
            # Устанавливаем позицию и размер
            overlay.geometry(f"{width_rect}x{height_rect}+{min(x1, x2)}+{min(y1, y2)}")
            
            # Создаем Canvas для рисования прямоугольника
            canvas = tk.Canvas(overlay, width=width_rect, height=height_rect, 
                             bg="black", highlightthickness=0)
            canvas.pack()
            
            # Рисуем прямоугольник
            canvas.create_rectangle(0, 0, width_rect, height_rect, 
                                  outline=color, width=width, fill="")
            
            # Устанавливаем прозрачность (работает не на всех системах)
            try:
                overlay.attributes("-alpha", alpha)
            except:
                pass
            
            # Принудительно устанавливаем поверх всех окон
            overlay.update()
            overlay.attributes("-topmost", True)
            overlay.lift()
            
            print(f"Создан оверлей: {width_rect}x{height_rect} на позиции ({min(x1, x2)}, {min(y1, y2)})")
            return overlay
        except Exception as e:
            print(f"Ошибка создания оверлея: {e}")
            return None
            
    def show_selection_overlay(self, x1: int, y1: int, x2: int, y2: int):
        """Показ динамического оверлея выбора области"""
        try:
            # Скрываем предыдущий оверлей выбора
            self.hide_selection_overlay()
            
            # Создаем новый оверлей выбора
            self.selection_overlay = self.create_overlay_window(
                x1, y1, x2, y2, 
                color=OVERLAY_COLORS["SELECTION"], 
                width=OVERLAY_WIDTH, 
                alpha=OVERLAY_ALPHA
            )
        except Exception as e:
            print(f"Ошибка показа оверлея выбора: {e}")
            
    def hide_selection_overlay(self):
        """Скрытие оверлея выбора области"""
        try:
            if self.selection_overlay and self.selection_overlay.winfo_exists():
                self.selection_overlay.destroy()
                if self.selection_overlay in self.active_overlays:
                    self.active_overlays.remove(self.selection_overlay)
            self.selection_overlay = None
        except Exception as e:
            print(f"Ошибка скрытия оверлея выбора: {e}")
            self.selection_overlay = None
            
    def show_area_overlay(self, x1: int, y1: int, x2: int, y2: int):
        """Показ фиксированного оверлея области поиска"""
        try:
            # Скрываем предыдущий оверлей области
            self.hide_area_overlay()
            
            # Создаем новый оверлей области
            self.area_overlay = self.create_overlay_window(
                x1, y1, x2, y2, 
                color=OVERLAY_COLORS["AREA"], 
                width=OVERLAY_WIDTH, 
                alpha=OVERLAY_ALPHA
            )
        except Exception as e:
            print(f"Ошибка показа оверлея области: {e}")
            
    def hide_area_overlay(self):
        """Скрытие оверлея области поиска"""
        try:
            if self.area_overlay and self.area_overlay.winfo_exists():
                self.area_overlay.destroy()
                if self.area_overlay in self.active_overlays:
                    self.active_overlays.remove(self.area_overlay)
            self.area_overlay = None
        except Exception as e:
            print(f"Ошибка скрытия оверлея области: {e}")
            self.area_overlay = None
            
    def show_success_overlay(self, x: int, y: int, duration: float = 2.0):
        """Показ оверлея успешного действия"""
        try:
            size = 20
            overlay = self.create_overlay_window(
                x - size, y - size, x + size, y + size,
                color=OVERLAY_COLORS["SUCCESS"],
                width=3,
                alpha=0.8
            )
            
            if overlay:
                # Автоматически скрываем через указанное время
                threading.Timer(duration, lambda: self._hide_overlay(overlay)).start()
                
        except Exception as e:
            print(f"Ошибка показа оверлея успеха: {e}")
            
    def _hide_overlay(self, overlay: tk.Toplevel):
        """Скрытие конкретного оверлея"""
        try:
            if overlay and overlay.winfo_exists():
                overlay.destroy()
                if overlay in self.active_overlays:
                    self.active_overlays.remove(overlay)
        except Exception:
            pass
            
    def force_cleanup_overlays(self):
        """Принудительная очистка всех оверлеев"""
        try:
            print("Принудительная очистка всех оверлеев...")
            
            # Закрываем все активные оверлеи
            for overlay in self.active_overlays.copy():
                try:
                    if overlay and overlay.winfo_exists():
                        overlay.destroy()
                except:
                    pass
                    
            # Очищаем списки
            self.active_overlays.clear()
            self.selection_overlay = None
            self.area_overlay = None
            
            print("Все оверлеи очищены")
        except Exception as e:
            print(f"Ошибка принудительной очистки оверлеев: {e}")
            
    def cleanup_old_overlays(self):
        """Очистка устаревших оверлеев"""
        try:
            # Проверяем все активные оверлеи
            for overlay in self.active_overlays.copy():
                try:
                    if not overlay or not overlay.winfo_exists():
                        self.active_overlays.remove(overlay)
                except:
                    # Если оверлей недоступен, удаляем из списка
                    if overlay in self.active_overlays:
                        self.active_overlays.remove(overlay)
                        
        except Exception as e:
            print(f"Ошибка очистки старых оверлеев: {e}")
            
    def get_active_overlays_count(self) -> int:
        """Получение количества активных оверлеев"""
        self.cleanup_old_overlays()
        return len(self.active_overlays)
        
    def hide_all_overlays(self):
        """Скрытие всех оверлеев"""
        self.hide_selection_overlay()
        self.hide_area_overlay()
        self.force_cleanup_overlays() 