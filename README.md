# DayR Modding Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**DayR Modding Tool** is a graphical tool for modding the game **Day R Survival** (version 1.694 and below). It automates all key modding steps: unpacking the `resource.car` archive, decompiling scripts, compiling modified files, packing the modded archive, and **checking code for errors** with the built‑in static analyzer Luacheck.

---

## 📥 Download the Ready‑to‑Use Program

**The latest stable version can be downloaded from the [Releases](https://github.com/Georgi20070822/DayR-Modding-Tool/releases) section.**  
Previous versions are also available there.

---

## 🆕 What's New in Version 0.0.3

- ✅ **Luacheck integration** — static Lua code analysis.
- ✅ **New buttons**: "Check one .lua" (row 3) and "Check all .lua" (row 4).
- ✅ Added a **"Check"** button for each file in the File Manager.
- ✅ Luacheck detects unused variables, undeclared globals, unreachable code, and other errors.
- ✅ Improved documentation and instructions.

### Previous Versions

**Version 0.0.2:**
- Project profile management (create, select, export/import).
- Built‑in Lua editor with syntax highlighting.
- Lua console for executing code.
- "Hash" button in the File Manager.
- Administrator rights check on startup.

**Version 0.0.1 (initial release):**
- Core functionality: unpack/pack resource.car, decompile/compile, file manager, font settings.
- Russian and English language support.

For a full list of changes, see the [Changelog](#-changelog) section.

---

## ⚙️ System Requirements

- **OS**: Windows 7/8/10/11 (32 or 64 bit)
- **RAM**: 512 MB or more
- **Free disk space**: ~100 MB for the tool + ~2 GB for game files (during unpacking)
- **Write permissions** in the working folder

---

## 🚀 Quick Start

1. Download `DayR_Modding_Tool.exe` from the [Releases](https://github.com/Georgi20070822/DayR-Modding-Tool/releases) section.
2. Run the program.
3. Select a project folder.
4. Specify the path to `resource.car` from the game.
5. Click "Unpack resource.car" → "Decompile all .lu → .lua".
6. Edit the required `.lua` files in the `mod_scripts` folder.
7. **Check your code** with Luacheck (the "Check one .lua" or "Check all .lua" button).
8. Compile the changed files via the File Manager (the "Build" button).
9. Click "Pack resource.car (mod)" and save the new archive.
10. Copy the resulting `resource.car` to the game folder.

For detailed instructions, see the **Help** section inside the program (the "?" button).

---

## 🛠️ Building from Source

If you want to build the program yourself from the source code (for development or custom modifications):

1. Make sure you have **Python 3.10+** and **pip** installed.
2. Clone the repository:
   ```bash
   git clone https://github.com/Georgi20070822/DayR-Modding-Tool.git
   cd DayR-Modding-Tool

# DayR Modding Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**DayR Modding Tool** — графическая программа для моддинга игры **Day R Survival** (версия 1.694 и ниже). Она автоматизирует все основные этапы создания модов: распаковку игрового архива `resource.car`, декомпиляцию скриптов, компиляцию изменённых файлов, сборку модифицированного архива и **проверку кода на ошибки** с помощью встроенного статического анализатора Luacheck.

---

## 📥 Скачать готовую программу

**Последнюю стабильную версию можно скачать в разделе [Releases](https://github.com/Georgi20070822/DayR-Modding-Tool/releases).**  
Там же доступны все предыдущие версии.

---

## 🆕 Что нового в версии 0.0.3

- ✅ **Интеграция Luacheck** — статический анализ кода на Lua.
- ✅ **Новые кнопки**: «Проверить один .lua» (ряд 3) и «Проверить все .lua» (ряд 4).
- ✅ В менеджере файлов добавлена кнопка **«Проверить»** для каждого файла.
- ✅ Luacheck находит неиспользуемые переменные, необъявленные глобалы, недостижимый код и другие ошибки.
- ✅ Улучшена документация и инструкции.

### Предыдущие версии

**Версия 0.0.2:**
- Управление профилями проектов (создание, выбор, экспорт/импорт).
- Встроенный редактор Lua с подсветкой синтаксиса.
- Lua-консоль для выполнения кода.
- Кнопка «Хеш» в менеджере файлов.
- Проверка прав администратора при запуске.

**Версия 0.0.1 (первый релиз):**
- Базовая функциональность: распаковка/упаковка resource.car, декомпиляция/компиляция, менеджер файлов, настройки шрифтов.
- Поддержка русского и английского языков.

Полный список изменений см. в разделе [История изменений](#-история-изменений-changelog).

---

## ⚙️ Системные требования

- **ОС**: Windows 7/8/10/11 (32 или 64 бит)
- **ОЗУ**: от 512 МБ
- **Свободное место**: ~100 МБ для программы + ~2 ГБ для файлов игры (при распаковке)
- **Права на запись** в рабочей папке

---

## 🚀 Быстрый старт

1. Скачайте `DayR_Modding_Tool.exe` из раздела [Releases](https://github.com/Georgi20070822/DayR-Modding-Tool/releases).
2. Запустите программу.
3. Выберите папку проекта.
4. Укажите путь к `resource.car` из игры.
5. Нажмите «Распаковать resource.car» → «Декомпилировать все .lu → .lua».
6. Отредактируйте нужные `.lua` файлы в папке `mod_scripts`.
7. **Проверьте код** через Luacheck (кнопка «Проверить один .lua» или «Проверить все .lua»).
8. Скомпилируйте изменённые файлы через менеджер файлов (кнопка «Собрать»).
9. Нажмите «Упаковать resource.car (мод)» и сохраните новый архив.
10. Скопируйте полученный `resource.car` в папку с игрой.

Подробная инструкция — в разделе [Помощь](#-помощь) внутри программы (кнопка «?»).

---

## 🛠️ Сборка из исходников

Если вы хотите собрать программу самостоятельно из исходного кода (для разработки или внесения изменений):

1. Убедитесь, что у вас установлен **Python 3.10+** и **pip**.
2. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Georgi20070822/DayR-Modding-Tool.git
   cd DayR-Modding-Tool
