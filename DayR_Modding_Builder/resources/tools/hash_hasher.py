import os
import hashlib
import sys

def compute_hashes(project_dir):
    """Вычисляет SHA-1 хеши файлов в папке hash/ внутри project_dir и возвращает строку."""
    hash_dir = os.path.join(project_dir, 'hash')
    if not os.path.exists(hash_dir):
        return f"Папка '{hash_dir}' не найдена. Создайте её и поместите туда файлы."

    files = [f for f in os.listdir(hash_dir) if os.path.isfile(os.path.join(hash_dir, f))]
    if not files:
        return "В папке hash нет файлов."

    result = "=== ХЕШИ ФАЙЛОВ (SHA-1) ===\n\n"
    for filename in sorted(files):
        filepath = os.path.join(hash_dir, filename)
        try:
            sha1 = hashlib.sha1()
            with open(filepath, 'rb') as f:
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    sha1.update(data)
            hash_value = sha1.hexdigest()
            result += f'    ["{filename}"] = "{hash_value}",\n'
        except Exception as e:
            result += f'Ошибка при чтении {filename}: {e}\n'
    return result

def main():
    # Для совместимости с вызовом из командной строки
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)  # поднимаемся на уровень выше (корень DayR_moding)
    print(compute_hashes(project_dir))

if __name__ == "__main__":
    main()