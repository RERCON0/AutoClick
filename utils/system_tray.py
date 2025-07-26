"""
Модуль для управления системным треем
Содержит SystemTrayManager класс для работы с иконкой в трее
"""

import pystray
from pystray import MenuItem, Icon
from PIL import Image, ImageDraw
import threading
import io
import base64
from config import *

class SystemTrayManager:
    """Класс для управления системным треем"""
    
    def __init__(self):
        self.tray_icon = None
        self.running = False
        
        # Коллбэки
        self.on_show_callback = None
        self.on_start_callback = None
        self.on_stop_callback = None
        self.on_quit_callback = None
        
    def set_callbacks(self, on_show=None, on_start=None, on_stop=None, on_quit=None):
        """Установка коллбэков для действий трея"""
        self.on_show_callback = on_show
        self.on_start_callback = on_start
        self.on_stop_callback = on_stop
        self.on_quit_callback = on_quit
        
    def create_icon(self, status="stopped"):
        """Создание иконки для трея"""
        try:
            # Создаем простую иконку 16x16
            image = Image.new('RGBA', (16, 16), (255, 255, 255, 0))
            draw = ImageDraw.Draw(image)
            
            if status == "running":
                # Зеленый круг для активного состояния
                draw.ellipse([2, 2, 14, 14], fill=(0, 255, 0, 255), outline=(0, 200, 0, 255))
            else:
                # Красный круг для неактивного состояния
                draw.ellipse([2, 2, 14, 14], fill=(255, 0, 0, 255), outline=(200, 0, 0, 255))
                
            # Добавляем маленький символ в центр
            if status == "running":
                # Символ паузы (две вертикальные линии)
                draw.rectangle([6, 5, 7, 11], fill=(255, 255, 255, 255))
                draw.rectangle([9, 5, 10, 11], fill=(255, 255, 255, 255))
            else:
                # Символ воспроизведения (треугольник)
                draw.polygon([(6, 5), (6, 11), (11, 8)], fill=(255, 255, 255, 255))
                
            return image
            
        except Exception as e:
            print(f"Ошибка при создании иконки: {e}")
            # Возвращаем простую иконку по умолчанию
            return Image.new('RGBA', (16, 16), (100, 100, 100, 255))
            
    def create_menu(self):
        """Создание контекстного меню трея"""
        return pystray.Menu(
            MenuItem("Показать", self._on_show, default=True),
            MenuItem("Запустить", self._on_start),
            MenuItem("Остановить", self._on_stop),
            pystray.Menu.SEPARATOR,
            MenuItem("Выход", self._on_quit)
        )
        
    def setup_tray(self):
        """Настройка системного трея"""
        try:
            if self.tray_icon:
                return True
                
            icon_image = self.create_icon("stopped")
            self.tray_icon = Icon(
                name=APP_NAME,
                icon=icon_image,
                title=f"{APP_NAME} - Остановлен",
                menu=self.create_menu()
            )
            
            return True
            
        except Exception as e:
            print(f"Ошибка при настройке трея: {e}")
            return False
            
    def start_tray(self):
        """Запуск трея в отдельном потоке"""
        if not self.tray_icon or self.running:
            return False
            
        try:
            self.running = True
            tray_thread = threading.Thread(target=self._run_tray, daemon=True)
            tray_thread.start()
            return True
            
        except Exception as e:
            print(f"Ошибка при запуске трея: {e}")
            self.running = False
            return False
            
    def _run_tray(self):
        """Запуск трея (выполняется в отдельном потоке)"""
        try:
            self.tray_icon.run()
        except Exception as e:
            print(f"Ошибка в работе трея: {e}")
        finally:
            self.running = False
            
    def update_status(self, status, click_count=0):
        """Обновление статуса трея"""
        if not self.tray_icon or not self.running:
            return
            
        try:
            # Обновляем иконку
            new_icon = self.create_icon(status)
            self.tray_icon.icon = new_icon
            
            # Обновляем заголовок
            if status == "running":
                title = f"{APP_NAME} - Активен (кликов: {click_count})"
            else:
                title = f"{APP_NAME} - Остановлен"
                
            self.tray_icon.title = title
            
        except Exception as e:
            print(f"Ошибка при обновлении статуса трея: {e}")
            
    def stop_tray(self):
        """Остановка трея"""
        if not self.tray_icon or not self.running:
            return
            
        try:
            self.tray_icon.stop()
            self.running = False
            
        except Exception as e:
            print(f"Ошибка при остановке трея: {e}")
            
    def _on_show(self, icon=None, item=None):
        """Обработчик показа главного окна"""
        if self.on_show_callback:
            threading.Thread(target=self.on_show_callback, args=(icon, item), daemon=True).start()
            
    def _on_start(self, icon=None, item=None):
        """Обработчик запуска кликера"""
        if self.on_start_callback:
            threading.Thread(target=self.on_start_callback, daemon=True).start()
            
    def _on_stop(self, icon=None, item=None):
        """Обработчик остановки кликера"""
        if self.on_stop_callback:
            threading.Thread(target=self.on_stop_callback, daemon=True).start()
            
    def _on_quit(self, icon=None, item=None):
        """Обработчик выхода из приложения"""
        if self.on_quit_callback:
            self.on_quit_callback(icon, item)
            
    def is_running(self):
        """Проверка работы трея"""
        return self.running
        
    def show_notification(self, title, message, timeout=3):
        """Показ уведомления через трей"""
        if not self.tray_icon or not self.running:
            return False
            
        try:
            self.tray_icon.notify(message, title)
            return True
        except Exception as e:
            print(f"Ошибка при показе уведомления: {e}")
            return False 