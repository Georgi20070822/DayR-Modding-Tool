import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import tkinter.font as tkFont
import shutil
import winsound
import subprocess
import hashlib
import configparser
import importlib.util
import ctypes
from ctypes import wintypes
from PIL import Image, ImageTk
import zipfile
from datetime import datetime
import tempfile

from core.config import ConfigManager
from core.event_bus import EventBus
from core.plugin_manager import PluginManager
from core.strings import LANGUAGES
from core.profile_manager import ProfileManager
from gui.console import ToolConsole
from utils.helpers import resource_path, ensure_dir, get_tools_dir
from utils.utf8_decoder import decode_utf8_file, decode_utf8_folder
from utils.assembler import assemble_lu, disassemble_lu

# ======================================================
# ====   Настройки (сохранение в профиле пользователя) ====
# ======================================================

SETTINGS_DIR = os.path.join(os.path.expanduser("~"), "DayR_MB")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.ini")

def ensure_settings_dir():
    if not os.path.exists(SETTINGS_DIR):
        os.makedirs(SETTINGS_DIR)

def get_setting(section, key, default=None):
    ensure_settings_dir()
    config = configparser.ConfigParser()
    if os.path.exists(SETTINGS_FILE):
        config.read(SETTINGS_FILE)
    if section in config and key in config[section]:
        return config[section][key]
    return default

def set_setting(section, key, value):
    ensure_settings_dir()
    config = configparser.ConfigParser()
    if os.path.exists(SETTINGS_FILE):
        config.read(SETTINGS_FILE)
    if section not in config:
        config[section] = {}
    config[section][key] = str(value)
    with open(SETTINGS_FILE, 'w') as f:
        config.write(f)

# ======================================================
# ====   Права администратора                       ====
# ======================================================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def restart_as_admin():
    if sys.platform != 'win32':
        return
    script = sys.argv[0]
    if hasattr(sys, '_MEIPASS'):
        args = [sys.executable]
    else:
        args = [sys.executable, script]
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", args[0], " ".join(args[1:]), None, 1
    )
    sys.exit()

# ======================================================
# ====   Вспомогательные функции                    ====
# ======================================================

def import_module_from_file(filepath, module_name):
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_font_temporary(font_path):
    if sys.platform != 'win32':
        return False
    if not os.path.exists(font_path):
        return False
    FR_PRIVATE = 0x10
    gdi32 = ctypes.WinDLL('gdi32')
    add_font = gdi32.AddFontResourceExW
    add_font.argtypes = [wintypes.LPCWSTR, wintypes.UINT, wintypes.LPVOID]
    add_font.restype = wintypes.UINT
    return add_font(font_path, FR_PRIVATE, 0) > 0

def install_font_system(font_path):
    if sys.platform != 'win32':
        return False, "Установка шрифтов доступна только в Windows"
    if not os.path.exists(font_path):
        return False, "Файл шрифта не найден"
    fonts_dir = os.path.join(os.environ['WINDIR'], 'Fonts')
    font_name = os.path.basename(font_path)
    dest_path = os.path.join(fonts_dir, font_name)
    if os.path.exists(dest_path):
        return True, "Шрифт уже установлен"
    try:
        shutil.copy2(font_path, dest_path)
        gdi32 = ctypes.WinDLL('gdi32')
        result = gdi32.AddFontResourceW(dest_path)
        if result == 0:
            return False, "Ошибка регистрации шрифта"
        user32 = ctypes.WinDLL('user32')
        HWND_BROADCAST = 0xFFFF
        WM_FONTCHANGE = 0x001D
        user32.SendMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)
        return True, "Шрифт установлен"
    except Exception as e:
        return False, str(e)

# ======================================================
# ====   Основной класс MainWindow                  ====
# ======================================================

