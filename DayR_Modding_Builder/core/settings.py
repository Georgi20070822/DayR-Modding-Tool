import os

# Папка для хранения настроек в профиле пользователя
SETTINGS_DIR = os.path.join(os.path.expanduser("~"), "DayR_MB")

def ensure_settings_dir():
    """Создаёт папку настроек, если её нет."""
    if not os.path.exists(SETTINGS_DIR):
        os.makedirs(SETTINGS_DIR)
    return SETTINGS_DIR