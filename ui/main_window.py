"""
OmniaClick - Главное окно приложения

Главный GUI класс с системой вкладок, сохраняющий полную функциональность оригинала
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

from config import *
from .tabs.main_tab import MainTab
from .tabs.modes_tab import ModesTab


class MainWindow:
    """Главное окно приложения с системой вкладок"""
    
    def __init__(self, app_instance):
        """
        Инициализация главного окна
        
        Args:
            app_instance: Экземпляр OmniaClickApp для доступа ко всем компонентам
        """
        self.app = app_instance
        self.window = app_instance.window
        
        # Настройка окна
        self._setup_window()
        
        # Создание системы вкладок
        self._setup_tabs()
        
        # Инициализация вкладок
        self._init_tabs()
        
        # Настройка обработчиков
        self._setup_event_handlers()
        
    def _setup_window(self):
        """Настройка главного окна"""
        self.window.title(APP_TITLE)
        self.window.geometry(WINDOW_GEOMETRY)
        self.window.resizable(False, False)
        
        # Парсим размеры из WINDOW_GEOMETRY для минимального размера
        width, height = map(int, WINDOW_GEOMETRY.split('x'))
        self.window.minsize(width, height)
        
        # Центрирование окна
        self._center_window()
        
        # Настройки pyautogui
        import pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0
        
    def _center_window(self):
        """Центрирование окна на экране"""
        # Принудительно устанавливаем размер
        self.window.geometry(WINDOW_GEOMETRY)
        self.window.update_idletasks()
        
        # Парсим размеры из WINDOW_GEOMETRY
        width, height = map(int, WINDOW_GEOMETRY.split('x'))
        
        # Вычисляем позицию для центрирования
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        
        # Устанавливаем окончательную геометрию
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
    def _setup_tabs(self):
        """Создание системы вкладок"""
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def _init_tabs(self):
        """Инициализация всех вкладок"""
        # Основная вкладка
        self.main_tab = MainTab(self.notebook, self.app)
        
        # Вкладка режимов кликов
        self.modes_tab = ModesTab(self.notebook, self.app)
        
        # Добавляем вкладки к notebook
        self.notebook.add(self.main_tab.frame, text="Основное")
        self.notebook.add(self.modes_tab.frame, text="Режимы кликов")
        
    def _setup_event_handlers(self):
        """Настройка обработчиков событий"""
        # Обработчик закрытия окна
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Биндинг для обновления статуса
        self.window.bind("<<StatusUpdate>>", self._on_status_update)
        self.window.bind("<<CountUpdate>>", self._on_count_update)
        
    def _on_status_update(self, event=None):
        """Обработчик обновления статуса"""
        if hasattr(self, 'main_tab'):
            self.main_tab.update_status()
            
    def _on_count_update(self, event=None):
        """Обработчик обновления счетчика"""
        if hasattr(self, 'main_tab'):
            self.main_tab.update_count()
            
    def _on_closing(self):
        """Обработчик закрытия приложения"""
        self.app._on_closing()
        
    def update_status(self, status):
        """Обновление статуса в интерфейсе"""
        if hasattr(self, 'main_tab'):
            self.main_tab.set_status(status)
            
    def update_count(self, count):
        """Обновление счетчика в интерфейсе"""
        if hasattr(self, 'main_tab'):
            self.main_tab.set_count(count)
            
    def set_buttons_state(self, clicking):
        """Установка состояния кнопок управления"""
        if hasattr(self, 'main_tab'):
            self.main_tab.set_buttons_state(clicking)
            
    def show_message(self, title, message, msg_type="info"):
        """Показ сообщения пользователю"""
        if msg_type == "info":
            messagebox.showinfo(title, message)
        elif msg_type == "warning":
            messagebox.showwarning(title, message)
        elif msg_type == "error":
            messagebox.showerror(title, message)
            
    def hide_to_tray(self):
        """Сворачивание в трей"""
        self.window.withdraw()
        
    def show_from_tray(self):
        """Показ из трея"""
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
        
    def get_current_settings(self):
        """Получение текущих настроек из GUI"""
        settings = {}
        
        # Настройки из основной вкладки
        if hasattr(self, 'main_tab'):
            settings.update(self.main_tab.get_settings())
            
        # Настройки из вкладки режимов
        if hasattr(self, 'modes_tab'):
            settings.update(self.modes_tab.get_settings())
            
        return settings
        
    def apply_settings(self, settings):
        """Применение настроек к GUI"""
        try:
            # Применяем к основной вкладке
            if hasattr(self, 'main_tab'):
                self.main_tab.apply_settings(settings)
                
            # Применяем к вкладке режимов
            if hasattr(self, 'modes_tab'):
                self.modes_tab.apply_settings(settings)
                
            return True
        except Exception as e:
            print(f"Ошибка применения настроек к GUI: {e}")
            return False
            
    def refresh_mode_display(self):
        """Обновление отображения режима"""
        if hasattr(self, 'modes_tab'):
            self.modes_tab.mode_changed() 
            
    def apply_color_selection(self, color):
        """Применение выбранного цвета"""
        if hasattr(self, 'modes_tab'):
            self.modes_tab.target_color_var.set(color)
            self.modes_tab.color_display.config(bg=color)
            
    def apply_template_selection(self, template_path, template_name):
        """Применение выбранного шаблона"""
        if hasattr(self, 'modes_tab'):
            self.modes_tab.template_image = template_path
            self.modes_tab.template_label.config(text=f"Шаблон: {template_name}")
            
    def update_sequence_display(self, sequence):
        """Обновление отображения последовательности"""
        if hasattr(self, 'modes_tab'):
            self.modes_tab.update_sequence_display(sequence)
            
    def highlight_sequence_item(self, index):
        """Подсветка элемента последовательности"""
        if hasattr(self, 'modes_tab'):
            self.modes_tab.highlight_sequence_item(index)
            
    def reset_sequence_highlight(self):
        """Сброс подсветки последовательности"""
        if hasattr(self, 'modes_tab'):
            self.modes_tab.reset_sequence_highlight()
            
    def select_sequence_item(self, index):
        """Выбор элемента последовательности"""
        if hasattr(self, 'modes_tab'):
            self.modes_tab.select_sequence_item(index) 