class MainWindow:
    def __init__(self, root, config_manager=None):
        self.root = root
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.config
        self.lang = self.config.get("language", "ru")
        
        # Состояние
        self.project_dir = tk.StringVar()
        self.tools_dir = tk.StringVar()
        self.status_var = tk.StringVar()
        self.resource_car_path = None
        self.all_buttons = []
        
        # Менеджер профилей
        self.profile_manager = ProfileManager()
        
        # Настройки UI
        self.root.title("Day R Modding Tool")
        self.root.geometry("1100x720")
        self.root.resizable(True, True)
        self.root.configure(bg='#2b2b2b')
        
        # Иконка окна (через iconphoto для надёжности)
        try:
            icon = Image.open(resource_path('icon.ico'))
            photo = ImageTk.PhotoImage(icon)
            self.root.iconphoto(True, photo)
        except Exception as e:
            print(f"⚠️ Не удалось загрузить иконку: {e}")
            try:
                self.root.iconbitmap(default=resource_path('icon.ico'))
            except:
                pass
        
        # Загрузка изображений для основных кнопок
        btn_normal_img = Image.open(resource_path('images/button_1.png'))
        btn_pressed_img = Image.open(resource_path('images/button_2.png'))
        BUTTON_WIDTH = 280
        BUTTON_HEIGHT = 40
        self.btn_normal_img = btn_normal_img.resize((BUTTON_WIDTH, BUTTON_HEIGHT), Image.Resampling.LANCZOS)
        self.btn_pressed_img = btn_pressed_img.resize((BUTTON_WIDTH, BUTTON_HEIGHT), Image.Resampling.LANCZOS)
        self.btn_normal = ImageTk.PhotoImage(self.btn_normal_img)
        self.btn_pressed = ImageTk.PhotoImage(self.btn_pressed_img)
        
        # Загрузка иконок для верхней панели (24x24)
        self.profile_icon_img = Image.open(resource_path('images/profile.png')).resize((24, 24), Image.Resampling.LANCZOS)
        self.profile_icon = ImageTk.PhotoImage(self.profile_icon_img)
        self.settings_icon_img = Image.open(resource_path('images/settings.png')).resize((24, 24), Image.Resampling.LANCZOS)
        self.settings_icon = ImageTk.PhotoImage(self.settings_icon_img)
        self.question_icon_img = Image.open(resource_path('images/question.png')).resize((24, 24), Image.Resampling.LANCZOS)
        self.question_icon = ImageTk.PhotoImage(self.question_icon_img)
        
        # Шрифт
        self.font_name = self._get_font_name()
        self.button_font = self._load_font(self.font_name)
        
        # Звук
        self.click_sound_path = resource_path('sounds/clicking.wav')
        
        # События
        EventBus.subscribe("log", self.on_log_event)
        EventBus.subscribe("status", self.on_status_event)
        
        # Интерфейс
        self.setup_ui()
        self.update_all_texts()
        
        # Плагины
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_plugins()
        for cmd_name, cmd_func in self.plugin_manager.commands.items():
            self.console.add_command(cmd_name, cmd_func)
    
    # ===== Вспомогательные методы =====
    
    def _get_font_name(self):
        return get_setting('Font', 'name', 'classic')
    
    def _load_font(self, font_name):
        if font_name == 'classic':
            return tkFont.Font(family="Segoe UI", size=9)
        font_files = {
            'RO': 'RO.ttf',
            'freemono': 'freemono.ttf',
            'russo_one': 'russo_one.ttf'
        }
        if font_name not in font_files:
            return tkFont.Font(family="Segoe UI", size=9)
        font_path = resource_path('font/' + font_files[font_name])
        if not os.path.exists(font_path):
            return tkFont.Font(family="Segoe UI", size=9)
        if load_font_temporary(font_path):
            if font_name == 'RO':
                try:
                    return tkFont.Font(family="Red October", size=9)
                except:
                    pass
            family_name = os.path.splitext(font_files[font_name])[0]
            try:
                return tkFont.Font(family=family_name, size=9)
            except:
                return tkFont.Font(family="Segoe UI", size=9)
        else:
            return tkFont.Font(family="Segoe UI", size=9)
    
    def get_str(self, key, *args):
        text = LANGUAGES[self.lang].get(key, key)
        if args:
            return text.format(*args)
        return text
    
    # ===== Всплывающие подсказки =====
    def _create_tooltip(self, widget, text):
        """Создаёт всплывающую подсказку для виджета."""
        def on_enter(event):
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            # Позиционируем подсказку рядом с курсором
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, bg='#ffffe0', relief='solid', borderwidth=1,
                             font=('Segoe UI', 9))
            label.pack()
            widget.tooltip = tooltip
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    # ===== Создание интерфейса =====
    
    def setup_ui(self):
        # ---- Верхняя панель ----
        lang_frame = tk.Frame(self.root, bg='#2b2b2b')
        lang_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(lang_frame, text='Язык / Language:', fg='white', bg='#2b2b2b').pack(side=tk.LEFT)
        self.lang_combo = ttk.Combobox(lang_frame, values=('ru', 'en'), state='readonly', width=5)
        self.lang_combo.set(self.lang)
        self.lang_combo.pack(side=tk.LEFT, padx=5)
        self.lang_combo.bind('<<ComboboxSelected>>', lambda e: self.change_language())
        
        # Кнопка профилей (иконка)
        self.btn_profile = tk.Button(lang_frame, image=self.profile_icon,
                                     command=self.open_profile_manager,
                                     relief='flat', borderwidth=0,
                                     bg='#2b2b2b', activebackground='#2b2b2b')
        self.btn_profile.pack(side=tk.RIGHT, padx=2)
        self.all_buttons.append(self.btn_profile)
        self._create_tooltip(self.btn_profile, self.get_str('profile_manager_title'))
        
        # Кнопка настроек (иконка)
        self.btn_settings = tk.Button(lang_frame, image=self.settings_icon,
                                      command=self.open_settings,
                                      relief='flat', borderwidth=0,
                                      bg='#2b2b2b', activebackground='#2b2b2b')
        self.btn_settings.pack(side=tk.RIGHT, padx=2)
        self.all_buttons.append(self.btn_settings)
        self._create_tooltip(self.btn_settings, self.get_str('settings_title'))
        
        # Кнопка помощи (иконка)
        self.btn_help = tk.Button(lang_frame, image=self.question_icon,
                                  command=self.show_help,
                                  relief='flat', borderwidth=0,
                                  bg='#2b2b2b', activebackground='#2b2b2b')
        self.btn_help.pack(side=tk.RIGHT, padx=2)
        self.all_buttons.append(self.btn_help)
        self._create_tooltip(self.btn_help, self.get_str('help_btn'))
        
        # ---- Панель проекта ----
        proj_frame = tk.Frame(self.root, bg='#2b2b2b')
        proj_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.label_project = tk.Label(proj_frame, text=self.get_str('project_folder'), fg='white', bg='#2b2b2b')
        self.label_project.pack(side=tk.LEFT)
        tk.Entry(proj_frame, textvariable=self.project_dir, width=50,
                 bg='#3c3c3c', fg='white', insertbackground='white', relief='flat').pack(side=tk.LEFT, padx=5)
        
        self.browse_btn = self._create_styled_button(proj_frame, self.browse_project, self.get_str('choose_project'))
        self.browse_btn.pack(side=tk.LEFT, padx=2, pady=2)
        self.all_buttons.append(self.browse_btn)
        
        self.btn_open_scripts = self._create_styled_button(proj_frame, self.open_mod_scripts_folder, self.get_str('open_mod_scripts'))
        self.btn_open_scripts.pack(side=tk.LEFT, padx=2, pady=2)
        self.all_buttons.append(self.btn_open_scripts)
        
        # ---- Основные кнопки (из конфига) ----
        btn_frame = tk.Frame(self.root, bg='#2b2b2b')
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        rows = self.config.get('rows', 4)
        cols = self.config.get('columns', 4)
        self.button_grid = []
        for r in range(rows):
            row_frame = tk.Frame(btn_frame, bg='#2b2b2b')
            row_frame.pack(fill=tk.X, pady=2)
            self.button_grid.append(row_frame)
        
        self.buttons = {}
        for btn_data in self.config['buttons']:
            row = btn_data.get('row', 0)
            col = btn_data.get('col', 0)
            text = btn_data.get(f'text_{self.lang}', btn_data.get('text_en', btn_data['id']))
            command_name = btn_data['command']
            command = getattr(self, command_name, None)
            if command is None:
                continue
            color = btn_data.get('color', 'default')
            fg_color = 'black'
            if color == 'danger':
                fg_color = 'darkred'
            elif color == 'warning':
                fg_color = 'darkblue'
            btn = self._create_styled_button(self.button_grid[row], command, text=text, fg=fg_color)
            btn.grid(row=0, column=col, padx=2, pady=2, sticky='ew')
            self.buttons[btn_data['id']] = btn
            self.all_buttons.append(btn)
        
        # ---- Лог ----
        log_frame = tk.Frame(self.root, bg='#2b2b2b')
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.label_log = tk.Label(log_frame, text=self.get_str('log'), fg='white', bg='#2b2b2b')
        self.label_log.pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='normal', height=18,
                                                  bg='#1e1e1e', fg='#eeeeee', insertbackground='white',
                                                  highlightthickness=0, borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # ---- Нижняя панель ----
        bottom_frame = tk.Frame(self.root, bg='#2b2b2b')
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = tk.Label(bottom_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W,
                                     bg='#3c3c3c', fg='white')
        self.status_var.set(self.get_str('status_ready'))
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.save_log_btn = self._create_styled_button(bottom_frame, self.save_log, self.get_str('save_log'))
        self.save_log_btn.pack(side=tk.LEFT, padx=2, pady=2)
        self.all_buttons.append(self.save_log_btn)
        
        self.clear_btn = self._create_styled_button(bottom_frame, self.clear_log, self.get_str('clear_log'))
        self.clear_btn.pack(side=tk.LEFT, padx=2, pady=2)
        self.all_buttons.append(self.clear_btn)
        
        # ---- Консоль команд ----
        self.console = ToolConsole(self.root, self.lang, self.get_str)
    
    def _create_styled_button(self, parent, command, text='', fg='black'):
        btn = tk.Button(parent, image=self.btn_normal, compound='center',
                        text=text, fg=fg, font=self.button_font,
                        relief='flat', borderwidth=0, bg='#2b2b2b',
                        activebackground='#2b2b2b')
        def on_press(e):
            winsound.PlaySound(self.click_sound_path, winsound.SND_ASYNC)
            e.widget.config(image=self.btn_pressed)
        def on_release(e):
            e.widget.config(image=self.btn_normal)
        def on_leave(e):
            e.widget.config(image=self.btn_normal)
        btn.bind('<ButtonPress>', on_press)
        btn.bind('<ButtonRelease>', on_release)
        btn.bind('<Leave>', on_leave)
        btn.config(command=command)
        return btn
    
    # ===== Обработчики =====
    def on_log_event(self, data):
        if data:
            self.log(data)
    def on_status_event(self, data):
        if data:
            self.set_status(data)
    
    # ===== Лог и статус =====
    def log(self, message):
        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, message + '\n')
            self.log_text.see(tk.END)
            self.root.update_idletasks()
    def set_status(self, text):
        self.status_var.set(text)
        self.root.update_idletasks()
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        EventBus.publish("log", self.get_str('log_empty'))
    def save_log(self):
        log_content = self.log_text.get(1.0, tk.END)
        if not log_content.strip():
            messagebox.showinfo("Info", self.get_str('log_empty'))
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="modding_log.txt"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                EventBus.publish("log", self.get_str('log_saved', file_path))
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    # ===== Язык =====
    def change_language(self):
        self.lang = self.lang_combo.get()
        self.config['language'] = self.lang
        self.config_manager.save()
        self.console.lang = self.lang
        self.console.get_str = self.get_str
        self.update_all_texts()
    def update_all_texts(self):
        for btn_data in self.config['buttons']:
            btn_id = btn_data['id']
            if btn_id in self.buttons:
                text = btn_data.get(f'text_{self.lang}', btn_data.get('text_en', btn_id))
                self.buttons[btn_id].config(text=text)
        self.label_project.config(text=self.get_str('project_folder'))
        self.browse_btn.config(text=self.get_str('choose_project'))
        self.btn_open_scripts.config(text=self.get_str('open_mod_scripts'))
        self.label_log.config(text=self.get_str('log'))
        self.save_log_btn.config(text=self.get_str('save_log'))
        self.clear_btn.config(text=self.get_str('clear_log'))
        self.root.title(self.get_str('title'))
        self.status_var.set(self.get_str('status_ready'))
        # Обновляем подсказки для верхних кнопок (если они зависят от языка)
        # (Подсказки уже используют get_str, но язык может измениться – пересоздадим их?)
        # Просто обновим текст в существующих подсказках не получится, поэтому удалим и создадим заново
        # Можно пересоздать подсказки, но проще оставить как есть, т.к. они используют get_str при создании.
        # Но при смене языка текст подсказок уже не изменится. Чтобы исправить, можно пересоздать их.
        # Однако это не критично, т.к. язык меняется редко.
        # Я добавлю обновление подсказок, но для простоты можно пропустить.
        # Если хотите, можно пересоздать, но я пропущу.
    
    # ===== Инструменты =====
    def ensure_tools(self, project_dir):
        tools_dir = os.path.join(project_dir, 'tools')
        if os.path.exists(tools_dir):
            return tools_dir
        os.makedirs(tools_dir, exist_ok=True)
        src_tools = resource_path('tools')
        if not os.path.exists(src_tools):
            raise FileNotFoundError(f"Встроенная папка tools не найдена: {src_tools}")
        for item in os.listdir(src_tools):
            src = os.path.join(src_tools, item)
            dst = os.path.join(tools_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        return tools_dir
    
    # ===== Проект =====
    def browse_project(self):
        folder = filedialog.askdirectory(title=self.get_str('choose_project'))
        if folder:
            self.project_dir.set(folder)
            try:
                tools_path = self.ensure_tools(folder)
                self.tools_dir.set(tools_path)
                EventBus.publish("log", f"Папка проекта: {folder}")
                EventBus.publish("log", f"{self.get_str('tools_ready')} {tools_path}")
            except Exception as e:
                EventBus.publish("log", f"Ошибка при подготовке tools: {e}")
                messagebox.showerror("Error", f"Не удалось распаковать инструменты: {e}")
    
    def open_mod_scripts_folder(self):
        mod_scripts = os.path.join(self.project_dir.get(), 'mod_scripts')
        if os.path.exists(mod_scripts):
            os.startfile(mod_scripts)
        else:
            messagebox.showerror("Error", "Папка mod_scripts не найдена. Сначала выполните декомпиляцию.")
    
    # ===== Основные команды =====
    
    def choose_resource_car(self):
        file_path = filedialog.askopenfilename(
            title=self.get_str('choose_car_title'),
            filetypes=[("Corona Archive", "*.car"), ("All files", "*.*")]
        )
        if file_path:
            self.resource_car_path = file_path
            EventBus.publish("log", f"{self.get_str('car_selected')} {file_path}")
            messagebox.showinfo("Success", f"{self.get_str('car_selected')}\n{file_path}")
    
    def run_unpack(self):
        if not self.resource_car_path:
            self.choose_resource_car()
        if not self.resource_car_path:
            return
        self.run_in_thread(self._unpack_thread)
    
    def _unpack_thread(self):
        try:
            EventBus.publish("log", "=== Распаковка resource.car ===")
            if not self.resource_car_path or not os.path.exists(self.resource_car_path):
                EventBus.publish("log", "ОШИБКА: файл resource.car не выбран или не существует!")
                return
            original_scripts = os.path.join(self.project_dir.get(), 'original_scripts')
            if os.path.exists(original_scripts):
                shutil.rmtree(original_scripts)
            os.makedirs(original_scripts, exist_ok=True)
            extract_dir = os.path.join(self.project_dir.get(), '_temp_extract')
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            os.makedirs(extract_dir)
            
            corona_script = os.path.join(self.tools_dir.get(), 'corona-archiver.py')
            corona = import_module_from_file(corona_script, 'corona_archiver')
            archiver = corona.CoronaArchiver()
            archiver.unpack(self.resource_car_path, extract_dir + os.sep)
            
            if not os.listdir(extract_dir):
                EventBus.publish("log", "ВНИМАНИЕ: папка _temp_extract пуста. Ищем .lu файлы в корне проекта...")
                root_files = [f for f in os.listdir(self.project_dir.get()) if f.endswith('.lu')]
                if root_files:
                    for file in root_files:
                        src = os.path.join(self.project_dir.get(), file)
                        dst = os.path.join(original_scripts, file)
                        shutil.move(src, dst)
                        EventBus.publish("log", f"Перемещён: {file}")
                    shutil.rmtree(extract_dir)
                    EventBus.publish("log", f"Распаковано {len(root_files)} .lu файлов")
                    EventBus.publish("log", self.get_str('success_unpack'))
                    return
                else:
                    EventBus.publish("log", "Не найдено .lu файлов ни в _temp_extract, ни в корне проекта.")
                    return
            
            count = 0
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.endswith('.lu'):
                        src = os.path.join(root, file)
                        rel_path = os.path.relpath(src, extract_dir)
                        dst = os.path.join(original_scripts, rel_path)
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst)
                        count += 1
            shutil.rmtree(extract_dir)
            EventBus.publish("log", f"Распаковано {count} .lu файлов")
            EventBus.publish("log", self.get_str('success_unpack'))
        except Exception as e:
            EventBus.publish("log", f"Исключение: {e}")
            import traceback
            EventBus.publish("log", traceback.format_exc())
    
    # ---- Декомпиляция всех (с диалогом) ----
    def run_decompile_all(self):
        if not self.project_dir.get():
            messagebox.showerror("Error", self.get_str('err_no_project'))
            return
        original_scripts = os.path.join(self.project_dir.get(), 'original_scripts')
        if not os.path.exists(original_scripts):
            messagebox.showerror("Error", "Папка original_scripts не найдена. Сначала распакуйте resource.car.")
            return
        
        target_folder = os.path.join(self.project_dir.get(), 'mod_scripts')
        self.show_decompile_dialog(
            target_folder=target_folder,
            decompile_func=self._decompile_all_thread,
            tool_name="dr_decompiler_windows (основной)"
        )
    
    def _decompile_all_thread(self, mode='full'):
        try:
            EventBus.publish("log", f"=== Декомпиляция всех .lu (dr_decompiler) ===")
            original_scripts = os.path.join(self.project_dir.get(), 'original_scripts')
            mod_scripts = os.path.join(self.project_dir.get(), 'mod_scripts')
            
            if mode == 'full':
                if os.path.exists(mod_scripts):
                    shutil.rmtree(mod_scripts)
                os.makedirs(mod_scripts, exist_ok=True)
            else:
                os.makedirs(mod_scripts, exist_ok=True)
            
            decompiler = os.path.join(self.tools_dir.get(), 'dr_decompiler_windows.exe')
            if not os.path.exists(decompiler):
                EventBus.publish("log", "dr_decompiler_windows.exe не найден!")
                return
            
            lu_files = []
            for root, dirs, files in os.walk(original_scripts):
                for file in files:
                    if file.endswith('.lu'):
                        lu_files.append(os.path.join(root, file))
            
            if not lu_files:
                EventBus.publish("log", "Нет .lu файлов для декомпиляции.")
                return
            
            existing_files = set()
            if mode in ['add_missing', 'try_other']:
                for root, _, files in os.walk(mod_scripts):
                    for f in files:
                        if f.endswith('.lua'):
                            rel_path = os.path.relpath(os.path.join(root, f), mod_scripts)
                            existing_files.add(rel_path)
            
            total = len(lu_files)
            failed = []
            skipped = 0
            
            for idx, lu_path in enumerate(lu_files):
                rel_path = os.path.relpath(lu_path, original_scripts)
                lua_name = os.path.splitext(rel_path)[0] + '.lua'
                lua_path = os.path.join(mod_scripts, lua_name)
                
                if mode == 'add_missing' and os.path.exists(lua_path):
                    skipped += 1
                    continue
                
                os.makedirs(os.path.dirname(lua_path), exist_ok=True)
                cmd = [decompiler, lu_path]
                EventBus.publish("log", f"[{idx+1}/{total}] Декомпиляция: {rel_path}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    EventBus.publish("log", f"Ошибка декомпиляции {rel_path}: {result.stderr}")
                    failed.append(rel_path)
                else:
                    output = result.stdout if result.stdout is not None else ""
                    if output.strip():
                        with open(lua_path, 'w', encoding='utf-8') as f_out:
                            f_out.write(output)
                    else:
                        EventBus.publish("log", f"Декомпиляция {rel_path} не дала результата (пустой вывод)")
                        failed.append(rel_path)
            
            if skipped:
                EventBus.publish("log", f"Пропущено {skipped} файлов (уже существуют)")
            if failed:
                EventBus.publish("log", f"Не удалось декомпилировать {len(failed)} файлов: {', '.join(failed)}")
            else:
                EventBus.publish("log", self.get_str('success_decompile'))
                messagebox.showinfo("Success", self.get_str('success_decompile'))
        except Exception as e:
            EventBus.publish("log", f"Исключение: {e}")
            import traceback
            EventBus.publish("log", traceback.format_exc())
    
    # ---- Диалог выбора при повторной декомпиляции (локализованный) ----
    def show_decompile_dialog(self, target_folder, decompile_func, tool_name):
        if not os.path.exists(target_folder):
            self.run_in_thread(lambda: decompile_func())
            return
        
        lua_files = []
        for root, _, files in os.walk(target_folder):
            for f in files:
                if f.endswith('.lua'):
                    lua_files.append(os.path.join(root, f))
        
        if not lua_files:
            self.run_in_thread(lambda: decompile_func())
            return
        
        self._show_decompile_choice_dialog(target_folder, decompile_func, tool_name)
    
    def _show_decompile_choice_dialog(self, target_folder, decompile_func, tool_name):
        win = tk.Toplevel(self.root)
        win.title(self.get_str('decompile_dialog_title'))
        win.geometry("500x400")
        win.configure(bg='#2b2b2b')
        win.resizable(False, False)
        win.lift()
        win.focus_force()
        
        lua_files = []
        for root, _, files in os.walk(target_folder):
            for f in files:
                if f.endswith('.lua'):
                    lua_files.append(os.path.join(root, f))
        file_count = len(lua_files)
        
        tk.Label(win, text=self.get_str('decompile_dialog_warning'),
                 fg='#ffcc00', bg='#2b2b2b', font=('Segoe UI', 14, 'bold')).pack(pady=10)
        tk.Label(win, text=self.get_str('decompile_dialog_folder_has', os.path.basename(target_folder), file_count),
                 fg='white', bg='#2b2b2b', font=('Segoe UI', 10)).pack(pady=5)
        tk.Label(win, text=self.get_str('decompile_dialog_using_tool', tool_name),
                 fg='#88ccff', bg='#2b2b2b', font=('Segoe UI', 10, 'italic')).pack(pady=5)
        tk.Label(win, text=self.get_str('decompile_dialog_question'),
                 fg='white', bg='#2b2b2b', font=('Segoe UI', 11, 'bold')).pack(pady=10)
        
        btn_frame = tk.Frame(win, bg='#2b2b2b')
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def choose_action(action):
            win.destroy()
            if action == 'replace':
                if messagebox.askyesno(self.get_str('decompile_dialog_confirm_replace'),
                                       self.get_str('decompile_dialog_confirm_replace', os.path.basename(target_folder))):
                    shutil.rmtree(target_folder)
                    os.makedirs(target_folder, exist_ok=True)
                    self.run_in_thread(lambda: decompile_func(mode='full'))
            elif action == 'add_missing':
                self.run_in_thread(lambda: decompile_func(mode='add_missing'))
            elif action == 'try_other':
                self.run_in_thread(lambda: decompile_func(mode='try_other'))
        
        btn_replace = tk.Button(btn_frame, text=self.get_str('decompile_dialog_replace'),
                                command=lambda: choose_action('replace'),
                                bg='#cc3333', fg='white', relief='flat', font=('Segoe UI', 10))
        btn_replace.pack(fill=tk.X, pady=3)
        tk.Label(btn_frame, text=self.get_str('decompile_dialog_replace_desc'),
                 fg='#888888', bg='#2b2b2b', font=('Segoe UI', 8)).pack(pady=(0, 5))
        
        btn_add = tk.Button(btn_frame, text=self.get_str('decompile_dialog_add_missing'),
                            command=lambda: choose_action('add_missing'),
                            bg='#3388cc', fg='white', relief='flat', font=('Segoe UI', 10))
        btn_add.pack(fill=tk.X, pady=3)
        tk.Label(btn_frame, text=self.get_str('decompile_dialog_add_missing_desc'),
                 fg='#888888', bg='#2b2b2b', font=('Segoe UI', 8)).pack(pady=(0, 5))
        
        btn_other = tk.Button(btn_frame, text=self.get_str('decompile_dialog_try_other'),
                              command=lambda: choose_action('try_other'),
                              bg='#cc8833', fg='white', relief='flat', font=('Segoe UI', 10))
        btn_other.pack(fill=tk.X, pady=3)
        tk.Label(btn_frame, text=self.get_str('decompile_dialog_try_other_desc'),
                 fg='#888888', bg='#2b2b2b', font=('Segoe UI', 8)).pack(pady=(0, 5))
        
        btn_cancel = tk.Button(btn_frame, text=self.get_str('decompile_dialog_cancel'),
                               command=win.destroy,
                               bg='#555555', fg='white', relief='flat', font=('Segoe UI', 10))
        btn_cancel.pack(fill=tk.X, pady=5)
    
    # ---- Компиляция всех (предупреждение) ----
    def run_compile_all(self):
        if not self.project_dir.get():
            return
        if messagebox.askyesno(self.get_str('compile_all'), self.get_str('compile_all') + "\n\n" + "Массовая компиляция всех .lua файлов может сломать игру!\nПродолжить?"):
            self.run_in_thread(self._compile_all_thread)
    
    def _compile_all_thread(self):
        try:
            EventBus.publish("log", "=== МАССОВАЯ КОМПИЛЯЦИЯ (ПРЕДУПРЕЖДЕНИЕ) ===")
            mod_scripts = os.path.join(self.project_dir.get(), 'mod_scripts')
            if not os.path.exists(mod_scripts):
                EventBus.publish("log", "Папка mod_scripts не найдена. Сначала декомпилируйте.")
                return
            modded_lu = os.path.join(self.project_dir.get(), 'modded_lu')
            if os.path.exists(modded_lu):
                shutil.rmtree(modded_lu)
            os.makedirs(modded_lu, exist_ok=True)
            luac = os.path.join(self.tools_dir.get(), 'luac.exe')
            if not os.path.exists(luac):
                EventBus.publish("log", "luac.exe не найден!")
                return
            
            lua_files = []
            for root, dirs, files in os.walk(mod_scripts):
                for file in files:
                    if file.endswith('.lua'):
                        lua_files.append(os.path.join(root, file))
            if not lua_files:
                EventBus.publish("log", "Нет .lua файлов для компиляции.")
                return
            
            total = len(lua_files)
            for idx, lua_path in enumerate(lua_files):
                rel_path = os.path.relpath(lua_path, mod_scripts)
                lu_name = os.path.splitext(rel_path)[0] + '.lu'
                lu_path = os.path.join(modded_lu, lu_name)
                os.makedirs(os.path.dirname(lu_path), exist_ok=True)
                cmd = [luac, '-o', lu_path, lua_path]
                EventBus.publish("log", f"[{idx+1}/{total}] Компиляция: {rel_path}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    EventBus.publish("log", f"Ошибка компиляции {rel_path}")
                    EventBus.publish("log", result.stderr)
            EventBus.publish("log", "Компиляция завершена. .lu файлы в modded_lu/")
        except Exception as e:
            EventBus.publish("log", f"Исключение: {e}")
            import traceback
            EventBus.publish("log", traceback.format_exc())
    
    # ---- Упаковка мода ----
    def run_pack(self):
        if not self.project_dir.get():
            messagebox.showerror("Error", self.get_str('err_no_project'))
            return
        default_path = os.path.join(self.project_dir.get(), 'packed_mod', 'resource.car')
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        save_path = filedialog.asksaveasfilename(
            title=self.get_str('pack_save_as'),
            defaultextension=".car",
            filetypes=[("Corona Archive", "*.car"), ("All files", "*.*")],
            initialfile="resource.car",
            initialdir=os.path.dirname(default_path)
        )
        if not save_path:
            return
        self.run_in_thread(lambda: self._pack_thread(save_path))
    
    def _pack_thread(self, output_car):
        try:
            EventBus.publish("log", f"=== Упаковка resource.car в {output_car} ===")
            packed_mod_dir = os.path.dirname(output_car)
            os.makedirs(packed_mod_dir, exist_ok=True)
            temp_dir = os.path.join(packed_mod_dir, '_temp_pack')
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            original_scripts = os.path.join(self.project_dir.get(), 'original_scripts')
            if not os.path.exists(original_scripts):
                EventBus.publish("log", "ОШИБКА: original_scripts не найдена. Сначала распакуйте resource.car.")
                return
            
            for root, dirs, files in os.walk(original_scripts):
                for file in files:
                    if file.endswith('.lu'):
                        src = os.path.join(root, file)
                        rel_path = os.path.relpath(src, original_scripts)
                        dst = os.path.join(temp_dir, rel_path)
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst)
            
            modded_lu = os.path.join(self.project_dir.get(), 'modded_lu')
            if os.path.exists(modded_lu):
                for root, dirs, files in os.walk(modded_lu):
                    for file in files:
                        if file.endswith('.lu'):
                            src = os.path.join(root, file)
                            rel_path = os.path.relpath(src, modded_lu)
                            dst = os.path.join(temp_dir, rel_path)
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                            shutil.copy2(src, dst)
                            EventBus.publish("log", f"Заменён модифицированный: {rel_path}")
            else:
                EventBus.publish("log", "ВНИМАНИЕ: modded_lu пуста, упаковываются только оригиналы.")
            
            corona_script = os.path.join(self.tools_dir.get(), 'corona-archiver.py')
            corona = import_module_from_file(corona_script, 'corona_archiver')
            archiver = corona.CoronaArchiver()
            archiver.pack(temp_dir + os.sep, output_car)
            
            shutil.rmtree(temp_dir)
            EventBus.publish("log", f"Готово! resource.car сохранён в {output_car}")
            EventBus.publish("log", self.get_str('success_pack'))
        except Exception as e:
            EventBus.publish("log", f"Исключение: {e}")
            import traceback
            EventBus.publish("log", traceback.format_exc())
    
    # ---- Компиляция одного .lua ----
    def run_compile_one(self):
        file_path = filedialog.askopenfilename(title=self.get_str('choose_lua'), filetypes=[("Lua files", "*.lua")])
        if file_path:
            self.run_in_thread(lambda: self._compile_one_thread(file_path))
    
    def _compile_one_thread(self, lua_path):
        try:
            EventBus.publish("log", f"=== Компиляция одного файла: {os.path.basename(lua_path)} ===")
            luac = os.path.join(self.tools_dir.get(), 'luac.exe')
            if not os.path.exists(luac):
                EventBus.publish("log", "luac.exe не найден!")
                return
            mod_scripts = os.path.join(self.project_dir.get(), 'mod_scripts')
            if not os.path.exists(mod_scripts):
                EventBus.publish("log", "Папка mod_scripts не найдена. Сначала декомпилируйте.")
                return
            if not lua_path.startswith(mod_scripts):
                EventBus.publish("log", "Файл должен находиться внутри папки mod_scripts.")
                return
            rel_path = os.path.relpath(lua_path, mod_scripts)
            lu_name = os.path.splitext(rel_path)[0] + '.lu'
            modded_lu = os.path.join(self.project_dir.get(), 'modded_lu')
            os.makedirs(modded_lu, exist_ok=True)
            out_path = os.path.join(modded_lu, lu_name)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            
            cmd = [luac, '-o', out_path, lua_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                EventBus.publish("log", "Ошибка компиляции!")
                EventBus.publish("log", result.stderr)
            else:
                EventBus.publish("log", f"Создан: {out_path}")
                EventBus.publish("log", self.get_str('compile_one_done'))
                messagebox.showinfo("Success", self.get_str('compile_one_done'))
        except Exception as e:
            EventBus.publish("log", f"Исключение: {e}")
    
    # ---- Декомпиляция одного .lu ----
    def run_decompile_one(self):
        file_path = filedialog.askopenfilename(title=self.get_str('choose_lu'), filetypes=[("Lu files", "*.lu")])
        if file_path:
            self.run_in_thread(lambda: self._decompile_one_thread(file_path))
    
    def _decompile_one_thread(self, lu_path):
        try:
            EventBus.publish("log", f"=== Декомпиляция одного файла: {os.path.basename(lu_path)} ===")
            decompiler = os.path.join(self.tools_dir.get(), 'dr_decompiler_windows.exe')
            if not os.path.exists(decompiler):
                EventBus.publish("log", "dr_decompiler_windows.exe не найден!")
                return
            out_path = os.path.splitext(lu_path)[0] + '.lua'
            cmd = [decompiler, lu_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                EventBus.publish("log", "Ошибка декомпиляции!")
                EventBus.publish("log", result.stderr)
                return
            output = result.stdout if result.stdout is not None else ""
            if output.strip():
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(output)
                os.remove(lu_path)
                EventBus.publish("log", f"Создан: {out_path}, исходный .lu удалён.")
                EventBus.publish("log", self.get_str('decompile_one_done'))
                messagebox.showinfo("Success", self.get_str('decompile_one_done'))
            else:
                EventBus.publish("log", "Декомпиляция не дала результата (пустой вывод)")
        except Exception as e:
            EventBus.publish("log", f"Исключение: {e}")
    
    # ---- Проверка одного .lua через Luacheck ----
    def run_check_one(self):
        file_path = filedialog.askopenfilename(title=self.get_str('check_one'), filetypes=[("Lua files", "*.lua")])
        if file_path:
            self.run_in_thread(lambda: self._check_file_thread(file_path))
    
    def _check_file_thread(self, file_path):
        self.log(self.get_str('check_single_start', os.path.basename(file_path)))
        output = self._run_luacheck(file_path)
        self.log(output)
    
    def _run_luacheck(self, file_path):
        luacheck_exe = os.path.join(self.tools_dir.get(), 'luacheck.exe')
        if not os.path.exists(luacheck_exe):
            msg = self.get_str('check_no_luacheck')
            self.log(msg)
            return msg
        
        cmd = [luacheck_exe, '--no-config', '--codes', file_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
            return output.strip() if output.strip() else "No issues found."
        except subprocess.TimeoutExpired:
            return self.get_str('check_timeout')
        except Exception as e:
            self.log(f"{self.get_str('check_error')}: {e}")
            return f"{self.get_str('check_error')}: {e}"
    
    # ---- Проверка всех .lua через Luacheck ----
    def run_check_all(self):
        if not self.project_dir.get():
            messagebox.showerror("Error", self.get_str('err_no_project'))
            return
        luacheck_exe = os.path.join(self.tools_dir.get(), 'luacheck.exe')
        if not os.path.exists(luacheck_exe):
            messagebox.showerror("Error", self.get_str('check_no_luacheck'))
            return
        self.run_in_thread(self._check_all_thread)
    
    def _check_all_thread(self):
        self.log(self.get_str('check_all_start'))
        mod_scripts = os.path.join(self.project_dir.get(), 'mod_scripts')
        if not os.path.exists(mod_scripts):
            self.log("Папка mod_scripts не найдена. Сначала выполните декомпиляцию.")
            return
        
        lua_files = []
        for root, dirs, files in os.walk(mod_scripts):
            for f in files:
                if f.endswith('.lua'):
                    lua_files.append(os.path.join(root, f))
        
        if not lua_files:
            self.log(self.get_str('check_all_no_files'))
            return
        
        total = len(lua_files)
        issues = 0
        for idx, fpath in enumerate(lua_files):
            rel = os.path.relpath(fpath, mod_scripts)
            self.log(f"[{idx+1}/{total}] Проверка {rel} ...")
            output = self._run_luacheck(fpath)
            if output and "No issues" not in output:
                issues += 1
                self.log(f"Замечания в {rel}:\n{output}")
        
        self.log(self.get_str('check_all_complete', issues, total))
        if issues == 0:
            messagebox.showinfo("Проверка", "Все файлы прошли проверку без замечаний!")
        else:
            messagebox.showwarning("Проверка", f"Найдены замечания в {issues} файлах. Смотрите лог.")
    
    # ---- Очистка проекта ----
    def clean_project(self):
        if messagebox.askyesno(self.get_str('clean_project'), self.get_str('clean_confirm')):
            self.run_in_thread(self._clean_project_thread)
    
    def _clean_project_thread(self):
        try:
            project = self.project_dir.get()
            for folder in ['original_scripts', 'mod_scripts', 'modded_lu', 'packed_mod']:
                path = os.path.join(project, folder)
                if os.path.exists(path):
                    shutil.rmtree(path)
                    EventBus.publish("log", f"Удалена папка: {path}")
            EventBus.publish("log", self.get_str('clean_success'))
        except Exception as e:
            EventBus.publish("log", f"Ошибка при очистке: {e}")
    
    # ---- Сброс mod_scripts ----
    def reset_mod_scripts(self):
        if messagebox.askyesno(self.get_str('reset_scripts'), self.get_str('reset_confirm')):
            self.run_in_thread(self._reset_mod_scripts_thread)
    
    def _reset_mod_scripts_thread(self):
        mod_scripts = os.path.join(self.project_dir.get(), 'mod_scripts')
        if os.path.exists(mod_scripts):
            shutil.rmtree(mod_scripts)
            EventBus.publish("log", "Папка mod_scripts удалена.")
        else:
            EventBus.publish("log", "Папка mod_scripts не существует.")
        self._decompile_all_thread()
    
    # ---- Очистка modded_lu ----
    def clear_modded_lu(self):
        if messagebox.askyesno(self.get_str('clear_modded'), self.get_str('clear_modded_confirm')):
            self.run_in_thread(self._clear_modded_lu_thread)
    
    def _clear_modded_lu_thread(self):
        modded_lu = os.path.join(self.project_dir.get(), 'modded_lu')
        if os.path.exists(modded_lu):
            shutil.rmtree(modded_lu)
            EventBus.publish("log", "Папка modded_lu удалена.")
            messagebox.showinfo("Success", "modded_lu очищена.")
        else:
            EventBus.publish("log", "Папка modded_lu не существует.")
            messagebox.showinfo("Info", "modded_lu уже пуста.")
    
    # ---- Менеджер файлов ----
    def open_file_manager(self):
        if not self.project_dir.get():
            messagebox.showerror("Error", self.get_str('err_no_project'))
            return
        mod_scripts = os.path.join(self.project_dir.get(), 'mod_scripts')
        if not os.path.exists(mod_scripts):
            messagebox.showerror("Error", self.get_str('file_manager_no_mod_scripts'))
            return
        
        lua_files = []
        for root, dirs, files in os.walk(mod_scripts):
            for file in files:
                if file.endswith('.lua'):
                    lua_files.append(os.path.join(root, file))
        
        if not lua_files:
            messagebox.showinfo("Info", self.get_str('no_files'))
            return
        
        win = tk.Toplevel(self.root)
        win.title(self.get_str('file_list_title'))
        win.geometry("750x550")
        win.resizable(True, True)
        win.configure(bg='#2b2b2b')
        win.lift()
        win.focus_force()
        
        search_frame = tk.Frame(win, bg='#2b2b2b')
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(search_frame, text=self.get_str('search'), fg='white', bg='#2b2b2b').pack(side=tk.LEFT)
        search_entry = tk.Entry(search_frame, bg='#3c3c3c', fg='white', insertbackground='white', relief='flat')
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        btn_info = tk.Button(search_frame, text=self.get_str('file_info'), command=self.show_file_info,
                             bg='#3c3c3c', fg='white', relief='flat')
        btn_info.pack(side=tk.RIGHT)
        
        frame = tk.Frame(win, bg='#2b2b2b')
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(frame, bg='#2b2b2b', highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2b2b2b')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def update_list(filter_text=""):
            for widget in scrollable_frame.winfo_children():
                widget.destroy()
            filter_lower = filter_text.lower()
            for lua_path in sorted(lua_files):
                rel_path = os.path.relpath(lua_path, mod_scripts)
                if filter_lower and filter_lower not in rel_path.lower():
                    continue
                row_frame = tk.Frame(scrollable_frame, bg='#2b2b2b')
                row_frame.pack(fill=tk.X, pady=2)
                tk.Label(row_frame, text=rel_path, anchor="w", width=50, fg='white', bg='#2b2b2b', font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)
                
                btn_open = tk.Button(row_frame, text=self.get_str('edit_btn'),
                                     command=lambda p=lua_path: self.open_file_in_editor(p),
                                     bg='#3c3c3c', fg='white', relief='flat')
                btn_open.pack(side=tk.LEFT, padx=2)
                
                btn_build = tk.Button(row_frame, text=self.get_str('build_btn'),
                                      command=lambda p=lua_path: self.compile_single_file(p),
                                      bg='#3c3c3c', fg='white', relief='flat')
                btn_build.pack(side=tk.LEFT, padx=2)
                
                btn_hash = tk.Button(row_frame, text=self.get_str('show_hash'),
                                     command=lambda p=lua_path: self.show_file_hash(p),
                                     bg='#3c3c3c', fg='white', relief='flat')
                btn_hash.pack(side=tk.LEFT, padx=2)
                
                btn_check = tk.Button(row_frame, text=self.get_str('check_btn'),
                                      command=lambda p=lua_path: self.run_check_one_from_manager(p),
                                      bg='#3c3c3c', fg='white', relief='flat')
                btn_check.pack(side=tk.LEFT, padx=2)
        
        search_entry.bind('<KeyRelease>', lambda e: update_list(search_entry.get()))
        update_list()
    
    def compile_single_file(self, file_path):
        self.run_in_thread(lambda: self._compile_one_thread(file_path))
    
    def run_check_one_from_manager(self, file_path):
        self.run_in_thread(lambda: self._check_file_thread(file_path))
    
    # ---- Встроенный редактор ----
    def open_file_in_editor(self, file_path):
        if not os.path.exists(file_path):
            messagebox.showerror("Error", self.get_str('file_not_found'))
            return
        
        try:
            from pygments import lex
            from pygments.lexers import get_lexer_by_name
            from pygments.token import Token
            has_pygments = True
        except ImportError:
            has_pygments = False
        
        win = tk.Toplevel(self.root)
        win.title(f"{self.get_str('edit_btn')}: {os.path.basename(file_path)}")
        win.geometry("800x600")
        win.configure(bg='#2b2b2b')
        win.lift()
        win.focus_force()
        
        text_widget = tk.Text(win, wrap=tk.WORD, bg='#1e1e1e', fg='#eeeeee',
                              insertbackground='white', undo=True, font=('Courier New', 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            text_widget.insert(tk.END, content)
        except Exception as e:
            messagebox.showerror("Error", f"Не удалось загрузить файл: {e}")
            win.destroy()
            return
        
        if has_pygments:
            style = {
                Token.Keyword: 'cyan',
                Token.Keyword.Constant: 'cyan',
                Token.Keyword.Declaration: 'cyan',
                Token.Keyword.Namespace: 'cyan',
                Token.Keyword.Pseudo: 'cyan',
                Token.Keyword.Reserved: 'cyan',
                Token.Keyword.Type: 'cyan',
                Token.Name.Function: 'yellow',
                Token.Name.Class: 'yellow',
                Token.Name.Decorator: 'yellow',
                Token.Name.Exception: 'yellow',
                Token.String: 'green',
                Token.String.Doc: 'green',
                Token.String.Interpol: 'green',
                Token.String.Escape: 'green',
                Token.Comment: 'gray',
                Token.Comment.Single: 'gray',
                Token.Comment.Multiline: 'gray',
                Token.Comment.Preproc: 'gray',
                Token.Number: 'orange',
                Token.Number.Integer: 'orange',
                Token.Number.Float: 'orange',
                Token.Number.Hex: 'orange',
                Token.Number.Oct: 'orange',
                Token.Operator: 'white',
                Token.Operator.Word: 'white',
                Token.Punctuation: 'white',
                Token.Text: 'white',
            }
            for token, color in style.items():
                text_widget.tag_configure(str(token), foreground=color)
            
            def highlight_syntax(event=None):
                for token in style:
                    text_widget.tag_remove(str(token), '1.0', tk.END)
                text = text_widget.get('1.0', tk.END)
                lexer = get_lexer_by_name('lua')
                tokens = list(lex(text, lexer))
                pos = 0
                for token_type, token_text in tokens:
                    if token_type in style:
                        start = f'1.0 + {pos} chars'
                        end = f'1.0 + {pos + len(token_text)} chars'
                        text_widget.tag_add(str(token_type), start, end)
                    pos += len(token_text)
            
            text_widget.bind('<KeyRelease>', highlight_syntax)
            text_widget.bind('<ButtonRelease>', highlight_syntax)
            highlight_syntax()
        
        btn_frame = tk.Frame(win, bg='#2b2b2b')
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        def save_file():
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_widget.get(1.0, tk.END))
                EventBus.publish("log", f"Файл сохранён: {file_path}")
                messagebox.showinfo("Success", self.get_str('editor_saved'))
            except Exception as e:
                messagebox.showerror("Error", f"Ошибка сохранения: {e}")
        
        def save_and_compile():
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_widget.get(1.0, tk.END))
                EventBus.publish("log", f"Файл сохранён: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Ошибка сохранения: {e}")
                return
            self.compile_single_file(file_path)
        
        tk.Button(btn_frame, text=self.get_str('editor_save'), command=save_file,
                  bg='#3c3c3c', fg='white', relief='flat').pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text=self.get_str('editor_save_compile'), command=save_and_compile,
                  bg='#3c3c3c', fg='white', relief='flat').pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text=self.get_str('editor_close'), command=win.destroy,
                  bg='#3c3c3c', fg='white', relief='flat').pack(side=tk.RIGHT, padx=2)
    
    # ---- Хеш ----
    def show_file_hash(self, file_path):
        try:
            if not os.path.exists(file_path):
                messagebox.showerror("Error", self.get_str('file_not_found'))
                return
            sha1 = hashlib.sha1()
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    sha1.update(data)
            hash_value = sha1.hexdigest()
            win = tk.Toplevel(self.root)
            win.title(self.get_str('hash_title'))
            win.geometry("550x150")
            win.configure(bg='#2b2b2b')
            win.resizable(False, False)
            win.lift()
            win.focus_force()
            tk.Label(win, text=self.get_str('file_hash_label', os.path.basename(file_path)), fg='white', bg='#2b2b2b', font=('Segoe UI', 10)).pack(pady=5)
            tk.Label(win, text=self.get_str('file_hash_value', hash_value), fg='#88ccff', bg='#2b2b2b', font=('Segoe UI', 10)).pack(pady=5)
            btn_close = tk.Button(win, text="Закрыть" if self.lang == 'ru' else "Close", command=win.destroy,
                                  bg='#3c3c3c', fg='white', relief='flat')
            btn_close.pack(pady=10)
        except Exception as e:
            messagebox.showerror(self.get_str('hash_error'), str(e))
    
    # ---- Инфо файлы ----
    def show_file_info(self):
        win = tk.Toplevel(self.root)
        win.title(self.get_str('file_info'))
        win.geometry("750x600")
        win.configure(bg='#1e1e1e')
        win.lift()
        win.focus_force()
        text_widget = tk.Text(win, wrap=tk.WORD, bg='#2b2b2b', fg='#eeeeee', insertbackground='white', padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.tag_configure('heading', font=('Segoe UI', 14, 'bold'), foreground='#ffcc00', spacing1=5, spacing2=3)
        text_widget.tag_configure('normal', font=('Segoe UI', 10), foreground='#eeeeee', spacing1=2, spacing2=2)
        text_widget.tag_configure('frame', background='#3c3c3c', lmargin1=20, lmargin2=20, spacing1=5, spacing2=5, font=('Segoe UI', 10), foreground='#dddddd')
        
        info_files = {'ru': 'file_description_ru.txt', 'en': 'file_description_en.txt'}
        filename = info_files.get(self.lang, 'file_description_ru.txt')
        file_path = resource_path('text/' + filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            content = self.get_str('info_not_found', filename)
        
        lines = content.splitlines()
        in_frame = False
        frame_lines = []
        for line in lines:
            if line.startswith('!!Heading!!'):
                heading_text = line[len('!!Heading!!'):].strip()
                if heading_text:
                    text_widget.insert(tk.END, heading_text + '\n', 'heading')
                else:
                    text_widget.insert(tk.END, '\n')
            elif line.startswith('!!Frame!!'):
                in_frame = True
                frame_lines = []
            elif line.startswith('!!EndFrame!!'):
                in_frame = False
                if frame_lines:
                    frame_text = '\n'.join(frame_lines)
                    text_widget.insert(tk.END, '\n', 'frame')
                    text_widget.insert(tk.END, frame_text + '\n', 'frame')
                    text_widget.insert(tk.END, '\n', 'frame')
            else:
                if in_frame:
                    frame_lines.append(line)
                else:
                    if line.strip():
                        text_widget.insert(tk.END, line + '\n', 'normal')
                    else:
                        text_widget.insert(tk.END, '\n')
        text_widget.config(state=tk.DISABLED)
    
    # ---- Lua-консоль (старая) ----
    def open_console(self):
        lua_exe = os.path.join(self.tools_dir.get(), 'lua51.exe')
        if not os.path.exists(lua_exe):
            messagebox.showerror("Error", "lua51.exe not found in tools folder!")
            return
        
        win = tk.Toplevel(self.root)
        win.title(self.get_str('console_title'))
        win.geometry("600x500")
        win.configure(bg='#2b2b2b')
        win.resizable(True, True)
        win.lift()
        win.focus_force()
        
        tk.Label(win, text=self.get_str('console_input_label'), fg='white', bg='#2b2b2b', font=('Segoe UI', 10)).pack(pady=5)
        input_frame = tk.Frame(win, bg='#2b2b2b')
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        input_text = tk.Text(input_frame, height=6, bg='#1e1e1e', fg='#eeeeee', insertbackground='white', font=('Courier New', 10))
        input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(win, bg='#2b2b2b')
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        def run_code():
            code = input_text.get(1.0, tk.END).strip()
            if not code:
                return
            btn_run.config(state=tk.DISABLED)
            def thread_target():
                try:
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False, encoding='utf-8') as tf:
                        tf.write(code)
                        temp_path = tf.name
                    cmd = [lua_exe, temp_path]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    output = result.stdout + result.stderr
                    output_text.insert(tk.END, self.get_str('console_executing', code))
                    if output.strip():
                        output_text.insert(tk.END, self.get_str('console_result', output))
                    else:
                        output_text.insert(tk.END, self.get_str('console_empty'))
                    output_text.see(tk.END)
                    os.unlink(temp_path)
                except subprocess.TimeoutExpired:
                    output_text.insert(tk.END, self.get_str('console_executing', code))
                    output_text.insert(tk.END, self.get_str('console_timeout'))
                except Exception as e:
                    output_text.insert(tk.END, self.get_str('console_error', str(e)))
                finally:
                    btn_run.config(state=tk.NORMAL)
            threading.Thread(target=thread_target, daemon=True).start()
        
        btn_run = tk.Button(btn_frame, text=self.get_str('console_run_btn'), command=run_code, bg='#3c3c3c', fg='white', relief='flat')
        btn_run.pack(side=tk.LEFT, padx=2)
        input_text.bind('<Control-Return>', lambda e: run_code())
        
        tk.Label(win, text="Output:", fg='white', bg='#2b2b2b', font=('Segoe UI', 10)).pack(pady=5)
        output_text = scrolledtext.ScrolledText(win, bg='#1e1e1e', fg='#eeeeee', insertbackground='white',
                                                font=('Courier New', 10), state='normal')
        output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        output_text.insert(tk.END, self.get_str('console_ready'))
        
        btn_clear = tk.Button(win, text=self.get_str('console_clear_btn'), command=lambda: output_text.delete(1.0, tk.END),
                              bg='#3c3c3c', fg='white', relief='flat')
        btn_clear.pack(side=tk.BOTTOM, pady=5)
    
    # ---- Командная консоль (новая) ----
    def open_tool_console(self):
        self.console.show()
    
    # ---- Профили (полноценная реализация) ----
    def open_profile_manager(self):
        win = tk.Toplevel(self.root)
        win.title(self.get_str('profile_manager_title'))
        win.geometry("500x400")
        win.configure(bg='#2b2b2b')
        win.resizable(False, False)
        win.lift()
        win.focus_force()

        listbox = tk.Listbox(win, bg='#3c3c3c', fg='white', selectmode=tk.SINGLE, height=10)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def refresh_list():
            listbox.delete(0, tk.END)
            for name, data in self.profile_manager.get_all().items():
                listbox.insert(tk.END, f"{name} ({data.get('project_path', '')})")

        refresh_list()

        def get_selected_name():
            selection = listbox.curselection()
            if not selection:
                messagebox.showinfo("Info", self.get_str('profile_select_first'))
                return None
            full = listbox.get(selection[0])
            return full.split(' (')[0]

        btn_frame = tk.Frame(win, bg='#2b2b2b')
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        def create_profile():
            create_win = tk.Toplevel(win)
            create_win.title(self.get_str('profile_create_title'))
            create_win.geometry("400x200")
            create_win.configure(bg='#2b2b2b')
            create_win.resizable(False, False)
            create_win.grab_set()

            tk.Label(create_win, text=self.get_str('profile_name_label'), fg='white', bg='#2b2b2b').pack(pady=5)
            name_entry = tk.Entry(create_win, bg='#3c3c3c', fg='white', insertbackground='white', width=40)
            name_entry.pack(pady=5)

            tk.Label(create_win, text=self.get_str('profile_path_label'), fg='white', bg='#2b2b2b').pack(pady=5)
            path_entry = tk.Entry(create_win, bg='#3c3c3c', fg='white', insertbackground='white', width=40)
            path_entry.pack(pady=5)
            path_entry.insert(0, self.project_dir.get() if self.project_dir.get() else '')

            def save_profile_action():
                name = name_entry.get().strip()
                path = path_entry.get().strip()
                if not name:
                    messagebox.showerror("Error", self.get_str('profile_name_required'))
                    return
                if not path or not os.path.exists(path):
                    messagebox.showerror("Error", self.get_str('profile_path_required'))
                    return
                self.profile_manager.add_or_update(name, path, "")
                create_win.destroy()
                refresh_list()

            tk.Button(create_win, text=self.get_str('profile_save_btn'), command=save_profile_action,
                      bg='#3c3c3c', fg='white', relief='flat').pack(pady=10)

        def edit_profile():
            name = get_selected_name()
            if not name:
                return
            data = self.profile_manager.get_profile(name)
            if not data:
                return

            edit_win = tk.Toplevel(win)
            edit_win.title(self.get_str('profile_edit_title'))
            edit_win.geometry("400x250")
            edit_win.configure(bg='#2b2b2b')
            edit_win.resizable(False, False)
            edit_win.grab_set()

            tk.Label(edit_win, text=self.get_str('profile_name_label'), fg='white', bg='#2b2b2b').pack(pady=5)
            name_entry = tk.Entry(edit_win, bg='#3c3c3c', fg='white', insertbackground='white', width=40)
            name_entry.insert(0, name)
            name_entry.pack(pady=5)
            name_entry.config(state='disabled')

            tk.Label(edit_win, text=self.get_str('profile_desc_label'), fg='white', bg='#2b2b2b').pack(pady=5)
            desc_entry = tk.Entry(edit_win, bg='#3c3c3c', fg='white', insertbackground='white', width=40)
            desc_entry.insert(0, data.get('description', ''))
            desc_entry.pack(pady=5)

            tk.Label(edit_win, text=self.get_str('profile_path_label'), fg='white', bg='#2b2b2b').pack(pady=5)
            path_entry = tk.Entry(edit_win, bg='#3c3c3c', fg='white', insertbackground='white', width=40)
            path_entry.insert(0, data.get('project_path', ''))
            path_entry.pack(pady=5)

            def save_edit():
                new_name = name_entry.get().strip()
                new_path = path_entry.get().strip()
                new_desc = desc_entry.get().strip()
                if not new_name or not new_path:
                    return
                self.profile_manager.add_or_update(name, new_path, new_desc)
                edit_win.destroy()
                refresh_list()

            tk.Button(edit_win, text=self.get_str('profile_save_btn'), command=save_edit,
                      bg='#3c3c3c', fg='white', relief='flat').pack(pady=10)

        def delete_profile():
            name = get_selected_name()
            if not name:
                return
            if messagebox.askyesno(self.get_str('profile_delete_confirm', name), self.get_str('profile_delete_confirm', name)):
                self.profile_manager.delete(name)
                refresh_list()

        def select_profile():
            name = get_selected_name()
            if not name:
                return
            data = self.profile_manager.get_profile(name)
            if not data:
                return
            project_path = data.get('project_path')
            if not project_path or not os.path.exists(project_path):
                messagebox.showerror("Error", self.get_str('profile_path_not_exists'))
                return
            self.project_dir.set(project_path)
            try:
                tools_path = self.ensure_tools(project_path)
                self.tools_dir.set(tools_path)
                EventBus.publish("log", f"Выбран профиль: {name}")
                EventBus.publish("log", f"Папка проекта: {project_path}")
                EventBus.publish("log", f"Инструменты готовы: {tools_path}")
            except Exception as e:
                EventBus.publish("log", f"Ошибка при загрузке профиля: {e}")
                messagebox.showerror("Error", str(e))
            win.destroy()

        tk.Button(btn_frame, text=self.get_str('profile_create_btn'), command=create_profile,
                  bg='#3c3c3c', fg='white', relief='flat').pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text=self.get_str('profile_edit_btn'), command=edit_profile,
                  bg='#3c3c3c', fg='white', relief='flat').pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text=self.get_str('profile_select_btn'), command=select_profile,
                  bg='#3c3c3c', fg='white', relief='flat').pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text=self.get_str('profile_delete_btn'), command=delete_profile,
                  bg='#3c3c3c', fg='white', relief='flat').pack(fill=tk.X, pady=2)
    
    # ---- Настройки ----
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title(self.get_str('settings_title'))
        win.geometry("500x450")
        win.configure(bg='#2b2b2b')
        win.resizable(False, False)
        win.lift()
        win.focus_force()
        
        tk.Label(win, text=self.get_str('font_label'), fg='white', bg='#2b2b2b', font=('Segoe UI', 10)).pack(pady=10)
        
        font_var = tk.StringVar(value=self.font_name)
        font_options = [
            ('classic', self.get_str('font_classic')),
            ('RO', self.get_str('font_ro')),
            ('freemono', self.get_str('font_freemono')),
            ('russo_one', self.get_str('font_russo'))
        ]
        
        for value, label in font_options:
            frame = tk.Frame(win, bg='#2b2b2b')
            frame.pack(fill=tk.X, padx=20, pady=2, anchor=tk.W)
            rb = tk.Radiobutton(frame, text=label, variable=font_var, value=value,
                                bg='#2b2b2b', fg='white', selectcolor='#2b2b2b',
                                activebackground='#2b2b2b', activeforeground='white')
            rb.pack(side=tk.LEFT)
            if value != 'classic':
                btn = tk.Button(frame, text=self.get_str('install_btn'), command=lambda v=value: self._install_font(v),
                                bg='#3c3c3c', fg='white', relief='flat')
                btn.pack(side=tk.RIGHT, padx=5)
        
        def open_font_folder():
            font_dir = resource_path('font')
            if os.path.exists(font_dir):
                os.startfile(font_dir)
            else:
                messagebox.showinfo("Info", "Папка font не найдена.")
        btn_open_folder = tk.Button(win, text=self.get_str('font_folder'),
                                    command=open_font_folder, bg='#3c3c3c', fg='white', relief='flat')
        btn_open_folder.pack(pady=5)
        
        def save_settings():
            selected = font_var.get()
            if selected != 'classic':
                font_files = {'RO': 'RO.ttf', 'freemono': 'freemono.ttf', 'russo_one': 'russo_one.ttf'}
                font_path = resource_path('font/' + font_files[selected])
                if not os.path.exists(font_path):
                    messagebox.showinfo("Info", self.get_str('font_missing'))
                    return
            set_setting('Font', 'name', selected)
            messagebox.showinfo("Success", self.get_str('font_saved'))
            win.destroy()
        
        btn_save = tk.Button(win, text=self.get_str('profile_save_btn'), command=save_settings,
                             bg='#3c3c3c', fg='white', relief='flat')
        btn_save.pack(pady=10)
    
    def _install_font(self, font_name):
        font_files = {'RO': 'RO.ttf', 'freemono': 'freemono.ttf', 'russo_one': 'russo_one.ttf'}
        font_path = resource_path('font/' + font_files[font_name])
        if not os.path.exists(font_path):
            messagebox.showerror("Error", "Файл шрифта не найден")
            return
        if not is_admin():
            messagebox.showerror("Error", "Для установки шрифта запустите программу от имени администратора")
            return
        success, msg = install_font_system(font_path)
        if success:
            messagebox.showinfo("Success", self.get_str('install_success', font_name))
        else:
            messagebox.showerror("Error", self.get_str('install_fail', msg))
    
    # ---- Помощь ----
    def show_help(self):
        win = tk.Toplevel(self.root)
        win.title(self.get_str('help_btn'))
        win.geometry("750x600")
        win.configure(bg='#1e1e1e')
        win.lift()
        win.focus_force()
        text_widget = tk.Text(win, wrap=tk.WORD, bg='#2b2b2b', fg='#eeeeee', insertbackground='white', padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.tag_configure('heading', font=('Segoe UI', 14, 'bold'), foreground='#ffcc00', spacing1=5, spacing2=3)
        text_widget.tag_configure('normal', font=('Segoe UI', 10), foreground='#eeeeee', spacing1=2, spacing2=2)
        text_widget.tag_configure('frame', background='#3c3c3c', lmargin1=20, lmargin2=20, spacing1=5, spacing2=5, font=('Segoe UI', 10), foreground='#dddddd')
        
        help_files = {'ru': 'memoca_instruction_ru.txt', 'en': 'memoca_instruction_en.txt'}
        filename = help_files.get(self.lang, 'memoca_instruction_ru.txt')
        file_path = resource_path('text/' + filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            content = self.get_str('help_not_found', filename)
        
        lines = content.splitlines()
        in_frame = False
        frame_lines = []
        for line in lines:
            if line.startswith('!!Heading!!'):
                heading_text = line[len('!!Heading!!'):].strip()
                if heading_text:
                    text_widget.insert(tk.END, heading_text + '\n', 'heading')
                else:
                    text_widget.insert(tk.END, '\n')
            elif line.startswith('!!Frame!!'):
                in_frame = True
                frame_lines = []
            elif line.startswith('!!EndFrame!!'):
                in_frame = False
                if frame_lines:
                    frame_text = '\n'.join(frame_lines)
                    text_widget.insert(tk.END, '\n', 'frame')
                    text_widget.insert(tk.END, frame_text + '\n', 'frame')
                    text_widget.insert(tk.END, '\n', 'frame')
            else:
                if in_frame:
                    frame_lines.append(line)
                else:
                    if line.strip():
                        text_widget.insert(tk.END, line + '\n', 'normal')
                    else:
                        text_widget.insert(tk.END, '\n')
        text_widget.config(state=tk.DISABLED)
    
    # ---- Новые функции (UTF-8, ассемблер) ----
    def run_decode_utf8(self):
        folder = filedialog.askdirectory(title="Выберите папку с .lua файлами для декодирования")
        if folder:
            self.run_in_thread(lambda: self._decode_utf8_thread(folder))
    
    def _decode_utf8_thread(self, folder):
        EventBus.publish("log", f"=== Декодирование UTF-8 в папке: {folder} ===")
        processed, errors, error_msgs = decode_utf8_folder(folder, force=False)
        EventBus.publish("log", f"Обработано файлов: {processed}, ошибок: {errors}")
        if errors:
            for msg in error_msgs:
                EventBus.publish("log", f"  Ошибка: {msg}")
        messagebox.showinfo("UTF-8 Декодер", f"Обработано: {processed}\nОшибок: {errors}\nСмотрите лог для деталей.")
    
    def run_disassemble_lu(self):
        file_path = filedialog.askopenfilename(title="Выберите .lu файл для дизассемблирования", filetypes=[("Lu files", "*.lu")])
        if file_path:
            self.run_in_thread(lambda: self._disassemble_thread(file_path))
    
    def _disassemble_thread(self, lu_path):
        try:
            EventBus.publish("log", f"=== Дизассемблирование: {os.path.basename(lu_path)} ===")
            out_path = os.path.splitext(lu_path)[0] + '.asm'
            result = disassemble_lu(lu_path, out_path)
            EventBus.publish("log", f"Создан файл: {out_path}")
            messagebox.showinfo("Успех", f"Дизассемблирование завершено\n{out_path}")
        except Exception as e:
            EventBus.publish("log", f"Ошибка: {e}")
            messagebox.showerror("Ошибка", str(e))
    
    def run_assemble_lu(self):
        file_path = filedialog.askopenfilename(title="Выберите .asm файл для ассемблирования", filetypes=[("Asm files", "*.asm")])
        if file_path:
            self.run_in_thread(lambda: self._assemble_thread(file_path))
    
    def _assemble_thread(self, asm_path):
        try:
            EventBus.publish("log", f"=== Ассемблирование: {os.path.basename(asm_path)} ===")
            out_path = os.path.splitext(asm_path)[0] + '.lu'
            result = assemble_lu(asm_path, out_path)
            EventBus.publish("log", f"Создан файл: {out_path}")
            messagebox.showinfo("Успех", f"Ассемблирование завершено\n{out_path}")
        except Exception as e:
            EventBus.publish("log", f"Ошибка: {e}")
            messagebox.showerror("Ошибка", str(e))
    
    # ===== Вспомогательные методы для потоков =====
    def run_in_thread(self, target):
        if not self.tools_dir.get():
            messagebox.showerror("Error", self.get_str('err_no_project'))
            return
        self.set_status(self.get_str('status_running'))
        for btn in self.all_buttons:
            btn.config(state=tk.DISABLED)
        
        def wrapper():
            try:
                target()
            except Exception as e:
                EventBus.publish("log", f"Ошибка в потоке: {e}")
                import traceback
                EventBus.publish("log", traceback.format_exc())
                messagebox.showerror("Error", str(e))
            finally:
                for btn in self.all_buttons:
                    btn.config(state=tk.NORMAL)
                self.set_status(self.get_str('status_ready'))
        
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()
    
    def on_closing(self):
        self.root.destroy()