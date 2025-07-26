"""
Модуль для работы с файлами
Содержит FileManager класс для сохранения/загрузки настроек и управления файлами
"""

import json
import os
import uuid
from tkinter import filedialog, messagebox
from config import *

class FileManager:
    """Класс для работы с файлами и настройками"""
    
    def __init__(self):
        self.settings_file = SETTINGS_FILE
        
    def save_settings(self, settings_data, custom_path=None):
        """Сохранение настроек в JSON файл"""
        try:
            file_path = custom_path if custom_path else self.settings_file
            
            # Создаем резервную копию если файл существует
            if os.path.exists(file_path):
                backup_path = f"{file_path}.backup"
                try:
                    with open(file_path, 'r', encoding='utf-8') as src:
                        with open(backup_path, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
                except:
                    pass
                    
            # Сохраняем настройки
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=2)
                
            return True, f"Настройки сохранены в {file_path}"
            
        except Exception as e:
            return False, f"Ошибка при сохранении настроек: {e}"
            
    def load_settings(self, custom_path=None):
        """Загрузка настроек из JSON файла"""
        try:
            file_path = custom_path if custom_path else self.settings_file
            
            if not os.path.exists(file_path):
                return False, f"Файл настроек не найден: {file_path}", None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
                
            # Базовая валидация настроек
            if not isinstance(settings_data, dict):
                return False, "Неверный формат файла настроек", None
                
            return True, f"Настройки загружены из {file_path}", settings_data
            
        except json.JSONDecodeError as e:
            return False, f"Ошибка парсинга JSON: {e}", None
        except Exception as e:
            return False, f"Ошибка при загрузке настроек: {e}", None
            
    def export_settings_dialog(self, settings_data):
        """Диалог экспорта настроек"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Сохранить настройки как...",
                defaultextension=".json",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
                initialfilename="autoclicker_settings.json"
            )
            
            if file_path:
                success, message = self.save_settings(settings_data, file_path)
                if success:
                    messagebox.showinfo("Экспорт", message)
                else:
                    messagebox.showerror("Ошибка экспорта", message)
                return success
            return False
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте: {e}")
            return False
            
    def import_settings_dialog(self):
        """Диалог импорта настроек"""
        try:
            file_path = filedialog.askopenfilename(
                title="Загрузить настройки",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            
            if file_path:
                success, message, settings_data = self.load_settings(file_path)
                if success:
                    messagebox.showinfo("Импорт", message)
                    return True, settings_data
                else:
                    messagebox.showerror("Ошибка импорта", message)
                    return False, None
            return False, None
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при импорте: {e}")
            return False, None
            
    def select_image_file(self, title="Выберите изображение"):
        """Диалог выбора файла изображения"""
        try:
            file_path = filedialog.askopenfilename(
                title=title,
                filetypes=[
                    ("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif"),
                    ("PNG файлы", "*.png"),
                    ("JPEG файлы", "*.jpg *.jpeg"),
                    ("Все файлы", "*.*")
                ]
            )
            return file_path if file_path else None
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при выборе файла: {e}")
            return None
            
    def generate_temp_filename(self, extension=".png"):
        """Генерация имени временного файла"""
        return f"{TEMP_TEMPLATE_PREFIX}{uuid.uuid4().hex[:8]}{extension}"
        
    def cleanup_temp_files(self, directory="."):
        """Очистка временных файлов"""
        cleaned_count = 0
        try:
            for file in os.listdir(directory):
                if file.startswith(TEMP_TEMPLATE_PREFIX):
                    try:
                        file_path = os.path.join(directory, file)
                        os.remove(file_path)
                        cleaned_count += 1
                    except Exception as e:
                        print(f"Не удалось удалить {file}: {e}")
                        
            return cleaned_count
            
        except Exception as e:
            print(f"Ошибка при очистке временных файлов: {e}")
            return 0
            
    def validate_image_file(self, file_path):
        """Проверка валидности файла изображения"""
        if not file_path or not os.path.exists(file_path):
            return False, "Файл не найден"
            
        # Проверяем расширение
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in IMAGE_EXTENSIONS:
            return False, f"Неподдерживаемый формат файла: {ext}"
            
        # Проверяем размер файла
        try:
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                return False, "Файл слишком большой (максимум 10MB)"
            if file_size < 100:  # 100 bytes
                return False, "Файл слишком маленький"
                
            return True, "OK"
            
        except Exception as e:
            return False, f"Ошибка при проверке файла: {e}"
            
    def get_file_info(self, file_path):
        """Получение информации о файле"""
        try:
            if not os.path.exists(file_path):
                return None
                
            stat = os.stat(file_path)
            return {
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified': stat.st_mtime,
                'path': file_path,
                'extension': os.path.splitext(file_path)[1].lower()
            }
            
        except Exception as e:
            print(f"Ошибка при получении информации о файле {file_path}: {e}")
            return None
            
    def copy_file(self, src_path, dst_path):
        """Копирование файла"""
        try:
            with open(src_path, 'rb') as src:
                with open(dst_path, 'wb') as dst:
                    dst.write(src.read())
            return True
        except Exception as e:
            print(f"Ошибка при копировании файла: {e}")
            return False
            
    def create_settings_template(self):
        """Создание шаблона настроек"""
        return {
            "version": APP_VERSION,
            "created": "автоматически",
            "interval": DEFAULT_INTERVAL,
            "click_type": DEFAULT_CLICK_TYPE,
            "click_mode": CLICK_MODES["NORMAL"],
            "target_color": DEFAULT_COLOR,
            "color_tolerance": DEFAULT_COLOR_TOLERANCE,
            "image_confidence": DEFAULT_IMAGE_CONFIDENCE,
            "turbo_mode": False,
            "extreme_mode": False,
            "hotkey_start": DEFAULT_HOTKEY_START,
            "hotkey_stop": DEFAULT_HOTKEY_STOP,
            "sound_notifications": True,
            "pause_on_mouse": False,
            "pause_on_window": False,
            "always_on_top": False,
            "search_area": None,
            "sequence_points": [],
            "image_sequence": [],
            "keyboard_sequence": []
        } 