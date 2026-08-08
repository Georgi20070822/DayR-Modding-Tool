import os
import sys
import importlib.util
import shutil
from .settings import SETTINGS_DIR, ensure_settings_dir
from .event_bus import EventBus
from utils.helpers import resource_path


class PluginManager:
    """
    Управление плагинами.
    Плагины хранятся в %USERPROFILE%/DayR_MB/plugins/
    """
    
    def __init__(self, plugins_dir=None):
        # Определяем папку плагинов (в DayR_MB)
        if plugins_dir is None:
            ensure_settings_dir()
            self.plugins_dir = os.path.join(SETTINGS_DIR, "plugins")
        else:
            self.plugins_dir = plugins_dir
        
        # Создаём папку плагинов, если её нет
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)
            # Копируем пример плагина из ресурсов (если есть)
            self._copy_example_plugin()
        
        self.plugins = []
        self.commands = {}
        self.event_handlers = {}
        
        # Автоматическая загрузка всех плагинов
        self.load_plugins()
    
    def _copy_example_plugin(self):
        """Копирует example_plugin.py из ресурсов в папку плагинов."""
        try:
            # Путь к примеру плагина внутри ресурсов (для EXE и для разработки)
            src = resource_path('plugins/example_plugin.py')
            if os.path.exists(src):
                dst = os.path.join(self.plugins_dir, 'example_plugin.py')
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                    print(f"✅ Пример плагина скопирован в {dst}")
            else:
                # Если файла нет – создаём минимальный пример
                self._create_default_example()
        except Exception as e:
            print(f"⚠️ Не удалось скопировать пример плагина: {e}")
    
    def _create_default_example(self):
        """Создаёт файл example_plugin.py с базовым содержимым."""
        example_path = os.path.join(self.plugins_dir, 'example_plugin.py')
        if os.path.exists(example_path):
            return
        content = '''"""
Пример плагина для DayR Modding Tool
"""

def register(plugin_manager):
    """Функция регистрации плагина (вызывается при загрузке)"""
    plugin_manager.add_command("hello", hello_command)
    plugin_manager.add_command("echo", echo_command)
    plugin_manager.add_event_handler("log", on_log_event)
    print("Плагин 'example' загружен!")

def hello_command(*args):
    """Команда: hello - выводит приветствие"""
    return "Hello from example plugin!"

def echo_command(*args):
    """Команда: echo <текст> - повторяет введённый текст"""
    if args:
        return " ".join(args)
    return "Usage: echo <text>"

def on_log_event(data):
    """Обработчик события лога"""
    # Можно делать что-то с сообщением лога
    pass
'''
        try:
            with open(example_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Создан пример плагина: {example_path}")
        except Exception as e:
            print(f"⚠️ Не удалось создать пример плагина: {e}")
    
    def load_plugins(self):
        """Загружает все плагины из папки."""
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)
            self._copy_example_plugin()
        
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                module_name = filename[:-3]
                module_path = os.path.join(self.plugins_dir, filename)
                try:
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Проверяем, есть ли функция регистрации
                    if hasattr(module, "register"):
                        module.register(self)
                        self.plugins.append(module)
                        print(f"✅ Плагин загружен: {module_name}")
                        # Оповещаем через EventBus
                        EventBus.publish("log", f"Плагин загружен: {module_name}")
                    else:
                        print(f"⚠️ Плагин {module_name} не имеет функции register()")
                        EventBus.publish("log", f"Плагин {module_name} не имеет функции register()")
                except Exception as e:
                    error_msg = f"Ошибка загрузки плагина {module_name}: {e}"
                    print(f"❌ {error_msg}")
                    EventBus.publish("log", error_msg)
    
    def add_command(self, name, func):
        """Добавляет команду для консоли."""
        self.commands[name] = func
    
    def add_event_handler(self, event_type, callback):
        """Добавляет обработчик события."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(callback)
    
    def get_plugin_commands(self):
        """Возвращает словарь всех команд, зарегистрированных плагинами."""
        return self.commands.copy()
    
    def reload_plugins(self):
        """Перезагружает все плагины (очищает и загружает заново)."""
        self.plugins.clear()
        self.commands.clear()
        self.event_handlers.clear()
        self.load_plugins()