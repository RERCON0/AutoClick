"""
OmniaClick - Основная вкладка

Основная вкладка с настройками интервала, кнопками управления,
горячими клавишами и дополнительными опциями
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re

from config import *


class MainTab:
    """Основная вкладка интерфейса"""
    
    def __init__(self, parent, app_instance):
        """
        Инициализация основной вкладки
        
        Args:
            parent: Родительский notebook
            app_instance: Экземпляр OmniaClickApp
        """
        self.app = app_instance
        self.parent = parent
        
        # Создание главного фрейма
        self.frame = ttk.Frame(parent)
        
        # GUI переменные
        self._init_variables()
        
        # Настройка интерфейса
        self._setup_gui()
        
        # Настройка обработчиков
        self._setup_event_handlers()
        
    def _init_variables(self):
        """Инициализация GUI переменных"""
        # Основные настройки
        self.interval_var = self.app.interval_var
        self.click_type_var = self.app.click_type_var
        self.turbo_mode_var = self.app.turbo_mode_var
        self.extreme_mode_var = self.app.extreme_mode_var
        
        # Дополнительные настройки (значения по умолчанию из скриншота)
        self.sound_notifications_var = tk.BooleanVar(value=True)      # Звуковые уведомления: ВКЛ
        self.pause_on_mouse_var = tk.BooleanVar(value=True)           # Пауза при движении мыши: ВКЛ
        self.pause_on_window_var = tk.BooleanVar(value=True)          # Автопауза при переключении окон: ВКЛ
        self.always_on_top_var = tk.BooleanVar(value=False)           # Всегда поверх всех окон: ВЫКЛ
        
        # Горячие клавиши
        self.hotkey_start_var = tk.StringVar(value=DEFAULT_HOTKEY_START)
        self.hotkey_stop_var = tk.StringVar(value=DEFAULT_HOTKEY_STOP)
        
    def _setup_gui(self):
        """Настройка интерфейса основной вкладки"""
        # Заголовок
        title_label = ttk.Label(self.frame, text=APP_NAME, 
                               font=FONT_TITLE)
        title_label.pack(pady=(10, 20))
        
        # Настройки интервала
        self._setup_interval_settings()
        
        # Тип клика
        self._setup_click_type()
        
        # Статус
        self._setup_status()
        
        # Кнопки управления
        self._setup_control_buttons()
        
        # Дополнительные кнопки
        self._setup_extra_buttons()
        
        # Горячие клавиши
        self._setup_hotkeys()
        
        # Дополнительные настройки
        self._setup_additional_settings()
        
        # Информация об экстренной остановке
        self._setup_emergency_info()
        
    def _setup_interval_settings(self):
        """Настройки интервала"""
        settings_frame = ttk.LabelFrame(self.frame, text="Настройки кликов", padding="10")
        settings_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Интервал между кликами
        ttk.Label(settings_frame, text="Интервал между кликами (сек):").pack(anchor=tk.W, pady=(10, 5))
        
        interval_frame = ttk.Frame(settings_frame)
        interval_frame.pack(fill=tk.X, pady=5)
        
        # Валидация для поля ввода интервала
        vcmd = (self.frame.register(self._validate_interval_entry), '%P')
        self.interval_entry = ttk.Entry(interval_frame, width=10, textvariable=self.interval_var, 
                                       font=FONT_NORMAL, validate='key', validatecommand=vcmd)
        self.interval_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Обработка выделения текста для замены
        self.interval_entry.bind('<Key>', self._on_interval_key_press)
        
        # Кнопка "Применить" для интервала
        self.apply_interval_button = ttk.Button(interval_frame, text="✓", width=3, 
                                               command=self._apply_interval_change)
        self.apply_interval_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Обработка Enter для применения интервала
        self.interval_entry.bind('<Return>', self._apply_interval_change)
        
        # Отключаем автоматическое обновление переменной
        self.interval_entry.config(validate="none")
        
        ttk.Label(interval_frame, text="(0.001 - 2.0)", font=("Arial", 8), foreground="gray").pack(side=tk.RIGHT, padx=(5, 0))
        
        # Турбо режим
        ttk.Checkbutton(settings_frame, text="Турбо режим (минимальная задержка)", 
                       variable=self.turbo_mode_var, command=self._toggle_turbo).pack(anchor=tk.W, pady=2)
        
        # Экстремальный режим
        if WIN32_AVAILABLE:
            ttk.Checkbutton(settings_frame, text="⚡ ЭКСТРЕМАЛЬНЫЙ режим (до 10,000+ кликов/сек)", 
                           variable=self.extreme_mode_var, command=self._toggle_extreme).pack(anchor=tk.W, pady=2)
            ttk.Label(settings_frame, text="⚠️ Внимание: может вызвать нестабильность системы!", 
                     font=("Arial", 7), foreground="red").pack(anchor=tk.W, pady=(0, 5))
        else:
            ttk.Label(settings_frame, text="Экстремальный режим (недоступно - установите pywin32)", 
                     foreground="gray", font=("Arial", 8)).pack(anchor=tk.W, pady=2)
                     
    def _setup_click_type(self):
        """Настройка типа клика"""
        settings_frame = self.frame.winfo_children()[-1]  # Получаем последний созданный frame
        
        # Тип клика
        ttk.Label(settings_frame, text="Кнопка мыши:").pack(anchor=tk.W, pady=(10, 5))
        click_frame = ttk.Frame(settings_frame)
        click_frame.pack(fill=tk.X)
        
        ttk.Radiobutton(click_frame, text="Левая", variable=self.click_type_var, 
                       value="left").pack(side=tk.LEFT)
        ttk.Radiobutton(click_frame, text="Правая", variable=self.click_type_var, 
                       value="right").pack(side=tk.LEFT, padx=(20, 0))
        ttk.Radiobutton(click_frame, text="Средняя", variable=self.click_type_var, 
                       value="middle").pack(side=tk.LEFT, padx=(20, 0))
                       
    def _setup_status(self):
        """Настройка статуса"""
        status_frame = ttk.LabelFrame(self.frame, text="Статус", padding="10")
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Остановлен", 
                                     font=FONT_MAIN, foreground=COLORS["ERROR"])
        self.status_label.pack()
        
        self.count_label = ttk.Label(status_frame, text="Кликов: 0", 
                                    font=FONT_NORMAL)
        self.count_label.pack(pady=(5, 0))
        
    def _setup_control_buttons(self):
        """Настройка кнопок управления"""
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="Запустить", 
                                      command=self.app.start_clicking)
        self.start_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="Остановить", 
                                     command=self.app.stop_clicking, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
    def _setup_extra_buttons(self):
        """Дополнительные кнопки"""
        extra_frame = ttk.Frame(self.frame)
        extra_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Первый ряд кнопок
        row1_frame = ttk.Frame(extra_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.reset_button = ttk.Button(row1_frame, text="Сбросить счетчик", 
                                      command=self._reset_counter)
        self.reset_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.hide_button = ttk.Button(row1_frame, text="Свернуть в трей", 
                                     command=self._hide_to_tray)
        self.hide_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Второй ряд кнопок
        row2_frame = ttk.Frame(extra_frame)
        row2_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.save_button = ttk.Button(row2_frame, text="💾 Сохранить", 
                                     command=self._save_settings)
        self.save_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        self.load_button = ttk.Button(row2_frame, text="📂 Загрузить", 
                                     command=self._load_settings)
        self.load_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 2))
        
        self.cleanup_button = ttk.Button(row2_frame, text="Очистить файлы", 
                                        command=self._cleanup_temp_files)
        self.cleanup_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
    def _setup_hotkeys(self):
        """Настройка горячих клавиш"""
        hotkeys_frame = ttk.LabelFrame(self.frame, text="Горячие клавиши", padding="10")
        hotkeys_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Информация о настройке
        info_label = ttk.Label(hotkeys_frame, text="Кликните на поле и нажмите клавишу", 
                              font=("Arial", 9), foreground="blue")
        info_label.pack(pady=(0, 5))
        
        # Клавиша запуска
        start_frame = ttk.Frame(hotkeys_frame)
        start_frame.pack(fill=tk.X, pady=5)
        ttk.Label(start_frame, text="Запуск:").pack(side=tk.LEFT)
        self.start_hotkey_entry = ttk.Entry(start_frame, textvariable=self.hotkey_start_var, width=15, 
                                           justify='center', font=('Arial', 10, 'bold'), state='readonly')
        self.start_hotkey_entry.pack(side=tk.RIGHT)
        
        # Клавиша остановки
        stop_frame = ttk.Frame(hotkeys_frame)
        stop_frame.pack(fill=tk.X, pady=5)
        ttk.Label(stop_frame, text="Остановка:").pack(side=tk.LEFT)
        self.stop_hotkey_entry = ttk.Entry(stop_frame, textvariable=self.hotkey_stop_var, width=15,
                                          justify='center', font=('Arial', 10, 'bold'), state='readonly')
        self.stop_hotkey_entry.pack(side=tk.RIGHT)
        
        # Настройка перехвата клавиш для полей ввода
        self._setup_hotkey_capture()
        
        ttk.Button(hotkeys_frame, text="Применить горячие клавиши", 
                  command=self._apply_hotkeys).pack(pady=10)
                  
    def _setup_additional_settings(self):
        """Настройка дополнительных опций"""
        extra_settings_frame = ttk.LabelFrame(self.frame, text="Дополнительно", padding="10")
        extra_settings_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Checkbutton(extra_settings_frame, text="Звуковые уведомления", 
                       variable=self.sound_notifications_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(extra_settings_frame, text="Пауза при движении мыши", 
                       variable=self.pause_on_mouse_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(extra_settings_frame, text="Всегда поверх всех окон", 
                       variable=self.always_on_top_var, command=self._toggle_always_on_top).pack(anchor=tk.W, pady=2)
        
        # Автопауза только если win32gui доступен
        if WIN32_AVAILABLE:
            ttk.Checkbutton(extra_settings_frame, text="Автопауза при переключении окон", 
                           variable=self.pause_on_window_var).pack(anchor=tk.W, pady=2)
        else:
            ttk.Label(extra_settings_frame, text="Автопауза при переключении окон (недоступно - установите pywin32)", 
                     foreground="gray", font=("Arial", 8)).pack(anchor=tk.W, pady=2)
                     
    def _setup_emergency_info(self):
        """Информация об экстренной остановке"""
        emergency_frame = ttk.Frame(self.frame)
        emergency_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        emergency_label = ttk.Label(emergency_frame, text="🚨 Экстренная остановка: ESC, F12 или Ctrl+Alt+X", 
                                   font=("Arial", 9), foreground="red")
        emergency_label.pack()
        
    def _setup_event_handlers(self):
        """Настройка обработчиков событий"""
        pass
        
    def _setup_hotkey_capture(self):
        """Настройка перехвата горячих клавиш"""
        # Пока заглушка - реализуем позже если нужно
        pass
        
    def _validate_interval_entry(self, value):
        """Валидация поля ввода интервала"""
        if value == "":
            return True
        allowed = "0123456789.,"
        for char in value:
            if char not in allowed:
                return False
        return True
        
    def _apply_interval_change(self, event=None):
        """Применение изменения интервала"""
        try:
            value = self.interval_entry.get()
            if not value:
                return
                
            value = value.replace(",", ".").strip()
            if not value:
                return
                
            interval = float(value)
            
            # Ограничиваем диапазон
            if interval < 0.001:
                interval = 0.001
            elif interval > 2.0:
                interval = 2.0
                
            # Применяем значение
            self.interval_var.set(f"{interval:.3f}")
            
            # Обновляем кликер
            self.app.clicker.set_interval(interval)
            
            # Визуальная обратная связь
            self.apply_interval_button.config(text="OK")
            self.frame.after(1000, lambda: self.apply_interval_button.config(text="✓"))
            
        except Exception as e:
            print(f"Ошибка применения интервала: {e}")
            
    def _on_interval_key_press(self, event):
        """Обработка нажатий клавиш в поле интервала"""
        # Обработка выделения текста для замены
        try:
            selection = self.interval_entry.selection_get()
            if selection and event.char in "0123456789.,":
                self.interval_entry.delete("sel.first", "sel.last")
                self.interval_entry.insert("insert", event.char)
                return "break"
        except tk.TclError:
            pass
            
    def _toggle_turbo(self):
        """Переключение турбо режима"""
        turbo = self.turbo_mode_var.get()
        self.app.clicker.set_turbo_mode(turbo)
        
        if turbo and self.extreme_mode_var.get():
            self.extreme_mode_var.set(False)
            self.app.clicker.set_extreme_mode(False)
            
    def _toggle_extreme(self):
        """Переключение экстремального режима"""
        extreme = self.extreme_mode_var.get()
        self.app.clicker.set_extreme_mode(extreme)
        
        if extreme and self.turbo_mode_var.get():
            self.turbo_mode_var.set(False)
            self.app.clicker.set_turbo_mode(False)
            
    def _toggle_always_on_top(self):
        """Переключение режима поверх всех окон"""
        on_top = self.always_on_top_var.get()
        self.app.window.attributes('-topmost', on_top)
        
    def _reset_counter(self):
        """Сброс счетчика кликов"""
        self.app.clicker.reset_counter()
        self.app.gui.update_count(0)
        
    def _hide_to_tray(self):
        """Сворачивание в системный трей"""
        self.app.gui.hide_to_tray()
        
    def _save_settings(self):
        """Сохранение настроек"""
        self.app.save_settings()
        
    def _load_settings(self):
        """Загрузка настроек"""
        self.app.load_settings()
        
    def _cleanup_temp_files(self):
        """Очистка временных файлов"""
        self.app.cleanup_temp_files()
        
    def _apply_hotkeys(self):
        """Применение горячих клавиш"""
        start_key = self.hotkey_start_var.get()
        stop_key = self.hotkey_stop_var.get()
        
        self.app.hotkey_manager.set_start_hotkey(start_key)
        self.app.hotkey_manager.set_stop_hotkey(stop_key)
        
        messagebox.showinfo("Горячие клавиши", "Горячие клавиши обновлены!")
        
    def set_status(self, status):
        """Установка статуса"""
        if status == "running":
            self.status_label.config(text="Активен", foreground=COLORS["SUCCESS"])
        else:
            self.status_label.config(text="Остановлен", foreground=COLORS["ERROR"])
            
    def set_count(self, count):
        """Установка счетчика"""
        self.count_label.config(text=f"Кликов: {count}")
        
    def update_status(self):
        """Обновление статуса"""
        if self.app.clicker.is_running():
            self.set_status("running")
        else:
            self.set_status("stopped")
            
    def update_count(self):
        """Обновление счетчика"""
        count = self.app.clicker.get_click_count()
        self.set_count(count)
        
    def set_buttons_state(self, clicking):
        """Установка состояния кнопок"""
        if clicking:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
    def get_settings(self):
        """Получение настроек из основной вкладки"""
        return {
            "interval": self.interval_var.get(),
            "click_type": self.click_type_var.get(),
            "turbo_mode": self.turbo_mode_var.get(),
            "extreme_mode": self.extreme_mode_var.get(),
            "sound_notifications": self.sound_notifications_var.get(),
            "pause_on_mouse": self.pause_on_mouse_var.get(),
            "pause_on_window": self.pause_on_window_var.get(),
            "always_on_top": self.always_on_top_var.get(),
            "hotkey_start": self.hotkey_start_var.get(),
            "hotkey_stop": self.hotkey_stop_var.get(),
        }
        
    def apply_settings(self, settings):
        """Применение настроек к основной вкладке"""
        try:
            self.interval_var.set(settings.get("interval", DEFAULT_INTERVAL))
            self.click_type_var.set(settings.get("click_type", DEFAULT_CLICK_TYPE))
            self.turbo_mode_var.set(settings.get("turbo_mode", False))
            self.extreme_mode_var.set(settings.get("extreme_mode", False))
            self.sound_notifications_var.set(settings.get("sound_notifications", True))
            self.pause_on_mouse_var.set(settings.get("pause_on_mouse", False))
            self.pause_on_window_var.set(settings.get("pause_on_window", False))
            self.always_on_top_var.set(settings.get("always_on_top", False))
            self.hotkey_start_var.set(settings.get("hotkey_start", DEFAULT_HOTKEY_START))
            self.hotkey_stop_var.set(settings.get("hotkey_stop", DEFAULT_HOTKEY_STOP))
            
            # Применяем настройки к компонентам
            self._toggle_always_on_top()
            
        except Exception as e:
            print(f"Ошибка применения настроек к основной вкладке: {e}") 