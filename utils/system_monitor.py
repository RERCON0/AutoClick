"""
OmniaClick - Мониторинг системы

Система для отслеживания активности пользователя и состояния системы
"""

import threading
import time
import pyautogui
from typing import Optional, Callable

from config import *

if WIN32_AVAILABLE:
    import win32gui
    import win32api


class SystemMonitor:
    """Мониторинг системы и активности пользователя"""
    
    def __init__(self):
        # Состояние мониторинга
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Последние зафиксированные состояния
        self.last_mouse_position = None
        self.last_active_window = None
        self.last_activity_time = time.time()
        
        # Настройки мониторинга
        self.mouse_sensitivity = 5  # пикселей для срабатывания
        self.activity_timeout = 1.0  # секунд бездействия
        self.monitor_interval = 0.1  # интервал проверки
        
        # Коллбэки
        self.callbacks = {}
        
        # Флаги состояния
        self.user_activity_detected = False
        self.window_change_detected = False
        
    def set_callbacks(self, **callbacks):
        """Установка коллбэков"""
        self.callbacks.update(callbacks)
        
    def start_monitoring(self) -> bool:
        """Запуск мониторинга"""
        try:
            if self.monitoring:
                return True
                
            if not WIN32_AVAILABLE:
                print("Мониторинг недоступен (требуется win32api)")
                return False
                
            self.monitoring = True
            self.user_activity_detected = False
            self.window_change_detected = False
            
            # Инициализируем начальные состояния
            self._update_initial_state()
            
            # Запускаем поток мониторинга
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop, 
                daemon=True
            )
            self.monitor_thread.start()
            
            print("Мониторинг системы запущен")
            return True
            
        except Exception as e:
            print(f"Ошибка запуска мониторинга: {e}")
            self.monitoring = False
            return False
            
    def stop_monitoring(self):
        """Остановка мониторинга"""
        try:
            if not self.monitoring:
                return
                
            self.monitoring = False
            
            # Ожидаем завершения потока
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=1.0)
                
            self.monitor_thread = None
            print("Мониторинг системы остановлен")
            
        except Exception as e:
            print(f"Ошибка остановки мониторинга: {e}")
            
    def _update_initial_state(self):
        """Обновление начального состояния"""
        try:
            # Начальная позиция мыши
            self.last_mouse_position = pyautogui.position()
            
            # Начальное активное окно
            if WIN32_AVAILABLE:
                self.last_active_window = win32gui.GetForegroundWindow()
                
            self.last_activity_time = time.time()
            
        except Exception as e:
            print(f"Ошибка инициализации состояния: {e}")
            
    def _monitor_loop(self):
        """Основной цикл мониторинга"""
        try:
            while self.monitoring:
                try:
                    # Проверяем движение мыши
                    self._check_mouse_activity()
                    
                    # Проверяем смену активного окна
                    self._check_window_activity()
                    
                    # Обрабатываем обнаруженную активность
                    self._process_activity()
                    
                except Exception as e:
                    print(f"Ошибка в цикле мониторинга: {e}")
                    
                time.sleep(self.monitor_interval)
                
        except Exception as e:
            print(f"Критическая ошибка мониторинга: {e}")
        finally:
            self.monitoring = False
            
    def _check_mouse_activity(self):
        """Проверка движения мыши"""
        try:
            current_position = pyautogui.position()
            
            if self.last_mouse_position:
                # Вычисляем расстояние перемещения
                dx = abs(current_position[0] - self.last_mouse_position[0])
                dy = abs(current_position[1] - self.last_mouse_position[1])
                
                # Проверяем превышение чувствительности
                if dx >= self.mouse_sensitivity or dy >= self.mouse_sensitivity:
                    self.user_activity_detected = True
                    self.last_activity_time = time.time()
                    
                    if 'on_mouse_activity' in self.callbacks:
                        self.callbacks['on_mouse_activity'](current_position, (dx, dy))
                        
            self.last_mouse_position = current_position
            
        except Exception as e:
            print(f"Ошибка проверки мыши: {e}")
            
    def _check_window_activity(self):
        """Проверка смены активного окна"""
        try:
            if not WIN32_AVAILABLE:
                return
                
            current_window = win32gui.GetForegroundWindow()
            
            if self.last_active_window and current_window != self.last_active_window:
                self.window_change_detected = True
                self.last_activity_time = time.time()
                
                if 'on_window_change' in self.callbacks:
                    try:
                        # Получаем информацию об окнах
                        old_title = win32gui.GetWindowText(self.last_active_window) if self.last_active_window else ""
                        new_title = win32gui.GetWindowText(current_window)
                        
                        self.callbacks['on_window_change'](
                            self.last_active_window, 
                            current_window,
                            old_title,
                            new_title
                        )
                    except Exception as e:
                        print(f"Ошибка в коллбэке смены окна: {e}")
                        
            self.last_active_window = current_window
            
        except Exception as e:
            print(f"Ошибка проверки окна: {e}")
            
    def _process_activity(self):
        """Обработка обнаруженной активности"""
        try:
            # Проверяем общую активность
            if self.user_activity_detected or self.window_change_detected:
                if 'on_user_activity' in self.callbacks:
                    self.callbacks['on_user_activity'](
                        self.user_activity_detected,
                        self.window_change_detected
                    )
                    
                # Сбрасываем флаги активности
                self.user_activity_detected = False
                self.window_change_detected = False
                
            # Проверяем тайм-аут бездействия
            elif time.time() - self.last_activity_time > self.activity_timeout:
                if 'on_idle_detected' in self.callbacks:
                    idle_time = time.time() - self.last_activity_time
                    self.callbacks['on_idle_detected'](idle_time)
                    
        except Exception as e:
            print(f"Ошибка обработки активности: {e}")
            
    def force_activity_reset(self):
        """Принудительный сброс детекции активности"""
        self.user_activity_detected = False
        self.window_change_detected = False
        self.last_activity_time = time.time()
        
        if 'on_activity_reset' in self.callbacks:
            self.callbacks['on_activity_reset']()
            
    def set_sensitivity(self, mouse_sensitivity: int = None, activity_timeout: float = None):
        """Настройка чувствительности мониторинга"""
        if mouse_sensitivity is not None:
            self.mouse_sensitivity = max(1, mouse_sensitivity)
            
        if activity_timeout is not None:
            self.activity_timeout = max(0.1, activity_timeout)
            
        print(f"Чувствительность: мышь={self.mouse_sensitivity}px, тайм-аут={self.activity_timeout}с")
        
    def get_current_state(self) -> dict:
        """Получение текущего состояния системы"""
        try:
            state = {
                "monitoring": self.monitoring,
                "mouse_position": self.last_mouse_position,
                "activity_detected": self.user_activity_detected or self.window_change_detected,
                "last_activity_time": self.last_activity_time,
                "idle_time": time.time() - self.last_activity_time
            }
            
            if WIN32_AVAILABLE and self.last_active_window:
                try:
                    state["active_window_title"] = win32gui.GetWindowText(self.last_active_window)
                    state["active_window_handle"] = self.last_active_window
                except:
                    state["active_window_title"] = "Неизвестно"
                    state["active_window_handle"] = None
                    
            return state
            
        except Exception as e:
            print(f"Ошибка получения состояния: {e}")
            return {"error": str(e)}
            
    def is_monitoring(self) -> bool:
        """Проверка активности мониторинга"""
        return self.monitoring
        
    def get_activity_status(self) -> tuple:
        """Получение статуса активности (mouse_activity, window_activity)"""
        return (self.user_activity_detected, self.window_change_detected)
        
    def setup_user_activity_monitor(self):
        """Настройка специфичного мониторинга активности пользователя"""
        # Эта функция была в оригинальном коде, добавляем для совместимости
        return self.start_monitoring() 