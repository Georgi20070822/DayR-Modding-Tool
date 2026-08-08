import os
import sys

def resource_path(relative_path):
    """Возвращает абсолютный путь к ресурсу (для сборки в EXE)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        return os.path.join(os.path.dirname(__file__), '..', relative_path)

def ensure_dir(path):
    """Создаёт папку, если её нет"""
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def get_tools_dir(project_dir):
    """Возвращает путь к папке tools в проекте"""
    tools_dir = os.path.join(project_dir, 'tools')
    ensure_dir(tools_dir)
    return tools_dir