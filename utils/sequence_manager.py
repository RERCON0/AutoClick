"""
OmniaClick - Управление последовательностями

Система для управления последовательностями действий (шаблоны + клавиши)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from typing import List, Dict, Optional, Callable

from config import *


class SequenceManager:
    """Менеджер последовательностей действий"""
    
    def __init__(self):
        # Последовательность действий
        self.sequence: List[Dict] = []
        self.current_index = 0
        self.sequence_repeat_count = 0
        self.sequence_repeats = 1
        
        # Коллбэки
        self.callbacks = {}
        
    def set_callbacks(self, **callbacks):
        """Установка коллбэков"""
        self.callbacks.update(callbacks)
        
    def add_template(self, template_path: str, clicks: int = 1) -> bool:
        """Добавление шаблона в последовательность"""
        try:
            if not os.path.exists(template_path):
                return False
                
            template_entry = {
                "type": "template",
                "path": template_path,
                "clicks": clicks,
                "name": f"Шаблон: {os.path.basename(template_path)} (x{clicks})"
            }
            
            self.sequence.append(template_entry)
            
            if 'on_sequence_updated' in self.callbacks:
                self.callbacks['on_sequence_updated'](self.sequence)
                
            return True
            
        except Exception as e:
            print(f"Ошибка добавления шаблона: {e}")
            return False
            
    def add_key(self, key: str, presses: int = 1) -> bool:
        """Добавление клавиши в последовательность"""
        try:
            if not key.strip():
                return False
                
            key_entry = {
                "type": "key",
                "key": key.strip(),
                "presses": presses,
                "name": f"Клавиша: {key} (x{presses})"
            }
            
            self.sequence.append(key_entry)
            
            if 'on_sequence_updated' in self.callbacks:
                self.callbacks['on_sequence_updated'](self.sequence)
                
            return True
            
        except Exception as e:
            print(f"Ошибка добавления клавиши: {e}")
            return False
            
    def remove_item(self, index: int) -> bool:
        """Удаление элемента из последовательности"""
        try:
            if 0 <= index < len(self.sequence):
                removed_item = self.sequence.pop(index)
                
                if 'on_sequence_updated' in self.callbacks:
                    self.callbacks['on_sequence_updated'](self.sequence)
                    
                print(f"Удален элемент: {removed_item['name']}")
                return True
            return False
            
        except Exception as e:
            print(f"Ошибка удаления элемента: {e}")
            return False
            
    def move_item_up(self, index: int) -> bool:
        """Перемещение элемента вверх по списку"""
        try:
            if 0 < index < len(self.sequence):
                # Меняем местами элементы
                self.sequence[index], self.sequence[index-1] = self.sequence[index-1], self.sequence[index]
                
                if 'on_sequence_updated' in self.callbacks:
                    self.callbacks['on_sequence_updated'](self.sequence)
                    
                if 'on_item_moved' in self.callbacks:
                    self.callbacks['on_item_moved'](index-1)  # Новый индекс
                    
                return True
            return False
            
        except Exception as e:
            print(f"Ошибка перемещения элемента вверх: {e}")
            return False
            
    def move_item_down(self, index: int) -> bool:
        """Перемещение элемента вниз по списку"""
        try:
            if 0 <= index < len(self.sequence) - 1:
                # Меняем местами элементы
                self.sequence[index], self.sequence[index+1] = self.sequence[index+1], self.sequence[index]
                
                if 'on_sequence_updated' in self.callbacks:
                    self.callbacks['on_sequence_updated'](self.sequence)
                    
                if 'on_item_moved' in self.callbacks:
                    self.callbacks['on_item_moved'](index+1)  # Новый индекс
                    
                return True
            return False
            
        except Exception as e:
            print(f"Ошибка перемещения элемента вниз: {e}")
            return False
            
    def clear_sequence(self):
        """Очистка последовательности"""
        self.sequence.clear()
        self.current_index = 0
        self.sequence_repeat_count = 0
        
        if 'on_sequence_updated' in self.callbacks:
            self.callbacks['on_sequence_updated'](self.sequence)
            
    def get_current_item(self) -> Optional[Dict]:
        """Получение текущего элемента последовательности"""
        if 0 <= self.current_index < len(self.sequence):
            return self.sequence[self.current_index]
        return None
        
    def advance_sequence(self) -> bool:
        """Переход к следующему элементу последовательности"""
        if not self.sequence:
            return False
            
        self.current_index += 1
        
        # Проверяем достижение конца последовательности
        if self.current_index >= len(self.sequence):
            self.current_index = 0
            self.sequence_repeat_count += 1
            
            # Проверяем лимит повторений
            if self.sequence_repeats > 0 and self.sequence_repeat_count >= self.sequence_repeats:
                self.reset_sequence()
                if 'on_sequence_completed' in self.callbacks:
                    self.callbacks['on_sequence_completed']()
                return False
                
        if 'on_sequence_advanced' in self.callbacks:
            self.callbacks['on_sequence_advanced'](self.current_index)
            
        return True
        
    def reset_sequence(self):
        """Сброс последовательности к началу"""
        self.current_index = 0
        self.sequence_repeat_count = 0
        
        if 'on_sequence_reset' in self.callbacks:
            self.callbacks['on_sequence_reset']()
            
    def set_repeats(self, repeats: int):
        """Установка количества повторений (0 = бесконечно)"""
        self.sequence_repeats = max(0, repeats)
        
    def get_sequence_info(self) -> Dict:
        """Получение информации о последовательности"""
        return {
            "total_items": len(self.sequence),
            "current_index": self.current_index,
            "current_repeat": self.sequence_repeat_count,
            "total_repeats": self.sequence_repeats,
            "items": self.sequence.copy()
        }
        
    def load_from_text(self, text: str) -> bool:
        """
        Загрузка последовательности из текста
        
        Формат:
        - Шаблон: [путь_к_файлу] клики=N
        - Клавиша: {клавиша} нажатий=N
        """
        try:
            lines = text.strip().split('\n')
            new_sequence = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):  # Пропускаем пустые строки и комментарии
                    continue
                    
                # Обработка шаблонов
                if ' клики=' in line:
                    parts = line.split(' клики=')
                    if len(parts) == 2:
                        template_path = parts[0].strip()
                        try:
                            clicks = int(parts[1].strip())
                            if os.path.exists(template_path):
                                new_sequence.append({
                                    "type": "template",
                                    "path": template_path,
                                    "clicks": clicks,
                                    "name": f"Шаблон: {os.path.basename(template_path)} (x{clicks})"
                                })
                            else:
                                print(f"Файл не найден: {template_path}")
                        except ValueError:
                            print(f"Некорректное количество кликов: {parts[1]}")
                            
                # Обработка клавиш
                elif line.startswith('{') and '}' in line and ' нажатий=' in line:
                    key_end = line.find('}')
                    if key_end > 1:
                        key = line[1:key_end]
                        rest = line[key_end+1:].strip()
                        if rest.startswith(' нажатий='):
                            try:
                                presses = int(rest.split('=')[1].strip())
                                new_sequence.append({
                                    "type": "key",
                                    "key": key,
                                    "presses": presses,
                                    "name": f"Клавиша: {key} (x{presses})"
                                })
                            except ValueError:
                                print(f"Некорректное количество нажатий: {rest}")
                                
            # Заменяем текущую последовательность
            self.sequence = new_sequence
            self.reset_sequence()
            
            if 'on_sequence_updated' in self.callbacks:
                self.callbacks['on_sequence_updated'](self.sequence)
                
            return True
            
        except Exception as e:
            print(f"Ошибка загрузки последовательности из текста: {e}")
            return False
            
    def export_to_text(self) -> str:
        """Экспорт последовательности в текст"""
        try:
            lines = []
            lines.append("# Последовательность OmniaClick")
            lines.append("# Формат:")
            lines.append("# - Шаблон: [путь_к_файлу] клики=N")
            lines.append("# - Клавиша: {клавиша} нажатий=N")
            lines.append("")
            
            for item in self.sequence:
                if item['type'] == 'template':
                    lines.append(f"{item['path']} клики={item['clicks']}")
                elif item['type'] == 'key':
                    lines.append(f"{{{item['key']}}} нажатий={item['presses']}")
                    
            return '\n'.join(lines)
            
        except Exception as e:
            print(f"Ошибка экспорта последовательности: {e}")
            return ""
            
    def open_text_editor(self, parent_window=None):
        """Открытие текстового редактора последовательности"""
        try:
            # Отключаем глобальные горячие клавиши программы
            if 'on_disable_hotkeys' in self.callbacks:
                self.callbacks['on_disable_hotkeys']()
            
            dialog = tk.Toplevel(parent_window)
            dialog.title("Редактирование последовательности")
            dialog.geometry("600x500")
            dialog.resizable(True, True)
            if parent_window:
                dialog.transient(parent_window)
            dialog.grab_set()
            
            # Восстанавливаем горячие клавиши при закрытии окна
            def on_dialog_closing():
                if 'on_enable_hotkeys' in self.callbacks:
                    self.callbacks['on_enable_hotkeys']()
                dialog.destroy()
                
            dialog.protocol("WM_DELETE_WINDOW", on_dialog_closing)
            
            # Центрируем окно
            dialog.update_idletasks()
            if parent_window:
                x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - (dialog.winfo_width() // 2)
                y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - (dialog.winfo_height() // 2)
            else:
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
            
            inst_label = ttk.Label(text_frame, text=instructions, 
                                 justify=tk.LEFT, font=('Consolas', 9))
            inst_label.pack(anchor=tk.W, pady=(0, 10))
            
            # Текстовое поле с прокруткой
            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Заполняем текущей последовательностью
            current_text = self.export_to_text()
            text_widget.insert(tk.END, current_text)
            
            # Кнопки
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            def apply_changes():
                new_text = text_widget.get('1.0', tk.END)
                if self.load_from_text(new_text):
                    if 'on_show_message' in self.callbacks:
                        self.callbacks['on_show_message'](
                            "Успех", 
                            "Последовательность успешно обновлена!",
                            "info"
                        )
                    on_dialog_closing()
                else:
                    if 'on_show_message' in self.callbacks:
                        self.callbacks['on_show_message'](
                            "Ошибка", 
                            "Ошибка при загрузке последовательности. Проверьте формат.",
                            "error"
                        )
                        
            ttk.Button(btn_frame, text="Применить", command=apply_changes).pack(side=tk.RIGHT, padx=(5, 0))
            ttk.Button(btn_frame, text="Отмена", command=on_dialog_closing).pack(side=tk.RIGHT)
            
        except Exception as e:
            print(f"Ошибка открытия текстового редактора: {e}")
            if 'on_show_message' in self.callbacks:
                self.callbacks['on_show_message'](
                    "Ошибка", 
                    f"Ошибка открытия редактора: {e}",
                    "error"
                ) 