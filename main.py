"""
OmniaClick - Автокликер Pro v1.0

Главный файл приложения, объединяющий все модули
Сохраняет полную функциональность оригинала с улучшенной архитектурой

"""

import tkinter as tk
from tkinter import messagebox
import sys
import os
import threading
import time

# Импорт конфигурации
from config import *

# Импорт core модулей
from core.clicker import ClickerEngine
from core.hotkeys import HotkeyManager
from core.color_detection import ColorDetector
from core.image_processing import ImageProcessor

# Импорт утилит
from utils.file_manager import FileManager
from utils.system_tray import SystemTrayManager
from utils.validation import ValidationHelper
from utils.overlay_manager import OverlayManager
from utils.area_selector import AreaSelector
from utils.color_picker import ColorPicker
from utils.template_capture import TemplateCapture
from utils.sequence_manager import SequenceManager
from utils.emergency_system import EmergencySystem
from utils.system_monitor import SystemMonitor

# Импорт GUI
from ui.main_window import MainWindow


class OmniaClickApp:
    """Главное приложение OmniaClick с полной функциональностью"""
    
    def __init__(self):
        # Основное окно
        self.window = tk.Tk()
        
        # Переменные состояния
        self.clicking = False
        self.current_mode = CLICK_MODES["NORMAL"]
        self.search_area = None
        
        # Переменные для последовательностей
        self.keyboard_sequence = []
        self.sequence_points = []
        self.image_sequence = []
        self.image_sequence_repeats_var = tk.IntVar(value=0)
        self.key_presses_var = tk.IntVar(value=1)  # Default to 1 click
        
        # Переменные настроек
        self.interval_var = tk.DoubleVar(value=DEFAULT_INTERVAL)
        self.click_type_var = tk.StringVar(value=DEFAULT_CLICK_TYPE)
        self.color_tolerance_var = tk.IntVar(value=DEFAULT_COLOR_TOLERANCE)
        self.image_confidence_var = tk.DoubleVar(value=DEFAULT_IMAGE_CONFIDENCE)
        self.turbo_mode_var = tk.BooleanVar(value=False)
        self.extreme_mode_var = tk.BooleanVar(value=False)
        
        # Инициализация компонентов
        self._init_components()
        self._init_gui()
        self._setup_event_handlers()
        self._setup_system()
        
    def _init_components(self):
        """Инициализация всех компонентов"""
        
        # Core компоненты
        self.clicker = ClickerEngine()
        self.hotkeys = HotkeyManager()
        self.color_detector = ColorDetector()
        self.image_processor = ImageProcessor()
        
        # Утилиты
        self.file_manager = FileManager()
        self.system_tray = SystemTrayManager()
        self.validation = ValidationHelper()
        
        # Новые модули
        self.overlay_manager = OverlayManager()
        self.area_selector = AreaSelector(self.overlay_manager)
        self.color_picker = ColorPicker()
        self.template_capture = TemplateCapture(self.overlay_manager)
        self.sequence_manager = SequenceManager()
        self.emergency_system = EmergencySystem()
        self.system_monitor = SystemMonitor()
        
    def _init_gui(self):
        """Инициализация GUI"""
        self.gui = MainWindow(self)
        
    def _setup_event_handlers(self):
        """Настройка обработчиков событий между компонентами"""
        
        # Callbacks для clicker
        self.clicker.set_callbacks(
            on_click=self._on_click_performed,
            on_status_change=self._on_clicker_status_change
        )
        
        # Callbacks для hotkeys
        self.hotkeys.set_callbacks(
            on_start=self.start_clicking,
            on_stop=self.stop_clicking,
            on_emergency_stop=self._emergency_stop
        )
        
        # Callbacks для color_detector
        self.color_detector.set_callbacks(
            on_found=self._on_color_click_success,
            on_not_found=self._on_color_click_failed
        )
        
        # Callbacks для image_processor  
        self.image_processor.set_callbacks(
            on_found=self._on_image_click_success,
            on_not_found=self._on_image_click_failed
        )
        
        # Callbacks для system_tray
        self.system_tray.set_callbacks(
            on_show=self._show_window,
            on_start=self.start_clicking,
            on_stop=self.stop_clicking,
            on_quit=self._on_quit
        )
        
        # Callbacks для overlay_manager
        self.overlay_manager.set_callbacks()
        
        # Callbacks для area_selector
        self.area_selector.set_callbacks(
            on_before_selection=self._before_area_selection,
            on_after_selection=self._after_area_selection,
            on_area_selected=self._on_area_selected,
            on_area_cleared=self._on_area_cleared,
            on_disable_hotkeys=self._disable_hotkeys_temporarily,
            on_enable_hotkeys=self._enable_hotkeys,
            on_show_message=self._show_gui_message
        )
        
        # Callbacks для color_picker
        self.color_picker.set_callbacks(
            on_color_picked=self._on_color_picked,
            on_disable_hotkeys=self._disable_hotkeys_temporarily,
            on_enable_hotkeys=self._enable_hotkeys,
            on_show_message=self._show_gui_message
        )
        
        # Callbacks для template_capture
        self.template_capture.set_callbacks(
            on_before_capture=self._before_template_capture,
            on_after_capture=self._after_template_capture,
            on_template_captured=self._on_template_captured,
            on_disable_hotkeys=self._disable_hotkeys_temporarily,
            on_enable_hotkeys=self._enable_hotkeys,
            on_show_message=self._show_gui_message
        )
        
        # Callbacks для sequence_manager
        self.sequence_manager.set_callbacks(
            on_sequence_updated=self._on_sequence_updated,
            on_sequence_advanced=self._on_sequence_advanced,
            on_sequence_completed=self._on_sequence_completed,
            on_sequence_reset=self._on_sequence_reset,
            on_item_moved=self._on_sequence_item_moved,
            on_disable_hotkeys=self._disable_hotkeys_temporarily,
            on_enable_hotkeys=self._enable_hotkeys,
            on_show_message=self._show_gui_message
        )
        
        # Callbacks для emergency_system
        self.emergency_system.set_callbacks(
            on_emergency_stop=self._emergency_stop,
            on_force_stop_all=self._force_stop_all,
            on_graceful_exit=self._graceful_exit
        )
        
        # Callbacks для system_monitor
        self.system_monitor.set_callbacks(
            on_user_activity=self._on_user_activity,
            on_mouse_activity=self._on_mouse_activity,
            on_window_change=self._on_window_change,
            on_idle_detected=self._on_idle_detected,
            on_activity_reset=self._on_activity_reset
        )
        
    def _setup_system(self):
        """Настройка системных компонентов"""
        # Настройка экстренной остановки
        self.emergency_system.setup()
        
        # Настройка мониторинга (опционально)
        if ENABLE_SYSTEM_MONITORING:
            self.system_monitor.start_monitoring()
            
        # Настройка горячих клавиш
        self.hotkeys.enable_hotkeys()
        
        # Настройка системного трея
        self.system_tray.setup_tray()
        
    # ====== Новые callback методы ======
    
    def _before_area_selection(self) -> bool:
        """Вызывается перед началом выбора области"""
        was_clicking = self.clicking
        if self.clicking:
            self.stop_clicking()
        return was_clicking
        
    def _after_area_selection(self):
        """Вызывается после завершения выбора области"""
        if hasattr(self, '_was_clicking_before_selection') and self._was_clicking_before_selection:
            self.start_clicking()
            
    def _on_area_selected(self, area: tuple, area_text: str):
        """Обработка выбранной области"""
        self.search_area = area
        self.color_detector.set_search_area(*area)  # Распаковываем tuple
        self.image_processor.set_search_area(*area)  # Распаковываем tuple
        
        if self.gui:
            self.gui.show_message("Область выбрана", area_text, "info")
            
    def _on_area_cleared(self):
        """Обработка очистки области"""
        self.search_area = None
        self.color_detector.clear_search_area()
        self.image_processor.clear_search_area()
        
    def _on_color_picked(self, color: str):
        """Обработка выбранного цвета"""
        self.color_detector.set_target_color(color)
        
        if self.gui:
            self.gui.apply_color_selection(color)
            
    def _before_template_capture(self) -> bool:
        """Вызывается перед захватом шаблона"""
        was_clicking = self.clicking
        if self.clicking:
            self.stop_clicking()
        return was_clicking
        
    def _after_template_capture(self):
        """Вызывается после захвата шаблона"""
        if hasattr(self, '_was_clicking_before_capture') and self._was_clicking_before_capture:
            self.start_clicking()
            
    def _on_template_captured(self, template_info: dict):
        """Обработка захваченного шаблона"""
        template_path = template_info['path']
        
        # Устанавливаем как текущий шаблон
        self.image_processor.set_current_template(template_path)
        
        if self.gui:
            self.gui.apply_template_selection(template_path, template_info['name'])
            
    def _on_sequence_updated(self, sequence: list):
        """Обработка обновления последовательности"""
        if self.gui:
            self.gui.update_sequence_display(sequence)
            
    def _on_sequence_advanced(self, current_index: int):
        """Обработка продвижения по последовательности"""
        if self.gui:
            self.gui.highlight_sequence_item(current_index)
            
    def _on_sequence_completed(self):
        """Обработка завершения последовательности"""
        if self.gui:
            self.gui.show_message("Последовательность", "Последовательность выполнена", "info")
            
    def _on_sequence_reset(self):
        """Обработка сброса последовательности"""
        if self.gui:
            self.gui.reset_sequence_highlight()
            
    def _on_sequence_item_moved(self, new_index: int):
        """Обработка перемещения элемента последовательности"""
        if self.gui:
            self.gui.select_sequence_item(new_index)
            
    def _on_user_activity(self, mouse_activity: bool, window_activity: bool):
        """Обработка активности пользователя"""
        # Уведомляем детекторы об активности
        if mouse_activity:
            self.color_detector.set_user_activity_detected(True)
            self.image_processor.set_user_activity_detected(True)
            
        # Опционально показываем в статусе
        if self.gui and (mouse_activity or window_activity):
            activity_type = []
            if mouse_activity:
                activity_type.append("мышь")
            if window_activity:
                activity_type.append("окно")
            self.gui.update_status(f"Активность: {', '.join(activity_type)}")
            
    def _on_mouse_activity(self, position: tuple, delta: tuple):
        """Обработка движения мыши"""
        pass  # Можно добавить логирование если нужно
        
    def _on_window_change(self, old_window, new_window, old_title: str, new_title: str):
        """Обработка смены активного окна"""
        if self.gui and SHOW_WINDOW_CHANGES:
            self.gui.update_status(f"Окно: {new_title[:30]}")
            
    def _on_idle_detected(self, idle_time: float):
        """Обработка бездействия"""
        pass  # Можно добавить автопаузу
        
    def _on_activity_reset(self):
        """Обработка сброса активности"""
        pass
        
    def _on_color_click_success(self, position: tuple):
        """Успешный клик по цвету"""
        if SHOW_SUCCESS_OVERLAY:
            self.overlay_manager.show_success_overlay(position[0], position[1])
            
    def _on_color_click_failed(self, reason: str):
        """Неудачный поиск цвета"""
        pass  # Можно добавить счетчик неудач
        
    def _on_image_click_success(self, position: tuple):
        """Успешный клик по изображению"""
        if SHOW_SUCCESS_OVERLAY:
            self.overlay_manager.show_success_overlay(position[0], position[1])
            
    def _on_image_click_failed(self, reason: str):
        """Неудачный поиск изображения"""
        pass  # Можно добавить счетчик неудач
        
    def _on_component_error(self, error_message: str):
        """Обработка ошибок компонентов"""
        if self.gui:
            self.gui.show_message("Ошибка", error_message, "error")
            
    def _disable_hotkeys_temporarily(self):
        """Временное отключение горячих клавиш"""
        self.hotkeys.temporarily_disable()
        
    def _enable_hotkeys(self):
        """Включение горячих клавиш"""
        self.hotkeys.re_enable()
        
    def _show_gui_message(self, title: str, message: str, message_type: str = "info"):
        """Показ сообщения через GUI"""
        if self.gui:
            self.gui.show_message(title, message, message_type)
        else:
            print(f"{title}: {message}")
            
    def _force_stop_all(self):
        """Принудительная остановка всех процессов"""
        self.clicking = False
        self.clicker.stop_clicking()
        self.hotkeys.disable_hotkeys()
        self.system_monitor.stop_monitoring()
        self.overlay_manager.hide_all_overlays()
        
    def _graceful_exit(self):
        """Корректный выход из приложения"""
        try:
            self._force_stop_all()
            self.cleanup_temp_files()
            if self.gui:
                self.gui.window.quit()
                self.gui.window.destroy()
        except Exception as e:
            print(f"Ошибка корректного выхода: {e}")
            
    # ====== Новые публичные методы ======
    
    def select_search_area(self):
        """Запуск интерактивного выбора области"""
        self.area_selector.select_search_area()
        
    def clear_search_area(self):
        """Очистка области поиска"""
        self.area_selector.clear_search_area()
        
    def pick_color(self):
        """Запуск пипетки для выбора цвета"""
        self.color_picker.pick_color()
        
    def capture_template(self):
        """Запуск захвата шаблона"""
        self.template_capture.capture_template()
        
    def open_sequence_editor(self):
        """Открытие редактора последовательности"""
        self.sequence_manager.open_text_editor(self.gui.window if self.gui else None)
        
    def move_sequence_item_up(self, index: int):
        """Перемещение элемента последовательности вверх"""
        return self.sequence_manager.move_item_up(index)
        
    def move_sequence_item_down(self, index: int):
        """Перемещение элемента последовательности вниз"""
        return self.sequence_manager.move_item_down(index)
        
    def trigger_emergency_stop(self):
        """Ручной запуск экстренной остановки"""
        self.emergency_system.trigger_emergency_stop()
            
    def start_clicking(self):
        """Запуск кликера"""
        try:
            if not self.clicking:
                # Применяем настройки к кликеру
                self.clicker.set_interval(self.interval_var.get())
                self.clicker.set_click_type(self.click_type_var.get())
                self.clicker.set_turbo_mode(self.turbo_mode_var.get())
                self.clicker.set_extreme_mode(self.extreme_mode_var.get())

                # Применяем настройки к детекторам
                self.color_detector.set_tolerance(self.color_tolerance_var.get())
                self.image_processor.set_confidence(self.image_confidence_var.get())

                # Устанавливаем текущий шаблон из GUI (если есть)
                if hasattr(self.gui, 'modes_tab') and hasattr(self.gui.modes_tab, 'template_path_var'):
                    template_path = self.gui.modes_tab.template_path_var.get()
                    if template_path and template_path != "Файл не выбран" and os.path.exists(template_path):
                        self.image_processor.set_current_template(template_path)

                # Передаём зависимости в ClickerEngine
                self.clicker.set_color_detector(self.color_detector)
                self.clicker.set_image_processor(self.image_processor)
                self.clicker.set_keyboard_sequence(self.keyboard_sequence)
                self.clicker.set_sequence_points(self.sequence_points)
                self.clicker.set_image_sequence(self.image_sequence)
                self.clicker.set_image_sequence_repeats(self.image_sequence_repeats_var.get())

                # Настраиваем режим клика
                if self.current_mode == CLICK_MODES["COLOR"]:
                    self.clicker.set_click_mode(CLICK_MODES["COLOR"])
                elif self.current_mode == CLICK_MODES["IMAGE"]:
                    self.clicker.set_click_mode(CLICK_MODES["IMAGE"])
                elif self.current_mode == CLICK_MODES["SEQUENCE"]:
                    self.clicker.set_click_mode(CLICK_MODES["SEQUENCE"])
                elif self.current_mode == CLICK_MODES["KEYBOARD"]:
                    self.clicker.set_click_mode(CLICK_MODES["KEYBOARD"])
                else:
                    self.clicker.set_click_mode(CLICK_MODES["NORMAL"])

                # Запускаем кликер
                self.clicking = True
                self.clicker.start_clicking()
                self.gui.set_buttons_state(True)

        except Exception as e:
            self.gui.show_message("Ошибка", f"Не удалось запустить кликер: {e}", "error")
            
    def stop_clicking(self):
        """Остановка кликера"""
        try:
            if self.clicking:
                self.clicking = False
                self.clicker.stop_clicking()
                self.gui.set_buttons_state(False)
                
        except Exception as e:
            self.gui.show_message("Ошибка", f"Не удалось остановить кликер: {e}", "error")
            
    def _perform_color_click(self) -> bool:
        """Выполнение клика по цвету"""
        return self.color_detector.find_and_click_color(self.click_type_var.get())
        
    def _perform_image_click(self) -> bool:
        """Выполнение клика по изображению"""
        return self.image_processor.find_and_click_image(click_type=self.click_type_var.get())
        
    def _perform_sequence_click(self) -> bool:
        """Выполнение клика по последовательности"""
        try:
            current_item = self.sequence_manager.get_current_item()
            if not current_item:
                return False
                
            success = False
            
            if current_item['type'] == 'template':
                # Кликаем по шаблону
                template_path = current_item['path']
                clicks = current_item.get('clicks', 1)
                
                for _ in range(clicks):
                    if self.image_processor.find_and_click_image(template_path, self.click_type_var.get()):
                        success = True
                    else:
                        break
                        
            elif current_item['type'] == 'key':
                # Нажимаем клавишу
                import pyautogui
                key = current_item['key']
                presses = current_item.get('presses', 1)
                
                for _ in range(presses):
                    pyautogui.press(key)
                    success = True
                    
            if success:
                # Переходим к следующему элементу
                self.sequence_manager.advance_sequence()
                
            return success
            
        except Exception as e:
            print(f"Ошибка выполнения последовательности: {e}")
            return False
            
    def _on_click_performed(self, click_count):
        """Обработчик выполненного клика"""
        self.gui.update_count(click_count)
        self.system_tray.update_status("running", click_count)
        
    def _on_clicker_status_change(self, status):
        """Обработчик изменения статуса кликера"""
        self.gui.update_status(status)
        self.system_tray.update_status(status, self.clicker.get_click_count())
        
    def _emergency_stop(self):
        """Экстренная остановка"""
        self.clicker.stop_clicking()
        self.gui.set_buttons_state(False)
        self.gui.show_message("Экстренная остановка", "Кликер принудительно остановлен!", "warning")
        
    def save_settings(self):
        """Сохранение настроек"""
        # Получаем настройки из GUI
        settings = self.gui.get_current_settings()
        
        # Добавляем системные настройки
        settings.update({
            "app_version": APP_VERSION,
            "click_count": self.clicker.get_click_count(),
            "search_area": self.search_area,
        })
        
        success, message = self.file_manager.save_settings(settings)
        if success:
            self.gui.show_message("Сохранение", message)
        else:
            self.gui.show_message("Ошибка", message, "error")
            
    def load_settings(self):
        """Загрузка настроек"""
        success, settings_data = self.file_manager.import_settings_dialog()
        if success and settings_data:
            try:
                # Применяем настройки к GUI
                if self.gui.apply_settings(settings_data):
                    # Применяем к компонентам
                    self.interval_var.set(settings_data.get("interval", DEFAULT_INTERVAL))
                    self.click_type_var.set(settings_data.get("click_type", DEFAULT_CLICK_TYPE))
                    self.color_tolerance_var.set(settings_data.get("color_tolerance", DEFAULT_COLOR_TOLERANCE))
                    self.image_confidence_var.set(settings_data.get("image_confidence", DEFAULT_IMAGE_CONFIDENCE))
                    self.turbo_mode_var.set(settings_data.get("turbo_mode", False))
                    self.extreme_mode_var.set(settings_data.get("extreme_mode", False))
                    
                    # Применяем к режиму
                    self.current_mode = settings_data.get("click_mode", CLICK_MODES["NORMAL"])
                    
                    # Восстанавливаем область поиска
                    self.search_area = settings_data.get("search_area")
                    
                    self.gui.show_message("Загрузка", "Настройки успешно применены!")
                else:
                    self.gui.show_message("Ошибка", "Не удалось применить настройки к интерфейсу", "error")
                    
            except Exception as e:
                self.gui.show_message("Ошибка", f"Не удалось применить настройки: {e}", "error")
                
    def cleanup_temp_files(self):
        """Очистка временных файлов"""
        count = self.file_manager.cleanup_temp_files()
        count += self.image_processor.cleanup_temp_files()
        self.gui.show_message("Очистка", f"Удалено временных файлов: {count}")
        
    def _show_window(self, icon=None, item=None):
        """Показ главного окна"""
        self.gui.show_from_tray()
        
    def _on_quit(self, icon=None, item=None):
        """Выход из приложения"""
        self._on_closing()
        
    def _on_closing(self):
        """Обработчик закрытия приложения"""
        # Останавливаем кликер
        self.clicker.stop_clicking()
        
        # Отключаем горячие клавиши
        self.hotkeys.disable_hotkeys()
        
        # Останавливаем трей
        self.system_tray.stop_tray()
        
        # Очищаем временные файлы
        self.file_manager.cleanup_temp_files()
        self.image_processor.cleanup_temp_files()
        
        # Закрываем приложение
        self.window.quit()
        self.window.destroy()
        
    def run(self):
        """Запуск главного цикла приложения"""
        try:
            self.window.mainloop()
        except KeyboardInterrupt:
            self._on_closing()
        except Exception as e:
            self.gui.show_message("Критическая ошибка", f"Неожиданная ошибка: {e}", "error")
            self._on_closing()

def main():
    """Главная функция запуска приложения"""
    try:
        # Проверяем что все зависимости импортированы
        print(f"Запуск {APP_TITLE}")
        print(f"OpenCV доступен: {OPENCV_AVAILABLE}")
        print(f"Win32 доступен: {WIN32_AVAILABLE}")
        print("✓ Все модули успешно загружены")
        print("✓ Новая архитектура активирована")
        print("=" * 50)
        
        # Создаем и запускаем приложение
        app = OmniaClickApp()
        app.run()
        
    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        messagebox.showerror("Ошибка зависимостей", 
                           f"Не удалось импортировать зависимости: {e}\n\n"
                           f"Убедитесь что установлены все библиотеки из requirements.txt")
    except Exception as e:
        print(f"Критическая ошибка при запуске: {e}")
        messagebox.showerror("Критическая ошибка", f"Не удалось запустить приложение: {e}")

if __name__ == "__main__":
    main() 