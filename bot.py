"""
Автокликер Pro - расширенный автокликер с GUI

Требуемые библиотеки:
pip install pyautogui keyboard pillow pystray psutil opencv-python

Опциональные (для дополнительных функций):
pip install pywin32  # для автопаузы при переключении окон и экстремального режима

Поддерживаемые режимы:
- Обычный клик мыши
- Клик по цвету пикселя (с областью поиска)
- Поиск и клик по картинке (одиночный и последовательность)
- Нажатие клавиш (последовательность 1-5 клавиш)
- Последовательность точек (разное количество кликов)

Режимы скорости:
- Обычный: 0.01-2.0 сек интервал
- Турбо: 0.001 сек (до 1000 кликов/сек)
- Экстремальный: 0.0001 сек (до 10,000+ кликов/сек через win32api)
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog, simpledialog
import pyautogui
import threading
import time
import json
import os
import sys
import uuid
from PIL import Image, ImageTk
import keyboard
import winsound
import pystray
from pystray import MenuItem, Icon
import psutil

# Опциональный импорт win32gui
try:
    import win32gui
    import win32api
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("win32gui/win32api не установлены. Некоторые функции будут недоступны.")

# Опциональный импорт OpenCV для точности поиска картинок
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("OpenCV не установлен. Поиск картинок будет менее точным.")

class AutoClicker:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("OmniaClick")
        self.window.geometry("900x800")
        self.window.resizable(False, False)
        
        # Центрирование окна
        self.center_window()
        
        # Настройки
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0  # Убираем встроенную задержку pyautogui

        
        # Переменные состояния
        self.clicking = False
        self.area_selection_active = False  # Флаг для блокировки кликера во время выбора области
        self.hotkeys_disabled = False  # Флаг для отключения горячих клавиш
        self.active_overlays = []  # Список активных оверлеев для отслеживания
        self.click_count = 0
        self.click_thread = None
        self.last_mouse_pos = pyautogui.position()
        self.monitor_thread = None
        self.active_window = None
        
        # Переменные настроек
        self.interval_var = tk.DoubleVar(value=0.1)
        self.click_type = tk.StringVar(value="left")
        self.turbo_mode = tk.BooleanVar(value=False)
        self.extreme_mode = tk.BooleanVar(value=False)  # Экстремальный режим
        self.pause_on_mouse = tk.BooleanVar(value=False)
        self.pause_on_window = tk.BooleanVar(value=False)
        self.sound_notifications = tk.BooleanVar(value=True)
        self.hotkey_start = tk.StringVar(value="f6")
        self.hotkey_stop = tk.StringVar(value="f7")
        
        # Переменные для режимов
        self.click_mode = tk.StringVar(value="normal")  # normal, color, sequence, image, keyboard
        self.target_color = "#FF0000"
        self.color_tolerance = tk.IntVar(value=10)
        self.search_area = None  # Область поиска (x1, y1, x2, y2)
        self.overlay_window = None  # Окно для отображения выбранной области
        self.selection_overlay = None  # Окно для отображения процесса выбора
        self.template_image = None  # Путь к шаблонной картинке
        self.image_confidence = tk.DoubleVar(value=0.8)  # Точность поиска картинки
        self.image_sequence = []  # Последовательность картинок для поиска
        self.current_image_index = 0  # Текущий индекс в последовательности картинок
        self.image_sequence_clicks = 0  # Счетчик кликов для текущего шаблона
        
        # Переменные для нажатия клавиш
        self.keyboard_sequence = []  # Последовательность клавиш для нажатия
        self.current_keyboard_index = 0  # Текущий индекс в последовательности клавиш
        self.keyboard_sequence_presses = 0  # Счетчик нажатий для текущей клавиши
        
        # Последовательность кликов
        self.sequence_points = []
        self.current_sequence_index = 0
        
        # Переменная для режима изображений
        self.image_mode = tk.StringVar(value="single")
        
        # Переменные для управления последовательностью шаблонов
        self.image_sequence_repeats = tk.IntVar(value=1)  # Количество повторений всей последовательности
        self.image_sequence_repeat_count = 0  # Счетчик текущего повторения последовательности
        
        # Переменные для добавления клавиш в последовательность
        self.sequence_key_var = tk.StringVar(value="Нажмите клавишу...")
        self.sequence_key_presses_var = tk.IntVar(value=1)
        
        # Системный трей
        self.tray_icon = None
        
        self.last_user_activity = 0  # Время последней активности пользователя
        self.user_pause_timeout = 2.0  # секунд паузы после активности
        self.setup_user_activity_monitor()
        
        self.setup_gui()
        self.setup_hotkeys(False)  # Тихая установка горячих клавиш при запуске
        self.setup_emergency_stop()  # Настройка экстренной остановки
        self.setup_tray()
        self.start_monitoring()
        

        
        self.last_found_image_position = None
        self.last_image_template = None
        self.user_activity_detected = False
        
        # Переменные для оптимизации поиска по цвету
        self.last_found_color_position = None
        self.last_target_color = None
        self.last_color_tolerance = None
        
        # Счетчики для периодической проверки валидности позиций
        self.clicks_since_last_search = 0
        self.recheck_interval = 50  # Перепроверяем каждые 50 кликов
        
    def center_window(self):
        """Центрирование окна на экране"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_gui(self):
        # Создаем notebook для вкладок
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Основная вкладка
        self.setup_main_tab()
        
        # Вкладка режимов
        self.setup_modes_tab()
        

        
    def setup_main_tab(self):
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Основное")
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="OmniaClick", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(10, 20))
        
        # Настройки интервала
        settings_frame = ttk.LabelFrame(main_frame, text="Настройки кликов", padding="10")
        settings_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Интервал между кликами
        ttk.Label(settings_frame, text="Интервал между кликами (сек):").pack(anchor=tk.W, pady=(10, 5))
        
        interval_frame = ttk.Frame(settings_frame)
        interval_frame.pack(fill=tk.X, pady=5)
        
        # Валидация для поля ввода интервала
        vcmd = (self.window.register(self.validate_interval_entry), '%P')
        self.interval_entry = ttk.Entry(interval_frame, width=10, textvariable=self.interval_var, 
                                       font=('Arial', 10), validate='key', validatecommand=vcmd)
        self.interval_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.interval_var.trace('w', self.on_interval_entry_change)
        
        # Обработка выделения текста для замены
        self.interval_entry.bind('<Key>', self.on_interval_key_press)
        
        ttk.Label(interval_frame, text="(0.001 - 2.0)", font=("Arial", 8), foreground="gray").pack(side=tk.RIGHT, padx=(5, 0))
        
        # Турбо режим
        ttk.Checkbutton(settings_frame, text="Турбо режим (минимальная задержка)", 
                       variable=self.turbo_mode, command=self.toggle_turbo).pack(anchor=tk.W, pady=2)
        
        # Экстремальный режим
        if WIN32_AVAILABLE:
            ttk.Checkbutton(settings_frame, text="⚡ ЭКСТРЕМАЛЬНЫЙ режим (до 10,000+ кликов/сек)", 
                           variable=self.extreme_mode, command=self.toggle_extreme).pack(anchor=tk.W, pady=2)
            ttk.Label(settings_frame, text="⚠️ Внимание: может вызвать нестабильность системы!", 
                     font=("Arial", 7), foreground="red").pack(anchor=tk.W, pady=(0, 5))
        else:
            ttk.Label(settings_frame, text="Экстремальный режим (недоступно - установите pywin32)", 
                     foreground="gray", font=("Arial", 8)).pack(anchor=tk.W, pady=2)
        

        
        # Тип клика
        ttk.Label(settings_frame, text="Кнопка мыши:").pack(anchor=tk.W, pady=(10, 5))
        click_frame = ttk.Frame(settings_frame)
        click_frame.pack(fill=tk.X)
        
        ttk.Radiobutton(click_frame, text="Левая", variable=self.click_type, 
                       value="left").pack(side=tk.LEFT)
        ttk.Radiobutton(click_frame, text="Правая", variable=self.click_type, 
                       value="right").pack(side=tk.LEFT, padx=(20, 0))
        ttk.Radiobutton(click_frame, text="Средняя", variable=self.click_type, 
                       value="middle").pack(side=tk.LEFT, padx=(20, 0))
        
        # Статус
        status_frame = ttk.LabelFrame(main_frame, text="Статус", padding="10")
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Остановлен", 
                                     font=("Arial", 12), foreground="red")
        self.status_label.pack()
        
        self.count_label = ttk.Label(status_frame, text="Кликов: 0", 
                                    font=("Arial", 10))
        self.count_label.pack(pady=(5, 0))
        
        # Кнопки управления
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="Запустить", 
                                      command=self.start_clicking)
        self.start_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="Остановить", 
                                     command=self.stop_clicking, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Дополнительные кнопки
        extra_frame = ttk.Frame(main_frame)
        extra_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.reset_button = ttk.Button(extra_frame, text="Сбросить счетчик", 
                                      command=self.reset_counter)
        self.reset_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.hide_button = ttk.Button(extra_frame, text="Свернуть в трей", 
                                     command=self.hide_to_tray)
        self.hide_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Кнопки сохранения/загрузки настроек
        save_frame = ttk.Frame(extra_frame)
        save_frame.pack(side=tk.RIGHT)
        
        ttk.Button(save_frame, text="💾 Сохранить", 
                  command=self.save_current_settings).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(save_frame, text="📂 Загрузить", 
                  command=self.load_saved_settings).pack(side=tk.LEFT)
        
        # Горячие клавиши
        hotkeys_frame = ttk.LabelFrame(main_frame, text="Горячие клавиши", padding="10")
        hotkeys_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Информация о настройке
        info_label = ttk.Label(hotkeys_frame, text="Кликните на поле и нажмите клавишу", 
                              font=("Arial", 9), foreground="blue")
        info_label.pack(pady=(0, 5))
        
        # Клавиша запуска
        start_frame = ttk.Frame(hotkeys_frame)
        start_frame.pack(fill=tk.X, pady=5)
        ttk.Label(start_frame, text="Запуск:").pack(side=tk.LEFT)
        self.start_hotkey_entry = ttk.Entry(start_frame, textvariable=self.hotkey_start, width=15, 
                                           justify='center', font=('Arial', 10, 'bold'))
        self.start_hotkey_entry.pack(side=tk.RIGHT)
        
        # Клавиша остановки
        stop_frame = ttk.Frame(hotkeys_frame)
        stop_frame.pack(fill=tk.X, pady=5)
        ttk.Label(stop_frame, text="Остановка:").pack(side=tk.LEFT)
        self.stop_hotkey_entry = ttk.Entry(stop_frame, textvariable=self.hotkey_stop, width=15,
                                          justify='center', font=('Arial', 10, 'bold'))
        self.stop_hotkey_entry.pack(side=tk.RIGHT)
        
        # Настройка перехвата клавиш для полей ввода
        self.setup_hotkey_capture()
        
        # Устанавливаем начальное состояние полей
        self.start_hotkey_entry.config(state='readonly')
        self.stop_hotkey_entry.config(state='readonly')
        
        ttk.Button(hotkeys_frame, text="Применить горячие клавиши", 
                  command=lambda: self.setup_hotkeys(True)).pack(pady=10)
        
        # Дополнительные настройки
        extra_settings_frame = ttk.LabelFrame(main_frame, text="Дополнительно", padding="10")
        extra_settings_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Checkbutton(extra_settings_frame, text="Звуковые уведомления", 
                       variable=self.sound_notifications).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(extra_settings_frame, text="Пауза при движении мыши", 
                       variable=self.pause_on_mouse).pack(anchor=tk.W, pady=2)
        
        # Автопауза только если win32gui доступен
        if WIN32_AVAILABLE:
            ttk.Checkbutton(extra_settings_frame, text="Автопауза при переключении окон", 
                           variable=self.pause_on_window).pack(anchor=tk.W, pady=2)
        else:
            ttk.Label(extra_settings_frame, text="Автопауза при переключении окон (недоступно - установите pywin32)", 
                     foreground="gray", font=("Arial", 8)).pack(anchor=tk.W, pady=2)
        
        # Информация об экстренной остановке
        emergency_frame = ttk.Frame(main_frame)
        emergency_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        emergency_label = ttk.Label(emergency_frame, text="🚨 Экстренная остановка: ESC, F12 или Ctrl+Alt+X", 
                                   font=("Arial", 9), foreground="red")
        emergency_label.pack()
        
    def setup_modes_tab(self):
        modes_frame = ttk.Frame(self.notebook)
        self.notebook.add(modes_frame, text="Режимы кликов")
        
        # Выбор режима
        mode_frame = ttk.LabelFrame(modes_frame, text="Режим клика", padding="10")
        mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Radiobutton(mode_frame, text="Обычный клик", variable=self.click_mode, 
                       value="normal", command=self.mode_changed).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Клик по цвету пикселя", variable=self.click_mode, 
                       value="color", command=self.mode_changed).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Поиск и клик по картинке", variable=self.click_mode, 
                       value="image", command=self.mode_changed).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Нажатие клавиш", variable=self.click_mode, 
                       value="keyboard", command=self.mode_changed).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Последовательность точек", variable=self.click_mode, 
                       value="sequence", command=self.mode_changed).pack(anchor=tk.W)
        
        # Настройки цвета
        self.color_frame = ttk.LabelFrame(modes_frame, text="Настройки поиска по цвету", padding="10")
        self.color_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        color_select_frame = ttk.Frame(self.color_frame)
        color_select_frame.pack(fill=tk.X)
        
        ttk.Label(color_select_frame, text="Целевой цвет:").pack(side=tk.LEFT)
        self.color_display = tk.Label(color_select_frame, bg=self.target_color, 
                                     width=4, height=2, relief="solid")
        self.color_display.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Button(color_select_frame, text="Выбрать цвет", 
                  command=self.choose_color).pack(side=tk.LEFT)
        ttk.Button(color_select_frame, text="Пипетка", 
                  command=self.pick_color).pack(side=tk.LEFT, padx=(5, 0))
        
        # Толерантность цвета
        ttk.Label(self.color_frame, text="Толерантность цвета:").pack(anchor=tk.W, pady=(10, 0))
        tolerance_frame = ttk.Frame(self.color_frame)
        tolerance_frame.pack(fill=tk.X, pady=5)
        
        tolerance_scale = ttk.Scale(tolerance_frame, from_=0, to=50, variable=self.color_tolerance, 
                 orient=tk.HORIZONTAL, command=self.update_tolerance_label)
        tolerance_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.tolerance_label = ttk.Label(tolerance_frame, text="10")
        self.tolerance_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Область поиска
        area_frame = ttk.Frame(self.color_frame)
        area_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(area_frame, text="Выбрать область поиска",
                  command=self.select_search_area).pack(side=tk.LEFT)
        ttk.Button(area_frame, text="Показать область",
                  command=self.show_area_overlay).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(area_frame, text="Скрыть область",
                  command=self.hide_area_overlay).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(area_frame, text="Очистить область",
                  command=self.clear_search_area).pack(side=tk.LEFT, padx=(5, 0))
        
        self.area_label = ttk.Label(area_frame, text="Область: весь экран")
        self.area_label.pack(side=tk.RIGHT)
        
        # Настройки поиска картинки
        self.image_frame = ttk.LabelFrame(modes_frame, text="Настройки поиска картинки", padding="10")
        self.image_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Выбор режима картинки
        image_mode_frame = ttk.Frame(self.image_frame)
        image_mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.image_mode = tk.StringVar(value="single")
        ttk.Radiobutton(image_mode_frame, text="Одиночный поиск", variable=self.image_mode, 
                       value="single", command=self.image_mode_changed).pack(side=tk.LEFT)
        ttk.Radiobutton(image_mode_frame, text="Последовательность картинок", variable=self.image_mode, 
                       value="sequence", command=self.image_mode_changed).pack(side=tk.LEFT, padx=(20, 0))
        
        # Одиночный шаблон
        self.single_template_frame = ttk.LabelFrame(self.image_frame, text="Одиночный шаблон", padding="5")
        self.single_template_frame.pack(fill=tk.X, pady=(0, 10))
        
        template_frame = ttk.Frame(self.single_template_frame)
        template_frame.pack(fill=tk.X)
        
        ttk.Button(template_frame, text="Загрузить шаблон", 
                  command=self.load_template_image).pack(side=tk.LEFT)
        ttk.Button(template_frame, text="Сделать скриншот области", 
                  command=self.capture_template).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(template_frame, text="Создать из области поиска", 
                  command=self.create_template_from_search_area_ui).pack(side=tk.LEFT, padx=(5, 0))
        
        self.template_label = ttk.Label(self.single_template_frame, text="Шаблон не выбран", 
                                       font=("Arial", 8), foreground="gray")
        self.template_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Последовательность шаблонов
        self.sequence_template_frame = ttk.LabelFrame(self.image_frame, text="Последовательность шаблонов", padding="5")
        self.sequence_template_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Список шаблонов
        sequence_list_frame = ttk.Frame(self.sequence_template_frame)
        sequence_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.image_sequence_listbox = tk.Listbox(sequence_list_frame, height=4)
        self.image_sequence_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        img_scrollbar = ttk.Scrollbar(sequence_list_frame, orient=tk.VERTICAL, command=self.image_sequence_listbox.yview)
        img_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_sequence_listbox.config(yscrollcommand=img_scrollbar.set)
        
        # Кнопки управления последовательностью шаблонов
        seq_img_buttons = ttk.Frame(self.sequence_template_frame)
        seq_img_buttons.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(seq_img_buttons, text="Добавить файл", 
                  command=self.add_template_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(seq_img_buttons, text="Захватить область", 
                  command=self.add_template_capture).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(seq_img_buttons, text="Удалить", 
                  command=self.remove_image_template).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(seq_img_buttons, text="Очистить", 
                  command=self.clear_image_sequence).pack(side=tk.LEFT, padx=(0, 5))
        
        # Кнопки для перемещения элементов
        move_buttons = ttk.Frame(self.sequence_template_frame)
        move_buttons.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(move_buttons, text="↑ Вверх", 
                  command=self.move_sequence_item_up).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(move_buttons, text="↓ Вниз", 
                  command=self.move_sequence_item_down).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(move_buttons, text="📝 Редактировать текст", 
                  command=self.edit_sequence_text).pack(side=tk.LEFT, padx=(10, 0))
        
        # Добавление клавиш в последовательность
        add_key_frame = ttk.Frame(self.sequence_template_frame)
        add_key_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(add_key_frame, text="Добавить клавишу:").pack(side=tk.LEFT)
        self.sequence_key_entry = ttk.Entry(add_key_frame, textvariable=self.sequence_key_var, width=15,
                                           justify='center', font=('Arial', 10, 'bold'))
        self.sequence_key_entry.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Label(add_key_frame, text="Нажатий:").pack(side=tk.LEFT, padx=(10, 5))
        sequence_key_presses_spinbox = ttk.Spinbox(add_key_frame, from_=1, to=50, width=5, 
                                                  textvariable=self.sequence_key_presses_var)
        sequence_key_presses_spinbox.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(add_key_frame, text="Добавить клавишу", 
                  command=self.add_key_to_sequence).pack(side=tk.LEFT, padx=(5, 0))
        
        # Настройка перехвата для поля ввода клавиш в последовательности
        self.setup_sequence_key_capture()
        
        # Настройка кликов для выбранного шаблона
        clicks_frame = ttk.Frame(self.sequence_template_frame)
        clicks_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(clicks_frame, text="Кликов для выбранного:").pack(side=tk.LEFT)
        self.template_clicks_var = tk.IntVar(value=1)
        clicks_spinbox = ttk.Spinbox(clicks_frame, from_=1, to=100, width=5, 
                                    textvariable=self.template_clicks_var,
                                    command=self.update_template_clicks)
        clicks_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(clicks_frame, text="Применить", 
                  command=self.update_template_clicks).pack(side=tk.LEFT, padx=(5, 0))
        
        # Настройки повторения последовательности
        sequence_settings_frame = ttk.Frame(self.sequence_template_frame)
        sequence_settings_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Количество повторений последовательности
        repeats_frame = ttk.Frame(sequence_settings_frame)
        repeats_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(repeats_frame, text="Повторений последовательности:").pack(side=tk.LEFT)
        repeats_spinbox = ttk.Spinbox(repeats_frame, from_=0, to=1000, width=5, 
                                     textvariable=self.image_sequence_repeats)
        repeats_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(repeats_frame, text="(0 = без остановки)").pack(side=tk.LEFT, padx=(5, 0))
        
        # Точность поиска
        confidence_label_text = "Точность поиска (0.1-1.0):"
        if not OPENCV_AVAILABLE:
            confidence_label_text += " (OpenCV не установлен - точное совпадение)"
        ttk.Label(self.image_frame, text=confidence_label_text).pack(anchor=tk.W, pady=(10, 0))
        
        confidence_frame = ttk.Frame(self.image_frame)
        confidence_frame.pack(fill=tk.X, pady=5)
        
        confidence_scale = ttk.Scale(confidence_frame, from_=0.1, to=1.0, variable=self.image_confidence, 
                   orient=tk.HORIZONTAL, command=self.update_confidence_label)
        confidence_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.confidence_label = ttk.Label(confidence_frame, text="0.8")
        self.confidence_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Предупреждение о OpenCV
        if not OPENCV_AVAILABLE:
            ttk.Label(self.image_frame, text="Для точного поиска установите: pip install opencv-python", 
                     font=("Arial", 8), foreground="orange").pack(anchor=tk.W, pady=(5, 0))
        
        # Область поиска для картинки
        image_area_frame = ttk.Frame(self.image_frame)
        image_area_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(image_area_frame, text="Выбрать область поиска",
                  command=self.select_search_area).pack(side=tk.LEFT)
        ttk.Button(image_area_frame, text="Показать область",
                  command=self.show_area_overlay).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(image_area_frame, text="Скрыть область",
                  command=self.hide_area_overlay).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(image_area_frame, text="Очистить область",
                  command=self.clear_search_area).pack(side=tk.LEFT, padx=(5, 0))
        
        self.image_area_label = ttk.Label(image_area_frame, text="Область: весь экран")
        self.image_area_label.pack(side=tk.RIGHT)
        
        # Настройки нажатия клавиш
        self.keyboard_frame = ttk.LabelFrame(modes_frame, text="Настройки нажатия клавиш", padding="10")
        self.keyboard_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Информация
        info_keyboard = ttk.Label(self.keyboard_frame, text="Настройте последовательность из 1-5 клавиш для циклического нажатия", 
                                 font=("Arial", 9), foreground="blue")
        info_keyboard.pack(pady=(0, 10))
        
        # Список клавиш
        keyboard_list_frame = ttk.Frame(self.keyboard_frame)
        keyboard_list_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.keyboard_sequence_listbox = tk.Listbox(keyboard_list_frame, height=5)
        self.keyboard_sequence_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        keyboard_scrollbar = ttk.Scrollbar(keyboard_list_frame, orient=tk.VERTICAL, command=self.keyboard_sequence_listbox.yview)
        keyboard_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.keyboard_sequence_listbox.config(yscrollcommand=keyboard_scrollbar.set)
        
        # Поле для ввода новой клавиши
        add_key_frame = ttk.Frame(self.keyboard_frame)
        add_key_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(add_key_frame, text="Добавить клавишу:").pack(side=tk.LEFT)
        self.new_key_var = tk.StringVar()
        self.new_key_entry = ttk.Entry(add_key_frame, textvariable=self.new_key_var, width=15,
                                      justify='center', font=('Arial', 10, 'bold'))
        self.new_key_entry.pack(side=tk.LEFT, padx=(10, 5))
        
        # Настройка количества нажатий
        ttk.Label(add_key_frame, text="Нажатий:").pack(side=tk.LEFT, padx=(10, 5))
        self.key_presses_var = tk.IntVar(value=1)
        key_presses_spinbox = ttk.Spinbox(add_key_frame, from_=1, to=50, width=5, 
                                         textvariable=self.key_presses_var)
        key_presses_spinbox.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(add_key_frame, text="Добавить", 
                  command=self.add_keyboard_key).pack(side=tk.LEFT, padx=(5, 0))
        
        # Настройка перехвата для поля ввода клавиш
        self.setup_keyboard_capture()
        
        # Кнопки управления последовательностью клавиш
        keyboard_buttons = ttk.Frame(self.keyboard_frame)
        keyboard_buttons.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(keyboard_buttons, text="Удалить выбранную", 
                  command=self.remove_keyboard_key).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(keyboard_buttons, text="Очистить все", 
                  command=self.clear_keyboard_sequence).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(keyboard_buttons, text="Изменить количество", 
                  command=self.update_key_presses).pack(side=tk.LEFT)
        
        # Ограничение: максимум 5 клавиш
        limit_label = ttk.Label(self.keyboard_frame, text="Максимум 5 клавиш в последовательности", 
                               font=("Arial", 8), foreground="gray")
        limit_label.pack(anchor=tk.W)
        
        # Настройки последовательности
        self.sequence_frame = ttk.LabelFrame(modes_frame, text="Последовательность точек", padding="10")
        self.sequence_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Список точек
        list_frame = ttk.Frame(self.sequence_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.sequence_listbox = tk.Listbox(list_frame, height=6)
        self.sequence_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.sequence_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sequence_listbox.config(yscrollcommand=scrollbar.set)
        
        # Кнопки управления последовательностью
        seq_buttons = ttk.Frame(self.sequence_frame)
        seq_buttons.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(seq_buttons, text="Выбрать точку на экране", 
                  command=self.select_point_on_screen).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(seq_buttons, text="Удалить", 
                  command=self.remove_sequence_point).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(seq_buttons, text="Очистить", 
                  command=self.clear_sequence).pack(side=tk.LEFT)
        
        self.mode_changed()  # Инициализация видимости
        
    def image_mode_changed(self):
        """Переключение между одиночным поиском и последовательностью"""
        mode = self.image_mode.get()
        if mode == "single":
            self.single_template_frame.pack(fill=tk.X, pady=(0, 10))
            self.sequence_template_frame.pack_forget()
        else:  # sequence
            self.single_template_frame.pack_forget()
            self.sequence_template_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        

        

        
    def validate_interval_entry(self, value):
        """Разрешить только цифры, точку, запятую и пустую строку"""
        if value == "":
            return True
        allowed = "0123456789.,"
        for char in value:
            if char not in allowed:
                return False
        return True

    def on_interval_entry_change(self, *args):
        """Обработка изменения интервала через текстовое поле"""
        try:
            try:
                value = self.interval_var.get()
            except tk.TclError:
                # Если поле пустое или содержит недопустимое значение
                return
                
            if isinstance(value, str):
                value = value.replace(",", ".")
                value = value.strip()
                if not value:
                    return
                try:
                    interval = float(value)
                except ValueError:
                    return  # Если не удается преобразовать в число, просто выходим
            else:
                interval = value
            if interval < 0.001:
                interval = 0.001
            elif interval > 2.0:
                interval = 2.0
            try:
                current_value = self.interval_var.get()
                if isinstance(current_value, str):
                    try:
                        current_float = float(current_value.replace(",", "."))
                        if abs(current_float - interval) > 0.0001:
                            self.interval_var.set(f"{interval:.3f}")
                    except ValueError:
                        pass  # Не сбрасываем, просто игнорируем
                else:
                    if abs(current_value - interval) > 0.0001:
                        self.interval_var.set(f"{interval:.3f}")
            except tk.TclError:
                pass  # Если не удается получить текущее значение, игнорируем
        except ValueError:
            pass  # Не сбрасываем, просто игнорируем
    
    def on_interval_key_press(self, event):
        """Обработка нажатий клавиш в поле интервала для замены выделенного текста"""
        # Проверяем, есть ли выделение
        try:
            selection = self.interval_entry.selection_get()
            if selection:
                # Если есть выделение и нажата цифра, точка или запятая, заменяем выделение
                if event.char in "0123456789.,":
                    # Очищаем выделение и вставляем новый символ
                    self.interval_entry.delete("sel.first", "sel.last")
                    self.interval_entry.insert("insert", event.char)
                    return "break"  # Предотвращаем стандартную обработку
        except tk.TclError:
            # Нет выделения, проверяем другие способы определения выделения
            try:
                # Проверяем через tag_ranges
                selection_range = self.interval_entry.tag_ranges("sel")
                if selection_range:
                    # Есть выделение, но не удалось получить текст
                    if event.char in "0123456789.,":
                        self.interval_entry.delete("sel.first", "sel.last")
                        self.interval_entry.insert("insert", event.char)
                        return "break"
            except:
                pass
                
        # Дополнительная проверка: если весь текст выделен (Ctrl+A), заменяем его
        try:
            if event.char in "0123456789.,":
                # Проверяем, выделен ли весь текст
                current_text = self.interval_entry.get()
                if current_text:
                    # Проверяем, совпадает ли выделение с длиной текста
                    try:
                        sel_start = self.interval_entry.index("sel.first")
                        sel_end = self.interval_entry.index("sel.last")
                        if sel_start == "1" and sel_end == f"{len(current_text) + 1}":
                            # Весь текст выделен, заменяем его
                            self.interval_entry.delete(0, tk.END)
                            self.interval_entry.insert(0, event.char)
                            return "break"
                    except tk.TclError:
                        pass
        except:
            pass
            
        # Обработка Backspace и Delete для очистки выделенного текста
        if event.keysym in ["BackSpace", "Delete"]:
            try:
                selection = self.interval_entry.selection_get()
                if selection:
                    # Если есть выделение, удаляем его
                    self.interval_entry.delete("sel.first", "sel.last")
                    return "break"
            except tk.TclError:
                pass
        
    def update_tolerance_label(self, value):
        if hasattr(self, 'tolerance_label'):
            self.tolerance_label.config(text=str(int(float(value))))
            
    def update_confidence_label(self, value):
        if hasattr(self, 'confidence_label'):
            self.confidence_label.config(text=f"{float(value):.2f}")
            
    def select_search_area(self):
        """Выбор области поиска на экране"""
        # Останавливаем кликер если он работает
        was_clicking = self.clicking
        if self.clicking:
            self.stop_clicking()
            # Ждем полной остановки кликера
            time.sleep(1.0)
            
            # Дополнительная проверка
            if self.clicking:
                messagebox.showerror("Ошибка", "Не удалось остановить кликер. Попробуйте еще раз.")
                return
        
        # Принудительно останавливаем кликер еще раз для надежности
        self.clicking = False
        
        # Устанавливаем флаг выбора области
        self.area_selection_active = True
        
        # Дополнительная пауза для гарантии остановки
        time.sleep(0.5)
        
        # Принудительно очищаем все оверлеи перед началом выбора
        self.force_cleanup_overlays()
        
        # Отключаем горячие клавиши во время выбора области
        self.disable_hotkeys()
        
        messagebox.showinfo("Выбор области", 
                           "Зажмите левую кнопку мыши и выделите прямоугольную область.\n" +
                           "Отпустите кнопку для завершения выбора.\n" +
                           "Прямоугольник будет показан поверх всех окон.")
         
         # Запускаем выбор области в отдельном потоке
        threading.Thread(target=lambda: self._select_area_thread(was_clicking), daemon=True).start()
         
    def _select_area_thread(self, was_clicking=False):
        """Поток для выбора области"""
        try:
            start_pos = None
            
            # Ожидаем нажатия левой кнопки мыши через win32api
            while True:
                try:
                    if WIN32_AVAILABLE and win32api.GetAsyncKeyState(0x01) & 0x8000:  # VK_LBUTTON
                        break
                except:
                    # Fallback на pyautogui если win32api недоступен
                    if pyautogui.mouseDown():
                        break
                time.sleep(0.01)
                 
            start_pos = pyautogui.position()
            last_pos = start_pos
            
            # Показываем динамический прямоугольник во время выбора
            while True:
                try:
                    if WIN32_AVAILABLE and win32api.GetAsyncKeyState(0x01) & 0x8000:  # VK_LBUTTON
                        current_pos = pyautogui.position()
                        
                        # Обновляем прямоугольник выбора если позиция изменилась
                        if current_pos != last_pos and current_pos[0] != start_pos[0] and current_pos[1] != start_pos[1]:
                            self.window.after(0, lambda x1=start_pos[0], y1=start_pos[1], x2=current_pos[0], y2=current_pos[1]: self.show_selection_overlay(x1, y1, x2, y2))
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
                            self.window.after(0, lambda x1=start_pos[0], y1=start_pos[1], x2=current_pos[0], y2=current_pos[1]: self.show_selection_overlay(x1, y1, x2, y2))
                            last_pos = current_pos
                        
                        time.sleep(0.01)
                    else:
                        break
            
            end_pos = pyautogui.position()
            
            # Проверяем, что выбранная область валидна
            if start_pos[0] == end_pos[0] or start_pos[1] == end_pos[1]:
                self.window.after(0, lambda: messagebox.showwarning("Предупреждение", "Выбранная область слишком мала. Попробуйте еще раз."))
                return
            
            # Скрываем временный прямоугольник выбора
            self.window.after(0, self.hide_selection_overlay)
            
            # Устанавливаем область поиска
            self.search_area = (
                min(start_pos[0], end_pos[0]),
                min(start_pos[1], end_pos[1]),
                max(start_pos[0], end_pos[0]),
                max(start_pos[1], end_pos[1])
            )
            
            # Показываем фиксированный прямоугольник выбранной области (зеленый)
            self.window.after(0, self.show_area_overlay)
            
            # Обновляем интерфейс и показываем сообщение
            area_text = f"Область: ({self.search_area[0]}, {self.search_area[1]}) - ({self.search_area[2]}, {self.search_area[3]})"
            self.window.after(0, lambda: self.update_area_labels(area_text))
            
            # Показываем сообщение об успехе
            self.window.after(0, lambda: self.show_area_success_dialog(area_text))
            
            # Снимаем флаг выбора области
            self.area_selection_active = False
            
            # Включаем горячие клавиши обратно
            self.window.after(0, self.enable_hotkeys)
            
            # Возобновляем кликер если он работал
            if was_clicking:
                time.sleep(1)  # Небольшая пауза
                self.window.after(0, self.start_clicking)
            
        except Exception as e:
            print(f"Ошибка выбора области: {e}")
            self.window.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка выбора области: {e}"))
        finally:
            # Гарантированно снимаем флаг выбора области
            self.area_selection_active = False
            # Гарантированно включаем горячие клавиши
            self.window.after(0, self.enable_hotkeys)
            self.window.after(0, self.hide_selection_overlay)
        
    def update_area_labels(self, text):
        """Обновление подписей области поиска"""
        if hasattr(self, 'area_label'):
            self.area_label.config(text=text)
        if hasattr(self, 'image_area_label'):
            self.image_area_label.config(text=text)
            
    def reset_search_area(self):
        """Сброс области поиска"""
        self.search_area = None
        self.update_area_labels("Область: весь экран")
        
    def load_template_image(self):
        """Загрузка шаблонной картинки"""
        filetypes = [
            ('Изображения', '*.png *.jpg *.jpeg *.bmp *.gif'),
            ('PNG файлы', '*.png'),
            ('JPEG файлы', '*.jpg *.jpeg'),
            ('Все файлы', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title="Выберите шаблонную картинку",
            filetypes=filetypes
        )
        
        if filename:
            self.template_image = filename
            # Получаем только имя файла для отображения
            name = os.path.basename(filename)
            if len(name) > 30:
                name = name[:27] + "..."
            self.template_label.config(text=f"Шаблон: {name}")
            
    def capture_template(self):
        """Захват области экрана как шаблона"""
        # Останавливаем кликер если он работает
        was_clicking = self.clicking
        if self.clicking:
            self.stop_clicking()
            # Ждем полной остановки кликера
            time.sleep(1.0)
            
            # Дополнительная проверка
            if self.clicking:
                messagebox.showerror("Ошибка", "Не удалось остановить кликер. Попробуйте еще раз.")
                return
        
        # Принудительно останавливаем кликер еще раз для надежности
        self.clicking = False
        
        # Устанавливаем флаг выбора области
        self.area_selection_active = True
        
        # Дополнительная пауза для гарантии остановки
        time.sleep(0.5)
        
        # Принудительно очищаем все оверлеи перед началом выбора
        self.force_cleanup_overlays()
        
        # Отключаем горячие клавиши во время выбора области
        self.disable_hotkeys()
        
        messagebox.showinfo("Захват шаблона", 
                           "Зажмите левую кнопку мыши и выделите область для шаблона.\n" +
                           "Отпустите кнопку для завершения.\n" +
                           "Нажмите ESC для отмены.")
        
        threading.Thread(target=lambda: self._capture_template_thread(was_clicking), daemon=True).start()
         
    def _capture_template_thread(self, was_clicking=False):
        """Поток для захвата шаблона"""
        try:
            # Ожидаем нажатия левой кнопки мыши через win32api
            while True:
                try:
                    if WIN32_AVAILABLE and win32api.GetAsyncKeyState(0x01) & 0x8000:  # VK_LBUTTON
                        break
                except:
                    # Fallback на pyautogui если win32api недоступен
                    if pyautogui.mouseDown():
                        break
                
                # Проверяем ESC для отмены
                if keyboard.is_pressed('esc'):
                    self.window.after(0, lambda: self.enable_hotkeys())
                    if was_clicking:
                        self.window.after(0, lambda: self.start_clicking())
                    return
                
                time.sleep(0.01)
             
            start_pos = pyautogui.position()
            last_pos = start_pos
            
            # Показываем динамический прямоугольник во время выбора
            while True:
                try:
                    if WIN32_AVAILABLE and win32api.GetAsyncKeyState(0x01) & 0x8000:  # VK_LBUTTON
                        current_pos = pyautogui.position()
                        
                        # Обновляем оверлей только если позиция изменилась
                        if current_pos != last_pos:
                            self.window.after(0, lambda: self.show_selection_overlay(
                                start_pos[0], start_pos[1], current_pos[0], current_pos[1]))
                            last_pos = current_pos
                        time.sleep(0.05)  # Ограничиваем частоту обновлений
                    else:
                        break
                except:
                    # Fallback на pyautogui
                    if pyautogui.mouseDown():
                        current_pos = pyautogui.position()
                        if current_pos != last_pos:
                            self.window.after(0, lambda: self.show_selection_overlay(
                                start_pos[0], start_pos[1], current_pos[0], current_pos[1]))
                            last_pos = current_pos
                        time.sleep(0.05)
                    else:
                        break
                 
            end_pos = pyautogui.position()
            
            # Скрываем динамический оверлей
            self.window.after(0, self.hide_selection_overlay)
            
            # Показываем фиксированный оверлей выбранной области
            self.window.after(0, lambda: self.create_overlay_window(
                start_pos[0], start_pos[1], end_pos[0], end_pos[1], "green", 2, 0.5))
             
            # Определяем область
            left = min(start_pos[0], end_pos[0])
            top = min(start_pos[1], end_pos[1])
            width = abs(end_pos[0] - start_pos[0])
            height = abs(end_pos[1] - start_pos[1])
             
            if width > 5 and height > 5:  # Минимальный размер
                # Делаем скриншот области
                screenshot = pyautogui.screenshot(region=(left, top, width, height))
                
                # Сохраняем временный файл
                template_path = "temp_template.png"
                screenshot.save(template_path)
                
                self.template_image = template_path
                self.window.after(0, lambda: self.template_label.config(text=f"Шаблон: захваченная область ({width}x{height})"))
            else:
                self.window.after(0, lambda: messagebox.showerror("Ошибка", "Выбранная область слишком мала"))
                
            # Возобновляем кликер если он работал
            if was_clicking:
                time.sleep(1)
                self.window.after(0, self.start_clicking)
            
            # Восстанавливаем горячие клавиши
            self.window.after(0, lambda: self.enable_hotkeys())
                
        except Exception as e:
            print(f"Ошибка захвата шаблона: {e}")
            # Восстанавливаем горячие клавиши даже при ошибке
            self.window.after(0, lambda: self.enable_hotkeys())
            if was_clicking:
                self.window.after(0, lambda: self.start_clicking())
            
    def add_template_file(self):
        """Добавление шаблона из файла в последовательность"""
        filetypes = [
            ('Изображения', '*.png *.jpg *.jpeg *.bmp *.gif'),
            ('PNG файлы', '*.png'),
            ('JPEG файлы', '*.jpg *.jpeg'),
            ('Все файлы', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title="Выберите шаблонную картинку",
            filetypes=filetypes
        )
        
        if filename:
            name = os.path.basename(filename)
            if len(name) > 25:
                name = name[:22] + "..."
            
            template_entry = {
                "path": filename,
                "name": name,
                "clicks": 1,
                "type": "file"
            }
            
            self.image_sequence.append(template_entry)
            self.update_image_sequence_list()
            
    def add_template_capture(self):
        """Добавление захваченного шаблона в последовательность"""
        # Останавливаем кликер если он работает
        was_clicking = self.clicking
        if self.clicking:
            self.stop_clicking()
            # Ждем полной остановки кликера
            time.sleep(1.0)
            
            # Дополнительная проверка
            if self.clicking:
                messagebox.showerror("Ошибка", "Не удалось остановить кликер. Попробуйте еще раз.")
                return
        
        # Принудительно останавливаем кликер еще раз для надежности
        self.clicking = False
        
        # Устанавливаем флаг выбора области
        self.area_selection_active = True
        
        # Дополнительная пауза для гарантии остановки
        time.sleep(0.5)
        
        # Принудительно очищаем все оверлеи перед началом выбора
        self.force_cleanup_overlays()
        
        messagebox.showinfo("Захват шаблона", 
                           "Зажмите левую кнопку мыши и выделите область для шаблона.\n" +
                           "Отпустите кнопку для завершения.")
        
        threading.Thread(target=lambda: self._capture_sequence_template_thread(was_clicking), daemon=True).start()
         
    def _capture_sequence_template_thread(self, was_clicking=False):
        """Поток для захвата шаблона в последовательность"""
        try:
            start_pos = None
            
            # Ожидаем нажатия левой кнопки мыши через win32api
            while True:
                try:
                    if WIN32_AVAILABLE and win32api.GetAsyncKeyState(0x01) & 0x8000:  # VK_LBUTTON
                        break
                except:
                    # Fallback на pyautogui если win32api недоступен
                    if pyautogui.mouseDown():
                        break
                time.sleep(0.01)
            
            start_pos = pyautogui.position()
            last_pos = start_pos
            
            # Показываем динамический прямоугольник во время выбора
            while True:
                try:
                    if WIN32_AVAILABLE and win32api.GetAsyncKeyState(0x01) & 0x8000:  # VK_LBUTTON
                        current_pos = pyautogui.position()
                        
                        # Обновляем прямоугольник выбора если позиция изменилась
                        if current_pos != last_pos and current_pos[0] != start_pos[0] and current_pos[1] != start_pos[1]:
                            self.window.after(0, lambda x1=start_pos[0], y1=start_pos[1], x2=current_pos[0], y2=current_pos[1]: self.show_selection_overlay(x1, y1, x2, y2))
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
                            self.window.after(0, lambda x1=start_pos[0], y1=start_pos[1], x2=current_pos[0], y2=current_pos[1]: self.show_selection_overlay(x1, y1, x2, y2))
                            last_pos = current_pos
                        
                        time.sleep(0.01)
                    else:
                        break
            
            end_pos = pyautogui.position()
            
            # Проверяем, что выбранная область валидна
            if start_pos[0] == end_pos[0] or start_pos[1] == end_pos[1]:
                self.window.after(0, lambda: messagebox.showwarning("Предупреждение", "Выбранная область слишком мала. Попробуйте еще раз."))
                return
            
            # Скрываем временный прямоугольник выбора
            self.window.after(0, self.hide_selection_overlay)
            
            # Определяем область
            left = min(start_pos[0], end_pos[0])
            top = min(start_pos[1], end_pos[1])
            width = abs(end_pos[0] - start_pos[0])
            height = abs(end_pos[1] - start_pos[1])
            
            if width > 5 and height > 5:  # Минимальный размер
                # Делаем скриншот области
                screenshot = pyautogui.screenshot(region=(left, top, width, height))
                
                # Сохраняем временный файл с уникальным именем
                template_path = f"temp_template_{uuid.uuid4().hex[:8]}.png"
                screenshot.save(template_path)
                
                template_entry = {
                    "path": template_path,
                    "name": f"Захват {width}x{height}",
                    "clicks": 1,
                    "type": "capture",
                    "region": (left, top, width, height)
                }
                
                self.image_sequence.append(template_entry)
                self.window.after(0, self.update_image_sequence_list)
                
                # Показываем фиксированный прямоугольник выбранной области (зеленый)
                self.window.after(0, lambda: self.show_area_overlay())
                
                # Показываем сообщение об успехе
                area_text = f"Шаблон захвачен: ({left}, {top}) - ({left+width}, {top+height})"
                self.window.after(0, lambda: self.show_area_success_dialog(area_text))
            else:
                self.window.after(0, lambda: messagebox.showerror("Ошибка", "Выбранная область слишком мала"))
            
            # Возобновляем кликер если он работал
            if was_clicking:
                time.sleep(1)
                self.window.after(0, self.start_clicking)
            
        except Exception as e:
            print(f"Ошибка захвата шаблона: {e}")
        finally:
            # Гарантированно снимаем флаг выбора области
            self.area_selection_active = False
            # Гарантированно включаем горячие клавиши
            self.window.after(0, self.enable_hotkeys)
            self.window.after(0, self.hide_selection_overlay)
            
    def update_image_sequence_list(self):
        """Обновление списка шаблонов в последовательности"""
        if hasattr(self, 'image_sequence_listbox'):
            self.image_sequence_listbox.delete(0, tk.END)
            for i, item in enumerate(self.image_sequence):
                if item['type'] == 'key':
                    text = f"{i+1}. {item['name']}"
                else:
                    text = f"{i+1}. {item['name']} - {item['clicks']} кликов"
                self.image_sequence_listbox.insert(tk.END, text)
                
    def remove_image_template(self):
        """Удаление выбранного шаблона из последовательности"""
        selection = self.image_sequence_listbox.curselection()
        if selection:
            index = selection[0]
            item = self.image_sequence[index]
            
            # Удаляем временный файл если это захваченный шаблон
            if item['type'] == 'capture' and os.path.exists(item['path']):
                try:
                    os.remove(item['path'])
                except:
                    pass
                    
            del self.image_sequence[index]
            self.update_image_sequence_list()
            
    def clear_image_sequence(self):
        """Очистка всей последовательности шаблонов"""
        # Удаляем все временные файлы
        for item in self.image_sequence:
            if item['type'] == 'capture' and os.path.exists(item['path']):
                try:
                    os.remove(item['path'])
                except:
                    pass
                    
        self.image_sequence.clear()
        self.update_image_sequence_list()
        
    def update_template_clicks(self):
        """Обновление количества кликов для выбранного шаблона"""
        selection = self.image_sequence_listbox.curselection()
        if selection:
            index = selection[0]
            item = self.image_sequence[index]
            if item['type'] != 'key':  # Только для шаблонов изображений
                item['clicks'] = self.template_clicks_var.get()
                self.update_image_sequence_list()
            

        
    def toggle_turbo(self):
        if self.turbo_mode.get():
            self.extreme_mode.set(False)  # Отключаем экстремальный режим
            self.interval_var.set(0.001)
        else:
            pass  # Ничего не делаем при отключении турбо режима
            
    def toggle_extreme(self):
        if self.extreme_mode.get():
            self.turbo_mode.set(False)
            self.interval_var.set(0.00001)
            messagebox.showwarning("Экстремальный режим", 
                                 "⚡ ВНИМАНИЕ! Экстремальный режим!\n\n" +
                                 "• Скорость: до 10,000+ кликов/сек\n" +
                                 "• ОЧЕНЬ ВЫСОКИЙ РИСК нестабильности\n" +
                                 "• Используйте только в крайних случаях!\n" +
                                 "• ESC, F12 или Ctrl+Alt+X для экстренной остановки")
        else:
            pass  # Ничего не делаем при отключении экстремального режима
            
    def mode_changed(self):
        # Скрываем оверлей области при смене режима
        self.hide_area_overlay()
        
        mode = self.click_mode.get()
        # Скрываем все фреймы настроек
        self.color_frame.pack_forget()
        self.image_frame.pack_forget()
        self.keyboard_frame.pack_forget()
        self.sequence_frame.pack_forget()
        # Показываем нужный фрейм
        if mode == "color":
            self.color_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            # Показываем оверлей, если область выбрана
            if self.search_area:
                self.show_area_overlay()
        elif mode == "image":
            self.image_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            self.image_mode_changed()  # Обновляем видимость подрежимов
            if self.search_area:
                self.show_area_overlay()
        elif mode == "keyboard":
            self.keyboard_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        elif mode == "sequence":
            self.sequence_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
            
    def choose_color(self):
        color = colorchooser.askcolor(color=self.target_color)
        if color[1]:
            self.target_color = color[1]
            self.color_display.config(bg=self.target_color)
            
    def pick_color(self):
        messagebox.showinfo("Пипетка", "Наведите курсор на нужный цвет и нажмите ПРОБЕЛ (Space).\nНажмите Esc для отмены.")
        threading.Thread(target=self._color_picker_thread, daemon=True).start()

    def _color_picker_thread(self):
        """Ожидает нажатие Space глобально и захватывает цвет курсора"""
        try:
            # ждём Space или Esc
            while True:
                if keyboard.is_pressed('space'):
                    break
                if keyboard.is_pressed('esc'):
                    return  # отмена
                time.sleep(0.05)
            x, y = pyautogui.position()
            pixel = pyautogui.screenshot().getpixel((x, y))
            hex_color = f"#{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}"
            self.target_color = hex_color
            self.window.after(0, lambda: self.color_display.config(bg=hex_color))
        finally:
            # убрать залипание клавиши
            keyboard.clear_all_hotkeys()
        
    def select_point_on_screen(self):
        """Выбор точки на экране для последовательности"""
        # Останавливаем кликер если он работает
        was_clicking = self.clicking
        if self.clicking:
            self.stop_clicking()
            time.sleep(0.5)
        
        # Отключаем горячие клавиши во время выбора точки
        self.disable_hotkeys()
        
        messagebox.showinfo("Выбор точки", 
                           "Наведите курсор на нужную точку и нажмите SHIFT + ЛЕВУЮ КНОПКУ МЫШИ.\n" +
                           "Нажмите ESC для отмены.")
        
        # Запускаем выбор точки в отдельном потоке
        threading.Thread(target=lambda: self._select_point_thread(was_clicking), daemon=True).start()
    
    def _select_point_thread(self, was_clicking=False):
        """Поток для выбора точки на экране"""
        try:
            # Ожидаем SHIFT + клик левой кнопкой мыши
            while True:
                try:
                    if WIN32_AVAILABLE:
                        # Проверяем SHIFT + левая кнопка мыши
                        shift_pressed = win32api.GetAsyncKeyState(0x10) & 0x8000  # VK_SHIFT
                        left_button = win32api.GetAsyncKeyState(0x01) & 0x8001   # VK_LBUTTON
                        if shift_pressed and left_button:
                            break
                    else:
                        # Fallback на keyboard + pyautogui
                        if keyboard.is_pressed('shift') and pyautogui.mouseDown():
                            break
                except:
                    # Fallback на pyautogui если win32api недоступен
                    if keyboard.is_pressed('shift') and pyautogui.mouseDown():
                        break
                
                # Проверяем ESC для отмены
                if keyboard.is_pressed('esc'):
                    self.window.after(0, lambda: self.enable_hotkeys())
                    if was_clicking:
                        self.window.after(0, lambda: self.start_clicking())
                    return
                
                time.sleep(0.01)
            
            # Получаем позицию курсора
            x, y = pyautogui.position()
            clicks = 10  # По умолчанию 10 кликов
            
            # Добавляем точку в последовательность
            point_text = f"({x}, {y}) - {clicks} кликов"
            self.sequence_points.append({"x": x, "y": y, "clicks": clicks})
            self.window.after(0, lambda: self.sequence_listbox.insert(tk.END, point_text))
            
            # Показываем уведомление
            self.window.after(0, lambda: messagebox.showinfo("Точка добавлена", 
                                                           f"Добавлена точка ({x}, {y}) с {clicks} кликами"))
            
        except Exception as e:
            print(f"Ошибка выбора точки: {e}")
        finally:
            # Восстанавливаем горячие клавиши
            self.window.after(0, lambda: self.enable_hotkeys())
            if was_clicking:
                self.window.after(0, lambda: self.start_clicking())
        
    def remove_sequence_point(self):
        selection = self.sequence_listbox.curselection()
        if selection:
            index = selection[0]
            self.sequence_listbox.delete(index)
            del self.sequence_points[index]
            
    def clear_sequence(self):
        self.sequence_listbox.delete(0, tk.END)
        self.sequence_points.clear()
        
    def start_clicking(self):
        """Запуск кликера"""
        if not self.clicking:
            self.clicking = True
            self.click_count = 0
            # Сбрасываем счетчик повторений последовательности
            self.image_sequence_repeat_count = 0
            self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
            self.click_thread.start()
            
            # Обновляем интерфейс
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            
            # Показываем статус
            mode = self.click_mode.get()
            status_text = "Кликинг..."
            
            if mode == "normal":
                status_text = "Обычный клик"
            elif mode == "color":
                status_text = "Поиск по цвету"
            elif mode == "image":
                image_mode = getattr(self, 'image_mode', tk.StringVar(value="single")).get()
                if image_mode == "single":
                    status_text = "Поиск по картинке"
                else:
                    status_text = "Последовательность шаблонов"
            elif mode == "keyboard":
                status_text = "Нажатие клавиш"
            elif mode == "sequence":
                status_text = "Последовательность точек"
                
            if self.extreme_mode.get():
                status_text += " (ЭКСТРЕМ)"

                
            self.status_label.config(text=status_text)
            
            # Звуковое уведомление
            if self.sound_notifications.get():
                try:
                    winsound.Beep(800, 100)
                except:
                    pass
    
    def stop_clicking(self):
        self.clicking = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Остановлен", foreground="red")
        
        # Сбрасываем счетчики
        self.current_sequence_index = 0
        self.current_image_index = 0
        self.current_keyboard_index = 0
        self.image_sequence_clicks = 0
        self.keyboard_sequence_presses = 0
        
        # Ждем полной остановки кликера
        max_wait = 2.0  # Максимум 2 секунды ожидания
        wait_time = 0.0
        while hasattr(self, 'click_thread') and self.click_thread and self.click_thread.is_alive():
            time.sleep(0.1)
            wait_time += 0.1
            if wait_time >= max_wait:
                break
        
        if self.sound_notifications.get():
            try:
                winsound.Beep(500, 200)
            except:
                pass
                
    def reset_counter(self):
        self.click_count = 0
        self.count_label.config(text="Кликов: 0")
        
    def click_loop(self):
        sequence_clicks = 0
        
        while self.clicking:
            try:
                # Проверяем, не идет ли выбор области
                if self.area_selection_active:
                    time.sleep(0.1)
                    continue
                
                # Экстренная остановка по ESC во всех режимах
                try:
                    if keyboard.is_pressed('esc'):
                        self.window.after(0, self.stop_clicking)
                        break
                except:
                    pass
                
                # Дополнительная экстренная остановка по F12 и Ctrl+Alt+X
                try:
                    if keyboard.is_pressed('f12') or (keyboard.is_pressed('ctrl') and keyboard.is_pressed('alt') and keyboard.is_pressed('x')):
                        self.emergency_stop()
                        break
                except:
                    pass
                
                # Небольшая пауза для более быстрой реакции на остановку
                time.sleep(0.001)
                
                # Дополнительная проверка выбора области после паузы
                if self.area_selection_active:
                    continue
                
                # Проверка паузы при движении мыши
                if self.pause_on_mouse.get():
                    current_pos = pyautogui.position()
                    if current_pos != self.last_mouse_pos:
                        self.last_mouse_pos = current_pos
                        time.sleep(0.5)
                        continue
                        
                # Проверка паузы при переключении окон
                if self.pause_on_window.get() and WIN32_AVAILABLE:
                    try:
                        current_window = win32gui.GetForegroundWindow()
                        if self.active_window and current_window != self.active_window:
                            time.sleep(0.5)
                            continue
                    except:
                        pass
                
                # Финальная проверка выбора области перед выполнением клика
                if self.area_selection_active:
                    continue
                
                # Выполнение клика в зависимости от режима
                mode = self.click_mode.get()
                
                if mode == "color":
                    if self.find_and_click_color():
                        self.window.after(0, self.update_counter)
                elif mode == "image":
                    if self.find_and_click_image():
                        self.window.after(0, self.update_counter)
                    else:
                        # Если поиск по картинке не удался, добавляем дополнительную паузу
                        time.sleep(0.05)
                elif mode == "keyboard":
                    if self.press_keyboard_sequence():
                        self.window.after(0, self.update_counter)
                elif mode == "sequence":
                    if self.sequence_points:
                        point = self.sequence_points[self.current_sequence_index]
                        pyautogui.click(point["x"], point["y"], button=self.click_type.get())
                        sequence_clicks += 1
                        
                        if sequence_clicks >= point["clicks"]:
                            sequence_clicks = 0
                            self.current_sequence_index = (self.current_sequence_index + 1) % len(self.sequence_points)
                            
                        self.window.after(0, self.update_counter)
                else:  # normal mode
                    if self.extreme_mode.get() and WIN32_AVAILABLE:
                        # Экстремально быстрый клик через win32api
                        self.fast_click()
                        # В экстремальном режиме обновляем счетчик реже для производительности
                        update_frequency = 50
                        if self.click_count % update_frequency == 0:
                            self.window.after(0, self.update_counter)
                        else:
                            self.click_count += 1
                    else:
                        # Обычный клик через pyautogui
                        pyautogui.click(button=self.click_type.get())
                        self.window.after(0, self.update_counter)
                
                # Пауза
                if self.extreme_mode.get():
                    # В экстремальном режиме вообще нет задержки
                    pass  # Максимальная скорость без задержек
                elif self.turbo_mode.get():
                    time.sleep(0.001)
                else:
                    time.sleep(self.interval_var.get())
                    
                # Пауза при пользовательской активности
                if time.time() - self.last_user_activity < self.user_pause_timeout:
                    time.sleep(0.05)
                    continue
            except Exception as e:
                print(f"Ошибка при клике: {e}")
                break
                
    def find_and_click_color(self):
        """Поиск и клик по цвету (оптимизированный для одиночного поиска)"""
        try:
            # Если пользователь недавно был активен — сбрасываем позицию
            if self.user_activity_detected:
                self.last_found_color_position = None
                self.user_activity_detected = False
            
            # Проверяем, изменились ли настройки цвета
            current_color = self.target_color
            current_tolerance = self.color_tolerance.get()
            
            if (self.last_target_color != current_color or 
                self.last_color_tolerance != current_tolerance):
                # Настройки изменились, нужно искать заново
                self.last_found_color_position = None
                self.last_target_color = current_color
                self.last_color_tolerance = current_tolerance
            
            # Если позиция уже найдена — кликаем по ней
            if self.last_found_color_position:
                # Периодически проверяем, что цвет еще там
                self.clicks_since_last_search += 1
                if self.clicks_since_last_search >= self.recheck_interval:
                    # Время для перепроверки
                    found, pos = self._search_color_position()
                    if found:
                        self.last_found_color_position = pos
                        self.clicks_since_last_search = 0
                    else:
                        # Цвет исчез, сбрасываем позицию
                        self.last_found_color_position = None
                        self.clicks_since_last_search = 0
                        return False
                
                pyautogui.click(self.last_found_color_position, button=self.click_type.get())
                return True
            
            # Иначе ищем цвет
            found, pos = self._search_color_position()
            if found:
                self.last_found_color_position = pos
                self.clicks_since_last_search = 0
                pyautogui.click(pos, button=self.click_type.get())
                return True
            else:
                self.last_found_color_position = None
                return False
                
        except Exception as e:
            print(f"Ошибка при поиске цвета: {e}")
            return False
    
    def _search_color_position(self):
        """Ищет цвет и возвращает (True, позиция) или (False, None)"""
        try:
            # Определяем область поиска
            if self.search_area:
                x1, y1, x2, y2 = self.search_area
                screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
                offset_x, offset_y = x1, y1
            else:
                screenshot = pyautogui.screenshot()
                offset_x, offset_y = 0, 0
            
            target_rgb = tuple(int(self.target_color[i:i+2], 16) for i in (1, 3, 5))
            
            # Поиск пикселя (оптимизированный алгоритм)
            width, height = screenshot.size
            step = max(1, min(width, height) // 100)  # Адаптивный шаг поиска
            
            for x in range(0, width, step):
                for y in range(0, height, step):
                    pixel = screenshot.getpixel((x, y))
                    if self.color_matches(pixel, target_rgb):
                        click_x = x + offset_x
                        click_y = y + offset_y
                        return True, (click_x, click_y)
            return False, None
        except Exception as e:
            print(f"Ошибка при поиске цвета: {e}")
            return False, None
            
    def fast_click(self):
        """Экстремально быстрый клик через win32api"""
        if not WIN32_AVAILABLE:
            return
            
        try:
            # Получаем текущую позицию курсора (кэшируем для скорости)
            if not hasattr(self, '_last_cursor_pos') or time.time() - getattr(self, '_last_cursor_time', 0) > 0.01:
                self._last_cursor_pos = win32gui.GetCursorPos()
                self._last_cursor_time = time.time()
            
            x, y = self._last_cursor_pos
            
            # Определяем кнопку мыши (кэшируем для скорости)
            if not hasattr(self, '_cached_button_type') or self._cached_button_type != self.click_type.get():
                self._cached_button_type = self.click_type.get()
            
            button_type = self._cached_button_type
            
            # Оптимизированные флаги для максимальной скорости
            if button_type == "left":
                # Нажатие левой кнопки мыши - объединяем в один вызов
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN | win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
            elif button_type == "right":
                # Нажатие правой кнопки мыши - объединяем в один вызов
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN | win32con.MOUSEEVENTF_RIGHTUP, x, y, 0, 0)
            elif button_type == "middle":
                # Нажатие средней кнопки мыши - объединяем в один вызов
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN | win32con.MOUSEEVENTF_MIDDLEUP, x, y, 0, 0)
                
        except Exception as e:
            print(f"Ошибка быстрого клика: {e}")
            # Fallback на обычный клик
            pyautogui.click(button=self.click_type.get())
            
    def press_keyboard_sequence(self):
        """Нажатие клавиш из последовательности"""
        if not self.keyboard_sequence:
            return False
            
        if not hasattr(self, 'keyboard_sequence_presses'):
            self.keyboard_sequence_presses = 0
            
        current_key_entry = self.keyboard_sequence[self.current_keyboard_index]
        
        try:
            # Нажимаем клавишу
            key = current_key_entry['key']
            
            # Преобразуем некоторые клавиши для pyautogui
            key_mapping = {
                'enter': 'enter',
                'esc': 'escape', 
                'space': 'space',
                'tab': 'tab',
                'shift': 'shift',
                'ctrl': 'ctrl',
                'alt': 'alt',
                'backspace': 'backspace',
                'delete': 'delete',
                'home': 'home',
                'end': 'end',
                'page_up': 'pageup',
                'page_down': 'pagedown',
                'up': 'up',
                'down': 'down',
                'left': 'left',
                'right': 'right',
                'insert': 'insert',
                'caps_lock': 'capslock'
            }
            
            # Функциональные клавиши
            if key.startswith('f') and len(key) >= 2:
                try:
                    num = int(key[1:])
                    if 1 <= num <= 12:
                        key = f'f{num}'
                except:
                    pass
                    
            # Цифровая клавиатура
            if key.startswith('num_'):
                suffix = key[4:]
                if suffix.isdigit():
                    key = f'num{suffix}'
                elif suffix == 'enter':
                    key = 'numpadenter'
                elif suffix == 'plus':
                    key = 'add'
                elif suffix == 'minus':
                    key = 'subtract'
            
            # Применяем маппинг
            key = key_mapping.get(key, key)
            
            pyautogui.press(key)
            self.keyboard_sequence_presses += 1
            
            # Проверяем, достигли ли нужного количества нажатий
            if self.keyboard_sequence_presses >= current_key_entry['presses']:
                self.keyboard_sequence_presses = 0
                self.current_keyboard_index = (self.current_keyboard_index + 1) % len(self.keyboard_sequence)
                
            return True
            
        except Exception as e:
            print(f"Ошибка нажатия клавиши {current_key_entry['key']}: {e}")
            return False
        except:
            return False
            
    def find_and_click_image(self):
        """Поиск и клик по картинке (оптимизация для одиночного поиска)"""
        image_mode = getattr(self, 'image_mode', tk.StringVar(value="single")).get()
        
        if image_mode == "single":
            # Одиночный поиск
            if (not self.template_image or not os.path.exists(self.template_image)):
                # Если есть область поиска — создаём шаблон автоматически
                if self.search_area:
                    new_template = self.create_template_from_search_area()
                    if new_template:
                        self.template_image = new_template
                        self.last_image_template = new_template
                        # Обновляем метку в интерфейсе, если есть
                        if hasattr(self, 'template_label'):
                            name = os.path.basename(new_template)
                            if len(name) > 30:
                                name = name[:27] + "..."
                            self.template_label.config(text=f"Шаблон: {name}")
                        print(f"Автоматически создан шаблон из области поиска: {new_template}")
                    else:
                        print("Не удалось создать шаблон из области поиска")
                        time.sleep(0.1)
                        return False
                else:
                    # Пытаемся найти временный шаблон автоматически
                    self.template_image = self.find_temp_template()
                    if not self.template_image:
                        print("Шаблон не выбран или файл не найден")
                        time.sleep(0.1)
                        return False
            # Если пользователь недавно был активен — сбрасываем позицию
            if self.user_activity_detected:
                self.last_found_image_position = None
                self.user_activity_detected = False
            # Если позиция уже найдена и шаблон не менялся — кликаем по ней
            if self.last_found_image_position and self.last_image_template == self.template_image:
                # Периодически проверяем, что картинка еще там
                self.clicks_since_last_search += 1
                if self.clicks_since_last_search >= self.recheck_interval:
                    # Время для перепроверки
                    found, pos = self._search_image_position(self.template_image)
                    if found:
                        self.last_found_image_position = pos
                        self.clicks_since_last_search = 0
                    else:
                        # Картинка исчезла, сбрасываем позицию
                        self.last_found_image_position = None
                        self.clicks_since_last_search = 0
                        return False
                pyautogui.click(self.last_found_image_position, button=self.click_type.get())
                return True
            # Иначе ищем картинку
            found, pos = self._search_image_position(self.template_image)
            if found:
                self.last_found_image_position = pos
                self.last_image_template = self.template_image
                self.clicks_since_last_search = 0
                pyautogui.click(pos, button=self.click_type.get())
                return True
            else:
                self.last_found_image_position = None
                return False
        else:
            # ... существующий код для последовательности ...
            # (оставляем без изменений)
            # ...
            # Последовательность шаблонов
            if not self.image_sequence:
                print("Последовательность шаблонов пуста")
                # Добавляем небольшую паузу, чтобы не загружать CPU
                time.sleep(0.1)
                return False
                
            if not hasattr(self, 'image_sequence_clicks'):
                self.image_sequence_clicks = 0
                
            current_item = self.image_sequence[self.current_image_index]
            
            # Обрабатываем клавиши
            if current_item['type'] == 'key':
                # Нажимаем клавишу
                key = current_item['key']
                presses = current_item['presses']
                
                for _ in range(presses):
                    try:
                        keyboard.press_and_release(key)
                        time.sleep(0.1)  # Небольшая пауза между нажатиями
                    except Exception as e:
                        print(f"Ошибка нажатия клавиши {key}: {e}")
                
                # Переходим к следующему элементу
                self.current_image_index = (self.current_image_index + 1) % len(self.image_sequence)
                
                # Если прошли всю последовательность
                if self.current_image_index == 0:
                    self.image_sequence_repeat_count += 1
                    
                    # Проверяем, нужно ли остановиться
                    max_repeats = self.image_sequence_repeats.get()
                    if max_repeats > 0 and self.image_sequence_repeat_count >= max_repeats:
                        # Останавливаем кликер после завершения последовательности
                        self.window.after(0, self.stop_clicking)
                        return False
                
                return True
            
            # Обрабатываем шаблоны изображений
            else:
                # Проверяем существование файла шаблона
                if not os.path.exists(current_item['path']):
                    print(f"Файл шаблона не найден: {current_item['path']}")
                    # Переходим к следующему элементу
                    self.current_image_index = (self.current_image_index + 1) % len(self.image_sequence)
                    return False
                
                # Пытаемся найти и кликнуть по текущему шаблону
                region = current_item.get('region') if 'region' in current_item else None
                if self._search_and_click_template(current_item['path'], region_override=region):
                    self.image_sequence_clicks += 1
                    
                    # Проверяем, достигли ли нужного количества кликов
                    if self.image_sequence_clicks >= current_item['clicks']:
                        self.image_sequence_clicks = 0
                        self.current_image_index = (self.current_image_index + 1) % len(self.image_sequence)
                        
                        # Если прошли всю последовательность
                        if self.current_image_index == 0:
                            self.image_sequence_repeat_count += 1
                            
                            # Проверяем, нужно ли остановиться
                            max_repeats = self.image_sequence_repeats.get()
                            if max_repeats > 0 and self.image_sequence_repeat_count >= max_repeats:
                                # Останавливаем кликер после завершения последовательности
                                self.window.after(0, self.stop_clicking)
                                return False
                            
                    return True
                    
                return False
                
    def find_temp_template(self):
        """Автоматический поиск временного шаблона"""
        import glob
        
        # Ищем временные файлы шаблонов
        temp_patterns = [
            "temp_template*.png",
            "temp_template*.jpg",
            "temp_template*.jpeg"
        ]
        
        for pattern in temp_patterns:
            files = glob.glob(pattern)
            if files:
                # Возвращаем самый новый файл
                latest_file = max(files, key=os.path.getctime)
                print(f"Автоматически найден шаблон: {latest_file}")
                return latest_file
                
        return None
            
    def _search_and_click_template(self, template_path, region_override=None):
        """Поиск и клик по конкретному шаблону (region_override - область поиска)"""
        if not template_path or not os.path.exists(template_path):
            print(f"Шаблон не найден: {template_path}")
            return False
        try:
            # Определяем область поиска
            region = None
            if region_override:
                region = region_override
            elif self.search_area:
                x1, y1, x2, y2 = self.search_area
                region = (x1, y1, x2 - x1, y2 - y1)
            
            # Проверяем размеры шаблона и области поиска
            try:
                from PIL import Image
                template_img = Image.open(template_path)
                template_width, template_height = template_img.size
                print(f"Размер шаблона: {template_width}x{template_height}")
                
                if region:
                    region_width, region_height = region[2], region[3]
                    print(f"Размер области поиска: {region_width}x{region_height}")
                    
                    # Проверяем, не превышает ли шаблон размеры области поиска
                    if template_width > region_width or template_height > region_height:
                        print(f"ОШИБКА: Шаблон ({template_width}x{template_height}) больше области поиска ({region_width}x{region_height})")
                        print("Создаем новый шаблон из области поиска...")
                        
                        # Создаем новый шаблон из области поиска
                        new_template = self.create_template_from_search_area()
                        if new_template:
                            self.template_image = new_template
                            print(f"Используем новый шаблон: {new_template}")
                            # Рекурсивно вызываем поиск с новым шаблоном
                            return self._search_and_click_template(new_template, region_override)
                        else:
                            print("Не удалось создать новый шаблон, используем поиск по всему экрану")
                            region = None  # Используем весь экран
                    else:
                        print("Размеры шаблона подходят для области поиска")
                else:
                    print("Поиск по всему экрану")
                    
            except Exception as e:
                print(f"Ошибка при проверке размеров: {e}")
            
            # Отладочная информация
            print(f"Поиск шаблона: {template_path}")
            if region:
                print(f"Область поиска: {region}")
            else:
                print("Область поиска: весь экран")
            
            # Добавляем таймаут для поиска картинки
            start_time = time.time()
            timeout = 2.0  # 2 секунды таймаут
            
            # Ищем картинку на экране
            if OPENCV_AVAILABLE:
                location = pyautogui.locateOnScreen(
                    template_path, 
                    confidence=self.image_confidence.get(),
                    region=region
                )
            else:
                # Fallback без confidence (точное совпадение)
                location = pyautogui.locateOnScreen(
                    template_path, 
                    region=region
                )
            
            # Проверяем таймаут
            if time.time() - start_time > timeout:
                print(f"Таймаут поиска картинки: {template_path}")
                return False
            
            if location:
                # Кликаем по центру найденной картинки
                center = pyautogui.center(location)
                print(f"Найдена картинка в позиции: {center}")
                pyautogui.click(center, button=self.click_type.get())
                return True
            else:
                print("Картинка не найдена на экране")
            
        except pyautogui.ImageNotFoundException:
            # Картинка не найдена - это нормально, не выводим ошибку
            print("Картинка не найдена (ImageNotFoundException)")
            pass
        except Exception as e:
            print(f"Ошибка поиска картинки: {e}")
        
        return False
            
    def color_matches(self, pixel, target):
        tolerance = self.color_tolerance.get()
        return all(abs(pixel[i] - target[i]) <= tolerance for i in range(3))
        
    def update_counter(self):
        self.click_count += 1
        self.count_label.config(text=f"Кликов: {self.click_count}")
        
    def setup_hotkey_capture(self):
        """Настройка перехвата клавиш для полей ввода горячих клавиш"""
        # Привязываем события к полям ввода
        self.start_hotkey_entry.bind('<Button-1>', lambda e: self.on_hotkey_click(e, 'start'))
        self.start_hotkey_entry.bind('<FocusIn>', lambda e: self.on_hotkey_focus_in(e, 'start'))
        self.start_hotkey_entry.bind('<FocusOut>', lambda e: self.on_hotkey_focus_out(e, 'start'))
        self.start_hotkey_entry.bind('<KeyPress>', lambda e: self.on_hotkey_press(e, 'start'))
        
        self.stop_hotkey_entry.bind('<Button-1>', lambda e: self.on_hotkey_click(e, 'stop'))
        self.stop_hotkey_entry.bind('<FocusIn>', lambda e: self.on_hotkey_focus_in(e, 'stop'))
        self.stop_hotkey_entry.bind('<FocusOut>', lambda e: self.on_hotkey_focus_out(e, 'stop'))
        self.stop_hotkey_entry.bind('<KeyPress>', lambda e: self.on_hotkey_press(e, 'stop'))
        
    def setup_keyboard_capture(self):
        """Настройка перехвата клавиш для поля ввода клавиш последовательности"""
        if hasattr(self, 'new_key_entry'):
            # Привязываем события к полю ввода клавиш
            self.new_key_entry.bind('<Button-1>', self.on_keyboard_click)
            self.new_key_entry.bind('<FocusIn>', self.on_keyboard_focus_in)
            self.new_key_entry.bind('<FocusOut>', self.on_keyboard_focus_out)
            self.new_key_entry.bind('<KeyPress>', self.on_keyboard_press)
            
    def on_hotkey_click(self, event, field_type):
        """Когда пользователь кликает на поле"""
        entry = event.widget
        entry.config(state='normal')
        entry.focus_set()
        return 'break'
        
    def on_hotkey_focus_in(self, event, field_type):
        """Когда поле получает фокус"""
        entry = event.widget
        entry.config(background='lightblue', state='normal')
        
        # Показываем placeholder только если поле пустое или содержит значение по умолчанию
        if field_type == 'start':
            current_value = self.hotkey_start.get()
            if current_value == '' or current_value in ['f6', 'Нажмите клавишу...']:
                self.hotkey_start.set('Нажмите клавишу...')
        else:
            current_value = self.hotkey_stop.get()
            if current_value == '' or current_value in ['f7', 'Нажмите клавишу...']:
                self.hotkey_stop.set('Нажмите клавишу...')
        
        entry.select_range(0, tk.END)
            
    def on_hotkey_focus_out(self, event, field_type):
        """Когда поле теряет фокус"""
        entry = event.widget
        entry.config(background='white', state='readonly')
        
        # Если ничего не было установлено, возвращаем значение по умолчанию
        if field_type == 'start' and self.hotkey_start.get() == 'Нажмите клавишу...':
            self.hotkey_start.set('f6')
        elif field_type == 'stop' and self.hotkey_stop.get() == 'Нажмите клавишу...':
            self.hotkey_stop.set('f7')
            
    def on_hotkey_press(self, event, field_type):
        """Обработка нажатия клавиши в поле ввода"""
        key_name = self.get_key_name(event)
        
        if key_name:
            if field_type == 'start':
                self.hotkey_start.set(key_name)
            else:
                self.hotkey_stop.set(key_name)
                
            # Убираем фокус с поля
            self.window.focus()
            
        return 'break'  # Предотвращаем обычную обработку события
        
    def get_key_name(self, event):
        """Получение правильного названия клавиши из события"""
        key = event.keysym.lower()
        
        # Функциональные клавиши (уже в правильном формате)
        if key.startswith('f') and len(key) >= 2:
            try:
                num = int(key[1:])
                if 1 <= num <= 12:
                    return key  # f1, f2, ..., f12
            except ValueError:
                pass
                
        # Буквы и цифры
        if len(key) == 1 and (key.isalpha() or key.isdigit()):
            return key
            
        # Специальные клавиши - приводим к стандартным названиям
        special_keys_map = {
            'space': 'space',
            'return': 'enter',
            'escape': 'esc', 
            'tab': 'tab',
            'shift_l': 'shift',
            'shift_r': 'shift',
            'control_l': 'ctrl',
            'control_r': 'ctrl',
            'alt_l': 'alt',
            'alt_r': 'alt',
            'insert': 'insert',
            'delete': 'delete',
            'home': 'home',
            'end': 'end',
            'page_up': 'page_up',
            'page_down': 'page_down',
            'up': 'up',
            'down': 'down',
            'left': 'left',
            'right': 'right',
            'backspace': 'backspace',
            'caps_lock': 'caps_lock'
        }
        
        if key in special_keys_map:
            return special_keys_map[key]
            
        # Цифровая клавиатура
        if key.startswith('kp_'):
            kp_key = key[3:]
            if kp_key.isdigit():
                return f'num_{kp_key}'
            elif kp_key == 'enter':
                return 'num_enter'
            elif kp_key == 'add':
                return 'num_plus'
            elif kp_key == 'subtract':
                return 'num_minus'
                
        # Если ничего не подошло, возвращаем исходную клавишу
        return key if len(key) <= 15 else None
        
    def setup_hotkeys(self, show_message=False):
        """Настройка горячих клавиш без дублирования"""
        try:
            keyboard.unhook_all()
            # Нормализация названий ключей
            start_key = self.normalize_key(self.hotkey_start.get())
            stop_key = self.normalize_key(self.hotkey_stop.get())
            # Проверка корректности
            if not self.is_valid_key(start_key) or not self.is_valid_key(stop_key):
                if show_message:
                    messagebox.showerror("Ошибка", "Некорректные горячие клавиши.")
                return
            # Назначаем
            keyboard.add_hotkey(start_key, self.hotkey_start_action)
            keyboard.add_hotkey(stop_key, self.hotkey_stop_action)
            if show_message:
                messagebox.showinfo("Успех", f"Горячие клавиши установлены:\nЗапуск: {start_key.upper()}\nОстановка: {stop_key.upper()}")
        except Exception as e:
            if show_message:
                messagebox.showerror("Ошибка", f"Не удалось установить горячие клавиши: {e}")
            
    def normalize_key(self, key):
        """Нормализация названия клавиши"""
        key = key.lower().strip()
        
        # Словарь соответствий
        key_mapping = {
            'space': 'space',
            'enter': 'enter', 
            'return': 'enter',
            'esc': 'esc',
            'escape': 'esc',
            'tab': 'tab',
            'shift': 'shift',
            'ctrl': 'ctrl',
            'alt': 'alt'
        }
        
        return key_mapping.get(key, key)
        
    def is_valid_key(self, key):
        """Проверка корректности клавиши"""
        # Буквы и цифры
        if len(key) == 1 and (key.isalpha() or key.isdigit()):
            return True
            
        # F-клавиши
        if key.startswith('f') and len(key) >= 2:
            try:
                num = int(key[1:])
                return 1 <= num <= 12
            except ValueError:
                return False
                
        # Специальные клавиши
        special_keys = [
            'space', 'enter', 'esc', 'tab', 'shift', 'ctrl', 'alt',
            'insert', 'delete', 'home', 'end', 'page_up', 'page_down',
            'up', 'down', 'left', 'right', 'backspace', 'caps_lock'
        ]
        
        # Цифровая клавиатура
        if key.startswith('num_'):
            suffix = key[4:]
            return suffix.isdigit() or suffix in ['enter', 'plus', 'minus']
            
        return key in special_keys
        
    def hotkey_start_action(self):
        """Действие для горячей клавиши запуска"""
        if not self.clicking:
            self.window.after(0, self.start_clicking)
            
    def hotkey_stop_action(self):
        """Действие для горячей клавиши остановки"""
        if self.clicking:
            self.window.after(0, self.stop_clicking)
            
    def setup_tray(self):
        try:
            # Создаем простую иконку
            image = Image.new('RGB', (64, 64), color='blue')
            
            menu = pystray.Menu(
                MenuItem("Показать", self.show_window),
                MenuItem("Скрыть", self.hide_to_tray),
                MenuItem("Выход", self.quit_app)
            )
            
            self.tray_icon = Icon("omniaclick", image, "OmniaClick", menu)
        except Exception as e:
            print(f"Ошибка создания трея: {e}")
            
    def hide_to_tray(self):
        self.window.withdraw()
        if self.tray_icon:
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
    def show_window(self, icon=None, item=None):
        self.window.deiconify()
        if self.tray_icon:
            self.tray_icon.stop()
            
    def start_monitoring(self):
        if not self.monitor_thread and WIN32_AVAILABLE:
            self.monitor_thread = threading.Thread(target=self.monitor_system, daemon=True)
            self.monitor_thread.start()
            
    def monitor_system(self):
        if not WIN32_AVAILABLE:
            return
            
        while True:
            try:
                # Сохраняем текущее активное окно
                self.active_window = win32gui.GetForegroundWindow()
                time.sleep(0.1)
            except:
                time.sleep(1)
                

            
    def quit_app(self, icon=None, item=None):
        """Выход из приложения"""
        try:
            # Останавливаем все процессы
            self.clicking = False
            if hasattr(self, 'monitor_thread') and self.monitor_thread:
                self.monitor_thread.join(timeout=1)
            
            # Принудительно очищаем все оверлеи
            self.force_cleanup_overlays()
            
            # Удаляем все временные файлы скриншотов
            self.cleanup_temp_files()
            
            # Удаляем иконку из трея
            if hasattr(self, 'tray_icon') and self.tray_icon:
                try:
                    self.tray_icon.stop()
                except:
                    pass
            
            # Закрываем окно только если оно еще существует
            if hasattr(self, 'window') and self.window:
                try:
                    if self.window.winfo_exists():
                        self.window.quit()
                        self.window.destroy()
                except:
                    pass
            
        except Exception as e:
            print(f"Ошибка при выходе: {e}")
            import sys
            sys.exit(0)
        
    def on_closing(self):
        try:
            self.save_settings(show_message=False)  # Тихое сохранение при выходе
            self.quit_app()
        except Exception as e:
            print(f"Ошибка при закрытии: {e}")
            import sys
            sys.exit(0)
        
    def run(self):
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def add_keyboard_key(self):
        """Добавляет новую клавишу в последовательность для нажатия"""
        key = self.new_key_var.get().strip()
        presses = self.key_presses_var.get()
        
        # Проверка на пустую строку
        if not key:
            messagebox.showwarning("Внимание", "Введите клавишу для добавления.")
            return
        # Проверка на максимальное количество клавиш
        if len(self.keyboard_sequence) >= 5:
            messagebox.showwarning("Внимание", "Максимум 5 клавиш в последовательности.")
            return
        # Проверка на дубликаты
        for entry in self.keyboard_sequence:
            if entry['key'] == key:
                messagebox.showwarning("Внимание", "Такая клавиша уже добавлена.")
                return
        # Добавление
        self.keyboard_sequence.append({'key': key, 'presses': presses})
        self.update_keyboard_sequence_list()
        self.new_key_var.set("")
        self.key_presses_var.set(1)

    def update_keyboard_sequence_list(self):
        """Обновляет отображение списка клавиш в listbox"""
        if hasattr(self, 'keyboard_sequence_listbox'):
            self.keyboard_sequence_listbox.delete(0, tk.END)
            for entry in self.keyboard_sequence:
                text = f"{entry['key']} (x{entry['presses']})"
                self.keyboard_sequence_listbox.insert(tk.END, text)
                
    def remove_keyboard_key(self):
        """Удаляет выбранную клавишу из последовательности"""
        if hasattr(self, 'keyboard_sequence_listbox'):
            selection = self.keyboard_sequence_listbox.curselection()
            if selection:
                index = selection[0]
                self.keyboard_sequence_listbox.delete(index)
                del self.keyboard_sequence[index]
            else:
                messagebox.showwarning("Внимание", "Выберите клавишу для удаления.")
                
    def clear_keyboard_sequence(self):
        """Очищает всю последовательность клавиш"""
        if hasattr(self, 'keyboard_sequence_listbox'):
            self.keyboard_sequence_listbox.delete(0, tk.END)
            self.keyboard_sequence.clear()
            
    def update_key_presses(self):
        """Изменяет количество нажатий для выбранной клавиши"""
        if hasattr(self, 'keyboard_sequence_listbox'):
            selection = self.keyboard_sequence_listbox.curselection()
            if selection:
                index = selection[0]
                if 0 <= index < len(self.keyboard_sequence):
                    # Создаем диалог для ввода нового количества нажатий
                    dialog = tk.Toplevel(self.window)
                    dialog.title("Изменить количество нажатий")
                    dialog.geometry("300x150")
                    dialog.resizable(False, False)
                    dialog.transient(self.window)
                    dialog.grab_set()
                    
                    # Центрируем диалог
                    dialog.update_idletasks()
                    x = (dialog.winfo_screenwidth() // 2) - (300 // 2)
                    y = (dialog.winfo_screenheight() // 2) - (150 // 2)
                    dialog.geometry(f"300x150+{x}+{y}")
                    
                    # Содержимое диалога
                    ttk.Label(dialog, text=f"Клавиша: {self.keyboard_sequence[index]['key']}", 
                             font=('Arial', 10, 'bold')).pack(pady=(20, 10))
                    
                    frame = ttk.Frame(dialog)
                    frame.pack(pady=10)
                    
                    ttk.Label(frame, text="Количество нажатий:").pack(side=tk.LEFT, padx=(0, 10))
                    presses_var = tk.IntVar(value=self.keyboard_sequence[index]['presses'])
                    spinbox = ttk.Spinbox(frame, from_=1, to=50, width=5, textvariable=presses_var)
                    spinbox.pack(side=tk.LEFT)
                    
                    # Кнопки
                    button_frame = ttk.Frame(dialog)
                    button_frame.pack(pady=20)
                    
                    def apply_changes():
                        new_presses = presses_var.get()
                        if 1 <= new_presses <= 50:
                            self.keyboard_sequence[index]['presses'] = new_presses
                            self.update_keyboard_sequence_list()
                            dialog.destroy()
                        else:
                            messagebox.showwarning("Внимание", "Количество нажатий должно быть от 1 до 50.")
                    
                    def cancel_changes():
                        dialog.destroy()
                    
                    ttk.Button(button_frame, text="Применить", command=apply_changes).pack(side=tk.LEFT, padx=(0, 10))
                    ttk.Button(button_frame, text="Отмена", command=cancel_changes).pack(side=tk.LEFT)
                    
                    # Фокус на spinbox
                    spinbox.focus_set()
                    spinbox.select_range(0, tk.END)
                    
                    # Привязываем Enter к применению изменений
                    dialog.bind('<Return>', lambda e: apply_changes())
                    dialog.bind('<Escape>', lambda e: cancel_changes())
                    
            else:
                messagebox.showwarning("Внимание", "Выберите клавишу для изменения количества нажатий.")

    def on_keyboard_click(self, event):
        """Когда пользователь кликает на поле ввода клавиш"""
        entry = event.widget
        entry.config(state='normal')
        entry.focus_set()
        return 'break'
        
    def on_keyboard_focus_in(self, event):
        """Когда поле ввода клавиш получает фокус"""
        entry = event.widget
        entry.config(background='lightblue', state='normal')
        current_value = self.new_key_var.get()
        if current_value == '' or current_value == 'Нажмите клавишу...':
            self.new_key_var.set('Нажмите клавишу...')
        entry.select_range(0, tk.END)
            
    def on_keyboard_focus_out(self, event):
        """Когда поле ввода клавиш теряет фокус"""
        entry = event.widget
        entry.config(background='white', state='normal')
        
        # Если ничего не было установлено, очищаем поле
        if self.new_key_var.get() == 'Нажмите клавишу...':
            self.new_key_var.set('')
            
    def on_keyboard_press(self, event):
        """Обработка нажатия клавиши в поле ввода клавиш"""
        key_name = self.get_key_name(event)
        
        if key_name:
            self.new_key_var.set(key_name)
            # Убираем фокус с поля
            self.window.focus()
            
        return 'break'  # Предотвращаем обычную обработку события

    def setup_emergency_stop(self):
        """Настройка экстренной остановки"""
        try:
            # Глобальная экстренная остановка через Ctrl+Alt+X
            keyboard.add_hotkey('ctrl+alt+x', self.emergency_stop)
            # Альтернативная экстренная остановка через F12
            keyboard.add_hotkey('f12', self.emergency_stop)
        except Exception as e:
            print(f"Не удалось установить экстренные горячие клавиши: {e}")
    
    def emergency_stop(self):
        """Экстренная остановка приложения"""
        print("ЭКСТРЕННАЯ ОСТАНОВКА АКТИВИРОВАНА!")
        self.clicking = False
        try:
            # Принудительно завершаем все потоки
            import os
            import signal
            os.kill(os.getpid(), signal.SIGTERM)
        except:
            # Если не удалось через signal, пытаемся через quit
            try:
                self.window.quit()
                self.window.destroy()
            except:
                # Последняя попытка - exit
                import sys
                sys.exit(1)

    def disable_hotkeys(self):
        """Отключить горячие клавиши"""
        try:
            self.hotkeys_disabled = True
            # Удаляем горячие клавиши с проверкой существования
            try:
                keyboard.remove_hotkey(self.hotkey_start.get())
            except:
                pass  # Игнорируем ошибку, если горячая клавиша не была зарегистрирована
            try:
                keyboard.remove_hotkey(self.hotkey_stop.get())
            except:
                pass  # Игнорируем ошибку, если горячая клавиша не была зарегистрирована
        except Exception as e:
            print(f"Ошибка отключения горячих клавиш: {e}")
    
    def enable_hotkeys(self):
        """Включить горячие клавиши"""
        try:
            self.hotkeys_disabled = False
            # Восстанавливаем горячие клавиши
            keyboard.add_hotkey(self.hotkey_start.get(), self.hotkey_start_action)
            keyboard.add_hotkey(self.hotkey_stop.get(), self.hotkey_stop_action)
        except Exception as e:
            print(f"Ошибка включения горячих клавиш: {e}")

    def create_overlay_window(self, x1, y1, x2, y2, color="red", width=2, alpha=0.3):
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
    
    def show_selection_overlay(self, x1, y1, x2, y2):
        """Показать/обновить оверлей выбора области (желтый, процесс выбора)"""
        # Проверяем, что координаты различаются и область достаточно большая
        if x1 == x2 or y1 == y2 or abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            return
        width_rect = abs(x2 - x1)
        height_rect = abs(y2 - y1)
        pos_x = min(x1, x2)
        pos_y = min(y1, y2)
        
        if not hasattr(self, 'selection_overlay') or self.selection_overlay is None or not self.selection_overlay.winfo_exists():
            # Создаем overlay только один раз
            self.selection_overlay = tk.Toplevel()
            self.selection_overlay.overrideredirect(True)
            self.selection_overlay.attributes("-topmost", True)
            self.selection_overlay.attributes("-transparentcolor", "black")
            self.selection_overlay.config(bg="black")
            self.selection_canvas = tk.Canvas(self.selection_overlay, bg="black", highlightthickness=0)
            self.selection_canvas.pack(fill=tk.BOTH, expand=True)
        # Меняем размер и позицию окна
        self.selection_overlay.geometry(f"{width_rect}x{height_rect}+{pos_x}+{pos_y}")
        self.selection_canvas.config(width=width_rect, height=height_rect)
        self.selection_canvas.delete("all")
        self.selection_canvas.create_rectangle(0, 0, width_rect, height_rect, outline="yellow", width=3)

    def hide_selection_overlay(self):
        """Скрытие временного оверлея выбора"""
        try:
            if hasattr(self, 'selection_overlay') and self.selection_overlay:
                if self.selection_overlay.winfo_exists():
                    self.selection_overlay.destroy()
                self.selection_overlay = None
                self.selection_canvas = None
        except Exception as e:
            print(f"Ошибка скрытия оверлея выбора: {e}")
            
    def show_area_overlay(self):
        """Показ фиксированного оверлея выбранной области"""
        if self.search_area:
            x1, y1, x2, y2 = self.search_area
            self.create_overlay_window(x1, y1, x2, y2, color="lime", width=3, alpha=0.5)
            
    def hide_area_overlay(self):
        """Скрытие фиксированного оверлея области (и очистка всех лишних оверлеев)"""
        try:
            if hasattr(self, 'overlay_window') and self.overlay_window:
                if self.overlay_window.winfo_exists():
                    self.overlay_window.destroy()
                self.overlay_window = None
            # Дополнительно очищаем все Toplevel окна (на всякий случай)
            self.force_cleanup_overlays()
        except Exception as e:
            print(f"Ошибка скрытия оверлея области: {e}")

    def show_area_success_dialog(self, area_text):
        """Показывает диалог с сообщением об успехе после выбора области"""
        messagebox.showinfo("Успех", f"Область выбрана:\n{area_text}")
        self.window.after(0, self.hide_selection_overlay)

    def force_cleanup_overlays(self):
        """Принудительная очистка всех оверлеев"""
        try:
            # Очищаем все дочерние окна только если главное окно существует
            if hasattr(self, 'window') and self.window and self.window.winfo_exists():
                for child in self.window.winfo_children():
                    try:
                        if isinstance(child, tk.Toplevel):
                            child.destroy()
                    except:
                        pass
            
            # Сбрасываем ссылки на оверлеи
            self.selection_overlay = None
            self.overlay_window = None
            
        except Exception as e:
            print(f"Ошибка очистки оверлеев: {e}")

    def cleanup_old_overlays(self):
        """Очистка старых оверлеев"""
        try:
            # Удаляем все Toplevel окна
            for widget in self.window.winfo_children():
                if isinstance(widget, tk.Toplevel):
                    try:
                        widget.destroy()
                    except:
                        pass
        except Exception as e:
            print(f"Ошибка очистки старых оверлеев: {e}")
            
    def cleanup_temp_files(self):
        """Удаление всех временных файлов скриншотов"""
        try:
            # Удаляем все временные файлы скриншотов из последовательности
            for template in self.image_sequence:
                if template.get('type') == 'capture' and os.path.exists(template.get('path', '')):
                    try:
                        os.remove(template['path'])
                    except:
                        pass
            
            # Удаляем одиночный временный шаблон
            if hasattr(self, 'template_image') and self.template_image:
                if os.path.basename(self.template_image).startswith('temp_template_'):
                    try:
                        os.remove(self.template_image)
                    except:
                        pass
                        
        except Exception as e:
            print(f"Ошибка очистки временных файлов: {e}")

    def add_key_to_sequence(self):
        """Добавляет нажатие клавиши в последовательность шаблонов"""
        key = self.sequence_key_var.get().strip()
        presses = self.sequence_key_presses_var.get()
        
        # Проверка на пустую строку
        if not key:
            messagebox.showwarning("Внимание", "Введите клавишу для добавления.")
            return
            
        # Добавление клавиши в последовательность
        key_entry = {
            "type": "key",
            "key": key,
            "presses": presses,
            "name": f"Клавиша: {key} (x{presses})"
        }
        
        self.image_sequence.append(key_entry)
        self.update_image_sequence_list()
        self.sequence_key_var.set("")
        self.sequence_key_presses_var.set(1)
        
    def move_sequence_item_up(self):
        """Перемещает выбранный элемент последовательности вверх"""
        if hasattr(self, 'image_sequence_listbox'):
            selection = self.image_sequence_listbox.curselection()
            if selection and selection[0] > 0:
                index = selection[0]
                # Меняем местами элементы
                self.image_sequence[index], self.image_sequence[index-1] = self.image_sequence[index-1], self.image_sequence[index]
                self.update_image_sequence_list()
                # Выбираем перемещенный элемент
                self.image_sequence_listbox.selection_set(index-1)
                
    def move_sequence_item_down(self):
        """Перемещает выбранный элемент последовательности вниз"""
        if hasattr(self, 'image_sequence_listbox'):
            selection = self.image_sequence_listbox.curselection()
            if selection and selection[0] < len(self.image_sequence) - 1:
                index = selection[0]
                # Меняем местами элементы
                self.image_sequence[index], self.image_sequence[index+1] = self.image_sequence[index+1], self.image_sequence[index]
                self.update_image_sequence_list()
                # Выбираем перемещенный элемент
                self.image_sequence_listbox.selection_set(index+1)
                
    def edit_sequence_text(self):
        """Открывает окно для текстового редактирования последовательности"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Редактирование последовательности")
        dialog.geometry("600x500")
        dialog.resizable(True, True)
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Центрируем окно
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Создаем текстовое поле
        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Заголовок с инструкциями
        instructions = """Формат записи:
- Шаблон: [путь_к_файлу] клики=N
- Клавиша: {клавиша} нажатий=N

Примеры:
C:\\images\\button.png клики=3
{space} нажатий=2
C:\\images\\icon.png клики=1
{enter} нажатий=1"""
        
        ttk.Label(text_frame, text=instructions, font=("Arial", 9), foreground="blue").pack(anchor=tk.W, pady=(0, 10))
        
        # Текстовое поле
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10))
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # Загружаем текущую последовательность
        current_text = ""
        for item in self.image_sequence:
            if item['type'] == 'capture' or item['type'] == 'file':
                current_text += f"{item['path']} клики={item['clicks']}\n"
            elif item['type'] == 'key':
                current_text += f"{{{item['key']}}} нажатий={item['presses']}\n"
        
        text_widget.insert(tk.END, current_text)
        
        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def apply_changes():
            try:
                # Парсим текст и создаем новую последовательность
                new_sequence = []
                lines = text_widget.get("1.0", tk.END).strip().split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Парсим строку
                    if 'клики=' in line:
                        # Шаблон изображения
                        parts = line.split(' клики=')
                        if len(parts) == 2:
                            path = parts[0].strip()
                            clicks = int(parts[1])
                            
                            if os.path.exists(path):
                                new_sequence.append({
                                    "type": "file" if not path.startswith("temp_template_") else "capture",
                                    "path": path,
                                    "clicks": clicks,
                                    "name": os.path.basename(path)
                                })
                            else:
                                messagebox.showerror("Ошибка", f"Файл не найден: {path}")
                                return
                    elif 'нажатий=' in line:
                        # Клавиша
                        parts = line.split(' нажатий=')
                        if len(parts) == 2:
                            key_part = parts[0].strip()
                            presses = int(parts[1])
                            
                            # Извлекаем клавишу из {клавиша}
                            if key_part.startswith('{') and key_part.endswith('}'):
                                key = key_part[1:-1]
                                new_sequence.append({
                                    "type": "key",
                                    "key": key,
                                    "presses": presses,
                                    "name": f"Клавиша: {key} (x{presses})"
                                })
                            else:
                                messagebox.showerror("Ошибка", f"Неверный формат клавиши: {key_part}")
                                return
                    else:
                        messagebox.showerror("Ошибка", f"Неверный формат строки: {line}")
                        return
                
                # Применяем новую последовательность
                self.image_sequence = new_sequence
                self.update_image_sequence_list()
                dialog.destroy()
                messagebox.showinfo("Успех", "Последовательность обновлена!")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при парсинге: {e}")
        
        def cancel_changes():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Применить", command=apply_changes).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Отмена", command=cancel_changes).pack(side=tk.RIGHT)
        
        # Фокус на текстовое поле
        text_widget.focus_set()
        
    def setup_sequence_key_capture(self):
        """Настройка перехвата клавиш для поля ввода клавиш в последовательности"""
        if hasattr(self, 'sequence_key_entry'):
            self.sequence_key_entry.bind('<Button-1>', self.on_sequence_key_click)
            self.sequence_key_entry.bind('<FocusIn>', self.on_sequence_key_focus_in)
            self.sequence_key_entry.bind('<FocusOut>', self.on_sequence_key_focus_out)
            self.sequence_key_entry.bind('<Key>', self.on_sequence_key_press)
            
    def on_sequence_key_click(self, event):
        """Обработчик клика по полю ввода клавиши в последовательности"""
        self.sequence_key_entry.config(state='readonly')
        self.sequence_key_entry.focus_set()
        
    def on_sequence_key_focus_in(self, event):
        """Обработчик получения фокуса полем ввода клавиши в последовательности"""
        if not self.sequence_key_var.get() or self.sequence_key_var.get() == "Нажмите клавишу...":
            self.sequence_key_var.set("")
            
    def on_sequence_key_focus_out(self, event):
        """Обработчик потери фокуса полем ввода клавиши в последовательности"""
        if not self.sequence_key_var.get():
            self.sequence_key_var.set("Нажмите клавишу...")
        self.sequence_key_entry.config(state='normal')
        
    def on_sequence_key_press(self, event):
        """Обработчик нажатия клавиши в поле ввода клавиши в последовательности"""
        key_name = self.get_key_name(event)
        if key_name:
            self.sequence_key_var.set(key_name)
            self.sequence_key_entry.config(state='normal')
        return "break"

    def setup_user_activity_monitor(self):
        """Настройка отслеживания пользовательской активности (мышь, клавиатура)"""
        self.window.bind_all('<Motion>', self.on_user_activity, add='+')
        self.window.bind_all('<Key>', self.on_user_activity, add='+')

    def on_user_activity(self, event=None):
        self.last_user_activity = time.time()
        self.user_activity_detected = True
        self.last_found_image_position = None
        self.last_found_color_position = None
        self.clicks_since_last_search = 0
        if self.clicking:
            self.user_pause = True

    def clear_search_area(self):
        """Сбросить выбранную область поиска"""
        self.search_area = None
        self.hide_area_overlay()
        if hasattr(self, 'area_label'):
            self.area_label.config(text="Область: весь экран")
        if hasattr(self, 'image_area_label'):
            self.image_area_label.config(text="Область: весь экран")
            
    def save_current_settings(self):
        """Сохраняет текущие настройки в файл"""
        try:
            settings = {
                "interval": self.interval_var.get(),
                "click_type": self.click_type.get(),
                "turbo_mode": self.turbo_mode.get(),
                "extreme_mode": self.extreme_mode.get(),
                "pause_on_mouse": self.pause_on_mouse.get(),
                "pause_on_window": self.pause_on_window.get(),
                "sound_notifications": self.sound_notifications.get(),
                "hotkey_start": self.hotkey_start.get(),
                "hotkey_stop": self.hotkey_stop.get(),
                "click_mode": self.click_mode.get(),
                "target_color": self.target_color,
                "color_tolerance": self.color_tolerance.get(),
                "sequence_points": self.sequence_points,
                "keyboard_sequence": self.keyboard_sequence,
                "image_sequence": self.image_sequence,
                "image_sequence_repeats": self.image_sequence_repeats.get(),
                "search_area": self.search_area,
                "template_image": self.template_image,
                "image_confidence": self.image_confidence.get(),
                "image_mode": getattr(self, 'image_mode', tk.StringVar(value="single")).get()
            }
            
            with open("saved_settings.json", 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Успех", "Настройки сохранены в файл saved_settings.json!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")
            
    def load_saved_settings(self):
        """Загружает настройки из файла"""
        try:
            if not os.path.exists("saved_settings.json"):
                messagebox.showwarning("Предупреждение", "Файл saved_settings.json не найден!")
                return
                
            with open("saved_settings.json", 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
            # Применяем настройки
            self.interval_var.set(settings.get("interval", 0.1))
            self.click_type.set(settings.get("click_type", "left"))
            self.turbo_mode.set(settings.get("turbo_mode", False))
            self.extreme_mode.set(settings.get("extreme_mode", False))
            self.pause_on_mouse.set(settings.get("pause_on_mouse", False))
            self.pause_on_window.set(settings.get("pause_on_window", False))
            self.sound_notifications.set(settings.get("sound_notifications", True))
            self.hotkey_start.set(settings.get("hotkey_start", "f6"))
            self.hotkey_stop.set(settings.get("hotkey_stop", "f7"))
            self.click_mode.set(settings.get("click_mode", "normal"))
            self.target_color = settings.get("target_color", "#FF0000")
            self.color_tolerance.set(settings.get("color_tolerance", 10))
            self.sequence_points = settings.get("sequence_points", [])
            self.keyboard_sequence = settings.get("keyboard_sequence", [])
            self.image_sequence = settings.get("image_sequence", [])
            self.image_sequence_repeats.set(settings.get("image_sequence_repeats", 1))
            self.search_area = settings.get("search_area")
            self.template_image = settings.get("template_image")
            self.image_confidence.set(settings.get("image_confidence", 0.8))
            
            if "image_mode" in settings and hasattr(self, 'image_mode'):
                self.image_mode.set(settings.get("image_mode", "single"))
                
            # Обновляем интерфейс
            if hasattr(self, 'color_display'):
                self.color_display.config(bg=self.target_color)
            if hasattr(self, 'tolerance_label'):
                self.tolerance_label.config(text=str(self.color_tolerance.get()))
            if hasattr(self, 'area_label'):
                txt = "Область: весь экран" if not self.search_area else f"Область: {self.search_area}"
                self.area_label.config(text=txt)
            if hasattr(self, 'image_area_label'):
                self.image_area_label.config(text=txt)
            if hasattr(self, 'sequence_listbox'):
                self.sequence_listbox.delete(0, tk.END)
                for point in self.sequence_points:
                    point_text = f"({point['x']}, {point['y']}) - {point['clicks']} кликов"
                    self.sequence_listbox.insert(tk.END, point_text)
            if hasattr(self, 'keyboard_sequence_listbox'):
                self.update_keyboard_sequence_list()
            if hasattr(self, 'image_sequence_listbox'):
                self.update_image_sequence_list()
                
            self.mode_changed()
            self.setup_hotkeys(False)
            
            messagebox.showinfo("Успех", "Настройки загружены из файла saved_settings.json!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить настройки: {e}")



    def create_template_from_search_area(self):
        """Создает новый шаблон из области поиска"""
        if not self.search_area:
            print("Область поиска не выбрана")
            return None
            
        try:
            x1, y1, x2, y2 = self.search_area
            width = x2 - x1
            height = y2 - y1
            
            # Делаем скриншот области поиска
            screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
            
            # Сохраняем как новый шаблон
            new_template_path = f"temp_template_area_{int(time.time())}.png"
            screenshot.save(new_template_path)
            
            print(f"Создан новый шаблон из области поиска: {new_template_path}")
            print(f"Размер: {width}x{height}")
            
            return new_template_path
            
        except Exception as e:
            print(f"Ошибка создания шаблона из области поиска: {e}")
            return None

    def create_template_from_search_area_ui(self):
        """Создает шаблон из области поиска через UI"""
        if not self.search_area:
            messagebox.showwarning("Предупреждение", "Сначала выберите область поиска!")
            return
            
        new_template = self.create_template_from_search_area()
        if new_template:
            self.template_image = new_template
            # Обновляем метку в интерфейсе
            name = os.path.basename(new_template)
            if len(name) > 30:
                name = name[:27] + "..."
            self.template_label.config(text=f"Шаблон: {name}")
            messagebox.showinfo("Успех", f"Создан новый шаблон: {name}")
        else:
            messagebox.showerror("Ошибка", "Не удалось создать шаблон из области поиска")

    def _search_image_position(self, template_path, region_override=None):
        """Ищет картинку и возвращает (True, позиция) или (False, None)"""
        if not template_path or not os.path.exists(template_path):
            return False, None
        try:
            region = None
            if region_override:
                region = region_override
            elif self.search_area:
                x1, y1, x2, y2 = self.search_area
                region = (x1, y1, x2 - x1, y2 - y1)
            if OPENCV_AVAILABLE:
                location = pyautogui.locateOnScreen(
                    template_path, 
                    confidence=self.image_confidence.get(),
                    region=region
                )
            else:
                location = pyautogui.locateOnScreen(
                    template_path, 
                    region=region
                )
            if location:
                center = pyautogui.center(location)
                return True, center
        except Exception as e:
            print(f"Ошибка поиска картинки: {e}")
        return False, None



if __name__ == "__main__":
    try:
        app = AutoClicker()
        app.run()
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        messagebox.showerror("Ошибка", f"Не удалось запустить приложение: {e}")