import os
import chardet

def detect_encoding(file_path):
    """Определяет кодировку файла"""
    with open(file_path, 'rb') as f:
        raw = f.read()
    result = chardet.detect(raw)
    return result['encoding']

def decode_utf8_file(file_path, force=False):
    """
    Перекодирует файл в UTF-8 без BOM
    Если force=True, принудительно перекодирует даже если уже UTF-8
    """
    if not os.path.exists(file_path):
        return False, "Файл не найден"
    
    # Определяем текущую кодировку
    encoding = detect_encoding(file_path)
    
    # Если уже UTF-8 и не принудительно — пропускаем
    if encoding and encoding.lower() in ['utf-8', 'ascii'] and not force:
        return True, f"Файл уже в UTF-8 ({encoding})"
    
    try:
        # Читаем в текущей кодировке
        with open(file_path, 'r', encoding=encoding or 'utf-8', errors='ignore') as f:
            content = f.read()
        
        # Сохраняем как UTF-8 без BOM
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, f"Файл перекодирован в UTF-8 (было: {encoding or 'unknown'})"
    except Exception as e:
        return False, f"Ошибка: {e}"

def decode_utf8_folder(folder_path, force=False):
    """
    Рекурсивно перекодирует все .lua файлы в папке
    Возвращает (количество_обработанных, количество_ошибок, список_ошибок)
    """
    if not os.path.exists(folder_path):
        return 0, 1, ["Папка не найдена"]
    
    processed = 0
    errors = 0
    error_messages = []
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.lua'):
                file_path = os.path.join(root, file)
                success, msg = decode_utf8_file(file_path, force)
                if success:
                    processed += 1
                else:
                    errors += 1
                    error_messages.append(f"{file_path}: {msg}")
    
    return processed, errors, error_messages