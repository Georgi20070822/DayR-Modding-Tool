import os
import sys
import subprocess

def get_tool_path(tool_name):
    """Возвращает путь к инструменту в папке tools проекта (оставлено для совместимости)"""
    project_dir = os.environ.get('DAYR_PROJECT_DIR')
    if project_dir:
        tools_dir = os.path.join(project_dir, 'tools')
        tool_path = os.path.join(tools_dir, tool_name)
        if os.path.exists(tool_path):
            return tool_path
    
    from .helpers import resource_path
    tool_path = resource_path(f'tools/{tool_name}')
    if os.path.exists(tool_path):
        return tool_path
    
    return None

def assemble_lu(input_file, output_file):
    """
    Ассемблирует .asm в .lu
    Использует asm_lu.py из папки asm (Python-версия)
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Входной файл не найден: {input_file}")
    
    # Определяем путь к скрипту ассемблера
    asm_script = os.path.join(os.path.dirname(__file__), 'asm', 'asm_lu.py')
    if not os.path.exists(asm_script):
        raise FileNotFoundError(f"Скрипт ассемблера не найден: {asm_script}")
    
    # Запускаем asm_lu.py через Python
    cmd = [sys.executable, asm_script, input_file, output_file]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise Exception(f"Ошибка ассемблера: {result.stderr or result.stdout}")
        return output_file
    except subprocess.TimeoutExpired:
        raise TimeoutError("Ассемблирование прервано по таймауту (30 сек)")
    except Exception as e:
        raise RuntimeError(f"Ошибка при запуске ассемблера: {e}")

def disassemble_lu(input_file, output_file):
    """
    Дизассемблирует .lu в .asm
    Использует disasm_lu.py из папки asm (Python-версия)
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Входной файл не найден: {input_file}")
    
    # Определяем путь к скрипту дизассемблера
    disasm_script = os.path.join(os.path.dirname(__file__), 'asm', 'disasm_lu.py')
    if not os.path.exists(disasm_script):
        raise FileNotFoundError(f"Скрипт дизассемблера не найден: {disasm_script}")
    
    # Запускаем disasm_lu.py через Python
    cmd = [sys.executable, disasm_script, input_file, output_file]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise Exception(f"Ошибка дизассемблера: {result.stderr or result.stdout}")
        return output_file
    except subprocess.TimeoutExpired:
        raise TimeoutError("Дизассемблирование прервано по таймауту (30 сек)")
    except Exception as e:
        raise RuntimeError(f"Ошибка при запуске дизассемблера: {e}")