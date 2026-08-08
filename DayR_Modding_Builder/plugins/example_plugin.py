"""
Пример плагина для DayR Modding Tool
"""

def register(plugin_manager):
    """Функция регистрации плагина (вызывается при загрузке)"""
    # Добавляем команду в консоль
    plugin_manager.add_command("hello", hello_command)
    plugin_manager.add_command("echo", echo_command)
    
    # Добавляем обработчик события
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