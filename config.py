"""
Конфигурационный файл для OmniaClick
Содержит все константы, настройки по умолчанию и конфигурацию приложения
"""

import os

# Режимы кликов
CLICK_MODES = {
    "NORMAL": "normal",
    "COLOR": "color", 
    "IMAGE": "image",
    "KEYBOARD": "keyboard",
    "SEQUENCE": "sequence"
}

# Настройки по умолчанию
DEFAULT_INTERVAL = 0.1
DEFAULT_CLICK_TYPE = "left"
DEFAULT_COLOR = "#FF0000"
DEFAULT_TARGET_COLOR = "#FF0000"  # Цвет по умолчанию для поиска
DEFAULT_COLOR_TOLERANCE = 10
DEFAULT_IMAGE_CONFIDENCE = 0.8
DEFAULT_RECHECK_INTERVAL = 50  # Интервал перепроверки кэша поиска

# Интервалы для режимов
TURBO_INTERVAL = 0.001     # Турбо режим
EXTREME_INTERVAL = 0.0001  # Экстремальный режим

# Настройки оверлеев
OVERLAY_COLORS = {
    "SELECTION": "blue",    # Цвет динамического выбора
    "AREA": "red",         # Цвет выбранной области
    "SUCCESS": "green"     # Цвет успешного действия
}
OVERLAY_WIDTH = 2
OVERLAY_ALPHA = 0.3

# Настройки мониторинга
ENABLE_SYSTEM_MONITORING = True
SHOW_WINDOW_CHANGES = False  # Показывать смену окон в статусе
SHOW_SUCCESS_OVERLAY = True  # Показывать оверлеи успешных кликов
USER_PAUSE_TIMEOUT = 2.0   # Таймаут паузы после активности пользователя
MONITOR_THREAD_DELAY = 0.1 # Задержка потока мониторинга

# Временные файлы
TEMP_TEMPLATE_PREFIX = "temp_template_"

# Проверка доступности зависимостей
try:
    import win32api
    import win32gui
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("win32api недоступен - некоторые функции будут ограничены")

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("OpenCV недоступен - поиск изображений будет менее точным")

# Настройки GUI
APP_NAME = "OmniaClick"
APP_TITLE = "OmniaClick - Автокликер Pro v1.0"
APP_VERSION = "2.0.0"
WINDOW_GEOMETRY = "900x1000"

# Горячие клавиши по умолчанию
DEFAULT_HOTKEY_START = "f6"
DEFAULT_HOTKEY_STOP = "f7"
EMERGENCY_STOP_KEY = "ctrl+alt+x"  # Экстренная остановка

# Настройки системного трея
TRAY_TITLE = "OmniaClick"
TRAY_ICON_SIZE = (16, 16)

# Сообщения
MESSAGES = {
    "APP_STARTED": "OmniaClick запущен",
    "APP_STOPPED": "OmniaClick остановлен", 
    "CLICKING_STARTED": "Автоклик запущен",
    "CLICKING_STOPPED": "Автоклик остановлен",
    "EMERGENCY_STOP": "Экстренная остановка активирована!",
    "AREA_SELECTED": "Область поиска выбрана",
    "COLOR_PICKED": "Цвет выбран для поиска",
    "TEMPLATE_CAPTURED": "Шаблон захвачен"
}

# Пути файлов
SETTINGS_FILE = "omnia_settings.json"
LOG_FILE = "omnia_log.txt"

# Лимиты
MAX_CLICK_INTERVAL = 10.0
MIN_CLICK_INTERVAL = 0.001
MAX_SEQUENCE_ITEMS = 100
MAX_TEMP_FILES = 50

# Дополнительные лимиты и константы
MIN_INTERVAL = MIN_CLICK_INTERVAL
MAX_INTERVAL = MAX_CLICK_INTERVAL

# Поддерживаемые типы кликов
CLICK_TYPES = ["left", "right", "middle"]

# Поддерживаемые расширения изображений
IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"]

# Шрифты для GUI
FONT_MAIN = ("Arial", 12)
FONT_TITLE = ("Arial", 16, "bold") 
FONT_SMALL = ("Arial", 8)
FONT_NORMAL = ("Arial", 10)

# Цвета для интерфейса
COLORS = {
    "SUCCESS": "green",
    "ERROR": "red", 
    "WARNING": "orange",
    "INFO": "blue",
    "GRAY": "gray"
}

# Валидация
VALIDATION = {
    "MAX_SEQUENCE_POINTS": 50,
    "MAX_IMAGE_SEQUENCE": 20,
    "MAX_KEYBOARD_SEQUENCE": 10,
    "MAX_KEY_PRESSES": 100
} 