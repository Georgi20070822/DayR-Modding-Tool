#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DayR Modding Tool v0.0.4
Главный файл запуска
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import ConfigManager
from core.event_bus import EventBus
from core.plugin_manager import PluginManager
from gui.main_window import MainWindow, is_admin, restart_as_admin
from utils.helpers import resource_path

def main():
    # Проверка прав администратора
    if sys.platform == 'win32' and not is_admin():
        answer = messagebox.askyesno(
            "Недостаточно прав",
            "Для корректной работы программы требуются права администратора.\n\n"
            "Перезапустить программу с правами администратора?"
        )
        if answer:
            restart_as_admin()
            return
        else:
            # Пользователь отказался — работаем без прав (могут быть проблемы)
            pass
    
    # Загружаем конфигурацию
    config_manager = ConfigManager()
    config = config_manager.config
    
    # Создаём главное окно
    root = tk.Tk()
    root.title("Day R Modding Tool")
    root.geometry("1100x720")
    root.resizable(True, True)
    root.configure(bg='#2b2b2b')
    
    try:
        icon_path = resource_path('resources/icon.ico')
        if os.path.exists(icon_path):
            self.root.iconbitmap(default=icon_path)
        else:
            # Запасной вариант через iconphoto
            icon = Image.open(resource_path('resources/icon.ico'))
            photo = ImageTk.PhotoImage(icon)
            self.root.iconphoto(True, photo)
    except Exception as e:
        print(f"⚠️ Не удалось установить иконку: {e}")
    
    app = MainWindow(root, config_manager)
    
    # Плагины
    plugin_manager = PluginManager()
    plugin_manager.load_plugins()
    for cmd_name, cmd_func in plugin_manager.commands.items():
        app.console.register_command(cmd_name, cmd_func)
    
    # Команда lua
    def cmd_lua(*args):
        try:
            app.open_console()
        except Exception as e:
            return app.get_str('cmd_lua_error', str(e))
        return None
    app.console.register_command("lua", cmd_lua)
    app.console.register_command("luaconsole", cmd_lua)
    
    # Подписка плагинов
    for event_type, callbacks in plugin_manager.event_handlers.items():
        for callback in callbacks:
            EventBus.subscribe(event_type, callback)
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Программа прервана пользователем")
        sys.exit(0)

if __name__ == "__main__":
    main()