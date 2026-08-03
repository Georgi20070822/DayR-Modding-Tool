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
import webbrowser
import configparser
import importlib.util
import ctypes
from ctypes import wintypes
from PIL import Image, ImageTk
import zipfile
from datetime import datetime
import tempfile

# ======================================================
# ====   Функции для работы с встроенными ресурсами ====
# ======================================================

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        return os.path.join(os.path.dirname(__file__), relative_path)

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
# ====   Работа со шрифтами                        ====
# ======================================================

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
# ====   Работа с инструментами (tools)            ====
# ======================================================

def ensure_tools(project_dir):
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

def import_module_from_file(filepath, module_name):
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# ======================================================
# ====   Языковые строки (русский и английский)    ====
# ======================================================

VERSION = "0.0.2"
LANGUAGES = {
    'ru': {
        'title': f'Day R Моддинг (версия {VERSION}) - GUI',
        'choose_project': 'Выбрать папку проекта',
        'project_folder': 'Папка проекта:',
        'tools_folder': 'Папка с утилитами (tools):',
        'unpack': 'Распаковать resource.car',
        'decompile_all': 'Декомпилировать все .lu → .lua',
        'compile_all': 'Скомпилировать все .lua → .lu (НЕ ИСПОЛЬЗОВАТЬ!)',
        'pack': 'Упаковать resource.car (мод)',
        'compile_one': 'Скомпилировать один .lua (выбрать)',
        'decompile_one': 'Декомпилировать один .lu (выбрать)',
        'file_manager': 'Менеджер файлов',
        'open_mod_scripts': 'Открыть папку mod_scripts',
        'clean_project': 'Очистить проект',
        'choose_car': 'Выбрать resource.car',
        'log': 'Лог операций:',
        'clear_log': 'Очистить лог',
        'save_log': 'Сохранить логи',
        'status_ready': 'Готов',
        'status_running': 'Выполняется...',
        'err_no_project': 'Сначала выберите папку проекта!',
        'err_no_resource': 'Файл resource.car не выбран или не существует.',
        'success_unpack': 'Распаковка завершена. Оригиналы .lu в original_scripts/',
        'success_decompile': 'Декомпиляция завершена. .lua файлы в mod_scripts/',
        'success_compile': 'Компиляция завершена. .lu файлы в modded_lu/',
        'success_pack': 'Упаковка завершена. resource.car сохранён.',
        'choose_lua': 'Выберите .lua файл для компиляции',
        'choose_lu': 'Выберите .lu файл для декомпиляции',
        'file_not_found': 'Файл не найден',
        'decompile_one_done': 'Декомпиляция выполнена, исходный .lu удалён',
        'compile_one_done': 'Компиляция выполнена, создан .lu',
        'error_occurred': 'Ошибка выполнения! Смотрите лог.',
        'tools_ready': 'Инструменты готовы:',
        'clean_confirm': 'Вы уверены, что хотите удалить все рабочие папки (original_scripts, mod_scripts, modded_lu, packed_mod)?\nЭто действие необратимо!',
        'clean_success': 'Проект очищен. Осталась только папка resources с resource.car.',
        'pack_save_as': 'Сохранить resource.car как...',
        'pack_default': 'packed_mod/resource.car',
        'open_file_error': 'Не удалось открыть файл',
        'file_list_title': 'Список файлов для редактирования',
        'edit_btn': 'Открыть',
        'build_btn': 'Собрать',
        'show_hash': 'Хеш',
        'hash_title': 'SHA-1 хеш файла',
        'hash_empty': 'Файл пуст',
        'hash_error': 'Ошибка при вычислении хеша',
        'no_files': 'Нет файлов .lua в mod_scripts. Сначала выполните декомпиляцию.',
        'build_success': 'Файл успешно скомпилирован в .lu и помещён в modded_lu',
        'choose_car_title': 'Выберите resource.car',
        'use_saved_path': 'Использовать сохранённый путь?',
        'car_selected': 'Выбран resource.car:',
        'car_not_selected': 'Файл не выбран',
        'reset_scripts': 'Сбросить mod_scripts',
        'clear_modded': 'Очистить modded_lu',
        'reset_confirm': 'Это удалит папку mod_scripts и пересоздаст её из оригинальных .lu файлов. Продолжить?',
        'clear_modded_confirm': 'Это удалит все скомпилированные .lu файлы из modded_lu. Продолжить?',
        'help_btn': 'Помощь',
        'settings_btn': 'Настройки',
        'file_info': 'Инфо файлы',
        'search': 'Поиск:',
        'settings_title': 'Настройки',
        'font_label': 'Выберите шрифт:',
        'font_classic': 'Классический',
        'font_ro': 'RO.ttf (Red October)',
        'font_freemono': 'freemono.ttf',
        'font_russo': 'russo_one.ttf',
        'font_missing': 'Файл шрифта отсутствует. Поместите файл в папку font.',
        'font_folder': 'Открыть папку с шрифтами',
        'font_saved': 'Настройки сохранены. Перезапустите программу для применения шрифта.',
        'help_not_found': 'Инструкция не найдена. Проверьте файл {0} в папке resources/text/.',
        'info_not_found': 'Описание файлов не найдено. Проверьте файл {0} в папке resources/text/.',
        'log_saved': 'Лог сохранён в {0}',
        'log_empty': 'Лог пуст.',
        'install_btn': 'Установить',
        'install_success': 'Шрифт {0} установлен!\nПерезапустите программу для применения.',
        'install_fail': 'Не удалось установить шрифт:\n{0}',
        'admin_required_title': 'Недостаточно прав',
        'admin_required_message': 'Для корректной работы программы требуются права администратора.\nПерезапустить программу с правами администратора?',
        'console_title': 'Lua-консоль',
        'console_input_label': 'Введите код Lua (можно несколько строк):',
        'console_run_btn': 'Выполнить',
        'console_clear_btn': 'Очистить вывод',
        'console_ready': 'Lua-консоль готова. Введите код и нажмите \'Выполнить\' или Ctrl+Enter.\n\n',
        'console_executing': '>>> Выполнение кода:\n{0}\n',
        'console_result': 'Результат:\n{0}\n\n',
        'console_empty': 'Результат: (пусто)\n\n',
        'console_timeout': '[Timeout] Превышено время выполнения (10 сек)\n\n',
        'console_error': '>>> Ошибка: {0}\n\n',
        'editor_save': 'Сохранить',
        'editor_save_compile': 'Сохранить и скомпилировать',
        'editor_close': 'Закрыть',
        'editor_saved': 'Файл сохранён',
        'editor_compiled': 'Файл скомпилирован и сохранён в modded_lu',
        'file_manager_no_mod_scripts': 'Папка mod_scripts не найдена. Сначала выполните декомпиляцию.',
        'file_hash_label': 'Файл: {0}',
        'file_hash_value': 'SHA-1: {0}',
        'profile_manager_title': 'Управление профилями',
        'profile_list_label': 'Профили:',
        'profile_create_btn': 'Создать профиль',
        'profile_edit_btn': 'Изменить профиль',
        'profile_select_btn': 'Выбрать профиль',
        'profile_delete_btn': 'Удалить профиль',
        'profile_export_btn': 'Экспортировать',
        'profile_import_btn': 'Импортировать',
        'profile_create_title': 'Создание профиля',
        'profile_edit_title': 'Редактирование профиля',
        'profile_name_label': 'Название профиля:',
        'profile_desc_label': 'Описание:',
        'profile_path_label': 'Папка проекта:',
        'profile_save_btn': 'Сохранить',
        'profile_select_first': 'Сначала выберите профиль',
        'profile_delete_confirm': 'Удалить профиль \'{0}\' и все его файлы?',
        'profile_path_not_exists': 'Папка проекта не существует',
        'profile_exported': 'Профиль экспортирован в:\n{0}',
        'profile_imported': 'Профиль импортирован:\n{0}',
        'profile_name_required': 'Введите название профиля',
        'profile_path_required': 'Укажите существующую папку проекта',
        'profile_name_empty': 'Введите название',
        'profile_path_empty': 'Укажите существующую папку',
        'profile_imported_from': 'Импортирован из {0}',
    },
    'en': {
        'title': f'Day R Modding (version {VERSION}) - GUI',
        'choose_project': 'Choose Project Folder',
        'project_folder': 'Project Folder:',
        'tools_folder': 'Tools Folder:',
        'unpack': 'Unpack resource.car',
        'decompile_all': 'Decompile all .lu → .lua',
        'compile_all': 'Compile all .lua → .lu (DO NOT USE!)',
        'pack': 'Pack resource.car (mod)',
        'compile_one': 'Compile one .lua (choose)',
        'decompile_one': 'Decompile one .lu (choose)',
        'file_manager': 'File Manager',
        'open_mod_scripts': 'Open mod_scripts folder',
        'clean_project': 'Clean Project',
        'choose_car': 'Choose resource.car',
        'log': 'Operation log:',
        'clear_log': 'Clear log',
        'save_log': 'Save log',
        'status_ready': 'Ready',
        'status_running': 'Running...',
        'err_no_project': 'Please select the project folder first!',
        'err_no_resource': 'Resource.car file not selected or does not exist.',
        'success_unpack': 'Unpack complete. Original .lu files in original_scripts/',
        'success_decompile': 'Decompile complete. .lua files in mod_scripts/',
        'success_compile': 'Compile complete. .lu files in modded_lu/',
        'success_pack': 'Pack complete. resource.car saved.',
        'choose_lua': 'Choose a .lua file to compile',
        'choose_lu': 'Choose a .lu file to decompile',
        'file_not_found': 'File not found',
        'decompile_one_done': 'Decompile done, original .lu deleted',
        'compile_one_done': 'Compile done, .lu created',
        'error_occurred': 'Execution error! Check the log.',
        'tools_ready': 'Tools ready:',
        'clean_confirm': 'Are you sure you want to delete all working folders (original_scripts, mod_scripts, modded_lu, packed_mod)?\nThis action is irreversible!',
        'clean_success': 'Project cleaned. Only resources folder with resource.car remains.',
        'pack_save_as': 'Save resource.car as...',
        'pack_default': 'packed_mod/resource.car',
        'open_file_error': 'Could not open file',
        'file_list_title': 'File list for editing',
        'edit_btn': 'Open',
        'build_btn': 'Build',
        'show_hash': 'Hash',
        'hash_title': 'SHA-1 hash of file',
        'hash_empty': 'File is empty',
        'hash_error': 'Error computing hash',
        'no_files': 'No .lua files in mod_scripts. Run decompilation first.',
        'build_success': 'File successfully compiled to .lu and placed in modded_lu',
        'choose_car_title': 'Choose resource.car',
        'use_saved_path': 'Use saved path?',
        'car_selected': 'Selected resource.car:',
        'car_not_selected': 'File not selected',
        'reset_scripts': 'Reset mod_scripts',
        'clear_modded': 'Clear modded_lu',
        'reset_confirm': 'This will delete mod_scripts and recreate it from original .lu files. Continue?',
        'clear_modded_confirm': 'This will delete all compiled .lu files from modded_lu. Continue?',
        'help_btn': 'Help',
        'settings_btn': 'Settings',
        'file_info': 'File info',
        'search': 'Search:',
        'settings_title': 'Settings',
        'font_label': 'Select font:',
        'font_classic': 'Classic',
        'font_ro': 'RO.ttf (Red October)',
        'font_freemono': 'freemono.ttf',
        'font_russo': 'russo_one.ttf',
        'font_missing': 'Font file missing. Place the file in font folder.',
        'font_folder': 'Open font folder',
        'font_saved': 'Settings saved. Restart the program to apply font.',
        'help_not_found': 'Help file not found. Check {0} in resources/text/.',
        'info_not_found': 'File info not found. Check {0} in resources/text/.',
        'log_saved': 'Log saved to {0}',
        'log_empty': 'Log is empty.',
        'install_btn': 'Install',
        'install_success': 'Font {0} installed!\nRestart the program to apply.',
        'install_fail': 'Failed to install font:\n{0}',
        'admin_required_title': 'Admin rights required',
        'admin_required_message': 'Administrator rights are required for the program to work correctly.\nRestart the program with administrator rights?',
        'console_title': 'Lua Console',
        'console_input_label': 'Enter Lua code (multiple lines allowed):',
        'console_run_btn': 'Run',
        'console_clear_btn': 'Clear output',
        'console_ready': 'Lua console ready. Enter code and press \'Run\' or Ctrl+Enter.\n\n',
        'console_executing': '>>> Executing code:\n{0}\n',
        'console_result': 'Result:\n{0}\n\n',
        'console_empty': 'Result: (empty)\n\n',
        'console_timeout': '[Timeout] Execution time exceeded (10 sec)\n\n',
        'console_error': '>>> Error: {0}\n\n',
        'editor_save': 'Save',
        'editor_save_compile': 'Save and compile',
        'editor_close': 'Close',
        'editor_saved': 'File saved',
        'editor_compiled': 'File compiled and saved to modded_lu',
        'file_manager_no_mod_scripts': 'mod_scripts folder not found. Run decompilation first.',
        'file_hash_label': 'File: {0}',
        'file_hash_value': 'SHA-1: {0}',
        'profile_manager_title': 'Profile Manager',
        'profile_list_label': 'Profiles:',
        'profile_create_btn': 'Create Profile',
        'profile_edit_btn': 'Edit Profile',
        'profile_select_btn': 'Select Profile',
        'profile_delete_btn': 'Delete Profile',
        'profile_export_btn': 'Export',
        'profile_import_btn': 'Import',
        'profile_create_title': 'Create Profile',
        'profile_edit_title': 'Edit Profile',
        'profile_name_label': 'Profile Name:',
        'profile_desc_label': 'Description:',
        'profile_path_label': 'Project Folder:',
        'profile_save_btn': 'Save',
        'profile_select_first': 'Select a profile first',
        'profile_delete_confirm': 'Delete profile \'{0}\' and all its files?',
        'profile_path_not_exists': 'Project folder does not exist',
        'profile_exported': 'Profile exported to:\n{0}',
        'profile_imported': 'Profile imported:\n{0}',
        'profile_name_required': 'Enter profile name',
        'profile_path_required': 'Specify existing project folder',
        'profile_name_empty': 'Enter a name',
        'profile_path_empty': 'Specify existing folder',
        'profile_imported_from': 'Imported from {0}',
    }
}

