import tkinter as tk
from tkinter import scrolledtext

class ToolConsole:
    """Консоль команд для управления тулом"""
    
    def __init__(self, master, lang='ru', get_str_func=None):
        self.master = master
        self.lang = lang
        self.get_str = get_str_func or (lambda key, *args: key)
        self.commands = {}
        self.window = None
        self.output = None
        self.entry = None
        self.history = []
        self.history_index = 0
        
        # Регистрируем базовые команды
        self.register_command("help", self.cmd_help)
        self.register_command("clear", self.cmd_clear)
        self.register_command("cls", self.cmd_clear)
        self.register_command("exit", self.cmd_exit)
        self.register_command("quit", self.cmd_exit)
    
    def register_command(self, name, func):
        """Регистрирует новую команду"""
        self.commands[name] = func
    
    def add_command(self, name, func):
        """Алиас для register_command"""
        self.register_command(name, func)
    
    def show(self):
        """Показывает окно консоли"""
        if self.window is not None and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return
        
        self.window = tk.Toplevel(self.master)
        self.window.title(self.get_str('cmd_console_title'))
        self.window.geometry("600x450")
        self.window.configure(bg='#2b2b2b')
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        
        # Поле вывода
        self.output = scrolledtext.ScrolledText(self.window, wrap=tk.WORD,
                                                 bg='#1e1e1e', fg='#eeeeee',
                                                 insertbackground='white',
                                                 font=('Courier New', 10))
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, self.get_str('cmd_console_ready'))
        self.output.config(state=tk.DISABLED)
        
        # Поле ввода
        input_frame = tk.Frame(self.window, bg='#2b2b2b')
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(input_frame, text="> ", fg='white', bg='#2b2b2b',
                 font=('Courier New', 10)).pack(side=tk.LEFT)
        
        self.entry = tk.Entry(input_frame, bg='#3c3c3c', fg='white',
                              insertbackground='white', font=('Courier New', 10))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind('<Return>', self.execute_command)
        self.entry.bind('<Up>', self.history_up)
        self.entry.bind('<Down>', self.history_down)
        self.entry.focus_set()
    
    def hide(self):
        """Скрывает окно консоли (не закрывает)"""
        if self.window:
            self.window.withdraw()
    
    def execute_command(self, event=None):
        """Выполняет введённую команду"""
        if self.entry is None:
            return
        cmd = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        
        if not cmd:
            return
        
        # Добавляем в историю
        self.history.append(cmd)
        self.history_index = len(self.history)
        
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, f"> {cmd}\n")
        
        # Разбираем команду с аргументами
        parts = cmd.split()
        cmd_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd_name in self.commands:
            try:
                result = self.commands[cmd_name](*args)
                if result is not None:
                    self.output.insert(tk.END, f"{result}\n")
            except Exception as e:
                self.output.insert(tk.END, f"Ошибка: {e}\n")
                import traceback
                self.output.insert(tk.END, traceback.format_exc() + "\n")
        else:
            self.output.insert(tk.END, self.get_str('cmd_unknown', cmd_name) + "\n")
            self.output.insert(tk.END, self.get_str('cmd_help_hint') + "\n")
        
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)
    
    def history_up(self, event):
        """Предыдущая команда в истории"""
        if not self.history:
            return
        if self.history_index > 0:
            self.history_index -= 1
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.history[self.history_index])
    
    def history_down(self, event):
        """Следующая команда в истории"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self.history[self.history_index])
        else:
            self.history_index = len(self.history)
            self.entry.delete(0, tk.END)
    
    # ===== Встроенные команды =====
    def cmd_help(self, *args):
        """Показывает список доступных команд"""
        if not self.commands:
            return "Нет доступных команд"
        lines = [self.get_str('cmd_help')]
        for name in sorted(self.commands.keys()):
            lines.append(f"  {name}")
        return "\n".join(lines)
    
    def cmd_clear(self, *args):
        """Очищает вывод консоли"""
        if self.output:
            self.output.config(state=tk.NORMAL)
            self.output.delete(1.0, tk.END)
            self.output.config(state=tk.DISABLED)
        return self.get_str('cmd_clear_done')
    
    def cmd_exit(self, *args):
        """Закрывает консоль"""
        self.hide()
        return self.get_str('cmd_exit_done')