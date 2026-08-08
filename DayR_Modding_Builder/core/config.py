import json
import os
import sys
import shutil
from .settings import SETTINGS_DIR, ensure_settings_dir

class ConfigManager:
    """Управление конфигурацией программы (хранится в DayR_MB/config.json)"""
    
    def __init__(self, config_path=None):
        if config_path is None:
            # Основной путь – в папке пользователя
            ensure_settings_dir()
            self.config_path = os.path.join(SETTINGS_DIR, "config.json")
        else:
            self.config_path = config_path
        
        # Если в папке пользователя нет config.json, но есть рядом с EXE – переносим
        if not os.path.exists(self.config_path):
            old_config = os.path.join(os.path.dirname(sys.executable), "config.json") if getattr(sys, 'frozen', False) else "config.json"
            if os.path.exists(old_config):
                shutil.copy2(old_config, self.config_path)
                print(f"✅ Перенесён config.json из {old_config} в {self.config_path}")
            else:
                # Иначе создаём дефолтный
                default = self.create_default_config()
                self.save(default)
        else:
            # Если файл есть – загружаем
            pass
        
        self.config = self.load()
    
    def load(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save(self, config=None):
        if config is None:
            config = self.config
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    
    def create_default_config(self):
        return {
            "rows": 5,
            "columns": 4,
            "language": "ru",
            "font": "classic",
            "buttons": [
                {
                    "id": "unpack",
                    "text_ru": "Распаковать resource.car",
                    "text_en": "Unpack resource.car",
                    "command": "run_unpack",
                    "row": 0,
                    "col": 0,
                    "color": "default"
                },
                {
                    "id": "decompile_all",
                    "text_ru": "Декомпилировать все .lu → .lua",
                    "text_en": "Decompile all .lu → .lua",
                    "command": "run_decompile_all",
                    "row": 0,
                    "col": 1,
                    "color": "default"
                },
                {
                    "id": "compile_all",
                    "text_ru": "Скомпилировать все .lua → .lu (НЕ ИСПОЛЬЗОВАТЬ!)",
                    "text_en": "Compile all .lua → .lu (DO NOT USE!)",
                    "command": "run_compile_all",
                    "row": 0,
                    "col": 2,
                    "color": "danger"
                },
                {
                    "id": "pack",
                    "text_ru": "Упаковать resource.car (мод)",
                    "text_en": "Pack resource.car (mod)",
                    "command": "run_pack",
                    "row": 1,
                    "col": 0,
                    "color": "default"
                },
                {
                    "id": "clean_project",
                    "text_ru": "Очистить проект",
                    "text_en": "Clean Project",
                    "command": "clean_project",
                    "row": 1,
                    "col": 1,
                    "color": "danger"
                },
                {
                    "id": "file_manager",
                    "text_ru": "Менеджер файлов",
                    "text_en": "File Manager",
                    "command": "open_file_manager",
                    "row": 1,
                    "col": 2,
                    "color": "default"
                },
                {
                    "id": "compile_one",
                    "text_ru": "Скомпилировать один .lua",
                    "text_en": "Compile one .lua",
                    "command": "run_compile_one",
                    "row": 2,
                    "col": 0,
                    "color": "default"
                },
                {
                    "id": "decompile_one",
                    "text_ru": "Декомпилировать один .lu",
                    "text_en": "Decompile one .lu",
                    "command": "run_decompile_one",
                    "row": 2,
                    "col": 1,
                    "color": "default"
                },
                {
                    "id": "choose_car",
                    "text_ru": "Выбрать resource.car",
                    "text_en": "Choose resource.car",
                    "command": "choose_resource_car",
                    "row": 2,
                    "col": 2,
                    "color": "default"
                },
                {
                    "id": "check_one",
                    "text_ru": "Проверить один .lua",
                    "text_en": "Check one .lua",
                    "command": "run_check_one",
                    "row": 2,
                    "col": 3,
                    "color": "default"
                },
                {
                    "id": "reset_scripts",
                    "text_ru": "Сбросить mod_scripts",
                    "text_en": "Reset mod_scripts",
                    "command": "reset_mod_scripts",
                    "row": 3,
                    "col": 0,
                    "color": "warning"
                },
                {
                    "id": "clear_modded",
                    "text_ru": "Очистить modded_lu",
                    "text_en": "Clear modded_lu",
                    "command": "clear_modded_lu",
                    "row": 3,
                    "col": 1,
                    "color": "danger"
                },
                {
                    "id": "console",
                    "text_ru": "Lua-консоль",
                    "text_en": "Lua Console",
                    "command": "open_console",
                    "row": 3,
                    "col": 2,
                    "color": "default"
                },
                {
                    "id": "check_all",
                    "text_ru": "Проверить все .lua",
                    "text_en": "Check all .lua",
                    "command": "run_check_all",
                    "row": 3,
                    "col": 3,
                    "color": "default"
                }
            ]
        }