COLORS = {
    'bg': '#2b2b2b',
    'bg_dark': '#1e1e1e',
    'bg_input': '#3c3c3c',
    'fg': '#eeeeee',
    'fg_white': '#ffffff',
    'accent': '#88ccff',
    'warning': '#ffcc00',
    'error': '#ff4444',
    'success': '#44ff88'
}

# ======================================================
# ====   Основной класс приложения                  ====
# ======================================================

class ModdingGUI:
    def __init__(self, root):
        self.root = root
        self.root.iconbitmap(default=resource_path('icon.ico'))
        self.root.configure(bg=COLORS['bg'])
        self.lang = 'ru'
        self.project_dir = tk.StringVar()
        self.tools_dir = tk.StringVar()
        self.status_var = tk.StringVar()
        self.resource_car_path = None

        self.click_sound_path = resource_path('sounds/clicking.wav')

        self.BUTTON_HEIGHT = 40
        self.BUTTON_WIDTH = 280

        btn_normal_img = Image.open(resource_path('images/button_1.png'))
        btn_pressed_img = Image.open(resource_path('images/button_2.png'))
        q_img = Image.open(resource_path('images/question.png'))
        q_img = q_img.resize((24, 24), Image.Resampling.LANCZOS)
        self.question_icon = ImageTk.PhotoImage(q_img)

        settings_img_path = resource_path('images/settings.png')
        if os.path.exists(settings_img_path):
            settings_img = Image.open(settings_img_path)
            settings_img = settings_img.resize((24, 24), Image.Resampling.LANCZOS)
            self.settings_icon = ImageTk.PhotoImage(settings_img)
        else:
            self.settings_icon = None

        profile_img_path = resource_path('images/profile.png')
        if os.path.exists(profile_img_path):
            profile_img = Image.open(profile_img_path)
            profile_img = profile_img.resize((24, 24), Image.Resampling.LANCZOS)
            self.profile_icon = ImageTk.PhotoImage(profile_img)
        else:
            self.profile_icon = None

        def resize_stretch(img, target_width, target_height):
            return img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        self.btn_normal_img = resize_stretch(btn_normal_img, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.btn_pressed_img = resize_stretch(btn_pressed_img, self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.btn_normal = ImageTk.PhotoImage(self.btn_normal_img)
        self.btn_pressed = ImageTk.PhotoImage(self.btn_pressed_img)

        self.font_name = self._get_font_name()
        self.button_font = self._load_font(self.font_name)

        self.setup_ui()
        self.update_all_texts()

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

    def setup_ui(self):
        self.root.geometry('1100x720')
        self.root.resizable(True, True)

        lang_frame = tk.Frame(self.root, bg=COLORS['bg'])
        lang_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(lang_frame, text='Язык / Language:', fg='white', bg=COLORS['bg']).pack(side=tk.LEFT)
        self.lang_combo = ttk.Combobox(lang_frame, values=('ru', 'en'), state='readonly', width=5)
        self.lang_combo.set('ru')
        self.lang_combo.pack(side=tk.LEFT, padx=5)
        self.lang_combo.bind('<<ComboboxSelected>>', lambda e: self.update_all_texts())

        if self.profile_icon:
            self.btn_profile = tk.Button(lang_frame, image=self.profile_icon, command=self.open_profile_manager,
                                         relief='flat', borderwidth=0, bg=COLORS['bg'], activebackground=COLORS['bg'])
        else:
            self.btn_profile = tk.Button(lang_frame, text="📁", font=('Segoe UI', 14),
                                         command=self.open_profile_manager, relief='flat', borderwidth=0,
                                         bg=COLORS['bg'], fg='white', activebackground=COLORS['bg'], activeforeground='white')
        self.btn_profile.pack(side=tk.RIGHT, padx=2)

        if self.settings_icon:
            self.btn_settings = tk.Button(lang_frame, image=self.settings_icon, command=self.open_settings,
                                          relief='flat', borderwidth=0, bg=COLORS['bg'], activebackground=COLORS['bg'])
        else:
            self.btn_settings = tk.Button(lang_frame, text="⚙️", font=('Segoe UI', 14),
                                          command=self.open_settings, relief='flat', borderwidth=0,
                                          bg=COLORS['bg'], fg='white', activebackground=COLORS['bg'], activeforeground='white')
        self.btn_settings.pack(side=tk.RIGHT, padx=2)

        self.btn_help = tk.Button(lang_frame, image=self.question_icon, command=self.show_help,
                                  relief='flat', borderwidth=0, bg=COLORS['bg'], activebackground=COLORS['bg'])
        self.btn_help.pack(side=tk.RIGHT, padx=2)

        proj_frame = tk.Frame(self.root, bg=COLORS['bg'])
        proj_frame.pack(fill=tk.X, padx=5, pady=5)

        self.label_project = tk.Label(proj_frame, text="", fg='white', bg=COLORS['bg'])
        self.label_project.pack(side=tk.LEFT)
        tk.Entry(proj_frame, textvariable=self.project_dir, width=50,
                 bg=COLORS['bg_input'], fg='white', insertbackground='white',
                 relief='flat').pack(side=tk.LEFT, padx=5)

        self.browse_btn = self._create_styled_button(proj_frame, self.browse_project)
        self.btn_open_scripts = self._create_styled_button(proj_frame, self.open_mod_scripts_folder)

        btn_frame = tk.Frame(self.root, bg=COLORS['bg'])
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        row1 = tk.Frame(btn_frame, bg=COLORS['bg'])
        row1.pack(fill=tk.X, pady=2)
        self.btn_unpack = self._create_styled_button(row1, self.run_unpack)
        self.btn_decompile_all = self._create_styled_button(row1, self.run_decompile_all)
        self.btn_compile_all = self._create_styled_button(row1, self.run_compile_all, fg='darkred')

        row2 = tk.Frame(btn_frame, bg=COLORS['bg'])
        row2.pack(fill=tk.X, pady=2)
        self.btn_pack = self._create_styled_button(row2, self.run_pack)
        self.btn_clean = self._create_styled_button(row2, self.clean_project, fg='darkred')
        self.btn_file_manager = self._create_styled_button(row2, self.open_file_manager)

        row3 = tk.Frame(btn_frame, bg=COLORS['bg'])
        row3.pack(fill=tk.X, pady=2)
        self.btn_compile_one = self._create_styled_button(row3, self.run_compile_one)
        self.btn_decompile_one = self._create_styled_button(row3, self.run_decompile_one)
        self.btn_choose_car = self._create_styled_button(row3, self.choose_resource_car)

        row4 = tk.Frame(btn_frame, bg=COLORS['bg'])
        row4.pack(fill=tk.X, pady=2)
        self.btn_reset_scripts = self._create_styled_button(row4, self.reset_mod_scripts, fg='darkblue')
        self.btn_clear_modded = self._create_styled_button(row4, self.clear_modded_lu, fg='darkred')
        self.btn_console = self._create_styled_button(row4, self.open_console, text='', font=self.button_font)

        log_frame = tk.Frame(self.root, bg=COLORS['bg'])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.label_log = tk.Label(log_frame, text="", fg='white', bg=COLORS['bg'])
        self.label_log.pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='normal', height=18,
                                                  bg=COLORS['bg_dark'], fg=COLORS['fg'], insertbackground='white',
                                                  highlightthickness=0, borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        bottom_frame = tk.Frame(self.root, bg=COLORS['bg'])
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)

        self.status_label = tk.Label(bottom_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W,
                                     bg=COLORS['bg_input'], fg='white')
        self.status_var.set('')
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.save_log_btn = self._create_styled_button(bottom_frame, self.save_log)
        self.clear_btn = self._create_styled_button(bottom_frame, self.clear_log)

        self.tools_dir.set('')

    def _create_styled_button(self, parent, command, text='', fg='black', compound='center', font=None):
        if font is None:
            font = self.button_font
        btn = tk.Button(parent, image=self.btn_normal, compound=compound, text=text,
                        fg=fg, font=font, relief='flat', borderwidth=0,
                        bg='#2b2b2b', activebackground='#2b2b2b', command=command)
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
        btn.pack(side=tk.LEFT, padx=2, pady=2)
        return btn
    # ===== Методы для работы с текстами и обновления =====
    def get_str(self, key, *args):
        text = LANGUAGES[self.lang].get(key, key)
        if args:
            return text.format(*args)
        return text

    def update_all_texts(self):
        self.lang = self.lang_combo.get()
        self.root.title(self.get_str('title'))
        self.label_project.config(text=self.get_str('project_folder'))
        self.browse_btn.config(text=self.get_str('choose_project'))
        self.btn_open_scripts.config(text=self.get_str('open_mod_scripts'))
        self.label_log.config(text=self.get_str('log'))
        self.save_log_btn.config(text=self.get_str('save_log'))
        self.clear_btn.config(text=self.get_str('clear_log'))
        self.btn_unpack.config(text=self.get_str('unpack'))
        self.btn_decompile_all.config(text=self.get_str('decompile_all'))
        self.btn_compile_all.config(text=self.get_str('compile_all'))
        self.btn_pack.config(text=self.get_str('pack'))
        self.btn_clean.config(text=self.get_str('clean_project'))
        self.btn_file_manager.config(text=self.get_str('file_manager'))
        self.btn_choose_car.config(text=self.get_str('choose_car'))
        self.btn_compile_one.config(text=self.get_str('compile_one'))
        self.btn_decompile_one.config(text=self.get_str('decompile_one'))
        self.btn_reset_scripts.config(text=self.get_str('reset_scripts'))
        self.btn_clear_modded.config(text=self.get_str('clear_modded'))
        self.btn_console.config(text=self.get_str('console_title'))
        self.status_var.set(self.get_str('status_ready'))

    def log(self, message):
        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, message + '\n')
            self.log_text.see(tk.END)
            self.root.update_idletasks()

    def set_status(self, text):
        self.status_var.set(text)
        self.root.update_idletasks()

    def disable_buttons(self, disabled):
        state = tk.DISABLED if disabled else tk.NORMAL
        for widget in [self.btn_unpack, self.btn_decompile_all, self.btn_compile_all,
                       self.btn_pack, self.btn_clean, self.btn_file_manager,
                       self.btn_open_scripts,
                       self.btn_compile_one, self.btn_decompile_one,
                       self.btn_choose_car, self.browse_btn, self.clear_btn,
                       self.btn_reset_scripts, self.btn_clear_modded,
                       self.btn_console, self.save_log_btn, self.btn_help, self.btn_settings, self.btn_profile]:
            widget.config(state=state)

    def run_in_thread(self, target):
        if not self.tools_dir.get():
            messagebox.showerror("Error", self.get_str('err_no_project'))
            return
        self.set_status(self.get_str('status_running'))
        self.disable_buttons(True)

        def wrapper():
            try:
                target()
            except Exception as e:
                self.log(f"Ошибка в потоке: {e}")
                import traceback
                self.log(traceback.format_exc())
                messagebox.showerror("Error", str(e))
            finally:
                self.disable_buttons(False)
                self.set_status(self.get_str('status_ready'))

        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()

    # ==========================================================
    # ====   Работа с проектом и папками                   ====
    # ==========================================================

    def browse_project(self):
        folder = filedialog.askdirectory(title=self.get_str('choose_project'))
        if folder:
            self.project_dir.set(folder)
            try:
                tools_path = ensure_tools(folder)
                self.tools_dir.set(tools_path)
                self.log(f"Папка проекта: {folder}")
                self.log(f"{self.get_str('tools_ready')} {tools_path}")
            except Exception as e:
                self.log(f"Ошибка при подготовке tools: {e}")
                messagebox.showerror("Error", f"Не удалось распаковать инструменты: {e}")

    def choose_resource_car(self):
        file_path = filedialog.askopenfilename(
            title=self.get_str('choose_car_title'),
            filetypes=[("Corona Archive", "*.car"), ("All files", "*.*")]
        )
        if file_path:
            self.resource_car_path = file_path
            self.log(f"{self.get_str('car_selected')} {file_path}")
            messagebox.showinfo("Success", f"{self.get_str('car_selected')}\n{file_path}")

    def run_unpack(self):
        if not self.resource_car_path:
            self.choose_resource_car()
        if not self.resource_car_path:
            return
        self.run_in_thread(self._unpack_thread)

    def _unpack_thread(self):
        try:
            self.log("=== Распаковка resource.car ===")
            if not self.resource_car_path or not os.path.exists(self.resource_car_path):
                self.log("ОШИБКА: файл resource.car не выбран или не существует!")
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
                self.log("ВНИМАНИЕ: папка _temp_extract пуста. Ищем .lu файлы в корне проекта...")
                root_files = [f for f in os.listdir(self.project_dir.get()) if f.endswith('.lu')]
                if root_files:
                    for file in root_files:
                        src = os.path.join(self.project_dir.get(), file)
                        dst = os.path.join(original_scripts, file)
                        shutil.move(src, dst)
                        self.log(f"Перемещён: {file}")
                    shutil.rmtree(extract_dir)
                    self.log(f"Распаковано {len(root_files)} .lu файлов")
                    self.log(self.get_str('success_unpack'))
                    return
                else:
                    self.log("Не найдено .lu файлов ни в _temp_extract, ни в корне проекта.")
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
            self.log(f"Распаковано {count} .lu файлов")
            self.log(self.get_str('success_unpack'))
        except Exception as e:
            self.log(f"Исключение: {e}")
            import traceback
            self.log(traceback.format_exc())

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
            self.log(f"=== Упаковка resource.car в {output_car} ===")
            packed_mod_dir = os.path.dirname(output_car)
            os.makedirs(packed_mod_dir, exist_ok=True)
            temp_dir = os.path.join(packed_mod_dir, '_temp_pack')
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)

            original_scripts = os.path.join(self.project_dir.get(), 'original_scripts')
            if not os.path.exists(original_scripts):
                self.log("ОШИБКА: original_scripts не найдена. Сначала распакуйте resource.car.")
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
                            self.log(f"Заменён модифицированный: {rel_path}")
            else:
                self.log("ВНИМАНИЕ: modded_lu пуста, упаковываются только оригиналы.")

            corona_script = os.path.join(self.tools_dir.get(), 'corona-archiver.py')
            corona = import_module_from_file(corona_script, 'corona_archiver')
            archiver = corona.CoronaArchiver()
            archiver.pack(temp_dir + os.sep, output_car)

            shutil.rmtree(temp_dir)
            self.log(f"Готово! resource.car сохранён в {output_car}")
            self.log(self.get_str('success_pack'))
        except Exception as e:
            self.log(f"Исключение: {e}")
            import traceback
            self.log(traceback.format_exc())

    def run_decompile_all(self):
        self.run_in_thread(self._decompile_all_thread)

    def _decompile_all_thread(self):
        try:
            self.log("=== Декомпиляция всех .lu ===")
            original_scripts = os.path.join(self.project_dir.get(), 'original_scripts')
            if not os.path.exists(original_scripts):
                self.log("Папка original_scripts не найдена. Сначала распакуйте resource.car.")
                return
            mod_scripts = os.path.join(self.project_dir.get(), 'mod_scripts')
            if os.path.exists(mod_scripts):
                shutil.rmtree(mod_scripts)
            os.makedirs(mod_scripts, exist_ok=True)
            decompiler = os.path.join(self.tools_dir.get(), 'dr_decompiler_windows.exe')
            if not os.path.exists(decompiler):
                self.log("dr_decompiler_windows.exe не найден!")
                return

            lu_files = []
            for root, dirs, files in os.walk(original_scripts):
                for file in files:
                    if file.endswith('.lu'):
                        lu_files.append(os.path.join(root, file))

            if not lu_files:
                self.log("Нет .lu файлов для декомпиляции.")
                return

            total = len(lu_files)
            failed = []
            for idx, lu_path in enumerate(lu_files):
                rel_path = os.path.relpath(lu_path, original_scripts)
                lua_name = os.path.splitext(rel_path)[0] + '.lua'
                lua_path = os.path.join(mod_scripts, lua_name)
                os.makedirs(os.path.dirname(lua_path), exist_ok=True)
                cmd = [decompiler, lu_path]
                self.log(f"[{idx+1}/{total}] Декомпиляция: {rel_path}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    self.log(f"Ошибка декомпиляции {rel_path}")
                    self.log(result.stderr)
                    failed.append(rel_path)
                else:
                    output = result.stdout if result.stdout is not None else ""
                    if output.strip():
                        with open(lua_path, 'w', encoding='utf-8') as f_out:
                            f_out.write(output)
                    else:
                        self.log(f"Декомпиляция {rel_path} не дала результата (пустой вывод)")
                        failed.append(rel_path)

            if failed:
                self.log(f"Не удалось декомпилировать {len(failed)} файлов: {', '.join(failed)}")
            else:
                self.log(self.get_str('success_decompile'))
                messagebox.showinfo("Success", self.get_str('success_decompile'))
        except Exception as e:
            self.log(f"Исключение: {e}")

    def run_compile_all(self):
        if not self.project_dir.get():
            return
        if messagebox.askyesno("ВНИМАНИЕ", "Массовая компиляция всех .lua файлов может сломать игру!\nПродолжить?"):
            self.run_in_thread(self._compile_all_thread)

    def _compile_all_thread(self):
        try:
            self.log("=== МАССОВАЯ КОМПИЛЯЦИЯ (ПРЕДУПРЕЖДЕНИЕ) ===")
            mod_scripts = os.path.join(self.project_dir.get(), 'mod_scripts')
            if not os.path.exists(mod_scripts):
                self.log("Папка mod_scripts не найдена. Сначала декомпилируйте.")
                return
            modded_lu = os.path.join(self.project_dir.get(), 'modded_lu')
            if os.path.exists(modded_lu):
                shutil.rmtree(modded_lu)
            os.makedirs(modded_lu, exist_ok=True)
            luac = os.path.join(self.tools_dir.get(), 'luac.exe')
            if not os.path.exists(luac):
                self.log("luac.exe не найден!")
                return

            lua_files = []
            for root, dirs, files in os.walk(mod_scripts):
                for file in files:
                    if file.endswith('.lua'):
                        lua_files.append(os.path.join(root, file))
            if not lua_files:
                self.log("Нет .lua файлов для компиляции.")
                return

            total = len(lua_files)
            for idx, lua_path in enumerate(lua_files):
                rel_path = os.path.relpath(lua_path, mod_scripts)
                lu_name = os.path.splitext(rel_path)[0] + '.lu'
                lu_path = os.path.join(modded_lu, lu_name)
                os.makedirs(os.path.dirname(lu_path), exist_ok=True)
                cmd = [luac, '-o', lu_path, lua_path]
                self.log(f"[{idx+1}/{total}] Компиляция: {rel_path}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    self.log(f"Ошибка компиляции {rel_path}")
                    self.log(result.stderr)
            self.log("Компиляция завершена. .lu файлы в modded_lu/")
        except Exception as e:
            self.log(f"Исключение: {e}")

    def run_compile_one(self):
        file_path = filedialog.askopenfilename(title=self.get_str('choose_lua'), filetypes=[("Lua files", "*.lua")])
        if file_path:
            self.run_in_thread(lambda: self._compile_one_thread(file_path))

    def _compile_one_thread(self, lua_path):
        try:
            self.log(f"=== Компиляция одного файла: {os.path.basename(lua_path)} ===")
            luac = os.path.join(self.tools_dir.get(), 'luac.exe')
            if not os.path.exists(luac):
                self.log("luac.exe не найден!")
                return
            mod_scripts = os.path.join(self.project_dir.get(), 'mod_scripts')
            if not os.path.exists(mod_scripts):
                self.log("Папка mod_scripts не найдена. Сначала декомпилируйте.")
                return
            if not lua_path.startswith(mod_scripts):
                self.log("Файл должен находиться внутри папки mod_scripts.")
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
                self.log("Ошибка компиляции!")
                self.log(result.stderr)
            else:
                self.log(f"Создан: {out_path}")
                self.log(self.get_str('compile_one_done'))
                messagebox.showinfo("Success", self.get_str('compile_one_done'))
        except Exception as e:
            self.log(f"Исключение: {e}")

    def run_decompile_one(self):
        file_path = filedialog.askopenfilename(title=self.get_str('choose_lu'), filetypes=[("Lu files", "*.lu")])
        if file_path:
            self.run_in_thread(lambda: self._decompile_one_thread(file_path))

    def _decompile_one_thread(self, lu_path):
        try:
            self.log(f"=== Декомпиляция одного файла: {os.path.basename(lu_path)} ===")
            decompiler = os.path.join(self.tools_dir.get(), 'dr_decompiler_windows.exe')
            if not os.path.exists(decompiler):
                self.log("dr_decompiler_windows.exe не найден!")
                return
            out_path = os.path.splitext(lu_path)[0] + '.lua'
            cmd = [decompiler, lu_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.log("Ошибка декомпиляции!")
                self.log(result.stderr)
                return
            output = result.stdout if result.stdout is not None else ""
            if output.strip():
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(output)
                os.remove(lu_path)
                self.log(f"Создан: {out_path}, исходный .lu удалён.")
                self.log(self.get_str('decompile_one_done'))
                messagebox.showinfo("Success", self.get_str('decompile_one_done'))
            else:
                self.log("Декомпиляция не дала результата (пустой вывод)")
        except Exception as e:
            self.log(f"Исключение: {e}")

    def clean_project(self):
        if messagebox.askyesno(self.get_str('clean_project'), self.get_str('clean_confirm')):
            self.run_in_thread(lambda: self._clean_project_thread())

    def _clean_project_thread(self):
        try:
            project = self.project_dir.get()
            for folder in ['original_scripts', 'mod_scripts', 'modded_lu', 'packed_mod']:
                path = os.path.join(project, folder)
                if os.path.exists(path):
                    shutil.rmtree(path)
                    self.log(f"Удалена папка: {path}")
            self.log(self.get_str('clean_success'))
        except Exception as e:
            self.log(f"Ошибка при очистке: {e}")

    def reset_mod_scripts(self):
        if messagebox.askyesno("Сброс", self.get_str('reset_confirm')):
            self.run_in_thread(self._reset_mod_scripts_thread)

    def _reset_mod_scripts_thread(self):
        mod_scripts = os.path.join(self.project_dir.get(), 'mod_scripts')
        if os.path.exists(mod_scripts):
            shutil.rmtree(mod_scripts)
            self.log("Папка mod_scripts удалена.")
        else:
            self.log("Папка mod_scripts не существует.")
        self._decompile_all_thread()

    def clear_modded_lu(self):
        if messagebox.askyesno("Очистка", self.get_str('clear_modded_confirm')):
            self.run_in_thread(self._clear_modded_lu_thread)

    def _clear_modded_lu_thread(self):
        modded_lu = os.path.join(self.project_dir.get(), 'modded_lu')
        if os.path.exists(modded_lu):
            shutil.rmtree(modded_lu)
            self.log("Папка modded_lu удалена.")
            messagebox.showinfo("Success", "modded_lu очищена.")
        else:
            self.log("Папка modded_lu не существует.")
            messagebox.showinfo("Info", "modded_lu уже пуста.")

    # ==========================================================
    # ====   Менеджер файлов                              ====
    # ==========================================================

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

        search_entry.bind('<KeyRelease>', lambda e: update_list(search_entry.get()))
        update_list()

    # ==========================================================
    # ====   Встроенный редактор файлов                     ====
    # ==========================================================

    def open_file_in_editor(self, file_path):
        """Открывает встроенный редактор с подсветкой синтаксиса."""
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "Файл не найден")
            return

        # Проверяем, установлен ли pygments
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

        # Основной текстовый виджет
        text_widget = tk.Text(win, wrap=tk.WORD, bg='#1e1e1e', fg='#eeeeee',
                              insertbackground='white', undo=True, font=('Courier New', 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Загружаем содержимое файла
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            text_widget.insert(tk.END, content)
        except Exception as e:
            messagebox.showerror("Error", f"Не удалось загрузить файл: {e}")
            win.destroy()
            return

        # Если pygments доступен – настраиваем подсветку
        if has_pygments:
            # Определяем цвета для токенов
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
                # Удаляем старые теги
                for token in style:
                    text_widget.tag_remove(str(token), '1.0', tk.END)
                # Получаем весь текст
                text = text_widget.get('1.0', tk.END)
                # Разбираем через pygments
                lexer = get_lexer_by_name('lua')
                tokens = list(lex(text, lexer))
                pos = 0
                for token_type, token_text in tokens:
                    if token_type in style:
                        start = f'1.0 + {pos} chars'
                        end = f'1.0 + {pos + len(token_text)} chars'
                        text_widget.tag_add(str(token_type), start, end)
                    pos += len(token_text)

            # Привязываем события для обновления подсветки
            text_widget.bind('<KeyRelease>', highlight_syntax)
            text_widget.bind('<ButtonRelease>', highlight_syntax)
            # Первоначальная подсветка
            highlight_syntax()
        else:
            # Если pygments нет – просто показываем без подсветки
            pass

        # ---- Панель кнопок ----
        btn_frame = tk.Frame(win, bg='#2b2b2b')
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        def save_file():
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_widget.get(1.0, tk.END))
                self.log(f"Файл сохранён: {file_path}")
                messagebox.showinfo("Success", self.get_str('editor_saved'))
            except Exception as e:
                messagebox.showerror("Error", f"Ошибка сохранения: {e}")

        def save_and_compile():
            # Сохраняем файл
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_widget.get(1.0, tk.END))
                self.log(f"Файл сохранён: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Ошибка сохранения: {e}")
                return
            # Компилируем (вызываем compile_single_file, который работает с модифицированным файлом)
            self.compile_single_file(file_path)

        tk.Button(btn_frame, text=self.get_str('editor_save'), command=save_file,
                  bg='#3c3c3c', fg='white', relief='flat').pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text=self.get_str('editor_save_compile'), command=save_and_compile,
                  bg='#3c3c3c', fg='white', relief='flat').pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text=self.get_str('editor_close'), command=win.destroy,
                  bg='#3c3c3c', fg='white', relief='flat').pack(side=tk.RIGHT, padx=2)

    # ==========================================================
    # ====   Хеш и информация о файлах                     ====
    # ==========================================================

    def show_file_hash(self, file_path):
        try:
            if not os.path.exists(file_path):
                messagebox.showerror("Error", "File not found")
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

    # ==========================================================
    # ====   Консоль                                       ====
    # ==========================================================

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

    # ==========================================================
    # ====   Профили                                       ====
    # ==========================================================

    def open_profile_manager(self):
        win = tk.Toplevel(self.root)
        win.title(self.get_str('profile_manager_title'))
        win.geometry("600x500")
        win.configure(bg='#2b2b2b')
        win.resizable(False, False)
        win.lift()
        win.focus_force()

        tk.Label(win, text=self.get_str('profile_list_label'), fg='white', bg='#2b2b2b', font=('Segoe UI', 12)).pack(pady=5)
        listbox = tk.Listbox(win, bg='#3c3c3c', fg='white', selectmode=tk.SINGLE, height=10)
        listbox.pack(fill=tk.X, padx=10, pady=5)

        profiles = self._load_profiles()
        for name, data in profiles.items():
            listbox.insert(tk.END, f"{name} ({data.get('project_path', '')})")

        def get_selected_profile():
            selection = listbox.curselection()
            if not selection:
                messagebox.showinfo("Info", self.get_str('profile_select_first'))
                return None
            full = listbox.get(selection[0])
            return full.split(' (')[0]

        def create_profile():
            create_win = tk.Toplevel(win)
            create_win.title(self.get_str('profile_create_title'))
            create_win.geometry("400x300")
            create_win.configure(bg='#2b2b2b')
            create_win.resizable(False, False)

            tk.Label(create_win, text=self.get_str('profile_name_label'), fg='white', bg='#2b2b2b').pack(pady=5)
            name_entry = tk.Entry(create_win, bg='#3c3c3c', fg='white', insertbackground='white', width=40)
            name_entry.pack(pady=5)

            tk.Label(create_win, text=self.get_str('profile_desc_label'), fg='white', bg='#2b2b2b').pack(pady=5)
            desc_entry = tk.Entry(create_win, bg='#3c3c3c', fg='white', insertbackground='white', width=40)
            desc_entry.pack(pady=5)

            tk.Label(create_win, text=self.get_str('profile_path_label'), fg='white', bg='#2b2b2b').pack(pady=5)
            project_entry = tk.Entry(create_win, bg='#3c3c3c', fg='white', insertbackground='white', width=40)
            project_entry.pack(pady=5)
            project_entry.insert(0, self.project_dir.get() if self.project_dir.get() else self.get_str('profile_path_not_exists'))

            def save_profile_action():
                name = name_entry.get().strip()
                desc = desc_entry.get().strip()
                project_path = project_entry.get().strip()
                if not name:
                    messagebox.showerror("Error", self.get_str('profile_name_required'))
                    return
                if not project_path or not os.path.exists(project_path):
                    messagebox.showerror("Error", self.get_str('profile_path_required'))
                    return
                self._save_profile(name, desc, project_path)
                create_win.destroy()
                win.destroy()
                self.open_profile_manager()

            tk.Button(create_win, text=self.get_str('profile_save_btn'), command=save_profile_action, bg='#3c3c3c', fg='white', relief='flat').pack(pady=10)

        def edit_profile():
            name = get_selected_profile()
            if not name:
                return
            profiles = self._load_profiles()
            if name not in profiles:
                return
            data = profiles[name]

            edit_win = tk.Toplevel(win)
            edit_win.title(self.get_str('profile_edit_title'))
            edit_win.geometry("400x300")
            edit_win.configure(bg='#2b2b2b')
            edit_win.resizable(False, False)

            tk.Label(edit_win, text=self.get_str('profile_name_label'), fg='white', bg='#2b2b2b').pack(pady=5)
            name_entry = tk.Entry(edit_win, bg='#3c3c3c', fg='white', insertbackground='white', width=40)
            name_entry.insert(0, name)
            name_entry.pack(pady=5)

            tk.Label(edit_win, text=self.get_str('profile_desc_label'), fg='white', bg='#2b2b2b').pack(pady=5)
            desc_entry = tk.Entry(edit_win, bg='#3c3c3c', fg='white', insertbackground='white', width=40)
            desc_entry.insert(0, data.get('description', ''))
            desc_entry.pack(pady=5)

            tk.Label(edit_win, text=self.get_str('profile_path_label'), fg='white', bg='#2b2b2b').pack(pady=5)
            project_entry = tk.Entry(edit_win, bg='#3c3c3c', fg='white', insertbackground='white', width=40)
            project_entry.insert(0, data.get('project_path', ''))
            project_entry.pack(pady=5)

            def save_edit_action():
                new_name = name_entry.get().strip()
                new_desc = desc_entry.get().strip()
                new_path = project_entry.get().strip()
                if not new_name:
                    messagebox.showerror("Error", self.get_str('profile_name_empty'))
                    return
                if not new_path or not os.path.exists(new_path):
                    messagebox.showerror("Error", self.get_str('profile_path_empty'))
                    return
                self._delete_profile(name)
                self._save_profile(new_name, new_desc, new_path)
                edit_win.destroy()
                win.destroy()
                self.open_profile_manager()

            tk.Button(edit_win, text=self.get_str('profile_save_btn'), command=save_edit_action, bg='#3c3c3c', fg='white', relief='flat').pack(pady=10)

        def select_profile():
            name = get_selected_profile()
            if not name:
                return
            profiles = self._load_profiles()
            if name not in profiles:
                return
            data = profiles[name]
            project_path = data.get('project_path')
            if not project_path or not os.path.exists(project_path):
                messagebox.showerror("Error", self.get_str('profile_path_not_exists'))
                return
            self.project_dir.set(project_path)
            try:
                tools_path = ensure_tools(project_path)
                self.tools_dir.set(tools_path)
                self.log(f"Выбран профиль: {name}")
                self.log(f"Папка проекта: {project_path}")
                self.log(f"Инструменты готовы: {tools_path}")
            except Exception as e:
                self.log(f"Ошибка при загрузке профиля: {e}")
                messagebox.showerror("Error", str(e))
            win.destroy()

        def delete_profile_action():
            name = get_selected_profile()
            if not name:
                return
            answer = messagebox.askyesno(self.get_str('profile_delete_confirm', name), self.get_str('profile_delete_confirm', name))
            if not answer:
                return
            profiles = self._load_profiles()
            if name in profiles:
                project_path = profiles[name].get('project_path')
                if project_path and os.path.exists(project_path):
                    shutil.rmtree(project_path)
                    self.log(f"Удалена папка проекта: {project_path}")
                self._delete_profile(name)
                win.destroy()
                self.open_profile_manager()

        def export_profile_action():
            name = get_selected_profile()
            if not name:
                return
            profiles = self._load_profiles()
            if name not in profiles:
                return
            data = profiles[name]
            project_path = data.get('project_path')
            if not project_path or not os.path.exists(project_path):
                messagebox.showerror("Error", self.get_str('profile_path_not_exists'))
                return
            export_path = filedialog.asksaveasfilename(
                defaultextension=".dayr",
                filetypes=[("Day R Profile", "*.dayr"), ("All files", "*.*")],
                initialfile=f"{name}.dayr"
            )
            if not export_path:
                return
            try:
                with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root_dir, dirs, files in os.walk(project_path):
                        for file in files:
                            file_path = os.path.join(root_dir, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(project_path))
                            zipf.write(file_path, arcname)
                self.log(f"Профиль экспортирован в: {export_path}")
                messagebox.showinfo("Success", self.get_str('profile_exported', export_path))
            except Exception as e:
                self.log(f"Ошибка экспорта: {e}")

        def import_profile_action():
            import_path = filedialog.askopenfilename(
                filetypes=[("Day R Profile", "*.dayr"), ("All files", "*.*")]
            )
            if not import_path:
                return
            extract_path = filedialog.askdirectory(title="Выберите папку для распаковки профиля")
            if not extract_path:
                return
            try:
                with zipfile.ZipFile(import_path, 'r') as zipf:
                    zipf.extractall(extract_path)
                profile_name = os.path.splitext(os.path.basename(import_path))[0]
                self._save_profile(profile_name, self.get_str('profile_imported_from', profile_name), extract_path)
                self.log(f"Профиль импортирован: {profile_name}")
                messagebox.showinfo("Success", self.get_str('profile_imported', profile_name))
                win.destroy()
                self.open_profile_manager()
            except Exception as e:
                self.log(f"Ошибка импорта: {e}")

        btn_frame = tk.Frame(win, bg='#2b2b2b')
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(btn_frame, text=self.get_str('profile_create_btn'), command=create_profile, bg='#3c3c3c', fg='white', relief='flat').pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text=self.get_str('profile_edit_btn'), command=edit_profile, bg='#3c3c3c', fg='white', relief='flat').pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text=self.get_str('profile_select_btn'), command=select_profile, bg='#3c3c3c', fg='white', relief='flat').pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text=self.get_str('profile_delete_btn'), command=delete_profile_action, bg='#3c3c3c', fg='white', relief='flat').pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text=self.get_str('profile_export_btn'), command=export_profile_action, bg='#3c3c3c', fg='white', relief='flat').pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text=self.get_str('profile_import_btn'), command=import_profile_action, bg='#3c3c3c', fg='white', relief='flat').pack(fill=tk.X, pady=2)

    def _get_profiles_dir(self):
        return os.path.join(SETTINGS_DIR, 'profiles')

    def _load_profiles(self):
        profiles = {}
        profiles_dir = self._get_profiles_dir()
        if not os.path.exists(profiles_dir):
            return profiles
        for item in os.listdir(profiles_dir):
            profile_path = os.path.join(profiles_dir, item)
            if os.path.isdir(profile_path):
                ini_path = os.path.join(profile_path, 'profile.ini')
                if os.path.exists(ini_path):
                    config = configparser.ConfigParser()
                    config.read(ini_path)
                    if 'Profile' in config:
                        profiles[item] = dict(config['Profile'])
        return profiles

    def _save_profile(self, name, description, project_path):
        profiles_dir = self._get_profiles_dir()
        os.makedirs(profiles_dir, exist_ok=True)
        profile_dir = os.path.join(profiles_dir, name)
        os.makedirs(profile_dir, exist_ok=True)
        config = configparser.ConfigParser()
        config['Profile'] = {
            'name': name,
            'description': description or '',
            'project_path': project_path,
            'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1'
        }
        with open(os.path.join(profile_dir, 'profile.ini'), 'w') as f:
            config.write(f)

    def _delete_profile(self, name):
        profiles_dir = self._get_profiles_dir()
        profile_dir = os.path.join(profiles_dir, name)
        if os.path.exists(profile_dir):
            shutil.rmtree(profile_dir)
            return True
        return False

    # ==========================================================
    # ====   Помощь и настройки                            ====
    # ==========================================================

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

    # ==========================================================
    # ====   Дополнительные методы                          ====
    # ==========================================================

    def open_mod_scripts_folder(self):
        mod_scripts = os.path.join(self.project_dir.get(), 'mod_scripts')
        if os.path.exists(mod_scripts):
            os.startfile(mod_scripts)
        else:
            messagebox.showerror("Error", "Папка mod_scripts не найдена. Сначала выполните декомпиляцию.")

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
                self.log(self.get_str('log_saved', file_path))
                messagebox.showinfo("Success", self.get_str('log_saved', file_path))
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

# ==========================================================
# ====   Запуск приложения                               ====
# ==========================================================

if __name__ == "__main__":
    if sys.platform == 'win32' and not is_admin():
        lang = get_setting('General', 'lang', 'ru')
        title = LANGUAGES[lang].get('admin_required_title', 'Admin rights required')
        message = LANGUAGES[lang].get('admin_required_message', 'Administrator rights are required.\nRestart the program?')
        answer = messagebox.askyesno(title, message)
        if answer:
            restart_as_admin()
        else:
            sys.exit()
    else:
        root = tk.Tk()
        app = ModdingGUI(root)
        root.mainloop()