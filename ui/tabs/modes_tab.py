"""
OmniaClick - Вкладка режимов кликов

Вкладка с различными режимами кликов: обычный, поиск по цвету,
поиск по изображению, нажатие клавиш, последовательность точек
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import os

from config import *


class ModesTab:
    """Вкладка режимов кликов"""
    
    def __init__(self, parent, app_instance):
        """
        Инициализация вкладки режимов
        
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
        
        # Инициализация видимости
        self.mode_changed()
        
        # Устанавливаем начальный режим в app
        self.app.current_mode = self.click_mode.get()
        
    def _init_variables(self):
        """Инициализация всех переменных для элементов интерфейса"""
        self.click_mode = tk.StringVar(value="normal")
        self.color_var = tk.StringVar(value="#FF0000")  
        self.search_area_text = tk.StringVar(value="Область не выбрана")
        
        # Переменные для изображений
        self.template_path_var = tk.StringVar(value="Файл не выбран")
        self.image_click_mode = tk.StringVar(value="single")
        
        # Переменные для клавиатуры
        self.key_to_press = tk.StringVar(value="space")
        
        # Переменные для последовательности шаблонов
        self.sequence_key_var = tk.StringVar(value="space")
        self.sequence_key_presses_var = tk.IntVar(value=1)
        self.template_clicks_var = tk.IntVar(value=1)
        
        # Массив для хранения последовательности шаблонов (как в оригинале)
        # Используем image_sequence из главного приложения
        
    def _setup_gui(self):
        """Настройка интерфейса вкладки режимов"""
        # Выбор режима кликов
        self._setup_mode_selection()
        
        # Настройки для каждого режима
        self._setup_color_settings()
        self._setup_image_settings()
        self._setup_keyboard_settings()
        self._setup_sequence_settings()
        
        # Показываем только настройки для выбранного режима
        self.mode_changed()
        
    def _setup_mode_selection(self):
        """Настройка выбора режима"""
        mode_frame = ttk.LabelFrame(self.frame, text="Режим клика", padding="10")
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
                       
    def _setup_color_settings(self):
        """Настройки поиска по цвету"""
        self.color_frame = ttk.LabelFrame(self.frame, text="Настройки поиска по цвету", padding="10")
        self.color_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Выбор цвета
        color_select_frame = ttk.Frame(self.color_frame)
        color_select_frame.pack(fill=tk.X)
        
        ttk.Label(color_select_frame, text="Целевой цвет:").pack(side=tk.LEFT)
        self.color_display = tk.Label(color_select_frame, bg=self.color_var.get(), 
                                     width=4, height=2, relief="solid")
        self.color_display.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Button(color_select_frame, text="Выбрать цвет", 
                  command=self._choose_color).pack(side=tk.LEFT)
        ttk.Button(color_select_frame, text="Пипетка", 
                  command=self._pick_color).pack(side=tk.LEFT, padx=(5, 0))
        
        # Толерантность цвета
        ttk.Label(self.color_frame, text="Толерантность цвета:").pack(anchor=tk.W, pady=(10, 0))
        tolerance_frame = ttk.Frame(self.color_frame)
        tolerance_frame.pack(fill=tk.X, pady=5)
        
        tolerance_scale = ttk.Scale(tolerance_frame, from_=0, to=50, variable=self.app.color_tolerance_var, 
                 orient=tk.HORIZONTAL, command=self._update_tolerance_label)
        tolerance_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.tolerance_label = ttk.Label(tolerance_frame, text=str(int(self.app.color_tolerance_var.get())))
        self.tolerance_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Область поиска для цвета
        self._setup_color_area_buttons()
        
    def _setup_color_area_buttons(self):
        """Кнопки области поиска для цвета"""
        area_frame = ttk.Frame(self.color_frame)
        area_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(area_frame, text="Выбрать область поиска",
                  command=self._select_search_area).pack(side=tk.LEFT)
        ttk.Button(area_frame, text="Показать область",
                  command=self._show_area_overlay).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(area_frame, text="Скрыть область",
                  command=self._hide_area_overlay).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(area_frame, text="Очистить область",
                  command=self._clear_search_area).pack(side=tk.LEFT, padx=(5, 0))
        
        self.area_label = ttk.Label(area_frame, text="Область: весь экран")
        self.area_label.pack(side=tk.RIGHT)
        
    def _setup_image_settings(self):
        """Настройки поиска картинки"""
        self.image_frame = ttk.LabelFrame(self.frame, text="Настройки поиска картинки", padding="10")
        self.image_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Выбор режима картинки
        image_mode_frame = ttk.Frame(self.image_frame)
        image_mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Radiobutton(image_mode_frame, text="Одиночный поиск", variable=self.image_click_mode, 
                       value="single", command=self._image_mode_changed).pack(side=tk.LEFT)
        ttk.Radiobutton(image_mode_frame, text="Последовательность картинок", variable=self.image_click_mode, 
                       value="sequence", command=self._image_mode_changed).pack(side=tk.LEFT, padx=(20, 0))
        
        # Одиночный шаблон
        self._setup_single_template()
        
        # Последовательность шаблонов
        self._setup_sequence_templates()
        
        # Точность поиска
        self._setup_image_confidence()
        
        # Область поиска для картинки
        self._setup_image_area_buttons()
        
    def _setup_single_template(self):
        """Настройка одиночного шаблона"""
        self.single_template_frame = ttk.LabelFrame(self.image_frame, text="Одиночный шаблон", padding="5")
        self.single_template_frame.pack(fill=tk.X, pady=(0, 10))
        
        template_frame = ttk.Frame(self.single_template_frame)
        template_frame.pack(fill=tk.X)
        
        ttk.Button(template_frame, text="Загрузить шаблон", 
                  command=self._load_template_image).pack(side=tk.LEFT)
        ttk.Button(template_frame, text="Сделать скриншот области", 
                  command=self._capture_template).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(template_frame, text="Создать из области поиска", 
                  command=self._create_template_from_search_area).pack(side=tk.LEFT, padx=(5, 0))
        
        self.template_label = ttk.Label(self.single_template_frame, text="Шаблон не выбран", 
                                       font=("Arial", 8), foreground="gray")
        self.template_label.pack(anchor=tk.W, pady=(5, 0))
        
    def _setup_sequence_templates(self):
        """Настройка последовательности шаблонов"""
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
                  command=self._add_template_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(seq_img_buttons, text="Захватить область", 
                  command=self._add_template_capture).pack(side=tk.LEFT, padx=(0, 5))
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
                  command=self._edit_sequence_text).pack(side=tk.LEFT, padx=(10, 0))
        
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
                  command=self._add_key_to_sequence).pack(side=tk.LEFT, padx=(5, 0))
        
        # Настройка кликов для выбранного шаблона
        clicks_frame = ttk.Frame(self.sequence_template_frame)
        clicks_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(clicks_frame, text="Кликов для выбранного:").pack(side=tk.LEFT)
        clicks_spinbox = ttk.Spinbox(clicks_frame, from_=1, to=100, width=5, 
                                    textvariable=self.template_clicks_var,
                                    command=self._update_template_clicks)
        clicks_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(clicks_frame, text="Применить", 
                  command=self._update_template_clicks).pack(side=tk.LEFT, padx=(5, 0))
                  
        # Настройки повторения последовательности
        sequence_settings_frame = ttk.Frame(self.sequence_template_frame)
        sequence_settings_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(sequence_settings_frame, text="Повторений последовательности:").pack(side=tk.LEFT)
        repeats_spinbox = ttk.Spinbox(sequence_settings_frame, from_=0, to=1000, width=5, 
                                     textvariable=self.app.image_sequence_repeats_var)
        repeats_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(sequence_settings_frame, text="(0 = без остановки)").pack(side=tk.LEFT, padx=(5, 0))
        
        # Настройка перехвата клавиш для поля ввода клавиш
        self.setup_sequence_key_capture()
        
    def _setup_image_confidence(self):
        """Настройка точности поиска"""
        confidence_label_text = "Точность поиска (0.1-1.0):"
        if not OPENCV_AVAILABLE:
            confidence_label_text += " (OpenCV не установлен - точное совпадение)"
        ttk.Label(self.image_frame, text=confidence_label_text).pack(anchor=tk.W, pady=(10, 0))
        
        confidence_frame = ttk.Frame(self.image_frame)
        confidence_frame.pack(fill=tk.X, pady=5)
        
        confidence_scale = ttk.Scale(confidence_frame, from_=0.1, to=1.0, variable=self.app.image_confidence_var, 
               orient=tk.HORIZONTAL, command=self._update_confidence_label)
        confidence_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.confidence_label = ttk.Label(confidence_frame, text=f"{self.app.image_confidence_var.get():.2f}")
        self.confidence_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Предупреждение о OpenCV
        if not OPENCV_AVAILABLE:
            ttk.Label(self.image_frame, text="Для точного поиска установите: pip install opencv-python", 
                     font=("Arial", 8), foreground="orange").pack(anchor=tk.W, pady=(5, 0))
                     
    def _setup_image_area_buttons(self):
        """Кнопки области поиска для картинки"""
        image_area_frame = ttk.Frame(self.image_frame)
        image_area_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(image_area_frame, text="Выбрать область поиска",
                  command=self._select_search_area).pack(side=tk.LEFT)
        ttk.Button(image_area_frame, text="Показать область",
                  command=self._show_area_overlay).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(image_area_frame, text="Скрыть область",
                  command=self._hide_area_overlay).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(image_area_frame, text="Очистить область",
                  command=self._clear_search_area).pack(side=tk.LEFT, padx=(5, 0))
        
        self.image_area_label = ttk.Label(image_area_frame, text="Область: весь экран")
        self.image_area_label.pack(side=tk.RIGHT)
        
    def _setup_keyboard_settings(self):
        """Настройки нажатия клавиш"""
        self.keyboard_frame = ttk.LabelFrame(self.frame, text="Настройки нажатия клавиш", padding="10")
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
        self.new_key_entry = ttk.Entry(add_key_frame, textvariable=self.key_to_press, width=15,
                                      justify='center', font=('Arial', 10, 'bold'))
        self.new_key_entry.pack(side=tk.LEFT, padx=(10, 5))
        
        # Настройка количества нажатий
        ttk.Label(add_key_frame, text="Нажатий:").pack(side=tk.LEFT, padx=(10, 5))
        key_presses_spinbox = ttk.Spinbox(add_key_frame, from_=1, to=50, width=5, 
                                         textvariable=self.app.key_presses_var)
        key_presses_spinbox.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(add_key_frame, text="Добавить", 
                  command=self._add_keyboard_key).pack(side=tk.LEFT, padx=(5, 0))
        
        # Кнопки управления последовательностью клавиш
        keyboard_buttons = ttk.Frame(self.keyboard_frame)
        keyboard_buttons.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(keyboard_buttons, text="Удалить выбранную", 
                  command=self._remove_keyboard_key).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(keyboard_buttons, text="Очистить все", 
                  command=self._clear_keyboard_sequence).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(keyboard_buttons, text="Изменить количество", 
                  command=self._update_key_presses).pack(side=tk.LEFT)
        
        # Ограничение: максимум 5 клавиш
        limit_label = ttk.Label(self.keyboard_frame, text="Максимум 5 клавиш в последовательности", 
                               font=("Arial", 8), foreground="gray")
        limit_label.pack(anchor=tk.W)
        
        # Настройка перехвата клавиш для поля ввода клавиш
        self.setup_keyboard_capture()
        
    def _setup_sequence_settings(self):
        """Настройка последовательности точек"""
        self.sequence_frame = ttk.LabelFrame(self.frame, text="Последовательность точек", padding="10")
        self.sequence_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Информация
        info_label = ttk.Label(self.sequence_frame, 
                              text="Выберите точки на экране для циклических кликов", 
                              font=("Arial", 9), foreground="blue")
        info_label.pack(pady=(0, 10))
        
        # Список точек
        list_frame = ttk.Frame(self.sequence_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.sequence_listbox = tk.Listbox(list_frame, height=6, font=("Arial", 9))
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.sequence_listbox.yview)
        self.sequence_listbox.config(yscrollcommand=scrollbar.set)
        
        self.sequence_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопки управления последовательностью точек
        seq_buttons = ttk.Frame(self.sequence_frame)
        seq_buttons.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(seq_buttons, text="Выбрать точку на экране", 
                  command=self._select_point_on_screen).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(seq_buttons, text="Удалить", 
                  command=self._remove_sequence_point).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(seq_buttons, text="Очистить", 
                  command=self._clear_sequence_points).pack(side=tk.LEFT)
        
        # Инструкция
        instruction_label = ttk.Label(self.sequence_frame, 
                                     text="Для выбора точки: наведите курсор и нажмите SHIFT + левая кнопка мыши", 
                                     font=("Arial", 8), foreground="gray")
        instruction_label.pack(pady=(10, 0))
        
    def mode_changed(self):
        """Обработчик изменения режима клика"""
        mode = self.click_mode.get()
        
        # Скрываем все фреймы режимов
        self.color_frame.pack_forget()
        self.image_frame.pack_forget()
        self.keyboard_frame.pack_forget()
        self.sequence_frame.pack_forget()
        
        # Показываем соответствующий фрейм
        if mode == "color":
            self.color_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        elif mode == "image":
            self.image_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            self._image_mode_changed()
        elif mode == "keyboard":
            self.keyboard_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        elif mode == "sequence":
            self.sequence_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
            self._update_sequence_display()  # Показываем текущую последовательность точек
            
        # Обновляем настройки в app
        self.app.current_mode = mode
        
    def _image_mode_changed(self):
        """Переключение между одиночным поиском и последовательностью"""
        mode = self.image_click_mode.get()
        if mode == "single":
            self.single_template_frame.pack(fill=tk.X, pady=(0, 10))
            self.sequence_template_frame.pack_forget()
        else:  # sequence
            self.single_template_frame.pack_forget()
            self.sequence_template_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
    # Обработчики для настроек цвета
    def _choose_color(self):
        """Выбор цвета через диалог"""
        color = colorchooser.askcolor(title="Выберите целевой цвет")
        if color[1]:  # Если цвет выбран
            self.color_var.set(color[1])
            self.color_display.config(bg=color[1])
            # Обновляем цвет в компоненте
            self.app.color_detector.set_target_color(color[1])
            
    def _pick_color(self):
        """Запуск пипетки для выбора цвета"""
        self.app.pick_color()
        
    def _update_tolerance_label(self, value):
        """Обновление подписи толерантности"""
        self.tolerance_label.config(text=str(int(float(value))))
        # Обновляем толерантность в компоненте
        self.app.color_detector.set_tolerance(int(float(value)))
        
    def _update_confidence_label(self, value):
        """Обновление подписи точности"""
        self.confidence_label.config(text=f"{float(value):.2f}")
        # Обновляем точность в компоненте
        self.app.image_processor.set_confidence(float(value))
        
    # Обработчики области поиска
    def _select_search_area(self):
        """Выбор области поиска"""
        self.app.select_search_area()
        
    def _show_area_overlay(self):
        """Показ области поиска"""
        if self.app.search_area:
            self.app.overlay_manager.show_area_overlay(*self.app.search_area)
        else:
            messagebox.showinfo("Область поиска", "Область поиска не выбрана")
        
    def _hide_area_overlay(self):
        """Скрытие области поиска"""
        self.app.overlay_manager.hide_area_overlay()
        
    def _clear_search_area(self):
        """Очистка области поиска"""
        self.app.clear_search_area()
        self.search_area_text.set("Область: весь экран")
        
    def _update_area_labels(self, text):
        """Обновление подписей области поиска"""
        self.area_label.config(text=text)
        self.image_area_label.config(text=text)
        
    # Обработчики для изображений
    def _load_template_image(self):
        """Загрузка шаблонной картинки"""
        file_path = self.app.file_manager.select_image_file()
        if file_path:
            self.template_path_var.set(file_path)
            self.app.image_processor.set_current_template(file_path)
            filename = os.path.basename(file_path)
            self.template_label.config(text=f"Шаблон: {filename}")
            
    def _capture_template(self):
        """Захват шаблона с экрана (одиночный)"""
        # Для одиночного шаблона
        self.app.capture_template()
        
    def _create_template_from_search_area(self):
        """Создание шаблона из области поиска"""
        if hasattr(self.app, 'search_area') and self.app.search_area:
            x1, y1, x2, y2 = self.app.search_area
            # Создаем шаблон из выбранной области
            self.app.template_capture.capture_from_search_area(x1, y1, x2, y2)
        else:
            messagebox.showwarning("Ошибка", "Сначала выберите область поиска")
        
    def _add_template_file(self):
        """Добавление файла шаблона в последовательность"""
        filename = filedialog.askopenfilename(
            title="Выберите картинку для добавления в последовательность",
            filetypes=[
                ('Изображения', '*.png *.jpg *.jpeg *.bmp *.gif'),
                ('Все файлы', '*.*')
            ]
        )
        
        if filename:
            name = os.path.basename(filename)
            self.image_sequence_listbox.insert(tk.END, f"Файл: {name}")
            
    def _add_template_capture(self):
        """Добавление захваченного шаблона в последовательность"""
        # Правильная реализация с callback как в оригинале
        def on_template_captured(template_info):
            """Callback для добавления захваченного шаблона в список"""
            if template_info and template_info.get('path'):
                # Добавляем в массив image_sequence как в оригинале
                template_item = {
                    'type': 'capture',
                    'name': template_info.get('name', 'Захваченный шаблон'),
                    'path': template_info['path'],
                    'clicks': 10  # Количество кликов по умолчанию
                }
                self.app.image_sequence.append(template_item)
                self.update_image_sequence_list()
                print(f"Шаблон добавлен в последовательность: {template_item['name']}")
                
        # Запускаем захват с правильным callback
        self.app.template_capture.capture_template(callback=on_template_captured)
        
    def _remove_image_template(self):
        """Удаление шаблона из последовательности"""
        selection = self.image_sequence_listbox.curselection()
        if selection:
            self.image_sequence_listbox.delete(selection[0])
            
    def _clear_image_sequence(self):
        """Очистка последовательности шаблонов"""
        self.image_sequence_listbox.delete(0, tk.END)
        
    # Обработчики для клавиш
    def _add_keyboard_key(self):
        """Добавление клавиши в последовательность"""
        key = self.key_to_press.get().strip()
        presses = self.app.key_presses_var.get()
        
        if not key:
            messagebox.showwarning("Ошибка", "Введите клавишу")
            return
            
        if len(self.app.keyboard_sequence) >= 5:
            messagebox.showwarning("Ограничение", "Максимум 5 клавиш в последовательности")
            return
            
        # Проверка на дубликаты
        for entry in self.app.keyboard_sequence:
            if entry['key'] == key:
                messagebox.showwarning("Ошибка", "Такая клавиша уже добавлена")
                return
            
        # Добавляем в последовательность
        self.app.keyboard_sequence.append({'key': key, 'presses': presses})
        self.update_keyboard_sequence_list()
        self.key_to_press.set("")
        
    def _remove_keyboard_key(self):
        """Удаление клавиши из последовательности"""
        selection = self.keyboard_sequence_listbox.curselection()
        if selection:
            index = selection[0]
            self.keyboard_sequence_listbox.delete(index)
            if 0 <= index < len(self.app.keyboard_sequence):
                del self.app.keyboard_sequence[index]
        else:
            messagebox.showwarning("Ошибка", "Выберите клавишу для удаления")
            
    def _clear_keyboard_sequence(self):
        """Очистка последовательности клавиш"""
        self.keyboard_sequence_listbox.delete(0, tk.END)
        self.app.keyboard_sequence.clear()
        
    def _update_key_presses(self):
        """Изменение количества нажатий для выбранной клавиши"""
        selection = self.keyboard_sequence_listbox.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите клавишу для изменения")
            return
            
        messagebox.showinfo("Изменение количества", "Функция изменения количества нажатий будет реализована позже")
        
    # Обработчики для последовательности точек
    def _select_point_on_screen(self):
        """Выбор точки на экране"""
        messagebox.showinfo("Выбор точки", 
                           "Наведите курсор на нужную точку на экране и нажмите SHIFT + левая кнопка мыши.\n" +
                           "Нажмите ESC для отмены.")
        # Здесь должна быть реализация выбора точки
        # Пока заглушка - в будущем добавим полноценную реализацию
        
    def _remove_sequence_point(self):
        """Удаление выбранной точки из последовательности"""
        selection = self.sequence_listbox.curselection()
        if selection:
            index = selection[0]
            self.sequence_listbox.delete(index)
            # Здесь должно быть удаление из массива sequence_points
            
    def _clear_sequence_points(self):
        """Очистка всех точек последовательности"""
        self.sequence_listbox.delete(0, tk.END)
        # Здесь должна быть очистка массива sequence_points
        
    def add_sequence_point(self, x, y, clicks=10):
        """Добавление точки в последовательность (вызывается из main.py)"""
        point_text = f"({x}, {y}) - {clicks} кликов"
        self.sequence_listbox.insert(tk.END, point_text)
        
    # Методы для старой последовательности шаблонов удалены
    # Теперь используется правильная последовательность точек
        
    def _ask_clicks_count(self):
        """Диалог для ввода количества кликов"""
        from tkinter.simpledialog import askinteger
        return askinteger("Количество кликов", "Сколько раз кликнуть по этой точке?", 
                         minvalue=1, maxvalue=100, initialvalue=10) or 10
                         
    def _ask_presses_count(self):
        """Диалог для ввода количества нажатий"""
        from tkinter.simpledialog import askinteger
        return askinteger("Количество нажатий", "Сколько раз нажать клавишу?", 
                         minvalue=1, maxvalue=100, initialvalue=1) or 0
                         
    def _update_sequence_display(self):
        """Обновление отображения последовательности точек"""
        if not hasattr(self, 'sequence_listbox'):
            return
            
        # Здесь будет обновление из sequence_points когда добавим в main.py
        pass
        
    def update_sequence_display(self, sequence):
        """Обновление отображения последовательности (вызывается из main.py)"""
        if hasattr(self, 'sequence_listbox'):
            self._update_sequence_display()
            
    def highlight_sequence_item(self, index):
        """Подсветка текущего элемента последовательности"""
        if hasattr(self, 'sequence_listbox'):
            self.sequence_listbox.selection_clear(0, tk.END)
            if 0 <= index < self.sequence_listbox.size():
                self.sequence_listbox.selection_set(index)
                self.sequence_listbox.see(index)
                
    def reset_sequence_highlight(self):
        """Сброс подсветки последовательности"""
        if hasattr(self, 'sequence_listbox'):
            self.sequence_listbox.selection_clear(0, tk.END)
            
    def select_sequence_item(self, index):
        """Выбор элемента последовательности"""
        if hasattr(self, 'sequence_listbox'):
            self.sequence_listbox.selection_clear(0, tk.END)
            if 0 <= index < self.sequence_listbox.size():
                self.sequence_listbox.selection_set(index)
        
    def get_settings(self):
        """Получение настроек из вкладки режимов"""
        return {
            "click_mode": self.click_mode.get(),
            "target_color": self.color_var.get(),
            "color_tolerance": self.app.color_tolerance_var.get(),
            "image_mode": self.image_click_mode.get(),
            "image_confidence": self.app.image_confidence_var.get(),
            "template_image": self.template_path_var.get(),
            "image_sequence_repeats": self.app.image_sequence_repeats_var.get(),
        }
        
    def apply_settings(self, settings):
        """Применение настроек к вкладке режимов"""
        try:
            self.click_mode.set(settings.get("click_mode", "normal"))
            self.color_var.set(settings.get("target_color", "#FF0000"))
            self.app.color_tolerance_var.set(settings.get("color_tolerance", DEFAULT_COLOR_TOLERANCE))
            self.image_click_mode.set(settings.get("image_mode", "single"))
            self.app.image_confidence_var.set(settings.get("image_confidence", DEFAULT_IMAGE_CONFIDENCE))
            self.template_path_var.set(settings.get("template_image", "Файл не выбран"))
            self.app.image_sequence_repeats_var.set(settings.get("image_sequence_repeats", 0))
            
            # Обновляем отображение цвета
            self.color_display.config(bg=self.color_var.get())
            
            # Обновляем режим
            self.mode_changed()
            
        except Exception as e:
            print(f"Ошибка применения настроек к вкладке режимов: {e}") 

    # Старые заглушечные методы удалены - используются правильные методы выше
            
    def _edit_sequence_text(self):
        """Открывает окно для текстового редактирования последовательности"""
        dialog = tk.Toplevel(self.app.gui.window)
        dialog.title("Редактирование последовательности")
        dialog.geometry("600x500")
        dialog.resizable(True, True)
        
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
C:\\\\images\\\\button.png клики=3
{space} нажатий=2
C:\\\\images\\\\icon.png клики=1
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
        for item in self.app.image_sequence:
            if item['type'] == 'capture' or item['type'] == 'file':
                current_text += f"{item['path']} клики={item['clicks']}\n"
            elif item['type'] == 'key':
                current_text += f"{{{item['key']}}} нажатий={item['presses']}\n"
        
        text_widget.insert(tk.END, current_text)
        
        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def apply_changes():
            """Применение изменений из текстового редактора"""
            try:
                text_content = text_widget.get("1.0", tk.END).strip()
                # Парсим текст и обновляем последовательность
                self._parse_sequence_text(text_content)
                dialog.destroy()
                messagebox.showinfo("Успех", "Последовательность обновлена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка парсинга: {e}")
        
        ttk.Button(button_frame, text="Применить", command=apply_changes).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT)
        
    def _parse_sequence_text(self, text_content):
        """Парсинг текста и обновление последовательности"""
        # Очищаем текущую последовательность
        self.clear_image_sequence()
        
        lines = text_content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            try:
                if line.startswith('{') and '}' in line:
                    # Парсим клавишу
                    key_end = line.find('}')
                    key = line[1:key_end]
                    if 'нажатий=' in line:
                        presses = int(line.split('нажатий=')[1])
                    else:
                        presses = 1
                    
                    key_item = {
                        'type': 'key',
                        'name': f"{key} (нажатий: {presses})",
                        'key': key,
                        'presses': presses
                    }
                    self.app.image_sequence.append(key_item)
                    
                elif 'клики=' in line:
                    # Парсим шаблон
                    parts = line.split(' клики=')
                    path = parts[0].strip()
                    clicks = int(parts[1])
                    
                    import os
                    template_item = {
                        'type': 'file' if os.path.exists(path) else 'capture',
                        'name': os.path.basename(path) if os.path.exists(path) else f"Шаблон {len(self.app.image_sequence)+1}",
                        'path': path,
                        'clicks': clicks
                    }
                    self.app.image_sequence.append(template_item)
                    
            except ValueError as e:
                print(f"Ошибка парсинга строки '{line}': {e}")
                
        # Обновляем отображение
        self.update_image_sequence_list()
        
    def _add_key_to_sequence(self):
        """Добавление клавиши в последовательность шаблонов"""
        key = self.sequence_key_var.get().strip()
        presses = self.sequence_key_presses_var.get()
        
        if not key:
            messagebox.showwarning("Ошибка", "Введите название клавиши")
            return
            
        # Добавляем в массив image_sequence как в оригинале
        key_item = {
            'type': 'key',
            'name': f"{key} (нажатий: {presses})",
            'key': key,
            'presses': presses
        }
        self.app.image_sequence.append(key_item)
        self.update_image_sequence_list()
        print(f"Клавиша добавлена в последовательность: {key_item['name']}")
        
    def _update_template_clicks(self):
        """Обновление количества кликов для выбранного шаблона"""
        selection = self.image_sequence_listbox.curselection()
        if selection:
            index = selection[0]
            clicks = self.template_clicks_var.get()
            
            # Обновляем в массиве image_sequence
            if index < len(self.app.image_sequence):
                item = self.app.image_sequence[index]
                if item['type'] != 'key':  # Только для шаблонов, не для клавиш
                    item['clicks'] = clicks
                    self.update_image_sequence_list()
                    messagebox.showinfo("Успех", f"Установлено {clicks} кликов для шаблона")
                else:
                    messagebox.showwarning("Ошибка", "Нельзя изменить количество кликов для клавиши")
            else:
                messagebox.showwarning("Ошибка", "Элемент не найден в последовательности")

    # Методы для управления последовательностью шаблонов (как в оригинале)
    def move_sequence_item_up(self):
        """Перемещает выбранный элемент последовательности вверх"""
        if hasattr(self, 'image_sequence_listbox'):
            selection = self.image_sequence_listbox.curselection()
            if selection and selection[0] > 0:
                index = selection[0]
                # Меняем местами элементы
                self.app.image_sequence[index], self.app.image_sequence[index-1] = self.app.image_sequence[index-1], self.app.image_sequence[index]
                self.update_image_sequence_list()
                # Выбираем перемещенный элемент
                self.image_sequence_listbox.selection_set(index-1)
                
    def move_sequence_item_down(self):
        """Перемещает выбранный элемент последовательности вниз"""
        if hasattr(self, 'image_sequence_listbox'):
            selection = self.image_sequence_listbox.curselection()
            if selection and selection[0] < len(self.app.image_sequence) - 1:
                index = selection[0]
                # Меняем местами элементы
                self.app.image_sequence[index], self.app.image_sequence[index+1] = self.app.image_sequence[index+1], self.app.image_sequence[index]
                self.update_image_sequence_list()
                # Выбираем перемещенный элемент
                self.image_sequence_listbox.selection_set(index+1)

    def update_image_sequence_list(self):
        """Обновление списка шаблонов в последовательности"""
        if hasattr(self, 'image_sequence_listbox'):
            self.image_sequence_listbox.delete(0, tk.END)
            for i, item in enumerate(self.app.image_sequence):
                if item['type'] == 'key':
                    text = f"{i+1}. {item['name']}"
                else:
                    text = f"{i+1}. {item['name']} - {item['clicks']} кликов"
                self.image_sequence_listbox.insert(tk.END, text)

    def remove_image_template(self):
        """Удаление выбранного шаблона из последовательности"""
        if hasattr(self, 'image_sequence_listbox'):
            selection = self.image_sequence_listbox.curselection()
            if selection:
                index = selection[0]
                item = self.app.image_sequence[index]
                
                # Удаляем временный файл если это захваченный шаблон
                if item['type'] == 'capture' and os.path.exists(item['path']):
                    try:
                        os.remove(item['path'])
                    except:
                        pass
                        
                del self.app.image_sequence[index]
                self.update_image_sequence_list()
                
    def clear_image_sequence(self):
        """Очистка всей последовательности шаблонов"""
        # Удаляем все временные файлы
        for item in self.app.image_sequence:
            if item['type'] == 'capture' and os.path.exists(item['path']):
                try:
                    os.remove(item['path'])
                except:
                    pass
        
        self.app.image_sequence.clear()
        self.update_image_sequence_list()

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

    def setup_sequence_key_capture(self):
        """Настройка перехвата клавиш для поля ввода клавиш в последовательности"""
        if hasattr(self, 'sequence_key_entry'):
            self.sequence_key_entry.bind('<Button-1>', self.on_sequence_key_click)
            self.sequence_key_entry.bind('<FocusIn>', self.on_sequence_key_focus_in)
            self.sequence_key_entry.bind('<FocusOut>', self.on_sequence_key_focus_out)
            self.sequence_key_entry.bind('<Key>', self.on_sequence_key_press) 

    def setup_keyboard_capture(self):
        """Настройка перехвата клавиш для поля ввода клавиш последовательности"""
        if hasattr(self, 'new_key_entry'):
            # Привязываем события к полю ввода клавиш
            self.new_key_entry.bind('<Button-1>', self.on_keyboard_click)
            self.new_key_entry.bind('<FocusIn>', self.on_keyboard_focus_in)
            self.new_key_entry.bind('<FocusOut>', self.on_keyboard_focus_out)
            self.new_key_entry.bind('<KeyPress>', self.on_keyboard_press)
            
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
        current_value = self.key_to_press.get()
        if current_value == '' or current_value == 'Нажмите клавишу...':
            self.key_to_press.set('Нажмите клавишу...')
        entry.select_range(0, tk.END)
            
    def on_keyboard_focus_out(self, event):
        """Когда поле ввода клавиш теряет фокус"""
        entry = event.widget
        entry.config(background='white', state='normal')
        
        # Если ничего не было установлено, очищаем поле
        if self.key_to_press.get() == 'Нажмите клавишу...':
            self.key_to_press.set('')
            
    def on_keyboard_press(self, event):
        """Обработка нажатия клавиши в поле ввода клавиш"""
        key_name = self.get_key_name(event)
        
        if key_name:
            self.key_to_press.set(key_name)
            # Убираем фокус с поля
            self.app.gui.window.focus()
            
        return 'break'  # Предотвращаем обычную обработку события

    def create_template_from_search_area_ui(self):
        """Создает шаблон из области поиска через UI"""
        if not self.app.search_area:
            messagebox.showwarning("Предупреждение", "Сначала выберите область поиска!")
            return
            
        # Используем template_capture для создания шаблона из области поиска
        def on_template_captured(template_info):
            """Callback для обработки созданного шаблона"""
            if template_info and template_info.get('path'):
                # Обновляем переменную template_path_var
                self.template_path_var.set(template_info.get('name', 'Шаблон из области'))
                messagebox.showinfo("Успех", f"Создан новый шаблон: {template_info.get('name')}")
            else:
                messagebox.showerror("Ошибка", "Не удалось создать шаблон из области поиска")
        
        # Запускаем создание шаблона из области поиска
        self.app.template_capture.capture_from_search_area(callback=on_template_captured)

    def update_keyboard_sequence_list(self):
        """Обновляет отображение списка клавиш в listbox"""
        if hasattr(self, 'keyboard_sequence_listbox'):
            self.keyboard_sequence_listbox.delete(0, tk.END)
            for entry in self.app.keyboard_sequence:
                text = f"{entry['key']} (x{entry['presses']})"
                self.keyboard_sequence_listbox.insert(tk.END, text) 

    def on_sequence_key_click(self, event):
        self.sequence_key_entry.config(state='readonly')
        self.sequence_key_entry.focus_set()
        return "break"

    def on_sequence_key_focus_in(self, event):
        if not self.sequence_key_var.get() or self.sequence_key_var.get() == "Нажмите клавишу...":
            self.sequence_key_var.set("")

    def on_sequence_key_focus_out(self, event):
        if not self.sequence_key_var.get():
            self.sequence_key_var.set("Нажмите клавишу...")
        self.sequence_key_entry.config(state='normal')

    def on_sequence_key_press(self, event):
        key_name = self.get_key_name(event)
        if key_name:
            self.sequence_key_var.set(key_name)
            self.sequence_key_entry.config(state='normal')
        return "break" 