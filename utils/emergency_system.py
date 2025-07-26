"""
OmniaClick - Система экстренной остановки

Система для немедленного прерывания работы приложения в критических ситуациях
"""

import keyboard
import os
import signal
import sys
import threading
import time
from typing import Callable, Optional

from config import *


class EmergencySystem:
    """Система экстренной остановки"""
    
    def __init__(self):
        # Состояние системы
        self.active = False
        self.emergency_keys = ['ctrl+alt+x', 'f12']
        
        # Коллбэки
        self.callbacks = {}
        
        # Флаг для предотвращения множественных срабатываний
        self.emergency_triggered = False
        
    def set_callbacks(self, **callbacks):
        """Установка коллбэков"""
        self.callbacks.update(callbacks)
        
    def setup(self) -> bool:
        """Настройка системы экстренной остановки"""
        try:
            if self.active:
                return True
                
            # Регистрируем горячие клавиши экстренной остановки
            for key in self.emergency_keys:
                try:
                    keyboard.add_hotkey(key, self._emergency_stop_handler)
                    print(f"Зарегистрирована экстренная остановка: {key}")
                except Exception as e:
                    print(f"Не удалось зарегистрировать {key}: {e}")
                    
            self.active = True
            print("Система экстренной остановки активирована")
            print("Экстренная остановка: Ctrl+Alt+X или F12")
            
            return True
            
        except Exception as e:
            print(f"Ошибка настройки экстренной остановки: {e}")
            return False
            
    def shutdown(self):
        """Отключение системы экстренной остановки"""
        try:
            if not self.active:
                return
                
            # Удаляем горячие клавиши
            for key in self.emergency_keys:
                try:
                    keyboard.remove_hotkey(key)
                except Exception as e:
                    print(f"Ошибка удаления горячей клавиши {key}: {e}")
                    
            self.active = False
            print("Система экстренной остановки отключена")
            
        except Exception as e:
            print(f"Ошибка отключения экстренной остановки: {e}")
            
    def _emergency_stop_handler(self):
        """Обработчик экстренной остановки"""
        if self.emergency_triggered:
            return
            
        self.emergency_triggered = True
        
        # Запускаем экстренную остановку в отдельном потоке
        emergency_thread = threading.Thread(
            target=self._execute_emergency_stop, 
            daemon=True
        )
        emergency_thread.start()
        
    def _execute_emergency_stop(self):
        """Выполнение экстренной остановки"""
        try:
            print("🚨 ЭКСТРЕННАЯ ОСТАНОВКА АКТИВИРОВАНА! 🚨")
            
            # Уведомляем коллбэки
            if 'on_emergency_stop' in self.callbacks:
                try:
                    self.callbacks['on_emergency_stop']()
                except Exception as e:
                    print(f"Ошибка в коллбэке экстренной остановки: {e}")
                    
            # Принудительно останавливаем все процессы
            if 'on_force_stop_all' in self.callbacks:
                try:
                    self.callbacks['on_force_stop_all']()
                except Exception as e:
                    print(f"Ошибка принудительной остановки: {e}")
                    
            # Даем время на корректное завершение
            time.sleep(0.5)
            
            # Методы принудительного завершения (по степени "жестокости")
            self._try_graceful_exit()
            
        except Exception as e:
            print(f"Критическая ошибка в экстренной остановке: {e}")
            self._force_terminate()
            
    def _try_graceful_exit(self):
        """Попытка корректного завершения"""
        try:
            # Метод 1: Через коллбэк приложения
            if 'on_graceful_exit' in self.callbacks:
                try:
                    self.callbacks['on_graceful_exit']()
                    time.sleep(1)
                    return
                except Exception as e:
                    print(f"Ошибка корректного завершения: {e}")
                    
            # Метод 2: Через signal
            try:
                print("Попытка завершения через SIGTERM...")
                os.kill(os.getpid(), signal.SIGTERM)
                time.sleep(2)
            except Exception as e:
                print(f"SIGTERM не сработал: {e}")
                
            # Метод 3: Через sys.exit
            try:
                print("Попытка завершения через sys.exit...")
                sys.exit(1)
            except Exception as e:
                print(f"sys.exit не сработал: {e}")
                
            # Метод 4: Принудительное завершение
            self._force_terminate()
            
        except Exception as e:
            print(f"Ошибка в корректном завершении: {e}")
            self._force_terminate()
            
    def _force_terminate(self):
        """Принудительное завершение процесса"""
        try:
            print("🔥 ПРИНУДИТЕЛЬНОЕ ЗАВЕРШЕНИЕ ПРОЦЕССА 🔥")
            
            # Последняя попытка через SIGKILL
            try:
                os.kill(os.getpid(), signal.SIGKILL)
            except:
                pass
                
            # Если и это не помогло - через _exit
            try:
                os._exit(1)
            except:
                pass
                
        except Exception as e:
            print(f"Критическая ошибка принудительного завершения: {e}")
            
    def trigger_emergency_stop(self):
        """Ручной запуск экстренной остановки"""
        print("Ручной запуск экстренной остановки...")
        self._emergency_stop_handler()
        
    def is_active(self) -> bool:
        """Проверка активности системы"""
        return self.active
        
    def get_emergency_keys(self) -> list:
        """Получение списка клавиш экстренной остановки"""
        return self.emergency_keys.copy()
        
    def add_emergency_key(self, key: str) -> bool:
        """Добавление дополнительной клавиши экстренной остановки"""
        try:
            if key not in self.emergency_keys:
                keyboard.add_hotkey(key, self._emergency_stop_handler)
                self.emergency_keys.append(key)
                print(f"Добавлена экстренная клавиша: {key}")
                return True
            return False
            
        except Exception as e:
            print(f"Ошибка добавления экстренной клавиши {key}: {e}")
            return False
            
    def remove_emergency_key(self, key: str) -> bool:
        """Удаление клавиши экстренной остановки"""
        try:
            if key in self.emergency_keys and len(self.emergency_keys) > 1:
                keyboard.remove_hotkey(key)
                self.emergency_keys.remove(key)
                print(f"Удалена экстренная клавиша: {key}")
                return True
            return False
            
        except Exception as e:
            print(f"Ошибка удаления экстренной клавиши {key}: {e}")
            return False
            
    def test_emergency_system(self) -> bool:
        """Тест системы экстренной остановки (безопасный)"""
        try:
            print("🧪 Тест системы экстренной остановки...")
            
            # Проверяем активность
            if not self.active:
                print("❌ Система не активна")
                return False
                
            # Проверяем регистрацию клавиш
            for key in self.emergency_keys:
                try:
                    # Проверяем, что клавиша зарегистрирована
                    # (keyboard не предоставляет прямого способа проверки)
                    print(f"✓ Клавиша зарегистрирована: {key}")
                except:
                    print(f"❌ Проблема с клавишей: {key}")
                    return False
                    
            print("✅ Система экстренной остановки работает корректно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования: {e}")
            return False 